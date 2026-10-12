"""Bounded offline readback of one completed low-via run; no process execution."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, sexpr as sx, floor_route as f
from autorouter.placement_clearance import inventory,read_bytes
from experiments.pic_mixed_transport_probe_v1 import driver, routing_input, routing_adapter, routing_checks, ses_checks, ses_native
RUN=ROOT/'.runs/pic-low-via-routing-001';OUT=Path(__file__).parent;WORK=RUN/'routing-native'
raw=lambda x:read_bytes(x,16*1024*1024)
load=lambda x:json.loads(raw(x))
sha=lambda x:hashlib.sha256(raw(x)).hexdigest()
inv=lambda x:inventory(x,max_bytes=64*1024*1024,max_files=2000,max_entries=4000)
before=inv(RUN);summary=load(RUN/'summary.json');native=summary['native_routing'];runtime=summary['runtime']
assert runtime==load(RUN/'runtime.json')
protocol=load(RUN/'code/experiments/pic_mixed_transport_probe_v1/ADAPTER_LOW_VIA_PROTOCOL.json')
current_runtime=driver.runtime(protocol)
extra_sources={k:v for k,v in current_runtime['sources'].items() if k not in runtime['sources']}
assert set(extra_sources)=={'autorouter/review_view.py'}
for name in extra_sources:current_runtime['sources'].pop(name)
assert current_runtime==runtime
for name,pin in runtime['sources'].items():
 assert driver.base.content(RUN/'code'/name,pin['bytes'],digest=True)==pin
source=RUN/'observe-input/pic_programmer.kicad_pcb';candidate=WORK/'candidate'/source.name
original_before=inv(ROOT/'.data/boards/kicad-pic-programmer')
assert original_before==runtime['original']==inv(source.parent) and len(original_before)==15
assert all(before[n]==v for n,v in summary['frozen_evidence'].items())
assert summary['status']=='observed-incomplete' and summary['routing_accepted'] is False and summary['observations_complete'] is False
assert all(summary[k] is True for k in ('native_process_executed','routing_executed','ses_executed','import_process_executed'))
assert all(summary[k] is False for k in ('custom_pad_support_qualified','mixed_clearance_equivalence_qualified'))
assert native['diagnostic_only'] is True and native['completed'] is False and native['routing_accepted'] is False
obs=load(RUN/'observations.json');expected=load(RUN/'routing-expectations.json');basis=load(RUN/'selective-basis-observations.json');context=load(RUN/'cached-native/context.json');adapter=load(RUN/'routing-adapter.json')
assert obs['cancel_before_routing'] is False
assert routing_input.verify(raw(RUN/'mixed.dsn'),load(RUN/'expectations.json'),raw(source),context,raw(RUN/'stripped-unrouted.dsn'),load(RUN/'removal-ledger.json'))
assert routing_adapter.verify(raw(RUN/'stripped-unrouted.dsn'),raw(RUN/'unrouted.dsn'),context,adapter)
assert routing_checks.compare(obs,expected,basis,adapter_receipt=adapter,scoring_variant='via_low')==summary['strict_routing_comparison']
assert routing_checks.compare(obs,expected,basis,adapter_receipt=adapter,scoring_variant='via_low',native_diagnostic=True)==summary['routing_comparison']
_,transport=ses_checks.audit(raw(RUN/'raw.ses'),raw(RUN/'unrouted.dsn'),expected,sx.read(RUN/'task-project'/source.name),obs['final_geometry'],generated=True)
for k,v in transport.items():
 if k!='scope':assert summary['generated_transport'][k]==v,k
assert transport['generated_engine_to_ses_exact'] and transport['engine_to_ses']=={'actual_segments':335,'expected_segments':335,'equal':True,'extra':[],'missing':[]}
assert obs['writer']['ses']['sha256']==sha(RUN/'raw.ses') and obs['writer']['ses']['bytes']==len(raw(RUN/'raw.ses'))
assert all(obs['writer']['ses'][k] is True for k in ('executed','returned','closed','write_completed'))
assert obs['writer']['route_geometry_after_ses']==obs['final_geometry'] and obs['writer']['state_after_ses']==obs['final_state']
scoring={k:json.loads(obs[k]['configuration_json'])['scoring'] for k in ('settings_loaded','settings_enabled','settings_final')}
assert all(v['via_costs']==25 and v['plane_via_costs']==3 for v in scoring.values())
assert sha(candidate)==native['candidate_sha256']
p.verify_candidate_files(candidate,original_before,native['candidate_sha256'])
assert p.immutable(sx.read(candidate))==p.immutable(sx.read(source))
assert ses_native.semantic_diff(sx.read(source),sx.read(WORK/'raw-routed.kicad_pcb'))==native['raw_immutable']=={'equal':True,'different_top_level_keys':[]}
engine=Counter()
for row in obs['final_geometry']['traces']:
 engine.update(ses_checks.segments(row['nets'][0],row['layer'],row['width_um'],[tuple(ses_checks.number(v) for v in point) for point in row['corners_um']]))
for board in (WORK/'raw-routed.kicad_pcb',candidate):
 native_paths,native_vias=ses_checks.source_routes(sx.read(board));assert native_paths==engine and not native_vias
assert sum(engine.values())==335 and len(obs['final_geometry']['traces'])==176
reports={}
for name in ('generated-raw-drc','refill-drc','final-drc'):
 binding=load(WORK/(name+'-binding.json'));actual=p.parse_report(WORK/(name+'.json'),source.name)
 assert inv(Path(binding['input']).parent)==binding['after']
 p.check_drc_project(binding['before'],binding['after'],source.name,saved=binding['saved'])
 assert all(binding['before'][k]==v for k,v in original_before.items() if k!=source.name)
 assert all(binding['after'][k]==v for k,v in original_before.items() if k!=source.name)
 if name=='final-drc':
  assert binding['source']==str(candidate) and binding['saved'] is False
  assert binding['before']==inv(candidate.parent) and binding['before'][source.name]==native['candidate_sha256']
  assert actual==native['final_native']
 if name=='generated-raw-drc':assert actual==native['raw_native']
 reports[name]={'counts':{k:actual[k] for k in ('opens','blocking','warnings','exclusions')},'finding_types':dict(Counter(v['type'] for v in actual['findings'])),'ignored_checks':actual['ignored_checks'],'report_sha256':sha(WORK/(name+'.json')),'binding_sha256':sha(WORK/(name+'-binding.json'))}
final=p.parse_report(WORK/'final-drc.json',source.name)
assert [final[k] for k in ('opens','blocking','warnings','exclusions')]==[5,0,41,0] and not p.native_accepted(final)
assert reports['final-drc']['report_sha256']==native['final_bound_report_sha256'] and reports['final-drc']['binding_sha256']==native['final_binding_sha256']
map_path=WORK/'final-netclasses.json';actual_audit=p.audit_candidate_netclasses(candidate,(),load(map_path));actual_audit['native_map_file_sha256']=sha(map_path)
assert actual_audit==load(WORK/'final-netclass-audit.json')
assert load(WORK/'metrics.json')==native['metrics']
steps=[]
for step in summary['steps']:
 name=step['name'];process=load(RUN/(name+'-process.json'))
 assert process=={k:v for k,v in step.items() if k!='name'}
 assert process['cleanup_complete'] is True and process['log_truncated'] is False
 assert process['argv'][:3]==f.SANDBOX and process['cwd']==str(WORK if name.startswith('ses-') else RUN)
 assert process['exit_code']==(5 if name.endswith('drc') else 0)
 assert process['status']==('nonzero_exit' if name.endswith('drc') else 'success')
 assert len(raw(Path(process['log'])))==process['log_bytes']
 if name.startswith('ses-'):
  inner=next(x for x in native['steps'] if x['name']==name.removeprefix('ses-'));assert all(inner[k]==v for k,v in process.items())
 if name.endswith('drc'):
  label=name.removeprefix('ses-');binding=load(WORK/(label+'-binding.json'))
  argv=[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(WORK/(label+'.json'))]
  if binding['saved']:argv.append('--save-board')
  argv.append(binding['input']);assert process['argv']==argv
 steps.append({k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','cleanup_complete')})
assert [x['name'] for x in steps]==['compile','import','ses-generated-import','ses-generated-raw-drc','ses-refill-drc','ses-final-netclasses','ses-final-drc','ses-generated-metrics']
assert load(RUN/'import-process.json')['argv'][-4:]==['SelectiveRoutingProbe',str(RUN/'unrouted.dsn'),str(RUN/'observations.json'),'adapter-low-via']
outer=load(ROOT/'.runs/pic-low-via-routing-001-execution.json')
assert outer['log_sha256']==sha(ROOT/'.runs/pic-low-via-routing-001-command.log') and outer['wrapper_sha256']==sha(ROOT/'.runs/run-pic-low-via-routing-001.py')
assert outer['git_head']==runtime['git']['head'] and outer['exit_code']==1 and outer['cleanup_signals']==[]
assert summary['wall_budget_seconds']==summary['cpu_budget_seconds']==180 and 0<summary['wall_seconds']<outer['wall_seconds']<180 and 0<summary['total_cpu_seconds']<outer['waited_child_cpu_seconds']<180
assert sum(x['cpu_seconds'] for x in steps)<=summary['total_cpu_seconds']
prior_run=ROOT/'.runs/pic-corrected-adapter-native-001';prior_before=inv(prior_run);prior=load(prior_run/'summary.json')
assert all(prior_before[k]==v for k,v in prior['frozen_evidence'].items())
for name in ('mixed.dsn','stripped-unrouted.dsn','unrouted.dsn','removal-ledger.json','routing-adapter.json','routing-expectations.json'):
 assert raw(RUN/name)==raw(prior_run/name),name
old=p.parse_report(prior_run/'routing-native/final-drc.json',source.name);assert old==prior['native_routing']['final_native']
assert [old[k] for k in ('opens','blocking','warnings','exclusions')]==[5,0,41,0]
assert prior['native_routing']['metrics']['vias']==native['metrics']['vias']==0
assert before==inv(RUN) and original_before==inv(ROOT/'.data/boards/kicad-pic-programmer') and prior_before==inv(prior_run)
result={'scope':'Independent stored evidence and shared pure-helper readback only; no native/JVM/compiler/solver/network/Git command','status':summary['status'],'routing_accepted':False,'native_scope_passed':False,'git_head':runtime['git']['head'],'captured_runtime_sources_tools_basis_current_exact':True,'current_source_additions_not_part_of_run':extra_sources,'full_run_files_unchanged':len(before),'frozen_files':len(summary['frozen_evidence']),'original_files_unchanged':len(original_before),'candidate_sha256':native['candidate_sha256'],'candidate_original_rules_and_immutable_geometry_equal':True,'raw_import_immutable_equal':True,'reports':reports,'native_class_generated_dimensions':actual_audit['route_dimensions'],'metrics':native['metrics'],'steps':steps,'engine_SES_raw_final_exact_segments':335,'engine_traces':176,'effective_scoring':scoring,'actual_argv':obs['case']['argv'],'strict_routing_comparison':summary['strict_routing_comparison'],'native_open_items':[x for x in final['findings'] if x['type']=='unconnected_items'],'comparison':{'default_native_counts':{k:old[k] for k in ('opens','blocking','warnings','exclusions')},'default_metrics':prior['native_routing']['metrics'],'same_derived_task_bytes':True,'completion_gain':False,'quality_comparison_admissible':False,'cost_scope':'New invocation includes fresh compile/router/SES and six native stages; prior default native001 was a continuation of a separately charged failed routing001. Costs are not interchangeable or a paired speed claim.','default_native_cost':{k:prior[k] for k in ('wall_seconds','total_cpu_seconds')},'default_routing_reuse':prior['routing_reuse']},'cost':{k:summary[k] for k in ('wall_seconds','total_cpu_seconds','accounting_point','cpu_enforcement')},'outer_execution':outer,'unsupported':native['original_preflight_reasons'],'bindings':{n:before[n] for n in ('summary.json','runtime.json','observations.json','raw.ses','routing-native/final-drc.json','routing-native/final-drc-binding.json','routing-native/final-netclass-audit.json')}}
(OUT/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(OUT/'run-inventory.json').write_text(json.dumps(before,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','git_head','full_run_files_unchanged','frozen_files','candidate_sha256','metrics','cost')},indent=2))
