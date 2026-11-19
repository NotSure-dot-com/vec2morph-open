# Validation and coverage audit — v0.1.0-research

Audit date 2026-11-19. Fixed checkpoint SHA-256 `790a90ef6ab8f17da146e0122f38acd161462bcb31638903c26666754d18c4f3`.

This post-release audit evaluates the existing checkpoint without retraining or changing thresholds. Reference labels are the original dataset annotations; agreement with those annotations does not establish clinical correctness.

## Findings that affect interpretation

The selected internal evaluation populations represent 41 of 53 source-specific label positions. 12 have no reference examples in those populations. The tables retain every label and mark unsupported recall/F1 estimates explicitly.

In the UNIVALI publisher test, the native head recognizes 11 of 46 atypical lymphocytes (recall 23.91%, precision 13.10%). In KU's post-hoc undrawn pool, it recognizes 308 of 448 reactive lymphocytes (recall 68.75%, precision 24.14%). These measurements show that the high shared-head accuracy does not establish reliable recognition of the atypical or reactive subtypes.

MLL23 reactive and neoplastic lymphocyte classes were entirely drawn during training; their undrawn audit populations are empty. Their generalization cannot be assessed from this residual pool.

## Populations and independence

The census covers all 101,418 retained annotated cells in the prepared four-source cache. The previously archived 1,323-cell Park evaluation is listed separately. This is not a claim that every image from every original dataset publication has been evaluated.

| Dataset | Prepared cells | Eligible training pool | Actually drawn in training | Not drawn, no exact training-image match | Excluded undrawn cells sharing a training image | Publisher test |
|---|---:|---:|---:|---:|---:|---:|
| MLL23 | 41621 | 41621 | 7039 | 34582 | 0 | 0 |
| Acevedo | 17074 | 17074 | 7680 | 9394 | 0 | 0 |
| KU-Optofil | 31483 | 31483 | 5670 | 25813 | 0 | 0 |
| UNIVALI | 11240 | 10037 | 4616 | 5110 | 311 | 1203 |

**MLL23, Acevedo and KU** below use retrospectively identified undrawn cells without an exact original-image hash match to the actually sampled training images. Their source was used in training, and this was not a prospectively reserved validation split. These are internal descriptive checks. No patient separation is available for MLL23 or Acevedo. KU group overlap is reported explicitly below.

Class-balanced training exhausted some rare classes. The remaining undrawn pools therefore have altered class proportions, and some reference classes are absent. Their precision and aggregate scores describe these particular residual pools; they do not estimate performance at the original dataset prevalence or in clinical use.

**UNIVALI** below uses the complete published test role, including original classes excluded from the seven-class endpoint. Exact-image training overlap was excluded, but ancestry of pre-augmented variants remains partly unresolved. This is an internal publisher test from a training source.

**Park** remains the selected external six-class endpoint from 97 previously unexposed smears. It contains no regular lymphocyte ground truth, three eosinophils, five basophils and eight erythroblasts from one smear. Smear IDs do not establish patient separation.

The reconstructed training-row and draw/orientation schedule hashes match the archived training protocol. All prepared cache hashes were checked. The manifest has no nonempty confirmed orientation-identity hashes; exact-image separation therefore does not establish independence from rotated, stained or other related variants.

## Head-level results

| Dataset / evaluation population | Shared cells | Shared classes represented | Shared accuracy | Shared macro-F1 | Native cells | Native classes represented | Native accuracy | Native macro-F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MLL23 / post-hoc internal, undrawn | 18742 | 7/7 | 93.90% | 89.24% | 34582 | 16/18 | 81.68% | 73.12% |
| Acevedo / post-hoc internal, undrawn | 8006 | 7/7 | 97.88% | 97.45% | 9394 | 8/8 | 98.20% | 97.97% |
| KU-Optofil / post-hoc internal, undrawn | 22897 | 4/7 | 98.81% | 97.21% | 25813 | 7/13 | 87.72% | 79.05% |
| UNIVALI / publisher test | 979 | 6/7 | 96.63% | 81.11% | 1203 | 10/14 | 75.31% | 58.65% |
| Park / selected external smears | 1323 | 6/7 | 82.46% | 57.47% | — | — | — | — |

