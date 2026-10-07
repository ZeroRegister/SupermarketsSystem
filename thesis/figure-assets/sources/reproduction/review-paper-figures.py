#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,html,zipfile,subprocess,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'thesis/figure-assets'
items=[]
for f in ['diagram-manifest.json','ui-manifest.json','code-manifest.json','plot-manifest.json']:items.extend(json.loads((OUT/'sources'/f).read_text()))
for n,item in enumerate(items,1):
 item['assetNumber']=n;png=next(f for f in item['files'] if f.endswith('.png'));im=Image.open(OUT/png);im.verify();im=Image.open(OUT/png);item['pixels']=[im.width,im.height];item['layoutHint']='Full width or landscape' if im.width/im.height>1.7 else ('Narrow figure / side-by-side' if im.height/im.width>1.8 else 'Portrait page, full text width');item['pngSha256']=hashlib.sha256((OUT/png).read_bytes()).hexdigest()
 for f in item['files']:
  if not (OUT/f).is_file() or (OUT/f).stat().st_size==0:raise ValueError('Missing figure file: '+f)
 if item['type']=='code':
  source=(ROOT/item['source']).read_text();assert hashlib.sha256(source.encode()).hexdigest()==item['sourceSha256']
  expected='\n'.join(source.splitlines()[item['startLine']-1:item['endLine']])+'\n'
  assert (OUT/'sources'/f"{item['id']}.txt").read_text()==expected
 if item['type']=='diagram':
  import xml.etree.ElementTree as E
  tree=E.parse(OUT/item['files'][0]);cells=tree.findall('.//mxCell');ids={c.get('id') for c in cells}
  for c in cells:
   if c.get('edge')=='1':
    assert c.find('mxGeometry') is not None
    for k in ['source','target']:
     if c.get(k):assert c.get(k) in ids
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',18)
for offset in range(0,len(items),12):
 batch=items[offset:offset+12];sheet=Image.new('RGB',(1600,1320),'#e9ebed');draw=ImageDraw.Draw(sheet)
 for j,it in enumerate(batch):
  f=next(x for x in it['files'] if x.endswith('.png'));im=Image.open(OUT/f).convert('RGB');im.thumbnail((510,275));x=(j%3)*530+10;y=(j//3)*330+10;sheet.paste(im,(x+(510-im.width)//2,y+35+(275-im.height)//2));draw.text((x,y),f"{it['assetNumber']:02}  {it['id']}",font=font,fill='#202a33')
 sheet.save(OUT/'review'/f'contact-{offset//12+1}.jpg',quality=92)
(OUT/'manifest.json').write_text(json.dumps({'language':'English','reference':'docs/_MasterThesiseExample.docx','scope':'Revised thesis figures; see thesis/reference-aligned/review for review history','gitRevision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'figures':items},indent=2))
rows=[]
for it in items:
 png=next(f for f in it['files'] if f.endswith('.png'));extras=' · '.join(f'<a href="{html.escape(f)}">{Path(f).suffix[1:].upper()}</a>' for f in it['files'] if not f.endswith('.png'))
 rows.append(f'<article id="asset-{it["assetNumber"]}" data-type="{it["type"]}"><div class="label">Asset {it["assetNumber"]:02} · Suggested chapter {it["chapter"]} · {html.escape(it["type"])}</div><h2>{html.escape(it["title"])}</h2><a href="{png}"><img loading="lazy" src="{png}" alt="{html.escape(it["title"])}"></a><p>{extras}</p><p class="note">{html.escape(it.get("note", ""))}</p><details><summary>Source and provenance</summary><pre>{html.escape(json.dumps({k:v for k,v in it.items() if k not in ['files']},indent=2))}</pre></details></article>')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Shelfwise thesis figure collection</title><style>body{font:16px/1.6 Arial,sans-serif;margin:0;background:#f4f5f6;color:#202a33}header{padding:32px max(24px,calc((100% - 1100px)/2));background:white;border-bottom:1px solid #ddd}h1{font-size:28px;margin:0}nav{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}button{padding:8px 14px;border:1px solid #bbb;background:white;border-radius:4px;cursor:pointer}main{max-width:1100px;margin:24px auto;padding:0 20px}article{background:white;margin:0 0 28px;padding:24px;border:1px solid #dce0e4}h2{font-size:21px;margin:5px 0 20px}.label,.note{font-size:14px;color:#596571}img{max-width:100%;max-height:750px;display:block;margin:auto;object-fit:contain}a{color:#2a5883}pre{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}</style><header><h1>Shelfwise thesis figure collection</h1><p>Editable diagrams, captured application screens, exact source excerpts and recorded test evidence.</p><p>Phone screenshots show the responsive Web interface. Performance plots use the explicitly dated historical benchmark.</p><nav><button onclick="filter('all')">All figures</button><button onclick="filter('diagram')">Diagrams</button><button onclick="filter('ui')">UI captures</button><button onclick="filter('code')">Code excerpts</button><button onclick="filter('evidence')">Test evidence</button></nav></header><main>'''+''.join(rows)+'''</main><script>function filter(t){document.querySelectorAll('article').forEach(a=>a.hidden=t!=='all'&&(t==='evidence'?!['test-result','benchmark-plot'].includes(a.dataset.type):a.dataset.type!==t))}</script></html>'''
(OUT/'index.html').write_text(page)
counts={}
for i in items:counts[i['type']]=counts.get(i['type'],0)+1
lines=['# Shelfwise 论文插图素材','',f'共 {len(items)} 幅图。图号为素材编号，正式论文排版时再按章节编号。英文标签，与现有系统界面一致。','',f'分类数量：{counts}','', '本目录仅收集插图，未修改论文正文。','', '## 使用方式','', f'- `diagrams/`：{counts.get("diagram",0)} 幅可编辑 draw.io 图，同时提供 SVG 矢量图和高分辨率 PNG。','- `ui/`：从 localhost 上实际运行的系统截取；包括完整页面、表单、角色视图和响应式手机页面。','- `code/`：源码片段的排版截图，保留原文件名、原行号；HTML 和 sources 中的文本可复核。','- `evidence/`：本次真实测试结果截图，及仓库已有原始性能样本绘制的图。','- `index.html`：可按类型筛选的完整图册。','- `manifest.json`：来源、建议章节、尺寸、时间和 SHA-256。','- `review/`：缩略联系表，用于整体检查。','', '## 数据与范围','', '- 手机图是响应式 Web，不代表开发了原生 App。','- 截图使用已有演示数据；表单截图仅打开和填写草稿，不提交库存、账户或目录改动。','- 测试结果来自 2026-10-07 执行：后端 Testcontainers 集成测试 45 项，前端 Vitest 测试 3 项。30 张 UI 捕获记录为 2026-10-06 UTC，详见 sources/ui-verification.json。','- 性能图来自 docs/evidence/cache-benchmark.json 的历史测试，原始记录日期为 2026-10-03 UTC；16 商品、并发 1、每模式 600 样本。没有把这些数据冒充本次测试。','- 类图、权限图、数据库关系依据当前源码。固定角色没有继承关系；Redis 是可选预警缓存。','- 代码图只做显示换行和语法着色，不改写源码。','', '## 全部素材','', '| 编号 | 建议章节 | 类型 | 图题与 PNG |','|---|---:|---|---|']
for i in items:
 png=next(f for f in i['files'] if f.endswith('.png'));lines.append(f"| {i['assetNumber']:02} | {i['chapter']} | {i['type']} | [{i['title']}]({png}) |")
(OUT/'README.md').write_text('\n'.join(lines)+'\n')
# A compact overview for quick review, with the full images available in the gallery.
preview=Image.new('RGB',(1600,1120),'#edf0f2');pd=ImageDraw.Draw(preview)
for j,(file,label) in enumerate([('diagrams/02-uc-catalogue.png','UML use case'),('diagrams/11-er-overall.png','Database relationships'),('ui/02-dashboard.png','Running Web application'),('code/02-code-stock-transaction.png','Actual source excerpt')]):
 im=Image.open(OUT/file).convert('RGB');im.thumbnail((760,480));x=(j%2)*800+20;y=(j//2)*560+20;pd.text((x,y),label,font=font,fill='#202a33');preview.paste(im,(x+(760-im.width)//2,y+45+(480-im.height)//2))
preview.save(OUT/'preview.png')
repro=OUT/'sources/reproduction';repro.mkdir(exist_ok=True)
for f in ['prepare-paper-diagrams.py','layout_paper_diagrams.py','capture-paper-ui.mjs','prepare-paper-code.py','prepare-paper-plots.py','render-paper-images.mjs','review-paper-figures.py','paper-figure-requirements.txt']:shutil.copy2(ROOT/'scripts'/f,repro/f)
with (OUT/'README.md').open('a') as f:f.write("\n## 再生成\n\n脚本位于仓库 scripts/，打包副本位于 sources/reproduction/。使用 workspace dependency loader 给出的 Python 和 Node 可执行文件。先用 Python 的 pip 将 scripts/paper-figure-requirements.txt 安装到 .runtime/paper-figure-deps；本机 draw.io CLI 用于 SVG 和 PNG 导出。\n\n顺序：运行 prepare-paper-diagrams.py；启动已有应用后运行 capture-paper-ui.mjs；运行现有后端与前端测试并保存日志到 sources；运行 prepare-paper-code.py 与 prepare-paper-plots.py；运行 render-paper-images.mjs；最后运行 review-paper-figures.py 更新图册和压缩包。后端 Testcontainers 使用当前 Colima socket：DOCKER_HOST=unix:///Users/fch/.colima/default/docker.sock。\n")
zipfile_path=ROOT/'dist/shelfwise-paper-figures.zip'
with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED) as z:
 for p in OUT.rglob('*'):
  if p.is_file():z.write(p,Path('shelfwise-paper-figures')/p.relative_to(OUT))
print(json.dumps({'figures':len(items),'counts':counts,'zip':str(zipfile_path)},indent=2))
