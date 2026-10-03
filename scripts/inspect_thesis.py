#!/usr/bin/env python3
"""Render thesis for visual inspection and check resolved text structure."""
from pathlib import Path
import json,subprocess
root=Path(__file__).resolve().parents[1];pdf=root/'dist/shelfwise-thesis.pdf';out=root/'.runtime/thesis-review';out.mkdir(parents=True,exist_ok=True)
subprocess.run(['pdftotext','-layout',str(pdf),str(out/'text.txt')],check=True)
info=subprocess.run(['pdfinfo',str(pdf)],check=True,capture_output=True,text=True).stdout
pages=int(next(l for l in info.splitlines() if l.startswith('Pages:')).split(':')[1]);text=(out/'text.txt').read_text()
assert '??' not in text,'Unresolved reference markers found'
for word in ['Abstract','Requirements and system analysis','Testing, optimisation, and evaluation','Conclusion and future work','Bibliography']:
 assert word in text,f'Missing required section: {word}'
subprocess.run(['pdftoppm','-scale-to','1100','-png',str(pdf),str(out/'page')],check=True)
result={'pdf':'dist/shelfwise-thesis.pdf','pages':pages,'text_extraction_passed':True,'unresolved_reference_markers':0,'render_directory':'.runtime/thesis-review','visual_review':'Rendered pages require visual inspection; final audit records the result.','metadata_fields':'Author, university, department, supervisor, degree and student number remain deliberate placeholders.'}
(root/'docs/evidence/thesis-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