Shared metrics score only cells whose reference annotations map to the seven shared classes. Native metrics score every cell in the specified population using that source’s full original class list. They have different tasks and denominators. Macro-F1 averages classes with positive reference support. None of these scores are probabilities or measures of unfamiliar-cell rejection.

## Counts and metrics by original cell class

`Available` counts all prepared cells for that source, including its publisher test where present. `Drawn` counts distinct rows actually sampled in training. `Eval N` is the size of the evaluation population specified above. TP, FP and FN refer to the native source-specific head.

Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). An em dash means not estimable. When Eval N is zero, recall and F1 are not estimated, even if the model calls that label on other classes. Very small Eval N gives little evidence about the class; cell-level confidence intervals are omitted because independence is not established.

### MLL23

Evaluation population 34582 cells; exact training-image overlap 0 cells.

| Original label | Available | Drawn | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basophil | 616 | 428 | 188 | 172 | 72 | 16 | 70.49% | 91.49% | 79.63% |
| eosinophil | 2448 | 425 | 2023 | 1938 | 51 | 85 | 97.44% | 95.80% | 96.61% |
| hairy_cell | 3265 | 427 | 2838 | 2724 | 251 | 114 | 91.56% | 95.98% | 93.72% |
| lymphocyte | 5532 | 427 | 5105 | 2804 | 305 | 2301 | 90.19% | 54.93% | 68.27% |
| lymphocyte_large_granular | 1849 | 427 | 1422 | 1123 | 751 | 299 | 59.93% | 78.97% | 68.14% |
| lymphocyte_neoplastic | 180 | 180 | 0 | 0 | 414 | 0 | 0.00% | — | — |
| lymphocyte_reactive | 33 | 33 | 0 | 0 | 724 | 0 | 0.00% | — | — |
| metamyelocyte | 483 | 425 | 58 | 49 | 234 | 9 | 17.31% | 84.48% | 28.74% |
| monocyte | 2510 | 427 | 2083 | 1511 | 145 | 572 | 91.24% | 72.54% | 80.82% |
| myeloblast | 8606 | 427 | 8179 | 6988 | 910 | 1191 | 88.48% | 85.44% | 86.93% |
| myelocyte | 747 | 428 | 319 | 155 | 69 | 164 | 69.20% | 48.59% | 57.09% |
| neutrophil_band | 687 | 426 | 261 | 200 | 885 | 61 | 18.43% | 76.63% | 29.72% |
| neutrophil_segmented | 7170 | 425 | 6745 | 5771 | 60 | 974 | 98.97% | 85.56% | 91.78% |
| normoblast | 2071 | 428 | 1643 | 1538 | 32 | 105 | 97.96% | 93.61% | 95.74% |
| plasma_cell | 1658 | 425 | 1233 | 1170 | 132 | 63 | 89.86% | 94.89% | 92.31% |
| promyelocyte | 745 | 428 | 317 | 208 | 241 | 109 | 46.33% | 65.62% | 54.31% |
| promyelocyte_atypical | 2033 | 427 | 1606 | 1366 | 645 | 240 | 67.93% | 85.06% | 75.53% |
| smudge_cell | 988 | 426 | 562 | 531 | 413 | 31 | 56.25% | 94.48% | 70.52% |

Shared seven-class head in the same population

| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutrophils | 7006 | 6799 | 191 | 207 | 97.27% | 97.05% | 97.16% |
| eosinophils | 2023 | 1968 | 61 | 55 | 96.99% | 97.28% | 97.14% |
| basophils | 188 | 170 | 78 | 18 | 68.55% | 90.43% | 77.98% |
| lymphocytes | 5105 | 4774 | 230 | 331 | 95.40% | 93.52% | 94.45% |
| monocytes | 2083 | 1634 | 108 | 449 | 93.80% | 78.44% | 85.44% |
| immature_granulocytes | 694 | 683 | 391 | 11 | 63.59% | 98.41% | 77.26% |
| erythroblasts | 1643 | 1571 | 84 | 72 | 94.92% | 95.62% | 95.27% |

