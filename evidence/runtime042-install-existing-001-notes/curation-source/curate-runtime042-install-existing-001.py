"""Additive installed-existing042 Native + one actual GUI082 vertical slice.

DRAFT: no Native, central readers, tests, GUI or tool execution by curation.
Requires the frozen final five-field GUI journal, never an active journal.
"""
from pathlib import Path
import argparse,ast,datetime,hashlib,json,math,os,re,resource,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--journal-sha256',required=True)
args=parser.parse_args();assert re.fullmatch('[0-9a-f]{64}',args.journal_sha256)
assert args.journal_sha256=='c416af5b0f317e9d9621175038da1e2cb8a1685b8ab0eba55e5ba2309e88f49d'
START=time.monotonic();CPU0=resource.getrusage(resource.RUSAGE_SELF)
HEAD='82aaa3b750007ef2ffaafd367ffcb718aa93865e'
MANIFEST='0fa1f13c4a43385d2d0b513c7c84fb89bb6370eb9962531018f0d1ccbfd6f039'
OLD_MANIFEST='1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e'
runtime=ROOT/'.runs/runtime042 fresh install 001';original=ROOT/'.runs/runtime-directory-042/runtime'
base=ROOT/'.runs/runtime042-install-existing-qualification-001';session=runtime/'.runs/gui-session082'
journal_path=base/'GUI082-observations-final-001.json'
assert journal_path.is_file() and p.sha(journal_path)==args.journal_sha256
journal=f.read_json(journal_path)
assert journal['actual_newroot_GUI_vertical_slice']is True and journal['no_save']is True
assert journal['job']=='autorouter-gui-611f6245c9c74b73817fb85276ba72c8'
for key in ('preopen_receipt_sha256','postopen_receipt_sha256'):
    assert type(journal[key])is str and re.fullmatch('[0-9a-f]{64}',journal[key])
notes=ROOT/'evidence/runtime042-install-existing-001-notes';output=ROOT/'evidence/runtime042-install-existing-001.json'
assert not os.path.lexists(notes) and not os.path.lexists(output)
refs={};files=[];material=[];total=0;dependencies=[];queue=[];omitted=[]
# Only the explicit current042 Native and linked081 indexes can provide reuse.
for name,pin in [('runtime042-native-milestone-001','7faf3fa21c08073ede6bbb1825b15633c25997a7440b6da37dc2e0edac140d4b'),
                 ('gui-runtime042-081-functional-summary-001','b658e4d480defb9132365c2299cc89f3af9ba3244c44d712828ecd6bc4ba0315')]:
    path=ROOT/'evidence'/(name+'.json');assert p.sha(path)==pin;data=f.read_json(path)
    assert data['source_head']==HEAD and data['runtime_manifest_sha256']==OLD_MANIFEST
    indexes=[data['files_index']] if 'files_index' in data else []
    for linked in data.get('packets',{}).values():
        linked_path=Path(linked['path']);assert linked_path.parent==ROOT/'evidence' and p.sha(linked_path)==linked['sha256']
        linked_data=f.read_json(linked_path);assert linked_data['files_index']==linked['files_index']
        indexes.append(linked['files_index'])
    for index in indexes:
        assert p.sha(ROOT/index['path'])==index['sha256'];idx=f.read_json(ROOT/index['path'])
        for row in idx.get('files',[]):refs.setdefault(row['sha256'],row['path'])
        for row in idx.get('material',[]):refs.setdefault(row['sha256'],row['retained'])
    dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pin,files_indexes=indexes))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
comparison=ROOT/'.runs/curate-runtime042-current-comparison-001.py'
own_source=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
assert p.sha(comparison)=='d6d99941d9afe8d6a81e862d406d66b72f39fdf1c5241dc6cb7403154a61d974' and p.sha(own_source)=='340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9'
for source,names in [(helper,['retain','tree','cost']),(comparison,['complete_cost','counts','delivered_proof']),
                     (own_source,['read','own_final'])]:
    functions=[n for n in ast.parse(source.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert [n.name for n in functions]==names
    exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),globals())
keys=('opens','blocking','warnings','exclusions')
real_retain=retain
def retain(path,name):
    path=Path(path);assert path.is_file() and not path.is_symlink() and ROOT in path.parents
    queue.append((path,Path(name)))
