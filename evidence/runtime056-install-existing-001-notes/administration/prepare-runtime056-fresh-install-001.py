"""Prepare two unchanged fresh-root056 CLI controls; never execute Native/GUI.

The existing artifact and copied venv must already exist. Installation records
are descriptive, not authority. Doctor/query run with private HOME/TMP/minimal
PATH in this helper's process/children only; owner/global settings are untouched.
A late failure retains its exclusive partial preparation, never reused here.
"""
import time, resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import copy,json,os,re,shutil,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,provenance as pv,floor_route as f,handoff as h,placement_clearance as io
from autorouter.runner import run
from scripts import freeze_current_comparison as shared
HEAD='a03b5e8b6ae523d9f099cf211815900053629fe3'
OLD='b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded'
NEW='6416d003b92b522fcb81aeb28bbd4ebe44dbb1a4c53f18dc896fe679f4d8749c'
source=ROOT/'.runs/runtime-directory-056/runtime';runtime=ROOT/'.runs/runtime056 fresh install 001'
base=ROOT/'.runs/runtime056-install-existing-qualification-001'
private=runtime/'.runs/install-existing-environment-001'
self_path=h.real_path(Path(__file__).absolute());assert self_path==ROOT/'.runs/prepare-runtime056-fresh-install-001.py'
pins={str(self_path):p.sha(self_path)}
def pin(path,expected=None):
    path=h.real_path(path);digest=p.sha(path)
    if expected is not None:assert digest==expected
    pins[str(path)]=digest;return f.read_json(path)
def left():return min(90-(time.monotonic()-START),90-(cpu()-CPU0))
def ok(process):
    assert process['status']=='success' and type(process['exit_code']) is int and process['exit_code']==0
    assert process['cleanup_complete'] is True and process['log_truncated'] is False
old=pin(source/pv.MANIFEST,OLD);new=pin(runtime/pv.MANIFEST,NEW)
assert old['root']==str(source) and new==dict(old,root=str(runtime))
assert old['build_source']['git_head']==HEAD and old['native_version']=='10.0.7' and old['local_engine'] is not None
assert len(old['immutable_files_sha256'])==54
implementation={name:digest for name,digest in old['immutable_files_sha256'].items() if name.startswith('autorouter/')}
old_identity=pv._runtime_identity(source,implementation);identity=pv._runtime_identity(runtime,implementation)
assert old_identity['manifest_sha256']==OLD and identity['manifest_sha256']==NEW and identity['git_head']==HEAD
recipe=pin(source.parent/'preparation.json')
assert recipe['prepared'] is True and recipe['source_head']==HEAD and recipe['manifest_sha256']==OLD
assert recipe['recipe']['source_provenance']==old_identity
full_path=ROOT/'.runs/full-integration-206/execution.json'
full=pin(full_path,recipe['full206_execution_sha256']);assert full['passed'] is True and full['sources_unchanged'] is True;ok(full['process'])
cohort=pin(ROOT/'evidence/runtime056-native-milestone-001.json','cc2973609c09bf607f08f0a0b1b9e15f93d03eb1bd99b0b696d56a228546e992')
assert cohort['source_head']==HEAD and cohort['runtime_manifest_sha256']==OLD and cohort['Native_cohort_passed'] is True
assert cohort['actual_GUI'] is False and len(cohort['cases'])==11
receipt_path=runtime/'.runs/install-existing-runtime-001.json'
receipt=pin(receipt_path,'778829fd42b47c8830e3dcf3a148d6f4d218c8643d477168fa3bf8ffe6cae7ef')
assert receipt['schema']==1 and receipt['kind']=='existing-runtime-installation-record-v1'
assert receipt['source_root']==str(source) and receipt['source_manifest_sha256']==OLD
assert receipt['destination_root']==str(runtime) and receipt['destination_manifest_sha256']==NEW
assert receipt['immutable_files']==len(new['immutable_files_sha256']) and receipt['local_engine']==new['local_engine']
assert receipt['record_is_authoritative'] is False and receipt['receipt_may_remain_on_refusal'] is True
assert all(receipt[key] is False for key in ('mutable_state_copied','venv_created','launcher_created','native_qualification_performed','standalone','published'))
installer=h.real_path(receipt['installer']['path']);assert installer==ROOT/'scripts/prepare_runtime.py'
assert p.sha(installer)==receipt['installer']['sha256'];pins[str(installer)]=p.sha(installer)
returned=pin(ROOT/'.runs/runtime056-install-existing-copy-001.log')
assert returned['root']==str(runtime) and returned['source_provenance']==identity
assert returned['installation_receipt']==str(receipt_path) and returned['installation_receipt_sha256']==pins[str(receipt_path)]
assert returned['local_engine_copied'] is True and returned['standalone'] is False
for name in ('runtime056-install-existing-copy-001-time.log','runtime056-install-existing-venv-001.log','runtime056-install-existing-venv-001-time.log'):
    path=h.real_path(ROOT/'.runs'/name);pins[str(path)]=p.sha(path)
