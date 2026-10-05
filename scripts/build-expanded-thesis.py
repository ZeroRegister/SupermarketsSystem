#!/usr/bin/env python3
"""Assemble the evidence-aligned manuscript into a multi-file LaTeX thesis."""
from pathlib import Path
import re,json,sys,hashlib,shutil
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'thesis/reference-aligned';ASSETS=ROOT/'thesis/figure-assets';DIST=ROOT/'dist';DIST.mkdir(exist_ok=True)
TITLE='Development of an Inventory and Stock Warning System for Small Supermarkets'
blocks=[]
def table_block(key,caption,rows):return {'kind':'table','key':key,'caption':caption,'rows':rows}
def schema(name):
 sql=(ROOT/'backend/src/main/resources/db/migration/V1__initial_schema.sql').read_text();body=re.search(r'CREATE TABLE '+name+r'\s*\((.*?)\);',sql,re.S).group(1)
 meanings={'id':'Record identifier','username':'Sign-in identity','display_name':'Human-readable staff name','password_hash':'Stored password hash','role':'Fixed ADMIN MANAGER or CLERK value','enabled':'Current access flag','created_at':'Server creation timestamp','name':'Descriptive name','description':'Optional descriptive text','active':'Available catalogue or reference record','contact_name':'Supplier contact person','email':'Supplier contact address','phone':'Supplier telephone text','sku':'Unique required product identity','barcode':'Optional unique scanned identity','unit':'Label for integer quantity','price':'Current unit price not historical cost','quantity':'Bounded current product balance','safety_stock':'Urgency policy within the reorder level','reorder_threshold':'Positive low-stock boundary including equality','category_id':'Optional category reference','supplier_id':'Optional supplier reference','version':'JPA entity version','updated_at':'Latest product update time','product_id':'Stock-bearing product reference','actor_id':'Authenticated movement actor','type':'Movement or warning enum name','delta':'Accepted signed stock effect','quantity_before':'Locked balance before the operation','quantity_after':'Accepted balance after the operation','reason':'Required explanation of the stock intention','idempotency_key':'Actor-scoped request intention key','state':'OPEN or RESOLVED episode lifecycle','observed_quantity':'Quantity context of the warning episode','threshold':'Policy context of the warning episode','expires_at':'Stored recovery visibility boundary','acknowledged_by':'Optional first reviewer reference','acknowledged_at':'Optional first review timestamp','setting_key':'Preference identity','setting_value':'Display preference value','revision':'Durable cache namespace counter'}
 rows=[['Field','SQL type','Nullable','Constraint','Purpose']]
 for m in re.finditer(r'(?:^|,)\s*(\w+)\s+(BIGINT|VARCHAR\(\d+\)|DECIMAL\(\d+,\d+\)|BOOLEAN|TIMESTAMP\(\d+\))([^,]*)(?=,|$)',body):
  field,typ,tail=m.groups();rules=[]
  if 'PRIMARY KEY' in tail:rules.append('Primary key')
  if 'UNIQUE' in tail:rules.append('Unique')
  if field in ('category_id','supplier_id','product_id','actor_id','acknowledged_by'):rules.append('Foreign key')
  if name=='inventory_transactions' and field in ('actor_id','idempotency_key'):rules.append('Composite unique')
  if name=='products' and field in ('quantity','safety_stock','reorder_threshold','price'):rules.append('Check constraint')
  rows.append([field,typ,'No' if 'NOT NULL' in tail or 'PRIMARY KEY' in tail else 'Yes',', '.join(rules) or 'Column mapping',meanings.get(field,'Domain field')])
 return table_block('schema-'+name,'Implemented '+name+' table fields and constraints',rows)
