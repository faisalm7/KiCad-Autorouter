from pathlib import Path
import sys,time,json,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,floor_route as f
from autorouter.runner import run
protocol=ROOT/'.runs/selected-net-native-input-001/protocol.json'
assert p.sha(protocol)=='1048fd95d81f02e63e6eef86c4cea56a3b235ad9ddef2621864cb5c6671a38d9'
plan=f.read_json(protocol);case=next(x for x in plan['cases'] if x['id']==sys.argv[1]);board=Path(case['board']);out=Path(case['output'])
assert p.tree_hash(board.parent)==case['source_hashes'] and p.sha(Path(case['settings']))==case['settings_sha256'] and not out.exists()
start=time.monotonic();cpu0=time.process_time()+f.child_cpu();outer=ROOT/'.runs'/('selected-net-native-'+case['id']+'-001-execution');outer.mkdir()
tools=p.tool_manifest()
for name,sha in tools['implementation_sha256'].items():
 raw=(ROOT/name).read_bytes();committed=subprocess.run(['git','show',tools['git_head']+':'+name],cwd=ROOT,capture_output=True,check=True,timeout=3).stdout
 assert raw==committed and p.sha(ROOT/name)==sha
argv=[str(ROOT/'.venv/bin/python'),'-B','-m','autorouter','route',str(board),'--settings',case['settings'],'--output',str(out)]
process=run(argv,cwd=outer,log=outer/'command.log',timeout=135,max_log_bytes=128*1024,max_workdir_bytes=32*1024**2,max_group_rss_bytes=4*1024**3)
record={'schema':1,'case':case['id'],'helper_sha256':p.sha(Path(__file__)),'input_protocol_sha256':p.sha(protocol),'input_protocol_code_pins_are_preparation_only':True,'executed_tools':tools,'argv':argv,'process':process,'original_preserved':p.tree_hash(board.parent)==case['source_hashes'],'settings_preserved':p.sha(Path(case['settings']))==case['settings_sha256'],'quality_comparison':False,'physical_electrical_validation':False,'selected_net_guard_qualified':False}
report=f.read_json(out/'result.json');record['routing_receipt_sha256']=p.sha(out/'result.json');record['routing_status']=report['status'];record['routing_accepted']=report['accepted'];record['routing_reason']=report.get('reason');record['native']=report.get('native');record['metrics']=report.get('metrics')
if case['id']=='positive' and report['accepted'] is True:
 record['readback']=p.check_result(out/'result.json');record['selected_net_guard_qualified']=record['readback']['current'] is True
elif case['id']=='unselected_open' and report['accepted'] is False:
 record['selected_net_guard_qualified']=bool('nonselected' in report.get('reason','') or 'protected' in report.get('reason','') or report.get('native',{}).get('opens',0)>0)
record['wall_seconds']=time.monotonic()-start;record['total_cpu_seconds']=time.process_time()+f.child_cpu()-cpu0;record['complete_outer_budget_seconds']=150
record['within_budget']=record['wall_seconds']<=150 and record['total_cpu_seconds']<=150
record['passed']=record['selected_net_guard_qualified'] and record['within_budget'] and record['original_preserved'] and record['settings_preserved'] and process['cleanup_complete']
p.save_json(outer/'execution.json',record)
print(json.dumps({k:record[k] for k in ('case','passed','routing_status','routing_reason','native','metrics','wall_seconds','total_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
