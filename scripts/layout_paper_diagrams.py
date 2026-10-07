"""Explicit routing and separate labels for the thesis's editable diagrams.

Draw.io's automatic edge-label placement cannot reserve space around other
vertices. These layouts use fixed waypoints and independent text boxes so
regeneration preserves the reviewed layout.
"""
from xml.etree import ElementTree as E


def path(d, points, label='', at=None, width=240, dashed=False, arrow=True):
    """An editable polyline with an explicitly positioned, opaque label."""
    d.n += 1
    c = E.SubElement(d.root, 'mxCell', id=str(d.n), parent='1', edge='1',
        style='html=1;rounded=0;strokeColor=#444444;strokeWidth=1.4;'
        'endArrow=' + ('block' if arrow else 'none') + ';endFill=1;'
        + ('dashed=1;' if dashed else ''))
    g = E.SubElement(c, 'mxGeometry', relative='1', attrib={'as': 'geometry'})
    for role, (x, y) in [('sourcePoint', points[0]), ('targetPoint', points[-1])]:
        E.SubElement(g, 'mxPoint', x=str(x), y=str(y), attrib={'as': role})
    if len(points) > 2:
        arr = E.SubElement(g, 'Array', attrib={'as': 'points'})
        for x, y in points[1:-1]:
            E.SubElement(arr, 'mxPoint', x=str(x), y=str(y))
    if label:
        assert at is not None
        height = 28 * (label.count('\n') + 1) + 8
        d.node(label, at[0], at[1], width, height,
               'strokeColor=none;fillColor=#ffffff;fontSize=20;')