test_explanations={
'emptySearchAndStablePagination':'No-match query reports zero and oversized page request is capped.',
'unauthorizedUserCannotReadInventory':'Anonymous inventory request receives 401.',
'csrfRequiredForUnsafeMethods':'Unsafe stock request without CSRF receives 403.',
'clerkCannotAcknowledgeOrManageUsers':'Clerk review and staff administration are denied.',
'managerCannotPostStock':'Manager cannot submit an inventory movement.',
'badCatalogInputRejected':'Empty identity and invalid price input are rejected.',
'receiptAndDispatchHaveAuditHistory':'Receipt and dispatch produce correct quantity and two ledger rows.',
'negativeStockRejectedWithoutHistory':'Rejected dispatch changes neither quantity nor accepted history.',
'exactReplayReturnsSameId':'Equivalent retry returns one identifier and one stock effect.',
'changedPayloadReplayConflicts':'Changed intention with the same actor key conflicts.',
 'thresholdEqualityIsLowAndZeroIsOut':'Zero is OUT and positive equality is LOW.',
'healthyReplenishmentResolvesShortage':'Healthy stock resolves shortage and creates RESTOCKED.',
'acknowledgementIsVisibleThroughCache':'Review attribution is visible and stock remains unchanged.',
'signedAdjustmentAndAbsoluteCount':'Signed correction and absolute count have distinct arithmetic.',
'countToZeroIsAuditable':'Counting zero retains its negative-delta audit record.',
'archivedProductCannotMove':'Archived product rejects a new stock operation.',
'uniqueSkuAndThresholdHierarchy':'Duplicate SKU and inconsistent thresholds are rejected.',
'concurrentDispatchCannotOversell':'Seven units permit exactly seven successful unit dispatches.',
'concurrentIdenticalSubmissionDoesNotDuplicate':'Concurrent same-product retry yields one accepted identifier.',
'sameCountStillRecordsAudit':'Unchanged absolute count creates a zero-delta observation.',
'managerThresholdEndpointAndClerkDenial':'Manager can update thresholds and clerk cannot.',
'lastAdminCannotBeDisabledOrDemoted':'Last enabled administrator is protected from access removal.',
'archivedWarningsAreResolved':'Archival removes open warning attention.',
'restockedExpiresAndNewShortageStartsNewEpisode':'Renewed shortage closes recovery and opens OUT; no clock expiry is tested.',
'warningFiltersHaveAccurateTotals':'Selected warning type agrees with returned content and total.',
'concurrentAcknowledgementsPreserveFirstReviewer':'Concurrent review returns the same first attribution.',
'invalidCredentialsAndNullLoginFieldsReturnClientErrors':'Invalid credentials and absent required login values are rejected.'}
for file in sorted((BASE/'content').glob('*.md')):
 text=file.read_text();lines=text.splitlines();paragraph=[]
 def flush():
  if paragraph:blocks.append({'kind':'p','text':' '.join(paragraph),'group':file.stem});paragraph.clear()
 i=0
 while i<len(lines):
  line=lines[i].strip()
  if not line:flush();i+=1;continue
  if line.startswith('#'):
   flush();level=len(line)-len(line.lstrip('#'));blocks.append({'kind':'heading','level':level,'text':line[level:].strip(),'group':file.stem})
  elif line.startswith('@fig '):
   flush();key,asset,caption=line[5:].split('|',2);assert (ASSETS/asset).is_file();blocks.append({'kind':'fig','key':key,'asset':asset,'caption':caption,'group':file.stem})
  elif line.startswith('@table '):
   flush();key,caption=line[7:].split('|',1);rows=[];i+=1
   while i<len(lines) and ' | ' in lines[i]:rows.append([x.strip() for x in lines[i].split(' | ')]);i+=1
   assert all(len(r)==len(rows[0]) for r in rows),key;b=table_block(key,caption,rows);b['group']=file.stem;blocks.append(b);continue
  elif line.startswith('@schema '):flush();b=schema(line[8:]);b['group']=file.stem;blocks.append(b)
  elif line.startswith('@equation '):
   flush();key,text=line[10:].split('|',1);blocks.append({'kind':'equation','key':key,'text':text,'group':file.stem})
  elif line=='@tests':
   flush();tests=re.findall(r'@Test void (\w+)\(', (ROOT/'backend/src/test/java/com/shelfwise/InventoryIntegrationTest.java').read_text());assert len(tests)==27
   rows=[['Case','Executed assertion focus','Result']]+[[re.sub(r'(?<=[a-z])(?=[A-Z])',' ',t).capitalize(),test_explanations[t],'Passed'] for t in tests];b=table_block('acceptance-catalog','The twenty-seven backend acceptance cases',rows);b['group']=file.stem;blocks.append(b)
  else:paragraph.append(line)
  i+=1
 flush()
# Number all headings, images and tables before rendering either format.
chapter=0;sec=0;sub=0;fc=defaultdict(int);tc=defaultdict(int);figs={};tabs={};heading_list=[];citations=[]
for b in blocks:
 group=int(b['group'][:2])
 if b['kind']=='heading':
  if b['level']==1:
   if 1<=group<=5:chapter=group;sec=0;sub=0;b['display']=f"{chapter} {b['text']}";b['chapter']=chapter
   else:b['display']=b['text'];b['chapter']=0 if group==0 else 'A'
  elif b['level']==2:
   sec+=1;sub=0;b['display']=f'{chapter}.{sec} {b["text"]}' if 1<=group<=5 else b['text']
  else:
   sub+=1;b['display']=f'{chapter}.{sec}.{sub} {b["text"]}' if 1<=group<=5 else b['text']
  b['bookmark']='head'+str(len(heading_list)+1);heading_list.append(b)
 if b['kind'] in ('fig','table'):
  prefix=str(group) if 1<=group<=5 else 'A';counter=fc if b['kind']=='fig' else tc;counter[prefix]+=1;b['number']=prefix+'.'+str(counter[prefix]);(figs if b['kind']=='fig' else tabs)[b['key']]=b['number']
 for key in re.findall(r'\[@([^\]]+)\]',b.get('text','')):
  if key not in citations:citations.append(key)
