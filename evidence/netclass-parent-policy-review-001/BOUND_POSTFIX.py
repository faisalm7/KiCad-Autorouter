"""Exact final bound closure: synthetic completed semantic state, real journals.

Only process binding, raw transport identity and final reconstruction publication
boundaries are tested here. Native geometry helpers are explicitly synthetic.
"""
import ast, copy, hashlib, json, subprocess, sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from autorouter import config as c, floor_route as f, netclass as n, pipeline as p, sexpr as sx, placement_clearance as io
from test_netclass_parent_policy import example

def main():
    source=ROOT/'experiments/netclass_parent_transport_v1/driver.py';raw=source.read_bytes()
    (OWN/'transport-driver-after-fix.py').write_bytes(raw)
    module=ast.parse(raw);experiment=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='experiment')
    node=next(x for x in experiment.body if isinstance(x,ast.FunctionDef) and x.name=='bound')
    scratch=OWN/'bound-postfix-seam';scratch.mkdir(exist_ok=False)
    case=scratch/'completed-case';jobdir=case/'job';jobdir.mkdir(parents=True)
    candidate=case/'candidate/fixture.kicad_pcb';candidate.parent.mkdir();candidate.write_text('(kicad_pcb)\n')
    original=case/'original';original.mkdir();sourceboard=original/candidate.name;sourceboard.write_bytes(candidate.read_bytes())
    _,native,project=example();(original/'fixture.kicad_pro').write_text(json.dumps(project))
    (jobdir/'native.dsn').write_bytes(b'(pcb synthetic)\n');(jobdir/'task.dsn').write_bytes(b'(pcb synthetic)\n')
    (jobdir/'imported.kicad_pcb').write_bytes(candidate.read_bytes());(jobdir/'refill').mkdir();(jobdir/'refill'/candidate.name).write_bytes(candidate.read_bytes())
    settings=['strict-synthetic-settings'];engineargv=['synthetic-engine','task.dsn','routes.ses']
    steps=[]
    for name,action,inputboard,target,args in [
       ('export','export',sourceboard,jobdir/'native.dsn',[jobdir/'native-netclasses.json']),
       ('import','import',sourceboard,jobdir/'imported.kicad_pcb',[jobdir/'routes.ses']),
       ('final-netclasses','netclasses',candidate,jobdir/'final-netclasses.json',[])]:
        argv=[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),action,str(inputboard),str(target),*[str(x) for x in args]]
        steps.append({'name':name,'argv':argv,'cwd':str(jobdir),'exit_code':0,'status':'success','cleanup_complete':True})
    steps.append({'name':'engine','argv':engineargv,'cwd':str(jobdir),'exit_code':0,'status':'success','cleanup_complete':True})
    job=SimpleNamespace(out=jobdir,steps=copy.deepcopy(steps))
    row={'case':'completed-case','final_candidate':str(candidate),'geometry':{'passed':True},'route_dimensions':{'passed':True},'dsn_audit':{'passed':True},'engine_settings':{'argv':settings},'protected_import':{'preserved':True}}
    def transplant(original,imported,**kwargs):
        kwargs['audit'].update(preserved=True);return ['kicad_pcb']
    namespace={'checks':[(job,'final-drc',candidate,{},False,{'passed':True})],
       'native_binding':lambda *a,**k:{'passed':True},'record':{'cases':[row]},'out':scratch,
       'Path':Path,'f':f,'c':c,'ROOT':ROOT,'io':io,'jobs':[job],'sources':{'completed-case':{}},'sx':sx,
       'p':SimpleNamespace(Rejected=p.Rejected,routes=lambda _:[],tree_hash=lambda _: {},audit_route_dimensions=lambda *a:row['route_dimensions'],engine_argv=lambda *a:engineargv,transplant_routes=transplant,transplant_fill=lambda rebuilt,refill:rebuilt),
       'geometry':lambda *a:row['geometry'],'observed':lambda *a:native,
       'n':SimpleNamespace(audit_native=n.audit_native,audit_dsn=lambda *a,**k:row['dsn_audit'])}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    def reset():
        for step in steps:(jobdir/(step['name']+'-process.json')).write_text(json.dumps(step))
        (jobdir/'native.dsn').write_bytes((jobdir/'task.dsn').read_bytes())
        candidate.write_text('(kicad_pcb)\n');row['protected_import']={'preserved':True}
    cases=[]
    mutations=[('engine_argv','engine','argv',['unexpected']),('export_argv','export','argv',['unexpected']),('import_cwd','import','cwd','/unexpected'),('final_map_status','final-netclasses','status','crash'),('raw_dsn_drift',None,None,None),('candidate_reconstruction_drift',None,None,None),('protected_import_receipt_drift',None,None,None)]
    with mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess')),mock.patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess')):
        reset();namespace['bound']();cases.append({'case':'controlling_positive','passed':True})
        for name,stage,key,value in mutations:
            reset()
            if stage:
                path=jobdir/(stage+'-process.json');data=json.loads(path.read_text());data[key]=value;path.write_text(json.dumps(data))
            elif name=='raw_dsn_drift':(jobdir/'native.dsn').write_bytes(b'(pcb changed)\n')
            elif name=='candidate_reconstruction_drift':candidate.write_text('(kicad_pcb (review_tamper))\n')
            else:row['protected_import']={'preserved':False}
            try:namespace['bound']()
            except p.Rejected as exc:cases.append({'case':name,'rejected':True,'reason':str(exc)})
            else:cases.append({'case':name,'rejected':False})
        reset();namespace['bound']()
    result={'scope':'exact AST final bound closure, synthetic DRC/geometry/DSN state, real process guards and raw file equality',
       'source_sha256':hashlib.sha256(raw).hexdigest(),'source_unchanged':source.read_bytes()==raw,
       'controls':cases,'all_controls_passed':all(x.get('passed',x.get('rejected',False)) for x in cases),
       'native_executed':False,'routing_qualification':False}
    (OWN/'bound-after-fix.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
