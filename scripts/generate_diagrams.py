#!/usr/bin/env python3
"""Render editable Graphviz source diagrams as SVG and thesis-resolution PNG."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'thesis'/'figures';OUT.mkdir(parents=True,exist_ok=True)
PALETTE={'blue':'#e8eefb','#green':'#e7f3ed','#purple':'#f0eafa','#amber':'#fff3dc','#rose':'#fff0e9','#grey':'#f4f6f9'}
STYLE='graph [bgcolor="white",pad=0.25,ranksep=0.72,nodesep=0.48,splines=polyline,labelloc=t,labeljust=l,fontname="Arial",fontsize=18,fontcolor="#24334b"]; node [shape=box,style="rounded,filled",fontname="Arial",fontsize=12,fontcolor="#24334b",color="#b9c3d1",penwidth=1.3,margin="0.20,0.14"]; edge [fontname="Arial",fontsize=9,fontcolor="#59677b",color="#8491a4",penwidth=1.15,arrowsize=.7];'

def render(name,source):
 source=source.replace('{{ {STYLE}', '{ '+STYLE).replace('{STYLE}',STYLE)
 p=OUT/f'{name}.dot';p.write_text(source)
 subprocess.run(['dot','-Tsvg',str(p),'-o',str(OUT/f'{name}.svg')],check=True)
 subprocess.run(['dot','-Tpng','-Gdpi=190',str(p),'-o',str(OUT/f'{name}.png')],check=True)
 print(name)

render('architecture','''digraph Architecture {{ {STYLE}
label="Shelfwise runtime architecture"; rankdir=TB;
client [label="STORE TEAM\\nWeb browser",fillcolor="#e8eefb"];
web [label="VUE 3 + TYPESCRIPT\\nResponsive screens · router · role-aware navigation · forms",fillcolor="#e8eefb",width=4.6];
api [label="SPRING BOOT MODULAR MONOLITH\\n\\nSession & authorization · CSRF · fixed roles\\nCatalog & reports · inventory transactions\\nWarning episodes · validation & pagination",fillcolor="#e7f3ed",width=6.4];
mysql [label="MYSQL 8 · SOURCE OF TRUTH\\nFlyway schema · products · users · transaction history\\nwarning episodes · settings · cache revision",shape=cylinder,fillcolor="#e7f3ed",width=4.7];
redis [label="REDIS 7 · OPTIONAL WARNING-PAGE CACHE\\n30 s TTL · revision-key namespace\\nCache miss/failure falls back to MySQL",fillcolor="#fff3dc",width=4.4];
{rank=same;mysql;redis}
client -> web [label="HTTPS"];
web -> api [label="REST / JSON · session cookie"];
api -> mysql [label="transactional state · row lock"];
api -> redis [label="versioned read cache",style=dashed];
redis -> mysql [label="revision read",style=dashed,dir=both];
}''')

render('erd','''digraph ERD {{ {STYLE}
label="Core relational data model"; rankdir=TB; nodesep=.55; ranksep=.65;
users [label="USERS\\nPK id · UK username\\ndisplay_name · password_hash\\nrole · enabled · created_at",fillcolor="#f0eafa"];
products [label="PRODUCTS\\nPK id · UK sku · UK barcode\\nname · unit · price · quantity\\nsafety_stock · reorder_threshold\\nFK category_id · FK supplier_id\\nactive · version · updated_at",fillcolor="#e7f3ed"];
categories [label="CATEGORIES\\nPK id · UK name\\ndescription · active",fillcolor="#e8eefb"];
suppliers [label="SUPPLIERS\\nPK id\\nname · contact · email · phone · active",fillcolor="#e8eefb"];
transactions [label="INVENTORY_TRANSACTIONS\\nPK id · FK product_id · FK actor_id\\nUK(actor_id, idempotency_key)\\ntype · delta · quantity_before\\nquantity_after · reason · created_at",fillcolor="#e7f3ed"];
warnings [label="WARNINGS\\nPK id · FK product_id\\nFK acknowledged_by (nullable)\\ntype · state · observed_quantity\\nthreshold · created_at · expires_at\\nacknowledged_at",fillcolor="#fff0e9"];
settings [label="APP_SETTINGS\\nPK setting_key · setting_value",fillcolor="#f4f6f9"];
revision [label="CACHE_REVISION\\nPK id · revision\\nmonotonic invalidation token",fillcolor="#fff3dc"];
{rank=same;users;categories;suppliers}
{rank=same;transactions;warnings}
{rank=same;settings;revision}
categories -> products [label="1 to many"];
suppliers -> products [label="0..1 per product"];
products -> transactions [label="one audit trail"];
users -> transactions [label="actor"];
products -> warnings [label="warning episodes"];
users -> warnings [label="optional reviewer"];
settings -> products [style=invis]; revision -> warnings [style=dashed,label="cache keys",constraint=false];
}''')

render('stock-workflow','''digraph StockWorkflow {{ {STYLE}
label="Stock movement: transaction and warning workflow"; rankdir=TB; ranksep=.55; nodesep=.4;
submit [label="1 · CLERK SUBMITS\\nproduct · type · quantity\\nreason · idempotency key",fillcolor="#e8eefb"];
validate [label="2 · VALIDATE\\nrole · fields · key replay\\nnormalize count vs delta",fillcolor="#f0eafa"];
lock [label="3 · LOCK PRODUCT\\nSELECT … FOR UPDATE\\nserialize stock changes",fillcolor="#e7f3ed"];
boundary [label="4 · CHECK BALANCE\\n0 ≤ new quantity\\n≤ 1,000,000,000",shape=diamond,fillcolor="#fff3dc"];
commit [label="5 · COMMIT ATOMICALLY\\nquantity + before/delta/after\\nactor + reason + time",fillcolor="#e7f3ed"];
warning [label="6 · UPDATE EPISODE\\nseverity / recovery / review\\ninside the same transaction",fillcolor="#fff0e9"];
revision [label="7 · REVISE CACHE KEY\\nrevision increment commits\\nwith the inventory change",fillcolor="#fff3dc"];
response [label="8 · READ / RESPOND\\nRedis cache or MySQL fallback\\nreturn transaction and warnings",fillcolor="#f4f6f9"];
submit -> validate -> lock -> boundary;
boundary -> commit [label="valid"];
boundary -> response [label="below zero / invalid",style=dashed];
commit -> warning -> revision -> response;
}''')

render('warning-lifecycle','''digraph WarningLifecycle {{ {STYLE}
label="Warning episodes and independent acknowledgement"; rankdir=TB; ranksep=.65; nodesep=.5;
change [label="Stock transaction or threshold edit\\nrecalculate product health",fillcolor="#e8eefb"];
zero [label="Quantity = 0?",shape=diamond,fillcolor="#fff3dc"];
out [label="OUT episode\\nopen / refresh",fillcolor="#fff0e9"];
reorder [label="Quantity ≤ reorder threshold?",shape=diamond,fillcolor="#fff3dc"];
low [label="LOW episode\\nopen / refresh",fillcolor="#fff3dc"];
healthy [label="Above reorder threshold\\nresolve shortage; open RESTOCKED\\nepisode for 24 hours",fillcolor="#e7f3ed"];
ack [label="Manager acknowledgement\\nreviewer + timestamp\\nstock remains unchanged",fillcolor="#f0eafa"];
expire [label="After 24 hours or renewed shortage\\nresolve RESTOCKED episode",fillcolor="#f4f6f9"];
change -> zero;
zero -> out [label="yes"];
zero -> reorder [label="no"];
reorder -> low [label="yes"];
reorder -> healthy [label="no"];
out -> ack [style=dashed,label="optional review"];
low -> ack [style=dashed,label="optional review"];
healthy -> expire;
expire -> change [style=dashed,label="future stock change",constraint=false];
}''')

render('use-cases',"""digraph UseCases { {STYLE}
label="Actors and responsibilities"; rankdir=LR;
admin [label="ADMINISTRATOR",fillcolor="#f0eafa"];manager [label="STORE MANAGER",fillcolor="#e8eefb"];clerk [label="STOCK CLERK",fillcolor="#e7f3ed"];
common [label="Sign in/out · search inventory · inspect history",fillcolor="#f4f6f9"];catalog [label="Manage products, categories, suppliers\\nManage users, roles and settings",fillcolor="#f0eafa"];review [label="Set thresholds · review/acknowledge warnings\\nInspect dashboard and reports",fillcolor="#e8eefb"];move [label="Receive · dispatch · adjust · stocktake\\nRecord reason and auditable movement",fillcolor="#e7f3ed"];
admin->catalog;admin->review;admin->move;admin->common;manager->review;manager->common;clerk->move;clerk->common;
}""")
render('deployment',"""digraph Deployment { {STYLE}
label="Local demonstration deployment"; rankdir=LR;
browser [label="Browser\\nlocalhost:5173",fillcolor="#e8eefb"];
subgraph cluster_host {label="macOS host";color="#d3dbe6";vite [label="Vite dev server :5173\\n/api same-origin proxy",fillcolor="#e8eefb"];java [label="Java 21 + Spring Boot :8080\\nServlet session · Flyway startup",fillcolor="#e7f3ed"];}
subgraph cluster_docker {label="Docker Compose / Colima";color="#d3dbe6";mysql [label="MySQL 8.4.8\\nloopback :3307 → :3306\\nnamed persistent volume",fillcolor="#e7f3ed"];redis [label="Redis 7.4.9\\nloopback :6380 → :6379\\ndisposable cache",fillcolor="#fff3dc"];}
browser->vite [label="HTTP (local)"];vite->java [label="proxy"];java->mysql [label="JDBC"];java->redis [label="Lettuce",style=dashed];
}""")
render('cache-path',"""digraph CachePath { {STYLE}
label="Revision-keyed warning query cache"; rankdir=TB;
read [label="Read revision r from MySQL\\nKey = warning:r:type:state:page:size",fillcolor="#e8eefb"];cache [label="Redis GET\\n30-second TTL",fillcolor="#fff3dc"];hit [label="Deserialize cached warning page\\nreturn same JSON contract",fillcolor="#e7f3ed"];miss [label="Query MySQL with filters before paging\\nmap episode + product + reviewer",fillcolor="#e7f3ed"];set [label="Best-effort SET under revision r\\nTTL reclaims old namespaces",fillcolor="#fff3dc"];write [label="Stock / threshold / acknowledgement write\\nupdates state and increments revision\\nin the same MySQL transaction",fillcolor="#f0eafa"];
read->cache;cache->hit [label="hit"];cache->miss [label="miss / connection failure"];miss->set [label="optional fill"];write->read [label="new reads use r+1",style=dashed];
}""")
render('acknowledgement',"""digraph Ack { {STYLE}
label="Warning acknowledgement request path"; rankdir=TB;
ui [label="Manager opens warning board\\nand selects Acknowledge",fillcolor="#e8eefb"];auth [label="POST /warnings/{id}/ack\\nsession + role + CSRF validation",fillcolor="#f0eafa"];mysql [label="Load warning episode\\nif already acknowledged: preserve first reviewer\\notherwise save actor + timestamp",fillcolor="#e7f3ed"];revision [label="Commit acknowledgement + revision\\nstock and lifecycle remain unchanged",fillcolor="#fff3dc"];refresh [label="Reload board with new revision key\\nshow reviewer name and reviewed status",fillcolor="#e8eefb"];ui->auth->mysql->revision->refresh;
}""")
