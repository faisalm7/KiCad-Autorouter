"""Read back this completed fixed diagnostic with its existing shared helpers."""
from pathlib import Path
from types import SimpleNamespace
import ast,collections,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;RUN=ROOT/'.runs/drc-input-protection-001';PKG=ROOT/'experiments/drc_input_protection_v1'
sys.dont_write_bytecode=True;sys.path[:0]=[str(PKG),str(ROOT)]
import driver as d
p=d.p;f=d.f
read=d.shared.read;h=p.sha
result=read(RUN/'summary.json');protocol=read(RUN/'code/experiments/drc_input_protection_v1/PROTOCOL.json')
assert result['status']=='observations_complete' and result['observations_complete'] is True and result['original_inputs_unchanged'] is True
assert all(result[key] is False for key in d.FALSE_FLAGS)
assert result['tools']['git_head']=='13d8db4d10cccaca715151184ecbaf16eb55d02f'
assert len(result['steps'])==4 and [x['case'] for x in result['cases']]==list(d.CASES)
assert h(RUN/'code/experiments/drc_input_protection_v1/PROTOCOL.json')==result['protocol_sha256']
assert result['sandbox_profile']==d.PROFILE
before=d.inventory(RUN);originals={path:d.inventory(Path(path)) for path in result['original_trees']}
assert originals==result['original_trees']=={str(ROOT/name):value for name,value in protocol['original_trees'].items()}
assert d.inventory(RUN/'code')==result['code_inventory']==result['runtime_sources']
assert all(result['runtime_sources'][name]==value for name,value in result['tools']['implementation_sha256'].items())
# ROOT may edit unrelated implementation after the run. Require exact unchanged
# helper bytes and exact ASTs for shared functions actually used in this readback.
for name in ['driver.py','canary.py']:
 assert h(PKG/name)==h(RUN/'code/experiments/drc_input_protection_v1'/name)
assert h(ROOT/'experiments/placement_production_controls_v1/driver.py')==h(RUN/'code/experiments/placement_production_controls_v1/driver.py')
def function(path,name):
 return ast.dump(next(n for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),include_attributes=False)
functions={'autorouter/pipeline.py':['parse_report','check_drc_project','native_accepted','native_rejection_reasons','sha'],
 'autorouter/floor_route.py':['process_check','read_json','canonical'],
 'autorouter/placement_clearance.py':['inventory','read_bytes'],
 'experiments/lipo_native_diagnostic_v1/driver.py':['inventory','read','owned','sha_bytes']}
for name,names in functions.items():
 for fn in names:assert function(ROOT/name,fn)==function(RUN/'code'/name,fn),(name,fn)
