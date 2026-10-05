#!/usr/bin/env python3
"""Verify the compiled LaTeX manuscript, captions and page count."""
from pathlib import Path
import json,re,hashlib
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'thesis/reference-aligned';OUT=ROOT/'.runtime/paper-review';OUT.mkdir(parents=True,exist_ok=True)
PDF=ROOT/'dist/shelfwise-reference-aligned-thesis.pdf'
blocks=json.loads((BASE/'manuscript-blocks.json').read_text());manifest=json.loads((BASE/'manuscript-manifest.json').read_text());r=PdfReader(PDF);pages=[p.extract_text() for p in r.pages]
assert 80<=len(pages)<=100,f'Actual PDF page count is {len(pages)}'
text='\n\f\n'.join(pages);assert '??' not in text;assert '\ufffd' not in text
normalize=lambda t:' '.join(re.findall(r'[A-Za-z0-9]+',t)).lower()
def locate(label,minimum=1):
 target=normalize(label)
 for i,page in enumerate(pages,1):
  if i<minimum:continue
  lines=page.splitlines()
  for j in range(len(lines)):
   for size in [1,2,3]:
    if normalize(' '.join(lines[j:j+size]))==target:return i
 raise AssertionError('Missing exact heading or caption: '+label)
start=locate('1 Object analysis');headmap={};figmap={};tablemap={}
for b in blocks:
 if b['kind']=='heading':headmap[b['bookmark']]=locate(b['display'],7 if int(b['group'][:2])==0 else start)
 if b['kind']=='fig':figmap['fig'+b['key'].replace('-','')]=locate('Figure '+b['number']+' '+b['caption'],start)
 if b['kind']=='table':tablemap['table'+b['key'].replace('-','')]=locate('Table '+b['number']+' '+b['caption'],start)
headmap['headrefs']=locate('Bibliography',start)
log=(BASE/'build/main.log').read_text()
assert not re.search(r'undefined references|Citation .* undefined|Reference .* undefined',log)
assert len(figmap)==manifest['figures'] and len(tablemap)==manifest['tables']
(OUT/'final-text.txt').write_text(text)
result={'pdf':'dist/shelfwise-reference-aligned-thesis.pdf','pages':len(pages),'body_start_physical_page':start,'figures':manifest['figures'],'tables':manifest['tables'],'references':manifest['references'],'prose_word_count':manifest['word_count'],'unresolved_markers':0,'caption_pages':{**figmap,**tablemap},'heading_pages':headmap,'pdf_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'visual_review':'Structural checks do not replace rendered-page inspection'}
(ROOT/'docs/evidence/reference-aligned-thesis-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['caption_pages','heading_pages']},indent=2))
