"""DRAFT: retain the completed frozen057 sanitized report; never run validation.

Execute only after all twelve arms and the unchanged reporter are terminal.
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
notes=ROOT/'evidence/runtime057-default-improve-development-001-notes'
target=ROOT/'evidence/runtime057-default-improve-development-001.json'
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
    ('evidence/runtime056-default-improve-development-001.json','5479f42176c07e1a86b522a0e15bcdfdb79cedf3a6498aab729c656d45b32246')):
    path=ROOT/name;data=json.loads(bind(path,pin));binding=data['files_index'];index=ROOT/binding['path']
    idx=json.loads(bind(index,binding['sha256']))
    dependency_pins[path]=pin;dependency_pins[index]=binding['sha256']
    dependencies.append(dict(path=name,sha256=pin,files_index=binding,historical=name.startswith('evidence/runtime056-')))
    for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
    for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
b=ROOT/'.runs/runtime057-default-improve-development-001'
facts=ROOT/'.runs/runtime057-default-improve-facts-001'
bind(facts/'report.json',args.report_sha256);bind(facts/'files.json',args.report_index_sha256)
bind(b/'population.json','cb39bc8fd63b77c44f5ee96bb0d9bdf5f8571500f53c91cf19c24e0904bc5e4e')
bind(b/'frozen-children.json','aeb1379bb7e34066517043c4a9dd517a5de45e1100044892ce696db7ed45b485')
population=read(b/'population.json');children=read(b/'frozen-children.json');report=read(facts/'report.json')
assert report['public_sanitize'] is True and report['reporter_sha256']==p.sha(timing) and len(report['rows'])==12
assert report['population_sha256']==p.sha(b/'population.json')=='cb39bc8fd63b77c44f5ee96bb0d9bdf5f8571500f53c91cf19c24e0904bc5e4e'
assert report['frozen_children_sha256']==p.sha(b/'frozen-children.json')=='aeb1379bb7e34066517043c4a9dd517a5de45e1100044892ce696db7ed45b485'
assert report['administration_head']==population['administration_head']==children['administration_head']=='ac6575b6ee5c26bfce557859a0d0ec8653208046'
assert report['source_head']=='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
assert report['runtime_manifest_sha256']=='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
assert population['runtime']==str(ROOT/'.runs/runtime057 fresh install 001') and population['planned_family_order']==['ds18b20','ir-obstacle']
assert [(row['family'],row['arm']) for row in report['rows']]==[(family,arm) for family in population['planned_family_order'] for arm in population['planned_arm_order']]
setup=[]
for ordinal,status in ((1,'pre_query_refusal'),(2,'pre_query_refusal'),(3,'pre_query_refusal'),(4,'prepared')):
    path=ROOT/'.runs'/('runtime057-default-improve-freeze-%03d-time.log'%ordinal)
    setup.append(dict(attempt=ordinal,status=status,complete_cost=cost(path),Native=False,engine=False))
qualification=dict(
    parser_regressions001=dict(tests=35,complete_cost=cost(ROOT/'.runs/current-comparison-ir-dependency-targeted-001-time.log')),
    parser_regressions002=dict(tests=36,complete_cost=cost(ROOT/'.runs/current-comparison-ir-dependency-targeted-002-time.log')),
    actual057_pure_metadata_admission=dict(passed=True,Native=False,query=False,central_reader=False,
        complete_cost=cost(ROOT/'.runs/current-comparison-ir-metadata-readback-057-001-time.log')))
reporting_cost=cost(ROOT/'.runs/runtime057-default-improve-report-001-time.log')
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
report_enclosure=ROOT/'.runs/runtime057-default-improve-report-enclosure-001'
process_path=report_enclosure/'process.json';command_log=report_enclosure/'command.log'
process=json.loads(bind(process_path,args.report_process_sha256))
report_argv=[str(ROOT/'.venv/bin/python'),'-B',str(timing),'--population',str(b/'population.json'),
    '--population-sha256',report['population_sha256'],'--children',str(b/'frozen-children.json'),
    '--children-sha256',report['frozen_children_sha256'],'--output',str(facts),'--public-sanitize']
assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0
assert process['cleanup_complete'] is True and process['log_truncated'] is False
assert process['argv']==report_argv and process['cwd']==str(report_enclosure) and process['log']==str(command_log)
command_raw=bind(command_log)
assert command_raw==(json.dumps(dict(rows=12,classifications=outcomes,accepted=False))+'\n').encode()
assert type(process['log_bytes']) is int and process['log_bytes']==len(command_raw)
for name in ('process.json','command.log'):add(report_enclosure/name,Path('administration/report-enclosure')/name)
administration=['freeze-runtime057-default-improve-development-001.py',
    'runtime057-default-improve-development-draft-001.json',
    'runtime057-default-improve-development-draft-001-prior-sourcepin-review.json',
    'runtime057-default-improve-setup-state-001.json',
    'runtime057-default-improve-report-001.log','runtime057-default-improve-report-001-time.log']
for ordinal in range(1,5):
    administration += ['freeze-runtime057-default-improve-development-001-reviewed-draft%03d.py'%ordinal,
        'runtime057-default-improve-freeze-%03d.log'%ordinal,'runtime057-default-improve-freeze-%03d-time.log'%ordinal]
for stem in ('current-comparison-ir-dependency-targeted-001','current-comparison-ir-dependency-targeted-002',
             'current-comparison-ir-metadata-readback-057-001'):
    administration += [stem+'.log',stem+'-time.log']
administration.extend(['retain-runtime057-default-improve-001-pre-seal.py','run-runtime057-comparison-report-001.py'])
bind(ROOT/'.runs/run-runtime057-comparison-report-001.py','1d9d72d5c4024c68efadcdb8dd1d6f686983a4a59c2dfede2efa64b017350615')
bind(ROOT/'.runs/retain-runtime057-default-improve-001-pre-seal.py','ce91e6b8eee4e7cc361f2f0b417a8b432d26360cd93d3514ea2f1d241322ba25')
for name in administration:add(ROOT/'.runs'/name,Path('administration')/name)
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
summary=dict(schema=1,kind='installed057-frozen-default-and-Improve-two-exposed-family-development-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],
    runtime=population['runtime'],original_runtime_manifest_sha256='9c667b15b916fc18fadec6dcbd6e0f9710a0c4cc6daeb36fc616f111ef03722e',
    administration_head=report['administration_head'],accepted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,
    all12_terminal=True,full_population=12,families=population['planned_family_order'],new_or_untouched_families=0,
    outcomes=outcomes,validated_delivery_counts=delivered,complete_external_totals=report['complete_external_totals'],
    additional_setup_attempts=setup,additional_administration_qualification=qualification,additional_reporting=reporting_cost,
    successful_report_invocation=dict(process_path=str(process_path),process_sha256=args.report_process_sha256,
        command_log_sha256=pins[command_log],report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,
        argv=report_argv,cwd=str(report_enclosure),status='success',exit_code=0,cleanup_complete=True,log_truncated=False),
    dependencies=dependencies,limits=population['limits'],
    policy='Exact frozen056 families and six policies on fresh installed057; corrected-standard/B1 remains default. No per-board tuning, reruns or stitched continuation. Every result/failure/warning remains in the frozen denominator.',
    decision='Interpret delivered geometry separately from completion, electrical suitability and human cleanup. This exposed two-family qualification cannot establish broad superiority or untouched confirmation; no outcome is assumed by the curator.',
    fairness='B0 retains common fidelity/protection/Native safeguards, not untouched official-plugin qualification. Baseline sealed API delivery and actual product CLI have differing authority workloads; all external exits count, no generic speed claim. Every actual final own Native/source/field/PRL/protected proof remains local.',
    evidence=dict(report_path=str((notes/'facts/report.json').relative_to(ROOT)),report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,population_sha256=report['population_sha256'],children_sha256=report['frozen_children_sha256']),
    accounting='Complete external attempt/conversion/selection/validation/review/choice/export/readback costs count once. Four setup attempts, both focused parser suites, pure metadata admission and final reporting are separately recorded additional events; do not add overlapping method or child samples. Full207/build/Native/install/GUI costs remain in linked packets. Authoring/AI review and whole interactive costs are unknown additional, not zero. Curation external complete exit must be recorded separately.',
    retention='Only unchanged shared public-sanitized facts, frozen metadata and owned logs/code. Foreign CAD/DSN/SES/plots/full findings/tools remain private on this Mac/outside010. Linked actual GUI091 is one same-Mac fresh-root slice, not fullGUI/queued timing/cleanOS/standalone/Windows/human/physical/electrical or release qualification.',
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
