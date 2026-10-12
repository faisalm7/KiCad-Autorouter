"""SES native diagnostic using the shared Job.drc/native and parent process runner."""
import shutil
import hashlib
from collections import Counter
from autorouter import pipeline as p, floor_route as floor, sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import ses_checks as checks

class SesJob(floor.FloorJob):
    def __init__(self,out,remaining,dispatch,env):
        super().__init__(out,180,remaining);self.dispatch=dispatch
        self.env.update(env)
    def step(self,name,argv,allowed=(0,),*,already_sandboxed=False):
        result=self.dispatch('ses-'+name,[str(x) for x in (argv if already_sandboxed else [*floor.SANDBOX,*argv])],30,
            allowed=allowed,cwd=self.out,env_override=self.env)
        self.steps.append({'name':name,**result});return result

def semantic_diff(original,actual):
    old=p.immutable(original);new=p.immutable(actual)
    if old==new:return {'equal':True,'different_top_level_keys':[]}
    keys=sorted({n[0] for tree in (old,new) for n in tree if isinstance(n,list) and n})
    changed=[k for k in keys if sx.children(old,k)!=sx.children(new,k)]
    return {
        'equal':False,'different_top_level_keys':changed,
        'original_immutable_sha256':hashlib.sha256(sx.dump(old).encode()).hexdigest(),
        'imported_immutable_sha256':hashlib.sha256(sx.dump(new).encode()).hexdigest()}

def same_findings(a,b):
    def values(x):return Counter(floor.canonical(v) for v in x['findings'])
    return all(a[k]==b[k] for k in ('opens','blocking','warnings','exclusions','ignored_checks')) and values(a)==values(b)

def negative_findings(baseline,bad,raw,padids,net):
    """Require a new actual unexcluded error from the native opens section."""
    old={floor.canonical(v) for v in baseline['findings']}
    findings=[v for v in raw['unconnected_items'] if v.get('type')=='unconnected_items'
        and v.get('severity')=='error' and v.get('excluded',False) is False and floor.canonical(v) not in old
        and any(i.get('uuid') in padids and net in i.get('description','') for i in v['items'])]
    if bad['opens']<=baseline['opens']:return []
    return findings

def execute(out,source,tree,expected,transport,remaining,dispatch,env,capture,record):
    job=SesJob(out/'ses-native',remaining,dispatch,env)
    original=sx.read(source);record['native_ses']={'routing_accepted':False,'candidate_emitted':False}
    result=record['native_ses']
    def copied(name,include_board=True):
        dest=job.out/name;dest.mkdir()
        for file in source.parent.rglob('*'):
            relative=file.relative_to(source.parent)
            if file.is_dir():(dest/relative).mkdir(exist_ok=True)
            elif include_board or file!=source:shutil.copy2(file,dest/relative)
        return dest/source.name
    baseline=job.drc('baseline',source,save=False);result['baseline']=baseline;capture()
    raw=copied('raw-positive',False)
    job.native('import-positive','import',source,raw,out/'raw.ses')
    p.verify_candidate_files(raw,p.tree_hash(source.parent));capture()
    imported=sx.read(raw)
    result['raw_immutable']=semantic_diff(original,imported)
    before_tracks,before_vias=checks.source_routes(original);after_tracks,after_vias=checks.source_routes(imported)
    result['raw_routes']=checks.diff(before_tracks,after_tracks);result['raw_vias_equal']=before_vias==after_vias
    result['raw_board_sha256']=p.sha(raw)
    raw_native=job.drc('raw-positive-drc',raw,save=False);result['raw_native']=raw_native
    result['raw_findings_equal']=same_findings(baseline,raw_native);capture()
    if (result['raw_immutable']['equal'] and result['raw_routes']['equal'] and result['raw_vias_equal']
            and transport['exact_route_survival'] and result['raw_findings_equal']):
        candidate=copied('candidate')
        rebuilt=p.transplant_routes(original,imported,protected=tuple(r for r in p.routes(original) if p.locked(r)))
        sx.write(candidate,rebuilt);capture()
        if p.immutable(rebuilt)!=p.immutable(original):raise ValueError('reconstructed immutable mismatch')
        final=job.drc('final-drc',candidate,save=False)
        p.verify_candidate_files(candidate,p.tree_hash(source.parent));result.update(candidate_emitted=True,candidate_sha256=p.sha(candidate),final_native=final,
            final_findings_equal=same_findings(baseline,final),final_bound_report=str(job.out/'final-drc.json'),final_bound_report_sha256=p.sha(job.out/'final-drc.json'))
        capture()
    invalid,recipe=checks.disconnected(tree,original,expected);negative=out/'disconnected.ses'
    negative.write_bytes(invalid);result['negative_recipe']=recipe;capture()
    bad=copied('raw-negative',False);job.native('import-negative','import',source,bad,negative)
    p.verify_candidate_files(bad,p.tree_hash(source.parent));capture()
    bad_native=job.drc('negative-drc',bad,save=False);result['negative_native']=bad_native
    padids={sx.unquote(sx.one(pad,'uuid')[1]) for fp in sx.children(original,'footprint') for pad in sx.children(fp,'pad') if sx.one(pad,'net')==['net','"'+recipe['net']+'"']}
    newopens=negative_findings(baseline,bad_native,floor.read_json(job.out/'negative-drc.json'),padids,recipe['net'])
    result['negative_required_findings']=newopens
    result['negative_detected']=bad_native['opens']>baseline['opens'] and bool(newopens)
    result['negative_immutable']=semantic_diff(original,sx.read(bad))
    result['completed']=bool(result['candidate_emitted'] and result.get('final_findings_equal') and result['negative_detected'] and result['negative_immutable']['equal'])
    result['steps']=job.steps;capture()
    return result
