#!/usr/bin/env python3
"""Exercise the upgraded localhost API. Adds explicitly named demo records; never resets data."""
import datetime as dt
import http.cookiejar
import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import uuid

root = Path(__file__).resolve().parents[1]
base = os.environ.get('SHELFWISE_API', 'http://localhost:8080')
password = os.environ.get('DEMO_PASSWORD')
if not password and (root / '.env').exists():
    for line in (root / '.env').read_text().splitlines():
        if line.startswith('DEMO_PASSWORD='):
            password = line.split('=', 1)[1].strip().strip('"\'')
if not password:
    raise SystemExit('Set DEMO_PASSWORD for the local demonstration environment.')
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf = ''
def call(method, path, payload=None, expected=200):
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if method != 'GET':
        headers['X-XSRF-TOKEN'] = csrf
    req = urllib.request.Request(base + '/api' + path, headers=headers, method=method,
                                 data=None if payload is None else json.dumps(payload).encode())
    try:
        response = client.open(req, timeout=30)
        status, raw = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    assert status == expected, f'{method} {path}: expected {expected}, got {status}: {raw.decode()}'
    return json.loads(raw) if raw else None

def login(role):
    global csrf
    csrf = call('GET', '/auth/csrf')['token']
    call('POST', '/auth/login', {'username': role, 'password': password})

checks = []
suffix = uuid.uuid4().hex[:8]
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).date()
login('admin')
vendor = call('POST', '/suppliers', {'name': 'Upgrade demo supplier ' + suffix}, 201)
product = call('POST', '/products', {'sku': 'UPGRADE-' + suffix, 'name': 'Upgrade demo yogurt ' + suffix,
    'unit': 'tub', 'price': 2.5, 'safetyStock': 2, 'reorderThreshold': 5, 'supplierId': vendor['id']}, 201)
pid = product['id']
def receipt(number, quantity, date):
    return call('POST', '/transactions', {'productId': pid, 'type': 'STOCK_IN', 'quantity': quantity,
        'reason': 'Upgrade demonstration receipt', 'idempotencyKey': str(uuid.uuid4()),
        'batchNumber': number + '-' + suffix, 'expiryDate': date.isoformat()}, 201)
receipt('expired', 5, today - dt.timedelta(days=1))
receipt('near', 3, today + dt.timedelta(days=2))
p = call('GET', f'/products/{pid}')
assert p['quantity'] == 8 and p['sellableQuantity'] == 3
events = [w for w in call('GET', '/warnings?state=open&size=100&cache=false')['items'] if w['productId'] == pid]
assert {w['type'] for w in events} == {'LOW', 'EXPIRING', 'EXPIRED'}
checks.append('physical vs sellable balances and three simultaneous rule types')
w = next(w for w in events if w['type'] == 'LOW')
call('POST', f"/warnings/{w['id']}/ack", {})
assignee = next(u for u in call('GET', '/warnings/assignees') if u['username'] == 'manager')
call('POST', f"/warnings/{w['id']}/actions", {'action': 'ASSIGN', 'assigneeId': assignee['id'], 'note': 'Check supplier delivery'})
call('POST', f"/warnings/{w['id']}/actions", {'action': 'PROCESS', 'note': 'Replenishment requested'})
checks.append('confirmation, assignment and processing history')
order = call('POST', '/purchases', {'supplierId': vendor['id'], 'reason': 'Demo replenishment',
    'warningId': w['id'], 'lines': [{'productId': pid, 'quantity': 7}]})
oid = order['id']
call('POST', f'/purchases/{oid}/actions', {'action': 'SUBMIT', 'note': 'Request stock'})
login('clerk')
call('POST', f'/purchases/{oid}/actions', {'action': 'APPROVE', 'note': 'Cannot approve'}, 403)
login('manager')
call('POST', f'/purchases/{oid}/actions', {'action': 'APPROVE', 'note': 'Checked sellable plus pending stock'})
assert not any(s['productId'] == pid for s in call('GET', '/replenishment'))
login('clerk')
body = {'lineId': order['lines'][0]['id'], 'quantity': 2, 'batchNumber': 'purchase-' + suffix,
        'expiryDate': (today + dt.timedelta(days=14)).isoformat(), 'idempotencyKey': str(uuid.uuid4())}
a = call('POST', f'/purchases/{oid}/receipts', body)
b = call('POST', f'/purchases/{oid}/receipts', body)
assert a['id'] == b['id'] and a['quantity'] == 2
assert call('GET', f'/purchases/{oid}')['state'] == 'PARTIAL'
checks.append('approval permission, stock position and receipt replay')
login('manager')
call('POST', f'/purchases/{oid}/actions', {'action': 'CANCEL', 'note': 'Cancel unreceived demo remainder'})
assert call('GET', f'/purchases/{oid}')['lines'][0]['remaining'] == 0
assert next(s for s in call('GET', '/replenishment') if s['productId'] == pid)['suggested'] == 5
checks.append('partial cancellation preserves received stock')
login('clerk')
expired = next(b for b in call('GET', f'/batches?productId={pid}')['items'] if b['status'] == 'EXPIRED')
body = {'kind': 'DISPOSAL', 'productId': pid, 'batchId': expired['id'], 'quantity': 5,
        'reason': 'Expired demo batch', 'requestKey': str(uuid.uuid4())}
r = call('POST', '/stock-reviews', body)
assert call('POST', '/stock-reviews', body)['id'] == r['id']
login('manager')
call('POST', f"/stock-reviews/{r['id']}/actions", {'action': 'APPROVE', 'note': 'Expiry verified'})
assert call('GET', f'/products/{pid}')['quantity'] == 5
assert not any(w['productId'] == pid for w in call('GET', '/warnings?type=EXPIRED&state=open&size=100')['items'])
checks.append('review request replay, approved disposal and warning recovery')
login('admin')
receipt('healthy', 6, today + dt.timedelta(days=20))
assert not any(w['productId'] == pid for w in call('GET', '/warnings?type=LOW&state=open&size=100')['items'])
assert 'RECOVER' in [a['action'] for a in call('GET', f"/warnings/{w['id']}/history")]
assert sum(b['quantity'] for b in call('GET', f'/batches?productId={pid}&size=100')['items']) == call('GET', f'/products/{pid}')['quantity']
checks.append('shortage recovery and batch balance reconciliation')
for kind in ('LOW', 'OUT', 'EXPIRING', 'EXPIRED', 'SLOW'):
    cached = call('GET', '/warnings?type=' + kind + '&size=100')
    uncached = call('GET', '/warnings?type=' + kind + '&size=100&cache=false')
    assert cached == uncached
checks.append('cached and direct warning pages agree')
evidence = {'checkedAt': dt.datetime.now(dt.timezone.utc).isoformat(), 'checks': checks,
            'demoProductId': pid, 'purchaseId': oid, 'reviewId': r['id']}
(root / 'docs/evidence/warning-upgrade-smoke.json').write_text(json.dumps(evidence, indent=2) + '\n')
print(json.dumps(evidence, indent=2))