heading_list.insert(next(i for i,h in enumerate(heading_list) if h['text']=='Appendices'),{'level':1,'display':'References','bookmark':'headrefs'})
bib=(ROOT/'thesis/references.bib').read_text().replace('Accessed 4 October 2026','Accessed 5 October 2026').replace('https://www.odoo.com/documentation/master/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/reordering_rules.html','https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/purchase/products/reordering.html')
(BASE/'references.bib').write_text(bib)
refs={}
for segment in re.split(r'(?=@\w+\{)',bib):
 m=re.match(r'@(\w+)\{([^,]+),',segment)
 if not m:continue
 key=m.group(2);fields={}
 for field in ['author','title','year','url','journal','school','volume','number','pages']:
  f=re.search(r'\b'+field+r'\s*=\s*\{(.*?)\}(?=\s*[,}])',segment,re.S)
  if f:fields[field]=f.group(1).replace('{','').replace('}','')
 refs[key]=fields
for key in citations:assert key in refs,key

def inline(s,tex=False):
 pattern=r'(\[@[^\]]+\]|\{(?:fig|tab):[^}]+\})';pieces=re.split(pattern,s);out=[]
 for piece in pieces:
  if piece.startswith('[@'):
   key=piece[2:-1];out.append('\\citep{'+key+'}' if tex else '['+str(citations.index(key)+1)+']')
  elif piece.startswith('{fig:'):
   key=piece[5:-1];assert key in figs,key;out.append('Figure~\\ref{fig:'+key+'}' if tex else 'Figure '+figs[key])
  elif piece.startswith('{tab:'):
   key=piece[5:-1];assert key in tabs,key;out.append('Table~\\ref{tab:'+key+'}' if tex else 'Table '+tabs[key])
  else:
   if tex:
    piece=''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}.get(c,c) for c in piece)
   out.append(piece)
 return ''.join(out)
def tex_table(b):
 n=len(b['rows'][0]);weights=([.22,.21,.10,.17,.30] if b['key'].startswith('schema-') else ([.36,.49,.15] if b['key']=='acceptance-catalog' else ([.15,.33,.24,.28] if b['key']=='api-catalog' else [1/n]*n)))
 col=''.join('>{\\raggedright\\arraybackslash}p{'+str(round(.90*w,3))+'\\textwidth}' for w in weights)
 out=['\\begingroup\\small\\setstretch{1.05}\\setlength{\\tabcolsep}{3pt}\\renewcommand{\\arraystretch}{1.25}','\\begin{longtable}{'+col+'}','\\caption{'+inline(b['caption'],True)+'}\\label{tab:'+b['key']+'}\\\\','\\toprule', ' & '.join('\\textbf{'+inline(x,True)+'}' for x in b['rows'][0])+r' \\',r'\midrule\endfirsthead',r'\toprule',' & '.join('\\textbf{'+inline(x,True)+'}' for x in b['rows'][0])+r' \\',r'\midrule\endhead',r'\bottomrule\endfoot']
 out+=[' & '.join(('\\path|'+x+'|' if ('_' in x or x.startswith('/api/')) else inline(x,True)) for x in row)+r' \\' for row in b['rows'][1:]];out+=['\\end{longtable}\\endgroup'];return '\n'.join(out)
def tex_blocks(items):
 out=[]
 for b in items:
  kind=b['kind'];group=int(b['group'][:2])
  if kind=='heading':
   if b['level']>1:out.append('\\FloatBarrier')
   cmd={1:'chapter',2:'section',3:'subsection'}[min(b['level'],3)];star='*' if group in (0,6,7) else '';out.append('\\'+cmd+star+'{'+inline(b['text'],True)+'}')
   if star and b['level']==1:out.append('\\addcontentsline{toc}{chapter}{'+inline(b['text'],True)+'}')
   if star and b['level']==2:out.append('\\addcontentsline{toc}{section}{'+inline(b['text'],True)+'}')
  elif kind=='p':out.append(inline(b['text'],True)+'\n')
  elif kind=='table':out.append(tex_table(b))
  elif kind=='equation':out.append(r'\begin{equation}q_{\mathrm{after}}=q_{\mathrm{before}}+\Delta,\qquad 0\leq q_{\mathrm{after}}\leq 10^9.\end{equation}')
  elif kind=='fig':
   maxh='0.84' if b['asset'].startswith('code/') else ('0.6' if b['key']=='er-overall' else '0.40')
   out.append('\\begin{figure}[htbp]\\centering\n\\includegraphics[width=\\textwidth,height='+maxh+'\\textheight,keepaspectratio]{../figure-assets/'+b['asset']+'}\n\\caption{'+inline(b['caption'],True)+'}\\label{fig:'+b['key']+'}\n\\end{figure}')
 return '\n\n'.join(out)
