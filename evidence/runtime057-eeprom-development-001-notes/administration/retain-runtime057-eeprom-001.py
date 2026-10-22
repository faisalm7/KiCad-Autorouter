"""DRAFT: retain the completed frozen057 EEPROM sanitized report; never run validation.

Execute only after all six EEPROM arms and the unchanged reporter are terminal.
Final report/index/runner-receipt hashes must come from completed reporting.
Missing inputs refuse; no future result/hash or outcome is assumed.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, math, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
ap=argparse.ArgumentParser()
for flag in ('report-sha256','report-index-sha256','report-process-sha256'):ap.add_argument('--'+flag,required=True)
args=ap.parse_args()
assert all(pv._DIGEST.fullmatch(value) for value in vars(args).values())
self_pin=p.sha(Path(__file__))
notes=ROOT/'evidence/runtime057-eeprom-development-001-notes'
target=ROOT/'evidence/runtime057-eeprom-development-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
pins={Path(__file__):self_pin}
def bind(path,expected=None):
    path=Path(path);raw=io.read_bytes(path,4*1024**2);pin=hashlib.sha256(raw).hexdigest()
    if expected is not None:assert pin==expected,str(path)
    if path in pins:assert pin==pins[path],str(path)
    else:pins[path]=pin
    return raw
read=lambda path:json.loads(bind(path))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
nodes=[n for n in ast.parse(bind(helper,'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1')).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
timing=ROOT/'scripts/report_current_comparison.py'
nodes=[n for n in ast.parse(bind(timing,'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e')).body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(timing)+'::cost','exec'),globals())
def cost(path):
    bind(path);value=complete_cost(path)
    assert Path(value['source'])==Path(path) and value['time_log_sha256']==pins[Path(path)]
    bind(path,value['time_log_sha256']);return value
dependencies=[];dependency_pins={}
for name,pin in (
    ('evidence/runtime057-native-milestone-001.json','37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9'),
    ('evidence/runtime057-ir-delivery-001.json','99717a53b4826dfb8e431c7b41bc511a3aef2f3450822ac1aba462152188e65d'),
    ('evidence/runtime057-install-existing-001.json','9d87a27e8a6329698b80e2e6f905361f40cb2391b70f9a54d7cf0f2917e6d006'),
    ('evidence/gui-runtime057-090-ordinary-001.json','6f55082fbc346a36a72a44bdc32e125c1b2707ea087cdde28120c7a56bc0cccf'),
    ('evidence/gui-runtime057-090-controls-deliveries-001.json','a4f4a2b3beb8a0dd7477d254a15fb800612a3d72f9956f1b45af67919aa48640'),
    ('evidence/gui-runtime057-install091-delivery-001.json','df33b95e2794b6a7c134a55ed5d88d510c35073f6210aa231b20a204eff8ddaf'),
    ('evidence/runtime057-default-improve-development-001.json','b7a38910aae7cdb3c9664fc662ce662afd454815891a19b09e70c45c83366abe'),
    ('evidence/development-eeprom-001.json','3cdf0561e184daaac153de58a788c735332bdfd67c340f73756530b6171ca223')):
    path=ROOT/name;data=json.loads(bind(path,pin));binding=data['files_index'];index=ROOT/binding['path']
    idx=json.loads(bind(index,binding['sha256']))
    dependency_pins[path]=pin;dependency_pins[index]=binding['sha256']
    dependencies.append(dict(path=name,sha256=pin,files_index=binding,historical=False))
    for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
b=ROOT/'.runs/runtime057-eeprom-development-001'
facts=ROOT/'.runs/runtime057-eeprom-facts-001'
bind(facts/'report.json',args.report_sha256);bind(facts/'files.json',args.report_index_sha256)
bind(b/'population.json','f9c871ea5259cc4b977b6448ceb9439dffb6e8f5626bf2b437d90afd2a8cf99b')
bind(b/'frozen-children.json','99101afda90de8fe7af40e8183ffb6d903be8f2b97cf24aa0ed3347bf51e17cc')
population=read(b/'population.json');children=read(b/'frozen-children.json');report=read(facts/'report.json')
assert report['public_sanitize'] is True and report['reporter_sha256']==p.sha(timing) and len(report['rows'])==6
assert report['population_sha256']==p.sha(b/'population.json')=='f9c871ea5259cc4b977b6448ceb9439dffb6e8f5626bf2b437d90afd2a8cf99b'
assert report['frozen_children_sha256']==p.sha(b/'frozen-children.json')=='99101afda90de8fe7af40e8183ffb6d903be8f2b97cf24aa0ed3347bf51e17cc'
assert report['administration_head']==population['administration_head']==children['administration_head']=='781b4be312427ef1d5748957786e312e6ab07255'
assert report['source_head']=='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
assert report['runtime_manifest_sha256']=='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e'
assert population['runtime']==str(ROOT/'.runs/runtime-directory-057/runtime') and population['planned_family_order']==['eeprom']
assert [(row['family'],row['arm']) for row in report['rows']]==[(family,arm) for family in population['planned_family_order'] for arm in population['planned_arm_order']]
assert population['planned_arm_order']==['Cdefault','B0','B1','B2single_tuned','B2_portfolio','Cimprove']
assert set(population['population'])==set(population['planned_arm_order']) and len(population['population'])==6
assert population['freezer_sha256']=='9729687563f9dd23fcee7b85d1cb4835dd57f436a23626d7f07d93a9d07033bd'
setup=[dict(attempt=1,status='prepared',complete_cost=cost(ROOT/'.runs/runtime057-eeprom-freeze-time-001.log'),Native=False,engine=False)]
reporting_cost=cost(ROOT/'.runs/runtime057-eeprom-report-001-time.log')
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for name in ('population.json','frozen-children.json','sources.json','qualification.json','tools-defaults.json','tools-defaults-process.json'):
    add(b/name,Path('frozen')/name)
for name in ('report.json','files.json'):add(facts/name,Path('facts')/name)
outcomes={};delivered={arm:0 for arm in population['population']}
for row in report['rows']:
    family,arm=row['family'],row['arm'];part=b/family/arm
    assert children['protocols'][family][arm]['sha256']==row['protocol_sha256']
    bind(part/'protocol.json',row['protocol_sha256']);bind(part/'enclosure/result.json',row['outer_sha256'])
    assert row['complete_cost']['source']==str(part/'outer-time.log')
    bind(part/'outer-time.log',row['complete_cost']['time_log_sha256'])
    assert cost(part/'outer-time.log')==row['complete_cost']
    assert type(row['workflow_delivered']) is bool
    outcomes[row['evidence_classification']]=outcomes.get(row['evidence_classification'],0)+1
    delivered[arm]+=int(row['workflow_delivered'])
    for name in ('protocol.json','outer.log','outer-time.log','enclosure/command.log','enclosure/process.json','enclosure/result.json'):
        add(part/name,Path('arms')/family/arm/name)
report_enclosure=ROOT/'.runs/runtime057-eeprom-report-enclosure-001'
process_path=report_enclosure/'process.json';command_log=report_enclosure/'command.log'
process=json.loads(bind(process_path,args.report_process_sha256))
report_argv=[str(ROOT/'.venv/bin/python'),'-B',str(timing),'--population',str(b/'population.json'),
    '--population-sha256',report['population_sha256'],'--children',str(b/'frozen-children.json'),
    '--children-sha256',report['frozen_children_sha256'],'--output',str(facts),'--public-sanitize']
assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0
assert process['cleanup_complete'] is True and process['log_truncated'] is False
assert process['argv']==report_argv and process['cwd']==str(report_enclosure) and process['log']==str(command_log)
command_raw=bind(command_log)
assert command_raw==(json.dumps(dict(rows=6,classifications=outcomes,accepted=False))+'\n').encode()
assert type(process['log_bytes']) is int and process['log_bytes']==len(command_raw)
for name in ('process.json','command.log'):add(report_enclosure/name,Path('administration/report-enclosure')/name)
administration=['runtime057-eeprom-freeze-001.log','runtime057-eeprom-freeze-time-001.log',
    'runtime057-eeprom-report-001.log','runtime057-eeprom-report-001-time.log','run-runtime057-eeprom-report-001.py']
bind(ROOT/'.runs/run-runtime057-eeprom-report-001.py','d6b546499d40708e84bb68d93a7210f52c164327bb09cb086c55d935982f0ccc')
freezer=ROOT/'scripts/freeze_current_comparison.py'
bind(freezer,'9729687563f9dd23fcee7b85d1cb4835dd57f436a23626d7f07d93a9d07033bd')
add(freezer,Path('administration/freeze_current_comparison.py'))
for name in administration:add(ROOT/'.runs'/name,Path('administration')/name)
add(ROOT/'.runs/retain-runtime057-eeprom-001-reviewed-draft001.py',Path('administration/retain-runtime057-eeprom-001-reviewed-draft001.py'))
bind(ROOT/'.runs/retain-runtime057-eeprom-001-reviewed-draft001.py','e4fda3cfc3656709d2fb4eb118b41eea8a8375d8de633c1e4b2f7be50ca2c1f8')
add(Path(__file__),Path('administration')/Path(__file__).name)
planned_refs=dict(refs);planned_files=[];planned_material=[];planned_bytes=0
for path,name in queue.items():
    raw=bind(path);pin=pins[path];destination=planned_refs.get(pin)
    if destination is None:
        assert b'\0' not in raw;raw.decode('utf8');destination=str((notes/name).relative_to(ROOT))
        planned_refs[pin]=destination;planned_bytes+=len(raw)
        planned_files.append(dict(path=destination,bytes=len(raw),sha256=pin))
    elif pin in refs:bind(ROOT/destination,pin)
    planned_material.append(dict(original=str(path.relative_to(ROOT)),retained=destination,bytes=len(raw),sha256=pin))
index=notes/'files.json';index_data=dict(schema=1,files=planned_files,material=planned_material)
index_raw=(json.dumps(index_data,indent=2)+'\n').encode();index_pin=hashlib.sha256(index_raw).hexdigest()
summary=dict(schema=1,kind='installed057-frozen-default-and-Improve-EEPROM-exposed-development-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],
    runtime=population['runtime'],original_runtime_manifest_sha256='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e',
    administration_head=report['administration_head'],accepted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,
    all6_terminal=True,full_population=6,families=population['planned_family_order'],new_development_exposed_families=1,untouched_or_independent_families=0,
    outcomes=outcomes,validated_delivery_counts=delivered,complete_external_totals=report['complete_external_totals'],
    additional_setup_attempts=setup,additional_reporting=reporting_cost,
    successful_report_invocation=dict(process_path=str(process_path),process_sha256=args.report_process_sha256,
        command_log_sha256=pins[command_log],report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,
        argv=report_argv,cwd=str(report_enclosure),status='success',exit_code=0,cleanup_complete=True,log_truncated=False),
    dependencies=dependencies,limits=population['limits'],
    policy='One newly development-exposed EEPROM family with the same six frozen policies on the original curated057 runtime root. Corrected-standard/B1 remains default. No per-board tuning, reruns or stitched continuation. Every result/failure/warning remains in the six-arm denominator.',
    decision='Interpret delivered geometry separately from completion, electrical suitability and human cleanup. This one development-exposed family cannot establish broad superiority, independent ancestry or untouched confirmation; no outcome is assumed by the curator.',
    fairness='B0 retains common fidelity/protection/Native safeguards, not untouched official-plugin qualification. Baseline sealed API delivery and actual product CLI have differing authority workloads; all external exits count, no generic speed claim. Every actual final own Native/source/field/PRL/protected proof remains local.',
    evidence=dict(report_path=str((notes/'facts/report.json').relative_to(ROOT)),report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,population_sha256=report['population_sha256'],children_sha256=report['frozen_children_sha256']),
    accounting='Complete external attempt/conversion/selection/validation/review/choice/export/readback costs count once. One freeze setup and final reporting are separately recorded additional events; do not add overlapping method or child samples. No new parser/test costs are attributed here. Full207/build/Native/IR/install/GUI/prior057study costs remain in linked packets; intake acquisition/inspection/original-diagnostic/Preview costs belong to its separate intake packet. Authoring/AI review and whole interactive costs are unknown additional, not zero. Curation external complete exit must be recorded separately.',
    retention='Only unchanged shared public-sanitized facts, frozen metadata and owned logs/code. Foreign CAD/DSN/SES/plots/full findings/tools remain private on this Mac/outside010. Rights are publisher declarations; public CAD/model/title closure and independent ancestry remain unqualified. Existing linked Native/IR/GUI/install/prior057study evidence is not newly executed by this comparison. No EEPROM GUI, electrical/human or release qualification is inferred.',
    intake_evidence=dict(path='evidence/development-eeprom-001.json',sha256='3cdf0561e184daaac153de58a788c735332bdfd67c340f73756530b6171ca223',binding_status='Completed source-only intake cutoff, bound above with its files index; no routing outcome or licence-body/ancestry/physical claim from that intake.'),
    files_index=dict(path=str(index.relative_to(ROOT)),sha256=index_pin))
summary_raw=(json.dumps(summary,indent=2)+'\n').encode();summary_pin=hashlib.sha256(summary_raw).hexdigest()
assert len(planned_files)+2<2000 and all(len(raw)<=4*1024**2 for raw in (index_raw,summary_raw))
assert planned_bytes+len(index_raw)+len(summary_raw)<16*1024**2,'Split before writing; never raise caps'
def fresh():
    for path,pin in pins.items():assert hashlib.sha256(io.read_bytes(path,4*1024**2)).hexdigest()==pin,str(path)
fresh()
for path,name in queue.items():retain(path,name)
assert files==planned_files and material==planned_material and total==planned_bytes
for path in files:pins[ROOT/path['path']]=path['sha256']
fresh();p.save_json(index,index_data);bind(index,index_pin);fresh()
fresh();p.save_json(target,summary);bind(target,summary_pin);fresh()
print(json.dumps(dict(files=len(files),bytes=total,outcomes=outcomes,delivered=delivered)))
