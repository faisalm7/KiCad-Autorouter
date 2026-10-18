"""Freeze the one bounded regression of demonstrated duplicate verification cost."""
from pathlib import Path
import copy, hashlib, json, os, shutil, subprocess, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, provenance as pv
old_path=ROOT/'.runs/runtime032-v2-portfolio-negative-001/protocol.json'
assert p.sha(old_path)=='c94cbf65c52edd55a0d78c9a09d3e61b14e7a00239322899946df7e7ecc94b76'
old=f.read_json(old_path);old_result=f.read_json(Path(old['output'])/'result.json')
old_summary=f.read_json(Path(old['portfolio_output'])/'portfolio-summary.json')
assert not old_result['controls_passed'] and old_summary['status']=='budget_exceeded'
assert old_summary['selected'] is None and old_summary['total_cpu_seconds']==420.9365169999999
assert f.read_json(ROOT/'.runs/runtime032-ordinary-partial2Cu-001/execution.json')['controls_passed']
assert f.read_json(ROOT/'.runs/runtime032-ordinary-whole4Cu-001/execution.json')['controls_passed']
pins={'scripts/experiment_portfolio.py':'a748da6492963fafd5418cddaac39bbf0313830b240ca7e2a120145c4aaa1e17','scripts/qualify_comparison_portfolio.py':'c99d47fc0eec00e77b34539b4601a9dbc9dda03fdddd2e1d8c766664f284de90','scripts/experiment_quality.py':old['administration_files_sha256']['scripts/experiment_quality.py']}
head=pv.git_head(ROOT)
assert head!=old['administration_head']
for name,digest in pins.items():
 assert p.sha(ROOT/name)==digest
 assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)).hexdigest()==digest
assert p.sha(Path(old['runtime'])/pv.MANIFEST)==old['runtime_manifest_sha256']
assert p.tree_hash(Path(old['source']).parent)==old['source_hashes']
assert p.sha(ROOT/'.runs/enclose-native7-independent-control-003.py')==old['enclosure_sha256']
assert shutil.disk_usage(ROOT).free>2*1024**3
plan=copy.deepcopy(old)
plan['administration_head']=head;plan['administration_files_sha256']=pins
plan['controller_sha256']=pins['scripts/qualify_comparison_portfolio.py']
plan['output']=old['output'].replace('portfolio-negative-001','portfolio-negative-002')
plan['portfolio_output']=old['portfolio_output'].replace('portfolio-negative-001','portfolio-negative-002')
plan['material_roots']=[name.replace('portfolio-negative-001','portfolio-negative-002') for name in old['material_roots']]
assert not any(os.path.lexists(name) for name in [plan['output'],*plan['material_roots']])
plan['prior_failed_protocol_sha256']=p.sha(old_path)
plan['scope']='Fresh bounded regression of demonstrated API duplicate negative readback cost and truthful failure diagnostic. Same exact Interf25files/runtime032b0/tools/threefixedscores/420route450method600whole120export/balanced30+15reserves as failed001; only committed external administration and fresh002names differ. Preserve all Native rejection/validation/source/rule/material/PRL/cancel/budget guards and failed001. All variants must finish; no fairmatrix, broad gain, GUI or production admission claim. Complete external exit counts all method work; software review/authoring/preparation/curation are additional.'
for key in old:
 if key not in ('administration_head','administration_files_sha256','controller_sha256','output','portfolio_output','material_roots','scope'):assert old[key]==plan[key],key
folder=ROOT/'.runs/runtime032-v2-portfolio-negative-002';folder.mkdir()
p.save_json(folder/'protocol.json',plan)
print(json.dumps(dict(protocol=str(folder/'protocol.json'),sha256=p.sha(folder/'protocol.json'),administration_head=head,free_bytes=shutil.disk_usage(ROOT).free)))
