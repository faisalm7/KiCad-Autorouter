"""Static retention of completed owned escape controls, never admission.

No Native/engine/acceptance reader runs. Shared retention and own-final helpers
verify existing bytes. CAD/netlists/plots/cache remain local with hashes only.
"""
from pathlib import Path
import ast, datetime, hashlib, json, os, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx, chain_proposals as cp
notes=ROOT/'evidence/qfn-escape-native-prerequisites-002-notes'
target=ROOT/'evidence/qfn-escape-native-prerequisites-002.json'
review_path=ROOT/'.runs/qfn-escape-native-prerequisites-result-review-002.json'
assert not notes.exists() and not target.exists() and not review_path.exists()
refs={};files=[];material=[];total=0;helpers=[]
for name,pin,names in (
 ('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',('retain','cost')),
 ('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',('read','own_final'))):
 helper=ROOT/'.runs'/name;assert p.sha(helper)==pin;helpers.append(helper)
 nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
dependency=ROOT/'evidence/runtime050-native-milestone-002.json'
assert p.sha(dependency)=='1d0d2019d5505f1fad0134cc2163b3337ce227e1b8d841c8c3c8a81e21a94934'
index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
previous=ROOT/'evidence/qfn-escape-native-prerequisites-001.json'
assert p.sha(previous)=='9b9f265d14fe271b3cad5373c62c037d002e10047f18ce719eeb2df1a1da751e'
previous_index=read(previous)['files_index'];assert p.sha(ROOT/previous_index['path'])==previous_index['sha256']
for row in read(ROOT/previous_index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
prep=ROOT/'.runs/qfn-escape-controls-preparation-002';output=ROOT/'.runs/qfn-escape-controls-native-002'
outer=ROOT/'.runs/qfn-escape-controls-native-002-enclosure';protocol=prep/'protocol.json'
assert p.sha(protocol)=='9aa58882194df68abfc673cb900bc3e28d2f28a654d2ce1ebdafcdec93a1af7d'
plan=read(protocol);result=read(output/'result.json');enclosed=read(outer/'result.json');process=read(outer/'process.json')
assert plan['kind']=='owned-native-escape-stub-prerequisites-v1' and plan['cases']==['positive','outside_short','seed_width_mutation']
assert Path(plan['output'])==output and Path(plan['enclosure'])==outer and Path(plan['preparation'])==prep
assert result['protocol_sha256']==enclosed['protocol_sha256']==p.sha(protocol)
assert enclosed['child_sha256']==p.sha(output/'result.json')=='e675708b7660b466d9be63b4cfe764869fccdb58cc280b00cb04ea02817aeeb3'
assert result['status']=='completed' and result['passed'] is True and not result['unattempted']
assert enclosed['passed'] is True and enclosed['process']==process
assert all(result[key] is False for key in ('accepted','production_admitted','routing_accepted','engine_executed'))
assert enclosed['accepted'] is False and enclosed['production_admitted'] is False
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
assert Path(process['cwd'])==outer and Path(process['log'])==outer/'command.log'
assert process['log_bytes']==(outer/'command.log').stat().st_size
runtime=Path(plan['runtime']);assert runtime==ROOT/'.runs/runtime-directory-050/runtime'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
assert plan['tools']==result['tools'] and plan['tools']['kicad']=='10.0.7'
for name,pin in plan['code_sha256'].items():assert p.sha(ROOT/name)==pin
for name,pin in plan['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
for name,pin in plan['tools']['files'].items():assert p.sha(Path(name))==pin
source=Path(plan['source']);hashes=plan['source_hashes']
assert io.inventory(source.parent)==hashes==result['source_hashes']
assert p.sha(prep/'seed-plan.json')==plan['seed_plan_sha256'];seed=read(prep/'seed-plan.json')
assert seed['generated_count']==16 and seed['protected_count']==1 and seed['targets']==plan['targets']
assert seed['accepted'] is False and seed['routing_accepted'] is False
original=sx.read(source);protected=[r for r in p.routes(original) if p.locked(r)]
assert len(p.routes(original))==18 and len(protected)==1
assert sum(len(sx.children(fp,'pad')) for fp in sx.children(original,'footprint'))==35
assert seed['policy']=='source-orthogonal-perimeter-escape-seed-v2'
center_skips=[row for row in seed['skips'] if row['reason']=='unchanged_square_center_solid_zone_pad'];assert len(center_skips)==1
assert any(len(row)==4 and row[2]=='user' and sx.unquote(row[1])=='F.Paste' and sx.unquote(row[3])=='OwnedPasteDisplay' for row in sx.one(original,'layers')[1:])
# Reuse the controller's exact completed-material definition; no new census API.
helper=ROOT/'experiments/hfe_original_native_v1/driver.py';helpers.append(helper)
assert p.sha(helper)==plan['code_sha256'][str(helper.relative_to(ROOT))]
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='material']
assert len(nodes)==1;LIMIT=128*1024**2
saved_material=material
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared-material','exec'),globals())
completed_material=material;material=saved_material
assert completed_material(output)==result['completed_evidence']
rows=[];own={};flags=[];route_maps={}
for name,row in result['cases'].items():
 folder=output/name;candidate=Path(row['candidate']);assert candidate==folder/'candidate'/source.name
 assert row['control_passed'] is True and p.sha(candidate)==row['candidate_sha256']
 tree=sx.read(candidate)
 assert p.immutable(tree)==p.immutable(original) and all(r in p.routes(tree) for r in protected)
 route_maps[name]={sx.unquote(sx.one(r,'uuid')[1]):r for r in p.routes(tree)}
 assert len(route_maps[name])==len(p.routes(tree))
 for item in seed['seeds']:
  route=route_maps[name][item['segment_uuid']]
  assert list(cp.xy(sx.one(route,'start')))==item['start_nm'] and list(cp.xy(sx.one(route,'end')))==item['end_nm']
  assert cp.nm(sx.one(route,'width')[1])==item['width_nm']+(name=='seed_width_mutation' and item is seed['seeds'][0])
 for step in row['steps']:
  process_path=folder/(step['name']+'-process.json');proc=read(process_path)
  assert set(step)-set(proc)<={'emitted_candidate','validated_input_sha256'} and all(step[key]==value for key,value in proc.items())
  assert proc['cleanup_complete'] is True and proc['log_truncated'] is False
  assert proc['exit_code'] in (0,5) and proc['status']==('success' if proc['exit_code']==0 else 'nonzero_exit')
  assert Path(proc['cwd'])==folder and Path(proc['log']).stat().st_size==proc['log_bytes']
  event=step.get('local_settings_protection')
  if event:
   assert event['flags_restored'] is True and event['bytes_unchanged'] is True
   assert p.sha(Path(event['path']))==event['sha256']
   assert os.stat(event['path']).st_flags==event['flags_before'];flags.append(event)
 mapping=read(folder/'final-netclasses.json');query=read(folder/'final-netclasses-process.json')
 assert mapping['native_version']=='10.0.7' and mapping['source']==str(candidate) and mapping['board_saved'] is False
 assert mapping['board_sha256']==row['candidate_sha256'] and mapping['project_sha256']==hashes[source.with_suffix('.kicad_pro').name]
 assert query['argv'][-4:]==[str(runtime/'autorouter/native.py'),'netclasses',str(candidate),str(folder/'final-netclasses.json')]
 refill=read(folder/'refill-drc-binding.json')
 assert refill['saved'] is True and refill['source']==refill['input']==str(folder/'refill'/source.name)
 assert refill['before']=={**hashes,source.name:row['candidate_sha256']}
 assert io.inventory(folder/'refill')==refill['after']
 counts=None
 if name!='seed_width_mutation':
  counts=[row['native'][key] for key in ('opens','blocking','warnings','exclusions')]
  assert counts==([0,0,19,0] if name=='positive' else [0,2,19,0])
  assert len(row['native']['ignored_checks'])==2 and row['original_protected_count']==1 and row['source_geometry_unchanged'] is True
  view=dict(row,native_report_sha256=p.sha(folder/'final-drc.json'))
  own[name]=own_final(view,folder,folder,hashes,candidate)  # Derived view only; raw row stays unchanged.
  audit=read(folder/'final-netclass-audit.json')
  assert audit['route_dimensions']['passed'] is True and audit['native']['passed'] is True
  assert audit['route_dimensions']['checked']['protected']==1 and audit['default_targets']['derived_nm']==plan['targets']
  assert audit['candidate_sha256']==row['candidate_sha256'] and audit['native_map_file_sha256']==p.sha(folder/'final-netclasses.json')
  field=read(folder/'final-drc-fields-proof.json');assert row['native']['field_parity']==field
  for key,file in (('native_report_sha256','final-drc.json'),('binding_sha256','final-drc-binding.json'),('netlist_sha256','final-drc-fields.net'),('fields_sha256','final-drc-fields.json'),('local_settings_guard_sha256','final-drc-fields-local-settings.json')):
   assert field[key]==p.sha(folder/file)
  local=read(folder/'final-drc-fields-local-settings.json');event=local['protection']
  assert local['before']==local['after'] and event['flags_restored'] is True and event['bytes_unchanged'] is True
  assert p.sha(Path(event['path']))==event['sha256'] and os.stat(event['path']).st_flags==event['flags_before'];flags.append(event)
  for worker,pin in local['processes_sha256'].items():assert p.sha(folder/(worker+'-process.json'))==pin
 else:
  assert 'native' not in row and row['rejected_before_final_DRC'] is True
  assert row['reason'].startswith('generated track differs from native netclass target:')
  assert [s['name'] for s in row['steps']]==['refill-drc','final-netclasses'] and not (folder/'final-drc.json').exists()
 rows.append(dict(case=name,control_passed=True,Native_counts=counts,ignored_checks=row.get('native',{}).get('ignored_checks'),candidate_sha256=row['candidate_sha256'],reason=row.get('reason'),steps=[dict(name=s['name'],status=s['status'],exit_code=s['exit_code'],cleanup_complete=s['cleanup_complete']) for s in row['steps']]))
short_errors=[r for r in result['cases']['outside_short']['native']['findings'] if r['severity']=='error']
assert set(route_maps['outside_short'])==set(route_maps['positive'])|{plan['short_uuid']}
assert all(route_maps['outside_short'][key]==route for key,route in route_maps['positive'].items())
assert set(route_maps['seed_width_mutation'])==set(route_maps['positive'])
assert all(route_maps['seed_width_mutation'][key]==route for key,route in route_maps['positive'].items() if key!=seed['seeds'][0]['segment_uuid'])
assert all(r['type']=='tracks_crossing' and plan['short_uuid'] in {item['uuid'] for item in r['items']} for r in short_errors)
assert [r for r in result['cases']['positive']['native']['findings'] if r['severity']!='error']==[r for r in result['cases']['outside_short']['native']['findings'] if r['severity']!='error']
review=dict(schema=1,kind='owned-escape-controls-static-result-review-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='AI static actual-result readback; curator and original-v1 generator author. Not independent generator-source or human review',human_review=False,protocol_sha256=p.sha(protocol),result_sha256=p.sha(output/'result.json'),enclosure_sha256=p.sha(outer/'result.json'),findings=[],cases=rows,own_final=own,source_and_completed_material_unchanged=True,runtime_tools_code_hashes_match=True,restored_PRL_events=len(flags),Native_or_engine_or_acceptance_reader_executed=False,limits='Existing raw reports/processes/bindings/field/PRL/default audits and pure original geometry compared; no Native validation repeated. Roomy control-only completion tails are not solver-generated routing or dense escape performance. Review/authoring elapsed and CPU unknown additional, notzero.')
with review_path.open('x') as stream:json.dump(review,stream,indent=2,sort_keys=True);stream.write('\n')
queue={};omitted=[]
def add(path,name):queue.setdefault(Path(path),Path(name))
for path in [Path(__file__),*helpers,review_path,ROOT/'.runs/qfn-escape-v2-source-review-001.json',protocol,prep/'seed-plan.json',runtime/'runtime-distribution.json']:
 add(path,Path('provenance')/path.name)
for name in plan['code_sha256']:add(ROOT/name,Path('source')/name)
for path in (ROOT/'experiments/qfn_escape_seed_v1/README.md',ROOT/'tests/test_qfn_escape_seed.py',ROOT/'tests/test_qfn_escape_controls.py',ROOT/'LICENSE'):add(path,Path('source')/path.relative_to(ROOT))
for stem in ('qfn-escape-controls-native-002','qfn-escape-controls-preparation-002','qfn-escape-v2-targeted-001','qfn-escape-v2-targeted-002'):
 for suffix in ('.log','-time.log'):add(ROOT/'.runs'/(stem+suffix),Path('costs-logs')/(stem+suffix))
sealed={}
for folder,label in ((output,'controls'),(outer,'enclosure')):
 inventory=io.inventory(folder,max_bytes=32*1024**2,max_files=2048,max_entries=4096);sealed[folder]=inventory
 for name,pin in inventory.items():
  path=folder/name
  if path.suffix in ('.json','.log','.kicad_prl') and not any(part in ('code','kicad-config','kicad-cache','kicad-documents','tmp') for part in Path(name).parts):add(path,Path(label)/name)
  else:omitted.append(dict(original=str(path.relative_to(ROOT)),sha256=pin,reason='CAD/netlist/cache or other payload local-only; owned factory retained for reproduction'))
assert len(queue)<2000 and sum(path.stat().st_size for path in queue)<16*1024**2
for path,name in queue.items():retain(path,name)
assert all(io.inventory(path,max_bytes=32*1024**2,max_files=2048,max_entries=4096)==inventory for path,inventory in sealed.items())
assert completed_material(output)==result['completed_evidence'] and io.inventory(source.parent)==hashes
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted=omitted))
p.save_json(target,dict(schema=1,kind='owned-QFN-escape-seed-v2-Native-prerequisites-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,routing_accepted=False,production_admitted=False,project_complete=False,engine_executed=False,actual_GUI=False,human_review=False,runtime_source_head=plan['tools']['git_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],administration_head=plan['administration_head'],dependency=dict(path=str(dependency.relative_to(ROOT)),sha256=p.sha(dependency)),previous_prerequisites=dict(path=str(previous.relative_to(ROOT)),sha256=p.sha(previous)),protocol_sha256=p.sha(protocol),source_hashes=hashes,seed_count=16,original_protected_count=1,cases=rows,own_final=own,static_review=dict(path=str(review_path.relative_to(ROOT)),sha256=p.sha(review_path)),accounting=dict(Native_batch_complete=cost(ROOT/'.runs/qfn-escape-controls-native-002-time.log'),preparation_complete_additional=cost(ROOT/'.runs/qfn-escape-controls-preparation-002-time.log'),enclosing_sample=dict(wall_seconds=enclosed['complete_wall_seconds'],CPU_seconds=enclosed['complete_full_CPU_seconds']),actor_sample=dict(wall_seconds=result['wall_seconds'],CPU_seconds=result['full_CPU_seconds']),limits='Nested actor/outer samples overlap complete Native batch exit; do not add them. Preparation is additional. Source authoring/AI review/curation are additional; unknown authoring/review is notzero. Curator exit measured separately.'),scope='One roomy owned contact witness plus Native outside-short and exact Default seed-width guard negatives. Positive0/0/19/0 and short0/2/19/0 retain19fieldwarnings/twoignoredchecks; width has real refill/map but no final Native count. Seventeen reference paths removed before generation, including the centre connector; independent control-only tails plus that source-derived control connector complete the positive. Source pin17 solid-centre pad is retained and skipped; noncopper display alias preserved. All seeds/tails remain generated; only one original KEEP protected. No engine, routing gain, new family, electrical or product admission.',backup='Owned metadata/log/PRL and reproducing source only. CAD/netlist/cache/plot/ZIP/tool binaries remain local outside010; no new raw restoration claim.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),review_sha256=p.sha(review_path))))