Stage-head checks, conditioned on cells with a reference stage label

| Head | Stage | Eval N | Direct stage-head recall | Recall including correct shared-head routing |
|---|---|---:|---:|---:|
| ne_stage | band | 261 | 95.79% | 74.33% |
| ne_stage | segmented | 6745 | 84.09% | 82.85% |
| ig_stage | promyelocyte | 317 | 68.14% | 66.88% |
| ig_stage | myelocyte | 319 | 63.64% | 63.01% |
| ig_stage | metamyelocyte | 58 | 70.69% | 65.52% |

### Acevedo

Evaluation population 9394 cells; exact training-image overlap 0 cells.

| Original label | Available | Drawn | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| basophil | 1212 | 960 | 252 | 250 | 12 | 2 | 95.42% | 99.21% | 97.28% |
| eosinophil | 3110 | 960 | 2150 | 2147 | 1 | 3 | 99.95% | 99.86% | 99.91% |
| erythroblast | 1551 | 960 | 591 | 581 | 7 | 10 | 98.81% | 98.31% | 98.56% |
| ig | 2892 | 960 | 1932 | 1888 | 99 | 44 | 95.02% | 97.72% | 96.35% |
| lymphocyte | 1214 | 960 | 254 | 253 | 12 | 1 | 95.47% | 99.61% | 97.50% |
| monocyte | 1419 | 960 | 459 | 436 | 6 | 23 | 98.64% | 94.99% | 96.78% |
| neutrophil | 3328 | 960 | 2368 | 2284 | 29 | 84 | 98.75% | 96.45% | 97.59% |
| platelet | 2348 | 960 | 1388 | 1386 | 3 | 2 | 99.78% | 99.86% | 99.82% |

Shared seven-class head in the same population

| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutrophils | 2368 | 2299 | 39 | 69 | 98.33% | 97.09% | 97.71% |
| eosinophils | 2150 | 2148 | 2 | 2 | 99.91% | 99.91% | 99.91% |
| basophils | 252 | 249 | 12 | 3 | 95.40% | 98.81% | 97.08% |
| lymphocytes | 254 | 253 | 16 | 1 | 94.05% | 99.61% | 96.75% |
| monocytes | 459 | 432 | 8 | 27 | 98.18% | 94.12% | 96.11% |
| immature_granulocytes | 1932 | 1879 | 87 | 53 | 95.57% | 97.26% | 96.41% |
| erythroblasts | 591 | 576 | 6 | 15 | 98.97% | 97.46% | 98.21% |

Stage-head checks, conditioned on cells with a reference stage label

| Head | Stage | Eval N | Direct stage-head recall | Recall including correct shared-head routing |
|---|---|---:|---:|---:|
| ne_stage | band | 0 | — | — |
| ne_stage | segmented | 0 | — | — |
| ig_stage | promyelocyte | 0 | — | — |
| ig_stage | myelocyte | 0 | — | — |
| ig_stage | metamyelocyte | 0 | — | — |

### KU-Optofil

Evaluation population 25813 cells; exact training-image overlap 0 cells.

The source contains 275 known metadata groups and 1 unknown group. 25801 evaluation cells share a metadata group with training. This evaluation is not patient-held-out.

