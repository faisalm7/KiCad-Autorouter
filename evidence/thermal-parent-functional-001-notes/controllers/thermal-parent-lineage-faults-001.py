"""Finite cold/cached proof faults on job copies; no Native execution."""
from pathlib import Path
import argparse,json,sys,copy,time,resource,hashlib
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();ROOT=Path(__file__).resolve().parents[1];ap=argparse.ArgumentParser();ap.add_argument('--runtime',required=True);ap.add_argument('--protocol',required=True);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args();runtime=Path(a.runtime);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,placement_clearance as io,review_export as ex
protocol=Path(a.protocol);assert p.sha(protocol)==a.protocol_sha256;plan=f.read_json(protocol);assert p.sha(Path(__file__))==plan['controller_sha256'];assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7' and Path(sys.prefix).resolve()==runtime/'.venv';assert p.tool_manifest()==plan['tools']
receipt=Path(plan['route_receipt']);directory=receipt.parent;out=Path(plan['output']);out.mkdir();source=Path(plan['source']);initial=io.inventory(directory,max_bytes=64*1024**2,max_files=2000);original_source=io.inventory(source.parent);assert p.sha(receipt)==plan['route_receipt_sha256'];assert p.check_result(receipt)['current'];data=f.read_json(receipt);child=directory/'incumbent/result.json';repair=directory/'recovery/repair.json';geometry=directory/'recovery/geometry.json';proposal=directory/'recovery/proposals.json'
def raw(value):return (json.dumps(value,indent=2)+'\n').encode()
def sha(value):return hashlib.sha256(value).hexdigest()
def parent_change(key,value=None,delete=False):
 q=copy.deepcopy(data)
 if delete:q.pop(key)
 else:q[key]=value
 return {receipt:raw(q)}
def child_profile():
 q=f.read_json(child);q['engine_profile']='completion-only';b=raw(q);parent=copy.deepcopy(data);parent['incumbent']['receipt_sha256']=sha(b);return {child:b,receipt:raw(parent)}
def omitted_map():
 q=f.read_json(repair);t=q['trials'][0];removed=[s for s in t['steps'] if s['name'] in ('final-netclasses','thermal-final-netclasses')];assert len(removed)==1;row=removed[0];t['steps']=[s for s in t['steps'] if s is not row];parent=copy.deepcopy(data);parent['repair']=q;parent['steps']=[s for s in parent['steps'] if not(s['name']==row['name'] and s['cwd']==row['cwd'])]
 parent['child_cpu_seconds']=sum(s['cpu_seconds'] for s in parent['steps']);parent['monitor_cpu_seconds']=sum(s['monitor_cpu_seconds'] for s in parent['steps']);parent['total_cpu_seconds']=sum(parent[k] for k in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds'))
 return {repair:raw(q),receipt:raw(parent)}
def geometry_version():
 q=f.read_json(geometry);q['native_version']='10.0.0';return {geometry:raw(q)}
def proposal_change():
 q=f.read_json(proposal);q['path_certificate_candidates'][0]['start_nm'][0]+=1;return {proposal:raw(q)}
def rule_change():
 path=directory/'candidate'/source.with_suffix('.kicad_pro').name;q=f.read_json(path);old=q['board']['design_settings']['rule_severities']['clearance'];assert old=='error';q['board']['design_settings']['rule_severities']['clearance']='warning';return {path:raw(q)}
cases=[('deleted_parent_policy',lambda:parent_change('thermal_parent_policy',delete=True)),('erased_parent_strategy',lambda:parent_change('strategy',delete=True)),('false_recovery_branch',lambda:parent_change('recovery_needed',False)),('rejected_child_profile_label_with_rehashed_reference',child_profile),('omitted_classmap_compute_with_reauthored_totals',omitted_map),('mixed_geometry_Native_version',geometry_version),('proposal_endpoint_tamper',proposal_change),('incumbent_hash_substituted_as_selected',lambda:parent_change('candidate_sha256',f.read_json(child)['candidate_sha256'])),('copied_rule_severity_weakened',rule_change)]
assert [x[0] for x in cases]==plan['cases'];records=[];passed=False;error=None
try:
 for name,mutate in cases:
  assert max(time.monotonic()-START,cpu()-CPU0)<225;assert io.inventory(directory,max_bytes=64*1024**2,max_files=2000)==initial
  changes=mutate();saved={path:io.read_bytes(path) for path in changes};folder=out/name;folder.mkdir();rows=[]
  with p.validation_readback_session():
   assert p.check_result(receipt)['current']
   try:
    for index,(path,value) in enumerate(changes.items()):
     backup=folder/('%02d-original'%index);mutant=folder/('%02d-mutant'%index)
     with backup.open('xb') as s:s.write(saved[path])
     with mutant.open('xb') as s:s.write(value)
     rows.append(dict(path=str(path),original_sha256=sha(saved[path]),mutant_sha256=sha(value),original_copy=str(backup),mutant_copy=str(mutant)));path.write_bytes(value)
    failures=[]
    for mode,check in [('cold',lambda:p._check_result_uncached(receipt)),('cached',lambda:p.check_result(receipt))]:
     try:check()
     except (p.Rejected,OSError,ValueError,KeyError,TypeError) as exc:failures.append(dict(mode=mode,rejected=True,reason=type(exc).__name__+': '+str(exc)))
     else:raise AssertionError('fault was accepted: '+name+'/'+mode)
   finally:
    for path,value in saved.items():path.write_bytes(value)
   assert p.check_result(receipt)['current']
  assert io.inventory(directory,max_bytes=64*1024**2,max_files=2000)==initial and io.inventory(source.parent)==original_source
  record=dict(case=name,checks=failures,mutation=rows,original_job_bytes_restored=True,Native_executed=False);p.save_json(folder/'result.json',record);records.append(record)
 assert p.check_result(receipt)['current'] and ex.check_export(Path(plan['export_receipt']))['current'];passed=True
except BaseException as exc:error=type(exc).__name__+': '+str(exc)
restored=io.inventory(directory,max_bytes=64*1024**2,max_files=2000)==initial and io.inventory(source.parent)==original_source and p.tool_manifest()==plan['tools'] and p.sha(protocol)==a.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256']
report=dict(schema=1,kind='integrated-thermal-parent-evidence-fault-controls',controls_passed=passed and restored and max(time.monotonic()-START,cpu()-CPU0)+2<=240,accepted=False,project_complete=False,actual_GUI=False,Native_executed=False,human_review=False,protocol_sha256=a.protocol_sha256,route_receipt_sha256=p.sha(receipt),export_receipt_sha256=p.sha(Path(plan['export_receipt'])),cases=records,error=error,source_and_final_job_bytes_unchanged=restored,sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,scope='Nine deliberate job-evidence/rule faults; cold andin-session centralreaders mustrefuse. Exactoriginalbuffers/rightsretained andrestored; pristine source neverwritten. Positiveandexportreadersmustremaincurrentafterrestore. NoNative rerouting/validation, GUI, human or new routingqualityclaim.')
p.save_json(out/'result.json',report);print(json.dumps({k:report[k] for k in ('controls_passed','error','source_and_final_job_bytes_unchanged','sampled_wall_seconds','sampled_full_CPU_seconds')}));raise SystemExit(0 if report['controls_passed'] else 2)
