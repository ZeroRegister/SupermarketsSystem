#!/usr/bin/env python3
"""Build quantitative figures and LaTeX tables directly from recorded evidence."""
from pathlib import Path
import json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parents[1]
b=json.loads((root/'docs/evidence/cache-benchmark.json').read_text())
results={}
for mode in ('cached','bypass'):
 samples=[s for r in b['records'] if r['mode']==mode for s in r['samples_ms']];ordered=sorted(samples)
 results[mode]={'n':len(samples),'median_ms':statistics.median(samples),'p95_ms':ordered[int((len(ordered)-1)*.95)],'p99_ms':ordered[int((len(ordered)-1)*.99)],'mean_ms':statistics.mean(samples)}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#35445d','text.color':'#24334b','xtick.color':'#65738a','ytick.color':'#65738a'})
fig,axes=plt.subplots(1,2,figsize=(9,3.7),gridspec_kw={'width_ratios':[1.05,1]})
modes=['cached','bypass'];positions=[0,1]
for offset,key,color,label in [(-.18,'median_ms','#5b73cc','Median'),(.18,'p95_ms','#6faa8c','95th percentile')]:
 vals=[results[m][key] for m in modes];bars=axes[0].bar([p+offset for p in positions],vals,width=.32,color=color,label=label)
 for bar,val in zip(bars,vals):axes[0].text(bar.get_x()+bar.get_width()/2,val+.15,f'{val:.2f}',ha='center',fontsize=9)
axes[0].set_xticks(positions,['Redis path','MySQL bypass']);axes[0].set_ylabel('HTTP latency (ms)');axes[0].set_ylim(0,max(results[m]['p95_ms'] for m in modes)*1.32);axes[0].legend(frameon=False,loc='upper left',fontsize=8);axes[0].grid(axis='y',alpha=.15);axes[0].set_axisbelow(True);axes[0].set_title('Aggregated local measurements',loc='left',fontsize=11)
for mode,color,label in [('cached','#5b73cc','Redis path'),('bypass','#6faa8c','MySQL bypass')]:
 ordered=sorted(s for r in b['records'] if r['mode']==mode for s in r['samples_ms']);axes[1].plot(ordered,[(i+1)/len(ordered) for i in range(len(ordered))],color=color,label=label,linewidth=1.8)
axes[1].set_xlabel('HTTP latency (ms)');axes[1].set_ylabel('Cumulative proportion');axes[1].set_ylim(0,1.02);axes[1].grid(alpha=.15);axes[1].legend(frameon=False,loc='lower right',fontsize=8);axes[1].set_title('Empirical latency distribution',loc='left',fontsize=11)
fig.tight_layout();fig.savefig(root/'thesis/figures/cache-latency.pdf',bbox_inches='tight');fig.savefig(root/'thesis/figures/cache-latency.png',dpi=200,bbox_inches='tight');plt.close(fig)
rows='\n'.join(f"{'Redis path' if m=='cached' else 'MySQL bypass'} & {results[m]['n']} & {results[m]['median_ms']:.2f} & {results[m]['p95_ms']:.2f} & {results[m]['p99_ms']:.2f} \\\\" for m in modes)
tex='''\\begin{table}[htbp]
\\centering\\small
\\caption{Authenticated warning-query latency on the recorded local workload. Each mode pools three alternating rounds; latencies are milliseconds.}
\\label{tab:latency}
\\begin{tabular}{lrrrr}\\toprule
Path & Samples & Median & p95 & p99 \\\\\\midrule
'''+rows+'''\n\\bottomrule\\end{tabular}
\\end{table}
'''
(root/'thesis/chapters/latency-table.tex').write_text(tex)
(root/'docs/evidence/benchmark-summary.json').write_text(json.dumps({'workload':b['workload'],'results':results},indent=2))
print(json.dumps(results,indent=2))
