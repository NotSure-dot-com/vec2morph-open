# VecToMorph Open

An offline inference edition of **VecToMorph Arm C v0.1.0-research**, a DINOv2 model fine-tuned on four public blood-cell microscopy datasets.

The repository contains the checkpoint, a Python loader, single-cell image preprocessing, an inference CLI and aggregate evaluation results. Python 3.11 or newer is required. The complete training and experiment pipeline is outside this inference edition.

This is a research and teaching model. Performance changes across acquisition systems and laboratories. It has no validated clinical operating threshold, calibrated diagnostic probabilities or reliable rejection of unfamiliar cells. The shared classifier always selects one of its seven classes, including for pathological or unrelated inputs.

## Quick start

Clone or download this repository. From its root directory, create an environment and install the requirements.

```sh
python -m venv .venv
```

Activate it with `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on Linux and macOS. Then run

```sh
python -m pip install -r requirements.txt
python scripts/predict_release.py cell.jpg --checkpoint model/vectomorph_arm_c_seed0.pth --source crop
```

The default is CPU inference in FP32. After dependencies are installed, inference requires no network connection or additional model download. For a supported CUDA installation, the original evaluation precision can be selected with `--device cuda --precision bfloat16`. The encoder then runs in BF16 and the heads run in FP32. Different hardware and precision can change decisions near a boundary.

The JSON output includes a predicted shared label, uncalibrated softmax scores and, for a predicted neutrophil or immature granulocyte, the corresponding stage-head output. Use `--output prediction.json` to save it.

## Images and preprocessing

Supply an image already centered on **one target cell**. The CLI does not find cells in whole-slide images, book pages or screenshots.

| `--source` | Crop recipe |
|---|---|
| `mll23` | Central 288-pixel square, bicubic sampling to 250 pixels, then 252 pixels |
| `acevedo` | Central 250-pixel square, then bicubic sampling to 252 pixels |
| `ku`, `univali`, `park`, `crop` | Central square using the shorter image side, then bicubic sampling to 252 pixels |

The MLL23 and Acevedo recipes represent a nominal common 25 µm field in the original source images. They only apply when the original acquisition scale has been preserved. An undersized image is rejected rather than padded. Other source options do not establish a physical scale. UNIVALI inputs are expected to have been cropped around an annotated target cell before this step.

All images are converted to RGB and normalized with ImageNet mean `(0.485, 0.456, 0.406)` and standard deviation `(0.229, 0.224, 0.225)`. No stain normalization or noise augmentation is applied during inference.

## Outputs

The shared head uses this fixed order

1. Neutrophils
2. Eosinophils
3. Basophils
4. Lymphocytes
5. Monocytes
6. Immature granulocytes
7. Erythroblasts

Two conditional heads distinguish band from segmented neutrophils and promyelocytes from myelocytes and metamyelocytes.

Source-specific heads preserve the original categories of Acevedo, KU, MLL23 and UNIVALI. To inspect one, add `--native-head mll23`, for example. Their full labels are listed in [model/model.json](model/model.json). These include blast and atypical-cell categories, but this release does not establish their diagnostic accuracy or cross-laboratory validity. The [post-release class-level audit](model/VALIDATION_AUDIT.md) adds native and conditional stage-head checks, with training contact and zero-support classes shown explicitly. Independent external validation of these heads remains open. A native head does not override the shared prediction.

## Training summary

The backbone is `vit_small_patch14_dinov2.lvd142m`, initialized from generic DINOv2 weights. Fine-tuning updated its last two transformer blocks and all linear heads. Features concatenate the CLS token and mean patch token into a 768-dimensional, L2-normalized vector.

| Setting | Value |
|---|---|
| Seed | 0 |
| Image size | 252 × 252 pixels |
| Epochs | 5 |
| Draws per epoch | 6,144, balanced to 1,536 per source |
| Total draws | 30,720 |
| Distinct sampled cells | 25,005 |
| Effective batch size | 32 |
| Optimizer | AdamW |
| Encoder / head learning rates | 0.00002 / 0.002 |
| Weight decay | 0.01 |
| Training augmentation | Eight right-angle rotations and reflections |

| Source | Eligible cells | Distinct cells sampled |
|---|---:|---:|
| MLL23 | 41,621 | 7,039 |
| Acevedo | 17,074 | 7,680 |
| KU-Optofil | 31,483 | 5,670 |
| UNIVALI published training split | 10,037 | 4,616 |

Sampling balanced sources and their original categories. The release uses the shared head's argmax without a KU-specific erythroblast cutoff. Dataset citations and licenses are in [SOURCES.md](SOURCES.md).

## Evaluation and limits

These results apply to the bundled checkpoint and its **shared head**. Macro-F1 averages only the six ground-truth classes represented in each evaluation subset.

| Evaluation | Cells | Accuracy | Macro-F1 | Missing ground-truth class |
|---|---:|---:|---:|---|
| Park, selected previously unexposed smears | 1,323 | 82.46% | 57.47% | Regular lymphocytes |
| UNIVALI, published internal test split | 979 | 96.63% | 81.11% | Erythroblasts |

Park was absent from release training. The selected 97 smears were also absent from earlier Park development probes. Those earlier probes had already exposed all smears containing regular lymphocytes, leaving no regular lymphocytes in this evaluation. Smear identifiers do not establish patient separation. Immature granulocytes account for 1,063 of 1,323 cells. Eosinophils number three and basophils five. All eight erythroblasts come from one smear. All eight were recognized, alongside eight erythroblast false positives.

UNIVALI is a training source. Its publisher test is an internal check, and augmented-image ancestry across its published splits is partly unresolved. It does not measure performance in a new laboratory.

The endpoints differ in source and class distribution. Their performance difference is consistent with domain sensitivity and does not isolate acquisition effects from case mix or annotation differences. Neither endpoint establishes complete seven-class external performance. Neither provides clinical validation. The class supports and confusion matrices are in [model/evaluation.json](model/evaluation.json).

For all original labels in the four prepared training-source datasets, see the [validation and coverage audit](model/VALIDATION_AUDIT.md). It distinguishes actually trained cells, retrospectively identified undrawn cells and the complete UNIVALI publisher test. The [aggregate audit JSON](model/validation_audit.json) includes per-class confusion matrices; this addendum uses the unchanged released checkpoint.

The [matched before/after comparison](model/FINETUNING_COMPARISON.md) reports frozen pretrained DINOv2 with trained heads alongside encoder fine-tuning with trained heads, including per-class F1 and changes in percentage points. These archived source-held-out recipe experiments use separate fold-specific checkpoints; their numbers are distinct from the released-checkpoint audit above. Our reporting convention keeps matched before/after results together and labels unavailable baselines explicitly.

The [generalization evidence overview](model/GENERALIZATION_EVIDENCE.md) separates measured encoder/source-breadth effects, missing controls and feature-mechanism hypotheses. It includes the one-source versus multi-source comparison and a short related-work check. Residual source sensitivity is observed; reliance on acquisition peculiarities instead of cell morphology has not been causally established.

The original release loader reproduced the archived Park confusion matrix on all 1,323 cells using CUDA BF16 encoder inference and FP32 heads. The open edition is checked separately for compatibility.

## Artifact integrity

The checkpoint is 86,882,533 bytes. The loader verifies its SHA-256 before deserialization with PyTorch's `weights_only=True`.

```text
790a90ef6ab8f17da146e0122f38acd161462bcb31638903c26666754d18c4f3  model/vectomorph_arm_c_seed0.pth
```

On Windows, verify it with `Get-FileHash model/vectomorph_arm_c_seed0.pth -Algorithm SHA256`. On Linux, use `sha256sum model/vectomorph_arm_c_seed0.pth`.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The contract tests cover checkpoint verification, restored heads, precision behavior, label order and crop/normalization rules. They use synthetic images and do not require downloading microscopy datasets.

## License and attribution

The code and fine-tuned checkpoint in this edition are offered under [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for DINOv2 and timm attribution, and [SOURCES.md](SOURCES.md) for the original image datasets and their separate licenses. Microscopy images are obtained from their original records and are not bundled here.
