"""DRAFT ONLY: retain one fresh-root057 GUI091 delivery and an aborted control.

Port087/090 retention mechanics; reuse unchanged030 retain and042 dual-path
own_final. Read stored proof bytes only. Never run Native, production acceptance
readers, GUI or the late-metadata controller. Preserved preopen exports provide
the proof bytes; editor-modified live exports gain no renewed validity.
"""
from pathlib import Path
import ast,datetime,hashlib,json,os,stat,sys,time
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runs/runtime057 fresh install 001';BASE=RUNTIME/'.runs/gui-session091'
sys.path.insert(0,str(RUNTIME));sys.path.insert(1,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io,handoff as h,local_settings as local,config as c
from scripts import report_current_comparison as timing
HEAD='ac1a48c3b25b2217e0f8252e0e6da21905f144a4'
MANIFEST='b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51'
PREPARED='903642f70376af8e6dc8ff365183b244d48598ddc7ad9a90676e4507c96a4de8'
RETENTION=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
FINAL=ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py'
FIRST=BASE/'jobs/autorouter-gui-cf6247f87e384c68bda447765c7ca1f3'
LATE=BASE/'jobs/autorouter-gui-4baaf37eb6f34cb295f2843f19f69830'
COUNTS=('opens','blocking','warnings','exclusions')
# These fixed paths/hashes are filled once at draft authoring, never at execution.
PINS={
 ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py':'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',
 ROOT/'.runs/curate-gui-runtime042-081-recovery-deliveries-001.py':'340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',
 ROOT/'.runs/retain-gui087-delivery-001.py':'b4bf2b60b0816607f6f5bbbf460e186dada2d171a3f07d2172486146f5305d8d',
 ROOT/'.runs/curate-gui-runtime057-090-ordinary-001.py':'9e802a7eef9124042b06e921fbbadb56d06a5ca501b21d778defc48109b3acbb',
 ROOT/'.runs/retain-gui090-controls-deliveries-001.py':'079cf73b48aafb514639326b5313f5abc62218d338cb38595a912380ef5038b5',
 ROOT/'scripts/report_current_comparison.py':'0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e',
 ROOT/'scripts/native_cancellation.py':'a2cb0c5cf81bd33ea1beff1f0051c568e360d4bde71b3bbcac38a8ce4f19e591',
 ROOT/'.runs/gui091-observations-001.json':'af6f37a9ce216288bdfd31a7489c3311e4e920e10f295c8a18bf5a049fd985ca',
 ROOT/'.runs/gui091-observations-002.json':'24d10e2d4722b7951a5b1ed1dcba0825986cf109f497ffaa7179adf7b3f41b44',
 ROOT/'.runs/gui091-observations-003.json':'c543c5121e0d6bdff54215e4efd6e0e223c116c0c69f1164a687f0b92d9bfd2a',
 ROOT/'.runs/prepare-runtime057-install-existing-gui091.py':'af3fe93c2c9d9a68f3f8462dcb4b1bc2542abcdb5a7e0c8f7485eff4717c94b6',
 ROOT/'.runs/gui091-preopen-001.py':'da2c20d315eb896957a8cb9e6c732bda5a89145d25cf773f3ba6635cae99ee7d',
 ROOT/'.runs/gui091-preopen-late-metadata-001.py':'6fce1b0aa57cc22237eae17a2e1ce6006f561f16c8cb1f3697543cc88dd50dfe',
 ROOT/'.runs/gui091-late-metadata-001.py':'22cb84a6f80621d062d8af290f689d3b32b7f80a0f925af14d3b971b4cfb3ac6',
 ROOT/'evidence/runtime057-install-existing-001.json':'9d87a27e8a6329698b80e2e6f905361f40cb2391b70f9a54d7cf0f2917e6d006',
 ROOT/'evidence/gui-runtime057-090-ordinary-001.json':'6f55082fbc346a36a72a44bdc32e125c1b2707ea087cdde28120c7a56bc0cccf',
 ROOT/'evidence/gui-runtime057-090-controls-deliveries-001.json':'a4f4a2b3beb8a0dd7477d254a15fb800612a3d72f9956f1b45af67919aa48640',
 ROOT/'evidence/runtime057-native-milestone-001.json':'37620250ac71559915a80873be8d9cfc36c4d65853fd337fa5537e0eac904eb9',
 ROOT/'.runs/runtime057 fresh install 001/runtime-distribution.json':'b1d7066dff94e331f967afa89a4c0b3e2cfa10067324c3216996b31476898c51',
 ROOT/'.runs/prepare-runtime057-install-existing-gui091-001.log':'75bcf4a68d94c9f5388d4012d798d53b4ff44afaa8a421d0c4315fd4b1c2a850',
 ROOT/'.runs/prepare-runtime057-install-existing-gui091-001-time.log':'b75cde60dab16427fedc2a2fc11d4984fac2c94dab23c23b8d3f3b0ec6fd8022',
 ROOT/'.runs/gui091-preopen-001.log':'49995973e55917b001881d224767b09918cd14386bec0077804dd4baf0e48eae',
 ROOT/'.runs/gui091-preopen-001-time.log':'ff4009589740bc530a41bccdbcc5f07f8f06c7792e417e8fcf2e2dc736711c37',
 ROOT/'.runs/gui091-preopen-late-metadata-001.log':'408e0c61c97890de56035e114efbb79390fc9c33527b69812b4ab20b49b0366e',
 ROOT/'.runs/gui091-preopen-late-metadata-001-time.log':'7c758cce5d19c9732374eee77e7a78acf4c14dfbecf762f360b22cc14b5d7eea',
 ROOT/'.runs/gui091-late-metadata-001.log':'e8e284f7d369ae3cca68073b8c9a87df500f8b9250cef92d164e1de7332dee41',
 ROOT/'.runs/gui091-late-metadata-001-time.log':'029cb100bb5a96aae24d99754965d629ea51af324e5638d6b56449b3c41464bf',
 ROOT/'.runs/gui-runtime057-091-launch-001-time.log':'05c18e84fa618ada7abf23ff1282c5e4ac2f50b3950c558a0649afa61ace33c6',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/prepared-state.json':'903642f70376af8e6dc8ff365183b244d48598ddc7ad9a90676e4507c96a4de8',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/protocol-required-001.json':'7cc220b0de2051c643832c5cd25b692b0b1adc10ccbd4ff42d9eb69fc47fcbe9',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/preopen-001/preopen.json':'7e43153ca3c5335f95c1f6cf4748bddbe08f0316c8ebdcfbcd06c88142708c96',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/preopen-001/postopen-001.json':'9be8b92c0b0192e23303fb78c4b6f18c7474f7d43c5cc340561e3add72ffe63f',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/preopen-late-metadata-001/preopen.json':'5bb345e6b0e33d19368919393893e4ba012ff64467d5b733b10d8030f4b3fbb5',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/late-metadata-control-001/intervention.json':'71a546392836b8dbc02851360c25d28858d2232f5f402d21d3c32d1c25837299',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/jobs/autorouter-gui-cf6247f87e384c68bda447765c7ca1f3/route/result.json':'4108ff17105375ede8e30641c02d4cfc8f3e3807ec8f6996e5553b5d87eb7a7a',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/preopen-001/export/export.json':'ec5179281e1e49490775d272173e56012c2e4c5919d042fa75930cb8ab339d59',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/jobs/autorouter-gui-4baaf37eb6f34cb295f2843f19f69830/route/result.json':'497ff0c0fb9d7da495cf024137392a19b8039426e6302681a8fa7e35c5e26960',
 ROOT/'.runs/runtime057 fresh install 001/.runs/gui-session091/preopen-late-metadata-001/export/export.json':'2cac08807edfbe1b7fe77b4ff8e13deb5623dd315e24874b9dcc8cca837ea06f',
}
COMMAND_PINS={'autorouter-gui-cf6247f87e384c68bda447765c7ca1f3': {'choice.command.process.json': 'eee7d83ef87932c2b9985a09cd6504e08e4a272eef9e27736ed23cb1529ae1b3', 'export.command.process.json': '592e8a54722812f01791f7353166f243200377ddb586b0fec7182641f298223c', 'inspect-export-2ee9aa54a3724bb3a86b23d30e6c4b76.command.process.json': '100fa5aaa4b54a82e57de67d06a5a3c156224bdc5fa4a3a2727b5cd97950e64e', 'inspect-export-9a97fb19503b4d5994ec7b5c1ae234b6.command.process.json': '7fa9c7a9c160291c8c9aa46861289cc01bbe120c63f4fc6508475212673fe553', 'preview.command.process.json': 'f56d1a5ab1257fc702a29f404d9a5ce235cc3694958132dde934262a6284f253', 'review.command.process.json': '137a521638fa88002c753a1928b0d80f1a7c3d9e4721a26da31bd96827f63462', 'route.command.process.json': 'c11b035c6716edbba40ba0f45c0ee40cb215c926e7075ae7d29efc1a3b2fd285', 'verify_export.command.process.json': 'db25d895c1a8a506d2ac80531736a3d04c31f083af970816b7f1a6d961cbab03'}, 'autorouter-gui-4baaf37eb6f34cb295f2843f19f69830': {'choice.command.process.json': '4112fcdf095824cb94cbc31db5cd355beca29101db3469afe0894f19922a1637', 'export.command.process.json': '6c542abad9b4d21c8113ba1c7935ca767fab746eef728817aecded7c8cd36b18', 'inspect-export-db79a4281e694f3b922acb405eb65375.command.process.json': '4009cf083d334348b3ea1788d7cd48a8e5a3ad96a3e6f2c88f474a3e76dd4b40', 'preview.command.process.json': '574cc8b45b4412516cb414657f1b9af2986c7f1ce910dc8a33acaf99ca356f9d', 'review.command.process.json': '6deecbd9c21184b5e1c3d41763d00f6377bd36c8d8b5960711b70b9eee1efc74', 'route.command.process.json': '40fad9c28989331715753ea36973e417ea5538acf4730f984fc1a1887f5356b5', 'verify_export.command.process.json': '557ad0401ded386fa02d5b36840e71bcf4aa5cbce995a094d324f1cae10fb842'}}

def load_functions(path,names):
 nodes=[n for n in ast.parse(io.read_bytes(path,4*1024**2)).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert {n.name for n in nodes}==set(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path)+'::unchanged-shared','exec'),globals())

