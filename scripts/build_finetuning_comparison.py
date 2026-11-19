#!/usr/bin/env python
"""Render matched frozen-encoder versus fine-tuned-encoder study results."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

NAMES={'mll23':'MLL23','acevedo':'Acevedo','ku':'KU-Optofil','univali':'UNIVALI'}


def mean(values):
    return sum(values)/len(values)


def pct(value):
    return '—' if value is None else f'{100*value:.2f}%'


def pp(value):
    return '—' if value is None else f'{100*value:+.2f}'


def measure(matrix):
    assert len(matrix)==7 and all(len(row)==7 for row in matrix)
    assert all(type(n) is int and n>=0 for row in matrix for n in row)
    support=[sum(row) for row in matrix]
    calls=[sum(row[i] for row in matrix) for i in range(7)]
    f1=[2*matrix[i][i]/(support[i]+calls[i]) if support[i] else None for i in range(7)]
    return {'n':sum(support),'support':support,'f1':f1,
            'macro_f1':mean([v for v in f1 if v is not None]),
            'accuracy':sum(matrix[i][i] for i in range(7))/sum(support)}


def build(data):
    assert data['format']=='vectomorph.encoder-finetuning-comparison.v1'
    assert data['training']['seeds']==[0,1]
    assert data['training']['epochs']==5 and data['training']['draws_per_epoch']==6144
    assert data['training']['effective_batch']==32
    assert len(data['labels'])==7 and set(data['datasets'])==set(NAMES)
    results={}
    for source, fold in data['datasets'].items():
        pairs=[]
        assert [p['seed'] for p in fold['pairs']]==[0,1]
        for p in fold['pairs']:
            assert source not in p['training_sources']
            assert set(p['training_sources'])==set(NAMES)-{source}
            for key in ('training_schedule_sha256','test_case_and_label_sequence_sha256'):
                assert len(p[key])==64 and all(c in '0123456789abcdef' for c in p[key])
            before=measure(p['before']['confusion_matrix'])
            after=measure(p['after']['confusion_matrix'])
            assert before['support']==after['support']
            pairs.append((before,after))
        assert pairs[0][0]['support']==pairs[1][0]['support']
        results[source]={'pairs':pairs,'n':pairs[0][0]['n'],
                         'before':mean([a['macro_f1'] for a,b in pairs]),
                         'after':mean([b['macro_f1'] for a,b in pairs])}
    out=['# Encoder fine-tuning: matched before/after results','',
         '**Before** means generic pretrained DINOv2 kept frozen, with its linear heads trained. **After** means the same generic encoder initialization with its last two blocks and all heads jointly fine-tuned. Both conditions train their heads. This compares encoder updating, not training an image model from scratch.','',
         '**Scope:** these are archived source-held-out recipe experiments with separate checkpoints for each held-out source and seed. They are not the four-source release checkpoint evaluated before and after an update. Each target source was excluded from training in both conditions.','',
         '## Shared-head macro-F1','',
         'Values average seeds 0 and 1. Macro-F1 averages reference classes represented in each evaluation. UNIVALI is supplementary and has six represented shared classes; the other three have seven.','',
         '| Held-out target dataset | Test cells | Frozen pretrained encoder + trained heads | Fine-tuned encoder + trained heads | Change, percentage points |',
         '|---|---:|---:|---:|---:|']
    for source in ('mll23','acevedo','ku','univali'):
        r=results[source]
        out.append(f"| {NAMES[source]} | {r['n']} | {pct(r['before'])} | {pct(r['after'])} | {pp(r['after']-r['before'])} |")
    a=mean([results[s]['before'] for s in data['primary_sources']])
    c=mean([results[s]['after'] for s in data['primary_sources']])
    out += [f'| Equal-weight mean of the three primary targets | — | {pct(a)} | {pct(c)} | {pp(c-a)} |','',
            f"Under this fixed protocol, mean macro-F1 improved on {sum(r['after']>r['before'] for r in results.values())} of the {len(results)} evaluated targets; {sum(b['macro_f1']>a['macro_f1'] for r in results.values() for a,b in r['pairs'])} of the 8 paired seed comparisons improved. The class-level tables below retain individual-class decreases. This is a descriptive result from these cohorts and two seeds.",'',
            '## Individual paired runs','',
            '| Target | Seed | Frozen encoder macro-F1 | Fine-tuned encoder macro-F1 | Change, percentage points |',
            '|---|---:|---:|---:|---:|']
    for source in ('mll23','acevedo','ku','univali'):
        for seed,(before,after) in zip((0,1),results[source]['pairs']):
            out.append(f"| {NAMES[source]} | {seed} | {pct(before['macro_f1'])} | {pct(after['macro_f1'])} | {pp(after['macro_f1']-before['macro_f1'])} |")
    out += ['', '## Shared cell classes','',
            'Per-class F1 values average the two seeds. Each pair and both seeds use the same reference support. A dash marks a class with no reference examples.','']
    for source in ('mll23','acevedo','ku','univali'):
        r=results[source]
        out += [f'### {NAMES[source]}','',
                '| Reference class | Test cells | Frozen encoder F1 | Fine-tuned encoder F1 | Change, percentage points |',
                '|---|---:|---:|---:|---:|']
        for i,label in enumerate(data['labels']):
            n=r['pairs'][0][0]['support'][i]
            a=mean([x['f1'][i] for x,y in r['pairs']]) if n else None
            c=mean([y['f1'][i] for x,y in r['pairs']]) if n else None
            out.append(f'| {label} | {n} | {pct(a)} | {pct(c)} | {pp(c-a) if n else "—"} |')
        out.append('')
    out += ['## Matching and evidence limits','',
            '- Both conditions use the same initial generic DINOv2 backbone, image preprocessing, augmentation, training sources, draw schedule, seeds, head architecture and loss. Each run uses five epochs of 6,144 draws, an effective batch size of 32 and 960 optimizer steps. Equal draws do not imply equal compute cost.','',
            '- The archived checkpoint and prediction hashes were verified. For each of the eight pairs, test-row and reference-label arrays match exactly, as do training sources, sampled-cell count and the draw/orientation schedule hash. The exported file contains only confusion matrices and aggregate/hash provenance.','',
            '- MLL23 and Acevedo lack patient grouping in the prepared manifest. UNIVALI published split ancestry is partly unresolved. These estimates concern the documented cohorts. They do not isolate acquisition effects from case mix and annotation differences.','',
            '- The [released-checkpoint class audit](VALIDATION_AUDIT.md) covers different checkpoints and evaluation populations. Its 53 native source-label positions and the Park endpoint do not have a matched frozen-encoder baseline in this comparison. Missing comparisons remain unmeasured rather than being inferred from these fold-specific values.','',
            '## Reporting convention','',
            'Report frozen pretrained encoder + trained heads and fine-tuned encoder + trained heads side by side whenever the test cases, labels and training protocol are matched. Include support, seed(s), source exposure and the change in percentage points. Mark unavailable or mismatched baselines explicitly. Do not combine before/after values from different checkpoints, class sets or test populations.','',
            'The underlying matrices and provenance are in [finetuning_comparison.json](finetuning_comparison.json). Rebuild this report with','',
            '```sh','python scripts/build_finetuning_comparison.py','```','']
    return '\n'.join(out)


def main():
    root=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=root/'model/finetuning_comparison.json')
    p.add_argument('--output',type=Path,default=root/'model/FINETUNING_COMPARISON.md')
    args=p.parse_args()
    args.output.write_text(build(json.loads(args.input.read_text(encoding='utf-8'))),encoding='utf-8')
    print(f'Recomputed matched before/after metrics; wrote {args.output.name}')

if __name__=='__main__':
    main()
