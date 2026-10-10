"""Offline exact evidence audit; imports launch no native/engine process."""
from pathlib import Path
from types import SimpleNamespace
from collections import Counter
import sys,json,hashlib,subprocess,math
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'toolchain.lock.json').is_file())
sys.path[:0]=[str(ROOT),str(ROOT/'experiments/placement_clearance_controls_v1')]
import driver as d
from autorouter import board_floor as g
p=d.p;sx=d.sx;f=d.f;r=d.r;s=d.s
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-clearance-controls-001';read=lambda x:json.loads(x.read_text());checks=[]
def ok(name,v):
 if not v:raise AssertionError(name)
 checks.append(name)
def main():
 before=p.tree_hash(RUN);record=read(RUN/'summary.json');freeze=record['freeze']
 ok('exact completed failed diagnostic summary',p.sha(RUN/'summary.json')=='81867c5e79adad1d084ce29648fa34f0de0fd3269a442aee1da513dbbe82f1dc' and record['status']=='completed' and record['controls_passed'] is False and all(record[x] is False for x in ('routing_accepted','comparison_eligible','production_qualified','engine_executed','geometry_margin_policy_qualified')))
 prior,candidate,source_hashes,candidate_hashes,prior_trees=d.baseline();base_raw=candidate.read_bytes()
 ok('prior exact recorded trees and source identity',source_hashes==record['source_hashes']==freeze['source_hashes'] and prior_trees==freeze['prior_recorded_trees'] and p.tree_hash(d.PAIR)==freeze['prior_pair_tree'])
 for path,tree in prior_trees.items():ok('prior retained tree '+path,p.tree_hash(Path(path))==tree)
 current=p.tool_manifest();ok('same installed tools/current core bytes', {k:v for k,v in current.items()if k!='git_head'}=={k:v for k,v in freeze['tools'].items()if k!='git_head'})
 for relative,digest in freeze['committed_source_bytes'].items():
  blob=subprocess.run(['git','show',freeze['tools']['git_head']+':'+relative],cwd=ROOT,check=True,capture_output=True,timeout=5).stdout
  ok('exact pinned commit bytes '+relative,p.sha(ROOT/relative)==digest==hashlib.sha256(blob).hexdigest())
 ok('retained whole code snapshot',p.tree_hash(RUN/'code')==freeze['code'])
 results=[]
 for i,entry in enumerate(record['cases']):
  case=entry['case'];directory=RUN/case;board=Path(entry['candidate']);raw=p.parse_report(directory/'native-drc.json',board.name)
  ok(case+': exact predeclared order and case record',case==r.CASES[i] and read(directory/'case.json')==entry)
  ok(case+': exact unchanged or two-segment derived bytes',board.read_bytes()==r.prepare(base_raw,case) and p.sha(board)==entry['candidate_sha256'] and p.immutable(sx.read(board))==p.immutable(sx.read(candidate)))
  ok(case+': unchanged original project except exact board',p.tree_hash(board.parent)==entry['project_hashes']=={**candidate_hashes,board.name:entry['candidate_sha256']})
  ok(case+': raw report/native/process binding',raw==entry['native'] and s.check_drc(SimpleNamespace(out=directory,steps=entry['steps']),'native-drc',board,raw)==entry['native_binding'])
  ok(case+': exact retained output tree',p.tree_hash(directory)==record['completed_evidence'][str(directory)])
  ok(case+': honest rejection and fixed predicate',r.verdict(case,raw,prior['native'])==entry['passed']==(i==0) and not p.native_accepted(raw) and entry['native_accepted'] is False and entry['routing_accepted'] is False)
  ok(case+': actual process fully completed',len(entry['steps'])==1 and entry['steps'][0]['exit_code']==5 and entry['steps'][0]['cleanup_complete'] is True and entry['steps'][0]['status']=='success')
  errors=[x for x in raw['findings']if x['severity']=='error' and x['type']!='unconnected_items']
  if i==1:
   ok('translated original RV13 errors gone but four nearby-track errors remain',raw['opens']==8 and raw['blocking']==4 and raw['warnings']==94 and raw['exclusions']==0 and len(errors)==4 and all(x['type']=='clearance' and r.PAD not in {z['uuid']for z in x['items']} and {z['uuid']for z in x['items']}&set(r.TARGETS) and any('[GND]'in z['description']for z in x['items'])for x in errors))
  results.append({'case':case,'passed':entry['passed'],'candidate_sha256':entry['candidate_sha256'],'native_report_sha256':p.sha(directory/'native-drc.json'),'native':{k:raw[k]for k in ('opens','blocking','warnings','exclusions')},'blocking_findings':errors,'binding':entry['native_binding']})
 ok('full native stage list contains both and only both processes',record['steps']==[x for c in record['cases']for x in c['steps']])
 ok('wall/CPU and process accounting within60caps',record['budget_seconds']==record['cpu_budget_seconds']==60 and record['within_budget'] and 0<record['wall_seconds']<60 and 0<record['total_cpu_seconds']<60 and record['total_cpu_seconds']>=record['process_cpu_seconds']+record['monitor_cpu_seconds'] and abs(record['process_cpu_seconds']-sum(x['cpu_seconds']for x in record['steps']))<1e-9)
 ok('all four payload copies under aggregate20MiB',d.project_payload(RUN)==record['actual_project_copy_payload_bytes']==18130406 and record['project_copy_payload_limit_bytes']==20*1024**2 and record['actual_project_copy_payload_bytes']<=record['project_copy_payload_limit_bytes'])
 public=[]
 for name in ('placement-search-fixture-001','placement-search-three-arm-001','placement-clearance-controls-001'):
  dst=ROOT/'evidence'/name;src=ROOT/'.runs'/name;index=read(dst/'files.json');actual={str(x.relative_to(dst))for x in dst.rglob('*')if x.is_file()}
  ok(name+': selected exact file population',actual==set(index)|{'files.json','SCOPE.md'})
  total=0
  for relative,meta in index.items():
   target=dst/relative;origin=src/relative
   ok(name+': public/raw exact '+relative,target.stat().st_size==origin.stat().st_size==meta['bytes'] and p.sha(target)==p.sha(origin)==meta['sha256']);total+=meta['bytes']
  public.append({'name':name,'files':len(index),'bytes':total,'files_manifest_sha256':p.sha(dst/'files.json'),'scope_sha256':p.sha(dst/'SCOPE.md'),'scope':(dst/'SCOPE.md').read_text()})
 ok('raw controls and prior pair/source unchanged through review',p.tree_hash(RUN)==before and p.tree_hash(d.PAIR)==freeze['prior_pair_tree'] and p.tree_hash(d.SOURCE.parent)==source_hashes)
 result={'audit_passed':True,'kind':'AI offline actual-evidence audit','native_or_engine_executed':False,'check_count':len(checks),'checks':checks,'summary_sha256':p.sha(RUN/'summary.json'),'frozen_head':freeze['tools']['git_head'],'cases':results,'wall_seconds':record['wall_seconds'],'total_cpu_seconds':record['total_cpu_seconds'],'accounting_point':record['accounting_point'],'public_subsets':public,'raw_run_inventory':before}
 with (HERE/'audit.json').open('x')as stream:json.dump(result,stream,indent=2);stream.write('\n')
 print(json.dumps({k:v for k,v in result.items()if k not in ('checks','raw_run_inventory','cases','public_subsets')},indent=2));print('public',[(x['name'],x['files'],x['bytes'])for x in public])
if __name__=='__main__':main()
