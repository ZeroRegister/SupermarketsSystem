#!/usr/bin/env python3
"""Add representative demonstration data through normal authenticated APIs; rerunnable."""
import http.cookiejar,json,os,urllib.request,uuid
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
password=os.environ.get('DEMO_PASSWORD') or env['DEMO_PASSWORD'].strip('"\'')
jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));base=os.environ.get('SHELFWISE_API','http://localhost:8080');token=''
def req(method,path,body=None):
 headers={'Content-Type':'application/json','X-XSRF-TOKEN':token}
 with client.open(urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method),timeout=15) as r:return json.loads(r.read())
token=req('GET','/api/auth/csrf')['token'];req('POST','/api/auth/login',{'username':'admin','password':password})
suppliers=req('GET','/api/suppliers')
for name,contact,email,phone in [('Meadowbrook Dairy','Demo contact','orders@example.invalid','000-000-0101'),('Greenfield Produce','Demo contact','fresh@example.invalid','000-000-0102'),('Harvest Pantry Co.','Demo contact','pantry@example.invalid','000-000-0103')]:
 if not any(s['name']==name for s in suppliers):req('POST','/api/suppliers',{'name':name,'contactName':contact,'email':email,'phone':phone})
suppliers=req('GET','/api/suppliers');categories=req('GET','/api/categories');existing=req('GET','/api/products?size=100')['items'];by_sku={p['sku']:p for p in existing}
items=[('PRD-2001','Apples, Gala','kg',3.9,38,5,12,'Produce','Greenfield Produce'),('PRD-2002','Carrots 1kg','bag',2.4,24,4,10,'Produce','Greenfield Produce'),('PRD-2003','Cheddar cheese 250g','pack',5.6,22,4,8,'Dairy & chilled','Meadowbrook Dairy'),('PRD-2004','Rice 2kg','bag',6.8,43,5,15,'Pantry','Harvest Pantry Co.'),('PRD-2005','Tomato soup 400g','can',2.3,46,6,15,'Pantry','Harvest Pantry Co.'),('PRD-2006','Olive oil 500ml','bottle',10.5,19,3,8,'Pantry','Harvest Pantry Co.')]
for sku,name,unit,price,qty,safety,threshold,category,supplier in items:
 if sku in by_sku:continue
 p=req('POST','/api/products',{'sku':sku,'barcode':None,'name':name,'unit':unit,'price':price,'safetyStock':safety,'reorderThreshold':threshold,'categoryId':next(c['id'] for c in categories if c['name']==category),'supplierId':next(s['id'] for s in suppliers if s['name']==supplier)})
 req('POST','/api/transactions',{'productId':p['id'],'type':'STOCK_IN','quantity':qty,'reason':'Opening demonstration delivery','idempotencyKey':'demo-opening-'+sku})
print('PASS: representative demo partners and products seeded through audited APIs; existing balances preserved.')
