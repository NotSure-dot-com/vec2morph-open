# Generalization: measured effects and open questions

## What the current experiments show

The evidence supports residual source sensitivity under this protocol. It does not identify which image features cause the remaining errors. A model can use useful cell morphology and source-associated cues at the same time. No causal demonstration that it relies on acquisition peculiarities instead of cell features was performed.

| Comparison | Measured evidence | Supported interpretation | Still open |
|---|---|---|---|
| Encoder updating, A versus C | Primary-target mean macro-F1 48.95% → 80.20%; gains on all four targets in both seeds | Updating the last two encoder blocks improves transfer in these matched experiments | Which learned features account for the gain; whether other unseen sources behave similarly |
| Extra training sources with encoder fine-tuning, B versus C | Primary-target mean 78.27% → 80.20%; two of four targets improve and two decline | Source breadth does not consistently improve target performance under this recipe | Effects of source choice, per-class sampling and training budget |
| Released four-source checkpoint on Park | 1323 cells; macro-F1 57.47% over six represented classes | Transfer to this selected new-source cohort remains imperfect | Matched no-Park versus Park-adaptation comparison; patient grouping; complete class coverage |
| More sources with a frozen encoder | Matched frozen-single-source control is absent | No isolated conclusion about source breadth without encoder updating | Complete the missing control |
| Fine-tuning directly on the target source | Matched target-adaptation comparison is absent | Target-specific adaptation remains a hypothesis in this study | Compare with equal-budget continued training that excludes the target |
| Imaging cues versus biological morphology | Not causally separated by these F1 tables | Domain sensitivity is observed; a shortcut mechanism is not established | Controlled feature and acquisition interventions |

A, B and C above refer to source-held-out recipe experiments with fold-specific checkpoints. The Park row refers to the final four-source release checkpoint and is a separate endpoint. Their numbers cannot be subtracted to estimate adaptation gains.

## Source breadth with encoder fine-tuning

Both conditions fine-tune the last two encoder blocks and train the heads. Each target source is excluded from both training conditions. Scores average seeds 0 and 1. UNIVALI is supplementary and has six represented shared classes; the other targets have seven.

| Held-out target | Single training source | Test cells | B: one source, macro-F1 | C: three sources, macro-F1 | C − B, percentage points |
|---|---|---:|---:|---:|---:|
| MLL23 | Acevedo | 23009 | 63.49% | 73.16% | +9.67 |
| Acevedo | MLL23 | 14726 | 86.48% | 88.94% | +2.46 |
| KU-Optofil | MLL23 | 26608 | 84.84% | 78.50% | -6.34 |
| UNIVALI | MLL23 | 979 | 46.06% | 38.16% | -7.90 |
| Equal-weight mean of the three primary targets | — | — | 78.27% | 80.20% | +1.93 |

This contrast holds the number of training draws and optimizer steps constant, not the class mixture or effective coverage of each source. Adding sources changes original-label granularity and source/class sampling composition. Only one designated single-source comparator was used per target. Thus the result concerns this source-breadth recipe and does not isolate acquisition style as the cause.

## The incomplete two-factor design

The numerical cells below are primary-target mean macro-F1, averaged over the three primary targets and two seeds.

| Encoder condition | One training source | Three training sources |
|---|---|---|
| Frozen generic DINOv2, trained heads | Not measured as a matched arm | A: 48.95% |
| Last two DINOv2 blocks and heads fine-tuned | B: 78.27% | C: 80.20% |

No pretraining was performed in this project. All arms start from the same generic pretrained DINOv2 backbone. The separately fitted heads are trained in every arm. Source-held-out means the target source was excluded from task training; it does not audit exposure in the upstream generic pretraining corpus.

## Hypotheses requiring additional experiments

1. **Target-source adaptation.** Reserve the target test population first. Compare fine-tuning on a disjoint target training population with equal-budget continued training on existing sources. Keep the shared labels, class balance and evaluation cases fixed where possible. Group by patient when IDs are usable, otherwise report the weaker grouping explicitly. All focal planes of one cell remain in one split.

2. **Source breadth without encoder updates.** Add the missing frozen-single-source arm, with the same source choice as B and matched training/evaluation protocol. Compare it with A to measure source breadth with a frozen encoder, and with B to measure encoder updating in the single-source condition.

3. **Feature mechanism.** Use validated cell/nucleus/background regions or controlled same-cell imaging pairs to distinguish acquisition sensitivity from morphological information. A source-prediction probe can detect residual source information, but that alone does not establish that the classification decision relies on it. Saliency maps or a performance drop alone are not a causal demonstration of shortcut use.

## Related work and novelty limits

The general problem is already established. [Tsutsui et al., 2023](https://arxiv.org/abs/2303.01777) benchmarked white-cell classification under changed imaging conditions and reported substantial cross-domain degradation in CNNs. Their architecture-specific findings should not be assumed to explain DINOv2.

[Chossegros et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11648780/) trained EfficientNet on two source datasets and adapted it to eight target datasets with at most 100 labeled target images. Their ablation study attributes most of the improvement to fine-tuning, with a smaller contribution from color transformation. This directly overlaps the proposed target-adaptation question, although its model, metrics and protocol differ from ours.

[DinoBloom, Koch et al., 2024](https://arxiv.org/abs/2404.05022) investigates hematology-specific DINOv2 representation learning and external transfer. Our generic-backbone partial fine-tuning results cannot establish a limitation of such domain-specific pretraining or of vision models generally. Any future comparison needs a pretraining-source-overlap audit.

[Chossegros et al., 2026](https://doi.org/10.1016/j.eswa.2026.132710) studies biologically informed hierarchical supervision in DINOv2 and reports improvements on external datasets. Learning more biologically meaningful, transferable representations is therefore an active research area, rather than a new general problem identified by this project.

This was a targeted literature check, not a systematic novelty review. A possible contribution is a transparent, reproducible application benchmark and class-level evidence audit for this specific model and protocol. A causal account of residual source sensitivity and a controlled estimate of target-adaptation benefit remain open. We do not claim that no cell features were learned, that every new laboratory must fine-tune, or that source-invariant blood-cell representation is a newly discovered gap.

## Suggested study conclusion

> Encoder fine-tuning improved transfer in the source-held-out experiments, whereas increasing training-source breadth did not yield consistent gains across target cohorts. Residual source sensitivity remained under the tested protocol. The contributions of acquisition style, case mix and annotation granularity require controlled follow-up.

Numeric inputs and artifact provenance are in [generalization_evidence.json](generalization_evidence.json). The detailed A/C and class-level values are in [FINETUNING_COMPARISON.md](FINETUNING_COMPARISON.md); the final-checkpoint populations are in [VALIDATION_AUDIT.md](VALIDATION_AUDIT.md). From a current repository checkout containing the reporting tools, rebuild this overview with

```sh
python scripts/build_generalization_evidence.py
```
