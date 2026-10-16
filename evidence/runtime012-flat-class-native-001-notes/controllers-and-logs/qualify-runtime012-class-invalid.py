"""One actual same-rule Native short, through shared installed validation."""
import json,resource,shutil,sys,time,uuid
from pathlib import Path
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu();runtime=Path(sys.argv[1]);setup_path=Path(sys.argv[2]);sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,config as c,floor_route as f,handoff as h,schematic_class_evidence as classes,placement_clearance as pc,sexpr as sx
assert c.ROOT==runtime and Path(sys.prefix).resolve()==runtime/'.venv'
setup=f.read_json(setup_path);tools=p.tool_manifest();assert tools['git_head']==setup['source_head']
receipt=runtime/'.runs/class-controls-001/clean-route/result.json';assert p.check_result(receipt)['current']is True
prior=f.read_json(receipt);source=Path(prior['source']);before=p.tree_hash(source.parent);original=sx.read(source);protected=p.protected_for_record(prior,original)
out=runtime/'.runs/class-invalid-short-001';out.mkdir();owner={};h.capture_destination(owner,out);pin=p.sha(Path(__file__))
record=dict(schema=1,accepted=False,control_passed=False,status='failed',actual_GUI=False,human_review=False,source=str(source),source_hashes=before,tools=tools,driver_sha256=pin,
 scope='Deliberately shorting owned candidate route only; immutable source/ten protected traces/rules untouched. Actual installed shared validate_candidate/refill/fullSCH/class comparator and shared process/DRC/proof readers. No engine, human/electrical or general quality claim.')
try:
 job=p.Job(out/'validation',60,protect_local_settings=True);candidate=job.out/'candidate'/source.name;shutil.copytree(Path(prior['candidate']).parent,candidate.parent)
 bad=sx.read(candidate);bad.append(['segment',['start','12','10'],['end','12','16'],['width','0.4'],['layer','"F.Cu"'],['net','"ROUTE"'],['uuid',json.dumps(str(uuid.uuid5(uuid.NAMESPACE_URL,'owned-flat-class-invalid-short-001')))]])
 sx.write(candidate,bad);preimage=p.sha(candidate)
 assert p.immutable(bad)==p.immutable(original)and all(route in p.routes(bad)for route in protected)
 digest,native=p.validate_candidate(job,original,candidate,before,protected,class_context=classes.CONTEXT)
 assert p.native_accepted(native)is False and native['blocking']>0 and any(row['type']=='shorting_items'for row in native['findings'])
 expected=dict(before);expected[source.name]=digest
 observed=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,job.out/'final-drc-input'/source.name,False,expected,schematic_parity=True,sandboxed=False)
 assert observed==native
 copied=dict(before);copied[source.name]=preimage
 f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',job.out/'refill'/source.name,job.out/'refill'/source.name,True,copied,sandboxed=False)
 data=dict(steps=job.steps,source_hashes=before,schematic_class_final=job.schematic_class_final)
 proof=classes.check(job.out,data,'final',board_raw=pc.read_bytes(candidate),source=str(candidate),project_raw=pc.read_bytes(candidate.with_suffix('.kicad_pro')),schematic_raw=pc.read_bytes(candidate.with_suffix('.kicad_sch')),native_map=job.out/'final-netclasses.json')
 assert proof['qualification']['class_parity_qualified']is True
 assert p.sha(candidate)==digest and p.tree_hash(source.parent)==before and p.tool_manifest()==tools and p.sha(Path(__file__))==pin
 assert h.owned_destination(owner)==out
 record.update(control_passed=True,status='passed',native=native,steps=job.steps,candidate=str(candidate),candidate_sha256=digest,final_native_sha256=p.sha(job.out/'final-drc.json'),class_metadata=job.schematic_class_final,class_parity_qualified=True,routing_accepted=False,protected_routes=len(protected),source_unchanged=True)
except(Exception,KeyboardInterrupt)as exc:record.update(control_passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',error=type(exc).__name__+': '+str(exc))
record.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,publication_allowance_seconds=2,external_exit_required=True)
if max(record['sampled_wall_seconds'],record['sampled_full_CPU_seconds'])+2>90:record.update(control_passed=False,status='budget_exceeded')
p.save_json(out/'result.json',record);print(json.dumps(dict(control_passed=record['control_passed'],status=record['status'],error=record.get('error'))))
raise SystemExit(0 if record['control_passed']else 2)
