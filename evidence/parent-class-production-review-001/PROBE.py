"""Narrow source-only policy branch seam; not a complete routing receipt."""
import ast,copy,hashlib,json,subprocess,sys
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,netclass as n,sexpr as sx,config as c,floor_route as f

def main():
    source=ROOT/'autorouter/pipeline.py';raw=source.read_bytes()
    (OWN/'pipeline-before-fix.py').write_bytes(raw)
    module=ast.parse(raw);function=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='_check_result_uncached')
    branch=next(x for x in function.body if isinstance(x,ast.If) and ast.unparse(x.test)=='netclass_policy(candidate) is not None')
    actual=ROOT/'.runs/netclass-parent-transport-001/controls/whole_unprotected'
    candidate=actual/'candidate/fixture.kicad_pcb';job=actual/'job';original=sx.read(actual/'original/fixture.kicad_pcb')
    native=f.read_json(job/'final-netclasses.json')
    audit=p.audit_candidate_netclasses(candidate,[],native);audit['native_map_file_sha256']=p.sha(job/'final-netclasses.json')
    journal={'argv':[str(c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(job/'final-netclasses.json')],
             'cwd':str(job),'name':'final-netclasses','exit_code':0,'status':'success','cleanup_complete':True}
    def evidence(name):
        if name=='final-netclasses.json':return copy.deepcopy(native)
        if name=='final-netclass-audit.json':return copy.deepcopy(audit)
        if name=='final-netclasses-process.json':return copy.deepcopy(journal)
        raise p.Rejected('missing synthetic parent export evidence: '+name)
    def run(baseline):
        data={'scope':'whole_board_unlocked_routing','baseline':baseline,'steps':[copy.deepcopy(journal)]}
        namespace=dict(vars(p));namespace.update(candidate=candidate,path=job/'result.json',data=data,original=original,protected=[],evidence=evidence)
        try:exec(compile(ast.Module(body=[branch],type_ignores=[]),str(source),'exec'),namespace)
        except Exception as exc:return {'baseline':baseline,'rejected':True,'reason':type(exc).__name__+': '+str(exc)}
        return {'baseline':baseline,'rejected':False,'missing_declarations':['netclass_policy','netclass_export_audit','netclass_task_audit','task_sha256']}
    with mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess')),mock.patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess')):
        controls=[run('B1'),run('C-prototype')]
    result={'scope':'exact current parent readback branch with an actual retained candidate/class observation and synthetic journal; NOT a full accepted receipt',
            'pipeline_sha256':hashlib.sha256(raw).hexdigest(),'source_unchanged':source.read_bytes()==raw,
            'source_parent_mode':p.netclass_policy(candidate)['mode'],'controls':controls,
            'native_executed':False,'complete_acceptance_claim':False}
    (OWN/'baseline-gap.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
