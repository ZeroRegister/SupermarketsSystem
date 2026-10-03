#!/usr/bin/env python3
"""Record or compare a sanitized inventory/history fingerprint around an application restart."""
import argparse,json,subprocess,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['record','verify']);args=parser.parse_args()
# Credentials are inherited inside the container and never printed; only a digest/count escapes.
command=['docker','compose','exec','-T','mysql','sh','-c','MYSQL_PWD="$MYSQL_PASSWORD" mysql -u "$MYSQL_USER" -N -B "$MYSQL_DATABASE" -e "SELECT id,sku,quantity FROM products ORDER BY id; SELECT id,product_id,delta,quantity_before,quantity_after FROM inventory_transactions ORDER BY id;"']
r=subprocess.run(command,cwd=root,check=True,capture_output=True,text=True);digest=hashlib.sha256(r.stdout.encode()).hexdigest();p=root/'.runtime/persistence-before.json';p.parent.mkdir(exist_ok=True)
if args.mode=='record':p.write_text(json.dumps({'sha256':digest,'rows':len(r.stdout.splitlines())}));print('Recorded stock/history fingerprint.')
else:
 old=json.loads(p.read_text());assert old['sha256']==digest,'Database stock/history changed across restart';out=root/'docs/evidence/persistence.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps({'after_application_restart':'same stock and inventory transaction rows','sha256':digest,'rows':old['rows'],'verified':True},indent=2));print('PASS: stock/history fingerprint identical across application restart.')
