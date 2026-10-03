#!/usr/bin/env python3
"""Local Redis outage/recovery acceptance check, restoring the owned service in finally."""
import http.cookiejar,json,os,time,urllib.request,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];env=dict(l.split('=',1) for l in (root/'.env').read_text().splitlines() if '=' in l and not l.startswith('#'));password=env['DEMO_PASSWORD'].strip('"\'')
jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar));base='http://localhost:8080';token=''
def req(method,path,body=None):
 with client.open(urllib.request.Request(base+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json','X-XSRF-TOKEN':token},method=method),timeout=15) as r:return json.loads(r.read())
token=req('GET','/api/auth/csrf')['token'];req('POST','/api/auth/login',{'username':'admin','password':password})
def normal(r):return [(w['id'],w['quantity'],w.get('acknowledgedBy')) for w in r['items']]
baseline=req('GET','/api/warnings?size=100&cache=false');start=time.perf_counter();cached=req('GET','/api/warnings?size=100');healthy_ms=(time.perf_counter()-start)*1000
try:
 subprocess.run(['docker','compose','stop','redis'],cwd=root,check=True,capture_output=True)
 start=time.perf_counter();during=req('GET','/api/warnings?size=100');failure_ms=(time.perf_counter()-start)*1000
 assert normal(during)==normal(baseline),'Redis outage changed warning results'
finally:
 subprocess.run(['docker','compose','up','-d','--wait','redis'],cwd=root,check=True,capture_output=True)
 start=time.perf_counter();recovered=req('GET','/api/warnings?size=100');recovery_ms=(time.perf_counter()-start)*1000
assert normal(recovered)==normal(baseline),'Recovery changed warning results'
result={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'healthy_ms':healthy_ms,'redis_unavailable_ms':failure_ms,'recovered_ms':recovery_ms,'warning_count':baseline['totalElements'],'same_database_result_during_outage':True,'recovered_service':True,'action':'stop and restart only the shelfwise Redis Compose service; MySQL remains running'}
p=root/'docs/evidence/redis-recovery.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,indent=2));print('PASS Redis unavailable fallback and recovery',result)
