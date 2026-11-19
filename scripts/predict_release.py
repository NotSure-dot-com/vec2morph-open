#!/usr/bin/env python
# SPDX-License-Identifier: Apache-2.0
"""Classify prepared single-cell images with the Arm C research checkpoint."""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import sys

from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.release import (
    ARM_C_SHA256, IMAGE_SOURCES, NATIVE_SOURCES, describe_prediction, load_release, preprocess_image,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+", help="One or more prepared single-cell images")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--source", choices=IMAGE_SOURCES, required=True, help="Select the source crop recipe")
    parser.add_argument("--native-head", choices=NATIVE_SOURCES, help="Also report this source's original labels")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    parser.add_argument("--precision", choices=("float32", "bfloat16"), default="float32")
    parser.add_argument("--output", type=Path, help="Write the JSON report to this path")
    args = parser.parse_args()
    if args.precision == "bfloat16" and args.device != "cuda":
        parser.error("The BF16 replay mode requires --device cuda")
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("CUDA is unavailable in this Python environment")
    if args.precision == "bfloat16" and not torch.cuda.is_bf16_supported():
        parser.error("This CUDA device does not support BF16")
    torch.set_num_threads(4)
    classifier = load_release(args.checkpoint, args.device)
    predictions = []
    with torch.inference_mode():
        for path in args.images:
            with Image.open(path) as image:
                tensor = preprocess_image(image, args.source).unsqueeze(0).to(args.device)
            precision = torch.autocast("cuda", dtype=torch.bfloat16) if args.precision == "bfloat16" else nullcontext()
            with precision:
                output = classifier(tensor)
            single = {key: value[0] for key, value in output.items() if key != "native"}
            single["native"] = {source: value[0] for source, value in output["native"].items()}
            predictions.append({"image": str(path), **describe_prediction(single, classifier, args.native_head)})
    report = {
        "model": "VecToMorph Arm C v0.1.0-research",
        "checkpoint_sha256": ARM_C_SHA256,
        "source_recipe": args.source,
        "device": args.device,
        "precision": args.precision,
        "score_interpretation": "Softmax scores are uncalibrated model outputs",
        "predictions": predictions,
    }
    content = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(content, encoding="utf-8")
    else:
        print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
