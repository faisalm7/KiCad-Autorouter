"""Original-rule native continuation using shared candidate validation and Job helpers."""
import copy
import shutil
from autorouter import pipeline as p, sexpr as sx, floor_route as floor
from experiments.pic_mixed_transport_probe_v1 import ses_native, ses_checks

def task_copy(source,destination):
    task=ses_native.validation_copy(source,destination)
    tree=sx.read(task)
    if any(p.locked(r) for r in p.routes(tree)):raise ValueError('finite diagnostic requires no protected original routing')
    stripped=copy.deepcopy(tree)
    stripped[:]=[n for n in stripped if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
    for zone in sx.children(stripped,'zone'):
        zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
    if p.immutable(tree)!=p.immutable(stripped) or p.routes(stripped):raise ValueError('task strip changed immutable source')
    sx.write(task,stripped)
    p.verify_candidate_files(task,p.tree_hash(source.parent))
    return task

def execute(out,source,expected,transport,remaining,dispatch,env,capture,record,pending_candidate):
    if transport.get('generated_engine_to_ses_exact') is not True:
        raise ValueError('new engine-to-SES geometry differs')
    job=ses_native.SesJob(out/'routing-native',remaining,dispatch,env)
    result={'candidate_emitted':False,'routing_accepted':False,'production_support_qualified':False}
    record['native_routing']=result
    task=task_copy(source,job.out/'task-project');capture()
    result['task_sha256']=p.sha(task);result['task_ordinary_routes']=len(p.routes(sx.read(task)))
    raw=job.out/'raw-routed.kicad_pcb'
    job.native('generated-import','import',task,raw,out/'raw.ses');capture()
    original=sx.read(source);imported=sx.read(raw)
    result['raw_immutable']=ses_native.semantic_diff(original,imported)
    result['raw_board_sha256']=p.sha(raw)
    # Observe raw native findings even if later transport/preservation guards reject.
    validation=ses_native.validation_copy(source,job.out/'raw-project',raw);capture()
    result['raw_native']=job.drc('generated-raw-drc',validation,save=False);capture()
    if not result['raw_immutable']['equal']:raise ValueError('raw import changed original nonrouting geometry')
    with pending_candidate(job.out/'candidate'/source.name):
        candidate=ses_native.validation_copy(source,job.out/'candidate')
        rebuilt=p.transplant_routes(sx.read(task),imported,protected=())
        sx.write(candidate,rebuilt);capture()
        final_hash,native=p.validate_candidate(job,original,candidate,p.tree_hash(source.parent),())
    p.verify_candidate_files(candidate,p.tree_hash(source.parent),final_hash)
    result.update(candidate_emitted=True,candidate_sha256=final_hash,final_native=native,
        final_bound_report=str(job.out/'final-drc.json'),final_bound_report_sha256=p.sha(job.out/'final-drc.json'),
        final_binding_sha256=p.sha(job.out/'final-drc-binding.json'),routing_accepted=p.native_accepted(native),
        original_preflight_reasons=p.preflight(source))
    if p.immutable(sx.read(candidate))!=p.immutable(original):raise ValueError('final candidate changed source intent')
    job.native('generated-metrics','metrics',candidate,job.out/'metrics.json')
    result['metrics']=floor.read_json(job.out/'metrics.json');result['steps']=job.steps
    p.verify_candidate_files(candidate,p.tree_hash(source.parent),final_hash);capture()
    # A native-clean diagnostic never grants production support for this input.
    result['completed']=result['routing_accepted']
    return result