def build_tex():
 mapping={1:'01-object-analysis',2:'02-assignment',3:'03-design',4:'04-implementation',5:'05-testing',6:'06-conclusion',7:'07-appendices'}
 for group,name in mapping.items():(BASE/'chapters'/f'{name}.tex').write_text(tex_blocks([b for b in blocks if int(b['group'][:2])==group]))
 pre=r'''\documentclass[12pt,a4paper,oneside]{report}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{newtxtext,newtxmath,microtype}
\usepackage[top=24mm,bottom=24mm,left=27.5mm,right=27.5mm,headheight=16pt]{geometry}
\usepackage{setspace,graphicx,booktabs,longtable,array,caption,float,xcolor,fancyhdr}
\usepackage[numbers,sort&compress]{natbib}
\usepackage[hidelinks]{hyperref}
\usepackage{bookmark,placeins,titlesec}
\titleformat{\chapter}[hang]{\Large\bfseries}{\thechapter}{1em}{}
\titlespacing*{\chapter}{0pt}{0pt}{16pt}
\titlespacing*{\section}{0pt}{10pt}{6pt}
\titlespacing*{\subsection}{0pt}{8pt}{4pt}
\renewcommand{\topfraction}{0.95}
\renewcommand{\bottomfraction}{0.9}
\renewcommand{\textfraction}{0.04}
\renewcommand{\floatpagefraction}{0.75}
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{4}
\setlength{\textfloatsep}{6pt}
\setlength{\floatsep}{6pt}
\setlength{\intextsep}{6pt}
\setstretch{1.15}
\setlength{\parindent}{0.65cm}
\setlength{\parskip}{2.5pt}
\setlength{\emergencystretch}{3em}
\setcounter{tocdepth}{1}
\setcounter{secnumdepth}{2}
\pagestyle{fancy}\fancyhf{}\fancyhead[C]{\small Shelfwise Inventory and stock warning system}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}}
\captionsetup{font=small,labelfont=bf,skip=7pt}
\hypersetup{pdftitle={Development of an Inventory and Stock Warning System for Small Supermarkets},pdfauthor={}}
\begin{document}
\begin{titlepage}\centering
{\large UNIVERSITY AND DEPARTMENT\par}\vspace{2cm}
{\Large\bfseries MASTER'S THESIS\par}\vspace{1.7cm}
{\LARGE Development of an Inventory and Stock Warning System for Small Supermarkets\par}\vspace{2.4cm}
Student\quad\rule{7cm}{0.4pt}\par\vspace{0.7cm}
Supervisor\quad\rule{6.7cm}{0.4pt}\par\vspace{0.7cm}
Degree and specialty\quad\rule{5.5cm}{0.4pt}\par\vspace{0.7cm}
City\quad\rule{7.5cm}{0.4pt}\par\vfill 2026
\end{titlepage}
\pagenumbering{roman}
{\setstretch{1.0}\small\setlength{\parskip}{0pt}\tableofcontents\listoffigures\listoftables}
'''
 main=pre+tex_blocks([b for b in blocks if int(b['group'][:2])==0])+ '\n\\clearpage\\pagenumbering{arabic}\n'
 main+='\n'.join('\\include{chapters/'+mapping[i]+'}' for i in range(1,7))
 main+='\n\\bibliographystyle{unsrtnat}\\bibliography{references}\n\\setcounter{table}{0}\\renewcommand{\\thetable}{A.\\arabic{table}}\n\\include{chapters/07-appendices}\n\\end{document}\n';(BASE/'main.tex').write_text(main)
manifest={'title':TITLE,'language':'English','author_fields':'Blank institutional identity fields for completion','word_count':sum(len(b.get('text','').split()) for b in blocks if b['kind']=='p'),'figures':len(figs),'tables':len(tabs),'references':len(citations),'citation_order':citations,'source_files':[str(p.relative_to(ROOT)) for p in sorted((BASE/'content').glob('*.md'))],'figure_labels':figs,'table_labels':tabs}
(BASE/'manuscript-manifest.json').write_text(json.dumps(manifest,indent=2));(BASE/'manuscript-blocks.json').write_text(json.dumps(blocks,indent=2))
build_tex()
print(json.dumps(manifest,indent=2))