| Original label | Available | Drawn | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| band_neutrophil | 199 | 199 | 0 | 0 | 1553 | 0 | 0.00% | — | — |
| basophil | 546 | 546 | 0 | 0 | 4 | 0 | 0.00% | — | — |
| blast | 814 | 591 | 223 | 217 | 432 | 6 | 33.44% | 97.31% | 49.77% |
| eosinophil | 1862 | 591 | 1271 | 1270 | 8 | 1 | 99.37% | 99.92% | 99.65% |
| erythroblast | 243 | 243 | 0 | 0 | 28 | 0 | 0.00% | — | — |
| giant_platelet | 2835 | 590 | 2245 | 2205 | 11 | 40 | 99.50% | 98.22% | 98.86% |
| lymphocyte | 5762 | 590 | 5172 | 3894 | 56 | 1278 | 98.58% | 75.29% | 85.38% |
| metamyelocyte | 262 | 262 | 0 | 0 | 53 | 0 | 0.00% | — | — |
| monocyte | 1381 | 592 | 789 | 652 | 20 | 137 | 97.02% | 82.64% | 89.25% |
| myelocyte | 98 | 98 | 0 | 0 | 13 | 0 | 0.00% | — | — |
| platelet_cluster | 188 | 188 | 0 | 0 | 19 | 0 | 0.00% | — | — |
| reactive_lymphocyte | 1038 | 590 | 448 | 308 | 968 | 140 | 24.14% | 68.75% | 35.73% |
| segmented_neutrophil | 16255 | 590 | 15665 | 14096 | 6 | 1569 | 99.96% | 89.98% | 94.71% |

Shared seven-class head in the same population

| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutrophils | 15665 | 15635 | 23 | 30 | 99.85% | 99.81% | 99.83% |
| eosinophils | 1271 | 1270 | 9 | 1 | 99.30% | 99.92% | 99.61% |
| basophils | 0 | 0 | 5 | 0 | 0.00% | — | — |
| lymphocytes | 5172 | 5047 | 19 | 125 | 99.62% | 97.58% | 98.59% |
| monocytes | 789 | 673 | 20 | 116 | 97.11% | 85.30% | 90.82% |
| immature_granulocytes | 0 | 0 | 152 | 0 | 0.00% | — | — |
| erythroblasts | 0 | 0 | 44 | 0 | 0.00% | — | — |

Stage-head checks, conditioned on cells with a reference stage label

| Head | Stage | Eval N | Direct stage-head recall | Recall including correct shared-head routing |
|---|---|---:|---:|---:|
| ne_stage | band | 0 | — | — |
| ne_stage | segmented | 15665 | 90.60% | 90.53% |
| ig_stage | promyelocyte | 0 | — | — |
| ig_stage | myelocyte | 0 | — | — |
| ig_stage | metamyelocyte | 0 | — | — |

### UNIVALI

Evaluation population 1203 cells; exact training-image overlap 0 cells.

| Original label | Available | Drawn | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Artefato | 132 | 100 | 32 | 21 | 43 | 11 | 32.81% | 65.62% | 43.75% |
| Basofilo | 22 | 16 | 6 | 6 | 0 | 0 | 100.00% | 100.00% | 100.00% |
| Bastonete | 770 | 547 | 22 | 11 | 71 | 11 | 13.41% | 50.00% | 21.15% |
| Blasto | 272 | 272 | 0 | 0 | 3 | 0 | 0.00% | — | — |
| Eosinofilo | 492 | 144 | 348 | 337 | 5 | 11 | 98.54% | 96.84% | 97.68% |
| Eritroblasto | 44 | 44 | 0 | 0 | 2 | 0 | 0.00% | — | — |
| Linfocito | 2608 | 548 | 281 | 188 | 7 | 93 | 96.41% | 66.90% | 78.99% |
| Linfocito atipico | 566 | 520 | 46 | 11 | 73 | 35 | 13.10% | 23.91% | 16.92% |
| Metamielocito | 416 | 415 | 1 | 1 | 10 | 0 | 9.09% | 100.00% | 16.67% |
| Mielocito | 249 | 249 | 0 | 0 | 5 | 0 | 0.00% | — | — |
| Monocito | 533 | 493 | 40 | 26 | 18 | 14 | 59.09% | 65.00% | 61.90% |
| Neutrofilo segmentado | 4270 | 548 | 281 | 211 | 18 | 70 | 92.14% | 75.09% | 82.75% |
| Promielocito | 214 | 214 | 0 | 0 | 0 | 0 | — | — | — |
| Restos celulares | 652 | 506 | 146 | 94 | 42 | 52 | 69.12% | 64.38% | 66.67% |

