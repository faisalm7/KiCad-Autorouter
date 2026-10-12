"""Read retained native results with existing project/report/render checkers. No execution."""
from pathlib import Path
import hashlib,json,sys,collections
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as pc,floor_route as f,review_view as v,config as c
HERE=Path(__file__).resolve().parent
HEAD='5d4703dc573d6f82469f1ef0066c702d4a01db45'
def read(path):return f.read_json(path)
def inv(path):return pc.inventory(path,max_bytes=100*1024**2,max_files=4000,max_entries=8000)
def digest(value):return hashlib.sha256(f.canonical(value).encode()).hexdigest()
def file(path):return {'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':p.sha(path)}
def outer(name):
 ex=read(ROOT/'.runs'/f'{name}-execution.json');log=ROOT/'.runs'/f'{name}-command.log';wrapper=ROOT/'.runs'/f'run-{name}.py'
 assert ex['git_head']==HEAD and ex['exit_code']==0 and ex['cleanup_signals']==[]
 assert p.sha(log)==ex['log_sha256'] and log.stat().st_size==ex['log_bytes']
 assert p.sha(wrapper)==ex['wrapper_sha256']
 return {'execution':file(ROOT/'.runs'/f'{name}-execution.json'),'command_log':file(log),'wrapper':file(wrapper),'wall_seconds':ex['wall_seconds'],'waited_child_cpu_seconds':ex['waited_child_cpu_seconds'],'exit_code':ex['exit_code']}
names=['review-render-fixture-003','review-render-multichannel-001','review-render-tamper-001','review-render-cancel-001','native-drc-failure-evidence-control-001']
roots=[ROOT/'.runs'/name for name in names]
positive_records=[read(root/'review.json') for root in roots[:2]]
receipts=[Path(row['receipt']) for row in positive_records]
source_roots=[Path(read(path)['source']).parent for path in receipts]
allroots=list(dict.fromkeys(roots+[p.parent for p in receipts]+source_roots))
initial={str(path):inv(path) for path in allroots}
code={str(path.relative_to(ROOT)):p.sha(path) for path in sorted((ROOT/'autorouter').glob('*.py'))}
result={'schema':1,'scope':'Independent retained-evidence consistency readback. No plot, DRC, native, JVM, GUI, Git or network commands executed.','recorded_head':HEAD,'positives':[],'negative_previews':[]}
central={str(path):p.check_result(path) for path in receipts}
for root,r in zip(roots[:2],positive_records):
 preview=r['preview'];receipt=Path(r['receipt']);routing=read(receipt);source=Path(routing['source']);candidate=Path(routing['candidate'])
 assert r['status']=='ready_for_manual_review' and r['native_validation_performed'] is False
 assert preview['native_validation_performed'] is False and preview['zone_refill_performed'] is False
 assert r['receipt_sha256']==p.sha(receipt) and r['candidate_sha256']==p.sha(candidate)==r['verified_candidate_sha256']
 assert r['source_project_hashes']==inv(source.parent)==inv(root/'before')
 assert r['initial_project_hashes']==inv(candidate.parent)==inv(root/'project')
 assert r['routing_evidence_hashes']==inv(receipt.parent)
 assert all(p.sha(Path(name))==sha for name,sha in r['runtime_source_sha256'].items())
 assert preview['plotter_sha256']==read(ROOT/'toolchain.lock.json')['tools']['kicad_cli']['sha256']
 assert all(p.sha(root/name)==sha for name,sha in preview['files'].items())
 assert all(inv(root/name)==expected for name,expected in preview['input_trees'].items())
 assert preview['layers']==['F.Cu','B.Cu'] and len(preview['steps'])==4 and len(preview['input_trees'])==4
 stages=[]
 for step in preview['steps']:
  name=step['name'];label,layer=name.split('-',1);board=(root/('before' if label=='before' else 'project')/source.name);work=root/'plot-work';private=work/(name+'-input');raw=work/'native-plots'/(name+'.svg');display=work/'plots'/(name+'.svg')
  process=read(work/(name+'-process.json'));binding=read(work/(name+'-input-binding.json'))
  assert process==step and step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True
  expected=f.SANDBOX+[str(c.CLI),'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--output',str(raw),str(private/source.name)]
  assert step['argv']==expected and step['cwd']==str(work)
  assert step['log_bytes']==Path(step['log']).stat().st_size and step['log_truncated'] is False
  assert binding=={'source':str(board),'input':str(private/source.name),'before':inv(board.parent),'after':inv(private)}
  p.check_drc_project(binding['before'],binding['after'],source.name)
  assert display.read_bytes()==v.display_svg(v.svg_bytes(raw))
  stages.append({'name':name,'wall_seconds':step['wall_seconds'],'cpu_seconds':step['cpu_seconds'],'supervisor_cpu_seconds':step['supervisor_cpu_seconds'],'added_files':sorted(set(binding['after'])-set(binding['before']))})
 assert set(x.name for x in (root/'plot-work').glob('*-process.json'))=={x['name']+'-process.json' for x in preview['steps']}
 assert r['within_budget'] is True and r['budget_seconds']==r['cpu_budget_seconds']==30
 assert sum(x['wall_seconds'] for x in preview['steps'])<=r['wall_seconds']<30
 assert sum(x['cpu_seconds'] for x in preview['steps'])<=r['total_cpu_seconds']<30
 native=p.parse_report(receipt.parent/'final-drc.json',source.name);assert native==routing['native']
 html=(root/'preview.html').read_text();assert str(native['warnings']) in html
 result['positives'].append({'run':str(root.relative_to(ROOT)),'review':file(root/'review.json'),'central_readback':central[str(receipt)],'candidate_sha256':p.sha(candidate),'preview_html':file(root/'preview.html'),'bound_preview_files':len(preview['files']),'bound_private_inputs':len(preview['input_trees']),'source_files':len(r['source_project_hashes']),'saved_routing_native_counts':{key:native[key] for key in ('opens','blocking','warnings','exclusions')},'warning_types':dict(collections.Counter(x['type'] for x in native['findings'] if x['severity']=='warning')),'stored_wall_seconds':r['wall_seconds'],'stored_full_cpu_seconds':r['total_cpu_seconds'],'stages':stages,'outer':outer(root.name)})