def venv_config(root):
    path=h.real_path(root/'.venv/pyvenv.cfg');raw=pv.read_bytes(path,64*1024);pins[str(path)]=p.sha(path)
    result={}
    for line in raw.decode().splitlines():
        key,sep,value=line.partition('=');assert sep and key.strip() not in result
        result[key.strip()]=value.strip()
    assert result['version']=='3.11.9' and result['include-system-site-packages']=='false'
    return result
old_cfg=venv_config(source);cfg=venv_config(runtime)
assert all(cfg[key]==old_cfg[key] for key in ('home','version','executable','include-system-site-packages'))
base_python=h.real_path(recipe['base_python']['path']);assert p.sha(base_python)==recipe['base_python']['sha256']
assert pv.file_digest(runtime/'.venv/bin/python',pv.MAX_ENGINE_BYTES)[0]==p.sha(base_python)
assert cfg['executable']==str(base_python) and os.access(runtime/'.venv/bin/python',os.X_OK)
pins[str(base_python)]=p.sha(base_python)
for path in (base,private):assert h.real_path(path,existing=False)==path and not os.path.lexists(path)
assert left()>60 and shutil.disk_usage(ROOT).free>4*1024**3
base.mkdir(mode=0o700);owner={};h.capture_destination(owner,base)
private.mkdir(mode=0o700);private_owner={};h.capture_destination(private_owner,private)
for name in ('home','tmp'):(private/name).mkdir(mode=0o700)
environment=dict(HOME=str(private/'home'),TMPDIR=str(private/'tmp')+'/',TMP=str(private/'tmp'),TEMP=str(private/'tmp'),
    PATH='/usr/bin:/bin:/usr/sbin:/sbin',LANG='C',LC_ALL='C',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1')
# query_runtime deliberately uses the shared child_environment. Restrict only
# this finite preparer's environment while it constructs that explicit child env.
# Restore it even on failure; no owner/global configuration is edited.
saved_environment=dict(os.environ)
try:
    os.environ.clear();os.environ.update(environment)
    query,query_pins=shared.query_runtime(runtime,base)
finally:
    os.environ.clear();os.environ.update(saved_environment)
pins.update(query_pins);tools=query['tools']
assert query['runtime']==str(runtime) and query['prefix']==str(runtime/'.venv') and query['interpreter']==str(runtime/'.venv/bin/python')
assert query['defaults']==dict(shared.pref.DEFAULTS) and tools['source_provenance']==identity
assert tools['git_head']==HEAD and tools['kicad']=='10.0.7' and tools['implementation_sha256']==implementation
assert left()>1
process=run([*f.SANDBOX,str(runtime/'.venv/bin/python'),'-B','-m','autorouter','doctor'],cwd=runtime,env=environment,
    log=base/'doctor.json',timeout=min(30,left()-1),max_log_bytes=512*1024,max_group_rss_bytes=1024**3,max_workdir_bytes=128*1024**2)
p.save_json(base/'doctor-process.json',process);ok(process)
doctor=pin(base/'doctor.json');pins[str(base/'doctor-process.json')]=p.sha(base/'doctor-process.json')
assert doctor['ready'] is True and doctor['workspace']==str(runtime)
assert doctor['checks']['runtime_provenance']==dict(verified=True,identity=identity)
encloser=ROOT/'.runs/enclose-runtime044-workflow-001.py';driver=ROOT/'scripts/qualify_runtime_workflow.py'
original_base=ROOT/'.runs/runtime056-native-qualification-001';frozen=pin(original_base/'frozen.json')
assert frozen['source_head']==HEAD and frozen['runtime_manifest_sha256']==OLD
rows={row['case']:row for row in frozen['protocols']};assert len(rows)==11
entries=[];source_hashes={}
for label,score in (('ordinary-alias2Cu',None),('via-high-partial2Cu','via_high')):
    row=rows[label];original=Path(row['protocol']);plan=pin(original,row['protocol_sha256'])
    assert plan['case']==label and plan['method']=='route' and plan['runtime']==str(source)
    assert plan['source_head']==HEAD and plan['runtime_manifest_sha256']==OLD
    assert plan['settings']==dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=score)
    assert plan['budgets']==dict(route=90,export=90) and plan['expected_counts']==[0,0,0,0] and plan['expected_protected_count']==4
    assert p.sha(encloser)==plan['enclosure_sha256'] and p.sha(driver)==plan['driver_sha256']
    board=h.real_path(plan['source']);assert board==ROOT/'.runs/native7-source-all-alias-controls-001/source/owned1007-transport.kicad_pcb'
    assert io.inventory(board.parent)==plan['source_hashes'];source_hashes[str(board.parent)]=plan['source_hashes']
    folder=base/label;folder.mkdir(mode=0o700);settings_raw=pv.read_bytes(original.parent/'settings.json',64*1024)
    assert p.sha(original.parent/'settings.json')==plan['settings_sha256']
    with (folder/'settings.json').open('xb') as stream:stream.write(settings_raw)
    output=runtime/'.runs'/(label+'-001');assert h.real_path(output,existing=False)==output and not os.path.lexists(output)
    current=copy.deepcopy(plan);current.update(runtime=str(runtime),runtime_manifest_sha256=NEW,tools=tools,output=str(output))
    p.save_json(folder/'protocol.json',current)
    entries.append(dict(case=label,protocol=str(folder/'protocol.json'),protocol_sha256=p.sha(folder/'protocol.json'),
        source_protocol=str(original),source_protocol_sha256=row['protocol_sha256'],Native_executed=False,
        enclosure_argv=['/usr/bin/env','-i',*[key+'='+value for key,value in sorted(environment.items())],str(ROOT/'.venv/bin/python'),'-B',str(encloser),'--protocol',str(folder/'protocol.json')]))