Shared seven-class head in the same population

| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutrophils | 303 | 302 | 12 | 1 | 96.18% | 99.67% | 97.89% |
| eosinophils | 348 | 338 | 0 | 10 | 100.00% | 97.13% | 98.54% |
| basophils | 6 | 6 | 1 | 0 | 85.71% | 100.00% | 92.31% |
| lymphocytes | 281 | 268 | 2 | 13 | 99.26% | 95.37% | 97.28% |
| monocytes | 40 | 31 | 11 | 9 | 73.81% | 77.50% | 75.61% |
| immature_granulocytes | 1 | 1 | 6 | 0 | 14.29% | 100.00% | 25.00% |
| erythroblasts | 0 | 0 | 1 | 0 | 0.00% | — | — |

Stage-head checks, conditioned on cells with a reference stage label

| Head | Stage | Eval N | Direct stage-head recall | Recall including correct shared-head routing |
|---|---|---:|---:|---:|
| ne_stage | band | 22 | 54.55% | 50.00% |
| ne_stage | segmented | 281 | 86.48% | 86.48% |
| ig_stage | promyelocyte | 0 | — | — |
| ig_stage | myelocyte | 0 | — | — |
| ig_stage | metamyelocyte | 1 | 100.00% | 100.00% |

## Park shared-head class audit

| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutrophils | 179 | 169 | 79 | 10 | 68.15% | 94.41% | 79.16% |
| eosinophils | 3 | 1 | 6 | 2 | 14.29% | 33.33% | 20.00% |
| basophils | 5 | 2 | 2 | 3 | 50.00% | 40.00% | 44.44% |
| lymphocytes | 0 | 0 | 61 | 0 | 0.00% | — | — |
| monocytes | 65 | 31 | 40 | 34 | 43.66% | 47.69% | 45.59% |
| immature_granulocytes | 1063 | 880 | 36 | 183 | 96.07% | 82.78% | 88.93% |
| erythroblasts | 8 | 8 | 8 | 0 | 50.00% | 100.00% | 66.67% |

## Training-contact checks

The following populations include cells actually sampled during fine-tuning. They are resubstitution checks and cannot support a validation claim. The aggregate JSON also retains complete class-level confusion matrices for these populations.

| Dataset | Drawn cells | Native accuracy on drawn cells | Native macro-F1 on drawn cells | Entire eligible pool cells | Native accuracy on entire pool |
|---|---:|---:|---:|---:|---:|
| MLL23 | 7039 | 82.58% | 80.56% | 41621 | 81.84% |
| Acevedo | 7680 | 98.42% | 98.43% | 17074 | 98.30% |
| KU-Optofil | 5670 | 87.23% | 83.70% | 31483 | 87.63% |
| UNIVALI | 4616 | 83.21% | 85.17% | 10037 | 79.69% |

## Reproducibility and remaining gaps

The checkpoint was frozen throughout. Inference used CUDA BF16 for the encoder and FP32 for all heads, batch size 32, fixed preprocessing and no test-time augmentation. The UNIVALI shared-head confusion matrix exactly reproduced the archived release endpoint. The Park table reuses the separately verified archived endpoint.

All counts refer to retained annotations after the original preparation exclusions and deduplication. Multiple annotated cells from one original image can remain. The undrawn internal populations exclude exact original images sampled in training; this does not resolve all biological or augmentation relationships.

A missing or zero-support class is an evidence gap. A trained label is not itself a validated capability. The undrawn source pools were not independent laboratory tests. This audit adds descriptive checks and does not convert the research prerelease into a clinically validated model.

Aggregate counts, per-class metrics and confusion matrices are in [validation_audit.json](validation_audit.json). No images, individual predictions, patient IDs or sample paths are included. Render this report with

```sh
python scripts/build_validation_audit.py
```
