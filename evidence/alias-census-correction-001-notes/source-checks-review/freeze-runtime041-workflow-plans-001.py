"""Freeze fresh ordinary/floor protocols after actual installed041/full186 prerequisites.
No Native/engine execution here; all sources and original rules remain unchanged.
"""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-041/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,preferences as pref
HEAD='__SOURCE_HEAD__'
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7'
assert p.sha(ROOT/'scripts/qualify_runtime_workflow.py')=='0b1a3bc61e576d6475a4c922a7727b7831ccf28f3e0a9d2d80b557e3c1964034'
assert p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py')=='69d87dee41f94fe9e479e505093914325ed653cbb0cd58c9545272afefc1d59c'
install=f.read_json(ROOT/'.runs/install-distribution-native-014/execution.json');assert install['passed'] is True and install['source_unchanged'] is True
built=f.read_json(ROOT/'.runs/runtime-directory-041/result.json');assert built['passed'] is True and built['git_head']==HEAD
manifest=runtime/'runtime-distribution.json';pin=p.sha(manifest);tools=p.tool_manifest();assert tools['git_head']==HEAD
assert tools['source_provenance']['manifest_sha256']==pin and tools['source_provenance']['native_version']=='10.0.7'
fullbase=ROOT/'.runs/full-integration-186';full=f.read_json(fullbase/'execution.json');fullplan=f.read_json(fullbase/'protocol.json')
assert full['passed'] is True and full['sources_unchanged'] is True and fullplan['tools']['git_head']==HEAD
assert full['process']['status']=='success' and full['process']['exit_code']==0 and full['process']['cleanup_complete'] is True and full['process']['log_truncated'] is False
for name,digest in fullplan['source_sha256'].items():assert p.sha(ROOT/name)==digest
installbase=ROOT/'.runs/install-distribution-native-014';installplan=f.read_json(installbase/'protocol.json')
assert installplan['source_head']==HEAD and installplan['output']==str(runtime.parent)
assert installplan['full_integration186']['execution_sha256']==p.sha(fullbase/'execution.json') and installplan['full_integration186']['protocol_sha256']==p.sha(fullbase/'protocol.json')
assert install['protocol_sha256']==p.sha(installbase/'protocol.json') and install['child_receipt']==str(runtime.parent/'result.json') and install['child_receipt_sha256']==p.sha(runtime.parent/'result.json')
assert install['process']['status']=='success' and install['process']['exit_code']==0 and install['process']['cleanup_complete'] is True and install['process']['log_truncated'] is False
rows=[]
for label in ('hierarchy-whole2Cu','whole4Cu','partial2Cu'):
 prior_case=label+('-002' if label=='hierarchy-whole2Cu' else '-001')
 prior_path=ROOT/'.runs'/('runtime039-ordinary-'+prior_case)/'protocol.json';previous=f.read_json(prior_path)
 source=Path(previous['source']);assert p.tree_hash(source.parent)==previous['source_hashes']
 rows.append((label,source,previous['settings'],previous['expected_counts'],previous['expected_protected_count'],{'unchanged_prior_source_protocol':str(prior_path),'sha256':p.sha(prior_path),'scope':'Required fresh changed-source integration regression; no new family or routing gain claim.'}))
construction=ROOT/'.runs/default-floor-owned-controls-001/construction.json';control=f.read_json(construction)
assert control['generator_sha256']==p.sha(ROOT/'.runs/default-floor-owned-fixture-001.py')
for case in control['cases']:
 source=Path(case['source']);assert p.tree_hash(source.parent)==case['source_hashes']
 rows.append(('floor-'+case['label'],source,pref.validate(dict(pref.DEFAULTS,scope='whole_board_unlocked_routing',seconds=90)),None,1,{'construction':str(construction),'sha256':p.sha(construction),'specific_failure':'Raw sole-Default DSN dimensions can be below original hard floors; complete real forced-via delivery must preserve protected KEEP and original rules.','mechanism':'Source-bound same-load Default/floor observations derive lawful planning targets without modifying original class, project or protected copper.','bounded_comparison':'Two predeclared owned 2Cu/4Cu controls, one 90route/90export pass each, no tuning. Fresh Native/original/source/protection proof mandatory; not benchmark families.','decision':'Qualify only on real completion and target-preservation; revise/refuse on mismatch, retain all failures and warnings.'}))
alias_path=ROOT/'.runs/native7-source-all-alias-controls-001/fixture-preparation.json'
assert p.sha(alias_path)=='5ce022a7666c9140c07cba188def2016da588e63d8903a4e1cfa1a03bb5f60b1'
alias=f.read_json(alias_path);source=Path(alias['source'])
assert p.tree_hash(source.parent)==alias['source_hashes'] and p.tree_hash(Path(alias['original_source']))==alias['original_source_hashes']
alias_settings=pref.validate(dict(pref.DEFAULTS,scope='partial_completion',seconds=90))
assert alias_settings==alias['settings'] and alias_settings==dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
rows.append(('alias2Cu',source,alias_settings,[0,0,0,0],4,{'fixture_preparation':str(alias_path),'sha256':p.sha(alias_path),'scope':'Owned signal/display alias plus padless-census combination control only; expected Native display rows must bind to the same-load source-all map and captured helper provenance across all four unchanged observation phases: upper_trace/lower_trace source atoms, physical IDs/names/types/order and all four original routes including both sides/through via unchanged. Actual fullSCH/final Native/original/protected/same-load source/DSN identity proof required; no layer-type/mask/class widening, family or algorithmic claim.'}))
for label,source,settings,expected,protected,basis in rows:
 base=ROOT/'.runs'/('runtime041-ordinary-'+label+'-001');assert not base.exists();base.mkdir()
 p.save_json(base/'settings.json',settings)
 value=dict(schema=1,kind='runtime041-six-stage-ordinary-CLI',runtime=str(runtime),runtime_manifest_sha256=pin,source_head=HEAD,source=str(source),source_hashes=p.tree_hash(source.parent),output=str(runtime/'.runs'/('ordinary-'+label+'-001')),settings=settings,settings_sha256=p.sha(base/'settings.json'),expected_counts=expected,expected_protected_count=protected,budgets=dict(route=settings['seconds'],export=settings['seconds']),driver_sha256=p.sha(ROOT/'scripts/qualify_runtime_workflow.py'),enclosure_sha256=p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-002.py'),basis=basis,scope='Actual installed041 production six-stage CLI after the narrow padless expected-display correction with same-load Native identity/provenance; own fullSCH/final Native/original/protected proof remains mandatory. Source/DSN names, types, masks and classes are not widened. Unchanged standard/B1 default; 240wholewall/fullCPU and255outer; no GUI/comparative/breadth/human claim.')
 if expected is None:value.update(warning_policy='retain_all_native_findings',expected_exclusions=0)
 p.save_json(base/'protocol.json',value)
 print({'label':label,'protocol':str(base/'protocol.json'),'sha256':p.sha(base/'protocol.json'),'expected_counts':expected,'protected':protected})
