#!/usr/bin/env python3
"""Render exact source excerpts with syntax highlighting and original line numbers."""
from pathlib import Path
import sys,json,html,hashlib,re,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.runtime/paper-figure-deps'))
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'thesis/figure-assets';CODE=OUT/'code';CODE.mkdir(exist_ok=True);M=[]
fmt=HtmlFormatter(nowrap=True,style='friendly');css=fmt.get_style_defs('.syntax')
def excerpt(id,title,file,start,end,lexer='java',chapter=4):
 text=(ROOT/file).read_text();lines=text.splitlines();end=min(end,len(lines));picked=lines[start-1:end]
 body=[]
 for no,line in enumerate(picked,start):body.append(f'<div class="row"><span class="number">{no}</span><pre class="syntax">{highlight(line,get_lexer_by_name(lexer),fmt).rstrip()}</pre></div>')
 raw='\n'.join(picked)+'\n';(OUT/'sources'/f'{id}.txt').write_text(raw)
 doc=f'''<!doctype html><meta charset="utf-8"><style>{css}
 *{{box-sizing:border-box}}html,body{{margin:0;background:#fff;color:#17202a}}body{{font-family:Arial,sans-serif;width:1000px}}
 header{{padding:20px 24px 18px;border-bottom:1px solid #d7dce1;font-size:18px;background:#f6f7f8}}header b{{display:block;margin-bottom:8px}}header small{{font-size:13px;color:#56616c}}
 main{{padding:20px 18px 24px}}.row{{display:flex;align-items:flex-start;min-height:32px}}.number{{width:50px;flex:none;text-align:right;padding-right:14px;font:16px/32px Menlo,monospace;color:#84909c;user-select:none}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;flex:1;font:21px/32px Menlo,Consolas,monospace;font-variant-ligatures:none}}.row:nth-child(even){{background:#fbfcfd}}
 </style><header><b>{html.escape(title)}</b><small>{html.escape(file)} · original lines {start}–{end}</small></header><main>{''.join(body)}</main>'''
 (CODE/f'{id}.html').write_text(doc)
 M.append(dict(id=id,title=title,chapter=chapter,type='code',source=file,startLine=start,endLine=end,sourceSha256=hashlib.sha256(text.encode()).hexdigest(),excerptSha256=hashlib.sha256(raw.encode()).hexdigest(),files=[f'code/{id}.png',f'code/{id}.html',f'sources/{id}.txt'],note='Exact source text with display wrapping; original line numbers retained.'))
service='backend/src/main/java/com/shelfwise/InventoryService.java';security='backend/src/main/java/com/shelfwise/SecurityConfig.java'
excerpt('01-code-product-lock','Pessimistic product row locking','backend/src/main/java/com/shelfwise/Repositories.java',1,19)
excerpt('02-code-stock-transaction','Atomic stock movement with audit and replay checks',service,56,66)
excerpt('03-code-product-filter','Stock filtering and deterministic pagination',service,26,41)
excerpt('04-code-warning-cache','Revision-based warning cache and database fallback',service,70,83)
lines=(ROOT/service).read_text().splitlines();start=next(i+1 for i,l in enumerate(lines) if '@Transactional void updateWarning' in l);end=next(i+1 for i,l in enumerate(lines) if 'private void invalidate' in l)
excerpt('05-code-warning-lifecycle','Warning episode transitions and recovery',service,start,end)
excerpt('06-code-security','Session security CSRF and endpoint authorization',security,26,40)
start=next(i+1 for i,l in enumerate((ROOT/security).read_text().splitlines()) if '@PostMapping("/login")' in l)
excerpt('07-code-session-login','Session authentication and session ID rotation',security,start,start+9)
excerpt('08-code-api-client','Typed frontend API and CSRF header interceptor','frontend/src/api.ts',1,20,'typescript')
excerpt('09-code-navigation','Authenticated route and role navigation guards','frontend/src/router.ts',1,24,'typescript')
excerpt('10-code-schema','Stock history schema and idempotency constraint','backend/src/main/resources/db/migration/V1__initial_schema.sql',31,51,'sql',3)
excerpt('11-code-deployment','MySQL and Redis container configuration','docker-compose.yml',1,32,'yaml')
test='backend/src/test/java/com/shelfwise/InventoryIntegrationTest.java';lines=(ROOT/test).read_text().splitlines();start=next(i+1 for i,l in enumerate(lines) if '@Test void concurrentDispatchCannotOversell' in l)
excerpt('12-code-concurrency-tests','Concurrent dispatch and identical-submission tests',test,start,start+1,chapter=5)
excerpt('13-code-boundary-tests','Frontend zero and threshold equality tests','frontend/src/inventory.spec.ts',1,21,'typescript',5)
excerpt('14-code-stock-form','Stock form request key and submission guard','frontend/src/views/WorkspaceView.vue',65,67,'typescript')
# Real test output, not a simulated terminal.
def logview(id,title,source,lines,chapter=5):
 raw='\n'.join(lines);(OUT/'sources'/f'{id}.txt').write_text(raw+'\n');safe=html.escape(raw)
 doc=f'''<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}body{{width:1080px;color:#1b2937;font-family:Arial}}header{{padding:22px;font-size:19px;background:#f4f6f8;border-bottom:1px solid #ccd4dc}}pre{{font:17px/28px Menlo,monospace;padding:24px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere}}</style><header>{html.escape(title)}</header><pre>{safe}</pre>'''
 (OUT/'evidence'/f'{id}.html').write_text(doc);M.append(dict(id=id,title=title,chapter=chapter,type='test-result',source=source,files=[f'evidence/{id}.png',f'evidence/{id}.html',f'sources/{id}.txt']))
b=(OUT/'sources/backend-tests.log').read_text().splitlines();start=next(i for i,l in enumerate(b) if '[INFO] Results:' in l);logview('01-backend-tests','Backend integration tests · current run','sources/backend-tests.log',b[start:])
f=(OUT/'sources/frontend-tests.log').read_text().splitlines();f=[re.sub(r'\x1b\[[0-9;]*m','',l) for l in f];logview('02-frontend-tests','Frontend threshold tests · current run','sources/frontend-tests.log',[l for l in f if l.strip()])
v=json.loads((OUT/'sources/ui-verification.json').read_text());logview('03-browser-verification','Browser capture and role checks · current run','sources/ui-verification.json',[f"Captured at: {v['capturedAt']}",f"Screenshots: {v['screenshots']}",f"JavaScript runtime errors: {len(v['consoleErrors'])}",f"Submitted durable writes: {v['durableWrites']}",'',*['PASS  '+c for c in v['checks']]])
(OUT/'sources/code-manifest.json').write_text(json.dumps(M,indent=2));print('Prepared',len(M),'source and test-output figures')
