#!/usr/bin/env python3
"""Standalone plots derived from the repository's recorded benchmark samples."""
from pathlib import Path
import sys,json,statistics,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.runtime/paper-figure-deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'thesis/figure-assets';M=[]
b=json.loads((ROOT/'docs/evidence/cache-benchmark.json').read_text());samples={m:[x for r in b['records'] if r['mode']==m for x in r['samples_ms']] for m in ('cached','bypass')}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white'})
colors=['#3c648d','#8799ab'];labels=['Redis cache enabled','MySQL cache bypass'];date=b['timestamp_utc'][:10];work=b['workload'];note=f'Recorded {date} UTC · {work["products"]} products · concurrency {work["concurrency"]} · {len(samples["cached"])} samples per mode'
def save(id,title,fig):
 fig.text(.5,.015,note,ha='center',fontsize=9,color='#505860');fig.tight_layout(rect=[0,.055,1,1]);
 for ext in ('png','svg','pdf'):fig.savefig(OUT/'evidence'/f'{id}.{ext}',dpi=300,bbox_inches='tight')
 plt.close(fig);M.append(dict(id=id,title=title,chapter=5,type='benchmark-plot',source='docs/evidence/cache-benchmark.json',files=[f'evidence/{id}.{e}' for e in ('png','svg','pdf')],note='Historical local measurements, not a newly executed benchmark. '+note))
fig,ax=plt.subplots(figsize=(8.5,4.6));metrics=['Median','p95','p99'];results={}
for mode in samples:
 s=sorted(samples[mode]);results[mode]=[statistics.median(s),s[int((len(s)-1)*.95)],s[int((len(s)-1)*.99)]]
for i,mode in enumerate(samples):
 x=[j+(-.18 if i==0 else .18) for j in range(3)];bars=ax.bar(x,results[mode],.34,label=labels[i],color=colors[i])
 for bar,val in zip(bars,results[mode]):ax.text(bar.get_x()+bar.get_width()/2,val+.12,f'{val:.2f}',ha='center',fontsize=10)
ax.set_xticks(range(3),metrics);ax.set_ylabel('HTTP response latency (ms)');ax.set_ylim(0,max(max(v) for v in results.values())*1.25);ax.legend(frameon=False,loc='upper left');ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);save('04-latency-summary','Local warning-query latency summary',fig)
fig,ax=plt.subplots(figsize=(8.5,4.6))
for i,mode in enumerate(samples):
 s=sorted(samples[mode]);ax.plot(s,[(j+1)/len(s) for j in range(len(s))],color=colors[i],label=labels[i],linewidth=2)
ax.set_xlabel('HTTP response latency (ms)');ax.set_ylabel('Empirical cumulative probability');ax.legend(frameon=False,loc='lower right');ax.grid(alpha=.18);save('05-latency-ecdf','Empirical warning-query latency distribution',fig)
fig,ax=plt.subplots(figsize=(8.5,4.6));bars=ax.boxplot([samples[m] for m in samples],tick_labels=labels,patch_artist=True,showfliers=True,flierprops={'markersize':3,'alpha':.35})
for p,c in zip(bars['boxes'],colors):p.set_facecolor(c);p.set_alpha(.55)
ax.set_ylabel('HTTP response latency (ms)');ax.grid(axis='y',alpha=.18);save('06-latency-boxplot','Warning-query latency variability',fig)
for file in ['cache-benchmark.json','benchmark-summary.json','redis-recovery.json','persistence.json']:shutil.copy2(ROOT/'docs/evidence'/file,OUT/'sources'/file)
(OUT/'sources/plot-manifest.json').write_text(json.dumps(M,indent=2));print('Prepared',len(M),'plots from real recorded samples')
