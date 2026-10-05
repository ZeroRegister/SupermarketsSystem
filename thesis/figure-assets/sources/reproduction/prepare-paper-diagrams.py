#!/usr/bin/env python3
"""Create evidence-aligned, editable diagrams for the Shelfwise figure collection."""
from pathlib import Path
from xml.etree import ElementTree as E
import json,re,subprocess,sys,shutil,tempfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'thesis/figure-assets';D=OUT/'diagrams';D.mkdir(parents=True,exist_ok=True)
DRAW='/Applications/draw.io.app/Contents/MacOS/draw.io'
BASE='whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=16;fontColor=#111111;strokeColor=#333333;strokeWidth=1.3;'
registry=[]
class Diagram:
 def __init__(self,name,title,chapter,source):
  self.name=name;self.meta=dict(id=name,title=title,chapter=chapter,type='diagram',source=source,files=[f'diagrams/{name}.drawio',f'diagrams/{name}.png',f'diagrams/{name}.svg'])
  self.xml=E.Element('mxfile',host='drawio',version='26.1.1');p=E.SubElement(self.xml,'diagram',name=title);self.model=E.SubElement(p,'mxGraphModel',grid='1',gridSize='10',page='0',background='#ffffff');self.root=E.SubElement(self.model,'root');E.SubElement(self.root,'mxCell',id='0');E.SubElement(self.root,'mxCell',id='1',parent='0');self.n=1
 def node(self,label,x,y,w=240,h=80,style='',parent='1'):
  self.n+=1;i=str(self.n);c=E.SubElement(self.root,'mxCell',id=i,value=label,style=BASE+'rounded=0;fillColor=#ffffff;'+style,vertex='1',parent=parent);E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'});return i
 def edge(self,a,b,label='',style='',points=None):
  self.n+=1;c=E.SubElement(self.root,'mxCell',id=str(self.n),value=label,style=BASE+'edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;fontSize=13;whiteSpace=nowrap;labelBackgroundColor=#ffffff;endArrow=block;endFill=1;'+style,edge='1',parent='1',source=a,target=b);g=E.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'})
  if points:
   arr=E.SubElement(g,'Array',attrib={'as':'points'})
   for x,y in points:E.SubElement(arr,'mxPoint',x=str(x),y=str(y))
 def line(self,x1,y1,x2,y2,label='',style=''):
  self.n+=1;c=E.SubElement(self.root,'mxCell',id=str(self.n),value=label,style=BASE+'endArrow=block;endFill=1;fontSize=14;whiteSpace=nowrap;verticalAlign=bottom;labelBackgroundColor=#ffffff;'+style,edge='1',parent='1');g=E.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'});E.SubElement(g,'mxPoint',x=str(x1),y=str(y1),attrib={'as':'sourcePoint'});E.SubElement(g,'mxPoint',x=str(x2),y=str(y2),attrib={'as':'targetPoint'})
 def save(self):
  E.indent(self.xml);E.ElementTree(self.xml).write(D/f'{self.name}.drawio',encoding='utf-8',xml_declaration=True);registry.append(self.meta)
