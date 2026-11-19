# SPDX-License-Identifier: Apache-2.0
"""Offline inference for the VecToMorph Arm C research checkpoint."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from torch import nn

from src.data.mapping import COARSE_LABELS
from src.data.transforms import IMAGENET_MEAN, IMAGENET_STD, PhysicalField
from src.models.dinov2 import create_dinov2_extractor


ARM_C_SHA256 = "790a90ef6ab8f17da146e0122f38acd161462bcb31638903c26666754d18c4f3"
SHARED_LABELS = {
    "coarse": tuple(COARSE_LABELS),
    "ne_stage": ("band", "segmented"),
    "ig_stage": ("promyelocyte", "myelocyte", "metamyelocyte"),
}
IMAGE_SOURCES = ("mll23", "acevedo", "ku", "univali", "park", "crop")
NATIVE_SOURCES = ("acevedo", "ku", "mll23", "univali")


def prepare_image(image: Image.Image, source: str) -> Image.Image:
    """Apply the training crop and return its RGB 252-pixel square."""
    if source not in IMAGE_SOURCES:
        raise ValueError(f"Unknown image source {source!r}")
    image = image.convert("RGB")
    if source in ("mll23", "acevedo"):
        image = PhysicalField(source)(image)
    else:
        side = min(image.size)
        left = round((image.width - side) / 2)
        top = round((image.height - side) / 2)
        image = image.crop((left, top, left + side, top + side))
    return image.resize((252, 252), Image.Resampling.BICUBIC)


def preprocess_image(image: Image.Image, source: str) -> torch.Tensor:
    """Convert a cell image to the normalized CHW input expected by the model."""
    pixels = np.array(prepare_image(image, source), dtype=np.float32) / 255.0
    tensor = torch.from_numpy(pixels).permute(2, 0, 1)
    mean = tensor.new_tensor(IMAGENET_MEAN).view(3, 1, 1)
    std = tensor.new_tensor(IMAGENET_STD).view(3, 1, 1)
    return tensor.sub(mean).div(std)


class ReleaseClassifier(nn.Module):
    """The trained encoder, shared classifiers and source-specific classifiers."""

    def __init__(self, model_config: dict, shared_labels: dict, native_labels: dict, train_sources: list):
        super().__init__()
        self.shared_labels = {key: tuple(labels) for key, labels in shared_labels.items()}
        if self.shared_labels != SHARED_LABELS:
            raise ValueError("Unexpected shared class order in the release checkpoint")
        if tuple(train_sources) != NATIVE_SOURCES or set(native_labels) != set(NATIVE_SOURCES):
            raise ValueError("Unexpected training sources in the release checkpoint")
        self.native_labels = {source: tuple(native_labels[source]) for source in train_sources}
        model = model_config["model"]
        if (model["name"], model["image_size"], model["feature_mode"], model["l2_normalize"]) != (
            "vit_small_patch14_dinov2.lvd142m", 252, "cls_patch_mean", True
        ):
            raise ValueError("Unsupported Arm C encoder configuration")
        if model.get("weights_path"):
            raise ValueError("Portable model configuration must contain its weights in the checkpoint")
        self.encoder = create_dinov2_extractor(model_config, pretrained=False)
        self.heads = nn.Module()
        self.heads.common = nn.ModuleDict({
            key: nn.Linear(self.encoder.embed_dim, len(labels)) for key, labels in SHARED_LABELS.items()
        })
        self.heads.native = nn.ModuleDict({
            source: nn.Linear(self.encoder.embed_dim, len(self.native_labels[source])) for source in train_sources
        })

    def forward(self, images: torch.Tensor) -> dict:
        images = images.contiguous(memory_format=torch.channels_last)
        features = self.encoder(images)
        with torch.autocast(device_type=images.device.type, enabled=False):
            features = features.float()
            logits = {key: head(features) for key, head in self.heads.common.items()}
            logits["native"] = {source: head(features) for source, head in self.heads.native.items()}
        return logits


def load_release(checkpoint: str | Path, device: str = "cpu") -> ReleaseClassifier:
    """Verify and load the pinned research checkpoint without network access."""
    path = Path(checkpoint)
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != ARM_C_SHA256:
        raise ValueError("Arm C checkpoint SHA-256 differs from the released artifact")
    bundle = torch.load(path, map_location="cpu", weights_only=True)
    if bundle.get("format") != "vectomorph.arm-c.v1":
        raise ValueError("Unsupported VecToMorph checkpoint format")
    classifier = ReleaseClassifier(
        bundle["model_config"], bundle["shared_labels"], bundle["native_labels"], bundle["train_sources"]
    )
    classifier.encoder.load_state_dict(bundle["encoder_state"], strict=True)
    classifier.heads.load_state_dict(bundle["head_state"], strict=True)
    return classifier.to(device).eval()


def label_scores(logits: torch.Tensor, labels: tuple[str, ...]) -> dict:
    """Report the top class and the uncalibrated softmax scores of one head."""
    probabilities = logits.float().softmax(dim=-1).cpu().tolist()
    return {
        "predicted_label": labels[int(logits.argmax().item())],
        "softmax_scores": dict(zip(labels, probabilities)),
    }


def describe_prediction(outputs: dict, classifier: ReleaseClassifier, native_source: str | None = None) -> dict:
    """Interpret one image's shared head and the applicable stage head."""
    result = label_scores(outputs["coarse"], classifier.shared_labels["coarse"])
    stage = {"neutrophils": "ne_stage", "immature_granulocytes": "ig_stage"}.get(result["predicted_label"])
    if stage is not None:
        result["stage"] = label_scores(outputs[stage], classifier.shared_labels[stage])
    if native_source is not None:
        if native_source not in classifier.native_labels:
            raise ValueError(f"No trained native head for {native_source!r}")
        result["native_head"] = {
            "source": native_source,
            **label_scores(outputs["native"][native_source], classifier.native_labels[native_source]),
        }
    return result
