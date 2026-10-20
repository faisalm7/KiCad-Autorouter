"""Retain shared sanitized cohort facts and original frozen controls, no Native."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/runtime050-default-improve-development-001-notes';target=ROOT/'evidence/runtime050-default-improve-development-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
b=ROOT/'.runs/runtime050-default-improve-development-001';facts=ROOT/'.runs/runtime050-default-improve-development-facts-001'
read=lambda path:json.loads(Path(path).read_bytes())
population=read(b/'population.json');children=read(b/'frozen-children.json');report=read(facts/'report.json')
assert p.sha(b/'population.json')==report['population_sha256']=='c45cf4bbcdbe602dce8ce236b01db1a404e6835aa5f97e5aa32fb21f5d6ee21b'
assert p.sha(b/'frozen-children.json')==report['frozen_children_sha256']=='017db06432d41123d9103fe32491e6cf3e1894e360791627339660f155cc6c1a'
assert report['public_sanitize'] is True and len(report['rows'])==12 and report['administration_head']=='e4e07280b4c6b877d63e493a3a8e439c3e423a43'
assert report['source_head']=='aa0072c6b3d8090de2603e5ecb42a95968fb873b' and report['runtime_manifest_sha256']=='8fdf819606e2345b932139f1c16c330825fd8634caef1b611b5e105b97be22a4'
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for name in ('population.json','frozen-children.json','sources.json','tools-defaults.json','tools-defaults-process.json','progress-after-ds18b20-001.json'):
    add(b/name,Path('frozen')/name)
add(facts/'report.json',Path('facts/report.json'));add(facts/'files.json',Path('facts/files.json'))
outcomes={};delivered={arm:0 for arm in population['population']}
for row in report['rows']:
    family,arm=row['family'],row['arm'];part=b/family/arm
    assert p.sha(part/'protocol.json')==children['protocols'][family][arm]['sha256']==row['protocol_sha256']
    assert (part/'enclosure/result.json').is_file()
    outcomes[row['evidence_classification']]=outcomes.get(row['evidence_classification'],0)+1
    delivered[arm]+=int(row['workflow_delivered'])
    for name in ('protocol.json','outer.log','outer-time.log','enclosure/command.log','enclosure/process.json','enclosure/result.json'):
        add(part/name,Path('arms')/family/arm/name)
assert outcomes=={'validated_delivery':10,'validated_completed_negative':1,'unqualified_or_not_delivered_method':1}
ir=next(row for row in report['rows'] if row['family']=='ir-obstacle' and row['arm']=='Cimprove')
assert ir['workflow_delivered'] is False and ir['attempt_qualified'] is False
producer=Path(read(b/'ir-obstacle/Cimprove/enclosure/result.json')['child_receipt']);data=read(producer)
assert data['outcome']=='unqualified_failure' and data['workflow_delivered'] is False
failed_review=producer.parent/'review.log';assert read(failed_review)=={'status':'rejected','reason':'review copy exceeded 30-second wall or full CPU ceiling'}
for path in (failed_review,producer.parent/'review.process.json'):add(path,Path('failure')/path.name)
route=read(Path(data['selected_route_receipt']));assert route['accepted'] is True and len(route['trials'])==18
assert [route['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,42,0]
failure=dict(method_delivered=False,route_accepted_but_not_delivered=True,route_receipt_sha256=p.sha(Path(data['selected_route_receipt'])),candidate_sha256=route['candidate_sha256'],Native_counts=[0,0,42,0],trials=18,unranked_diagnostic_metrics=route['metrics'],actual_failure='review copy exceeded 30-second wall or full CPU ceiling',actual_review_CLI_wall_seconds=read(producer.parent/'review.process.json')['wall_seconds'],interpretation='Valid route is not completed installed delivery. Every trial and original raw proof retained; do not splice a later repair into this frozen cohort.')
for name in ('runtime050-default-improve-freeze-001.log','runtime050-default-improve-freeze-001-time.log','runtime050-default-improve-report-001.log','runtime050-default-improve-report-001-time.log','toolchain-release-metadata-check-20261020-001.json'):
    add(ROOT/'.runs'/name,Path('administration')/name)
add(Path(__file__),Path('administration')/Path(__file__).name)
for path,name in queue.items():retain(path,name)
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='installed050-frozen-default-and-Improve-two-exposed-family-development-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],administration_head=report['administration_head'],accepted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,all12_terminal=True,full_population=12,families=['ds18b20','ir-obstacle'],new_or_untouched_families=0,outcomes=outcomes,validated_delivery_counts=delivered,complete_external_totals=report['complete_external_totals'],additional_setup=cost(ROOT/'.runs/runtime050-default-improve-freeze-001-time.log'),additional_reporting=cost(ROOT/'.runs/runtime050-default-improve-report-001-time.log'),additional_integration=dict(path='evidence/current-comparison-integration200-001.json',sha256=p.sha(ROOT/'evidence/current-comparison-integration200-001.json')),failed_optional_workflow=failure,decision='B1standard default unchanged. No completion or quality gain beyond corrected/tunedB2 established. Optional Improve delivered only DS18(no trials, matches tuned); IR valid routing could not reach review/delivery. Diagnose general review scaling under unchanged correctness criteria; no rerun/stitch of this cohort. Stock shorter on DS18 and fails IR; tuned portfolio offers IR0vias/175.68976mm versus standard2vias/167.42506mm, a tradeoff.',limits=population['limits'],fairness='B0 shares fidelity/native safeguards, not untouched official-plugin qualification. API baselines and installedCLI have different authority workloads; count all external costs, no generic speed claim. Sources/constraints/code/policy frozen before all12; extra profile/authoring/AIreview/curation separate and unknown costs notzero.',evidence=dict(report_path=str((notes/'facts/report.json').relative_to(ROOT)),report_sha256=p.sha(facts/'report.json'),population_sha256=report['population_sha256'],children_sha256=report['frozen_children_sha256']),retention='Only sanitized shared facts, frozen metadata and owned logs copied. Foreign CAD/DSN/SES/plots/full findings and full raw Native evidence stay on thisMac/outside010; no new restore claim. Expected source opens are routing demand, warnings/ignored checks remain; physical/electrical/cleanup and broad superiority unproved.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(files=len(files),bytes=total,outcomes=outcomes,delivered=delivered)))