def simple(name,title,chapter,labels,source):
 d=Diagram(name,title,chapter,source);ids=[d.node(t,60,40+i*140,560,80,('ellipse;' if chapter==4 and i in (0,len(labels)-1) else '')) for i,t in enumerate(labels)]
 for a,b in zip(ids,ids[1:]):d.edge(a,b,style='exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
 d.save()
# Object analysis: function decomposition and module-specific UML use cases.
d=Diagram('01-functional-model','Overall functional model',1,['docs/requirements.md','frontend/src/views/WorkspaceView.vue']);hub=d.node('Shelfwise\nSupermarket inventory management',440,40,340,80)
mods=[('Identity and access',['Sign in / sign out','Manage staff and roles']),('Catalogue',['Products and thresholds','Categories and suppliers']),('Stock activity',['Receive / dispatch','Adjust / stocktake']),('Stock warnings',['Shortage episodes','Review and acknowledge']),('Reporting',['Inventory summary','Movement history / CSV'])]
for i,(title,items) in enumerate(mods):
 x=20+i*270;n=d.node(title,x,240,240,60,'fillColor=#f3f3f3;');d.edge(hub,n,style=f'exitX={(i+1)/6};exitY=1;entryX=0.5;entryY=0;',points=[(x+120,190)])
 for j,t in enumerate(items):
  q=d.node(t,x,370+j*110,240,65);d.edge(n,q,style=f'exitX={.3+j*.4};exitY=1;entryX=0.5;entryY=0;',points=[(x-15 if j==1 else x+120,340+j*110)] if j==1 else None)
d.save()
def usecase(name,title,rows):
 d=Diagram(name,title+' use cases',1,['backend/src/main/java/com/shelfwise/SecurityConfig.java','docs/requirements.md'])
 actions=list(dict.fromkeys(action for role,acts in rows for action in acts));height=100+len(actions)*140
 boundary=d.node(title,240,20,620,height,'swimlane;startSize=40;container=1;pointerEvents=0;fontStyle=1;')
 cases={action:d.node(action,60,70+i*140,500,85,'ellipse;',parent=boundary) for i,action in enumerate(actions)}
 for role,acts in rows:
  if role=='Administrator':x,y=20,110
  elif role=='Stock clerk':x,y=20,max(340,height-220)
  else:x,y=930,height//2-40
  actor=d.node(role,x,y,130,120,'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;')
  for action in acts:
   d.edge(actor,cases[action],style='edgeStyle=none;endArrow=none;exitX='+('0' if x>240 else '1')+';exitY=0.35;exitPerimeter=0;entryX='+('1' if x>240 else '0')+';entryY=0.5;')
 d.save()
usecase('02-uc-catalogue','Catalogue management',[('Administrator',['Inspect inventory','Create or edit product','Archive product','Manage categories / suppliers','Update stock thresholds']),('Store manager',['Inspect inventory','Update stock thresholds']),('Stock clerk',['Inspect inventory'])])
usecase('03-uc-stock','Stock activity',[('Administrator',['Receive stock','Dispatch stock','Adjust quantity','Record stocktake','Inspect movement history']),('Stock clerk',['Receive stock','Dispatch stock','Adjust quantity','Record stocktake','Inspect movement history']),('Store manager',['Inspect movement history'])])
usecase('04-uc-warning','Warning management',[('Administrator',['Inspect shortage and recovery','Acknowledge warning']),('Store manager',['Inspect shortage and recovery','Acknowledge warning'])])
usecase('05-uc-report','Inventory reporting',[('Administrator',['Inspect dashboard and reports','Export current inventory page']),('Store manager',['Inspect dashboard and reports','Export current inventory page']),('Stock clerk',['Inspect stock summary','Export current inventory page'])])
usecase('06-uc-access','Identity and administration',[('Administrator',['Sign in / sign out','Manage staff accounts and roles','Edit store settings']),('Store manager',['Sign in / sign out']),('Stock clerk',['Sign in / sign out'])])
# Permission model: fixed roles, no invented hierarchy.
d=Diagram('07-permission-model','Fixed role authorization model',2,['backend/src/main/java/com/shelfwise/SecurityConfig.java']);
for i,(role,rights) in enumerate([('ADMIN','All catalogue operations\nAll stock operations\nWarnings and reports\nUsers and store settings'),('MANAGER','Read inventory and history\nUpdate thresholds\nReview / acknowledge warnings\nRead dashboard and reports'),('CLERK','Read inventory and history\nReceive / dispatch stock\nAdjust / stocktake\nRead stock summary')]):
 r=d.node(role,40+i*370,40,310,60,'fillColor=#f3f3f3;fontStyle=1;');n=d.node(rights,40+i*370,170,310,200);d.edge(r,n,style='exitX=0.5;exitY=1;entryX=0.5;entryY=0;')
d.node('Roles are fixed enum values; there is no role inheritance.\nServer checks permissions on each request; UI navigation is an additional guard.',40,440,1050,70,'strokeColor=none;fontSize=14;');d.save()
simple('08-runtime-architecture','Layered runtime architecture',3,['Browser on desktop or phone\nResponsive Vue 3 interface','Vue Router / Pinia / Axios / Element Plus / ECharts\nREST JSON + session cookie + CSRF header','Spring Boot modular monolith\nSecurity filters → controllers → inventory service','Spring Data JPA repositories\nTransactional writes and pessimistic product locking','MySQL durable state\nRedis optional warning-page cache (30 s)'],['docs/architecture.md','frontend/package.json','backend/pom.xml'])
simple('09-frontend-structure','Frontend module structure',3,['Vue application / App.vue','Router guards and auth store\nSession restoration / role-aware views','LoginView.vue and WorkspaceView.vue\nInventory / catalogue / stock / warnings / reports / administration','Typed API client and domain types\nAxios request / response interceptors','Spring Boot REST API'],['frontend/src/router.ts','frontend/src/views/WorkspaceView.vue','frontend/src/api.ts'])
simple('10-backend-structure','Backend module structure',3,['Spring Security filter chain\nSession authentication / role refresh / CSRF','REST controllers\nEndpoint mapping / validated inputs / errors','InventoryService\nCatalogue / movements / warning episodes / reports','Spring Data repositories\nJpaRepository / query predicates / pessimistic locks','Domain entities and Flyway schema\nMySQL persistence + optional Redis read cache'],['backend/src/main/java/com/shelfwise/Controllers.java','backend/src/main/java/com/shelfwise/InventoryService.java','backend/src/main/java/com/shelfwise/Repositories.java'])
# Schema figures are derived from the migration, including nullable FK cardinality.
sql=(ROOT/'backend/src/main/resources/db/migration/V1__initial_schema.sql').read_text();tables={}
for name,body in re.findall(r'CREATE TABLE (\w+)\s*\((.*?)\);',sql,re.S):
 fields=[]
 for m in re.finditer(r'(?:^|,)\s*(\w+)\s+(BIGINT|VARCHAR\(\d+\)|DECIMAL\(\d+,\d+\)|BOOLEAN|TIMESTAMP\(\d+\))([^,]*)(?=,|$)',body):
  f,typ,tail=m.groups();mark='PK' if 'PRIMARY KEY' in tail else ('FK' if f in ['category_id','supplier_id','product_id','actor_id','acknowledged_by'] else ('UK' if 'UNIQUE' in tail else ''))
  fields.append(f'{mark:2}  {f} : {typ}')
 tables[name]=fields
relations=[('categories','products','category_id','optional'),('suppliers','products','supplier_id','optional'),('users','inventory_transactions','actor_id','required'),('products','inventory_transactions','product_id','required'),('users','warnings','acknowledged_by','optional'),('products','warnings','product_id','required')]
def er(name,title,names,positions):
 d=Diagram(name,title,3,['backend/src/main/resources/db/migration/V1__initial_schema.sql']);ids={}
 for table in names:
  x,y=positions[table];height=44+26*len(tables[table]);box=d.node(table,x,y,360,height,'swimlane;startSize=38;fontStyle=1;container=1;pointerEvents=0;fillColor=#eef3f8;')
  d.node('<div style="text-align:left;font-family:monospace;font-size:14px;line-height:26px">'+'<br>'.join(tables[table])+'</div>',0,38,360,height-38,'strokeColor=none;align=left;spacingLeft=12;verticalAlign=top;',box);ids[table]=box
 for i,(a,b,fk,opt) in enumerate(relations):
  if a not in ids or b not in ids:continue
  ax,ay=positions[a];bx,by=positions[b];same=ay==by
  style=('exitX=1;exitY=0.5;entryX=0;entryY=0.5;' if ax<bx else 'exitX=0;exitY=0.5;entryX=1;entryY=0.5;') if same else f'exitX={.25 if i%2 else .75};exitY=1;entryX={.25 if i%2 else .75};entryY=0;'
  points=None
  if len(names)>4 and a=='users':
   if b=='inventory_transactions':style='exitX=0;exitY=0.7;entryX=1;entryY=0.25;';points=[(450,220),(450,1060)]
   else:style='exitX=1;exitY=0.7;entryX=0;entryY=0.25;';points=[(900,220),(900,1060)]
  edge_name=('actor' if b=='inventory_transactions' else 'reviewer') if len(names)>4 and a=='users' else fk
  d.edge(ids[a],ids[b],edge_name+'\n1 : 0..*' if opt=='required' else edge_name+'\n0..1 : 0..*',style+'endArrow=ERzeroToMany;startArrow='+('ERmandOne' if opt=='required' else 'ERzeroToOne')+';endFill=0;startFill=0;',points=points)
 if len(names)>4:d.node('app_settings and cache_revision are independent tables.\nUNIQUE(actor_id, idempotency_key) prevents duplicate stock submissions.',40,1360,1200,60,'strokeColor=none;fontSize=14;')
 d.save()
er('11-er-overall','Overall relational schema',list(tables),{'categories':(40,40),'suppliers':(940,40),'users':(490,40),'products':(490,420),'inventory_transactions':(40,980),'warnings':(940,980),'app_settings':(40,550),'cache_revision':(940,550)})
er('12-er-catalogue','Product category and supplier relationships',['categories','products','suppliers'],{'categories':(40,40),'suppliers':(900,40),'products':(470,340)})
er('13-er-movements','Stock audit relationships',['users','products','inventory_transactions'],{'users':(40,40),'products':(920,40),'inventory_transactions':(480,570)})
er('14-er-warnings','Warning episode and reviewer relationships',['users','products','warnings'],{'users':(40,40),'products':(920,40),'warnings':(480,570)})
er('15-er-support','Settings and cache revision tables',['app_settings','cache_revision'],{'app_settings':(40,40),'cache_revision':(520,40)})
# UML domain classes: attributes and associations correspond to Domain.java.
d=Diagram('16-uml-domain','Core domain UML class diagram',3,['backend/src/main/java/com/shelfwise/Domain.java']);spec=[('Product','~ quantity: long<br>~ reorderThreshold: long<br>~ active: boolean<br>~ version: long'),('UserAccount','~ username: String<br>~ role: Role<br>~ enabled: boolean'),('InventoryTransaction','~ type: MovementType<br>~ delta: long<br>~ quantityBefore: long<br>~ quantityAfter: long<br>~ idempotencyKey: String'),('WarningEpisode','~ type: WarningType<br>~ state: WarningState<br>~ acknowledgedAt: Instant<br>~ expiresAt: Instant')];ids={}
for i,(title,attrs) in enumerate(spec):
 x=40+(i%2)*580;y=40+(i//2)*380;n=d.node(title,x,y,390,230,'swimlane;startSize=40;container=1;fontStyle=1;');d.node('<div style="text-align:left">'+attrs+'</div>',0,40,390,190,'strokeColor=none;align=left;spacingLeft=20;',n);ids[title]=n
for a,b,label,style,points in [
 ('Product','InventoryTransaction','product: 1 to 0..*','exitX=0.3;exitY=1;entryX=0.3;entryY=0;',None),
 ('UserAccount','WarningEpisode','reviewer: 0..1 to 0..*','exitX=0.7;exitY=1;entryX=0.7;entryY=0;',None),
 ('Product','WarningEpisode','product: 1 to 0..*','exitX=0.75;exitY=1;entryX=0.3;entryY=0;',[(332,365),(737,365)]),
 ('UserAccount','InventoryTransaction','actor: 1 to 0..*','exitX=0.25;exitY=1;entryX=0.6;entryY=0;',[(717,315),(274,315)])]:
 d.edge(ids[a],ids[b],label,'endArrow=none;'+style,points=points)

d.save()
d=Diagram('17-uml-service','Service and repository UML dependencies',3,['backend/src/main/java/com/shelfwise/InventoryService.java','backend/src/main/java/com/shelfwise/Repositories.java']);svc=d.node('InventoryService',420,40,480,260,'swimlane;startSize=40;fontStyle=1;container=1;');d.node('<div style="text-align:left">~ move(input, username): TransactionView<br>~ updateWarning(product): void<br>~ warningPage(...): PageResult<br>~ acknowledge(id, username): WarningView<br>~ dashboard(): DashboardView<br>~ report(): Map</div>',0,40,480,220,'strokeColor=none;align=left;spacingLeft=20;',svc)
for i,name in enumerate(['ProductRepository','TransactionRepository','WarningRepository','CacheRevisionRepository']):
 n=d.node('«interface»<br>'+name,40+i*340,460,300,90);d.edge(svc,n,'uses','dashed=1;endArrow=open;exitX='+str((i+1)/5)+';exitY=1;entryX=0.5;entryY=0;')
d.save()
def sequence(name,title,participants,messages):
 d=Diagram(name,title,4,['backend/src/main/java/com/shelfwise/InventoryService.java','backend/src/main/java/com/shelfwise/SecurityConfig.java']);xs=[120+i*300 for i in range(len(participants))];end=160+len(messages)*85
 for x,p in zip(xs,participants):d.node(p,x-115,30,230,65,'fillColor=#f3f3f3;');d.line(x,95,x,end,'','dashed=1;endArrow=none;strokeColor=#888888;')
 for i,(a,b,label,ret) in enumerate(messages):
  y=160+i*85
  if a==b:
   d.line(xs[a],y,xs[a]+80,y,label,'endArrow=none;');d.line(xs[a]+80,y,xs[a]+80,y+30,'','endArrow=none;');d.line(xs[a]+80,y+30,xs[a],y+30,'','endArrow=open;')
  else:d.line(xs[a],y,xs[b],y,label,('dashed=1;endArrow=open;' if ret else 'endArrow=block;'))
 d.save()
sequence('18-seq-login','Session authentication sequence',['Browser','AuthController','AuthenticationManager','UserRepository / MySQL','HttpSession'],[(0,1,'GET /auth/csrf',False),(1,0,'CSRF token',True),(0,1,'POST /auth/login + CSRF',False),(1,2,'authenticate credentials',False),(2,3,'load enabled account / password hash',False),(3,2,'account and role',True),(2,1,'authenticated principal',True),(1,4,'rotate session ID / store context',False),(1,0,'UserView + session cookie',True)])
sequence('19-seq-stock','Audited stock movement sequence',['Browser','Controller','InventoryService','MySQL'],[(0,1,'POST /transactions + request key',False),(1,2,'move(input, authenticated actor)',False),(2,3,'lock product row',False),(3,2,'current product quantity',True),(2,3,'find actor + idempotency key',False),(3,2,'prior result or absent',True),(2,2,'check replay / bounds',False),(2,3,'write quantity + audit + warnings + revision',False),(3,2,'transaction commit',True),(2,1,'TransactionView',True),(1,0,'201 + movement result',True)])
sequence('20-seq-warning','Warning page cache sequence',['Browser','InventoryService','MySQL','Redis'],[(0,1,'GET /warnings',False),(1,2,'read cache_revision',False),(2,1,'revision',True),(1,3,'GET warning:{revision}:filters',False),(3,1,'cached JSON or miss / failure',True),(1,2,'on miss: query filtered warning page',False),(2,1,'warning page',True),(1,3,'best effort SET + 30 s TTL',False),(1,0,'same PageResult contract',True)])
simple('21-stock-flow','Stock movement transaction workflow',4,['Authenticated ADMIN or CLERK submits movement','Acquire product lock and reject archived products','Check actor + request key\nEqual replay returns existing result; mismatch returns 409','Derive signed delta or absolute stocktake delta\nCheck 0 ≤ new quantity ≤ 1,000,000,000','Write product quantity and immutable movement audit\nUpdate warning episodes and increment cache revision','Commit transaction and return movement view\nAny exception rolls back the transaction'],['backend/src/main/java/com/shelfwise/InventoryService.java'])
d=Diagram('22-warning-state','Stock warning episode lifecycle',3,['backend/src/main/java/com/shelfwise/InventoryService.java']);healthy=d.node('Healthy stock\nq > threshold',390,40,310,100,'rounded=1;');low=d.node('LOW episode / OPEN\n0 < q ≤ threshold',40,280,310,110,'rounded=1;');out=d.node('OUT episode / OPEN\nq = 0',740,280,310,110,'rounded=1;');rest=d.node('RESTOCKED episode / OPEN\n24-hour visibility',390,570,310,110,'rounded=1;')
d.edge(healthy,low,'threshold crossed','exitX=0.2;exitY=1;entryX=0.5;entryY=0;');d.edge(healthy,out,'quantity becomes zero','exitX=0.8;exitY=1;entryX=0.5;entryY=0;');d.edge(low,out,'q becomes zero\nclose old severity','exitX=1;exitY=0.3;entryX=0;entryY=0.3;');d.edge(out,low,'0 < q ≤ threshold\nclose old severity','exitX=0;exitY=0.75;entryX=1;entryY=0.75;',points=[(670,450),(410,450)]);d.edge(low,rest,'q > threshold\nresolve shortage','exitX=0.5;exitY=1;entryX=0;entryY=0.5;');d.edge(out,rest,'q > threshold\nresolve shortage','exitX=0.5;exitY=1;entryX=1;entryY=0.5;');d.edge(rest,healthy,'expires: mark RESOLVED','exitX=1;exitY=0.8;entryX=1;entryY=0.5;',points=[(1150,660),(1150,90)]);d.node('Acknowledgement is independent of OPEN / RESOLVED state.\nRenewed shortage resolves RESTOCKED and opens LOW or OUT.\nArchive resolves open episodes; same severity retains the reviewer.',40,800,1010,100,'strokeColor=none;fontSize=15;');d.save()
simple('23-security-flow','Request authentication and authorization',3,['Request with host-only session cookie','Restore SecurityContext / require CSRF for unsafe requests\nMissing CSRF token → HTTP 403','Refresh account enabled flag and current role from MySQL','Apply method / endpoint role rules\nAnonymous → 401; disallowed role → 403','Validate request fields and execute controller\nActor identity comes from server authentication'],['backend/src/main/java/com/shelfwise/SecurityConfig.java'])
d=Diagram('24-deployment','Implemented local deployment topology',4,['docker-compose.yml','frontend/vite.config.ts','backend/src/main/resources/application.yml']);browser=d.node('Browser',40,40,300,70);vue=d.node('Vite dev server\nlocalhost:5173',40,230,300,100);spring=d.node('Spring Boot / Java 21\nlocalhost:8080',40,460,300,100);mysql=d.node('Docker Compose: MySQL 8.4\nlocalhost:3307 → 3306\nmysql-data persistent volume',530,350,420,120,'shape=cylinder3;');redis=d.node('Docker Compose: Redis 7.4\nlocalhost:6380 → 6379\nOptional volatile cache',530,620,420,120,'shape=cylinder3;');d.edge(browser,vue,'HTTP','exitX=0.5;exitY=1;entryX=0.5;entryY=0;');d.edge(vue,spring,'/api proxy','exitX=0.5;exitY=1;entryX=0.5;entryY=0;');d.edge(spring,mysql,'JDBC / transactions','exitX=1;exitY=0.25;entryX=0;entryY=0.5;');d.edge(spring,redis,'cache reads / best effort writes','exitX=1;exitY=0.75;entryX=0;entryY=0.5;');d.save()
(OUT/'sources/diagram-manifest.json').write_text(json.dumps(registry,indent=2))
if '--no-export' not in sys.argv:
 with tempfile.TemporaryDirectory(prefix='shelfwise-drawio-') as staging:
  for file in D.glob('*.drawio'):shutil.copy2(file,Path(staging)/file.name)
  logs=[]
  for fmt in ('svg','png'):
   cmd=[DRAW,'-x','-f',fmt,'-b','20','-o',str(D)]
   if fmt=='png':cmd+=['-s','2']
   cmd+=[staging];r=subprocess.run(cmd,capture_output=True,text=True);logs.append(r.stdout+r.stderr)
   if r.returncode or 'Error: Export failed' in r.stdout+r.stderr:raise RuntimeError(r.stdout+r.stderr)
  (OUT/'sources/drawio-export.log').write_text('\n'.join(logs))
print('Prepared',len(registry),'editable diagrams')
