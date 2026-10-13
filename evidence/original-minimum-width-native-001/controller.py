from pathlib import Path
import datetime,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
from autorouter.runner import run
from scripts import experiment_quality as q
started=time.monotonic();cpu0=time.process_time()+f.child_cpu();board,family=q.selected_source('ardujoy-c64');frozen=q.freeze(board)
out=ROOT/'.runs/original-minimum-width-native-001';out.mkdir();route=out/'route'
argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B','-m','autorouter','route',str(board),'--seconds','90','--adapter','both','--profile','standard','--output',str(route)]
env=os.environ.copy();env['PYTHONPATH']=str(ROOT)
p.save_json(out/'protocol.json',{'source':str(board),'source_hashes':frozen['source_hashes'],'tools':frozen['tools'],'hypothesis':'original positive minimum disables engine width reduction while all original rules/pads/geometry/schematic conflicts remain','new_routing_quality_claim':False,'routing_budget':90,'outer_budget':120,'controller_sha256':p.sha(Path(__file__))})
process=run(argv,cwd=out,env=env,log=out/'command.log',timeout=100,max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=2*1024**3);p.save_json(out/'launch-process.json',process)
record={'schema':1,'kind':'changed-original-width-guard-native-control','accepted':False,'control_passed':False,'process':process,'new_quality_comparison':False,'source_schematic_mapping_repaired':False}
try:
 report=f.read_json(route/'result.json');q.verify_freeze(frozen,board)
 findings=report.get('native',{}).get('findings',[]);width=[x for x in findings if x['type']=='track_width'];conflict=[x for x in findings if x['type']=='net_conflict']
 record.update(result_sha256=p.sha(route/'result.json'),native=report.get('native'),metrics=report.get('metrics'),width_errors=len(width),schematic_net_conflicts=len(conflict),original_width_guard=report.get('minimum_width_guard'),source_preserved=True)
 assert report['accepted'] is False and report['minimum_width_guard']==p.minimum_width_guard(board,'both') and report['engine_budget']['strict_class_targets'] is True
 assert len(width)==0 and len(conflict)==4 and report['native']['opens']==0
 actual=f.read_json(route/'engine-process.json');assert '--router.automatic_neckdown=false' in actual['argv'] and '--router.neck_width_um=0' in actual['argv'] and '--schematic-parity' in f.read_json(route/'final-drc-process.json')['argv']
 assert actual['cleanup_complete'] and process['cleanup_complete'];record.update(control_passed=True,status='observed-width-policy-and-retained-schematic-rejection',native_report_sha256=p.sha(route/'final-drc.json'),candidate_sha256=report['candidate_sha256'])
except Exception as exc:record.update(status='failed',reason=type(exc).__name__+': '+str(exc))
record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu0);record['within_budget']=max(record['wall_seconds'],record['total_cpu_seconds'])<=120
if not record['within_budget']:record['control_passed']=False
p.save_json(out/'result.json',record);print(json.dumps({k:record.get(k) for k in ('status','control_passed','width_errors','schematic_net_conflicts','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if record['control_passed'] else 2)
