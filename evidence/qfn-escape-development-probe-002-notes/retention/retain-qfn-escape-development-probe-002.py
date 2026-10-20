"""Metadata-only retention of one completed negative; never acceptance evidence.

Actual Native/CAD/field values remain local. Generated public facts identify
their exact raw receipts and are explicitly not authoritative substitutes.
"""
from pathlib import Path
from collections import Counter
import ast, datetime, hashlib, json, os, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx
REVIEW_SHA256='c5863a9a42d2eebc7c432f5e3fb6ade26dc21ed8c3ea6059174192764ac2929c'
notes=ROOT/'evidence/qfn-escape-development-probe-002-notes';target=ROOT/'evidence/qfn-escape-development-probe-002.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
for name,pin,names in (
 ('curate-runtime030-native-workflow-qualification-001.py','b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1',('retain','cost')),
 ('curate-gui-runtime042-081-recovery-deliveries-001.py','340f1605f68ab9cef9133a0afe4c896ec339a3938e7f3dd636e9d508580c44f9',('read','own_final'))):
 helper=ROOT/'.runs'/name;assert p.sha(helper)==pin
 nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names]
 assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
review_path=ROOT/'.runs/qfn-escape-probe002-result-review-001.json'
assert review_path.is_file() and p.sha(review_path)==REVIEW_SHA256
review=read(review_path);assert type(review) is dict
assert review['findings']==[] and review['reviewer']['human_review'] is False
assert review['identity']['protocol_sha256']=='2aac6b5c7949abc48a30bcde966bd2f11eeb37190081f8eb1af87c0a86f8097d'
classification=review['private_finding_classification']
assert classification['raw_geometry_or_finding_descriptions_retained_in_this_review'] is False
assert classification['all_three_clearance_pairs_already_present_in_seeded_source_DRC'] is True
assert classification['three_clearance_error_item_classes']==[['generated_seed','original_source']]*3
dependencies=[]
for name,pin in (
 ('qfn-escape-native-prerequisites-003.json','19c2b1735ce56f9b40f51cc60a9c9c4cc5a59dbea104567f62f18c98a05307c7'),
 ('qfn-escape-development-probe-001.json','2c6b3b5173e4c634c00ba96201c7069248bd9fcab3da9e523b6cf7c55d09f781'),
 ('runtime050-devobordo-development-001.json','09cbea0b1731bae31572ba9d6934045ab7eb3a7dfb4bd69bdd1306cbaded8bdc')):
 dependency=ROOT/'evidence'/name;assert p.sha(dependency)==pin
 index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
 for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
 dependencies.append(dict(path=str(dependency.relative_to(ROOT)),sha256=pin))
