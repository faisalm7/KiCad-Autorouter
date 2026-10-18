"""Finite non-admitting component control; actual shared Native/repair helpers."""
from pathlib import Path
import argparse,json,sys,time,resource,copy,hashlib
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);ap.add_argument('--case',choices=('legacy0','native7','invalid7','cancel7'),required=True);a=ap.parse_args()
runtime=Path(a.runtime);assert runtime in (ROOT,ROOT/'.runs/runtime-directory-027/runtime');sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,thermal,floor_route as f,placement_clearance as io,sexpr as sx,config as c
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
protocol=Path(a.protocol);assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol);case=plan['cases'][a.case]
assert case['runtime']==str(runtime) and case['version']==c.NATIVE_VERSION and p.sha(Path(__file__))==plan['controller_sha256']
source=Path(plan['source']);source_hashes=plan['source_hashes'];old_candidate=Path(case['input_candidate']);output=Path(case['output']);seconds=plan['case_wall_CPU_seconds'];tools=p.tool_manifest();job=None;repair=None
assert p.tree_hash(source.parent)==source_hashes and p.sha(old_candidate)==case['input_candidate_sha256']
assert tools['implementation_sha256']==plan['implementation_sha256'] and tools['git_head']==plan['source_head']
if runtime!=ROOT:assert p.sha(runtime/'runtime-distribution.json')==plan['engineering_runtime_manifest_sha256']
p.check_storage(active_root=output);p.verify_candidate_files(old_candidate,source_hashes,case['input_candidate_sha256'])
report=dict(schema=1,kind='nonadmitting-selected-native-thermal-component',case=a.case,accepted=False,production_admitted=False,routing_accepted=False,component_passed=False,status='failed',actual_GUI=False,human_review=False,protocol_sha256=a.protocol_sha256,tools=tools,source_hashes=source_hashes,source=str(source),input_candidate=str(old_candidate),input_candidate_sha256=case['input_candidate_sha256'],budget_seconds=seconds,finalization_reserve_seconds=15,scope='Actual component observations/trials only; no normal Route/recover parent, no export or comparative gain/admission. Existing geometry, original rules/protected checks, <=4proposals and fresh fullSCH Native validation unchanged.')
def remaining():return max(0,min(seconds-(time.monotonic()-START),seconds-(cpu()-CPU0))-15)
def stable():
 assert p.sha(protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256']
 assert p.tree_hash(source.parent)==source_hashes and p.sha(old_candidate)==case['input_candidate_sha256']
 assert p.tool_manifest()==tools
 if job is not None:assert p.tree_hash(job.out/'snapshot')==source_hashes
try:
 job=p.Job(output,seconds,protect_local_settings=True);job.started=START;job.deadline=START+seconds;job.cpu_started=time.process_time()
 original=p.preflight(source);protected=copy.deepcopy([x for x in p.routes(original) if p.locked(x)])
 for folder,files in ((job.out/'snapshot',io.inventory(source.parent,contents=True)),(job.out/'candidate',io.inventory(old_candidate.parent,contents=True))):
  folder.mkdir()
  for name,raw in files.items():
   target=folder/name;target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as s:s.write(raw)
 candidate=job.out/'candidate'/source.name
 if a.case=='invalid7':
  native_map=Path(case['input_native_map']);assert p.sha(native_map)==case['input_native_map_sha256'];rows=f.read_json(native_map)['nets'];classes={r['name']:r['class'] for r in rows if r['copper_pad_count']>0}
  tree=sx.read(candidate);names={sx.atom(n[1]):sx.unquote(n[2]) for n in sx.children(original,'net')};ids={name:i for i,name in names.items()}
  track=next(r for r in p.routes(tree) if sx.atom(r[0])=='segment' and r not in protected and names.get(sx.atom(sx.one(r,'net')[1])) in classes)
  old_id=sx.atom(sx.one(track,'net')[1]);old_name=names[old_id];new_name=next(n for n in sorted(classes) if n!=old_name and classes[n]==classes[old_name] and n in ids)
  sx.one(track,'net')[1]=ids[new_name];candidate.write_text(sx.dump(tree)+'\n')
  report['deliberate_candidate_fault']=dict(kind='one unprotected segment assigned to a different same-class source net',old_net=old_name,new_net=new_name,original_source_changed=False)
 stable();print('fresh-candidate-validation',flush=True)
 digest,native=p.validate_candidate(job,original,candidate,source_hashes,protected,schematic_parity=True)
 report.update(prevalidation_native=native,prevalidation_candidate_sha256=digest,prevalidation_report_sha256=p.sha(job.out/'final-drc.json'),protected_count=len(protected))
 if a.case!='invalid7':assert thermal.sole_thermal(native) is not None,'fresh prevalidation is not an eligible solethermal'
 else:assert thermal.sole_thermal(native) is None and (native['opens']>0 or native['blocking']>1),'deliberate fault did not establish a Native invalid control'
 stable();assert remaining()>8;print('thermal-component',flush=True)
 repair=thermal.attempt_repair(job,original,candidate,source_hashes,protected,native,report_path=job.out/'final-drc.json',binding_path=job.out/'final-drc-binding.json',remaining_seconds=remaining,out=job.out/'recovery')
 report['repair']=repair;assert repair['routing_accepted'] is False
 if a.case=='invalid7':
  assert repair['validation_passed'] is False and repair['geometry_receipt'] is None and not repair['trials'];report.update(component_passed=True,status='invalid_native_refused')
 else:report.update(component_passed=repair['validation_passed'] is True,status='component_validated' if repair['validation_passed'] else 'unsupported_or_native_rejected')
except (Exception,KeyboardInterrupt) as exc:
 report.update(component_passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
finally:
 try:stable()
 except BaseException as exc:report.update(component_passed=False,status='freshness_failed',freshness_error=type(exc).__name__+': '+str(exc))
 report.update(steps=job.steps if job else [],sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_exit_accounting_required=True,source_originals_unchanged=p.tree_hash(source.parent)==source_hashes)
 if max(report['sampled_wall_seconds'],report['sampled_full_CPU_seconds'])>seconds:report.update(component_passed=False,status='budget_exceeded')
 if job is not None:p.save_json(job.out/'component-result.json',report)
 print(json.dumps({k:report.get(k) for k in ('case','status','component_passed','accepted','production_admitted','reason','sampled_wall_seconds','sampled_full_CPU_seconds')}),flush=True)
raise SystemExit(0 if report['component_passed'] else 130 if report['status']=='cancelled' else 2)
