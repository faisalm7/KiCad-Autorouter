"""Read-only independent audit of actual retained native handoff evidence.
No native/engine/GUI commands. Only this review directory receives outputs.
"""
import hashlib,json,math,subprocess,sys,time,traceback
from pathlib import Path
from types import SimpleNamespace
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,sexpr as sx,config as c
from experiments.placement_handoff_native_v1 import driver as d
from experiments.placement_production_controls_v1 import driver as prior
HERE=Path(__file__).resolve().parent;RUN=ROOT/'.runs/placement-handoff-native-001'
EXPECTED='e3620b0673c1971943eb40e20b412a71dfa1e958b422f409838d6f3fa587e4e8'
checks=[];start=time.monotonic();result={'schema':1,'review':'Independent AI offline actual-evidence audit; not human PCB review','native_jobs':0,'engine_jobs':0,'gui_actions':0,'network_calls':0}
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def sha(path):return hashlib.sha256(pc.read_bytes(path)).hexdigest()
def inv(path):return pc.inventory(path,max_bytes=100*1024*1024,max_files=4000,max_entries=8000)
def uid(node):return sx.unquote(sx.one(node,'uuid')[1])
def xy(node,key):return tuple(sx.one(node,key)[1:])
try:
 before=inv(RUN);raw_summary=pc.read_bytes(RUN/'summary.json');data=f.read_json(RUN/'summary.json')
 check('exact root-announced summary',hashlib.sha256(raw_summary).hexdigest()==EXPECTED)
 check('completed controls true',data['status']=='completed' and data['controls_passed'] is True and data['original_inputs_unchanged'] is True)
 check('no additional acceptance/GUI/live apply/engine claims',all(data[k] is False for k in ['routing_accepted','gui_qualified','live_apply_qualified','new_engine_execution']))
 check('fixed two cases', [x['case'] for x in data['cases']]==['positive','missing_via'] and len(data['steps'])==2)
 inp=data['inputs'];receipt=Path(inp['receipt']);handoff=Path(inp['handoff']);source=Path(inp['source']);candidate=Path(inp['candidate'])
 material={str(x):inv(x) for x in [source.parent,candidate.parent,receipt.parent,handoff.parent]}
 check('original accepted receipt hash',sha(receipt)==inp['receipt_sha256']==d.RECEIPT_SHA)
 check('new handoff exact record hash',sha(handoff)==inp['handoff_sha256'])
 for path,key in [(source.parent,'source_hashes'),(candidate.parent,'candidate_hashes'),(receipt.parent,'evidence'),(handoff.parent,'handoff_tree')]:check('complete recorded inventory '+key,material[str(path)]==inp[key])
 check('fresh pure central receipt readback',p.check_result(receipt)==inp['verified'])
 review=f.read_json(handoff)
 check('handoff status policy',review['status']=='ready_for_manual_review' and review['input_policy']=='placement-clearance-v1' and review['source_receipt_schema']==3 and review['native_validation_performed'] is False)
 check('handoff full provenance inventories',review['source_project_hashes']==inp['source_hashes'] and review['routing_evidence_hashes']==inp['evidence'])
 check('handoff complete copied project',inv(Path(review['project']))==review['initial_project_hashes']==inp['candidate_hashes'])
 check('handoff board receipt identity',review['receipt']==str(receipt) and review['receipt_sha256']==inp['receipt_sha256'] and review['candidate_sha256']==d.CANDIDATE_SHA==review['verified_candidate_sha256'])
 check('exact current HEAD',subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==data['tools']['git_head']=='c29fc88fd5cfee9192840b6592a7f27833a34ebd')
 check('all current pinned tools and core manifest',p.tool_manifest()==data['tools'])
 check('complete saved code inventory',inv(RUN/'code')==data['code_inventory'])
 for name,digest in data['code_inventory'].items():
  path=ROOT/name;check('current code '+name,sha(path)==digest)
  blob=subprocess.check_output(['git','show',data['tools']['git_head']+':'+name],cwd=ROOT,timeout=3)
  check('committed code '+name,hashlib.sha256(blob).hexdigest()==digest)
 for name,digest in review['runtime_source_sha256'].items():check('handoff runtime source '+name,sha(Path(name))==digest)
 check('reviewed native controller exact',data['code_inventory']['experiments/placement_handoff_native_v1/driver.py']=='5a0f2cf37c79da9585bfc9b9fb8d7383a51a7cec15cd754c038060e763e66c60')
 check('reviewed handoff exact',data['code_inventory']['autorouter/handoff.py']=='74f022bae8a8d89ebf86d7d2a3255a7c41a6f171e041ecc0c73ee5346a82a936')
 original=sx.read(candidate);routes=p.routes(original);vias=[x for x in routes if x[0]=='via'];check('one required positive via',len(vias)==1)
 via=vias[0];adjacent=[x for x in routes if x[0]=='segment' and sx.one(x,'net')==sx.one(via,'net') and xy(via,'at') in (xy(x,'start'),xy(x,'end'))]
 check('via joins two copper sides',len(adjacent)==2 and {sx.unquote(sx.one(x,'layer')[1]) for x in adjacent}=={'F.Cu','B.Cu'})
 required={uid(x) for x in adjacent};case_out=[]
 for case,step in zip(data['cases'],data['steps']):
  name=case['case'];folder=RUN/name;board=folder/'candidate'/candidate.name;native_input=folder/'native-drc-input'/candidate.name
  raw=f.read_json(folder/'native-drc.json');binding=f.read_json(folder/'native-drc-binding.json');process=f.read_json(folder/'native-drc-process.json')
  check(name+' completed inventory',inv(folder)==data['completed_evidence'][str(folder)])
  check(name+' case summary exact',f.read_json(folder/'case.json')==case)
  check(name+' current case candidate inventory',inv(board.parent)==case['candidate_hashes'])
  check(name+' raw version/schema/source/all severities',raw['kicad_version']=='10.0.0' and raw['$schema']=='https://schemas.kicad.org/drc.v1.json' and raw['source']==candidate.name and raw['included_severities']==['error','warning','exclusion'])
  findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity'];check(name+' no exclusions',all(not x.get('excluded',False) and x['severity']!='exclusion' for x in findings))
  counts={'opens':len(raw['unconnected_items']),'blocking':sum(x['severity']=='error' for x in raw['violations']+raw['schematic_parity']),'warnings':sum(x['severity']=='warning' for x in findings),'exclusions':0}
  check(name+' independent raw counters',all(case['native'][k]==v for k,v in counts.items()))
  check(name+' production parser parity',p.parse_report(folder/'native-drc.json',candidate.name)==case['native'])
  check(name+' unchanged ignored checks',raw['ignored_checks']==inp['ignored_checks'])
  check(name+' original project rules bytes',board.with_suffix('.kicad_pro').read_bytes()==candidate.with_suffix('.kicad_pro').read_bytes()==source.with_suffix('.kicad_pro').read_bytes())
  check(name+' original immutable board geometry',p.immutable(sx.read(board))==p.immutable(original))
  check(name+' native binding exact paths/no save',binding['source']==str(board) and binding['input']==str(native_input) and binding['saved'] is False)
  check(name+' native input existing bytes unchanged',binding['before']==case['candidate_hashes'] and all(binding['after'].get(k)==v for k,v in binding['before'].items()))
  additions=set(binding['after'])-set(binding['before']);check(name+' only permissible PRL addition',additions=={'fixture.kicad_prl'})
  check(name+' actual native input after inventory',inv(native_input.parent)==binding['after'])
  check(name+' exact DRC argv no save/engine',step['argv']==d.drc_argv(folder,board) and '--save-board' not in step['argv'])
  check(name+' process status cleanup',step['name']=='native-drc' and step['cwd']==str(folder) and step['cleanup_complete'] is True and step['exit_code']==(0 if name=='positive' else 5) and step['status']==('success' if name=='positive' else 'nonzero_exit'))
  # Job.drc appends binding identifiers after the subprocess receipt was saved.
  check(name+' process record matches root step',all(step[k]==v for k,v in process.items()) and set(step)-set(process)=={'validated_input_sha256','emitted_candidate'})
  check(name+' step candidate identity',step['validated_input_sha256']==sha(board) and step['emitted_candidate']==str(board))
  for file,digest in case['stage_hashes'].items():check(name+' frozen stage '+file,sha(folder/file)==digest)
  job=SimpleNamespace(out=folder,steps=[step]);check(name+' independent reused process/input checker',prior.check_drc(job,'native-drc',board,case['native'])==case['binding'])
  check(name+' recipe adjacent IDs',set(case['recipe']['adjacent_route_uuids'])==required and case['recipe']['positive_via_uuid']==uid(via))
  if name=='positive':
   check(name+' all candidate files unchanged',inv(board.parent)==inp['candidate_hashes'])
   check(name+' native positive actually clean',not findings and p.native_accepted(case['native']) and counts==dict(opens=0,blocking=0,warnings=0,exclusions=0))
  else:
   after=sx.read(board);check(name+' exactly original via deleted',after==[x for x in original if x is not via])
   check(name+' all other project files identical',{k:v for k,v in case['candidate_hashes'].items() if k!=board.name}=={k:v for k,v in inp['candidate_hashes'].items() if k!=board.name})
   hit=raw['unconnected_items'];check(name+' expected single required-via open',len(hit)==1 and hit[0]['severity']=='error' and {x['uuid'] for x in hit[0]['items']}==required)
   check(name+' expected two dangling warnings',len(raw['violations'])==2 and {x['items'][0]['uuid'] for x in raw['violations']}==required and all(x['type']=='track_dangling' and x['severity']=='warning' for x in raw['violations']))
   check(name+' targeted finding and actual rejection',case['targeted_findings']==hit and not p.native_accepted(case['native']) and counts==dict(opens=1,blocking=0,warnings=2,exclusions=0))
  case_out.append({'case':name,'counts':counts,'native_report_sha256':sha(folder/'native-drc.json'),'candidate_sha256':sha(board),'existing_native_input_files_unchanged':len(binding['before']),'allowed_added_files':sorted(additions),'exit_code':step['exit_code'],'cleanup_reported':step['cleanup_complete']})
 check('fixed shared caps',data['budget_seconds']==data['cpu_budget_seconds']==60 and data['output_ceiling_bytes']==20*1024*1024)
 check('finite positive measured samples',all(type(data[k]) in (int,float) and math.isfinite(data[k]) and 0<data[k]<60 for k in ['wall_seconds','total_cpu_seconds']))
 check('child CPU arithmetic',math.isclose(data['child_step_cpu_seconds'],sum(s['cpu_seconds'] for s in data['steps']),abs_tol=1e-10) and data['total_cpu_seconds']>=data['child_step_cpu_seconds'])
 check('step wall enclosed',sum(s['wall_seconds'] for s in data['steps'])<data['wall_seconds'])
 check('four project copies accounted',data['planned_project_copy_bytes']==4*sum((candidate.parent/k).stat().st_size for k in inp['candidate_hashes']))
 total=sum((RUN/k).stat().st_size for k in before);check('actual full output within cap',total<=data['output_ceiling_bytes'])
 for path,known in material.items():check('final original unchanged '+path,inv(Path(path))==known)
 check('final actual run unchanged',inv(RUN)==before and sha(RUN/'summary.json')==EXPECTED)
 check('final current runtime/head/tools unchanged',p.tool_manifest()==data['tools'])
 result.update(passed=True,summary_sha256=EXPECTED,code_head=data['tools']['git_head'],case_results=case_out,required_via_uuid=uid(via),adjacent_route_uuids=sorted(required),original_material_unchanged=True,actual_run_files=len(before),actual_run_bytes=total,stored_wall_seconds=data['wall_seconds'],stored_total_cpu_seconds=data['total_cpu_seconds'],child_step_cpu_seconds=data['child_step_cpu_seconds'],accounting_point=data['accounting_point'],limitations=['Stored prepublication sample is not an independently measured full invocation time; actual source enforces a final acceptance cap after its last scan/readback.','Reported cleanup and process records are mutable local evidence, not authenticated telemetry.','Both native controls concern the exact owned disposable review project; no GUI/live apply/undo or new routing-quality claim.'])
except BaseException as exc:
 result.update(passed=False,error=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
finally:
 result.update(check_count=len(checks),checks=checks,audit_wall_seconds=time.monotonic()-start)
 target=HERE/'audit-001.json'
 if target.exists():raise FileExistsError(target)
 target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','traceback']},indent=2))
 if not result['passed']:sys.exit(1)
