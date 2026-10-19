"""Retain the bounded non-admitting observation, reusing shared text retention."""
from pathlib import Path
import ast, datetime, hashlib, json, runpy, sys
ROOT=Path(__file__).resolve().parents[1];runtime=ROOT/'.runs/runtime-directory-035/runtime'
sys.path.insert(0,str(runtime));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io,local_settings as local
notes=ROOT/'evidence/runtime035-hierarchy-observation-001-notes';packet=ROOT/'evidence/runtime035-hierarchy-observation-001.json'
assert not notes.exists() and not packet.exists()
refs={};files=[];material=[];total=0;queued=[]
previous=ROOT/'evidence/runtime035-native-milestone-001.json';d=f.read_json(previous)
index=ROOT/d['files_index']['path'];assert p.sha(index)==d['files_index']['sha256']
for row in f.read_json(index)['files']+f.read_json(index)['material']:
 refs.setdefault(row['sha256'],row.get('path',row.get('retained')))
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
functions=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
assert len(functions)==3;exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'))
shared=retain
def retain(path,name):queued.append((Path(path),Path(name)))
newbase=ROOT/'.runs/runtime035-hierarchy-observation-003';plan=f.read_json(newbase/'protocol.json')
assert p.sha(newbase/'protocol.json')=='906a18dd332a29e022fd6219606be6cb9e259835d69ccc865e947061b50ab302'
controller=ROOT/'.runs/qualify-runtime035-hierarchy-observation-003.py'
assert p.sha(controller)==plan['controller_sha256']=='16bef76d117cbe3a206245bb88771835558cbe9a571cd6bd747bdf333f5643b5'
defs=runpy.run_path(str(controller));defs['source_contract']();prior_netlist,prior_board=defs['completed_export001'](plan)
out=Path(plan['output']);r=f.read_json(out/'result.json');outer=f.read_json(newbase/'enclosure/result.json')
assert p.sha(out/'result.json')=='263d10940aff846c8586685c36c80e6fa4fe8221e8657cfb48b83aecdb5ca873'
assert r['status']=='completed' and r['control_passed'] is True and r['disposition']=='defer'
assert all(r[k] is False for k in ('accepted','routing_accepted','support_admitted','production_admitted','actual_GUI','human_review'))
assert outer['passed'] is True and outer['child_sha256']==p.sha(out/'result.json')
assert outer['process']['cleanup_complete'] is True and outer['process']['log_truncated'] is False
assert f.evidence_inventory(out)==r['evidence_sha256']==outer['completed_evidence']
assert p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']==p.tree_hash(out/'observation/candidate')
observed=f.read_json(out/'observation/native-pcb.json');assert defs['extract'](prior_netlist,observed,prior_board)==r['observations']
assert [r['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,24,206,0]
stage=f.check_drc_stage(out/'observation',r,'source-full-drc',out/'observation/candidate'/Path(plan['source']).name,out/'observation/source-full-drc-input'/Path(plan['source']).name,False,plan['source_hashes'],schematic_parity=True)
assert stage==r['native'];argv=r['steps'][-1]['argv'];assert '--refill-zones' in argv and '--save-board' not in argv
review=ROOT/'.runs/runtime035-hierarchy-source-result-review-001.json';assert p.sha(review)=='9768ad9824912e591f06b7ac2dada799fd6ae53dabc1fa708136a35ecf7d73c1'
for folder,label in ((newbase,'resume003-enclosure'),(ROOT/'.runs/runtime035-hierarchy-observation-001','failed001-enclosure')):
 tree(folder,Path(label))
old=Path(plan['completed_export001']['root'])
for name in ('protocol.json','result.json','observation/hierarchy.net','observation/hierarchy-netlist-process.json','observation/hierarchy-netlist.log'):
 retain(old/name,Path('failed001')/name)
for name in ('protocol.json','result.json','observation/extracted-observations.json','observation/native-pcb.json','observation/observe-pcb.py','observation/pcb-observation-input-binding.json','observation/pcb-observation-process.json','observation/pcb-observation.log','observation/source-full-drc-binding.json','observation/source-full-drc-process.json','observation/source-full-drc.json','observation/source-full-drc.log'):
 retain(out/name,Path('resume003')/name)
controllers=('qualify-runtime035-hierarchy-observation-001.py','freeze-runtime035-hierarchy-observation-001.py',
 'qualify-runtime035-hierarchy-observation-002.py','prepare-runtime035-hierarchy-resume-002.py',
 'qualify-runtime035-hierarchy-observation-003.py','prepare-runtime035-hierarchy-resume-003.py',
 'enclose-native7-independent-control-004.py','breadth-next-gap-runtime035-001.json',
 'runtime035-hierarchy-lead-source-review-001.json','runtime035-hierarchy-source-result-review-001.json',
 'runtime035-native-packet-lead-readback-001.json','runtime035-native-packet-lead-readback-001-command.log','runtime035-native-packet-lead-readback-001-time.log',
 'curate-runtime035-native-milestone-001.py','curate-runtime035-native-milestone-001-command.log','curate-runtime035-native-milestone-001-time.log')
for name in controllers:retain(ROOT/'.runs'/name,Path('controllers-readback')/name)
for stem in ('freeze-runtime035-hierarchy-observation-001','prepare-runtime035-hierarchy-resume-002','prepare-runtime035-hierarchy-resume-003'):
 for suffix in ('-command.log','-time.log'):retain(ROOT/'.runs'/(stem+suffix),Path('costs')/(stem+suffix))
for stem in ('runtime035-hierarchy-observation-001','runtime035-hierarchy-observation-003'):
 for suffix in ('-controller.log','-time.log'):retain(ROOT/'.runs'/(stem+suffix),Path('costs')/(stem+suffix))
retain(ROOT/'.runs/runtime035-hierarchy-observation-002/protocol.json',Path('unexecuted002/protocol.json'))
for name in ('LICENSE.CC-BY-SA-4.0','LICENSE.README'):retain(Path(plan['source']).parent/'_licenses'/name,Path('source-licences')/name)
retain(Path(__file__),Path('controllers-readback')/Path(__file__).name)
new={}
for path,name in queued:
 raw=io.read_bytes(path,4*1024**2);assert b'\0' not in raw;raw.decode('utf8');pin=hashlib.sha256(raw).hexdigest()
 if pin in refs:assert p.sha(ROOT/refs[pin])==pin
 else:new.setdefault(pin,len(raw))
assert sum(new.values())<16*1024**2 and len(new)<2000
for path,name in queued:shared(path,name)
assert len(files)==len(new) and total==sum(new.values())
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='runtime035-bounded-hierarchy-observation-with-raw-export-reuse',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 diagnostic_completed=True,accepted=False,routing_accepted=False,support_admitted=False,production_admitted=False,actual_GUI=False,human_review=False,project_complete=False,
 source_head=plan['source_head'],runtime_manifest_sha256=plan['runtime_manifest_sha256'],source=str(Path(plan['source']).relative_to(ROOT)),source_hashes=plan['source_hashes'],source_rights=plan['source_rights'],
 considered_population=dict(exposed=25,static_eligible=7,static_unsupported=18,unchanged=True),
 reason='Hierarchy is a documented sole static blocker for two exposed cohort rows. This one existing licensed repeated-sheet source tests whether instance paths, terminals and classes are observable before any product admission.',
 observations=dict(sheets=5,files=2,Native_footprints=114,Native_pads=327,schematic_nets=80,Native_copper_nets=80,all_Native_footprint_paths_observed=True,raw_unknowns=48),
 interpretation='Independent AI readback identifies47 no-net None/empty-string differences and5 present multi-UUID stamp nodes that the scalar parser rejects. Raw unknowns remain unchanged. This removes an observability suspicion, not the need for a versioned unit/instance/class binder, invalid controls or final Native qualification.',
 source_Native_counts=[0,24,206,0],source_findings_scope='24 source clearance errors,206 warnings,7 ignored checks retained. No routed candidate, source invalidity classification or completion gain inferred. Expected opens would not alone make an invalid source.',
 evidence_wording_correction='Raw003 source_zone_refill_performed:false and protocol no-refill prose are inaccurate: the actual source-full-drc argv requests --refill-zones in memory. It omits --save-board; all17 copied and external source files remain exact. Raw records are preserved, not rewritten. No saved refilled or routed candidate exists.',
 disposition='defer product admission; retain observability for a bounded future versioned binder, no more Native attempts needed for this probe',
 preserved_attempts=dict(failed001=dict(cost=cost(ROOT/'.runs/runtime035-hierarchy-observation-001-time.log'),reason='Native export completed then generated onePRL; strict project inventory stopped before PCB/DRC. Original17 files exact; no missing post-export binding fabricated.'),
 unexecuted002=dict(Native_executed=False,reason='Lead caught singleton-loop tuple defect before execution; frozen draft/protocol retained.'),
 resumed003=dict(cost=cost(ROOT/'.runs/runtime035-hierarchy-observation-003-time.log'),only_missing_Native_steps=['pcb-observation','source-full-drc'],netlist_repeated=False)),
 preparation_costs={name:cost(ROOT/'.runs'/(name+'-time.log')) for name in ('freeze-runtime035-hierarchy-observation-001','prepare-runtime035-hierarchy-resume-002','prepare-runtime035-hierarchy-resume-003')},
 Native035_curation_cost=cost(ROOT/'.runs/curate-runtime035-native-milestone-001-time.log'),
 review=dict(hierarchy_AI_source_result_sha256=p.sha(review),scope='Separate source/result review of003; reviewer authored no003. Not humanPCB review. Separate Native035 packet result reviewer failed at model capacity before a receipt; lead exact-material readback only.'),
 limits='No hierarchy routing support, new eligible family, algorithm/comparison/holdout, actual035GUI, Windows or release qualification. Conditional non-final-drc field-finding collector mismatch stays documented in experimental controller; actual003 did not trigger it. No product code changed.',
 backup_scope='Sanitized essential text only. Licensed raw source projects, complete copied inputs, Native preferences and newer raw work stay on thisMac outside008/010. Not a full artifact backup or restoration.',
 retention=dict(shared_helper=str(helper.relative_to(ROOT)),shared_helper_sha256=p.sha(helper),new_bytes=total,new_files=len(files),max_new_bytes=16*1024**2,max_new_files=2000),
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
assert p.tool_manifest()==plan['tools'] and p.tree_hash(Path(plan['source']).parent)==plan['source_hashes']
assert f.evidence_inventory(out)==r['evidence_sha256']==outer['completed_evidence']
local.check_final_events([(out/'observation',r)],p.c.CLI)
p.save_json(packet,record)
print(json.dumps(dict(files=len(files),bytes=total,material=len(material),diagnostic_completed=True,support_admitted=False)))