plan=read(base/'protocol.json');outer=read(base/'enclosure/result.json');preparation=read(base/'preparation.json')
out=Path(plan['output']);result=read(out/'result.json');workflow=read(out/'workflow/result.json');cli=Path(result['workspace'])
assert plan['runtime']==str(runtime) and plan['source_head']==HEAD
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']==MANIFEST
assert p.sha(original/'runtime-distribution.json')==OLD_MANIFEST
old=read(original/'runtime-distribution.json');assert read(runtime/'runtime-distribution.json')==dict(old,root=str(runtime))
assert preparation['setup_completed']is True and preparation['immutable_maps_unchanged']is True
assert preparation['runtime_manifest_sha256']==MANIFEST and preparation['source_manifest_sha256']==OLD_MANIFEST
assert all(p.sha(runtime/name)==pin and p.sha(original/name)==pin for name,pin in old['immutable_files_sha256'].items())
assert outer['passed']is True and outer['status']=='completed' and outer['accepted']is False
assert outer['protocol_sha256']==result['protocol_sha256']==p.sha(base/'protocol.json')
assert outer['child_receipt']==str(out/'result.json') and outer['child_sha256']==p.sha(out/'result.json')
assert out==runtime/'.runs/clean-env-partial-delivery-001' and f.evidence_inventory(out)==outer['completed_material']
assert result['controls_passed']is True and result['workflow_delivered']is True and result['status']=='completed'
assert result['accepted']is False and result['production_admitted']is False and result['actual_GUI']is False
assert result['doctor']['ready']is True and result['Native_counts']==[0,0,0,0]
assert result['protected_routes']==4 and result['all_four_original_routes_preserved']is True
assert workflow['workflow_delivered']is True and workflow['settings']==plan['settings']==result['settings']
assert cli.parent==out/'workflow' and cli.name.startswith('autorouter-gui-')
assert [row['stage'] for row in workflow['processes']]==['preview','route','review','choice','export','verify_export']
for row in workflow['processes']:
    assert row['process']['exit_code']==0 and row['process']['cancel_requested']is False and row['process']['log_truncated']is False
for process in [outer['process']]+[row['process'] for row in result['processes']]+[row['process'] for row in preparation['processes']]:
    assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']is True and process['log_truncated']is False
hashes=plan['source_hashes'];source=Path(plan['source']);assert io.inventory(source.parent)==hashes
assert result['source_hashes']==workflow['source_hashes']==hashes and result['tools']==workflow['tools']==plan['tools']
allowed=[cli];cli_proofs={}
for label,receipt,is_export in [('route',cli/'route/result.json',False),('export',cli/'export/export.json',True)]:
    proof=delivered_proof(receipt,export=is_export,source_hashes=hashes,allowed=allowed);data=read(receipt)
    folder=receipt.parent/'validation' if is_export else receipt.parent
    proof['own_final']=own_final(data,folder,folder,hashes,data['candidate']);cli_proofs[label]=proof
    assert proof['Native_counts']==[0,0,0,0] and data['tools']==plan['tools']
