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
WIDTH=80
def reflow(line,java=True):
 """Break a dense source line at statement boundaries for display.

 Only whitespace is added: braces and semicolons outside strings and parentheses
 end a display row, and nesting adds indentation. Every token is kept as written.
 """
 if len(line)<=WIDTH:return [line]
 base=len(line)-len(line.lstrip(' '));text=line.strip();rows=[];buf='';depth=0;paren=0;quote=None;i=0
 def emit():
  nonlocal buf
  if buf.strip():rows.append(' '*(base+2*depth)+buf.strip())
  buf=''
 while i<len(text):
  c=text[i]
  if quote:
   buf+=c
   if c=='\\' and i+1<len(text):buf+=text[i+1];i+=2;continue
   if c==quote:quote=None
   i+=1;continue
  if c in '"\'`':quote=c;buf+=c;i+=1;continue
  if c in '([':paren+=1
  elif c in ')]':paren=max(0,paren-1)
  if paren==0 and c=='{':buf+=c;emit();depth+=1;i+=1;continue
  if paren==0 and c=='}':
   emit();depth=max(0,depth-1);buf='}';i+=1;rest=text[i:].lstrip()
   if re.match(r'(else|catch|finally|while)\b',rest) or rest[:1] in (')',';',','):continue
   emit();continue
  if paren==0 and c==';':buf+=c;emit();i+=1;continue
  buf+=c;i+=1
 emit()
 rows=[part for row in rows for part in split_long(row,java)]
 assert re.sub(r'\s','',''.join(rows))==re.sub(r'\s','',line),'reflow changed source text'
 return rows
def split_long(row,java):
 """Continue an over-long row before chained calls (and Java ternary operators)."""
 if len(row)<=WIDTH:return [row]
 indent=len(row)-len(row.lstrip(' '));text=row.strip();cuts=[];paren=0;quote=None;calls=0
 for i,c in enumerate(text):
  if quote:
   if c==quote and text[i-1]!='\\':quote=None
   continue
  if c in '"\'`':quote=c;continue
  if c in '([{':paren+=1
  elif c in ')]}':paren=max(0,paren-1)
  elif paren==0 and c=='.' and re.match(r'\.[A-Za-z_]\w*\(',text[i:]):
   calls+=1
   if calls>1:cuts.append(i)
  elif paren==0 and java and c in '?:' and i>0:cuts.append(i);calls=0
 if not cuts:return [row]
 parts=[text[a:b] for a,b in zip([0]+cuts,cuts+[len(text)])]
 return [' '*indent+parts[0]]+[' '*(indent+4)+part for part in parts[1:]]
def hang(segment):
 # Continuation lines sit four columns inside the row's own indentation.
 n=len(segment)-len(segment.lstrip(' '))+4
 return f' style="padding-left:{n}ch;text-indent:-{n}ch"'
def excerpt(id,title,file,start,end,lexer='java',chapter=4):
 text=(ROOT/file).read_text();lines=text.splitlines();end=min(end,len(lines));picked=lines[start-1:end]
 body=[]
 for no,line in enumerate(picked,start):
  for k,segment in enumerate(reflow(line,lexer=='java') if lexer in ('java','typescript') else [line]):
   code=highlight(segment,get_lexer_by_name(lexer),fmt).rstrip();wrap=len(segment)>WIDTH
   # Rows that still exceed the width may break only after punctuation, with a hanging indent.
   if wrap:code=''.join(part if part.startswith('<') else re.sub(r'([,.(])',r'\1<wbr>',part) for part in re.split(r'(<[^>]+>)',code))
   body.append(f'<div class="row"><span class="number">{no if k==0 else ""}</span><pre class="syntax{" wrap" if wrap else ""}"{hang(segment) if wrap else ""}>{code}</pre></div>')
 raw='\n'.join(picked)+'\n';(OUT/'sources'/f'{id}.txt').write_text(raw)
 doc=f'''<!doctype html><meta charset="utf-8"><style>{css}
 *{{box-sizing:border-box}}html,body{{margin:0;background:#fff;color:#17202a}}body{{font-family:Arial,sans-serif;width:1000px}}
 header{{padding:20px 24px 18px;border-bottom:1px solid #d7dce1;font-size:18px;background:#f6f7f8}}header b{{display:block;margin-bottom:8px}}header small{{font-size:13px;color:#56616c}}
 main{{padding:20px 18px 24px}}.row{{display:flex;align-items:flex-start;min-height:24px}}.number{{width:50px;flex:none;text-align:right;padding-right:14px;font:15px/24px Menlo,monospace;color:#84909c;user-select:none}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;flex:1;font:19px/24px Menlo,Consolas,monospace;font-variant-ligatures:none}}pre.wrap{{overflow-wrap:break-word}}.row:nth-child(even){{background:#fbfcfd}}
 </style><header><b>{html.escape(title)}</b><small>{html.escape(file)} · original lines {start}–{end}</small></header><main>{''.join(body)}</main>'''
 (CODE/f'{id}.html').write_text(doc)
 M.append(dict(id=id,title=title,chapter=chapter,type='code',source=file,startLine=start,endLine=end,sourceSha256=hashlib.sha256(text.encode()).hexdigest(),excerptSha256=hashlib.sha256(raw.encode()).hexdigest(),files=[f'code/{id}.png',f'code/{id}.html',f'sources/{id}.txt'],note='Exact source tokens; dense lines are broken at statement boundaries for display, and numbers mark original lines.'))
