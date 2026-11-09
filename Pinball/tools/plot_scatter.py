#!/usr/bin/env python3
"""Optional matplotlib figure from the deterministic scatter report."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('report',type=Path)
p.add_argument('--out',type=Path)
a=p.parse_args();r=json.loads(a.report.read_text())
out=a.out or a.report.with_suffix('.png')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,(flight,boards)=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1,1.6]})
cases=['passive_oblique','powered_typical_oblique','powered_max_oblique']
labels=['Passive wall','Bumper: board strength','Bumper: maximum allowed']
colors=['#126c91','#dd8155']
for i,(name,label) in enumerate([('current','Current'),('softer_powered','Half powered')]):
    values=[r['results'][name]['contacts'][k]['displacement_60_frames_px']['p95'] for k in cases]
    flight.barh([j+(i-.5)*.3 for j in range(3)],values,height=.28,color=colors[i],label=label)
flight.set_yticks(range(3),labels);flight.invert_yaxis()
flight.axvline(4,color='#b54942',linestyle='--',linewidth=1,label='Half ball diameter')
flight.set_xlabel('p95 displacement after 1 second (pixels)')
flight.set_title('Controlled oblique rebounds')
flight.legend(loc='lower right',frameon=False,fontsize=9)
rows=r['results']['current']['boards']
for i,(data,label) in enumerate([(rows,'Current vs scatter off'),(r['current_vs_softer_powered']['boards'],'Current vs half powered')]):
    vals=[b['duration']['percent'] for b in data]
    errors=[[v-b['duration']['ci95'][0] for b,v in zip(data,vals)],
            [b['duration']['ci95'][1]-v for b,v in zip(data,vals)]]
    boards.errorbar(vals,[j+(i-.5)*.24 for j in range(len(rows))],xerr=errors,
                    fmt='o',capsize=2,color=colors[i],label=label,markersize=4)
boards.set_yticks(range(len(rows)),[b['title'] for b in rows]);boards.invert_yaxis()
boards.axvline(0,color='#777',linewidth=1);boards.axvline(-15,color='#b54942',linestyle='--',linewidth=1)
boards.set_xlabel('Observed reactive session duration change (%)')
boards.set_title('Per-board duration: paired 95% bootstrap intervals')
boards.legend(loc='lower right',frameon=False,fontsize=9)
fig.suptitle('Pinball scatter: physical effect and gameplay impact',fontsize=16,x=.04,ha='left')
fig.text(.04,.015,f"{r['workload']['seeds']} fixed seeds per board / policy · {r['workload']['seconds']} s cap · 9 boards · survival is censored at the cap",fontsize=9,color='#555')
fig.tight_layout(rect=(0,.045,1,.95));fig.savefig(out,dpi=160,facecolor='white');print(out)
