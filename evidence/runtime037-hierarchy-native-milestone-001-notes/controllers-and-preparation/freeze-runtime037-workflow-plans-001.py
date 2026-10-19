"""Freeze existing shared six-stage qualifiers only after Native identity controls."""
from pathlib import Path
import sys,copy
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-037/runtime';sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,preferences as pref
assert c.ROOT==runtime and c.NATIVE_VERSION=='10.0.7'
controls=ROOT/'.runs/hierarchy-native-controls-002';enclosure=f.read_json(controls/'enclosure/result.json');assert enclosure['passed'] is True
plan=f.read_json(controls/'protocol.json');data=f.read_json(Path(plan['output'])/'result.json');assert data['control_passed'] is True and len(data['cases'])==5
positive=data['cases'][0];assert positive['case']=='positive' and positive['Native']['opens']==6 and positive['Native']['blocking']==0
manifest=runtime/'runtime-distribution.json';pin=p.sha(manifest);assert pin==plan['runtime_manifest_sha256'] and p.tool_manifest()==plan['tools']
rows=[('hierarchy-whole2Cu',Path(plan['source']),pref.validate(dict(pref.DEFAULTS,scope='whole_board_unlocked_routing',seconds=90)),[0,0,positive['Native']['warnings'],positive['Native']['exclusions']],0,{'controls_protocol_sha256':p.sha(controls/'protocol.json'),'positive_case_result_sha256':p.sha(Path(plan['output'])/'result.json'),'qualification':'Future completion requireszeroopens/zeroblock and exactly originalsourcewarnings/exclusions; expected6sourceopens are unrouted, notinvaliddesign.'})]
for label,old in [('whole4Cu','runtime035-ordinary-whole4Cu-002'),('partial2Cu','runtime035-ordinary-partial2Cu-001')]:
 prior_path=ROOT/'.runs'/old/'protocol.json';previous=f.read_json(prior_path)
 source=Path(previous['source']);assert p.tree_hash(source.parent)==previous['source_hashes']
 rows.append((label,source,previous['settings'],previous['expected_counts'],previous['expected_protected_count'],{'unchanged_prior_source_protocol':str(prior_path),'sha256':p.sha(prior_path),'scope':'Fresh final-source ordinary regression, not a repetition merely afterrestart.'}))
for label,source,settings,expected,protected,basis in rows:
 base=ROOT/'.runs'/('runtime037-ordinary-'+label+'-001');assert not base.exists();base.mkdir()
 p.save_json(base/'settings.json',settings)
 value=dict(schema=1,kind='runtime037-six-stage-ordinary-CLI',runtime=str(runtime),runtime_manifest_sha256=pin,source_head=plan['source_head'],source=str(source),source_hashes=p.tree_hash(source.parent),output=str(runtime/'.runs'/('ordinary-'+label+'-001')),settings=settings,settings_sha256=p.sha(base/'settings.json'),expected_counts=expected,expected_protected_count=protected,budgets=dict(route=settings['seconds'],export=settings['seconds']),driver_sha256=p.sha(ROOT/'scripts/qualify_runtime_workflow.py'),enclosure_sha256=p.sha(ROOT/'.runs/enclose-runtime030-ordinary-workflow-001.py'),basis=basis,scope='Actual installed037 Request/Workflow/CliJob/CLI preview/Route/review/acceptintent/export/verify and checkedinspect path; own final Native/fullSCH/original proof required, allwarnings retained. SOFTWAREqualification, no actualGUI/human/broadfamily/Windows/comparisonwin claim. Unchanged standard/B1default,240wholewall/fullCPU/255outerhardcap; route/exportallocation preserved exactly in declaredbudgets (hierarchy90,partial90,whole120).')
 p.save_json(base/'protocol.json',value)
 print({'label':label,'protocol':str(base/'protocol.json'),'sha256':p.sha(base/'protocol.json'),'expected_counts':expected,'protected':protected})
