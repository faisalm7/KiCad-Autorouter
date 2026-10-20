"""Retain shared sanitized full-population facts and frozen controls, never Native."""
from pathlib import Path
import ast, datetime, hashlib, json, math, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
notes=ROOT/'evidence/runtime056-default-improve-development-001-notes'
target=ROOT/'evidence/runtime056-default-improve-development-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
timing=ROOT/'scripts/report_current_comparison.py'
assert p.sha(timing)=='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
nodes=[n for n in ast.parse(timing.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(timing)+'::cost','exec'),globals())
b=ROOT/'.runs/runtime056-default-improve-development-001'
facts=ROOT/'.runs/runtime056-default-improve-development-facts-001'
read=lambda path:json.loads(Path(path).read_bytes())
population=read(b/'population.json');children=read(b/'frozen-children.json');report=read(facts/'report.json')
assert report['public_sanitize'] is True and len(report['rows'])==12
assert report['population_sha256']==p.sha(b/'population.json')=='483d39a12f35705dcc72848ce9fa9a18b66a5d05a7574dee8b18d0e00a035cea'
assert report['frozen_children_sha256']==p.sha(b/'frozen-children.json')=='c8980b9bab253b054b7bc6543b87c00120adaf2d13cf80f4390ed3af6842e625'
assert report['administration_head']=='896ac626f38352702e5d7a237ec6b5cc45d7e04d'
assert report['source_head']=='a03b5e8b6ae523d9f099cf211815900053629fe3'
assert report['runtime_manifest_sha256']=='b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded'
assert population['planned_family_order']==['ds18b20','ir-obstacle']
assert set((r['family'],r['arm']) for r in report['rows'])=={(family,arm) for family in population['planned_family_order'] for arm in population['planned_arm_order']}
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for name in ('population.json','frozen-children.json','sources.json','tools-defaults.json','tools-defaults-process.json'):
    add(b/name,Path('frozen')/name)
for name in ('report.json','files.json'):add(facts/name,Path('facts')/name)
outcomes={};delivered={arm:0 for arm in population['population']}
for row in report['rows']:
    family,arm=row['family'],row['arm'];part=b/family/arm
    assert p.sha(part/'protocol.json')==children['protocols'][family][arm]['sha256']==row['protocol_sha256']
    assert type(row['workflow_delivered']) is bool
    outcomes[row['evidence_classification']]=outcomes.get(row['evidence_classification'],0)+1
    delivered[arm]+=int(row['workflow_delivered'])
    for name in ('protocol.json','outer.log','outer-time.log','enclosure/command.log','enclosure/process.json','enclosure/result.json'):
        add(part/name,Path('arms')/family/arm/name)
for name in ('runtime056-default-improve-freeze-001.log','runtime056-default-improve-freeze-001-time.log',
             'runtime056-default-improve-report-001.log','runtime056-default-improve-report-001-time.log',
             'runtime056-optional-improve-development-intent-001.json','runtime056-optional-improve-development-intent-002.json',
             'runtime056-cutoff-reporting-failure-001.json','runtime056-cutoff-reporting-failure-002.json'):
    add(ROOT/'.runs'/name,Path('administration')/name)
add(Path(__file__),Path('administration')/Path(__file__).name)
for path,name in queue.items():retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='installed056-frozen-default-and-Improve-two-exposed-family-development-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],
    administration_head=report['administration_head'],accepted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,
    all12_terminal=True,full_population=12,families=population['planned_family_order'],new_or_untouched_families=0,
    outcomes=outcomes,validated_delivery_counts=delivered,complete_external_totals=report['complete_external_totals'],
    additional_setup=complete_cost(ROOT/'.runs/runtime056-default-improve-freeze-001-time.log'),
    additional_reporting=complete_cost(ROOT/'.runs/runtime056-default-improve-report-001-time.log'),
    additional_administration_qualification=dict(path='evidence/current-comparison-native-cohort-056-001.json',sha256=p.sha(ROOT/'evidence/current-comparison-native-cohort-056-001.json')),
    previous050_study_unchanged=dict(path='evidence/runtime050-default-improve-development-001.json',sha256=p.sha(ROOT/'evidence/runtime050-default-improve-development-001.json')),
    limits=population['limits'],policy='Corrected-standard/B1 remains default; optional Improve uses the same fixed policy on both families. No per-board tuning, reruns or stitched continuation. Every result/failure/warning remains in the frozen denominator.',
    decision='Interpret delivered candidate geometry separately from completion, electrical suitability and human cleanup. This exposed two-family regression cannot establish broad superiority or untouched confirmation. No default or release change is authorized by its outcome.',
    fairness='B0 retains common fidelity/protection/Native safeguards, not untouched official-plugin qualification. Baseline sealed API delivery and actual product CLI have differing authority workloads; all external exits counted, no generic speed claim. Own final Native/source/field/PRL/protected proofs remain local for every actual final.',
    evidence=dict(report_path=str((notes/'facts/report.json').relative_to(ROOT)),report_sha256=p.sha(facts/'report.json'),population_sha256=report['population_sha256'],children_sha256=report['frozen_children_sha256']),
    accounting='Complete external conversion/attempt/selection/validation/review/choice/export/readback costs count once. Setup/reporting/qualification/full206/failed drafts/authoring/research/AI review/GUI/curation are additional; unmetered partial-progress caller costs are unknown, notzero. Two partial-progress metadata callers refused; Native work was not repeated or changed. Existing full-population reporter supplies the final facts.',
    retention='Only shared public-sanitized facts, frozen metadata and owned logs/code. Foreign CAD/DSN/SES/plots/full findings/tools remain local on this Mac/outside010. No full raw restoration, new-root GUI, Windows, human/physical/electrical or release claim.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,outcomes=outcomes,delivered=delivered)))