baseline=[row for row in read(ROOT/'evidence/runtime050-devobordo-development-001.json')['methods'] if row['arm']=='B1']
assert len(baseline)==1 and baseline[0]['Native_counts']==[66,1,74,0]
prep=ROOT/'.runs/qfn-escape-probe-preparation-002';output=ROOT/'.runs/qfn-escape-probe-native-002';outer=ROOT/'.runs/qfn-escape-probe-native-002-enclosure'
protocol=prep/'protocol.json';assert p.sha(protocol)=='2aac6b5c7949abc48a30bcde966bd2f11eeb37190081f8eb1af87c0a86f8097d'
plan=read(protocol);parent=read(output/'result.json');child=read(output/'partial-route/result.json');enclosed=read(outer/'result.json');process=read(outer/'process.json')
assert parent['protocol_sha256']==enclosed['protocol_sha256']==p.sha(protocol) and enclosed['child_sha256']==p.sha(output/'result.json')=='2ce7985e8cad5d0b0ab261bed14e2810ff120622b5e4d9b16758a639075795f7'
assert Path(plan['output'])==output and Path(plan['enclosure'])==outer and plan['publication']=='hashes_only'
assert parent['status']=='completed_native_diagnostic' and parent['passed'] is True and parent['attempt_qualified'] is True
assert all(parent[key] is False for key in ('accepted','production_admitted','workflow_delivered','Native_routing_scope_passed','actual_GUI','human_review','physical_electrical_validation'))
assert enclosed['passed'] is True and enclosed['accepted'] is False and enclosed['workflow_delivered'] is False and enclosed['production_admitted'] is False
assert enclosed['process']==process and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False
assert parent['child_receipt_sha256']==p.sha(output/'partial-route/result.json') and parent['child_status']==child['status']=='drc_rejected' and child['accepted'] is False
assert parent['child_accepted'] is False and parent['child_partial_validation_is_not_original_acceptance'] is True
runtime=Path(plan['runtime']);assert runtime==ROOT/'.runs/runtime-directory-050/runtime'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
assert parent['tools']==child['tools']==plan['tools']
for name,pin in plan['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
for name,pin in plan['code_sha256'].items():assert p.sha(ROOT/name)==pin
for name,pin in plan['prerequisites'].items():assert p.sha(Path(name))==pin
hashes=plan['source_hashes'];source=Path(plan['source']);assert io.inventory(source.parent)==hashes==parent['source_hashes']
assert parent['seed_count']==64 and parent['original_protected_count']==0 and parent['original_geometry_and_protected_unchanged'] is True
assert p.sha(output/'seed-plan.json')==parent['seed_plan_sha256'] and io.inventory(output/'seeded-source')==parent['seeded_source_hashes']==child['source_hashes']
assert p.sha(output/'original-target-query/original-netclasses.json')==parent['source_target_query_sha256']
assert io.inventory(output/'original-target-query/original')==hashes
assert parent['candidate_sha256']==child['candidate_sha256'] and p.sha(Path(parent['candidate']))==parent['candidate_sha256']
assert review['identity']['candidate_sha256']==parent['candidate_sha256'] and review['identity']['own_native_report_sha256']==parent['native_report_sha256']
assert p.immutable(sx.read(Path(parent['candidate'])))==p.immutable(sx.read(source))
counts=[parent['native'][key] for key in ('opens','blocking','warnings','exclusions')]
assert counts==[67,3,136,0] and [child['native'][key] for key in ('opens','blocking','warnings','exclusions')]==counts
taxonomy=Counter((item['type'],item['severity']) for item in parent['native']['findings'])
assert taxonomy=={('unconnected_items','error'):67,('clearance','error'):3,('track_dangling','warning'):62,('lib_footprint_issues','warning'):40,('footprint_symbol_field_mismatch','warning'):34}
proofs={};audits={};step_facts=[];field_qualification=None
for label,data,folder,source_hashes,protected in (
 ('whole_original',parent,output/'whole-original-validation',hashes,0),
 ('partial_seeded',child,output/'partial-route',parent['seeded_source_hashes'],64)):
 proofs[label]=own_final(data,folder,folder,source_hashes,Path(data['candidate']))
 audit=read(folder/'final-netclass-audit.json')
 assert audit['candidate_sha256']==data['candidate_sha256'] and audit['native']['passed'] is True and audit['route_dimensions']['passed'] is True
 assert audit['route_dimensions']['checked']['protected']==protected and audit['default_targets']['derived_nm']==plan['targets']
 assert audit['native_map_file_sha256']==p.sha(folder/'final-netclasses.json')
 audits[label]=dict(candidate_sha256=data['candidate_sha256'],native_map_sha256=audit['native_map_file_sha256'],audit_sha256=p.sha(folder/'final-netclass-audit.json'),route_dimensions=audit['route_dimensions'],unchanged_original_targets=plan['targets'])
 field=read(folder/'final-drc-fields-proof.json');assert field==data['native']['field_parity']
 assert field['qualification']==dict(qualified=False,reason='duplicate source symbol or footprint field');field_qualification=field['qualification']
 for key,name in (('native_report_sha256','final-drc.json'),('binding_sha256','final-drc-binding.json'),('fields_sha256','final-drc-fields.json'),('netlist_sha256','final-drc-fields.net'),('local_settings_guard_sha256','final-drc-fields-local-settings.json')):assert p.sha(folder/name)==field[key]
 guard=read(folder/'final-drc-fields-local-settings.json');event=guard['protection']
 assert event['flags_restored'] is True and event['bytes_unchanged'] is True and guard['before']==guard['after']
 assert p.sha(Path(event['path']))==event['sha256'] and os.stat(event['path']).st_flags==event['flags_before']
 for step in data['steps']:
  stage_folder=Path(step['cwd']);assert stage_folder in (folder,output/'original-target-query')
  actual=read(stage_folder/(step['name']+'-process.json'))
  assert set(step)-set(actual)<={'emitted_candidate','validated_input_sha256'} and all(step[key]==value for key,value in actual.items())
  assert step['cleanup_complete'] is True and step['log_truncated'] is False and step['exit_code'] in (0,5)
  step_facts.append(dict(packet=label,name=step['name'],status=step['status'],exit_code=step['exit_code'],cleanup_complete=True,process_sha256=p.sha(stage_folder/(step['name']+'-process.json'))))
engine=read(output/'partial-route/engine-process.json');assert engine['status']=='success' and engine['exit_code']==0 and engine['cleanup_complete'] is True and engine['log_truncated'] is False
assert p.sha(Path(plan['preparation_time_log']))==parent['preparation_complete_cost']['time_log_sha256']=='7b9f1803574a159116d4915db811919c817aebb28272edfd0f9885f1447271e0'
assert parent['preparation_complete_cost']==enclosed['preparation_complete_cost']
inventory,directories=io.inventory(output,max_bytes=100*1024**2,max_files=2000,max_entries=4000,with_directories=True)
captured={name:pin for name,pin in inventory.items() if name not in {'result.json','result.json.partial'} and not name.startswith(('invalidated-result-','interrupted-result-'))}
assert parent['completed_evidence']==dict(files=captured,directories=list(directories))
facts=dict(schema=1,generated_metadata_facts=True,authoritative_validation_receipt=False,raw_receipts=dict(parent_sha256=p.sha(output/'result.json'),child_sha256=p.sha(output/'partial-route/result.json')),completed_diagnostic=True,raw_attempt_qualified=True,meaning='Diagnostic stages completed; not acceptance, field qualification or delivery',accepted=False,production_admitted=False,workflow_delivered=False,Native_counts=counts,findings_by_type_and_severity=[dict(type=key[0],severity=key[1],count=count) for key,count in sorted(taxonomy.items())],ignored_checks=parent['native']['ignored_checks'],full_schematic_Native_executed=True,field_qualification=field_qualification,ordinary_acceptance_or_eligibility=False,seed_count=64,original_protected_count=0,own_final=proofs,Default_audits=audits,steps=step_facts,invalid_unranked_metrics=parent['metrics'],source_hashes=hashes,review=dict(path=str(review_path.relative_to(ROOT)),sha256=REVIEW_SHA256,raw_not_copied=True,scope='Separate AI static actual-result review, not human PCB approval'),completed_material_hashes=parent['completed_evidence'])
facts['review']['raw_not_copied']=False
facts['review']['metadata_only_review_inspected_before_copy']=True
facts['clearance_origin_review_fact']=dict(count=3,item_classes=['generated_seed','original_source'],already_present_in_seeded_source_before_engine=True,independent_AI_review_sha256=REVIEW_SHA256,not_a_human_or_repairability_claim=True)
queue={};omitted=[]
def add(path,name):queue.setdefault(Path(path),Path(name))
add(Path(__file__),Path('retention')/Path(__file__).name);add(protocol,Path('provenance/protocol.json'))
add(review_path,Path('provenance/AI-static-result-review.json'))
for name in ('result.json','process.json','command.log'):add(outer/name,Path('enclosure')/name)
for stem in ('qfn-escape-probe-preparation-002','qfn-escape-probe-native-002'):
 for suffix in ('.log','-time.log'):add(ROOT/'.runs'/(stem+suffix),Path('costs-logs')/(stem+suffix))
# Explicit metadata allowlist. Raw Native/field reports, audits, query maps,
# seed plans, all CAD/DSN/SES/netlists/plots and engine logs are never copied.
safe_suffixes=('-process.json','-binding.json','-fields-proof.json','-fields-local-settings.json')
for name,pin in inventory.items():
 path=output/name
 if path.name.endswith(safe_suffixes) or path.suffix=='.kicad_prl':add(path,Path('proof-metadata')/name)
 else:omitted.append(dict(original=str(path.relative_to(ROOT)),sha256=pin,reason='Raw foreign geometry/findings/fields/query/seed/code/log or other payload local-only'))
assert len(queue)<2000 and sum(path.stat().st_size for path in queue)<16*1024**2
for path,name in queue.items():retain(path,name)
generated=notes/'generated-diagnostic-facts.json';p.save_json(generated,facts)
files.append(dict(path=str(generated.relative_to(ROOT)),bytes=generated.stat().st_size,sha256=p.sha(generated)));total+=generated.stat().st_size
assert total<16*1024**2 and len(files)<2000
assert io.inventory(output,max_bytes=100*1024**2,max_files=2000,max_entries=4000)==inventory and io.inventory(source.parent)==hashes
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material,omitted=omitted))
complete=cost(ROOT/'.runs/qfn-escape-probe-native-002-time.log');prep_cost=cost(ROOT/'.runs/qfn-escape-probe-preparation-002-time.log')
p.save_json(target,dict(schema=1,kind='escape-development-probe-completed-Native-negative-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),generated_metadata_summary=True,authoritative_validation_receipt=False,accepted=False,production_admitted=False,workflow_delivered=False,project_complete=False,human_review=False,actual_GUI=False,completed_diagnostic=True,attempt_qualified_meaning='Raw experimental controller completed its own diagnostic; not Native acceptance/ordinary field eligibility',Native_counts=counts,field_qualification=field_qualification,source_hashes=hashes,source_rights=plan['source_rights'],publication='metadata_and_hashes_only',protocol_sha256=p.sha(protocol),administration_head=plan['administration_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],dependencies=dependencies,generated_facts=dict(path=str(generated.relative_to(ROOT)),sha256=p.sha(generated)),raw_own_final=proofs,accounting=dict(probe_complete=complete,preparation_additional=prep_cost,complete_including_preparation=dict(wall_seconds=round(complete['wall_seconds']+prep_cost['wall_seconds'],2),CPU_seconds=round(complete['CPU_seconds']+prep_cost['CPU_seconds'],2)),actor_nested=dict(wall_seconds=parent['wall_seconds'],CPU_seconds=parent['full_CPU_seconds']),engine_nested=dict(wall_seconds=engine['wall_seconds'],CPU_seconds=engine['cpu_seconds']),limits='Nested actor/child/engine/Native samples overlap complete exit and are not added. Preparation is additional. Previous failed probe001 remains separately costed/unmodified. Authoring/AI review/curation additional, unknown authoring/review notzero.'),comparison=dict(existing_exposed_B1_counts=baseline[0]['Native_counts'],current_counts=counts,completion_gain=False,metrics_invalid_unranked=True,scope='One new exposed diagnostic, not a replacement/stitch of frozen six-arm cohort or a fresh fair performance trial'),decision='Defer this fixed escape initialization: no completion or B1/B2 gain; no length/via/parameter retries or automatic rerun. Keep the negative and original probe001 serialization failure.',limits='Own fullSCH Native executed against unchanged original rules, but Native negative and bound field qualificationFalse mean neither field-clean nor ordinary accepted/eligible. Child treats64seeds protected only within seeded task; whole-original Default audit treats allseeds new with0originalprotected. No delivery/GUI/human/electrical/holdout/general gain claim. Raw actual every-candidate Native reports/CAD/field/query/seed data stay Mac-only outside010; public generated facts/hashes are not authentic acceptance or raw backup.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),Native_counts=counts,field_qualified=False)))
