"""Compact stored native-report/invariant readback, reusing production pure helpers."""
from pathlib import Path
import hashlib,json,sys
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx,floor_route as f
from autorouter.placement_clearance import inventory,read_bytes
from experiments.pic_mixed_transport_probe_v1 import ses_native
RUN=ROOT/'.runs/pic-corrected-adapter-native-001';OUT=Path(__file__).parent;WORK=RUN/'routing-native'
load=lambda x:json.loads(read_bytes(x,16*1024*1024))
sha=lambda x:hashlib.sha256(read_bytes(x,16*1024*1024)).hexdigest()
inv=lambda x:inventory(x,max_bytes=64*1024*1024,max_files=2000,max_entries=4000)
before=inv(RUN);summary=load(RUN/'summary.json');native=summary['native_routing'];runtime=summary['runtime']
source=RUN/'observe-input/pic_programmer.kicad_pcb';candidate=WORK/'candidate'/source.name
original_before=inv(ROOT/'.data/boards/kicad-pic-programmer')
assert original_before==runtime['original']==inv(source.parent)
assert all(before[n]==v for n,v in summary['frozen_evidence'].items())
assert summary['status']=='observed-incomplete' and summary['routing_accepted'] is False
assert summary['native_process_executed'] is True and summary['routing_executed'] is False and summary['ses_executed'] is False
assert native['diagnostic_only'] is True and native['completed'] is False and native['routing_accepted'] is False
assert summary['generated_transport']['generated_engine_to_ses_exact'] is True
assert summary['generated_transport']['engine_to_ses']=={'actual_segments':337,'expected_segments':337,'equal':True,'extra':[],'missing':[]}
assert sha(candidate)==native['candidate_sha256']
p.verify_candidate_files(candidate,original_before,native['candidate_sha256'])
assert p.immutable(sx.read(candidate))==p.immutable(sx.read(source))
assert ses_native.semantic_diff(sx.read(source),sx.read(WORK/'raw-routed.kicad_pcb'))==native['raw_immutable']=={'equal':True,'different_top_level_keys':[]}
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
 assert process['cwd']==str(WORK) and process['argv'][:3]==f.SANDBOX
 assert process['exit_code']==(5 if name.endswith('drc') else 0)
 assert process['status']==('nonzero_exit' if name.endswith('drc') else 'success')
 assert len(read_bytes(Path(process['log'])))==process['log_bytes']
 inner=next(x for x in native['steps'] if x['name']==name.removeprefix('ses-'))
 assert all(inner[k]==v for k,v in process.items())
 if name.endswith('drc'):
  label=name.removeprefix('ses-');binding=load(WORK/(label+'-binding.json'))
  argv=[*f.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(WORK/(label+'.json'))]
  if binding['saved']:argv.append('--save-board')
  argv.append(binding['input']);assert process['argv']==argv
 steps.append({k:step[k] for k in ('name','status','exit_code','wall_seconds','cpu_seconds','cleanup_complete')})
assert [x['name'] for x in steps]==['ses-generated-import','ses-generated-raw-drc','ses-refill-drc','ses-final-netclasses','ses-final-drc','ses-generated-metrics']
prior=ROOT/'.runs/pic-corrected-adapter-routing-001';cached=load(RUN/'cached-routing-summary.json')
assert cached==load(prior/'summary.json') and cached['status']=='failed'
assert all(sha(prior/n)==v for n,v in cached['frozen_evidence'].items())
assert all(read_bytes(RUN/n,16*1024*1024)==read_bytes(prior/n,16*1024*1024) for n in ('observations.json','raw.ses','prepared.json'))
assert before==inv(RUN) and original_before==inv(ROOT/'.data/boards/kicad-pic-programmer')
result={'scope':'Independent stored native evidence readback only; no native/JVM/solver/compiler execution','status':summary['status'],'routing_accepted':False,'native_scope_passed':False,'git_head':runtime['git']['head'],'full_run_files_unchanged':len(before),'frozen_files':len(summary['frozen_evidence']),'original_files_unchanged':len(original_before),'candidate_sha256':native['candidate_sha256'],'candidate_original_rules_and_immutable_geometry_equal':True,'raw_import_immutable_equal':True,'reports':reports,'native_class_and_generated_dimensions_audit_equal':True,'metrics':native['metrics'],'steps':steps,'exact_generated_engine_SES_segments':337,'prior_failed_routing_unchanged':True,'prior_cost':summary['routing_reuse'],'cost':{k:summary[k] for k in ('wall_seconds','total_cpu_seconds','accounting_point')},'unsupported':native['original_preflight_reasons'],'bindings':{n:before[n] for n in ('summary.json','runtime.json','cached-routing-summary.json','routing-native/final-drc.json','routing-native/final-drc-binding.json','routing-native/final-netclass-audit.json')}}
(OUT/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('status','git_head','full_run_files_unchanged','frozen_files','candidate_sha256','metrics','cost')},indent=2))
