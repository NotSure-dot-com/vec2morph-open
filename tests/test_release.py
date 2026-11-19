"""Contracts that keep the release compatible with the archived Arm C checkpoint."""

import hashlib

import numpy as np
from PIL import Image
import pytest
import torch
from torch import nn

from src.models import release


CONFIG = {
    "model": {
        "name": "vit_small_patch14_dinov2.lvd142m",
        "image_size": 252,
        "feature_mode": "cls_patch_mean",
        "l2_normalize": True,
    }
}
NATIVE = {source: ("first", "second") for source in release.NATIVE_SOURCES}


class TinyEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed_dim = 4
        self.projection = nn.Linear(3, self.embed_dim)

    def forward(self, images):
        return self.projection(images.mean(dim=(2, 3)))


def test_loader_constructs_offline_and_restores_every_head(tmp_path, monkeypatch):
    calls = []

    def create(config, pretrained):
        calls.append(pretrained)
        assert config == CONFIG
        return TinyEncoder()

    monkeypatch.setattr(release, "create_dinov2_extractor", create)
    original = release.ReleaseClassifier(CONFIG, release.SHARED_LABELS, NATIVE, list(release.NATIVE_SOURCES)).eval()
    path = tmp_path / "model.pth"
    torch.save({
        "format": "vectomorph.arm-c.v1",
        "model_config": CONFIG,
        "shared_labels": release.SHARED_LABELS,
        "native_labels": NATIVE,
        "train_sources": list(release.NATIVE_SOURCES),
        "encoder_state": original.encoder.state_dict(),
        "head_state": original.heads.state_dict(),
    }, path)
    monkeypatch.setattr(release, "ARM_C_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())
    loaded = release.load_release(path)
    images = torch.rand(2, 3, 8, 8)
    with torch.inference_mode():
        expected = original(images)
        actual = loaded(images)
    assert calls == [False, False]
    assert not loaded.training
    for key in release.SHARED_LABELS:
        torch.testing.assert_close(actual[key], expected[key], rtol=0, atol=0)
    for source in release.NATIVE_SOURCES:
        torch.testing.assert_close(actual["native"][source], expected["native"][source], rtol=0, atol=0)


def test_wrong_artifact_hash_is_rejected_before_deserialization(tmp_path, monkeypatch):
    path = tmp_path / "model.pth"
    path.write_bytes(b"an unrelated checkpoint")
    monkeypatch.setattr(torch, "load", lambda *args, **kwargs: pytest.fail("Unverified artifact was deserialized"))
    with pytest.raises(ValueError, match="SHA-256"):
        release.load_release(path)


def test_autocast_preserves_float32_head_arithmetic(monkeypatch):
    monkeypatch.setattr(release, "create_dinov2_extractor", lambda *args, **kwargs: TinyEncoder())
    classifier = release.ReleaseClassifier(CONFIG, release.SHARED_LABELS, NATIVE, list(release.NATIVE_SOURCES))
    with torch.inference_mode(), torch.autocast("cpu", dtype=torch.bfloat16):
        output = classifier(torch.rand(2, 3, 8, 8))
    assert output["coarse"].dtype == torch.float32
    assert all(value.dtype == torch.float32 for value in output["native"].values())


def test_legacy_label_order_cannot_silently_change_the_output(monkeypatch):
    monkeypatch.setattr(release, "create_dinov2_extractor", lambda *args, **kwargs: pytest.fail("Labels must be checked first"))
    labels = {**release.SHARED_LABELS, "coarse": tuple(reversed(release.SHARED_LABELS["coarse"]))}
    with pytest.raises(ValueError, match="class order"):
        release.ReleaseClassifier(CONFIG, labels, NATIVE, list(release.NATIVE_SOURCES))


@pytest.mark.parametrize("source,minimum", [("mll23", 288), ("acevedo", 250)])
def test_physical_field_rejects_images_smaller_than_the_known_scale(source, minimum):
    with pytest.raises(ValueError, match="smaller"):
        release.preprocess_image(Image.new("RGB", (minimum - 1, 400)), source)


def test_generic_center_crop_keeps_legacy_rounding_without_padding():
    pixels = np.full((252, 255, 3), 100, dtype=np.uint8)
    pixels[:, 2] = (11, 22, 33)
    pixels[:, 253] = (44, 55, 66)
    image = release.prepare_image(Image.fromarray(pixels), "crop")
    assert image.size == (252, 252)
    np.testing.assert_array_equal(np.asarray(image)[:, 0], pixels[:, 2])
    np.testing.assert_array_equal(np.asarray(image)[:, -1], pixels[:, 253])


def test_normalization_accepts_grayscale_without_changing_channel_order():
    tensor = release.preprocess_image(Image.new("L", (252, 252), 255), "crop")
    assert tensor.shape == (3, 252, 252)
    expected = (torch.ones(3) - torch.tensor(release.IMAGENET_MEAN)) / torch.tensor(release.IMAGENET_STD)
    torch.testing.assert_close(tensor[:, 20, 20], expected)


def test_stage_is_reported_for_the_predicted_lineage_only():
    class Labels:
        shared_labels = release.SHARED_LABELS
        native_labels = NATIVE

    outputs = {
        "coarse": torch.tensor([0., 0., 0., 3., 0., 0., 0.]),
        "ne_stage": torch.tensor([1., 0.]),
        "ig_stage": torch.tensor([0., 1., 0.]),
        "native": {source: torch.tensor([0., 1.]) for source in release.NATIVE_SOURCES},
    }
    lymphocyte = release.describe_prediction(outputs, Labels(), "ku")
    assert lymphocyte["predicted_label"] == "lymphocytes"
    assert "stage" not in lymphocyte
    assert lymphocyte["native_head"]["predicted_label"] == "second"
    outputs["coarse"] = torch.tensor([0., 0., 0., 0., 0., 3., 0.])
    immature = release.describe_prediction(outputs, Labels())
    assert immature["stage"]["predicted_label"] == "myelocyte"