service='backend/src/main/java/com/shelfwise/InventoryService.java';security='backend/src/main/java/com/shelfwise/SecurityConfig.java'
excerpt('01-code-product-lock','Pessimistic product row locking','backend/src/main/java/com/shelfwise/Repositories.java',1,19)
slines=(ROOT/service).read_text().splitlines()
move_start=next(i+1 for i,l in enumerate(slines) if 'TransactionView move(' in l)
move_end=next(i+1 for i,l in enumerate(slines) if 'private long signedDelta' in l)-1
excerpt('02-code-stock-transaction','Atomic stock movement with audit and replay checks',service,move_start,move_end)
excerpt('03-code-product-filter','Stock filtering and deterministic pagination',service,26,41)
cstart=next(i+1 for i,l in enumerate(slines) if 'PageResult<WarningView> warningPage(' in l)
cend=next(i+1 for i,l in enumerate(slines) if i+1>cstart and l==' }')
excerpt('04-code-warning-cache','Revision-based warning cache and database fallback',service,cstart,cend)
lines=(ROOT/service).read_text().splitlines();start=next(i+1 for i,l in enumerate(lines) if '@Transactional void updateWarning' in l);end=next(i+1 for i,l in enumerate(lines) if 'private void invalidate' in l)-1
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
view='frontend/src/views/WorkspaceView.vue';vlines=(ROOT/view).read_text().splitlines()
vstart=next(i+1 for i,l in enumerate(vlines) if 'async function openMovement(' in l)
vend=next(i+1 for i,l in enumerate(vlines) if 'async function saveMovement(' in l)
excerpt('14-code-stock-form','Stock form request key and submission guard',view,vstart,vend,'typescript')
purchase='backend/src/main/java/com/shelfwise/Purchasing.java';plines=(ROOT/purchase).read_text().splitlines()
pstart=next(i+1 for i,l in enumerate(plines) if 'switch(in.action())' in l)
pend=next(i+1 for i,l in enumerate(plines) if 'default -> throw error("Unknown purchase action"' in l)
excerpt('15-code-purchasing','Purchase approval and state guards',purchase,pstart,pend,'java',4)
# Real test output, not a simulated terminal.
def logview(id,title,source,lines,chapter=5):
 raw='\n'.join(lines);(OUT/'sources'/f'{id}.txt').write_text(raw+'\n');safe=html.escape(raw)
 doc=f'''<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}body{{width:1080px;color:#1b2937;font-family:Arial}}header{{padding:22px;font-size:19px;background:#f4f6f8;border-bottom:1px solid #ccd4dc}}pre{{font:17px/28px Menlo,monospace;padding:24px;margin:0;white-space:pre-wrap;overflow-wrap:anywhere}}</style><header>{html.escape(title)}</header><pre>{safe}</pre>'''
 (OUT/'evidence'/f'{id}.html').write_text(doc);M.append(dict(id=id,title=title,chapter=chapter,type='test-result',source=source,files=[f'evidence/{id}.png',f'evidence/{id}.html',f'sources/{id}.txt']))
b=(OUT/'sources/backend-tests.log').read_text().splitlines();start=next(i for i,l in enumerate(b) if '[INFO] Results:' in l);logview('01-backend-tests','Backend integration tests · current run','sources/backend-tests.log',b[start:])
f=(OUT/'sources/frontend-tests.log').read_text().splitlines();f=[re.sub(r'\x1b\[[0-9;]*m','',l) for l in f];logview('02-frontend-tests','Frontend threshold tests · current run','sources/frontend-tests.log',[l for l in f if l.strip()])
v=json.loads((OUT/'sources/ui-verification.json').read_text());logview('03-browser-verification','Browser capture and role checks · current run','sources/ui-verification.json',[f"Captured at: {v['capturedAt']}",f"Screenshots: {v['screenshots']}",f"JavaScript runtime errors: {len(v['consoleErrors'])}",f"Submitted durable writes: {v['durableWrites']}",'',*['PASS  '+c for c in v['checks']]])
(OUT/'sources/code-manifest.json').write_text(json.dumps(M,indent=2));print('Prepared',len(M),'source and test-output figures')
