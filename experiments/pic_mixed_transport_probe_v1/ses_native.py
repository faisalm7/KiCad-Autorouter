"""SES native diagnostic using the shared Job.drc/native and parent process runner."""
import shutil
import hashlib
from collections import Counter
from autorouter import pipeline as p, floor_route as floor, sexpr as sx
from experiments.pic_mixed_transport_probe_v1 import ses_checks as checks

def validation_copy(source,destination,imported=None):
    """Copy original rules/dependencies; use only the isolated import's PCB."""
    shutil.copytree(source.parent,destination)
    board=destination/source.name
    if imported is not None:shutil.copy2(imported,board)
    p.verify_candidate_files(board,p.tree_hash(source.parent))
    return board

def cached_positive(cached,before,inventory):
    """Read the fixed failed receipt; never mark its project rewrite accepted."""
    old=floor.read_json(cached/'summary.json');work=cached/'ses-native'
    original=before['original'];source=cached/'observe-input/pic_programmer.kicad_pcb'
    if (old.get('status')!='failed' or old.get('error')!='Rejected: candidate project/rules/file set changed'
            or old['runtime']['original']!=original or old['runtime']['tools']!=before['tools']
            or any(inventory.get(k)!=v for k,v in old['frozen_evidence'].items())
            or p.tree_hash(source.parent)!=original):raise ValueError('cached native failure/source differs')
    for name in ('autorouter/native.py','autorouter/pipeline.py','autorouter/floor_route.py','autorouter/sexpr.py'):
        if old['runtime']['sources'][name]!=before['sources'][name]:raise ValueError('cached native implementation differs')
    if [s['name'] for s in old['steps']]!=['ses-baseline','ses-import-positive']:
        raise ValueError('cached native stages differ')
    board=work/'baseline-input'/source.name
    binding=floor.read_json(work/'baseline-binding.json')
    if (binding.get('source')!=str(source) or binding.get('input')!=str(board)
            or binding.get('saved') is not False or binding.get('before')!=original
            or binding.get('after')!=p.tree_hash(board.parent)):
        raise ValueError('cached baseline binding differs')
    p.check_drc_project(original,binding['after'],source.name,saved=False)
    baseline=p.parse_report(work/'baseline.json',source.name)
    if baseline!=old['native_ses']['baseline']:raise ValueError('cached baseline summary differs')
    raw=work/'raw-positive'/source.name
    commands=[[*floor.SANDBOX,str(p.c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(work/'baseline.json'),str(board)],
        [*floor.SANDBOX,str(p.c.PYTHON),str(p.c.ROOT/'autorouter/native.py'),'import',str(source),str(raw),str(cached/'raw.ses')]]
    for step,argv,code in zip(old['steps'],commands,(5 if baseline['findings'] else 0,0)):
        process=floor.read_json(cached/(step['name']+'-process.json'))
        expected=dict(process,name=step['name'])
        if (step!=expected or process.get('argv')!=argv or process.get('cwd')!=str(work)
                or type(process.get('exit_code')) is not int or process['exit_code']!=code
                or process.get('status')!=('success' if code==0 else 'nonzero_exit')
                or process.get('cleanup_complete') is not True or process.get('log_truncated') is not False):
            raise ValueError('cached native process differs')
    return baseline,raw,{'run':str(cached),'summary_sha256':p.sha(cached/'summary.json'),
        'git_head':old['runtime']['git']['head'],'original_status':old['status'],
        'prior_run_wall_seconds':old['wall_seconds'],'prior_run_total_cpu_seconds':old['total_cpu_seconds'],
        'new_baseline_execution':False,'new_positive_import_execution':False,
        'raw_board_sha256':p.sha(raw),'baseline_report_sha256':p.sha(work/'baseline.json'),
        'scope':'Original failed receipt retained; reuse actual imported PCB only, never its generated project/rules.'}

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

def execute(out,source,tree,expected,transport,remaining,dispatch,env,capture,record,reuse=None):
    job=SesJob(out/'ses-native',remaining,dispatch,env)
    original=sx.read(source);record['native_ses']={'routing_accepted':False,'candidate_emitted':False}
    result=record['native_ses']
    if reuse is None:
        baseline=job.drc('baseline',source,save=False)
        raw=job.out/'raw-positive.kicad_pcb'
        job.native('import-positive','import',source,raw,out/'raw.ses')
    else:
        baseline,saved,binding=reuse;raw=job.out/'raw-positive.kicad_pcb'
        shutil.copy2(saved,raw);result['native_reuse']=binding
    result['baseline']=baseline;capture()
    positive=validation_copy(source,job.out/'positive-project',raw);capture()
    imported=sx.read(raw)
    result['raw_immutable']=semantic_diff(original,imported)
    before_tracks,before_vias=checks.source_routes(original);after_tracks,after_vias=checks.source_routes(imported)
    result['raw_routes']=checks.diff(before_tracks,after_tracks);result['raw_vias_equal']=before_vias==after_vias
    result['raw_board_sha256']=p.sha(raw)
    raw_native=job.drc('raw-positive-drc',positive,save=False);result['raw_native']=raw_native
    result['raw_findings_equal']=same_findings(baseline,raw_native);capture()
    if (result['raw_immutable']['equal'] and result['raw_routes']['equal'] and result['raw_vias_equal']
            and transport['exact_route_survival'] and result['raw_findings_equal']):
        candidate=validation_copy(source,job.out/'candidate')
        rebuilt=p.transplant_routes(original,imported,protected=tuple(r for r in p.routes(original) if p.locked(r)))
        sx.write(candidate,rebuilt);capture()
        if p.immutable(rebuilt)!=p.immutable(original):raise ValueError('reconstructed immutable mismatch')
        final=job.drc('final-drc',candidate,save=False)
        p.verify_candidate_files(candidate,p.tree_hash(source.parent));result.update(candidate_emitted=True,candidate_sha256=p.sha(candidate),final_native=final,
            final_findings_equal=same_findings(baseline,final),final_bound_report=str(job.out/'final-drc.json'),final_bound_report_sha256=p.sha(job.out/'final-drc.json'))
        capture()
    invalid,recipe=checks.disconnected(tree,original,expected);negative=out/'disconnected.ses'
    negative.write_bytes(invalid);result['negative_recipe']=recipe;capture()
    bad=job.out/'raw-negative.kicad_pcb';job.native('import-negative','import',source,bad,negative);capture()
    negative_project=validation_copy(source,job.out/'negative-project',bad);capture()
    bad_native=job.drc('negative-drc',negative_project,save=False);result['negative_native']=bad_native
    padids={sx.unquote(sx.one(pad,'uuid')[1]) for fp in sx.children(original,'footprint') for pad in sx.children(fp,'pad') if sx.one(pad,'net')==['net','"'+recipe['net']+'"']}
    newopens=negative_findings(baseline,bad_native,floor.read_json(job.out/'negative-drc.json'),padids,recipe['net'])
    result['negative_required_findings']=newopens
    result['negative_detected']=bad_native['opens']>baseline['opens'] and bool(newopens)
    result['negative_immutable']=semantic_diff(original,sx.read(bad))
    result['completed']=bool(result['candidate_emitted'] and result.get('final_findings_equal') and result['negative_detected'] and result['negative_immutable']['equal'])
    result['steps']=job.steps;capture()
    return result
