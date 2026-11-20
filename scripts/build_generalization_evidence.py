#!/usr/bin/env python
"""Render measured transfer effects, untested hypotheses and research context."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from build_finetuning_comparison import measure,mean,pct,pp,NAMES


def build(data,reference,evaluation):
    assert data['format']=='vectomorph.generalization-evidence.v1'
    assert data['labels']==reference['labels']
    assert data['source_metrics_sha256']==reference['source_metrics_sha256']
    assert data['training']=={key:reference['training'][key] for key in data['training']}
    assert data['training']['seeds']==[0,1]
    assert evaluation['checkpoint_sha256']=='790a90ef6ab8f17da146e0122f38acd161462bcb31638903c26666754d18c4f3'
    results={}
    for source,fold in data['datasets'].items():
        assert [p['seed'] for p in fold['pairs']]==[0,1]
        runs=[]
        for p,ref in zip(fold['pairs'],reference['datasets'][source]['pairs']):
            assert p['seed']==ref['seed']
            assert p['test_case_and_label_sequence_sha256']==ref['test_case_and_label_sequence_sha256']
            row={key:measure(p[key]['confusion_matrix']) for key in ('frozen_multi','finetuned_single','finetuned_multi')}
            assert row['frozen_multi']['support']==row['finetuned_single']['support']==row['finetuned_multi']['support']
            for key,n in (('frozen_multi',3),('finetuned_single',1),('finetuned_multi',3)):
                assert len(p[key]['training_sources'])==n and source not in p[key]['training_sources']
            for key,old in (('frozen_multi','before'),('finetuned_multi','after')):
                for field in ('confusion_matrix','checkpoint_sha256','predictions_sha256'):
                    assert p[key][field]==ref[old][field]
                assert p[key]['training_schedule_sha256']==ref['training_schedule_sha256']
            runs.append(row)
        assert runs[0]['frozen_multi']['support']==runs[1]['frozen_multi']['support']
        results[source]={key:mean([r[key]['macro_f1'] for r in runs]) for key in runs[0]}
        results[source]['n']=runs[0]['frozen_multi']['n']
        assert fold['pairs'][0]['finetuned_single']['training_sources']==fold['pairs'][1]['finetuned_single']['training_sources']
        results[source]['single_source']=fold['pairs'][0]['finetuned_single']['training_sources'][0]
    primary={key:mean([results[s][key] for s in data['primary_sources']]) for key in ('frozen_multi','finetuned_single','finetuned_multi')}
    park=evaluation['park']
    out=['# Generalization: measured effects and open questions','',
         '## What the current experiments show','',
         'The evidence supports residual source sensitivity under this protocol. It does not identify which image features cause the remaining errors. A model can use useful cell morphology and source-associated cues at the same time. No causal demonstration that it relies on acquisition peculiarities instead of cell features was performed.','',
         '| Comparison | Measured evidence | Supported interpretation | Still open |',
         '|---|---|---|---|',
         f"| Encoder updating, A versus C | Primary-target mean macro-F1 {pct(primary['frozen_multi'])} → {pct(primary['finetuned_multi'])}; gains on all four targets in both seeds | Updating the last two encoder blocks improves transfer in these matched experiments | Which learned features account for the gain; whether other unseen sources behave similarly |",
         f"| Extra training sources with encoder fine-tuning, B versus C | Primary-target mean {pct(primary['finetuned_single'])} → {pct(primary['finetuned_multi'])}; two of four targets improve and two decline | Source breadth does not consistently improve target performance under this recipe | Effects of source choice, per-class sampling and training budget |",
         f"| Released four-source checkpoint on Park | {park['cells']} cells; macro-F1 {pct(park['macro_f1_on_represented_classes'])} over six represented classes | Transfer to this selected new-source cohort remains imperfect | Matched no-Park versus Park-adaptation comparison; patient grouping; complete class coverage |",
         '| More sources with a frozen encoder | Matched frozen-single-source control is absent | No isolated conclusion about source breadth without encoder updating | Complete the missing control |',
         '| Fine-tuning directly on the target source | Matched target-adaptation comparison is absent | Target-specific adaptation remains a hypothesis in this study | Compare with equal-budget continued training that excludes the target |',
         '| Imaging cues versus biological morphology | Not causally separated by these F1 tables | Domain sensitivity is observed; a shortcut mechanism is not established | Controlled feature and acquisition interventions |','',
         'A, B and C above refer to source-held-out recipe experiments with fold-specific checkpoints. The Park row refers to the final four-source release checkpoint and is a separate endpoint. Their numbers cannot be subtracted to estimate adaptation gains.','',
         '## Source breadth with encoder fine-tuning','',
         'Both conditions fine-tune the last two encoder blocks and train the heads. Each target source is excluded from both training conditions. Scores average seeds 0 and 1. UNIVALI is supplementary and has six represented shared classes; the other targets have seven.','',
         '| Held-out target | Single training source | Test cells | B: one source, macro-F1 | C: three sources, macro-F1 | C − B, percentage points |',
         '|---|---|---:|---:|---:|---:|']
    for source in ('mll23','acevedo','ku','univali'):
        r=results[source]
        out.append(f"| {NAMES[source]} | {NAMES[r['single_source']]} | {r['n']} | {pct(r['finetuned_single'])} | {pct(r['finetuned_multi'])} | {pp(r['finetuned_multi']-r['finetuned_single'])} |")
    out += [f"| Equal-weight mean of the three primary targets | — | — | {pct(primary['finetuned_single'])} | {pct(primary['finetuned_multi'])} | {pp(primary['finetuned_multi']-primary['finetuned_single'])} |",'',
            'This contrast holds the number of training draws and optimizer steps constant, not the class mixture or effective coverage of each source. Adding sources changes original-label granularity and source/class sampling composition. Only one designated single-source comparator was used per target. Thus the result concerns this source-breadth recipe and does not isolate acquisition style as the cause.','',
            '## The incomplete two-factor design','',
            'The numerical cells below are primary-target mean macro-F1, averaged over the three primary targets and two seeds.','',
            '| Encoder condition | One training source | Three training sources |',
            '|---|---|---|',
            f"| Frozen generic DINOv2, trained heads | Not measured as a matched arm | A: {pct(primary['frozen_multi'])} |",
            f"| Last two DINOv2 blocks and heads fine-tuned | B: {pct(primary['finetuned_single'])} | C: {pct(primary['finetuned_multi'])} |",'',
            'No pretraining was performed in this project. All arms start from the same generic pretrained DINOv2 backbone. The separately fitted heads are trained in every arm. Source-held-out means the target source was excluded from task training; it does not audit exposure in the upstream generic pretraining corpus.','',
            '## Hypotheses requiring additional experiments','',
            '1. **Target-source adaptation.** Reserve the target test population first. Compare fine-tuning on a disjoint target training population with equal-budget continued training on existing sources. Keep the shared labels, class balance and evaluation cases fixed where possible. Group by patient when IDs are usable, otherwise report the weaker grouping explicitly. All focal planes of one cell remain in one split.','',
            '2. **Source breadth without encoder updates.** Add the missing frozen-single-source arm, with the same source choice as B and matched training/evaluation protocol. Compare it with A to measure source breadth with a frozen encoder, and with B to measure encoder updating in the single-source condition.','',
            '3. **Feature mechanism.** Use validated cell/nucleus/background regions or controlled same-cell imaging pairs to distinguish acquisition sensitivity from morphological information. A source-prediction probe can detect residual source information, but that alone does not establish that the classification decision relies on it. Saliency maps or a performance drop alone are not a causal demonstration of shortcut use.','',
            '## Related work and novelty limits','',
            'The general problem is already established. [Tsutsui et al., 2023](https://arxiv.org/abs/2303.01777) benchmarked white-cell classification under changed imaging conditions and reported substantial cross-domain degradation in CNNs. Their architecture-specific findings should not be assumed to explain DINOv2.','',
            '[Chossegros et al., 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11648780/) trained EfficientNet on two source datasets and adapted it to eight target datasets with at most 100 labeled target images. Their ablation study attributes most of the improvement to fine-tuning, with a smaller contribution from color transformation. This directly overlaps the proposed target-adaptation question, although its model, metrics and protocol differ from ours.','',
            '[DinoBloom, Koch et al., 2024](https://arxiv.org/abs/2404.05022) investigates hematology-specific DINOv2 representation learning and external transfer. Our generic-backbone partial fine-tuning results cannot establish a limitation of such domain-specific pretraining or of vision models generally. Any future comparison needs a pretraining-source-overlap audit.','',
            '[Chossegros et al., 2026](https://doi.org/10.1016/j.eswa.2026.132710) studies biologically informed hierarchical supervision in DINOv2 and reports improvements on external datasets. Learning more biologically meaningful, transferable representations is therefore an active research area, rather than a new general problem identified by this project.','',
            'This was a targeted literature check, not a systematic novelty review. A possible contribution is a transparent, reproducible application benchmark and class-level evidence audit for this specific model and protocol. A causal account of residual source sensitivity and a controlled estimate of target-adaptation benefit remain open. We do not claim that no cell features were learned, that every new laboratory must fine-tune, or that source-invariant blood-cell representation is a newly discovered gap.','',
            '## Suggested study conclusion','',
            '> Encoder fine-tuning improved transfer in the source-held-out experiments, whereas increasing training-source breadth did not yield consistent gains across target cohorts. Residual source sensitivity remained under the tested protocol. The contributions of acquisition style, case mix and annotation granularity require controlled follow-up.','',
            'Numeric inputs and artifact provenance are in [generalization_evidence.json](generalization_evidence.json). The detailed A/C and class-level values are in [FINETUNING_COMPARISON.md](FINETUNING_COMPARISON.md); the final-checkpoint populations are in [VALIDATION_AUDIT.md](VALIDATION_AUDIT.md). From a current repository checkout containing the reporting tools, rebuild this overview with','',
            '```sh','python scripts/build_generalization_evidence.py','```','']
    return '\n'.join(out)


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=root/'model/GENERALIZATION_EVIDENCE.md')
    args=p.parse_args()
    data=json.loads((root/'model/generalization_evidence.json').read_text())
    reference=json.loads((root/'model/finetuning_comparison.json').read_text())
    evaluation=json.loads((root/'model/evaluation.json').read_text())
    args.output.write_text(build(data,reference,evaluation),encoding='utf-8')
    print(f'Recomputed source-breadth and encoder-update effects; wrote {args.output.name}')

if __name__=='__main__':main()