assert cli_proofs['route']['protected_count']==4
assert cli_proofs['route']['candidate_sha256']==cli_proofs['export']['candidate_sha256']==result['candidate_sha256']
assert p.sha(cli/'route/result.json')==result['route_receipt_sha256'] and p.sha(cli/'export/export.json')==result['export_receipt_sha256']
prepared=read(session/'prepared-state.json');gui=session/'jobs'/journal['job']
assert prepared['runtime_manifest_sha256']==MANIFEST and prepared['source_head']==HEAD and prepared['tools']==plan['tools']
assert prepared['source_hashes']==hashes and io.inventory(session/'project')==hashes
pre_path=session/'preopen-001.json';post_path=session/'postopen-001.json'
assert p.sha(pre_path)==journal['preopen_receipt_sha256'] and p.sha(post_path)==journal['postopen_receipt_sha256']
pre=read(pre_path);post=read(post_path);before=Path(pre['snapshot']);after=Path(post['snapshot'])
assert before==session/'preopen-snapshot-001' and after==session/'postopen-snapshot-001'
assert pre['workspace']==post['workspace']==str(gui) and pre['role']==post['role']=='positive'
assert pre['route']['current']is True and pre['export']['current']is True
assert pre['source_unchanged']is True and post['source_unchanged']is True and post['candidate_PCB_unchanged']is True
assert io.inventory(before)==pre['snapshot_hashes'] and io.inventory(after)==post['snapshot_hashes']==io.inventory(gui/'export')
assert pre['source_hashes']==hashes and p.sha(before/'export.json')==pre['export_receipt_sha256']
route=read(gui/'route/result.json');exported=read(before/'export.json')
assert route['accepted']is True and exported['export_accepted']is True and exported['applied']is False
assert route['invariants_unchanged']is True and exported['original_geometry_and_routing_unchanged']is True
assert route['source_hashes']==exported['source_hashes']==hashes and route['tools']==exported['tools']==prepared['tools']
assert route['source']==exported['inputs']['source']==prepared['source'] and Path(route['source']).parent==session/'project'
assert p.sha(gui/'settings.json')==pre['settings_sha256'] and read(gui/'settings.json')==plan['settings']
assert all(step['cleanup_complete']is True and step['log_truncated']is False for data in (route,exported) for step in data['steps'])
assert route['schematic_parity']==exported['schematic_parity']=='checked by final native DRC'
assert counts(route['native'])==counts(exported['native'])==[0,0,0,0]
assert len(route['protected_route_import']['matches'])==4 and route['budget_seconds']==exported['budget_seconds']==90
assert exported['inputs']['receipt_sha256']==p.sha(gui/'route/result.json')
assert route['candidate_sha256']==exported['candidate_sha256']
choice=read(gui/'choice/choice.json');assert choice['choice']=='accept' and choice['applied']is False
assert choice['receipt_sha256']==p.sha(gui/'route/result.json') and choice['human_pcb_approval_observed']is False
# Reuse own_final with separate actual and snapshot folders. Raw receipts and
# embedded original paths are never rewritten; modified GUI export is NOT read.
gui_route_final=own_final(route,gui/'route',gui/'route',hashes,route['candidate'])
gui_export_final=own_final(exported,before/'validation',gui/'export/validation',hashes,exported['candidate'])
relative=Path(exported['candidate']).relative_to(gui/'export')
assert p.sha(before/relative)==p.sha(after/relative)==exported['candidate_sha256']
changed={key:dict(before=pre['snapshot_hashes'].get(key),after=post['snapshot_hashes'].get(key))
    for key in sorted(set(pre['snapshot_hashes'])|set(post['snapshot_hashes']))
    if pre['snapshot_hashes'].get(key)!=post['snapshot_hashes'].get(key)}
assert changed==post['changed']
fullbase=ROOT/'.runs/full-integration-188';full=read(fullbase/'execution.json');fullplan=read(fullbase/'protocol.json')
assert full['passed']is True and full['sources_unchanged']is True
assert full['process']['status']=='success' and full['process']['exit_code']==0 and full['process']['cleanup_complete']is True
assert full['process']['log_truncated']is False
full_log=Path(full['process']['log']);assert p.sha(full_log)==full['log_sha256']
assert re.search(r'Ran 2330 tests\b',io.read_bytes(full_log,4*1024**2).decode())
assert all(p.sha(ROOT/name)==pin for name,pin in fullplan['source_sha256'].items())
for path in base.iterdir():
    if path.is_file() and path.name!='GUI082-observations-live.json':retain(path,Path('qualification')/path.name)
tree(base/'enclosure',Path('qualification/enclosure'));tree(fullbase,Path('full188'))
for path in out.iterdir():
    if path.is_file():retain(path,Path('Native-parent')/path.name)
for name in ('workflow','enclosure'):tree(out/name,Path('Native-parent')/name)
tree(gui,Path('GUI082/job'));tree(before,Path('GUI082/preopen'));tree(after,Path('GUI082/postopen'))
for name in ('prepared-state.json','route-settings.json','protocol-required-001.json','prepare-launcher.log','prepare-launcher-process.json','preopen-001.json','postopen-001.json'):
    retain(session/name,Path('GUI082/preparation-opening')/name)
tree(session/'project',Path('GUI082/pristine-source'));retain(Path(prepared['launcher']),'GUI082/Launch Autorouter.command')
for path in [runtime/'runtime-distribution.json',original/'runtime-distribution.json',runtime/'.venv/pyvenv.cfg',runtime/'.runs/install-existing-runtime-001.json']:
    retain(path,Path('runtime-installation')/('original-runtime-distribution.json' if path.parent==original else path.name))
