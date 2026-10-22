"""DRAFT: retain the completed frozen058 sanitized report; never run validation.

Execute only after all eighteen arms and the unchanged reporter are terminal.
Final report/index/runner-receipt hashes must come from completed reporting.
Missing inputs refuse; no future result/hash or outcome is assumed.
"""
from pathlib import Path
import argparse, ast, datetime, hashlib, json, math, os, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,provenance as pv
ap=argparse.ArgumentParser()
for flag in ('report-sha256','report-index-sha256','report-process-sha256'):ap.add_argument('--'+flag,required=True)
args=ap.parse_args()
assert all(pv._DIGEST.fullmatch(value) for value in vars(args).values())
self_pin=p.sha(Path(__file__))
notes=ROOT/'evidence/runtime058-installed-three-family-001-notes'
target=ROOT/'evidence/runtime058-installed-three-family-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(target)
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
    ('evidence/runtime058-native-milestone-001.json','1dd9972cdf5b20392cde77f42ddb177838e8a65c2b4cd22dc8409580ad42fc29'),
    ('evidence/runtime058-ir-delivery-001.json','f2fd277f94a94e05be1748b5619490870bc2ef134bf33fb4d04eed0b19eceed8'),
    ('evidence/runtime058-eeprom-improve-regression-001.json','4d05669921fa9b186552a2d57ff3f8a50aa70dead331de3edf89ef8d8ba44176'),
    ('evidence/runtime058-install-existing-001.json','0058dd996b0a57249d05e80a9b8e5703eb8cdb413510a7ff0a4d1e0db0bb02f5'),
    ('evidence/gui-runtime058-092-ordinary-001.json','84da001767e76f9ca6c8d7ebc862a3b177f14a3c4f623a1478383145a6c114f6'),
    ('evidence/gui-runtime058-092-observations-001.json','e32c66208cdc46668853ea7f81465f64151da806d283e04374e934ad07bf9138'),
    ('evidence/gui-runtime058-install093-observations-002.json','d56e8e3824d137f0807a4d6f53f13f1e4acc46baa3a00bdca19d10319fe4d403'),
    ('evidence/runtime057-default-improve-development-001.json','b7a38910aae7cdb3c9664fc662ce662afd454815891a19b09e70c45c83366abe'),
    ('evidence/runtime057-eeprom-development-001.json','d679f83e507225b83861e08d8380ecc3b28294aabdfd4475aea1aae11386ff79')):
    path=ROOT/name;data=json.loads(bind(path,pin));binding=data.get('files_index')
    dependency_pins[path]=pin
    dependencies.append(dict(path=name,sha256=pin,files_index=binding,historical=name.startswith('evidence/runtime057-')))
    # Current GUI observation-only packets deliberately have no full-proof index.
    if binding is not None:
        index=ROOT/binding['path'];idx=json.loads(bind(index,binding['sha256']));dependency_pins[index]=binding['sha256']
        for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
        for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
b=ROOT/'.runs/runtime058-installed-three-family-001'
facts=ROOT/'.runs/runtime058-installed-three-family-report-001'
bind(facts/'report.json',args.report_sha256);bind(facts/'files.json',args.report_index_sha256)
bind(b/'population.json','7aa591a491b9358868c351b4cf357dcbe38351185bdfc5a7e91832a5330a71f8')
bind(b/'frozen-children.json','c0e04f9d0751cf1272abe00ed68ec3af9ccdea53759d32695c3d950fe0895b8f')
population=read(b/'population.json');children=read(b/'frozen-children.json');report=read(facts/'report.json')
assert report['public_sanitize'] is True and report['reporter_sha256']==p.sha(timing) and len(report['rows'])==18
assert report['population_sha256']==p.sha(b/'population.json')=='7aa591a491b9358868c351b4cf357dcbe38351185bdfc5a7e91832a5330a71f8'
assert report['frozen_children_sha256']==p.sha(b/'frozen-children.json')=='c0e04f9d0751cf1272abe00ed68ec3af9ccdea53759d32695c3d950fe0895b8f'
assert report['administration_head']==population['administration_head']==children['administration_head']=='f832b0435ea231332de1ac3831d166bc71c10b12'
assert report['source_head']=='8f5e96b88dd22cd25919bb71ce47711612994efa'
assert report['runtime_manifest_sha256']=='19bdfe08169624f49a3b2bee1b789258f2ccaac63ad24a1e06c1d6ba371788f2'
assert population['runtime']==str(ROOT/'.runs/runtime058 fresh install 001') and population['planned_family_order']==['ds18b20','ir-obstacle','eeprom']
assert [(row['family'],row['arm']) for row in report['rows']]==[(family,arm) for family in population['planned_family_order'] for arm in population['planned_arm_order']]
setup=[dict(attempt=1,status='prepared',complete_cost=cost(ROOT/'.runs/runtime058-installed-three-family-freeze001-time.log'),Native=False,engine=False)]
reporting_cost=cost(ROOT/'.runs/runtime058-three-family-report-001-time.log')
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
report_enclosure=ROOT/'.runs/runtime058-installed-three-family-report-enclosure-001'
process_path=report_enclosure/'process.json';command_log=report_enclosure/'command.log'
process=json.loads(bind(process_path,args.report_process_sha256))
report_argv=[str(ROOT/'.venv/bin/python'),'-B',str(timing),'--population',str(b/'population.json'),
    '--population-sha256',report['population_sha256'],'--children',str(b/'frozen-children.json'),
    '--children-sha256',report['frozen_children_sha256'],'--output',str(facts),'--public-sanitize']
assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0
assert process['cleanup_complete'] is True and process['log_truncated'] is False
assert process['argv']==report_argv and process['cwd']==str(report_enclosure) and process['log']==str(command_log)
command_raw=bind(command_log)
assert command_raw==(json.dumps(dict(rows=18,classifications=outcomes,accepted=False))+'\n').encode()
assert type(process['log_bytes']) is int and process['log_bytes']==len(command_raw)
launcher_summary=read(ROOT/'.runs/runtime058-three-family-report-001.log')
assert launcher_summary['passed'] is True and launcher_summary['process_sha256']==args.report_process_sha256
assert launcher_summary['report_sha256']==args.report_sha256 and launcher_summary['index_sha256']==args.report_index_sha256
assert launcher_summary['Native'] is False and launcher_summary['engine'] is False
assert launcher_summary['controller_sha256']=='af5f3dfd48e18e7e634dab55515aad7b53cf7953cd10251ea4aca2e163b265b8'
for name in ('process.json','command.log'):add(report_enclosure/name,Path('administration/report-enclosure')/name)
administration=['freeze-runtime058-installed-three-family-001.py',
    'runtime058-installed-three-family-draft-001.json',
    'runtime058-installed-three-family-freeze001.log','runtime058-installed-three-family-freeze001-time.log',
    'run-runtime058-three-family-report-001.py','runtime058-three-family-report-draft-001.json',
    'runtime058-three-family-report-001.log','runtime058-three-family-report-001-time.log']
bind(ROOT/'.runs/freeze-runtime058-installed-three-family-001.py','6ed6bdad407f7977209231907d29ce2830fa0f39cbab3b40cc75f23bc72d8952')
bind(ROOT/'.runs/run-runtime058-three-family-report-001.py','af5f3dfd48e18e7e634dab55515aad7b53cf7953cd10251ea4aca2e163b265b8')
bind(ROOT/'.runs/runtime058-installed-three-family-draft-001.json','7cddff5bd277dac92aa1465505a5f549fd73fab95afc89077c7fdd02ccf7f540')
bind(ROOT/'.runs/runtime058-three-family-report-draft-001.json','f42e8d33dc248d6d823815748ada7b030f6c2f7b58a3d8a4d79b4118eaaf5e79')
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
summary=dict(schema=1,kind='installed058-frozen-default-and-Improve-three-exposed-family-development-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=report['source_head'],runtime_manifest_sha256=report['runtime_manifest_sha256'],
    runtime=population['runtime'],original_runtime_manifest_sha256='4f923e053577eb7b7f0425dee6a90be34075641495b4ac2a359ccb1a759f2c74',
    administration_head=report['administration_head'],accepted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,
    all18_terminal=True,full_population=18,families=population['planned_family_order'],new_or_untouched_families=0,
    outcomes=outcomes,validated_delivery_counts=delivered,complete_external_totals=report['complete_external_totals'],
    additional_setup_attempts=setup,additional_reporting=reporting_cost,
    successful_report_invocation=dict(process_path=str(process_path),process_sha256=args.report_process_sha256,
        command_log_sha256=pins[command_log],report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,
        argv=report_argv,cwd=str(report_enclosure),status='success',exit_code=0,cleanup_complete=True,log_truncated=False),
    dependencies=dependencies,limits=population['limits'],
    policy='Exact exposed DS18/IR/EEPROM sources and six frozen policies on fresh installed058; corrected-standard/B1 remains default. No per-board tuning, per-arm retries or stitched old outcomes. Every result/failure/warning remains in the frozen denominator.',
    decision='Interpret delivered geometry separately from completion, electrical suitability and human cleanup. This exposed three-family qualification cannot establish broad superiority or untouched confirmation; no outcome is assumed by the curator.',
    fairness='B0 retains common fidelity/protection/Native safeguards, not untouched official-plugin qualification. Baseline sealed API delivery and actual product CLI have differing authority workloads; all external exits count, no generic speed claim. Every actual final own Native/source/field/PRL/protected proof remains local.',
    evidence=dict(report_path=str((notes/'facts/report.json').relative_to(ROOT)),report_sha256=args.report_sha256,report_index_sha256=args.report_index_sha256,population_sha256=report['population_sha256'],children_sha256=report['frozen_children_sha256']),
    accounting='Complete external attempt/conversion/selection/validation/review/choice/export/readback costs count once. Current prospective setup and final reporting are separately recorded additional events; do not add overlapping method or child samples. Full209/build/Native/install/GUI and prior057 study costs remain in linked packets, not added as new arms or setup. Authoring/AI review and whole interactive costs are unknown additional, not zero. Curation external complete exit must be recorded separately.',
    retention='Only unchanged shared public-sanitized facts, frozen metadata and owned logs/code. Foreign CAD/DSN/SES/plots/full findings/tools remain private on this Mac/outside010. Linked actual GUI093 is one same-Mac fresh-root slice; its observation-only packet is not a backup of all raw final proofs, not fullGUI/queued timing/cleanOS/standalone/Windows/human/physical/electrical or release qualification.',
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
