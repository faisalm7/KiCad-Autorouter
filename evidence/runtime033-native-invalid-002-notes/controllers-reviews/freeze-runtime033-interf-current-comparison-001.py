"""Freeze all six development arms before any member is executed."""
from pathlib import Path
import copy,hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
runtime=ROOT/'.runs/runtime-directory-033/runtime';manifest=runtime/'runtime-distribution.json'
assert p.sha(manifest)=='115c881aa04a34bf642c57d5af312fe692d1aff013bed095caa3856a614f3987'
query=ROOT/'.runs/runtime033-method-material-002/tools-defaults.json';material=f.read_json(query);tools=material['tools'];defaults=dict(material['defaults'],seconds=420)
assert tools['source_provenance']['manifest_sha256']==p.sha(manifest) and tools['git_head']=='a476a0a0647bc51889d291e3e6e2598f4ec24370'
source_record=f.read_json(ROOT/'.runs/runtime032-v2-portfolio-negative-002/protocol.json')
source=Path(source_record['source']);hashes=source_record['source_hashes'];assert p.tree_hash(source.parent)==hashes and len(hashes)==25
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
public=ROOT/'scripts/qualify_current_method.py';assert p.sha(public)=='2610e8175b0fcbe256b9e6c570cdc878019f3f357fe0f51296d3464b0f2bf837'
assert hashlib.sha256(subprocess.check_output(['git','show',head+':scripts/qualify_current_method.py'],cwd=ROOT)).hexdigest()==p.sha(public)
admin_names=('scripts/qualify_comparison_portfolio.py','scripts/experiment_portfolio.py','scripts/experiment_quality.py')
admin={name:p.sha(ROOT/name) for name in admin_names}
for name,digest in admin.items():assert hashlib.sha256(subprocess.check_output(['git','show',head+':'+name],cwd=ROOT)).hexdigest()==digest
prereq_paths=[ROOT/'.runs/full-integration-176/execution.json',ROOT/'.runs/install-distribution-native-006/execution.json',ROOT/'.runs/runtime033-ordinary-whole4Cu-001/execution.json',ROOT/'.runs/runtime033-ordinary-partial2Cu-001/execution.json',ROOT/'.runs/runtime033-ordinary-native-invalid-001/enclosure/result.json',ROOT/'.runs/runtime032-v2-portfolio-negative-002/enclosure/result.json',ROOT/'.runs/current-method-controller-review-001.json',query]
for path in prereq_paths:assert path.is_file(),path
assert f.read_json(prereq_paths[0])['passed'] and f.read_json(prereq_paths[1])['passed']
assert f.read_json(prereq_paths[2])['controls_passed'] and f.read_json(prereq_paths[3])['controls_passed']
assert f.read_json(prereq_paths[4])['passed'] and f.read_json(prereq_paths[5])['passed']
assert shutil.disk_usage(ROOT).free>2*1024**3
population=['B0','B1','B2single_tuned','B2_portfolio','Cdefault','Cthermal']
outputs={name:str(runtime/'.runs'/((('native7-comparison-' if name.startswith('B') else 'native7-method-')+'current-interf-'+name+'-001'))) for name in population}
assert len({Path(value) for value in outputs.values()})==6 and not any(os.path.lexists(value) for value in outputs.values())
portfolio=Path(outputs['B2_portfolio']+'-portfolio');extra=[portfolio,*[portfolio.with_name(portfolio.name+'-'+f'{n:02d}-'+variant) for n,variant in enumerate(('via_default','via_low','via_high'),1)]]
assert not any(os.path.lexists(value) for value in extra)
child=runtime/'.runs/qualify-current-method-001.py';assert not child.exists();child.parent.mkdir(exist_ok=True);shutil.copyfile(public,child);assert p.sha(child)==p.sha(public)
rights=dict(family='kicad-interf-exposed',license='CC-BY-SA-4.0',provenance='Exact unchanged25file official KiCad Interf source from data/sources.json and prior023v4 inventory, including original licenses and Larry Ewing/The GIMP Tux attribution. Exposed development family, not holdout. Source opens/repairable thermal findings are separate from structural net/pad conflicts. No private source or reference route used for policy selection.')
base=ROOT/'.runs/runtime033-interf-current-comparison-001';base.mkdir()
parent=dict(schema=1,kind='frozen-six-arm-current-installed-exposed-development-v1',population=population,planned_order=['Cdefault','B0','B1','B2single_tuned','B2_portfolio','Cthermal'],outputs=outputs,runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=tools['git_head'],administration_head=head,source=str(source),source_hashes=hashes,source_rights=rights,default_settings=defaults,limits=dict(routing_seconds=420,method_wall_cpu_cap_seconds=450,delivery_wall_cpu_cap_seconds=600,export_validation_seconds=120),policy='Shipped corrected-standard/B1 default; optional fixed native thermal bridge separately. No best-policy per-board selection. Finite three-score B2 uses fixed valid(vias,length,index)rank; single tuned is separate. No changes during run.',eligibility='One already exposed licensed family with complete25file source. New source families/untouched confirmation and30-50 representative development remain unmet; no broad generalization. Original constraints/scope identical; all warnings/exclusions/failures retained.',stock_caveat='Stock engine/native DSN with shared fidelity/validation safeguards, not untouched official plugin. API comparison delivery differs from actual CLI default/recovery delivery, and every actual step/startup is charged.',negative_contract='Cdefault explicit standard diagnostic; B0/B1/B2 exact Context. Cthermal failed parent without complete final Native proof remains method_not_delivered, not counted as router failure. No acceptance after cancellation/stale/unsupported/over-budget.',accounting='Each external full exit includes all startup/conversion/attempt/selection/validation/readback/delivery/publication.420inner/450method/600whole plus120export, shared15whole publication reserve. Preparation/failures/research/authoring/AIreview/curation extra; unknowninteractiveCPU notzero. Stored nested samples do not replace complete exit or get added twice.',not_confirmatory=True,project_complete=False)
p.save_json(base/'population.json',parent);parent_pin=p.sha(base/'population.json')
prereqs={str(path):p.sha(path) for path in [*prereq_paths,base/'population.json']}
common=dict(schema=1,runtime=str(runtime),runtime_manifest_sha256=p.sha(manifest),source_head=tools['git_head'],tools=tools,source=str(source),source_hashes=hashes,whole_wall_full_cpu_seconds=600,pass_key='controls_passed',administration_root=str(ROOT),enclosure_sha256=p.sha(ROOT/'.runs/enclose-native7-independent-control-004.py'))
children={}
for arm in population:
 folder=base/arm;folder.mkdir()
 if arm=='B2_portfolio':
  plan=copy.deepcopy(source_record)
  plan.update(common,administration_head=head,administration_files_sha256=admin,controller=str(ROOT/'scripts/qualify_comparison_portfolio.py'),controller_sha256=admin['scripts/qualify_comparison_portfolio.py'],controller_args=['--runtime',str(runtime)],output=outputs[arm],portfolio_output=str(portfolio),material_roots=[str(path) for path in extra],scope='Prospectively frozen B2finite-three-score member of current033sixarm Interf exposed-development comparison; unchanged420/450/600120export balanced30+15reserves. All attempts/costs/native failures retained; valid winner only fixedrank. No production/GUI/general superiority claim.')
  plan.pop('prior_failed_protocol_sha256',None)
 else:
  plan=dict(common,kind='installed-native7-current-method-v1',arm=arm,population=population,outputs=outputs,output=outputs[arm],controller=str(child),controller_sha256=p.sha(child),controller_args=['--runtime',str(runtime)],source_inventory_sha256=hashlib.sha256((json.dumps(hashes,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest(),source_rights=rights,source_rights_sha256=hashlib.sha256(f.canonical(rights).encode()).hexdigest(),qualifier_sha256=p.sha(ROOT/'scripts/qualify_installed_workflow.py'),prerequisite_sha256=prereqs,default_settings=defaults,limits=parent['limits'],scope='Prospectively frozen '+arm+' member of current033sixarm Interf exposed-development comparison. Identical source/constraints/420route450method600whole120export. Actual default Workflow/CLI or optional recoverCLI; API baselines use sealed caller Context/librarydelivery. All startup/Native/failure/selection/readbacks/delivery counted, full external exit required. No untouched/GUI/general superiority or physical claim.')
 plan['population_protocol_path']=str(base/'population.json');plan['population_protocol_sha256']=parent_pin
 p.save_json(folder/'protocol.json',plan);children[arm]=dict(path=str(folder/'protocol.json'),sha256=p.sha(folder/'protocol.json'))
p.save_json(base/'frozen-children.json',dict(schema=1,population_path=str(base/'population.json'),population_sha256=parent_pin,protocols=children,administration_head=head,policy_or_board_changes_after_first_arm=False,project_complete=False))
print(json.dumps(dict(frozen=True,base=str(base),population_sha256=parent_pin,protocols=children,administration_head=head)))
