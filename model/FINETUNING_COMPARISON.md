# Encoder fine-tuning: matched before/after results

**Before** means generic pretrained DINOv2 kept frozen, with its linear heads trained. **After** means the same generic encoder initialization with its last two blocks and all heads jointly fine-tuned. Both conditions train their heads. This compares encoder updating, not training an image model from scratch.

**Scope:** these are archived source-held-out recipe experiments with separate checkpoints for each held-out source and seed. They are not the four-source release checkpoint evaluated before and after an update. Each target source was excluded from training in both conditions.

## Shared-head macro-F1

Values average seeds 0 and 1. Macro-F1 averages reference classes represented in each evaluation. UNIVALI is supplementary and has six represented shared classes; the other three have seven.

| Held-out target dataset | Test cells | Frozen pretrained encoder + trained heads | Fine-tuned encoder + trained heads | Change, percentage points |
|---|---:|---:|---:|---:|
| MLL23 | 23009 | 43.27% | 73.16% | +29.89 |
| Acevedo | 14726 | 55.85% | 88.94% | +33.09 |
| KU-Optofil | 26608 | 47.74% | 78.50% | +30.76 |
| UNIVALI | 979 | 27.56% | 38.16% | +10.59 |
| Equal-weight mean of the three primary targets | — | 48.95% | 80.20% | +31.25 |

Under this fixed protocol, mean macro-F1 improved on 4 of the 4 evaluated targets; 8 of the 8 paired seed comparisons improved. The class-level tables below retain individual-class decreases. This is a descriptive result from these cohorts and two seeds.

## Individual paired runs

| Target | Seed | Frozen encoder macro-F1 | Fine-tuned encoder macro-F1 | Change, percentage points |
|---|---:|---:|---:|---:|
| MLL23 | 0 | 43.31% | 75.38% | +32.08 |
| MLL23 | 1 | 43.24% | 70.93% | +27.69 |
| Acevedo | 0 | 56.85% | 89.04% | +32.19 |
| Acevedo | 1 | 54.85% | 88.83% | +33.99 |
| KU-Optofil | 0 | 46.18% | 77.56% | +31.37 |
| KU-Optofil | 1 | 49.30% | 79.45% | +30.15 |
| UNIVALI | 0 | 30.70% | 38.22% | +7.52 |
| UNIVALI | 1 | 24.43% | 38.09% | +13.67 |

## Shared cell classes

Per-class F1 values average the two seeds. Each pair and both seeds use the same reference support. A dash marks a class with no reference examples.

### MLL23

| Reference class | Test cells | Frozen encoder F1 | Fine-tuned encoder F1 | Change, percentage points |
|---|---:|---:|---:|---:|
| neutrophils | 7857 | 66.74% | 92.96% | +26.22 |
| eosinophils | 2448 | 38.87% | 76.36% | +37.49 |
| basophils | 616 | 22.17% | 63.23% | +41.05 |
| lymphocytes | 5532 | 19.58% | 72.24% | +52.66 |
| monocytes | 2510 | 37.40% | 70.20% | +32.80 |
| immature_granulocytes | 1975 | 49.08% | 70.80% | +21.71 |
| erythroblasts | 2071 | 69.04% | 66.31% | -2.74 |

### Acevedo

| Reference class | Test cells | Frozen encoder F1 | Fine-tuned encoder F1 | Change, percentage points |
|---|---:|---:|---:|---:|
| neutrophils | 3328 | 62.79% | 93.64% | +30.85 |
| eosinophils | 3110 | 15.17% | 99.08% | +83.91 |
| basophils | 1212 | 67.44% | 93.18% | +25.74 |
| lymphocytes | 1214 | 49.90% | 90.76% | +40.86 |
| monocytes | 1419 | 58.27% | 77.95% | +19.68 |
| immature_granulocytes | 2892 | 66.90% | 76.83% | +9.93 |
| erythroblasts | 1551 | 70.45% | 91.10% | +20.65 |

### KU-Optofil

| Reference class | Test cells | Frozen encoder F1 | Fine-tuned encoder F1 | Change, percentage points |
|---|---:|---:|---:|---:|
| neutrophils | 16454 | 81.87% | 99.06% | +17.19 |
| eosinophils | 1862 | 38.89% | 99.16% | +60.26 |
| basophils | 546 | 62.62% | 98.58% | +35.96 |
| lymphocytes | 5762 | 68.14% | 86.73% | +18.60 |
| monocytes | 1381 | 52.28% | 82.05% | +29.77 |
| immature_granulocytes | 360 | 23.42% | 56.51% | +33.10 |
| erythroblasts | 243 | 6.98% | 27.42% | +20.44 |

### UNIVALI

| Reference class | Test cells | Frozen encoder F1 | Fine-tuned encoder F1 | Change, percentage points |
|---|---:|---:|---:|---:|
| neutrophils | 303 | 62.56% | 83.89% | +21.33 |
| eosinophils | 348 | 66.90% | 92.83% | +25.93 |
| basophils | 6 | 16.90% | 15.18% | -1.71 |
| lymphocytes | 281 | 0.35% | 5.70% | +5.35 |
| monocytes | 40 | 18.26% | 30.21% | +11.95 |
| immature_granulocytes | 1 | 0.41% | 1.13% | +0.72 |
| erythroblasts | 0 | — | — | — |

## Matching and evidence limits

- Both conditions use the same initial generic DINOv2 backbone, image preprocessing, augmentation, training sources, draw schedule, seeds, head architecture and loss. Each run uses five epochs of 6,144 draws, an effective batch size of 32 and 960 optimizer steps. Equal draws do not imply equal compute cost.

- The archived checkpoint and prediction hashes were verified. For each of the eight pairs, test-row and reference-label arrays match exactly, as do training sources, sampled-cell count and the draw/orientation schedule hash. The exported file contains only confusion matrices and aggregate/hash provenance.

- MLL23 and Acevedo lack patient grouping in the prepared manifest. UNIVALI published split ancestry is partly unresolved. These estimates concern the documented cohorts. They do not isolate acquisition effects from case mix and annotation differences.

- The [released-checkpoint class audit](VALIDATION_AUDIT.md) covers different checkpoints and evaluation populations. Its 53 native source-label positions and the Park endpoint do not have a matched frozen-encoder baseline in this comparison. Missing comparisons remain unmeasured rather than being inferred from these fold-specific values.

## Reporting convention

Report frozen pretrained encoder + trained heads and fine-tuned encoder + trained heads side by side whenever the test cases, labels and training protocol are matched. Include support, seed(s), source exposure and the change in percentage points. Mark unavailable or mismatched baselines explicitly. Do not combine before/after values from different checkpoints, class sets or test populations.

The underlying matrices and provenance are in [finetuning_comparison.json](finetuning_comparison.json). Rebuild this report with

```sh
python scripts/build_finetuning_comparison.py
```