def repair_layouts(diagrams, factory, tables):
    def fresh(name):
        old = diagrams[name]
        d = factory(name, old.meta['title'], old.meta['chapter'], old.meta['source'])
        d.meta = old.meta
        diagrams[name] = d
        return d

    # Actors occupy distinct vertical positions; associations have no arrowhead.
    for name in ['02-uc-catalogue', '03-uc-stock', '04-uc-warning',
                 '05-uc-report', '06-uc-access']:
        old = diagrams[name]
        cells = {c.get('id'): c for c in old.root.findall('mxCell')}
        associations = {}
        for c in cells.values():
            if c.get('edge') == '1':
                role = cells[c.get('source')].get('value')
                action = cells[c.get('target')].get('value')
                associations.setdefault(role, []).append(action)
        if name == '03-uc-stock':
            associations = {
                'Administrator': ['Receive stock', 'Dispatch / record SALE', 'Adjust / count directly',
                                  'Submit count / disposal review', 'Inspect movement history',
                                  'Approve count / disposal review'],
                'Stock clerk': ['Receive stock', 'Dispatch / record SALE',
                                'Submit count / disposal review', 'Inspect movement history'],
                'Store manager': ['Approve count / disposal review', 'Inspect movement history']}
        actions = list(dict.fromkeys(a for values in associations.values() for a in values))
        d = fresh(name)
        h = 110 + len(actions) * 125
        d.node(old.meta['title'].replace(' use cases', ''), 280, 20, 580, h,
               'swimlane;startSize=50;fontStyle=1;fontSize=24;')
        for i, action in enumerate(actions):
            d.node(action, 330, 100+i*125, 480, 76, 'ellipse;')
        left = [r for r in associations if r != 'Store manager']
        for role, acts in associations.items():
            right = role == 'Store manager'
            y = h / 2 - 50 if right else (80 if left.index(role) == 0 else h - 180)
            x = 940 if right else 10
            d.node(role, x, y, 160, 105,
                   'shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;fontSize=22;')
            for j, action in enumerate(acts):
                cy = 138 + actions.index(action)*125
                # Straight UML associations may cross each other in the empty
                # corridor, but never traverse an actor's label or another case.
                path(d, [(x if right else x+160, y+30+j*6),
                         (810 if right else 330, cy)], arrow=False)

    d = fresh('01-functional-model')
    modules = [('Identity and access', ['Sign in / sign out', 'Staff, roles and settings']),
               ('Catalog', ['Products and thresholds', 'Categories and suppliers']),
               ('Stock activity', ['Receive / dispatch / SALE', 'Adjust, count and history']),
               ('Batches and reviews', ['Batch balances and quarantine', 'Count / disposal review']),
               ('Warnings', ['Quantity, expiry and slow rules', 'Review and acknowledge']),
               ('Purchasing', ['Replenishment suggestions', 'Approval and receipts']),
               ('Reporting', ['Dashboard and reports', 'Inventory CSV export'])]
    pitch, top = 150, 20
    centers = [top + 65 + i*pitch for i in range(len(modules))]
    hub_y = (centers[0] + centers[-1]) / 2
    d.node('Shelfwise', 20, hub_y-50, 220, 100, 'rounded=1;fontStyle=1;fontSize=26;')
    path(d, [(240, hub_y), (300, hub_y)], arrow=False)
    path(d, [(300, centers[0]), (300, centers[-1])], arrow=False)
    for (title, leaves), cy in zip(modules, centers):
        path(d, [(300, cy), (360, cy)])
        d.node(title, 360, cy-32, 290, 64, 'fillColor=#f3f3f3;fontStyle=1;')
        path(d, [(650, cy), (700, cy)], arrow=False)
        ys = [cy-33, cy+33]
        path(d, [(700, ys[0]), (700, ys[1])], arrow=False)
        for leaf, ly in zip(leaves, ys):
            path(d, [(700, ly), (750, ly)])
            d.node(leaf, 750, ly-28, 380, 56, 'align=left;spacingLeft=16;')

    # Figure 2.1: one card per fixed role; the administrator card lists only what
    # it adds to the other two, matching the authorization matrix in Chapter 3.
    d = fresh('07-permission-model')
    cards = [
        ('ADMIN', ['All manager and clerk', 'operations, plus:', '• Product identity and archival',
                   '• Staff accounts and roles', '• Store settings', '• Direct adjustments and counts']),
        ('MANAGER', ['• Inventory and history', '• Thresholds and target stock', '• Warning review and reports',
                     '• Stock-review approval', '• Purchase drafts and approval', '• Batch quarantine']),
        ('CLERK', ['• Inventory and history', '• Receipts, dispatches, SALE', '• Count / disposal requests',
                   '• Purchase drafts', '• Purchase receipts', '• Stock summary'])]
    for i, (role, lines) in enumerate(cards):
        x = 20 + i*400
        box = d.node(role, x, 20, 370, 290, 'swimlane;startSize=56;fontStyle=1;fontSize=24;fillColor=#f3f3f3;container=1;')
        d.node('<br>'.join(lines), 0, 56, 370, 234,
               'strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=22;spacingTop=14;fontSize=22;', box)

    # Runtime arrows and image-distribution information occupy separate regions.
    for name in ['08-runtime-architecture', '24-deployment']:
        d = fresh(name)
        release = name == '24-deployment'
        d.node('Windows browser' if release else 'Browser\ndesktop or phone', 330, 30, 380, 80, '')
        d.node('Frontend container\nNginx + compiled Vue client\n127.0.0.1:5173', 330, 230, 380, 120, '')
        d.node('Backend container\nSpring Boot / Java 21\nPrivate Compose network', 330, 490, 380, 120, '')
        d.node('MySQL 8.4\nDurable business state\nmysql-data volume', 30, 820, 380, 150, 'shape=cylinder3;spacingTop=22;')
        d.node('Redis 7.4\nRevision-keyed cache\nDisposable state', 630, 820, 380, 150, 'shape=cylinder3;spacingTop=22;')
        path(d, [(520,110),(520,230)], 'HTTP', (550,145), 150)
        path(d, [(520,350),(520,490)], '/api proxy', (550,390), 210)
        path(d, [(420,610),(420,700),(220,700),(220,820)], 'JPA / Flyway', (90,725), 260)
        path(d, [(620,610),(620,700),(820,700),(820,820)], 'Cache reads / writes', (675,725), 300)

    # The overall ER image intentionally depicts V1 only; later schema layers
    # are documented in the text, rather than implying an exhaustive current ER.
    positions = {'users':(40,40), 'products':(720,40),
                 'inventory_transactions':(40,650), 'warnings':(720,650),
                 'categories':(40,1230), 'suppliers':(720,1230),
                 'app_settings':(40,1610), 'cache_revision':(720,1610)}
    subsets = {
        '11-er-overall': (list(tables), positions),
        '12-er-catalogue': (['categories','suppliers','products'],
             {'categories':(40,40),'suppliers':(720,40),'products':(380,420)}),
        '13-er-movements': (['users','products','inventory_transactions'],
             {'users':(40,40),'products':(720,40),'inventory_transactions':(380,540)}),
        '14-er-warnings': (['users','products','warnings'],
             {'users':(40,40),'products':(720,40),'warnings':(380,540)}),
        '15-er-support': (['app_settings','cache_revision'],
             {'app_settings':(40,40),'cache_revision':(720,40)})}
    rels = [('categories','products','category_id','0..1'),
            ('suppliers','products','supplier_id','0..1'),
            ('users','inventory_transactions','actor_id','1'),
            ('products','inventory_transactions','product_id','1'),
            ('users','warnings','acknowledged_by','0..1'),
            ('products','warnings','product_id','1')]
    for name, (names, pos) in subsets.items():
        d = fresh(name)
        if name not in ['11-er-overall', '15-er-support']:
            parents = names[:2]
            child = names[2]
            parent_bottom = max(pos[n][1]+50+32*len(tables[n]) for n in parents)
            pos[child] = (pos[child][0], parent_bottom+300)
        heights = {}
        for table in names:
            x,y = pos[table]
            height = 50+32*len(tables[table])
            heights[table] = height
            box = d.node(table, x,y,440,height,
                         'swimlane;startSize=44;fontStyle=1;container=1;fillColor=#f3f3f3;')
            d.node('<div style="text-align:left;font-family:monospace;font-size:19px;line-height:32px">'
                   + '<br>'.join(tables[table]) + '</div>', 0,44,440,height-44,
                   'strokeColor=none;align=left;spacingLeft=12;verticalAlign=top;',box)
        if name == '11-er-overall':
            path(d, [(260,40+heights['users']),(260,650)], 'actor_id\n1 : 0..*', (40,460), 210, arrow=False)
            path(d, [(940,40+heights['products']),(940,650)], 'product_id\n1 : 0..*', (720,555), 210, arrow=False)
            path(d, [(480,100),(570,100),(570,740),(720,740)], 'acknowledged_by\n0..1 : 0..*', (500,200), 210, arrow=False)
            path(d, [(720,280),(650,280),(650,920),(480,920)], 'product_id\n1 : 0..*', (500,1020), 210, arrow=False)
            path(d, [(260,1230),(260,1180),(0,1180),(0,10),(820,10),(820,40)],
                 'category_id\n0..1 : 0..*', (30,1120), 210, arrow=False)
            path(d, [(1160,1290),(1450,1290),(1450,330),(1160,330)],
                 'supplier_id\n0..1 : 0..*', (1270,760), 270, arrow=False)
        else:
            selected = [r for r in rels if r[0] in names and r[1] in names]
            for j,(a,b,fk,cardinality) in enumerate(selected):
                ax,ay=pos[a];bx,by=pos[b]
                sx=ax+220; tx=bx+(120 if j==0 else 320)
                lane=by-150+(j*70)
                path(d, [(sx,ay+heights[a]),(sx,lane),(tx,lane),(tx,by)],
                     fk+'\n'+cardinality+' : 0..*',
                     (300 if j==0 else 650, lane-70),250,arrow=False)

    d = fresh('16-uml-domain')
    # K2,2 can be drawn without crossings: four classes on a diamond, with
    # the associations following its four sides.
    specs=[('Product',390,20,'quantity: long\nsellableQuantity: long\nreorderThreshold: long\nversion: long'),
           ('InventoryTransaction',40,390,'type: MovementType\ndelta: long\nquantityBefore: long\nquantityAfter: long\nidempotencyKey: String'),
           ('WarningEpisode',740,390,'type: WarningType\nstate: WarningState\nacknowledgedAt: Instant\nexpiresAt: Instant'),
           ('UserAccount',390,800,'username: String\nrole: Role\nenabled: boolean')]
    for title,x,y,attrs in specs:
        d.node(title,x,y,350,240,'swimlane;startSize=44;fontStyle=1;fillColor=#f3f3f3;')
        d.node(attrs,x+10,y+55,330,170,'strokeColor=none;align=left;spacingLeft=10;')
    path(d,[(440,260),(440,320),(215,320),(215,390)],'product\n1 : 0..*',(80,245),230,arrow=False)
    path(d,[(690,260),(690,320),(915,320),(915,390)],'product\n1 : 0..*',(805,245),230,arrow=False)
    path(d,[(440,800),(440,730),(215,730),(215,630)],'actor\n1 : 0..*',(100,735),210,arrow=False)
    path(d,[(690,800),(690,730),(915,730),(915,630)],'reviewer\n0..1 : 0..*',(820,735),230,arrow=False)

    d = fresh('17-uml-service')
    d.node('InventoryService',20,310,440,250,'swimlane;startSize=44;fontStyle=1;fillColor=#f3f3f3;')
    d.node('move(input, actor)\nupdateWarning(product)\nwarningPage(filters)\nacknowledge(id, actor)\ndashboard() / report()',40,365,400,180,'strokeColor=none;align=left;')
    path(d,[(460,435),(600,435)],dashed=True,arrow=False)
    path(d,[(600,62),(600,692)],dashed=True,arrow=False)
    for i,name in enumerate(['ProductRepository','TransactionRepository','WarningRepository','CacheRevisionRepository']):
        y=20+i*210
        d.node('«interface»\n'+name,740,y,440,85)
        path(d,[(600,y+42),(740,y+42)],'uses',(625,y-1),95,dashed=True)

    # Sequence messages use a large font and independent labels; the self-call
    # reserves its own row and does not put text over a lifeline.
    for name in ['18-seq-login','19-seq-stock','20-seq-warning']:
        old=diagrams[name]
        participants=[c.get('value') for c in old.root.findall('mxCell') if c.get('vertex')=='1']
        messages=[]
        for c in old.root.findall('mxCell'):
            if c.get('edge')=='1' and c.get('value'):
                g=c.find('mxGeometry')
                s=g.find("mxPoint[@as='sourcePoint']");t=g.find("mxPoint[@as='targetPoint']")
                a=round((float(s.get('x'))-120)/300)
                b=round((float(t.get('x'))-120)/300)
                messages.append((a,b,c.get('value'),'dashed=1' in c.get('style')))
        d=fresh(name); xs=[150+i*340 for i in range(len(participants))]
        height=160+len(messages)*110
        for x,p in zip(xs,participants):
            d.node(p,x-140,20,280,90,'fillColor=#f3f3f3;fontSize=24;')
            path(d,[(x,110),(x,height)],dashed=True,arrow=False)
        for i,(a,b,label,ret) in enumerate(messages):
            y=195+i*110
            # Explicitly break the longest adjacent-participant message.
            label=label.replace('load enabled account / password hash','load account /\npassword hash')
            if a==b:
                path(d,[(xs[a],y),(xs[a]+100,y),(xs[a]+100,y+35),(xs[a],y+35)])
                d.node(label,xs[a]-160,y-70,320,60,'strokeColor=none;fontSize=22;')
            else:
                path(d,[(xs[a],y),(xs[b],y)],dashed=ret)
                middle=(xs[a]+xs[b])/2
                d.node(label,middle-170,y-70,340,64,'strokeColor=none;fontSize=22;')

    d=fresh('22-warning-state')
    d.node('Healthy stock\nq_sellable > threshold',360,20,380,110,'rounded=1;')
    d.node('LOW / OPEN\n0 < q_sellable ≤ threshold',20,300,360,120,'rounded=1;')
    d.node('OUT / OPEN\nq_sellable = 0',720,300,360,120,'rounded=1;')
    d.node('RESTOCKED / OPEN\n24-hour visibility',360,720,380,110,'rounded=1;')
    path(d,[(450,130),(450,205),(200,205),(200,300)],'threshold crossed',(20,150),290)
    path(d,[(650,130),(650,205),(900,205),(900,300)],'quantity becomes zero',(735,150),310)
    path(d,[(380,330),(720,330)],'q becomes zero',(425,275),270)
    path(d,[(720,395),(610,395),(610,500),(450,500),(450,395),(380,395)],
         '0 < q_sellable ≤ threshold',(395,510),310)
    path(d,[(200,420),(200,640),(420,640),(420,720)],'healthy replenishment',(15,580),320)
    path(d,[(900,420),(900,640),(680,640),(680,720)],'healthy replenishment',(750,580),320)
    path(d,[(740,775),(1160,775),(1160,75),(740,75)],'expiry resolves recovery',(1020,450),280)

    d=fresh('25-warning-rules')
    cols=[200,580,960]
    d.node('Product, batch and movement records',390,20,380,80,'fontStyle=1;fillColor=#f3f3f3;')
    inputs=['Sellable quantity\nexcluding expired and\nquarantined batches','Batch expiry dates\nevaluated in the\nbusiness timezone','SALE movements\nin the configured\nslow-moving window']
    rules=['Quantity rule\nOUT / LOW / RESTOCKED','Expiry rule\nEXPIRING / EXPIRED','Slow-moving rule\nSLOW']
    path(d,[(580,100),(580,150)],arrow=False)
    path(d,[(cols[0],150),(cols[-1],150)],arrow=False)
    for x,inp,rule in zip(cols,inputs,rules):
        path(d,[(x,150),(x,200)])
        d.node(inp,x-170,200,340,120,'')
        path(d,[(x,320),(x,390)])
        d.node(rule,x-170,390,340,100,'rounded=1;')
        path(d,[(x,490),(x,540)],arrow=False)
    path(d,[(cols[0],540),(cols[-1],540)],arrow=False)
    path(d,[(580,540),(580,590)])
    d.node('Persisted warning episodes\ntype, state and reviewer',390,590,380,100,'fontStyle=1;fillColor=#f3f3f3;')

    # Figure 1.4: a state diagram; cancellable states share one composite frame.
    d=fresh('26-purchasing-workflow')
    d.node('Replenishment\nsuggestion',340,20,220,90,'')
    d.node('Open purchase document (cancellable)',300,170,940,420,
           'rounded=1;dashed=1;fillColor=none;align=right;verticalAlign=top;spacingRight=24;spacingTop=10;fontStyle=2;')
    for title,x,y in [('DRAFT',340,260),('SUBMITTED',660,260),('APPROVED',980,260),
                      ('REJECTED',660,470),('PARTIAL',980,470),('CANCELLED',660,700),('COMPLETED',980,700)]:
        d.node(title,x,y,220,80,'rounded=1;')
    path(d,[(450,110),(450,260)],'create draft',(465,118),160)
    path(d,[(560,300),(660,300)],'submit',(563,246),94)
    path(d,[(880,300),(980,300)],'approve',(883,246),94)
    path(d,[(740,340),(740,470)],'reject',(640,385),90)
    path(d,[(820,470),(820,340)],'resubmit',(832,385),120)
    path(d,[(660,510),(450,510),(450,340)],'edit',(462,400),70)
    path(d,[(1090,340),(1090,470)],'partial\nreceipt',(975,372),105)
    path(d,[(1090,550),(1090,700)],'final receipt',(1102,620),160)
    path(d,[(1200,300),(1300,300),(1300,740),(1200,740)],'full\nreceipt',(1312,486),90)
    path(d,[(770,590),(770,700)],'cancel',(660,625),95)

    d=fresh('27-batch-fefo')
    d.node('Receipt\nBatch number and dates',30,20,400,100,'')
    d.node('Inventory batches\nPhysical / sellable / quarantine',30,260,400,120,'')
    d.node('Dispatch allocation\nFEFO; FIFO fallback',650,260,400,120,'')
    d.node('Batch allocations\nLink batch to accepted movement',650,600,400,110,'')
    d.node('Count / disposal review\nValidate snapshot or remainder',30,600,400,110,'')
    d.node('Audited stock movement\nQuantity before, delta and after',330,950,440,110,'')
    path(d,[(230,120),(230,260)],'create or replay',(255,165),240)
    path(d,[(430,320),(650,320)],'eligible batches',(445,265),200)
    path(d,[(850,380),(850,600)],'consume eligible stock',(675,460),320)
    path(d,[(230,380),(230,600)],'observation / disposal',(35,460),350)
    path(d,[(230,710),(230,840),(430,840),(430,950)],'approved adjustment / count',(15,780),365)
    path(d,[(850,710),(850,840),(670,840),(670,950)],'allocation attribution',(735,780),330)

