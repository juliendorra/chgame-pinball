#!/usr/bin/env python3
"""Optional matplotlib figure for benchmark_spin.py (not a build dependency)."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--out',type=Path)
a=p.parse_args();r=json.loads(a.report.read_text());out=a.out or a.report.with_suffix('.png')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,(duration,score)=plt.subplots(1,2,figsize=(12,5.8))
names=['spin_light','spin','spin_grippy','hybrid','spin_no_memory']
labels=['Light spin (1/16 grip)','Spin (1/8 grip)','Strong spin (1/4 grip)',
        'Spin + powered scatter','Friction without spin history']
colors=['#16877e','#2673a3','#9d4663','#90612e','#777777']
for ax,field,title in [(duration,'paired_duration','Reactive session duration'),(score,'paired_score','Reactive score')]:
    for i,(name,color) in enumerate(zip(names,colors)):
        c=r['vs_current'][name]['policies']['reactive'][field];v=c['percent'];lo,hi=c['ci95']
        ax.errorbar([v],[i],xerr=[[max(0,v-lo)],[max(0,hi-v)]],fmt='o',color=color,capsize=4,markersize=6)
    ax.set_yticks(range(len(names)),labels if ax==duration else ['']*len(names));ax.invert_yaxis()
    ax.axvline(0,color='#999',lw=1);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    ax.set_xlabel('Change versus current model (%)');ax.set_title(title)
fig.suptitle('Contact spin: no consistent gain across the existing boards',x=.03,ha='left',fontsize=15)
fig.text(.03,.075,'Dots: paired changes · Bars: 95% seed-bootstrap intervals · Current = seeded angular scatter',fontsize=9,color='#444')
fig.text(.03,.035,f"9 boards · {r['workload']['seeds']} seeds per board/player · {r['workload']['seconds']} s cap (censored survival) · Scores do not measure human fun",fontsize=9,color='#444')
fig.tight_layout(rect=(0,.11,1,.92));fig.savefig(out,dpi=160,facecolor='white');print(out)
