#!/usr/bin/env python3
"""Repeatable contact/flight experiments and paired full-board scatter playtests.

Run from any directory. No device, serial port, renderer or wall-clock timing is
involved. Compile-time ablations use the shared Studio engine build recipe.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics as st
import subprocess
import sys

from build_studio import GAME, ROOT, WORK, engine_inputs, inputs
from boards import encode

BASELINE = GAME / 'docs/scatter-baseline.json'
FIELDS = ('frames', 'score', 'lives', 'coverage', 'types', 'stalled', 'drought',
          'fast', 'ramps', 'flips', 'searches', 'banks', 'lanes', 'multiballs')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def percentile(values, p):
    a = sorted(values)
    at = (len(a)-1)*p
    lo = math.floor(at)
    return a[lo] + (a[min(lo+1, len(a)-1)]-a[lo])*(at-lo)


def distribution(values):
    return {k: round(v, 6) for k, v in dict(mean=st.mean(values), median=st.median(values),
             p95=percentile(values, .95), maximum=max(values)).items()}


def paired_change(rows, reference, field):
    # Resample seed clusters; each sampled seed retains all nine boards.
    by_seed = defaultdict(lambda: [0, 0])
    for key, r in rows.items():
        by_seed[r['seed']][0] += r[field]
        by_seed[r['seed']][1] += reference[key][field]
    pairs = list(by_seed.values())
    def change(p):
        a, b = map(sum, zip(*p))
        return (a/b-1)*100 if b else 0
    rng = random.Random(0xB0057)
    boot = [change([pairs[rng.randrange(len(pairs))] for _ in pairs]) for _ in range(2000)]
    return dict(percent=round(change(pairs), 3), ci95=[round(percentile(boot, p), 3) for p in (.025, .975)])


def analyse(records, boards, reference_name='off', scatter_invariants=True):
    baseline = records[reference_name]
    ref_shots = {(r['powered'], r['vx'], r['speed'], r['kick'], r['seed']): r for r in baseline if r['kind']=='shot'}
    ref_games = {(r['board'], r['seed'], r['policy']): r for r in baseline if r['kind']=='game'}
    result = {}
    for name, data in records.items():
        shots = [r for r in data if r['kind']=='shot']
        game_rows = {(r['board'], r['seed'], r['policy']): r for r in data if r['kind']=='game'}
        assert game_rows.keys() == ref_games.keys()
        soft = next(r for r in data if r['kind']=='soft')
        assert soft['rng']==12345
        if scatter_invariants:assert soft == next(r for r in baseline if r['kind']=='soft')
        entry = dict(config=data[0], contacts={}, policies={}, boards=[])
        for powered, label, kick in ((0, 'passive', None), (1, 'powered', None), (1, 'powered_typical', 280), (1, 'powered_max', 1600)):
            for normal, geometry in ((True, 'normal'), (False, 'oblique')):
                cases = [r for r in shots if r['powered']==powered and (r['vx']==0)==normal and (kick is None or r['kick']==kick)]
                angles, changed, near, far, displaced = [], [], [], [], []
                for r in cases:
                    ref = ref_shots[(r['powered'],r['vx'],r['speed'],r['kick'],r['seed'])]
                    a, b = r['samples'][0], ref['samples'][0]
                    if scatter_invariants:assert a[4] != r['seed'], 'contact fixture must actually sample scatter'
                    assert all(s[4]==a[4] for s in r['samples']), 'secondary contact invalidates isolated flight'
                    angles.append(abs(math.degrees(math.atan2(a[2]*b[3]-a[3]*b[2],a[2]*b[2]+a[3]*b[3]))))
                    changed.append(a[2:4]!=b[2:4])
                    distances = [math.hypot(x[0]-y[0],x[1]-y[1])/256 for x,y in zip(r['samples'],ref['samples'])]
                    near.append(distances[1]);far.append(distances[-1]);displaced.append(max(distances))
                entry['contacts'][label+'_'+geometry] = dict(samples=len(cases),
                    changed_velocity_percent=round(100*st.mean(changed), 3), angle_degrees=distribution(angles),
                    displacement_15_frames_px=distribution(near), displacement_60_frames_px=distribution(far),
                    maximum_sampled_displacement_px=distribution(displaced),
                    half_ball_displacement_percent=round(100*st.mean(d>=4 for d in displaced), 3))
        for policy in ('fixed', 'reactive'):
            rows = {k:r for k,r in game_rows.items() if r['policy']==policy}
            path_changes, first_divergences = [], []
            for key, r in rows.items():
                ref = ref_games[key]
                if policy=='fixed': assert r['input_hash']==ref['input_hash']
                first = None
                for i in range(0, min(len(r['path']),len(ref['path'])), 3):
                    a,b=r['path'][i:i+3],ref['path'][i:i+3]
                    if a[2] and b[2] and math.hypot(a[0]-b[0],a[1]-b[1])>=8*256:
                        first=i//3;break
                path_changes.append(first is not None)
                if first is not None:first_divergences.append(first)
            total_frames=sum(r['frames'] for r in rows.values())
            entry['policies'][policy] = dict(games=len(rows),
                changed_outcome_percent=round(100*st.mean(any(r[f]!=ref_games[k][f] for f in ('score','frames','lives')) for k,r in rows.items()),3),
                one_ball_path_divergence_percent=round(100*st.mean(path_changes),3),
                median_seconds_to_path_divergence=st.median(first_divergences) if first_divergences else None,
                mean_seconds=round(total_frames/len(rows)/60,3),
                time_limit_percent=round(100*st.mean(not r['over'] for r in rows.values()),3),
                life_losses_per_minute=round(sum(3-r['lives'] for r in rows.values())*3600/total_frames,4),
                mean_score=round(st.mean(r['score'] for r in rows.values()),3),
                score_per_minute=round(sum(r['score'] for r in rows.values())*3600/total_frames,3),
                paired_duration=paired_change(rows,ref_games,'frames'),
                paired_score=paired_change(rows,ref_games,'score'),
                metrics={f:round(st.mean(r[f] for r in rows.values()),4) for f in FIELDS if f not in ('frames','score')})
        for b in boards:
            rows={k:r for k,r in game_rows.items() if r['board']==b['id'] and r['policy']=='reactive'}
            entry['boards'].append(dict(title=b['title'],duration=paired_change(rows,ref_games,'frames'),
                score=paired_change(rows,ref_games,'score')))
        result[name]=entry
    return result


def markdown(report):
    lines=['# Scatter gameplay benchmark','',
        'Shared integer solver, fixed seed corpora, 60 Hz, all nine boards. Each native run is repeated byte for byte.', '',
        'Flight fixtures hit a real horizontal wall or powered bumper on frame one, then sample an unobstructed second of flight. Bumpers use typical 280 and maximum-valid 1600 kick strengths. '
        'Normal and oblique shots are separate because integer friction can erase small sideways impulses.', '',
        '| Configuration | Passive p95 flight shift, normal / oblique | Powered oblique p95 flight shift, typical / maximum kick | Fixed-input games with ≥1 ball-diameter route change | Reactive duration Δ (95% CI) | Reactive score Δ (95% CI) |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for name,r in report['results'].items():
        def flight(kind):
            keys=[kind+'_'+g for g in ('normal','oblique')] if kind=='passive' else ['powered_typical_oblique','powered_max_oblique']
            return ' / '.join(f"{r['contacts'][k]['displacement_60_frames_px']['p95']:.3f}" for k in keys)+' px'
        def ci(metric):
            c=r['policies']['reactive'][metric];return f"{c['percent']:+.1f}% [{c['ci95'][0]:+.1f}, {c['ci95'][1]:+.1f}]"
        lines.append(f"| {name} | {flight('passive')} | {flight('powered')} | {r['policies']['fixed']['one_ball_path_divergence_percent']:.1f}% | {ci('paired_duration')} | {ci('paired_score')} |")
    lines+=['', '## Angle-only controls', '',
        'These comparisons preserve the same conservative cosine and contact sampling, while setting the sine to zero in the control. This separates angular variation from constant speed loss.', '',
        '| Angles enabled | Fixed-input ball-diameter route changes | Fixed-input outcome changes |',
        '| --- | ---: | ---: |']
    for name,r in report['angular_controls'].items():
        p=r['policies']['fixed'];lines.append(f"| {name} | {p['one_ball_path_divergence_percent']:.1f}% | {p['changed_outcome_percent']:.1f}% |")
    lines+=['', '## Current settings by board', '',
        'Point estimates with 95% seed-bootstrap intervals. Current versus half-strength powered scatter keeps passive and eject scatter unchanged. Local regressions remain visible even when the aggregate improves.', '',
        '| Board | Duration vs off | Score vs off | Duration vs half powered | Score vs half powered |',
        '| --- | ---: | ---: | ---: | ---: |']
    contrast=report['current_vs_softer_powered']['boards']
    def value(c):return f"{c['percent']:+.1f}% [{c['ci95'][0]:+.1f}, {c['ci95'][1]:+.1f}]"
    for b,c in zip(report['results']['current']['boards'],contrast):
        lines.append(f"| {b['title']} | {value(b['duration'])} | {value(b['score'])} | {value(c['duration'])} | {value(c['score'])} |")
    lines+=['','## Interpretation'  ,'',*report['findings'],'','## Repeat and compare','',
        '```sh','python3 Pinball/tools/benchmark_scatter.py --check','python3 Pinball/tools/benchmark_scatter.py --record-baseline','```','',
        '`--check` fails on changed measurements, workload or hard invariants. Review the new JSON/Markdown report before deliberately recording a new baseline. '
        'Reports include per-board effects, seed-cluster bootstrap intervals and raw trial hashes. Full raw trials are kept beside the report.', '',
        'The fixed-input player uses the exact same complete button tape in every configuration. The reactive player sees the changed ball path and responds; '
        'its seed/timing policy stays fixed, but its button tape necessarily changes. Route divergence compares the common active portion of the first ball, '
        'sampled once per second; it is not a frame-perfect collision or multiball metric.', '',
        'The intervals describe variation over the fixed seed cohort, retaining all nine boards in each resampled seed cluster. '
        'Games still alive at the limit are censored: duration here means observed capped session time, not an estimate of uncapped lifetime. '
        'Automated players and these diagnostic thresholds do not establish human fun or physical button feel.', '',
        'Quantitative review thresholds are design choices: a 4 px shift is half the ball diameter; a 15% loss of observed reactive duration '
        'or 20% score loss merits review. Confidence intervals crossing those thresholds are inconclusive. '
        'A tiny one-second displacement can still change later contacts in a chaotic table; both local and full-session effects are reported.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=32)
    parser.add_argument('--seconds',type=int,default=120)
    parser.add_argument('--shot-seeds',type=int,default=512)
    parser.add_argument('--out',type=Path,default=GAME/'out/scatter-benchmark')
    parser.add_argument('--baseline',type=Path,default=BASELINE)
    mode=parser.add_mutually_exclusive_group();mode.add_argument('--check',action='store_true');mode.add_argument('--record-baseline',action='store_true')
    args=parser.parse_args()
    if not 2<=args.seeds<=256 or not 10<=args.seconds<=300 or not 16<=args.shot_seeds<=4096:
        parser.error('use 2..256 seeds, 10..300 seconds and 16..4096 shot seeds')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    WORK.mkdir(parents=True,exist_ok=True)
    flags,sources,_=engine_inputs()
    before=inputs()
    # Saved study's historical scatter-only reference, independent of defaults.
    current=dict(passive=4,powered=16,eject=8)
    configs={'off':dict(passive=0,powered=0,eject=0),
             'passive_only':dict(passive=current['passive'],powered=0,eject=0),
             'powered_only':dict(passive=0,powered=current['powered'],eject=0),
             'current':current,
             'softer_powered':dict(current,powered=max(2,current['powered']//2) if current['powered'] else 0),
             'stronger_passive':dict(current,passive=min(16,current['passive']*2))}
    for c in configs.values():c['angle_zero']=0
    configs.update(passive_damping_only=dict(configs['passive_only'],angle_zero=1),
                   powered_damping_only=dict(configs['powered_only'],angle_zero=1),
                   zero_angles=dict(current,angle_zero=1))
    boards=json.loads((GAME/'boards/tables.json').read_text());paths=[]
    for b in boards:
        p=out/(b['file']+'.pbt');p.write_bytes(encode(b));paths.append(p)
    compiler=os.environ.get('CXX','clang++');bench=GAME/'tools/wasm/scatter_bench.cpp'
    # Compile only Physics.cpp per configuration; everything else is identical.
    objects=[]
    for i,src in enumerate(sources):
        if src.name=='Physics.cpp':continue
        obj=out/f'common-{i}.o';key=digest([before,flags,str(src)])
        stamp=obj.with_suffix('.sha256')
        if not obj.exists() or not stamp.exists() or stamp.read_text()!=key:
            subprocess.run([compiler,*flags,'-c',str(src),'-o',str(obj)],check=True,cwd=ROOT)
            stamp.write_text(key)
        objects.append(obj)
    def build(item):
        name,config=item;obj=out/(name+'.o');exe=out/name
        # This study's 'current' label is the historical scatter-only control,
        # independent of the shipping light-spin configuration.
        defines=['-DPINBALL_SPIN_GRIP=0','-DPINBALL_SPIN_FORGET=0']+[
            f'-DPINBALL_SCATTER_{k.upper()}={v}' for k,v in config.items() if k!='angle_zero' or v]
        subprocess.run([compiler,*flags,*defines,'-c',str(GAME/'Physics.cpp'),'-o',str(obj)],check=True,cwd=ROOT)
        # The benchmark's config banner must use the same defines as Physics.cpp.
        probe=out/(name+'-probe.o')
        subprocess.run([compiler,*flags,*defines,'-c',str(bench),'-o',str(probe)],check=True,cwd=ROOT)
        common=objects
        subprocess.run([compiler,*map(str,common),str(obj),str(probe),'-o',str(exe)],check=True,cwd=ROOT)
        return exe
    with ThreadPoolExecutor(max_workers=3) as pool:executables=list(pool.map(build,configs.items()))
    records={};hashes={}
    for (name,config),exe in zip(configs.items(),executables):
        command=[str(exe),str(args.seeds),str(args.seconds*60),str(args.shot_seeds),*map(str,paths)]
        first=subprocess.check_output(command,cwd=ROOT);second=subprocess.check_output(command,cwd=ROOT)
        if first!=second:raise SystemExit(f'{name}: non-repeatable native measurements')
        (out/(name+'.jsonl')).write_bytes(first);hashes[name]=hashlib.sha256(first).hexdigest()
        records[name]=[json.loads(line) for line in first.splitlines()]
        assert records[name][0]==dict(kind='config',**config),records[name][0]
        print(f'{name}: {len(records[name])} records, exact repeat passed',flush=True)
    if before!=inputs():raise SystemExit('Sources changed during benchmark; rerun for consistent measurements.')
    results=analyse(records,boards)
    angular={}
    for candidate,control in [('passive_only','passive_damping_only'),('powered_only','powered_damping_only'),('current','zero_angles')]:
        angular[candidate]=analyse({control:records[control],candidate:records[candidate]},boards,control)[candidate]
    contrast=analyse({'softer_powered':records['softer_powered'],'current':records['current']},boards,'softer_powered')['current']
    findings=[]
    passive=results['passive_only']['policies']['fixed'];current_result=results['current']
    findings.append(f"Passive-only scatter changes a ball-diameter route in {passive['one_ball_path_divergence_percent']:.1f}% of fixed-input games and changes score/lives/duration in {passive['changed_outcome_percent']:.1f}%.")
    p95=max(current_result['contacts'][kind+'_'+g]['displacement_60_frames_px']['p95'] for kind in ('powered_typical','powered_max') for g in ('normal','oblique'))
    findings.append(f"With the same conservative speed loss in the control, passive angles alone change ball-diameter routes in {angular['passive_only']['policies']['fixed']['one_ball_path_divergence_percent']:.1f}% of games and outcomes in {angular['passive_only']['policies']['fixed']['changed_outcome_percent']:.1f}%.")
    findings.append(f"Powered scatter's largest fixture p95 displacement after one second is {p95:.3f} px, against a 4 px half-ball review threshold.")
    for kind in ('powered_typical','powered_max'):
        shift=max(current_result['contacts'][kind+'_'+g]['displacement_60_frames_px']['p95'] for g in ('normal','oblique'))
        findings.append(f"{kind}: worst geometry's p95 one-second shift is {shift:.3f} px.")
    for b in current_result['boards']:
        if b['duration']['percent'] < -15 or b['score']['percent'] < -20:
            findings.append(f"Review {b['title']}: duration {b['duration']['percent']:+.1f}%, score {b['score']['percent']:+.1f}% versus scatter off; see per-board confidence intervals and the half-power comparison.")
    duration=current_result['policies']['reactive']['paired_duration'];score=current_result['policies']['reactive']['paired_score']
    for label,value,threshold in [('reactive duration',duration,-15),('reactive score',score,-20)]:
        status='within the review threshold' if value['ci95'][0]>threshold else 'past the review threshold' if value['ci95'][1]<threshold else 'inconclusive at the review threshold'
        findings.append(f"Current {label}: {value['percent']:+.1f}% (95% CI {value['ci95'][0]:+.1f} to {value['ci95'][1]:+.1f}%), {status} ({threshold:+d}%).")
    report=dict(schema=1,workload=dict(seeds=args.seeds,seconds=args.seconds,shot_seeds=args.shot_seeds,
        physics_seed_stream='xorshift32: 0xA11CE517',shot_seed_stream='xorshift32: 0x51A77E12',
        bootstrap_seed=0xB0057,bootstrap_replicates=2000,board_hash=digest(boards)),
        configs=configs,angular_controls=angular,current_vs_softer_powered=contrast,source_hash=digest(before),raw_sha256=hashes,results=results,findings=findings,
        compiler=subprocess.check_output([compiler,'--version'],text=True).splitlines()[0])
    baseline=None
    if args.baseline.exists():
        baseline=json.loads(args.baseline.read_text())
        report['baseline_comparison']=dict(same_workload=baseline['workload']==report['workload'],
            same_current_measurements=baseline['raw_sha256']['current']==hashes['current'],
            same_measurements=baseline['raw_sha256']==hashes,
            previous_config=baseline['configs']['current'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'report.md').write_text(markdown(report))
    print('\n'.join(findings));print(out/'report.md')
    if args.record_baseline:
        args.baseline.write_text(json.dumps(report,indent=2)+'\n');print('Recorded baseline:',args.baseline)
    elif args.check and (baseline is None or not all(report['baseline_comparison'][k] for k in ('same_workload','same_measurements'))):
        raise SystemExit('Scatter measurements changed or baseline missing. Review report before recording a new baseline.')


if __name__=='__main__':main()