# Negative previews use the same immutable owned fixture/source as the first positive.
fixture_receipt=read(receipts[0]);fixture_source=Path(fixture_receipt['source']);fixture_candidate=Path(fixture_receipt['candidate'])
for root in roots[2:4]:
 r=read(root/'review.json');control_path=ROOT/'.runs'/(root.name+'-control.json');ctrl=read(control_path)
 assert ctrl['passed'] is True and ctrl['status']==r['status']=='rejected' and ctrl['error']==r['error']
 assert ctrl['source_and_routing_evidence_unchanged'] is True and ctrl['no_ready_html'] is True and not (root/'preview.html').exists()
 assert inv(root/'before')==inv(fixture_source.parent) and inv(root/'project')==inv(fixture_candidate.parent)
 assert ctrl['control_sha256']==p.sha(ROOT/'.runs/native-review-render-controls-001.py')
 assert all(p.sha(ROOT/name)==sha for name,sha in ctrl['source_sha256'].items())
 processes=[read(path) for path in sorted((root/'plot-work').glob('*-process.json'))];assert processes==ctrl['native_processes']
 for step in processes:
  name=step['name'];label,layer=name.split('-',1);work=root/'plot-work';private=work/(name+'-input')
  assert step['argv']==f.SANDBOX+[str(c.CLI),'pcb','export','svg','--mode-single','--layers',layer+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','--output',str(work/'native-plots'/(name+'.svg')),str(private/fixture_source.name)]
  assert step['cleanup_complete'] is True and step['log_bytes']==Path(step['log']).stat().st_size
  base=inv((root/'before') if label=='before' else (root/'project'));p.check_drc_project(base,inv(private),fixture_source.name)
  binding=work/(name+'-input-binding.json')
  if binding.exists():assert read(binding)=={'source':str((root/('before' if label=='before' else 'project'))/fixture_source.name),'input':str(private/fixture_source.name),'before':base,'after':inv(private)}
 if ctrl['mode']=='tamper':
  assert len(processes)==2 and all(x['status']=='success' and x['exit_code']==0 for x in processes)
  mutation=ctrl['observed'][2];assert p.sha(Path(mutation['preserved']))==mutation['before_sha256'] and p.sha(Path(mutation['target']))==mutation['after_sha256']
  assert Path(mutation['preserved']).read_bytes()==v.display_svg(v.svg_bytes(root/'plot-work/native-plots/before-F.Cu.svg'))
  assert mutation['before_sha256']!=mutation['after_sha256']
 else:
  assert len(processes)==1 and processes[0]['status']=='cancelled' and processes[0]['exit_code']==-15 and processes[0]['cancel_signal']=='SIGTERM'
  assert processes[0]['pid']==ctrl['observed'][0]['live_native_group'] and ctrl['observed'][0]['signal']=='SIGTERM'
  # Historical group-gone assertion is in the bound controller and succeeded before its exit0.
 assert r['within_budget'] is True and r['wall_seconds']<30 and r['total_cpu_seconds']<30
 result['negative_previews'].append({'run':str(root.relative_to(ROOT)),'review':file(root/'review.json'),'control':file(control_path),'error':r['error'],'stored_wall_seconds':r['wall_seconds'],'stored_full_cpu_seconds':r['total_cpu_seconds'],'native_stages':[{'name':x['name'],'status':x['status'],'exit_code':x['exit_code'],'cleanup_complete':x['cleanup_complete'],'wall_seconds':x['wall_seconds'],'cpu_seconds':x['cpu_seconds']} for x in processes],'no_ready_html':True,'outer':outer(root.name)})
root=roots[4];summary=read(root/'summary.json');work=root/'work'
assert summary['passed'] is True and summary['inputs_unchanged'] is True
assert {name:sha for name,sha in inv(root).items() if name!='summary.json'}==summary['files']
assert summary['source_sha256']==code and summary['script_sha256']==p.sha(ROOT/'.runs/native-drc-failure-evidence-control-001.py')
assert summary['source_receipt_sha256']==p.sha(receipts[0]) and summary['source_candidate_sha256']==p.sha(fixture_candidate)
parsed={name:p.parse_report(work/(name+'.json'),fixture_candidate.name) for name in ('positive','legacy-prl')}
assert parsed['positive']==summary['positive'] and parsed['legacy-prl']==summary['negative_raw_native']
assert all(p.native_accepted(row) and row['warnings']==0 for row in parsed.values())
for name in parsed:
 binding=read(work/(name+'-binding.json'));assert binding['saved'] is False and binding['before']==inv(Path(binding['source']).parent) and binding['after']==inv(Path(binding['input']).parent)
 process=read(work/(name+'-process.json'));step=next(x for x in summary['steps'] if x['name']==name)
 assert all(step[k]==val for k,val in process.items()) and process['exit_code']==0 and process['status']=='success' and process['cleanup_complete'] is True
 assert process['argv']==f.SANDBOX+[str(c.CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','--refill-zones','--exit-code-violations','--output',str(work/(name+'.json')),binding['input']]
 assert process['cwd']==str(work) and process['log_bytes']==Path(process['log']).stat().st_size
 if name=='positive':p.check_drc_project(binding['before'],binding['after'],fixture_candidate.name)
 else:
  try:p.check_drc_project(binding['before'],binding['after'],fixture_candidate.name)
  except p.Rejected as exc:assert str(exc)==summary['negative_guard']
  else:raise AssertionError('strict legacy PRL guard did not reject')
  changed=[key for key in binding['before'] if binding['before'][key]!=binding['after'].get(key)];assert changed==['fixture.kicad_prl'] and set(binding['before'])==set(binding['after'])
  failure=read(work/'legacy-prl-failure.json');assert failure['passed'] is False and failure['phase']=='project_preservation' and failure['capture_errors']==[]
  assert failure['binding']==binding and failure['validation_copy_before']==binding['before']
  assert failure['error']=={'type':'Rejected','message':summary['negative_guard']}
  assert p.sha(work/'legacy-prl-failure.json')==summary['failure_record_sha256']
  for relative,entry in failure['artifacts'].items():assert entry=={'sha256':p.sha(work/relative),'bytes':(work/relative).stat().st_size}
assert summary['wall_seconds']<30 and summary['total_cpu_seconds']<30
assert sum(x['wall_seconds'] for x in summary['steps'])<=summary['wall_seconds'] and sum(x['cpu_seconds'] for x in summary['steps'])<=summary['total_cpu_seconds']
result['drc_failure_evidence']={'summary':file(root/'summary.json'),'failure_record':file(work/'legacy-prl-failure.json'),'raw_counts':{name:{k:row[k] for k in ('opens','blocking','warnings','exclusions')} for name,row in parsed.items()},'guard':summary['negative_guard'],'failure_phase':failure['phase'],'changed_validation_copy_files':changed,'stored_wall_seconds':summary['wall_seconds'],'stored_full_cpu_seconds':summary['total_cpu_seconds'],'outer':outer(root.name)}
browser=ROOT/'.runs/review-render-browser-attempt-001.json';browser_record=read(browser)
assert browser_record['visual_inspection_performed'] is False and browser_record['workaround_attempted'] is False
(HERE/'browser-attempt.json').write_bytes(browser.read_bytes())
result['browser_attempt']={'original':file(browser),'copy_sha256':p.sha(HERE/'browser-attempt.json'),'record':browser_record}
assert all(inv(Path(path))==value for path,value in initial.items())
assert code=={str(path.relative_to(ROOT)):p.sha(path) for path in sorted((ROOT/'autorouter').glob('*.py'))}
result['unchanged_inventories']=[{'path':str(Path(path).relative_to(ROOT)),'files':len(value),'inventory_sha256':digest(value)} for path,value in initial.items()]
result['source_sha256']=code;result['passed']=True
(HERE/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':True,'positive_costs':[(x['run'],x['stored_wall_seconds'],x['stored_full_cpu_seconds'],x['saved_routing_native_counts']) for x in result['positives']],'negative_previews':[(x['run'],x['error']) for x in result['negative_previews']],'drc_guard':summary['negative_guard'],'inventories_unchanged':len(initial)},indent=2))
