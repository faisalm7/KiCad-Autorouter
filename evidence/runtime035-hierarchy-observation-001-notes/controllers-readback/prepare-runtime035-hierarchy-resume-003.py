"""Correct a pre-execution singleton tuple defect; no Native work or reruns."""
from pathlib import Path
import ast, hashlib, json, sys
R=Path(__file__).resolve().parents[1];rt=R/'.runs/runtime-directory-035/runtime'
sys.path.insert(0,str(rt));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f
old=R/'.runs/qualify-runtime035-hierarchy-observation-002.py'
assert p.sha(old)=='59c3d78f4df341fc723230a46d9349b98d4f79a77b8f3470c71775821aa9bd30'
source=old.read_text()
needle="],job.out/'native-pcb.json')):"
assert source.count(needle)==1
source=source.replace(needle,"],job.out/'native-pcb.json'),):")
source=source.replace('qualify-runtime035-hierarchy-observation-002.py','qualify-runtime035-hierarchy-observation-003.py').replace('runtime035-hierarchy-observability-resume-v2','runtime035-hierarchy-observability-resume-v3').replace('native7-comparison-control-runtime035-hierarchy-002','native7-comparison-control-runtime035-hierarchy-003')
tree=ast.parse(source)
loops=[node for node in ast.walk(tree) if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple) and [a.id for a in node.target.elts if isinstance(a,ast.Name)]==['name','argv','output']]
assert len(loops)==1 and isinstance(loops[0].iter,ast.Tuple) and len(loops[0].iter.elts)==1
assert isinstance(loops[0].iter.elts[0],ast.Tuple) and len(loops[0].iter.elts[0].elts)==3
old_plan=R/'.runs/runtime035-hierarchy-observation-002/protocol.json'
assert p.sha(old_plan)=='7aa0ba6c90ac82542e160217370985e60f78bb36d097fc63d63a7f847a611a2f'
plan=f.read_json(old_plan)
assert not Path(plan['output']).exists() and not (old_plan.parent/'enclosure').exists()
for name,pin in plan['prerequisite_files'].items():assert p.sha(Path(name))==pin
assert p.tool_manifest()==plan['tools'] and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
prior=plan['completed_export001'];assert p.sha(Path(prior['root'])/'result.json')==prior['result_sha256']
q=R/'.runs/qualify-runtime035-hierarchy-observation-003.py';child=rt/'.runs'/q.name
base=R/'.runs/runtime035-hierarchy-observation-003';out=rt/'.runs/native7-comparison-control-runtime035-hierarchy-003'
assert not any(path.exists() for path in (q,child,base,out))
q.write_text(source);child.write_bytes(q.read_bytes());base.mkdir()
plan.update(kind='runtime035-hierarchy-observability-resume-v3',controller=str(child),controller_sha256=p.sha(q),output=str(out),
 preparation=dict(preparer_sha256=p.sha(Path(__file__)),reused_prior_protocol_sha256=p.sha(old_plan),Native_executed=False,
 pre_execution_defect='002 singleton-loop tuple lost its outer tuple after the completed export was removed. Lead caught it before execution;002 remains frozen and unexecuted.003 changes only loop shape and run identity. No prior export repeated.'))
p.save_json(base/'protocol.json',plan)
print(json.dumps(dict(protocol=str(base/'protocol.json'),protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(q),Native_executed=False)))