current_differences=[name for name,digest in result['runtime_sources'].items() if h(ROOT/name)!=digest]
for name,digest in result['tools']['files'].items():assert h(Path(name))==digest
outer=read(ROOT/'.runs/drc-input-protection-001-execution.json');wrapper=ROOT/'.runs/run-drc-input-protection-001.py';log=ROOT/'.runs/drc-input-protection-001-command.log'
assert outer['wrapper_sha256']==h(wrapper) and outer['log_sha256']==h(log) and outer['log_bytes']==log.stat().st_size
assert outer['exit_code']==0 and outer['cleanup_signals']==[] and outer['git_head']==result['tools']['git_head'] and outer['cwd']==str(ROOT)
assert outer['argv']==['python3','-B','experiments/drc_input_protection_v1/driver.py','--run-native','--output','.runs/drc-input-protection-001']
assert json.loads(log.read_bytes())=={key:result[key] for key in ('status','observations_complete','routing_accepted')}
assert result['within_budget'] is True and result['budget_seconds']==result['cpu_budget_seconds']==30 and result['output_ceiling_bytes']==d.LIMIT
assert 0<result['wall_seconds']<outer['wall_seconds']<30 and 0<result['total_cpu_seconds']<outer['waited_child_cpu_seconds']<30
base_receipt=read(ROOT/protocol['fixture_receipt']);candidate=Path(base_receipt['candidate']);base=d.bytes_tree(candidate.parent)
legacy=(ROOT/protocol['owned_legacy_prl']).read_bytes();facts=[]
for row in result['cases']:
 case=row['case'];out=RUN/case;name='canary' if case=='canary' else 'drc';process=read(out/(name+'-process.json'))
 job=SimpleNamespace(out=out,steps=[step for step in result['steps'] if step['cwd']==str(out)],captured=row['stage_evidence'])
 assert len(job.steps)==1 and result['captured_stages'][str(out)]==job.captured
 d.check_capture(job)
 assert process['cleanup_complete'] is True and process['name']==name and process['argv']==row['stage_evidence'][name]['argv']
 assert process['status']==('success' if process['exit_code']==0 else 'nonzero_exit')
 assert process['cpu_seconds']>=0 and process['wall_seconds']>0 and process['resource_guards']['max_workdir_bytes']==d.LIMIT
 entry={'case':case,'process_sha256':h(out/(name+'-process.json')),'log_sha256':h(out/(name+'.log')),'report_sha256':h(out/(name+'.json')),
   'exit_code':process['exit_code'],'wall_seconds':process['wall_seconds'],'cpu_seconds':process['cpu_seconds'],'cleanup_complete':True,'actual_argv':process['argv']}
 if case=='canary':
  raw=read(out/'canary.json');assert d.canary_check(raw,out/'canary-input')==row['result']
  f.process_check(out,{'steps':job.steps},name,d.prefix(out/'canary-input')+d.stage_argv(out,name))
  assert all(v==d.digest(d.canary.SENTINEL) for v in d.inventory(out/'canary-input').values())
  assert (out/'canary.replace-source').read_bytes()==b'owned outside replacement\n'
  entry.update(attempts=raw['attempts'],outside_write_succeeded=True)
 else:
  source=Path(row['source']);assert d.inventory(source.parent)==row['source_hashes']
  if case in ('positive','missing_via'):
   board,project,mutation=d.fixture.prepare(case,base[candidate.name],base[candidate.with_suffix('.kicad_pro').name])
   expected=d.hashes(dict(base,**{candidate.name:board,candidate.with_suffix('.kicad_pro').name:project,candidate.with_suffix('.kicad_prl').name:legacy}))
   assert expected==row['source_hashes'] and mutation==row['mutation']
  raw,native=d.drc_readback(job,source,row['source_hashes']);assert f.canonical(native)==f.canonical(row['native'])
  if case=='positive':assert p.native_accepted(native) and native['warnings']==0 and native['ignored_checks']==protocol['fixture_effective_ignored']
  elif case=='missing_via':assert d.negative_check(raw,native,row['mutation'],protocol['fixture_effective_ignored'])==row['witness']
  else:
   assert f.canonical(native)==f.canonical(p.parse_report(ROOT/protocol['paw_old_report'],source.name))
   assert native['ignored_checks']==protocol['paw_effective_ignored'] and len(row['source_hashes'])==14
  project=read(source.with_suffix('.kicad_pro'));ignored=sorted(k for k,v in project['board']['design_settings']['rule_severities'].items() if v=='ignore')
  assert ignored==protocol['paw_explicit_ignored' if case=='paw3395' else 'fixture_explicit_ignored']
  prl=source.with_suffix('.kicad_prl');actual=out/'drc-input'/prl.name;assert h(prl)==h(actual)==row['source_hashes'][prl.name]
  entry.update(native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},finding_types=dict(collections.Counter(x['type']+':'+x['severity'] for x in native['findings'])),
    ignored_checks=native['ignored_checks'],explicit_ignored=ignored,prl_sha256=h(prl),original_project_files=len(row['source_hashes']),binding_sha256=h(out/'drc-binding.json'),target_witness=row['witness'])
 facts.append(entry)
old=read(ROOT/'.runs/paw3395-native-diagnostic-001/summary.json');assert old['observations_complete'] is False and old['status']!='observations_complete'
assert d.inventory(RUN)==before and {path:d.inventory(Path(path)) for path in originals}==originals
for name,names in functions.items():
 for fn in names:assert function(ROOT/name,fn)==function(RUN/'code'/name,fn)
value={'schema':1,'audit_passed':True,'no_new_native_execution':True,'stored_head':result['tools']['git_head'],'summary_sha256':h(RUN/'summary.json'),
 'outer_execution_sha256':h(ROOT/'.runs/drc-input-protection-001-execution.json'),'wrapper_sha256':h(wrapper),'protocol_sha256':result['protocol_sha256'],
 'run_inventory':{'file_count':len(before),'bytes':sum((RUN/name).stat().st_size for name in before),'sha256':d.digest(f.canonical(before).encode())},
 'original_inventory_counts':{str(Path(path).relative_to(ROOT)):len(value) for path,value in originals.items()},'original_and_run_unchanged':True,
 'captured_code_inventory_exact':True,'used_shared_function_asts_exact':True,'current_runtime_file_differences':current_differences,'recorded_tool_files_still_exact':True,
 'cases':facts,'costs':{'stored_wall_seconds':result['wall_seconds'],'stored_full_cpu_seconds':result['total_cpu_seconds'],'outer_wall_seconds':outer['wall_seconds'],'outer_waited_cpu_seconds':outer['waited_child_cpu_seconds'],
   'stored_accounting_point':result['accounting_point']},'old_paw001':{'status':old['status'],'observations_complete':False,'error':old.get('error'),'summary_sha256':h(ROOT/'.runs/paw3395-native-diagnostic-001/summary.json')},
 'scope':'Observed protected-input diagnostic only; no production, legacy format/severity, library closure, save/import or routing qualification. Finite hash/readback samples; no claim of atomic authentication.'}
(OUT/'facts.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'audit_passed':True,'cases':[(x['case'],x.get('native_counts')) for x in facts],'run_files':len(before),'current_code_differences':current_differences}))
