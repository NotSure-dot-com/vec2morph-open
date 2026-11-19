#!/usr/bin/env python
"""Render the aggregate-only audit for the fixed VecToMorph research release."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

NAMES = {'mll23': 'MLL23', 'acevedo': 'Acevedo', 'ku': 'KU-Optofil', 'univali': 'UNIVALI'}
SHA256 = '790a90ef6ab8f17da146e0122f38acd161462bcb31638903c26666754d18c4f3'


def pct(value):
    return '—' if value is None else f'{100 * value:.2f}%'


def validate_metrics(item):
    cm = item['confusion_matrix']
    labels = item['labels']
    assert len(cm) == len(labels)
    assert all(len(row) == len(labels) for row in cm)
    assert all(type(n) is int and n >= 0 for row in cm for n in row)
    support = [sum(row) for row in cm]
    calls = [sum(row[i] for row in cm) for i in range(len(labels))]
    assert sum(support) == item['cells']
    expected_f1 = []
    for i, row in enumerate(item['per_class']):
        assert row['label'] == labels[i]
        assert (row['n'], row['tp'], row['fp'], row['fn']) == (
            support[i], cm[i][i], calls[i]-cm[i][i], support[i]-cm[i][i])
        for key, expected in {
            'precision': cm[i][i]/calls[i] if calls[i] else None,
            'recall': cm[i][i]/support[i] if support[i] else None,
            'f1': 2*cm[i][i]/(support[i]+calls[i]) if support[i] else None,
        }.items():
            assert (row[key] is None and expected is None) or (
                row[key] is not None and expected is not None and abs(row[key]-expected)<1e-12)
        if row['n']:
            expected_f1.append(row['f1'])
    if item['cells']:
        assert abs(item['accuracy']-sum(cm[i][i] for i in range(len(labels)))/item['cells'])<1e-12
        assert abs(item['macro_f1']-sum(expected_f1)/len(expected_f1))<1e-12
    else:
        assert item['accuracy'] is None and item['macro_f1'] is None


def build(data):
    assert data['checkpoint_sha256'] == SHA256
    assert data['archived_univali_shared_confusion_matrix_equal'] is True
    assert sum(x['all_cells'] for x in data['datasets'].values()) == data['row_count'] == 101418
    assert sum(x['drawn_cells'] for x in data['datasets'].values()) == data['drawn_unique'] == 25005
    for dataset in data['datasets'].values():
        assert dataset['all_cells'] == dataset['eligible_cells'] + dataset['published_test_cells']
        assert dataset['eligible_cells'] == dataset['drawn_cells'] + dataset['not_drawn_cells']
        assert dataset['not_drawn_cells'] == dataset['not_drawn_image_unseen_cells'] + dataset['not_drawn_training_image_match_cells']
        assert sum(row['total'] for row in dataset['raw_label_inventory']) == dataset['all_cells']
        for field, expected in (('eligible', dataset['eligible_cells']), ('drawn', dataset['drawn_cells']),
                                ('unseen', dataset['not_drawn_image_unseen_cells']),
                                ('published_test', dataset['published_test_cells'])):
            assert sum(row[field] for row in dataset['raw_label_inventory']) == expected
        for cohort in dataset['cohorts'].values():
            assert cohort['heads']['native']['cells'] == cohort['cells']
            for head in cohort['heads'].values():
                validate_metrics(head)
    selected = {source: dataset['cohorts']['published_test' if source == 'univali' else 'pool_not_drawn_image_unseen']['heads']['native']
                for source, dataset in data['datasets'].items()}
    slots = sum(len(head['labels']) for head in selected.values())
    missing = sum(row['n'] == 0 for head in selected.values() for row in head['per_class'])
    atypical = next(row for row in selected['univali']['per_class'] if row['label'] == 'Linfocito atipico')
    reactive = next(row for row in selected['ku']['per_class'] if row['label'] == 'reactive_lymphocyte')
    out = [
        '# Validation and coverage audit — v0.1.0-research', '',
        f"Audit date {data['date']}. Fixed checkpoint SHA-256 `{SHA256}`.", '',
        'This post-release audit evaluates the existing checkpoint without retraining or changing thresholds. Reference labels are the original dataset annotations; agreement with those annotations does not establish clinical correctness.', '',
        '## Findings that affect interpretation', '',
        f"The selected internal evaluation populations represent {slots-missing} of {slots} source-specific label positions. {missing} have no reference examples in those populations. The tables retain every label and mark unsupported recall/F1 estimates explicitly.", '',
        f"In the UNIVALI publisher test, the native head recognizes {atypical['tp']} of {atypical['n']} atypical lymphocytes (recall {pct(atypical['recall'])}, precision {pct(atypical['precision'])}). In KU's post-hoc undrawn pool, it recognizes {reactive['tp']} of {reactive['n']} reactive lymphocytes (recall {pct(reactive['recall'])}, precision {pct(reactive['precision'])}). These measurements show that the high shared-head accuracy does not establish reliable recognition of the atypical or reactive subtypes.", '',
        'MLL23 reactive and neoplastic lymphocyte classes were entirely drawn during training; their undrawn audit populations are empty. Their generalization cannot be assessed from this residual pool.', '',
        '## Populations and independence', '',
        'The census covers all 101,418 retained annotated cells in the prepared four-source cache. The previously archived 1,323-cell Park evaluation is listed separately. This is not a claim that every image from every original dataset publication has been evaluated.', '',
        '| Dataset | Prepared cells | Eligible training pool | Actually drawn in training | Not drawn, no exact training-image match | Excluded undrawn cells sharing a training image | Publisher test |',
        '|---|---:|---:|---:|---:|---:|---:|',
    ]
    for source in ('mll23','acevedo','ku','univali'):
        d = data['datasets'][source]
        out.append(f"| {NAMES[source]} | {d['all_cells']} | {d['eligible_cells']} | {d['drawn_cells']} | {d['not_drawn_image_unseen_cells']} | {d['not_drawn_training_image_match_cells']} | {d['published_test_cells']} |")
    out += ['',
        '**MLL23, Acevedo and KU** below use retrospectively identified undrawn cells without an exact original-image hash match to the actually sampled training images. Their source was used in training, and this was not a prospectively reserved validation split. These are internal descriptive checks. No patient separation is available for MLL23 or Acevedo. KU group overlap is reported explicitly below.', '',
        'Class-balanced training exhausted some rare classes. The remaining undrawn pools therefore have altered class proportions, and some reference classes are absent. Their precision and aggregate scores describe these particular residual pools; they do not estimate performance at the original dataset prevalence or in clinical use.', '',
        '**UNIVALI** below uses the complete published test role, including original classes excluded from the seven-class endpoint. Exact-image training overlap was excluded, but ancestry of pre-augmented variants remains partly unresolved. This is an internal publisher test from a training source.', '',
        '**Park** remains the selected external six-class endpoint from 97 previously unexposed smears. It contains no regular lymphocyte ground truth, three eosinophils, five basophils and eight erythroblasts from one smear. Smear IDs do not establish patient separation.', '',
        'The reconstructed training-row and draw/orientation schedule hashes match the archived training protocol. All prepared cache hashes were checked. The manifest has no nonempty confirmed orientation-identity hashes; exact-image separation therefore does not establish independence from rotated, stained or other related variants.', '',
        '## Head-level results', '',
        '| Dataset / evaluation population | Shared cells | Shared classes represented | Shared accuracy | Shared macro-F1 | Native cells | Native classes represented | Native accuracy | Native macro-F1 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|',
    ]
    for source in ('mll23','acevedo','ku','univali'):
        d = data['datasets'][source]
        key = 'published_test' if source == 'univali' else 'pool_not_drawn_image_unseen'
        h = d['cohorts'][key]['heads']
        kind = 'publisher test' if source == 'univali' else 'post-hoc internal, undrawn'
        out.append(f"| {NAMES[source]} / {kind} | {h['coarse']['cells']} | {h['coarse']['represented_classes']}/7 | {pct(h['coarse']['accuracy'])} | {pct(h['coarse']['macro_f1'])} | {h['native']['cells']} | {h['native']['represented_classes']}/{len(h['native']['labels'])} | {pct(h['native']['accuracy'])} | {pct(h['native']['macro_f1'])} |")
    park = data['external_park']
    validate_metrics({'labels': park['labels'], 'cells': park['cells'], 'accuracy': park['accuracy'],
                      'macro_f1': park['macro_f1_on_represented_classes'],
                      'confusion_matrix': park['confusion_matrix'],
                      'per_class': [{'label': label, 'n': r['cells'], 'tp': r['true_positives'],
                                     'fp': r['false_positives'], 'fn': r['cells']-r['true_positives'],
                                     'precision': r['precision'], 'recall': r['recall'], 'f1': r['f1']}
                                    for label, r in park['per_class'].items()]})
    out.append(f"| Park / selected external smears | {park['cells']} | 6/7 | {pct(park['accuracy'])} | {pct(park['macro_f1_on_represented_classes'])} | — | — | — | — |")
    out += ['',
        'Shared metrics score only cells whose reference annotations map to the seven shared classes. Native metrics score every cell in the specified population using that source’s full original class list. They have different tasks and denominators. Macro-F1 averages classes with positive reference support. None of these scores are probabilities or measures of unfamiliar-cell rejection.', '',
        '## Counts and metrics by original cell class', '',
        '`Available` counts all prepared cells for that source, including its publisher test where present. `Drawn` counts distinct rows actually sampled in training. `Eval N` is the size of the evaluation population specified above. TP, FP and FN refer to the native source-specific head.', '',
        'Precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN). An em dash means not estimable. When Eval N is zero, recall and F1 are not estimated, even if the model calls that label on other classes. Very small Eval N gives little evidence about the class; cell-level confidence intervals are omitted because independence is not established.', '',
    ]
    for source in ('mll23','acevedo','ku','univali'):
        d = data['datasets'][source]
        key = 'published_test' if source == 'univali' else 'pool_not_drawn_image_unseen'
        c = d['cohorts'][key]
        out += [f'### {NAMES[source]}', '',
                f"Evaluation population {c['cells']} cells; exact training-image overlap {c['training_image_overlap_cells']} cells.", '']
        if source == 'ku':
            out += [f"The source contains {d['known_group_count']} known metadata groups and {d['unknown_group_count']} unknown group. {c['training_group_overlap_cells']} evaluation cells share a metadata group with training. This evaluation is not patient-held-out.", '']
        out += ['| Original label | Available | Drawn | Eval N | TP | FP | FN | Precision | Recall | F1 |',
                '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        inventory = {row['label']:row for row in d['raw_label_inventory']}
        for row in c['heads']['native']['per_class']:
            inv = inventory[row['label']]
            out.append(f"| {row['label']} | {inv['total']} | {inv['drawn']} | {row['n']} | {row['tp']} | {row['fp']} | {row['fn']} | {pct(row['precision'])} | {pct(row['recall'])} | {pct(row['f1'])} |")
        out += ['', 'Shared seven-class head in the same population', '',
                '| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |',
                '|---|---:|---:|---:|---:|---:|---:|---:|']
        for row in c['heads']['coarse']['per_class']:
            out.append(f"| {row['label']} | {row['n']} | {row['tp']} | {row['fp']} | {row['fn']} | {pct(row['precision'])} | {pct(row['recall'])} | {pct(row['f1'])} |")
        out += ['', 'Stage-head checks, conditioned on cells with a reference stage label', '',
                '| Head | Stage | Eval N | Direct stage-head recall | Recall including correct shared-head routing |',
                '|---|---|---:|---:|---:|']
        for head in ('ne_stage','ig_stage'):
            for row, routed in zip(c['heads'][head]['per_class'],c['heads'][head]['routed_recall']):
                assert row['label'] == routed['label'] and row['n'] == routed['n']
                assert 0 <= routed['correct'] <= row['tp'] <= row['n']
                assert (routed['recall'] is None and not row['n']) or (row['n'] and abs(routed['recall']-routed['correct']/row['n'])<1e-12)
                out.append(f"| {head} | {row['label']} | {row['n']} | {pct(row['recall'])} | {pct(routed['recall'])} |")
        out.append('')
    out += ['## Park shared-head class audit', '',
            '| Shared label | Eval N | TP | FP | FN | Precision | Recall | F1 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|']
    for label in park['labels']:
        r=park['per_class'][label]
        out.append(f"| {label} | {r['cells']} | {r['true_positives']} | {r['false_positives']} | {r['cells']-r['true_positives']} | {pct(r['precision'])} | {pct(r['recall'])} | {pct(r['f1'])} |")
    out += ['', '## Training-contact checks', '',
            'The following populations include cells actually sampled during fine-tuning. They are resubstitution checks and cannot support a validation claim. The aggregate JSON also retains complete class-level confusion matrices for these populations.', '',
            '| Dataset | Drawn cells | Native accuracy on drawn cells | Native macro-F1 on drawn cells | Entire eligible pool cells | Native accuracy on entire pool |',
            '|---|---:|---:|---:|---:|---:|']
    for source in ('mll23','acevedo','ku','univali'):
        d=data['datasets'][source]
        seen=d['cohorts']['training_drawn']['heads']['native']
        allpool=d['cohorts']['training_pool_all']['heads']['native']
        out.append(f"| {NAMES[source]} | {seen['cells']} | {pct(seen['accuracy'])} | {pct(seen['macro_f1'])} | {allpool['cells']} | {pct(allpool['accuracy'])} |")
    out += ['', '## Reproducibility and remaining gaps', '',
            'The checkpoint was frozen throughout. Inference used CUDA BF16 for the encoder and FP32 for all heads, batch size 32, fixed preprocessing and no test-time augmentation. The UNIVALI shared-head confusion matrix exactly reproduced the archived release endpoint. The Park table reuses the separately verified archived endpoint.', '',
            'All counts refer to retained annotations after the original preparation exclusions and deduplication. Multiple annotated cells from one original image can remain. The undrawn internal populations exclude exact original images sampled in training; this does not resolve all biological or augmentation relationships.', '',
            'A missing or zero-support class is an evidence gap. A trained label is not itself a validated capability. The undrawn source pools were not independent laboratory tests. This audit adds descriptive checks and does not convert the research prerelease into a clinically validated model.', '',
            'Aggregate counts, per-class metrics and confusion matrices are in [validation_audit.json](validation_audit.json). No images, individual predictions, patient IDs or sample paths are included. Render this report with', '',
            '```sh', 'python scripts/build_validation_audit.py', '```', '']
    return '\n'.join(out)


def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=root/'model/validation_audit.json')
    parser.add_argument('--output',type=Path,default=root/'model/VALIDATION_AUDIT.md')
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding='utf-8'))
    args.output.write_text(build(data),encoding='utf-8')
    print(f'Validated aggregate counts and metrics; wrote {args.output.name}')

if __name__=='__main__':
    main()
