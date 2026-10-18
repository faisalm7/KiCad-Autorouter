"""Retain each final/failure using existing bounded evidence helpers; no rerouting."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
base=ROOT/'.runs/runtime033-interf-current-comparison-001'
frozen=f.read_json(base/'frozen-children.json');population=f.read_json(base/'population.json')
assert p.sha(base/'population.json')==frozen['population_sha256']
assert all((Path(frozen['protocols'][arm]['path']).parent/'enclosure/result.json').is_file()
           for arm in population['population']), 'all six complete outer receipts required before retention'
refs={};files=[];material=[];total=0;rows=[];packets=[]
for name in ('runtime033-native-invalid-001','runtime033-ordinary-install-001','runtime032-native-controls-001','runtime032-negative-portfolio-002','runtime022-thermal-export-control-001'):
 data=f.read_json(ROOT/('evidence/'+name+'.json'));index=ROOT/data['files_index']['path'];assert p.sha(index)==data['files_index']['sha256'];idx=f.read_json(index)
 for row in idx.get('files',[])+idx.get('material',[]):refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')];assert len(functions)==3
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
keys=('opens','blocking','warnings','exclusions')
for arm in population['planned_order']:
 pin=frozen['protocols'][arm];protocol=Path(pin['path']);assert p.sha(protocol)==pin['sha256']
 plan=f.read_json(protocol);out=Path(plan['output']);outer=f.read_json(protocol.parent/'enclosure/result.json')
 child=out/'result.json';data=f.read_json(child) if child.is_file() else {}
 assert outer['protocol_sha256']==pin['sha256'] and outer['child_sha256']==(p.sha(child) if child.is_file() else None)
 note_name='runtime033-current-interf-'+arm+'-001-notes';notes=ROOT/'evidence'/note_name
 assert not notes.exists();files=[];material=[];total=0
 tree(protocol.parent,Path('enclosure'))
 if out.is_dir():tree(out,Path('method'))
 for index,value in enumerate(plan.get('material_roots',[])):
  path=Path(value)
  if path.is_dir():tree(path,Path('portfolio-material')/str(index))
 for suffix in ('controller.log','time.log'):
  path=ROOT/'.runs'/('runtime033-current-interf-'+arm+'-001-'+suffix);retain(path,Path('logs')/path.name)
 for name in ('population.json','frozen-children.json'):retain(base/name,Path('population')/name)
 if arm=='Cdefault':
  for name in ('freeze-runtime033-interf-current-comparison-001-controller.log','freeze-runtime033-interf-current-comparison-001-time.log','runtime033-current-Cdefault-result-review-001.json','runtime033-ordinary-native-invalid-result-review-001.json'):
   path=ROOT/'.runs'/name;retain(path,Path('reviews-preparation')/name)
  retain(Path(__file__),Path('reviews-preparation')/Path(__file__).name)
 native=data.get('route_native') or data.get('native');summary=None
 if arm=='B2_portfolio':
  path=Path(plan['portfolio_output'])/'portfolio-summary.json'
  if path.is_file():summary=f.read_json(path)
 delivery=bool(outer.get('passed') and data.get('workflow_delivered'))
 row=dict(arm=arm,outer_passed=outer['passed'],controller_status=data.get('status'),
  outcome=data.get('outcome',summary.get('status') if summary else None),
  attempt_qualified=data.get('attempt_qualified',data.get('controls_passed') if outer['passed'] else False),
  workflow_delivered=delivery,complete_cost=cost(ROOT/'.runs'/('runtime033-current-interf-'+arm+'-001-time.log')),
  protocol_sha256=pin['sha256'],child_sha256=outer['child_sha256'],
  reason=data.get('reason',data.get('error')),Native_counts=[native[key] for key in keys] if native else None,
  route_metrics=data.get('route_metrics'),delivered_metrics=data.get('metrics') if delivery else None,
  selected_route_receipt=data.get('selected_route_receipt'),export_receipt=data.get('export_receipt'),
  source_hashes=plan['source_hashes'],all_costs_counted='External whole exit; nested samples retained, not added twice.')
 if summary:
  row['portfolio']=dict(status=summary['status'],selected=summary['selected'],all_variants_attempted=summary['all_variants_attempted'],
   trials=[dict(variant=trial.get('id'),eligible=trial.get('eligible'),validated_rejection=trial.get('validated_rejection'),
    Native_counts=[trial['native'][key] for key in keys] if trial.get('native') else None) for trial in summary['trials']])
 p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
 packet=ROOT/'evidence'/('runtime033-current-interf-'+arm+'-001.json')
 p.save_json(packet,dict(schema=1,kind='frozen-current033-single-arm-actual-evidence-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,actual_GUI=False,human_review=False,source_head=population['source_head'],runtime_manifest_sha256=population['runtime_manifest_sha256'],population_sha256=frozen['population_sha256'],administration_head=frozen['administration_head'],row=row,source_rights=population['source_rights'],limits=population['limits'],stock_caveat=population['stock_caveat'],scope='One exposed development family. All six arms remain in aggregate, including failures and unsupported/incomplete results. No broad quality, speed, human-cleanup or physical/electrical claim.',backup_scope='Essential public licensed proof only. Newer full raw remains on this Mac outside008/010. No restoration claim.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
 rows.append(row);packets.append(dict(path=str(packet.relative_to(ROOT)),sha256=p.sha(packet),files=len(files),bytes=total,material=len(material)))
aggregate=ROOT/'evidence/runtime033-current-interf-comparison-001.json';assert not aggregate.exists()
p.save_json(aggregate,dict(schema=1,kind='frozen-current033-six-arm-exposed-development-comparison-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,actual_GUI=False,human_review=False,independent_families=1,exposed_development=True,confirmatory=False,population=population,rows=rows,packets=packets,accounting='Every complete parent/child exit counted, including failed/unqualified outcomes. Preparation/freezing, invalid-control prerequisite, installation, full suites, research/authoring/AI reviews and curation are additional. Unknown interactive costs are not zero. No nested CPU double counting.',release_gates=['CurrentGUI notqualified','Broader unrelated development and untouched frozen-policy confirmation','Native Windows equivalent safeguards','New-target full restoration headroom','Actual independent engineer/cleanup/physicalvalidation; separateformalpublication approval']))
print(json.dumps(dict(aggregate=str(aggregate),arms=len(rows),delivered=[row['arm'] for row in rows if row['workflow_delivered']],packets=packets)))
