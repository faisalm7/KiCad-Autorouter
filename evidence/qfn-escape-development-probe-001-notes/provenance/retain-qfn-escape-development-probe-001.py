"""Retain failed probe001 as pre-engine interchange failure, never Native pass.

Only existing metadata/log/PRL bytes are copied. No Native/engine/acceptance
reader, geometry publication, correction, retry or current-code substitution.
"""
from pathlib import Path
import ast, datetime, hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io, sexpr as sx
notes=ROOT/'evidence/qfn-escape-development-probe-001-notes'
target=ROOT/'evidence/qfn-escape-development-probe-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
def read(path):return json.loads(io.read_bytes(path,4*1024**2))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','cost')]
assert len(nodes)==2;exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::shared','exec'),globals())
dependency=ROOT/'evidence/qfn-escape-native-prerequisites-002.json'
assert p.sha(dependency)=='f6f461d9308b6242fca60747b64060ba65ca61e9cf5da253cda983ce3c2fd1b3'
index=read(dependency)['files_index'];assert p.sha(ROOT/index['path'])==index['sha256']
for row in read(ROOT/index['path'])['files']:refs.setdefault(row['sha256'],row['path'])
prep=ROOT/'.runs/qfn-escape-probe-preparation-001';output=ROOT/'.runs/qfn-escape-probe-native-001'
outer=ROOT/'.runs/qfn-escape-probe-native-001-enclosure';protocol=prep/'protocol.json';partial=output/'partial-route'
assert p.sha(protocol)=='7f1ca3586c4f5627d0c2f13d0821f6689329d5e03051504c8249a8d513b4a094'
plan=read(protocol);result=read(output/'result.json');enclosed=read(outer/'result.json');process=read(outer/'process.json')
assert Path(plan['output'])==output and Path(plan['enclosure'])==outer and Path(plan['preparation'])==prep
assert plan['publication']=='hashes_only' and plan['kind']=='source-geometry-escape-single-development-probe-v1'
assert result['protocol_sha256']==enclosed['protocol_sha256']==p.sha(protocol)
assert p.sha(output/'result.json')==enclosed['child_sha256']=='de9112fe0bd0b08148ea93ace2d032bc20090480b1a3d9065d7e68ef024500e1'
assert result['status']=='failed' and all(result[key] is False for key in ('passed','attempt_qualified','accepted','production_admitted','workflow_delivered','child_accepted'))
assert result['reason']=='Rejected: partial child did not complete a Native candidate: Rejected: source-drc: nonzero_exit exit=3'
assert enclosed['passed'] is False and enclosed['accepted'] is False and enclosed['production_admitted'] is False and enclosed['workflow_delivered'] is False
assert enclosed['process']==process and process['status']=='nonzero_exit' and process['exit_code']==2 and process['cleanup_complete'] is True and process['log_truncated'] is False
assert Path(process['cwd'])==outer and Path(process['log'])==outer/'command.log' and process['log_bytes']==(outer/'command.log').stat().st_size
runtime=Path(plan['runtime']);assert runtime==ROOT/'.runs/runtime-directory-050/runtime'
assert p.sha(runtime/'runtime-distribution.json')==plan['runtime_manifest_sha256']=='c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
assert result['tools']==plan['tools'] and result['source']==plan['source'] and result['source_hashes']==plan['source_hashes']
for name,pin in plan['tools']['implementation_sha256'].items():assert p.sha(runtime/name)==pin
source=Path(plan['source']);assert io.inventory(source.parent)==plan['source_hashes']
assert result['seed_count']==64 and result['original_protected_count']==0
assert p.sha(output/'seed-plan.json')==result['seed_plan_sha256']
assert io.inventory(output/'seeded-source')==result['seeded_source_hashes']
assert p.sha(output/'original-target-query/original-netclasses.json')==result['source_target_query_sha256']
query=read(output/'original-target-query/original-netclasses-process.json')
assert len(result['steps'])==1 and result['steps'][0]==query
assert query['status']=='success' and query['exit_code']==0 and query['cleanup_complete'] is True and query['log_truncated'] is False
assert io.inventory(output/'original-target-query/original')==plan['source_hashes']
child=read(partial/'result.json');assert p.sha(partial/'result.json')==result['child_receipt_sha256']
assert child['status']==result['child_status']=='rejected' and child['accepted'] is False and child['schematic_parity']=='not checked'
assert child['source_hashes']==result['seeded_source_hashes'] and child['source']==str(output/'seeded-source'/source.name)
assert 'native' not in child and 'native' not in result and 'candidate' not in child and 'candidate' not in result
step=read(partial/'source-drc-process.json');assert child['steps']==[step]
assert step['status']=='nonzero_exit' and step['exit_code']==3 and step['cleanup_complete'] is True and step['log_truncated'] is False
assert Path(step['cwd'])==partial and step['log_bytes']==(partial/'source-drc.log').stat().st_size
log=io.read_bytes(partial/'source-drc.log',4096).decode();assert 'Failed to load board' in log and 'offset 216418' in log
binding=read(partial/'source-drc-binding.json');failure=read(partial/'source-drc-failure.json')
assert failure['passed'] is False and failure['binding']==binding and not failure['capture_errors']
assert binding['before']==result['seeded_source_hashes'] and binding['saved'] is False
assert binding['input']==str(partial/'source-drc-input'/source.name) and io.inventory(partial/'source-drc-input')==binding['after']
assert failure['artifacts']['source-drc.json'] is None and not (partial/'source-drc.json').exists()
for name in ('source-drc.log','source-drc-process.json'):
 assert failure['artifacts'][name]['sha256']==p.sha(partial/name) and failure['artifacts'][name]['bytes']==(partial/name).stat().st_size
