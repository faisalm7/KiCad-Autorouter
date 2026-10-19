"""Freeze fresh ordinary/floor protocols after actual installed038 prerequisite.
No Native/engine execution here; all sources and original rules remain unchanged.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-038/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,preferences as pref
HEAD='3a71a124521ab1c051a9d772849d7913125518f0'
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7'
install=f.read_json(ROOT/'.runs/install-distribution-native-011/execution.json');assert install['passed'] is True and install['source_unchanged'] is True
built=f.read_json(ROOT/'.runs/runtime-directory-038/result.json');assert built['passed'] is True and built['git_head']==HEAD
manifest=runtime/'runtime-distribution.json';pin=p.sha(manifest);assert p.tool_manifest()['git_head']==HEAD
rows=[]
for label in ('hierarchy-whole2Cu','whole4Cu','partial2Cu'):
 prior_path=ROOT/'.runs'/('runtime037-ordinary-'+label+'-001')/'protocol.json';previous=f.read_json(prior_path)
 source=Path(previous['source']);assert p.tree_hash(source.parent)==previous['source_hashes']
 rows.append((label,source,previous['settings'],previous['expected_counts'],previous['expected_protected_count'],{'unchanged_prior_source_protocol':str(prior_path),'sha256':p.sha(prior_path),'scope':'Required fresh changed-source integration regression; no new family or routing gain claim.'}))
construction=ROOT/'.runs/default-floor-owned-controls-001/construction.json';control=f.read_json(construction)
assert control['generator_sha256']==p.sha(ROOT/'.runs/default-floor-owned-fixture-001.py')
for case in control['cases']:
 source=Path(case['source']);assert p.tree_hash(source.parent)==case['source_hashes']
 rows.append(('floor-'+case['label'],source,pref.validate(dict(pref.DEFAULTS,scope='whole_board_unlocked_routing',seconds=90)),None,1,{'construction':str(construction),'sha256':p.sha(construction),'specific_failure':'Raw sole-Default DSN dimensions can be below original hard floors; complete real forced-via delivery must preserve protected KEEP and original rules.','mechanism':'Source-bound same-load Default/floor observations derive lawful planning targets without modifying original class, project or protected copper.','bounded_comparison':'Two predeclared owned 2Cu/4Cu controls, one 90route/90export pass each, no tuning. Fresh Native/original/source/protection proof mandatory; not benchmark families.','decision':'Qualify only on real completion and target-preservation; revise/refuse on mismatch, retain all failures and warnings.'}))
for label,source,settings,expected,protected,basis in rows:
 base=ROOT/'.runs'/('runtime038-ordinary-'+label+'-001');assert not base.exists();base.mkdir()
 p.save_json(base/'settings.json',settings)
 value=dict(schema=1,kind='runtime038-six-stage-ordinary-CLI',runtime=str(runtime),runtime_manifest_sha256=pin,source_head=HEAD,source=str(source),source_hashes=p.tree_hash(source.parent),output=str(runtime/'.runs'/('ordinary-'+label+'-001')),settings=settings,settings_sha256=p.sha(base/'settings.json'),expected_counts=expected,expected_protected_count=protected,budgets=dict(route=settings['seconds'],export=settings['seconds']),driver_sha256=p.sha(ROOT/'scripts/qualify_runtime_workflow.py'),enclosure_sha256=p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py'),basis=basis,scope='Actual installed038 production six-stage CLI with own fullSCH/final Native/original/protected proof. Unchanged standard/B1 default; 240wholewall/fullCPU and255outer; no GUI/comparative/breadth/human claim.')
 if expected is None:value.update(warning_policy='retain_all_native_findings',expected_exclusions=0)
 p.save_json(base/'protocol.json',value)
 print({'label':label,'protocol':str(base/'protocol.json'),'sha256':p.sha(base/'protocol.json'),'expected_counts':expected,'protected':protected})
