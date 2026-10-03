#!/usr/bin/env python3
"""Measure authenticated warning-query latency with identical cached/bypass responses."""
import argparse, http.cookiejar, json, os, platform, statistics, time, urllib.request
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--iterations',type=int,default=200);parser.add_argument('--rounds',type=int,default=3);parser.add_argument('--output',default='docs/evidence/cache-benchmark.json');args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
password=os.environ.get('DEMO_PASSWORD')
if not password:
 for line in (root/'.env').read_text().splitlines():
  if line.startswith('DEMO_PASSWORD='):password=line.split('=',1)[1].strip('"\'')
if not password:raise SystemExit('Set DEMO_PASSWORD.')
base=os.environ.get('SHELFWISE_API','http://localhost:8080');jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def request(method,path,body=None,csrf=None):
 headers={'Content-Type':'application/json'}
 if csrf:headers['X-XSRF-TOKEN']=csrf
 req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
 with opener.open(req,timeout=10) as r:return json.loads(r.read())
csrf=request('GET','/api/auth/csrf')['token'];request('POST','/api/auth/login',{'username':'admin','password':password},csrf)
productCount=request('GET','/api/products?size=1')['totalElements'];warningCount=request('GET','/api/warnings?size=100&cache=false')['totalElements']
records=[];responses={}
for round_index in range(args.rounds):
 for mode in (['cached','bypass'] if round_index%2==0 else ['bypass','cached']):
  path='/api/warnings?state=open&size=100&cache='+('true' if mode=='cached' else 'false')
  for _ in range(20):request('GET',path)
  samples=[]
  for _ in range(args.iterations):
   start=time.perf_counter_ns();response=request('GET',path);samples.append((time.perf_counter_ns()-start)/1e6)
  responses[mode]=response
  ordered=sorted(samples)
  percentile=lambda p:ordered[min(len(ordered)-1,int((len(ordered)-1)*p))]
  records.append({'round':round_index+1,'mode':mode,'samples_ms':samples,'median_ms':statistics.median(samples),'p95_ms':percentile(.95),'p99_ms':percentile(.99),'mean_ms':statistics.mean(samples)})
# Datetimes may be strings or epoch seconds depending on Jackson; compare stable item ids and values.
assert responses['cached']==responses['bypass'], 'Cache and DB disagree'
out={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'environment':{'os':platform.platform(),'machine':platform.machine(),'python':platform.python_version(),'backend':'Spring Boot 3.5.16 / Java 21.0.12.1+1','mysql':'8.4.8','redis':'7.4.9','network':'loopback HTTP, Colima containers'},'workload':{'products':productCount,'open_warning_episodes':warningCount,'page_size':100,'concurrency':1,'iterations_per_mode_per_round':args.iterations,'rounds':args.rounds,'warmup_per_mode':20,'mode_order':'alternates each round'},'records':records,'response_equivalence':True}
p=root/args.output;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,indent=2))
for row in records:print(row['round'],row['mode'],'median',round(row['median_ms'],3),'p95',round(row['p95_ms'],3))
print(p)