# Inspect only the offending token shape, never retain a CAD excerpt or coordinates.
tree=sx.read(partial/'source-drc-input'/source.name)
bad=[r for r in p.routes(tree) if len(sx.one(r,'net',[]))==3]
assert len(bad)==64 and all(r[0]=='segment' for r in bad)
assert p.sha(Path(plan['preparation_time_log']))==result['preparation_complete_cost']['time_log_sha256']=='7776e58e2db16f625db2ba88e36a234358956e82640bfaa8ec74235d687241ad'
assert enclosed['preparation_complete_cost']==result['preparation_complete_cost']
inventory,directories=io.inventory(output,max_bytes=100*1024**2,max_files=2000,max_entries=4000,with_directories=True)
captured={name:pin for name,pin in inventory.items() if name not in {'result.json','result.json.partial'} and not name.startswith(('invalidated-result-','interrupted-result-'))}
assert result['completed_evidence']==dict(files=captured,directories=list(directories))
assert not any(Path(name).name in ('engine-process.json','routes.ses','import-process.json','final-drc.json') for name in inventory)
queue={}
def add(path,name):queue.setdefault(Path(path),Path(name))
for path in (Path(__file__),helper,protocol,output/'result.json',outer/'result.json',outer/'process.json',outer/'command.log',partial/'result.json',partial/'source-drc-process.json',partial/'source-drc-binding.json',partial/'source-drc-failure.json',partial/'source-drc.log',output/'original-target-query/original-netclasses-process.json',output/'original-target-query/original-netclasses.log'):
 label=path.relative_to(output) if path.is_relative_to(output) else Path('enclosure')/path.name if path.parent==outer else Path('provenance')/path.name
 add(path,label)
for stem in ('qfn-escape-probe-preparation-001','qfn-escape-probe-native-001'):
 for suffix in ('.log','-time.log'):add(ROOT/'.runs'/(stem+suffix),Path('costs-logs')/(stem+suffix))
for name in inventory:
 if Path(name).suffix=='.kicad_prl':add(output/name,Path(name))
assert len(queue)<2000 and sum(path.stat().st_size for path in queue)<16*1024**2
for path,name in queue.items():retain(path,name)
assert io.inventory(output,max_bytes=100*1024**2,max_files=2000,max_entries=4000)==inventory and io.inventory(source.parent)==plan['source_hashes']
index=notes/'files.json';p.save_json(index,dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='escape-development-probe-pre-engine-load-failure-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),accepted=False,production_admitted=False,workflow_delivered=False,attempt_qualified=False,passed=False,engine_executed=False,actual_GUI=False,human_review=False,Native_counts=None,status='failed_before_engine',protocol_sha256=p.sha(protocol),administration_head=plan['administration_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],source_hashes=plan['source_hashes'],source_rights=plan['source_rights'],publication='metadata_and_hashes_only',dependency=dict(path=str(dependency.relative_to(ROOT)),sha256=p.sha(dependency)),reason=result['reason'],seed_count=64,original_protected_count=0,diagnosis='Generated segments retained PAD code-plus-label net token shape; selected Native loader refused at closing-parenthesis offset216418. Sixtyfour such segment tokens observed in the exact hash-bound failed source input. This is generator interchange grammar failure, not qualified Native routing rejection, board infeasibility or original-source invalidity.',outcomes=dict(original_target_query='success exit0',partial_child='source-drc board-load failure exit3, cleanupTrue; parity not checked',enclosure='nonzero exit2, cleanupTrue',engine=False,SES=False,imported_candidate=False,final_Native=False,delivery=False,automatic_retry=False),frozen_code_pins=plan['code_sha256'],accounting=dict(preparation_complete_additional=cost(ROOT/'.runs/qfn-escape-probe-preparation-001-time.log'),probe_complete=cost(ROOT/'.runs/qfn-escape-probe-native-001-time.log'),enclosure_sample=dict(wall_seconds=enclosed['complete_wall_seconds'],CPU_seconds=enclosed['complete_full_CPU_seconds']),actor_sample=dict(wall_seconds=result['wall_seconds'],CPU_seconds=result['full_CPU_seconds']),partial_sample=dict(wall_seconds=child['wall_seconds'],CPU_seconds=child['total_cpu_seconds']),limits='Nested samples overlap complete probe exit; do not add them. Preparation is additional. Source-authoring/AI review/curation additional, unknown authoring/review notzero; curation exit measured separately.'),AI_review=dict(scope='Static current receipts/process/binding/material/hash readback and offending token shape only. Curator/original-v1 generator author, not independent generator-source or human review.',concrete_discrepancy=None,source_unchanged=True,qualified_Native_counts_available=False,current_source_fix_not_substituted_for_frozen_pins=True),backup='Only metadata/log/PRL retained. Original query map/target-audit/seed plan/CAD/DSN/SES/plots and foreign geometry are not copied; full raw remains Mac-only outside010. Frozen source hashes are identity evidence, not a backup of later-edited code or whole raw source.',files_index=dict(path=str(index.relative_to(ROOT)),sha256=p.sha(index))))
print(json.dumps(dict(path=str(target),sha256=p.sha(target),files=len(files),bytes=total,material=len(material),status='failed_before_engine',Native_counts=None)))
