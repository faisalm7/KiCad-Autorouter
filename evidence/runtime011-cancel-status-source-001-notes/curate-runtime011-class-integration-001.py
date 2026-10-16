"""Curate owned actual Native evidence, preserving the failed batch verbatim."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1];case=ROOT/'.runs/runtime-directory-011';runtime=case/'runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,review_export as ex,floor_route as f,placement_clearance as pc,config as c
assert c.ROOT==runtime
setup=f.read_json(case/'setup.json');matching=f.read_json(runtime/'.runs/qualification-matching/result.json');workspace=Path(matching['workspace'])
controls=runtime/'.runs/class-controls-001';batch=f.read_json(controls/'result.json')
assert matching['workflow_delivered']is True and batch['controls_passed']is False
jobs=[('matching-route',workspace/'route'),('matching-export',workspace/'export/validation'),('clean-route',controls/'clean-route'),('clean-export',controls/'clean-export/validation'),('mismatch',controls/'mismatch-route'),('cancel-status-defect',controls/'cancel-route')]
positive=[]
for label,receipt,export in [('matching',workspace/'route/result.json',workspace/'export/export.json'),('clean-field-direct',controls/'clean-route/result.json',controls/'clean-export/export.json')]:
 assert p.check_result(receipt)['current']is True and ex.check_export(export)['current']is True
 d=f.read_json(receipt);e=f.read_json(export)
 positive.append(dict(name=label,receipt=str(receipt),receipt_sha256=p.sha(receipt),export=str(export),export_sha256=p.sha(export),candidate_sha256=d['candidate_sha256'],export_candidate_sha256=e['candidate_sha256'],native=d['native'],export_native=e['native'],metrics=d['metrics'],route_compute={k:d[k]for k in('wall_seconds','total_cpu_seconds')},export_compute={k:e[k]for k in('wall_seconds','total_cpu_seconds')},protected=len(d['protected_route_import']['matches']),steps=[s['name']for s in d['steps']]))
bad=f.read_json(controls/'mismatch-route/result.json');cancel=f.read_json(controls/'cancel-route/result.json');engine=f.read_json(controls/'cancel-route/engine-process.json')
assert bad['accepted']is False and 'class_identity_mismatch'in bad['reason']and not(controls/'mismatch-route/engine.log').exists()
assert cancel['accepted']is False and cancel['status']=='rejected'and engine['status']=='cancelled'and engine['cleanup_complete']is True
notes=ROOT/'evidence/runtime011-flat-class-integration-001-notes';notes.mkdir();rows=[]
def copy(source,relative):
 raw=pc.read_bytes(source,4*1024**2);target=notes/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 rows.append(dict(path=str(target.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),local_source=str(source)))
for label,folder in jobs:
 for name in pc.inventory(folder,max_bytes=100*1024**2):
  if Path(name).parts[0]in {'code','kicad-cache','kicad-config','kicad-documents','engine-config'}:continue
  copy(folder/name,Path(label)/name)
for name,item in setup['sources'].items():
 folder=Path(item['board']).parent;assert p.tree_hash(folder)==item['source_hashes']
 for filename in item['source_hashes']:copy(folder/filename,Path('source-'+name)/filename)
for name in ['setup.json']:copy(case/name,Path(name))
for folder in [runtime/'.runs/enclosure-matching',runtime/'.runs/enclosure-class-controls-001']:
 for name in('execution.json','command.log'):copy(folder/name,Path(folder.name)/name)
for source in [runtime/'.runs/qualification-matching/result.json',controls/'result.json',workspace/'export/export.json',controls/'clean-export/export.json']:
 copy(source,Path('summaries')/(source.parent.name+'-'+source.name)if source.parent.name!='export'else Path('summaries')/'matching-export.json')
for name in ['.runs/qualify-runtime011-class-controls.py','.runs/run-runtime011-class-controls-001.py','.runs/runtime011-class-controls-001-time.log','.runs/runtime011-class-controls-001-command.log','.runs/runtime-directory011-workflow-matching-time.log','.runs/runtime-directory011-workflow-matching-command.log','.runs/prepare-runtime-directory-011-time.log','.runs/prepare-runtime-directory-011-command.log']:
 copy(ROOT/name,Path('controllers-and-logs')/Path(name).name)
record=dict(schema=1,kind='actual-flat-class-installed-integration-with-cancel-status-defect',source_head=setup['source_head'],accepted=False,full_qualification_passed=False,Native_executed=True,JVM_executed=True,actual_GUI=False,human_review=False,positive_cases=positive,
 actual_mismatch=dict(accepted=bad['accepted'],reason=bad['reason'],engine_started=False,steps=[s['name']for s in bad['steps']]),
 actual_cancellation=dict(accepted=cancel['accepted'],route_status=cancel['status'],worker_status=engine['status'],worker_cleanup_complete=engine['cleanup_complete'],classification_correct=False,known_defect='Job.step wrapped a cancelled runner as Rejected instead of propagating KeyboardInterrupt; no accepted fallback, but cancelled status missing'),
 tamper_controls=batch['checks'][2:],batch_status=batch['status'],batch_error=batch['error'],
 external_compute=dict(build=dict(wall_seconds=1.54,full_CPU_seconds=1.33),matching_workflow=dict(wall_seconds=36.14,full_CPU_seconds=31.43),controls_entire_failed_batch=dict(wall_seconds=34.53,full_CPU_seconds=29.60),subsets_not_added_again=True,research_authoring_review_costs='not measured, not zero'),
 scope='Two owned variants in one exposed family: actual openROUTE completion, ten protectedsegments, class task before engine/final proof/own fresh Native export. clean-field case has no field-worker stages. Six Datasheet warnings retained on matching; clean variant0warnings;2original ignored checks each. No comparative quality or independent family/Windows/physical claim.',
 retention='Selected complete owned project/Native inputs,reports,bindings,processes,class proofs,engine outputs/logs copied exactly; source code is remotely backed at source_head, excluded redundant code/runtime caches from this small packet. Full local evidence retained, not deleted. All originals unchanged.',files=rows)
assert len(rows)==len({r['path']for r in rows})
(ROOT/'evidence/runtime011-flat-class-integration-001.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(dict(files=len(rows),bytes=sum(r['bytes']for r in rows),positive_cases=len(positive),full_qualification=False,cancel_status_defect=True)))