pins[str(encloser)]=p.sha(encloser);pins[str(driver)]=p.sha(driver);pins[str(Path(shared.__file__))]=p.sha(Path(shared.__file__))
record=dict(schema=1,kind='runtime056-existing-artifact-private-environment-two-CLI-plans-v1',runtime=str(runtime),source_head=HEAD,
    runtime_manifest_sha256=NEW,source_runtime=str(source),source_manifest_sha256=OLD,immutable_maps_build_source_engine_unchanged=True,
    immutable_files=len(new['immutable_files_sha256']),source_recipe_sha256=pins[str(source.parent/'preparation.json')],
    installation_receipt_sha256=pins[str(receipt_path)],installation_record_is_authoritative=False,
    doctor_ready=True,tools=tools,python_version=cfg['version'],private_environment=environment,protocols=entries,prerequisite_sha256=pins,
    prepared_only=True,Native_executed=False,actual_GUI=False,workflow_delivered=False,project_complete=False,
    sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,external_complete_exit_required=True,
    scope='Prospective fresh-root Native slices only, not transferred qualification. Original056 artifact/source/11-case provenance retained. Only manifest root changes; sameMac/account/basePython3.11.9/external dependency locations. No Native/engine/GUI/cleanOS/standalone/Windows/quality claim. Original protocol scope text retains its historical11-case dispatch description; these two unchanged enclosures each retain240s wall/fullCPU acceptance and255s runner bound. No aggregate future quota.',
    environment_scope='Private HOME/TMP/minimalPATH for query/doctor and recorded later enclosure argv; no owner/global app/environment/security/default-browser changes.',
    limits='90s preparation wall/fullCPU acceptance; query shared30s, doctor<=30s; existing1GiB RSS/512KiB log guards. Lead must retain complete external exit and require<=90s; late refusal retains partial namespace and is never reused.')
p.save_json(base/'preparation.json',record);record_pin=p.sha(base/'preparation.json')
assert h.owned_destination(owner)==base and h.owned_destination(private_owner)==private
assert pv._runtime_identity(source,implementation)==old_identity and pv._runtime_identity(runtime,implementation)==identity
for name,digest in pins.items():assert p.sha(Path(name))==digest
for name,hashes in source_hashes.items():assert io.inventory(Path(name))==hashes
for entry in entries:
    assert p.sha(Path(entry['protocol']))==entry['protocol_sha256']
    assert not os.path.lexists(Path(f.read_json(Path(entry['protocol']))['output']))
assert p.sha(base/'preparation.json')==record_pin and left()>0
print(json.dumps(dict(preparation=str(base/'preparation.json'),sha256=record_pin,runtime_manifest_sha256=NEW,doctor_ready=True,Native_executed=False,actual_GUI=False)))