controllers=['install-existing-runtime042-prepare-001.py','qualify-runtime042-install-existing-environment-001.py',
    'run-runtime042-install-existing-environment-001.py','prepare-runtime042-install-existing-gui082.py',
    'gui082-boundary-via-shared081-001.py','gui081-preopen-001.py','gui081-postopen-001.py',
    'run-full-integration-188.py','install-existing-runtime042-prepare-001.log','install-existing-runtime042-prepare-001-time.log',
    'prepare-runtime042-install-existing-gui082.log','prepare-runtime042-install-existing-gui082-time.log',
    'full-integration-188-controller.log','full-integration-188-time.log']
for name in controllers:retain(ROOT/'.runs'/name,Path('controllers-costs')/name)
for key in ('controller','outer_controller_path','driver_path','enclosure_path','installer_path'):
    path=Path(plan[key]);retain(path,Path('controllers')/path.name)
for path in (helper,comparison,own_source,Path(__file__),ROOT/'LICENSE'):
    retain(path,Path('curation-source')/path.name)
timings=dict(full188=complete_cost(ROOT/'.runs/full-integration-188-time.log'),
    setup=complete_cost(ROOT/'.runs/install-existing-runtime042-prepare-001-time.log'),
    Native_parent=complete_cost(base/'outer-time.log'),GUI_preparation=complete_cost(ROOT/'.runs/prepare-runtime042-install-existing-gui082-time.log'))
for name in ('preopen','postopen'):
    path=base/('gui082-'+name+'-time.log');timings['GUI_'+name]=complete_cost(path) if path.is_file() else None
assert timings['full188']['wall_seconds']==388.92 and timings['full188']['CPU_seconds']==373.98
assert timings['setup']['wall_seconds']==1.28 and timings['setup']['CPU_seconds']==0.74
assert timings['Native_parent']['wall_seconds']==38.26 and timings['Native_parent']['CPU_seconds']==34.95
known=set(refs);planned_bytes=0;planned_files=0;expected={};filtered=[]
for path,name in queue:
    raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest()
    if path.suffix.lower() in {'.zip','.png','.jpg','.jpeg','.gif','.webp','.bmp','.pyc','.jar','.so','.dylib'} or b'\0' in raw:
        omitted.append(dict(original=str(path.relative_to(ROOT)),bytes=len(raw),sha256=digest,reason='ZIP/pixels/binary/cache remain Mac-only; digest only.'));continue
    raw.decode('utf8')
    if digest not in known:known.add(digest);planned_bytes+=len(raw);planned_files+=1
    filtered.append((path,name));expected[str(path)]=(len(raw),digest)
assert planned_bytes<16*1024**2-16384 and planned_files<1998,(planned_bytes,planned_files)
# Preflight completes before the first exclusive public payload write.
notes.mkdir(mode=0o700)
for path,name in filtered:
    assert (path.stat().st_size,p.sha(path))==expected[str(path)];real_retain(path,name)
