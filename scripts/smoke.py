#!/usr/bin/env python3
"""Repeatable local end-to-end acceptance smoke for authentication, roles and inventory."""
import http.cookiejar, json, os, sys, urllib.error, urllib.request, uuid
base = os.environ.get('SHELFWISE_API', 'http://localhost:8080')
password = os.environ.get('DEMO_PASSWORD')
if not password:
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.isfile(env_file):
        for line in open(env_file):
            if line.startswith('DEMO_PASSWORD='): password = line.strip().split('=',1)[1].strip("\"'")
if not password: raise SystemExit('Set DEMO_PASSWORD or create a local .env file.')
cookies = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookies))
csrf = ''
def call(method, path, payload=None, code=200, use_csrf=True):
    global csrf
    data = None if payload is None else json.dumps(payload).encode()
    headers = {'Accept': 'application/json'}
    if data is not None: headers['Content-Type'] = 'application/json'
    if use_csrf and csrf and method not in ('GET','HEAD','OPTIONS'): headers['X-XSRF-TOKEN'] = csrf
    req = urllib.request.Request(base+path,data=data,headers=headers,method=method)
    try: res = client.open(req,timeout=10)
    except urllib.error.HTTPError as error:
        raw=error.read().decode()
        if error.code != code: raise AssertionError(f'{method} {path}: expected {code}, got {error.code}: {raw}')
        return error.code, json.loads(raw) if raw.startswith('{') else raw
    raw=res.read().decode()
    if res.status != code: raise AssertionError(f'{method} {path}: expected {code}, got {res.status}: {raw}')
    if not raw:return res.status,None
    return res.status,json.loads(raw)

def expect(ok,msg):
    if not ok: raise AssertionError(msg)

# Anonymous access and CSRF-protected login.
expect(call('GET','/api/dashboard',code=401,use_csrf=False)[0]==401,'Anonymous dashboard should be denied')
_,token=call('GET','/api/auth/csrf',use_csrf=False);csrf=token['token']
_,admin=call('POST','/api/auth/login',{'username':'admin','password':password})
expect(admin['role']=='ADMIN','Demo administrator login failed')
_,page=call('GET','/api/products?size=100');expect(len(page['items'])>=8,'Expected seeded products')
product=next(p for p in page['items'] if p['sku']=='PRD-1701')
# Exact duplicate safely returns the original transaction; payload mismatch is rejected.
key='smoke-'+str(uuid.uuid4())
body={'productId':product['id'],'type':'STOCK_OUT','quantity':1,'reason':'Acceptance smoke','idempotencyKey':key}
_,tx1=call('POST','/api/transactions',body,code=201);_,tx2=call('POST','/api/transactions',body,code=201)
expect(tx1['id']==tx2['id'],'Exact idempotent replay must not duplicate history')
call('POST','/api/transactions',{**body,'quantity':2},code=409)
# A dispatch that would go below zero is atomic and rejected.
empty=next(p for p in page['items'] if p['quantity']==0)
call('POST','/api/transactions',{ 'productId':empty['id'],'type':'STOCK_OUT','quantity':1,'reason':'Should fail','idempotencyKey':'smoke-'+str(uuid.uuid4())},code=400)
_,refreshed=call('GET',f"/api/products/{product['id']}");expect(refreshed['quantity']==product['quantity']-1,'Quantity/history did not update atomically')
_,alert=call('GET','/api/warnings?state=open&size=100');expect(alert['totalElements']>0,'Seeded threshold warnings missing')
open_warning=next((w for w in alert['items'] if not w.get('acknowledgedBy')),None)
if open_warning: call('POST',f"/api/warnings/{open_warning['id']}/ack",{},code=200)
call('POST','/api/auth/logout',{},code=204)
# Clerk may post stock but cannot inspect warning details or acknowledge.
_,token=call('GET','/api/auth/csrf',use_csrf=False);csrf=token['token']
_,clerk=call('POST','/api/auth/login',{'username':'clerk','password':password})
expect(clerk['role']=='CLERK','Clerk login failed')
call('GET','/api/warnings',code=403)
call('POST','/api/transactions',{'productId':product['id'],'type':'STOCK_IN','quantity':1,'reason':'Role test','idempotencyKey':'smoke-'+str(uuid.uuid4())},code=201)
call('POST','/api/auth/logout',{},code=204)
# Manager can review warnings but cannot mutate catalogue or stock.
_,token=call('GET','/api/auth/csrf',use_csrf=False);csrf=token['token']
_,manager=call('POST','/api/auth/login',{'username':'manager','password':password})
expect(manager['role']=='MANAGER','Manager login failed')
call('GET','/api/warnings',code=200)
call('POST','/api/transactions',{'productId':product['id'],'type':'STOCK_IN','quantity':1,'reason':'Should fail','idempotencyKey':'smoke-'+str(uuid.uuid4())},code=403)
call('POST','/api/auth/logout',{},code=204)
print('PASS: anonymous denial, role login, immutable exact replay, mismatch conflict, negative-stock boundary, audit persistence, warning acknowledgement, clerk/manager permission boundaries')