def main():
 global notes,refs,files,material,total
 start=time.monotonic();cpu0=time.process_time();stem='gui-runtime057-install091-delivery-001'
 notes=ROOT/'evidence'/(stem+'-notes');target=ROOT/'evidence'/(stem+'.json')
 assert PINS and COMMAND_PINS and not os.path.lexists(notes) and not os.path.lexists(target),'Fresh packet; preserve partial failures'
 assert c.ROOT==RUNTIME and c.NATIVE_VERSION=='10.0.7' and Path(p.__file__).resolve()==RUNTIME/'autorouter/pipeline.py'
 pins=dict(PINS);roots={};owners={};queue={};destinations={};costs={};command_rows=[]
 def expect(path,expected):
  path=Path(path);assert p.sha(path)==expected,str(path)
  if path in pins:assert pins[path]==expected,str(path)
  else:pins[path]=expected
 def bind(path,expected=None):
  path=h.real_path(path);raw=io.read_bytes(path,4*1024**2);digest=hashlib.sha256(raw).hexdigest()
  if expected is not None:assert digest==expected,str(path)
  expect(path,digest);return raw
 for path,pin in tuple(pins.items()):expect(path,pin)
 load_functions(RETENTION,('retain',));load_functions(FINAL,('read','own_final'))
 def pinned_read(path,expected=None):return json.loads(bind(path,expected))
 def watch(folder,expected=None):
  folder=h.real_path(folder);inventory=io.inventory(folder,max_bytes=64*1024**2)
  if expected is not None:assert inventory==expected,str(folder)
  if folder in roots:assert roots[folder]==inventory,str(folder)
  else:
   roots[folder]=inventory;owner={};h.capture_destination(owner,folder);owners[folder]=owner
  return inventory
 def add(path,name):
  path=h.real_path(path);name=Path(name)
  assert path.is_file() and ROOT in path.parents and not name.is_absolute() and not ({'..','.runs'}&set(name.parts))
  if path in queue:return
  assert name not in destinations,('Destination collision',name)
  queue[path]=name;destinations[name]=path
 def metadata(folder,name):
  folder=Path(folder)
  for relative in watch(folder):
   path=folder/relative;parts=Path(relative).parts
   if (len(parts)==1 and path.suffix in ('.json','.log','.net')) or (len(parts)==2 and parts[0].endswith('-input') and path.suffix=='.kicad_prl'):
    add(path,Path(name)/relative)
 prepared=pinned_read(BASE/'prepared-state.json',PREPARED);tools=prepared['tools']
 assert prepared['source_head']==HEAD and prepared['runtime_manifest_sha256']==MANIFEST and prepared['runtime']==str(RUNTIME)
 assert prepared['method']=='route' and prepared['actual_GUI_qualified'] is False and prepared['Native_executed'] is False
 assert p.tool_manifest()==tools
 for name,pin in tools['implementation_sha256'].items():expect(RUNTIME/name,pin)
 for name,pin in prepared['prerequisites_sha256'].items():expect(Path(name),pin)
 protocol=pinned_read(Path(prepared['protocol_required']),prepared['protocol_required_sha256'])
 source=h.real_path(prepared['source']);hashes=prepared['source_hashes'];original_source=h.real_path(prepared['original_source'])
 assert source==BASE/'project/owned1007-transport.kicad_pcb' and len(hashes)==4
 watch(source.parent,hashes);watch(original_source.parent,hashes)
 settings=dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
 assert prepared['settings']==pinned_read(Path(prepared['settings_path']),prepared['settings_sha256'])==settings
 journals=[pinned_read(ROOT/'.runs'/('gui091-observations-%03d.json'%n)) for n in (1,2,3)]
 j1,j2,j3=journals
 for journal in journals:
  assert journal['runtime']==str(RUNTIME) and journal['session']=='091' and journal['source_head']==HEAD and journal['manifest_sha256']==MANIFEST
  assert journal['actual_GUI'] is True and journal['human_review'] is False and journal['project_complete'] is False
 assert j2['previous']['sha256']==pins[ROOT/'.runs/gui091-observations-001.json'] and j3['previous']['sha256']==pins[ROOT/'.runs/gui091-observations-002.json']
 assert j1['workspace']==str(FIRST) and j1['prepared_state_sha256']==PREPARED and j1['settings']==settings and j1['source_hashes']==hashes
 for key in ('actual_newroot_GUI_vertical_slice','toolbar_launch','actual_preview','actual_route','rendered_Edge_F_B_before_after_images','all_findings_visible','actual_ack_accept_recorded','fresh_export_and_check_completed','actual_checked_export_manager_and_PCB_open','PCB_closed_without_save','export_manager_closed_using_FileCloseProject','stale_editor_modified_export_refused','positive_controls_cleared','source_unchanged'):assert j1[key] is True,key
 assert j1['full_GUI_qualified'] is False and j1['native']==[0,0,0,0] and j1['protected']==4 and j1['observed_unrouted']==0
 for key in ('actual_idle_GUI_closed_normally','actual_idle_manager_quit_normally','source_original_unchanged'):assert j3[key] is True,key
 dependencies=[];refs={};files=[];material=[];total=0
 dependency_paths=[ROOT/'evidence'/name for name in ('runtime057-install-existing-001.json','gui-runtime057-090-ordinary-001.json','gui-runtime057-090-controls-deliveries-001.json','runtime057-native-milestone-001.json')]
 dependency_indexes=set()
 for path in dependency_paths:
  data=pinned_read(path);index=ROOT/data['files_index']['path'];contents=pinned_read(index,data['files_index']['sha256']);dependency_indexes.add(index)
  for row in contents['files']:refs.setdefault(row['sha256'],row['path'])
  for row in contents['material']:refs.setdefault(row['sha256'],row['retained'])
  dependencies.append(dict(path=str(path.relative_to(ROOT)),sha256=pins[path],files_index=data['files_index'],scope='Owned rights/same-byte dedup and stated prerequisite scope only; no transfer of GUI or timing qualification.'))
 original=p.sx.read(source);deliveries=[];preopen={}
 for label,work,control in (('positive-installation',FIRST,BASE/'preopen-001'),('aborted-late-control',LATE,BASE/'preopen-late-metadata-001')):
  assert work.parent==BASE/'jobs';watch(work)
  pre=pinned_read(control/'preopen.json');before=control/'export';watch(before,pre['snapshot_hashes']);assert len(pre['snapshot_hashes'])==90
  preopen[label]=pre
  assert pre['workspace']==str(work) and pre['snapshot']==str(before) and pre['runtime']==str(RUNTIME) and pre['session']=='091'
  assert pre['source_head']==HEAD and pre['runtime_manifest_sha256']==MANIFEST and pre['source']==str(source) and pre['source_hashes']==hashes and pre['source_unchanged'] is True
  assert pre['actual_GUI_opening'] is False and pre['human_review'] is False and pre['route']['current'] is True and pre['export']['current'] is True and pre['export']['fresh_native_run_performed_by_check'] is False
  helper=ROOT/'.runs'/('gui091-preopen-001.py' if work==FIRST else 'gui091-preopen-late-metadata-001.py');expect(helper,pre['controller_sha256'])
  assert pinned_read(work/'settings.json',pre['settings_sha256'])==settings
  route=pinned_read(work/'route/result.json');exported=pinned_read(before/'export.json')
  assert route['accepted'] is True and route['invariants_unchanged'] is True and route['scope']=='partial_completion' and route['adapter']=='both' and route['engine_profile']=='standard' and route['scoring_variant'] is None
  assert route['routing_preferences']['effective']==settings and exported['export_accepted'] is True and exported['applied'] is False and exported['original_geometry_and_routing_unchanged'] is True
  assert route['budget_seconds']==route['cpu_budget_seconds']==exported['budget_seconds']==exported['cpu_budget_seconds']==90
  assert exported['inputs']['source']==route['source']==str(source) and exported['inputs']['receipt']==str(work/'route/result.json') and exported['inputs']['receipt_sha256']==pins[work/'route/result.json']
  assert route['candidate_sha256']==exported['candidate_sha256']
  protected=p.protected_for_record(route,original);assert len(protected)==4
  guide=pinned_read(work/'route/default-targets.json',route['default_target_transport']['sha256']);proofs={}
  for name,data,folder,actual in (('route',route,work/'route',work/'route'),('export',exported,before/'validation',work/'export/validation')):
   assert data['source_hashes']==hashes and data['tools']==tools and data['schematic_parity']=='checked by final native DRC'
   assert [data['native'][key] for key in COUNTS]==[0,0,0,0] and len(data['native']['ignored_checks'])==2
   candidate=folder/'candidate'/source.name;tree=p.sx.read(candidate)
   assert p.sha(candidate)==data['candidate_sha256'] and p.immutable(tree)==p.immutable(original) and all(item in p.routes(tree) for item in protected)
   proof=own_final(data,folder,actual,hashes,actual/'candidate'/source.name)
   audit=pinned_read(folder/'final-netclass-audit.json');binding=pinned_read(folder/'final-drc-binding.json');process=pinned_read(folder/'final-drc-process.json')
   assert audit['candidate_sha256']==data['candidate_sha256'] and audit['project_sha256']==hashes[source.with_suffix('.kicad_pro').name]
   assert audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True and audit['route_dimensions']['checked']['protected']==4
   assert audit['native_map_file_sha256']==p.sha(folder/'final-netclasses.json') and all(audit['default_targets'][key]==guide[key] for key in ('raw_nm','original_floors_nm','derived_nm'))
   prl=source.with_suffix('.kicad_prl').name
   assert process['local_settings_policy']=='job-owned-prl-immutable-v1'
   assert process['local_settings_protection']==dict(policy='mac-owned-prl-immutable-v1',present=True,path=str(actual/'final-drc-input'/prl),sha256=hashes[prl],flags_before=0,flags_during=stat.UF_IMMUTABLE,flags_restored=True,bytes_unchanged=True)
   assert binding['before'][prl]==hashes[prl] and local.check_current_metadata(folder/'final-drc-input'/prl)
   auxiliary=timing.improve_auxiliary(actual,data,dict(source=str(source),source_hashes=hashes))
   assert all(p.sha(folder/relative)==pin for relative,pin in auxiliary['files_sha256'].items())
   proofs[name]=dict(own_final=proof,Default_field_PRL_auxiliary=auxiliary,Native_counts=[0,0,0,0],protected_original_items=4,ignored_checks=data['native']['ignored_checks'])
   metadata(folder,Path(label)/name)
   add(folder/'candidate'/prl,Path(label)/name/'candidate'/prl)
  for name in ('review','review/plot-work','choice'):metadata(work/name,Path(label)/name)
  choice=pinned_read(work/'choice/choice.json');review=pinned_read(work/'review/review.json')
  assert choice['choice']=='accept' and choice['choice_recorded'] is True and choice['applied'] is False and choice['human_pcb_approval_observed'] is False
  assert choice['receipt_sha256']==review['receipt_sha256']==pins[work/'route/result.json'] and choice['review_sha256']==pins[work/'review/review.json'] and choice['validated_candidate_sha256']==route['candidate_sha256']
  live=watch(work/'export');changes=[dict(path=n,before=pre['snapshot_hashes'].get(n),after=live.get(n)) for n in sorted(set(pre['snapshot_hashes'])|set(live)) if pre['snapshot_hashes'].get(n)!=live.get(n)]
  if work==FIRST:
   post=pinned_read(control/'postopen-001.json',j1['postopen_sha256'])
   assert pins[control/'preopen.json']==j1['preopen_sha256'] and pins[work/'route/result.json']==j1['route_sha256'] and pins[before/'export.json']==j1['export_sha256'] and route['candidate_sha256']==j1['candidate_sha256']
   for key in ('snapshot_unchanged','source_unchanged','actual_GUI','actual_export_manager_and_PCB_opened','actual_PCB_closed_without_save','actual_manager_FileCloseProject','PCB_bytes_unchanged','positive_proof_not_renewed'):assert post[key] is True,key
   assert post['preopen_sha256']==pins[control/'preopen.json'] and post['current_export_inventory']==live and changes==post['changes'] and sorted(Path(row['path']).suffix for row in changes)==['.kicad_prl','.kicad_pro','.zip']
   assert post['observed_unrouted']==0 and p.sha(Path(exported['candidate']))==route['candidate_sha256']
  expected_commands=COMMAND_PINS[work.name];paths=sorted(work.glob('*.command.process.json'));assert {path.name for path in paths}==set(expected_commands)
  for path in paths:
   process=pinned_read(path,expected_commands[path.name]);log=path.with_name(path.name.replace('.process.json','.log'));bind(log)
   assert process['argv'][:4]==[str(RUNTIME/'.venv/bin/python'),'-B','-m','autorouter'] and process['cancel_requested'] is False and process['log_truncated'] is False and process['log_bytes']==log.stat().st_size
   stale=work==FIRST and str(log)==j1['stale_log'];assert process['exit_code']==(2 if stale else 0)
   if stale:assert pins[path]==j1['stale_process_sha256'] and pinned_read(log)==dict(current=False,reason='export inputs/runtime/evidence changed')
   row=dict(workspace=str(work),command=path.name,receipt_sha256=pins[path],log_sha256=pins[log],sample=process);command_rows.append((path,log,row))
   add(path,Path('commands')/work.name/path.name);add(log,Path('commands')/work.name/log.name)
  deliveries.append(dict(role=label,workspace=str(work),candidate_sha256=route['candidate_sha256'],route_sha256=pins[work/'route/result.json'],export_sha256=pins[before/'export.json'],preopen_sha256=pins[control/'preopen.json'],preserved_snapshot=str(before),own_final_bindings=proofs,metrics=route['metrics'],nested_route=dict(wall_seconds=route['wall_seconds'],CPU_seconds=route['total_cpu_seconds']),nested_export=dict(wall_seconds=exported['wall_seconds'],CPU_seconds=exported['total_cpu_seconds']),live_export_changes=changes,actual_GUI_opening_qualified=work==FIRST,current_Native_validity_renewed=False,scope='Stored preopen proof and actual first-job opening only; the second job is retained solely as the aborted control denominator.'))
 intervention_root=BASE/'late-metadata-control-001';intervention=pinned_read(intervention_root/'intervention.json',j2['intervention_sha256']);watch(intervention_root)
 assert j2['workspace']==str(LATE) and j2['control_passed'] is False and j2['mutation_performed'] is False and j2['retained_link_absent'] is True and j2['actual_GUI_pause_resumed'] is True and j2['actual_GUI_controls_recovered'] is True
 assert intervention['passed'] is False and intervention['error']=='AssertionError: ' and intervention['resume_requested'] is True and 'resume_error' not in intervention
 assert 'control_intervention_completed' not in intervention and 'mutation' not in intervention and 'CLI_exit_info' not in intervention and intervention['actual_GUI_outcome_observed'] is False and intervention['CallAfter_enqueued_before_mutation_proved'] is False
 assert intervention['preopen_sha256']==pins[BASE/'preopen-late-metadata-001/preopen.json'] and intervention['controller_sha256']==pins[ROOT/'.runs/gui091-late-metadata-001.py']
 positive_log=Path(intervention['inspection_log']);positive_process=positive_log.with_name(positive_log.name.replace('.log','.process.json'))
 assert pinned_read(positive_log,j2['positive_log_sha256'])==j2['positive_CLI_after_resume'] and pinned_read(positive_process,j2['CLI_receipt_sha256'])==j2['CLI_process']
 assert j2['CLI_process']['exit_code']==0 and j2['positive_CLI_after_resume']['current'] is True and j2['positive_CLI_after_resume']['export_accepted'] is True and j2['positive_CLI_after_resume']['applied'] is False and j2['positive_CLI_after_resume']['fresh_native_run_performed_by_check'] is False
 prl=LATE/'export/validation/final-drc-input'/source.with_suffix('.kicad_prl').name
 assert p.sha(prl)==hashes[prl.name] and prl.stat().st_nlink==j2['PRL_links']==1 and prl.stat().st_flags==j2['PRL_flags']==0 and not os.path.lexists(intervention_root/'retained-PRL-link.kicad_prl')
 for name in ('prepare-runtime057-install-existing-gui091-001','gui091-preopen-001','gui091-preopen-late-metadata-001','gui091-late-metadata-001'):
  path=ROOT/'.runs'/(name+'-time.log');value=timing.complete_cost(path);bind(path,value['time_log_sha256']);costs[name]=value;bind(ROOT/'.runs'/(name+'.log'))
 launcher_cost=timing.complete_cost(Path(j3['launch_interval']['source']));assert launcher_cost==j3['launch_interval'];bind(Path(launcher_cost['source']),launcher_cost['time_log_sha256']);costs['GUI091_launcher_interval']=dict(launcher_cost,scope=j3['accounting'])
 for path in (Path(__file__),ROOT/'LICENSE'):bind(path)
 for path in tuple(PINS)+tuple(Path(value['source']) for value in costs.values())+(Path(__file__),ROOT/'LICENSE'):
  if path in dependency_paths or path in dependency_indexes:continue
  if path.suffix in ('.json','.log','.py') or path.name=='LICENSE':add(path,Path('controls')/str(path.relative_to(ROOT)).replace('.runs/','retained-run/'))
 for path in (BASE/'prepare-launcher.log',BASE/'prepare-launcher-process.json'):
  bind(path);add(path,Path('setup')/path.name)
 add(Path(prepared['settings_path']),'settings/route-settings.json')
 for work in (FIRST,LATE):add(work/'settings.json',Path('settings')/(work.name+'.json'))
 for label,control in (('positive-installation',BASE/'preopen-001'),('aborted-late-control',BASE/'preopen-late-metadata-001')):add(control/'export/export.json',Path(label)/'export.json')
 metadata(BASE/'late-metadata-control-001','aborted-late-control/intervention')
 omitted=list({str((folder/relative).relative_to(ROOT)):dict(original=str((folder/relative).relative_to(ROOT)),sha256=pin,reason='Unselected owned CAD/transport/plots/ZIP/cache/raw material remains local; hash only.') for folder,inventory in roots.items() for relative,pin in inventory.items() if folder/relative not in queue}.values())
 def controls_fresh():
  for path,pin in pins.items():assert p.sha(path)==pin,str(path)
  for value in costs.values():assert p.sha(Path(value['source']))==value['time_log_sha256']
  for path,log,row in command_rows:assert p.sha(path)==row['receipt_sha256'] and p.sha(log)==row['log_sha256']
  for folder,inventory in roots.items():
   assert h.owned_destination(owners[folder])==folder and io.inventory(folder,max_bytes=64*1024**2)==inventory
   for relative in inventory:
    if Path(relative).suffix=='.kicad_prl':assert local.check_current_metadata(folder/relative)
  assert p.tool_manifest()==tools and prl.stat().st_nlink==1 and prl.stat().st_flags==0 and not os.path.lexists(intervention_root/'retained-PRL-link.kicad_prl')
 known=set(refs);planned=count=0;sealed={}
 for path in queue:
  raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf8');digest=hashlib.sha256(raw).hexdigest()
  expected=pins.get(path)
  if expected is None:
   found={inventory[str(path.relative_to(folder))] for folder,inventory in roots.items() if folder in path.parents and str(path.relative_to(folder)) in inventory};assert found=={digest}
  else:assert digest==expected
  sealed[path]=(len(raw),digest)
  if digest not in known:known.add(digest);planned+=len(raw);count+=1
 assert count<1998 and planned+sum(512+3*len(str(path))+3*len(str(name)) for path,name in queue.items())+len(json.dumps(omitted).encode())+512*1024<16*1024**2,'Split before writing; never raise caps'
 controls_fresh();notes.mkdir()
 for path,name in queue.items():retain(path,name)
 controls_fresh()
 for path,(size,digest) in sealed.items():assert path.stat().st_size==size and p.sha(path)==digest
 index=notes/'files.json';index_data=dict(schema=1,files=files,material=material,omitted_local_hash_only=omitted)
 summary=dict(schema=1,kind='runtime057-install091-single-actual-GUI-delivery-with-aborted-late-control-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_head=HEAD,runtime_manifest_sha256=MANIFEST,prepared_state_sha256=PREPARED,runtime=str(RUNTIME),session='091',accepted=False,actual_GUI_observed=True,actual_newroot_GUI_vertical_slice=True,workflow_delivered=True,actual_GUI_qualified=False,full_GUI_qualified=False,project_complete=False,human_review=False,physical_electrical_validation=False,
  source=str(source),original_source=str(original_source),source_hashes=hashes,source_unchanged=True,settings=settings,journals=[dict(path=str((ROOT/'.runs'/('gui091-observations-%03d.json'%n)).relative_to(ROOT)),sha256=pins[ROOT/'.runs'/('gui091-observations-%03d.json'%n)]) for n in (1,2,3)],deliveries=deliveries,
  actual_GUI_observations=j1,aborted_late_metadata_control=dict(observation=j2,intervention=intervention,control_passed=False,mutation_performed=False,retained_link_absent=True,actual_GUI_opening_qualified=False,CallAfter_already_queued_proved=False,failure_scalar='Unknown: retained assertions did not record which scalar failed; no identity/exit-status guard pass inferred.',method_stopped_no_retry=True),normal_close=dict(observation=j3,source_original_unchanged=True,absence_scope='Owned processes absent at the recorded snapshot only; no permanent absence claim.'),
  accounting=dict(command_samples=[row for _,_,row in command_rows],command_wall_sum_seconds=sum(row['sample']['wall_seconds'] for _,_,row in command_rows),command_CPU_seconds=None,complete_external_records=costs,whole_interactive_wall_seconds=None,whole_interactive_CPU_seconds=None,scope='Both jobs and the failed intervention remain in the denominator. Per-command and nested Native/route/review/export costs overlap; do not add them. Launcher interval1011.19wall/60.39CPU includes UI pauses and some descendants, not fullGUI accounting, and is not added to overlapping CLI/job costs. Setup/preopen/controller complete exits remain separately addressable. Authoring/AI/review/curation overhead is additional and partly unmetered, unknown not zero; no fair speed claim.'),
  dependencies=dependencies,pending=dict(exact_forced_queued_callback_timing=True,full_GUI_qualification=True),scope='One same-Mac/account fresh installed-root ordinary partial90/default-score/protected4 GUI slice: actual toolbar/Preview/Route/EdgeF+B/ackAccept/fresh export/check/KiCadPCB0unrouted/close without save/editor-metadata stale refusal. Separate late-metadata attempt aborted before mutation and resumed; it does not qualify GUI opening, metadata-boundary refusal or an already queued callback. Existing source/basePython3.11.9/external dependency paths; no all-combination, independent-user/cleanOS/standalone/Windows, electrical/human/quality/release/restoration claim. Stored proof only; no Native or production reader rerun by curator.',
  publication=dict(new_files=len(files),new_bytes=total,material_rows=len(material),file_cap=4*1024**2,packet_cap=16*1024**2,file_count_cap=2000,scope='Small owned metadata/log/net/PRL/controller/journal/time text only. No CAD, SVG/HTML/pixels/plots/ZIP, engines/apps, private or foreign bytes. Raw/preopen material remains Mac-only/outside010, not a full raw backup.'),curation=dict(sampled_wall_seconds=time.monotonic()-start,sampled_parent_CPU_seconds=time.process_time()-cpu0,complete_external_exit_not_included=True,Native_executed=False,production_readers_rerun=False))
 assert len(json.dumps(index_data,indent=2).encode())<4*1024**2 and len(json.dumps(summary,indent=2).encode())+1024<4*1024**2
 assert total+len(json.dumps(index_data,indent=2).encode())+len(json.dumps(summary,indent=2).encode())+1024<16*1024**2
 controls_fresh();p.save_json(index,index_data)
 summary['files_index']=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))
 controls_fresh();p.save_json(target,summary);controls_fresh()
 print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),actual_newroot_GUI_vertical_slice=True,full_GUI_qualified=False,Native_executed=False)))
if __name__=='__main__':main()
