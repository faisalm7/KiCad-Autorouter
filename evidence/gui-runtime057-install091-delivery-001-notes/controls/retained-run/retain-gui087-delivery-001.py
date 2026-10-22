"""Retain the completed new-root GUI slice using existing own-final/text helpers.

No Native solve, acceptance reader, GUI action or foreign CAD publication.
"""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/gui-runtime050-install087-delivery-001-notes'
target=ROOT/'evidence/gui-runtime050-install087-delivery-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
for name,pin,names in (
 ('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',('retain','cost')),
 ('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',('read','own_final'))):
    helper=ROOT/'.runs'/name;assert p.sha(helper)==pin
    nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
runtime=ROOT/'.runs/runtime050 fresh install 001';base=runtime/'.runs/gui-session087'
w=base/'jobs/autorouter-gui-b83efbdd85134cc7970e575959dc3099'
prep=read(base/'prepared-state.json');prepath=base/'preopen-001/preopen.json';pre=read(prepath)
assert p.sha(base/'prepared-state.json')=='f8776f10cdc34552c3ab53bef470d5678bd5bfb10c7711ab0edbc2d6bc8cebf6'
assert p.sha(runtime/'runtime-distribution.json')==prep['runtime_manifest_sha256']=='8fdf819606e2345b932139f1c16c330825fd8634caef1b611b5e105b97be22a4'
assert io.inventory(base/'project')==io.inventory(Path(prep['original_source']).parent)==prep['source_hashes']
assert p.sha(base/'route-settings.json')==prep['settings_sha256']
assert read(w/'settings.json')==prep['settings']
snapshot=Path(pre['snapshot']);assert io.inventory(snapshot)==pre['snapshot_hashes']
route=read(w/'route/result.json');export=read(snapshot/'export.json');choice=read(w/'choice/choice.json')
assert route['accepted'] is True and export['export_accepted'] is True and choice['choice']=='accept' and choice['choice_recorded'] is True
assert choice['applied'] is False and route['invariants_unchanged'] is True
assert route['tools']==export['tools']==prep['tools'] and route['candidate_sha256']==export['candidate_sha256']
own={}
for label,data,folder,actual in [('route',route,w/'route',w/'route'),('export',export,snapshot/'validation',w/'export/validation')]:
    assert [data['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,0,0]
    assert data['schematic_parity']=='checked by final native DRC' and len(data['native']['ignored_checks'])==2
    proof=own_final(data,folder,actual,prep['source_hashes'],data['candidate'])
    audit=read(folder/'final-netclass-audit.json')
    assert audit['candidate_sha256']==data['candidate_sha256'] and audit['route_dimensions']['checked']['protected']==4
    own[label]=dict(receipt_sha256=p.sha(w/'route/result.json' if label=='route' else snapshot/'export.json'),candidate_sha256=data['candidate_sha256'],own_final=proof,Native_counts=[0,0,0,0],protected_routes=4,ignored_checks=data['native']['ignored_checks'],Default_audit_sha256=p.sha(folder/'final-netclass-audit.json'))
current=io.inventory(w/'export',max_bytes=64*1024**2)
changed=[name for name in current if current[name]!=pre['snapshot_hashes'].get(name)]
assert set(changed)=={'validation/candidate/owned1007-transport.kicad_pro','validation/candidate/owned1007-transport.kicad_prl','validation/candidate/owned1007-transport-backups/owned1007-transport-2026-10-20_030640.zip'}
assert current['validation/candidate/owned1007-transport.kicad_pcb']==route['candidate_sha256']
failure='inspect-export-4a9a5cf67fde4e34b6b3444157a8254d'
q=read(w/(failure+'.command.process.json'));assert q['exit_code']!=0 and q['cancel_requested'] is False
assert 'changed' in (w/(failure+'.command.log')).read_text()
samples={}
for path in sorted(w.glob('*.command.process.json')):
    d=read(path);samples[path.name]=dict(wall_seconds=d['wall_seconds'],exit_code=d['exit_code'],cancel_requested=d['cancel_requested'])
observed=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_GUI=True,actual_newroot_GUI_vertical_slice=True,full_GUI_qualified=False,project_complete=False,human_review=False,workspace=str(w),observations=['Prepared toolbar launch and settings load retained in progress002; controls accessible again after owner reply.','Actual Preview: partial90, four existing routes protected. Actual Route: Native0/0/0/0, four protected,49mm/1via.','Actual Open preview in Microsoft Edge showed current job URL, saved metrics and both rendered F.Cu and B.Cu before/after. Owner Chrome unchanged.','Actual review acknowledgement and Accept intent recorded; Fresh export produced its own final Native proof.','Pre-editor export preserved and checked by shared production readers. Actual Open checked export loaded intended project; Tools > PCB Editor opened actual candidate. Screenshot showed6pads/1via/6segments/3nets/0unrouted and older-format notice. No board save.','Owned KiCad processes absent after close actions; GUI remains idle.','Actual editor changed exportPRO/PRL and added backupZIP, PCB unchanged. Subsequent GUI Open checked export refused changed evidence, cleared positive controls and review acknowledgement; no positive state adopted.'],export_changes=changed,source_unchanged=True,settings_unchanged=True,preopen_receipt_sha256=p.sha(prepath),live_export_after_editor_inventory=current)
journal=base/'GUI087-delivery-observation-001.json';assert not journal.exists();p.save_json(journal,observed)
for path in (journal,prepath,ROOT/'.runs/gui087-preopen-001.py',ROOT/'.runs/gui087-preopen-001.log',ROOT/'.runs/gui087-preopen-001-time.log',Path(__file__)):
    retain(path,Path('controls')/path.name)
for directory,label in ((w,'job'),(snapshot,'pre-editor-export')):
    for rel in io.inventory(directory,max_bytes=64*1024**2):
        if set(Path(rel).parts)&{'kicad-cache','kicad-config','kicad-documents','engine-config','tmp','__pycache__'}:continue
        path=directory/rel
        if path.suffix in ('.json','.log'):retain(path,Path(label)/rel)
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='runtime050-install087-actual-Native-and-single-GUI-vertical-slice-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=str(runtime),source_head=prep['source_head'],runtime_manifest_sha256=prep['runtime_manifest_sha256'],actual_GUI=True,actual_newroot_GUI_vertical_slice=True,full_GUI_qualified=False,workflow_delivered=True,production_admitted=False,accepted=False,project_complete=False,human_review=False,dependencies=[dict(path=name,sha256=p.sha(ROOT/name)) for name in ('evidence/runtime050-install-existing-001.json','evidence/gui-runtime050-install087-progress-002.json')],observations=observed,own_final=own,CLI_process_wall_samples=samples,accounting=dict(preopen_additional=cost(ROOT/'.runs/gui087-preopen-001-time.log'),nested_route=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),nested_export=dict(wall_seconds=export['wall_seconds'],CPU_seconds=export['total_cpu_seconds']),interpretation='Nested route/export and CLI samples overlap; count once. Complete interactive wall/CPU, authoring/review unknown additional, notzero. Curation separately timed, no Native solve by curator.'),scope='One same-Mac new-root ordinary partial90/protected4 installation GUI vertical slice. No transfer of all GUI086 roles, exact queuedCallAfter interval, optimizer comparison, standalone/cleanOS/relocation, Windows, human/electrical/physical or broad routing claim. Original prepared-only CLI packet immutable.',backup='Owned small metadata only; CAD/plots/ZIP and newer fullraw remain Mac-only/outside010. No full-restoration claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),actual_newroot_GUI_vertical_slice=True,full_GUI_qualified=False)))
