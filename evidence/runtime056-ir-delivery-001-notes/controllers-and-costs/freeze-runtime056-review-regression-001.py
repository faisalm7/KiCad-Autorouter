"""Freeze one fresh installed Improve repair regression; never rerun cohort arms."""
from pathlib import Path
import copy,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,provenance as pv
from scripts.freeze_current_comparison import query_runtime
HEAD='a03b5e8b6ae523d9f099cf211815900053629fe3'
runtime=ROOT/'.runs/runtime-directory-056/runtime';base=ROOT/'.runs/runtime056-ir-review-regression-001'
assert pv.git_head(ROOT)==HEAD and not base.exists() and shutil.disk_usage(ROOT).free>4*1024**3
full=f.read_json(ROOT/'.runs/full-integration-206/execution.json');assert full['passed'] and full['sources_unchanged'] and full['process']['cleanup_complete']
prepared=f.read_json(ROOT/'.runs/runtime-directory-056/preparation.json');assert prepared['prepared'] and prepared['source_head']==HEAD
manifest=runtime/'runtime-distribution.json';assert p.sha(manifest)==prepared['manifest_sha256']
base.mkdir(mode=0o700);query,pins=query_runtime(runtime,base);tools=query['tools']
assert tools['source_provenance']['git_head']==HEAD and tools['source_provenance']['manifest_sha256']==p.sha(manifest)
old=ROOT/'.runs/runtime050-default-improve-development-001/ir-obstacle/Cimprove/protocol.json'
children=ROOT/'.runs/runtime050-default-improve-development-001/frozen-children.json'
assert p.sha(children)=='017db06432d41123d9103fe32491e6cf3e1894e360791627339660f155cc6c1a'
assert p.sha(old)==f.read_json(children)['protocols']['ir-obstacle']['Cimprove']['sha256']
plan=copy.deepcopy(f.read_json(old));assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
child=runtime/'.runs/qualify-current-method-002.py';assert not child.exists();shutil.copyfile(ROOT/'scripts/qualify_current_method.py',child)
outputs={name:str(runtime/'.runs'/(( 'native7-comparison-' if name in ('B0','B1','B2single_tuned','B2_portfolio') else 'native7-method-')+'runtime056-ir-review-regression-001-'+name)) for name in plan['population']}
plan.update(runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=HEAD,tools=tools,controller=str(child),controller_sha256=p.sha(child),controller_args=['--runtime',str(runtime)],outputs=outputs,output=outputs['Cimprove'],population_protocol_path=None,population_protocol_sha256=None,scope='Fresh single exposed IR Improve delivery regression after explicit ordinary via_high admission; Improve retains default scoring and unchanged single-complete-read lifecycle. Same420/450/600/export120 settings and unchanged source/constraints. Only Cimprove executes; the other required authority namespaces are reserved but not run. Not a six-arm comparison, cohort repair, holdout or routing-superiority claim.',qualification_context='Current default-score Improve regression after ordinary scoring customization; outside unchanged frozen050 cohort.')
prereqs=[manifest,ROOT/'scripts/qualify_current_method.py',child,ROOT/'scripts/enclose_current_comparison.py',ROOT/'scripts/qualify_installed_workflow.py',ROOT/'.runs/full-integration-206/execution.json',ROOT/'evidence/review-syntax-repair-001.json',ROOT/'evidence/runtime051-review-regression-001.json',ROOT/'evidence/runtime052-review-regression-001.json',ROOT/'evidence/immutable-projection-repair-001.json',ROOT/'evidence/runtime053-review-regression-001.json',ROOT/'evidence/native7-context-reconstruction-repair-001.json',ROOT/'evidence/runtime054-review-regression-001.json',ROOT/'evidence/review-single-full-repair-001.json',ROOT/'.runs/runtime042-unrelated-development-sources-001.json']
plan['prerequisite_sha256']={str(q):p.sha(q) for q in prereqs}
plan['enclosure_sha256']=p.sha(ROOT/'scripts/enclose_current_comparison.py');plan['qualifier_sha256']=p.sha(ROOT/'scripts/qualify_installed_workflow.py')
p.save_json(base/'protocol.json',plan)
p.save_json(base/'frozen.json',dict(schema=1,kind='runtime056-single-Improve-delivery-repair-regression-v1',source_head=HEAD,runtime=str(runtime),manifest_sha256=p.sha(manifest),original_cohort_protocol_sha256=p.sha(old),protocol_sha256=p.sha(base/'protocol.json'),controller_sha256=p.sha(Path(__file__)),source_hashes=plan['source_hashes'],executed=False,only_arm='Cimprove',not_a_comparison=True,project_complete=False))
print(json.dumps(dict(protocol=str(base/'protocol.json'),sha256=p.sha(base/'protocol.json'),manifest_sha256=p.sha(manifest))))
