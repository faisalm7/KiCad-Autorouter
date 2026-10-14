"""Exact controller bound-closure seam; all native/semantic work is synthetic.

Shows a stale process journal passing the final closure before a new witness.
It does not simulate or qualify KiCad geometry or an actual native process.
"""
import ast, copy, hashlib, json, subprocess, sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
ROOT=Path(__file__).resolve().parents[2];OWN=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from autorouter import floor_route as f, netclass as n, pipeline as p
from test_netclass_parent_policy import example
from experiments.original_project_native_v1.driver import completed_evidence

def main():
    source=ROOT/'experiments/netclass_parent_transport_v1/driver.py'
    raw=source.read_bytes();(OWN/'transport-driver-before-fix.py').write_bytes(raw)
    tree=ast.parse(raw);experiment=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='experiment')
    node=next(x for x in experiment.body if isinstance(x,ast.FunctionDef) and x.name=='bound')
    scratch=OWN/'bound-seam';scratch.mkdir(exist_ok=False)
    case=scratch/'completed-case';jobdir=case/'job';jobdir.mkdir(parents=True)
    candidate=case/'candidate/fixture.kicad_pcb';candidate.parent.mkdir();candidate.write_text('(kicad_pcb)\n')
    original=case/'original';original.mkdir();(original/candidate.name).write_bytes(candidate.read_bytes())
    _,native,project=example();(original/'fixture.kicad_pro').write_text(json.dumps(project))
    argv=['synthetic-engine','task.dsn','routes.ses']
    process={'name':'engine','argv':argv,'cwd':str(jobdir),'exit_code':0,'status':'success','cleanup_complete':True}
    processfile=jobdir/'engine-process.json';processfile.write_text(json.dumps(process))
    data={'steps':[copy.deepcopy(process)]};job=SimpleNamespace(out=jobdir,steps=data['steps'])
    positive=f.process_check(jobdir,data,'engine',argv)
    row={'case':'completed-case','final_candidate':str(candidate),'geometry':{'passed':True},'route_dimensions':{'passed':True},'dsn_audit':{'passed':True}}
    namespace={'checks':[(job,'final-drc',candidate,{},False,{'passed':True})],
       'native_binding':lambda *a,**k:{'passed':True},'record':{'cases':[row]},'out':scratch,
       'Path':Path,'f':f,'sources':{'completed-case':{}},
       'sx':SimpleNamespace(read=lambda _:['kicad_pcb']),
       'p':SimpleNamespace(Rejected=p.Rejected,routes=lambda _:[],tree_hash=lambda _: {},audit_route_dimensions=lambda *a:row['route_dimensions']),
       'geometry':lambda *a:row['geometry'],'observed':lambda *a:native,
       'n':SimpleNamespace(audit_native=n.audit_native,audit_dsn=lambda *a,**k:row['dsn_audit'])}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    with mock.patch.object(subprocess,'run',side_effect=AssertionError('No subprocess')),mock.patch.object(subprocess,'Popen',side_effect=AssertionError('No subprocess')):
        namespace['bound']()  # controlling positive
        mutated={**process,'argv':['unexpected-argv']};processfile.write_text(json.dumps(mutated))
        try:f.process_check(jobdir,data,'engine',argv)
        except p.Rejected as exc:direct_rejection=str(exc)
        else:raise AssertionError('mutation did not break the real process guard')
        namespace['bound']()  # exact final closure accepts this stale journal
        witness=completed_evidence(scratch)
    result={'scope':'exact AST bound closure with synthetic DRC/geometry/DSN helpers; real parent and process guards',
       'source_sha256':hashlib.sha256(raw).hexdigest(),'source_unchanged':source.read_bytes()==raw,
       'initial_process_control_passed':positive==process,'mutated_process_rejected_by_shared_guard':direct_rejection,
       'final_bound_accepted_mutated_journal':True,
       'new_completed_witness_rebound_mutated_journal':witness['files']['completed-case/job/engine-process.json']==p.sha(processfile),
       'native_executed':False,'routing_accepted_claim':False}
    (OWN/'bound-gap.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':main()