scope='Fresh-root installation of the still-bound042 artifact on the SAME Mac/account and existing base Python/KiCad/Java locations. The manifest differs only in root; every immutable source/build/version/lock/engine pin remains original. A new --copies --without-pip venv and isolated launcher were prepared. Installation record is non-authoritative and is not Native acceptance.\n\nActual doctor plus six-stage CLI delivery has its own Route/export Native/refill/fullSCH/original/protected4 proof, all Native counts0. GUI082 is ONE actual ordinary new-root vertical slice: its frozen lead journal is observation authority, not human PCB approval. GUI preopen snapshot retains the own fresh export proof with an explicit original-export-root to snapshot-relative mapping; receipts are not rewritten. After editor opening without save, source and PCB remain unchanged while metadata/new ZIP changed. Postopen bytes are observations only, never renewed Native/current-export validity. No production reader or Native was rerun by curation.\n\nFull188 and setup/CLI/GUI preparation/pre/post measurements are separate. Nested process/Native samples are included in their parent envelopes, not added twice. Whole interactive GUI wall/CPU and unmetered authoring/review costs remain unknown, not zero. Standard/B1 and all constraints remain unchanged. This is not an effectiveness gain, family expansion, full-GUI/release completeness, cleanOS/new-account/dependency-relocation/standalone/Windows/human/physical/electrical qualification.\n\nOnly bounded essential owned text proof and exact approved042 Native/081 references are retained. No JAR, binary executable, application, environment, cache/preference, pixel or ZIP payload is published; pyvenv.cfg and the text launcher are retained. Exact omitted hashes remain recorded. New raw remains on this Mac outside010; restoration capacity is still blocked, and this packet is not a full raw backup.\n'
scope_path=notes/'SCOPE.md';scope_raw=scope.encode();scope_path.open('xb').write(scope_raw)
sha=hashlib.sha256(scope_raw).hexdigest();total+=len(scope_raw)
files.append(dict(path=str(scope_path.relative_to(ROOT)),bytes=len(scope_raw),sha256=sha))
material.append(dict(original='authored:SCOPE.md',retained=str(scope_path.relative_to(ROOT)),bytes=len(scope_raw),sha256=sha))
assert total<16*1024**2 and len(files)<2000
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted_binary_payloads=omitted))
u=resource.getrusage(resource.RUSAGE_SELF)
summary=dict(schema=1,kind='runtime042-install-existing-actual-Native-and-single-GUI-vertical-slice-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,project_complete=False,human_review=False,
    source_head=HEAD,original_runtime_manifest_sha256=OLD_MANIFEST,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,
    immutable_files=len(old['immutable_files_sha256']),immutable_map_build_lock_version_unchanged=True,
    full188=dict(passed=True,tests=2330,skips=1,complete_cost=timings['full188']),complete_costs=timings,
    Native=dict(doctor_ready=True,six_stage_delivery=True,counts=[0,0,0,0],protected4=True,proofs=cli_proofs,
        protocol_sha256=p.sha(base/'protocol.json'),parent_sha256=p.sha(out/'result.json'),outer_sha256=p.sha(base/'enclosure/result.json')),
    actual_newroot_GUI_vertical_slice=True,actual_GUI_fully_qualified=False,GUI_job=journal['job'],journal_sha256=args.journal_sha256,
    GUI_proof=dict(route_final=gui_route_final,export_final_before_open=gui_export_final,Native_counts=[0,0,0,0],protected_count=4,ignored_checks=exported['native']['ignored_checks'],
        candidate_sha256=exported['candidate_sha256'],preopen_sha256=p.sha(pre_path),postopen_sha256=p.sha(post_path),
        original_export_root=str(gui/'export'),preopen_snapshot_root=str(before),path_mapping='snapshot / original_relative_path; raw receipts and embedded paths unchanged',
        preopen_files=len(pre['snapshot_hashes']),postopen_files=len(post['snapshot_hashes']),postopen_changes=changed,
        no_save=True,PCB_source_unchanged=True,renewed_postopen_Native_or_current_reader_validity_claimed=False),
    interactive_GUI_complete_wall_seconds=None,interactive_GUI_complete_CPU_seconds=None,
    accounting='Complete external measurements authoritative; nested samples overlap. Full188/setup/CLI/GUI preparation/snapshot work distinct; whole interactive GUI and unmetered costs unknown, not zero.',
    dependencies=dependencies,source_rights='Owned GPL code and four-file fixture; exact prior fixture/settings notices through explicit042 Native/081 indexes.',
    backup_scope='Essential text only; new full raw Mac-only outside010; restore capacity blocked.',
    retention=dict(max_file_bytes=4*1024**2,max_packet_payload_bytes=16*1024**2,max_new_files=2000,
        new_files=len(files),new_bytes=total,material_rows=len(material),omitted_binary_rows=len(omitted),preflight_complete=True),
    curation_sample=dict(wall_seconds=time.monotonic()-START,CPU_seconds=(u.ru_utime+u.ru_stime)-(CPU0.ru_utime+CPU0.ru_stime),complete_external_unknown=True),
    files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index)))
p.save_json(output,summary)
assert p.sha(journal_path)==args.journal_sha256 and p.sha(runtime/'runtime-distribution.json')==MANIFEST
assert f.evidence_inventory(out)==outer['completed_material'] and io.inventory(source.parent)==hashes
assert p.sha(original/'runtime-distribution.json')==OLD_MANIFEST
assert all(p.sha(runtime/name)==pin and p.sha(original/name)==pin for name,pin in old['immutable_files_sha256'].items())
assert io.inventory(before)==pre['snapshot_hashes'] and io.inventory(after)==post['snapshot_hashes']
assert io.inventory(session/'project')==hashes
for row in material:
    raw=io.read_bytes(ROOT/row['retained'],4*1024**2);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
print(json.dumps(dict(packet=str(output.relative_to(ROOT)),sha256=p.sha(output),index_sha256=p.sha(index),new_files=len(files),new_bytes=total,material_rows=len(material))))
