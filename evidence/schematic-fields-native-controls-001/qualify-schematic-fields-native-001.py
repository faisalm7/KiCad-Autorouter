from pathlib import Path
import copy,json,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,sexpr as sx,schematic_field_evidence as fields
out=ROOT/'.runs/schematic-fields-native-controls-001';out.mkdir();start=time.monotonic();cpu=time.process_time()+f.child_cpu()
src=ROOT/'.runs/nus-original-native-001/original/src';original_hashes=p.tree_hash(src)
prior=ROOT/'.runs/nus-native-paired-001/run/B1';prior_record=f.read_json(prior/'result.json');retained=Path(prior_record['candidate'])
assert p.sha(retained)==prior_record['candidate_sha256'] and prior_record['accepted'] is False
assert p.immutable(sx.read(retained))==p.immutable(sx.read(src/'usb_led.kicad_pcb'))
p.save_json(out/'protocol.json',{'schema':1,'tools':p.tool_manifest(),'source_hashes':original_hashes,'retained_candidate_sha256':p.sha(retained),
 'scope':'Fresh current savingrefill/mandatorypour audit/complete nativeparity and complete effectivefield proof. Reuse retained rejectedB1 routing only for validator controls, noengine/quality/retroacceptance. Authored PCBfield negatives preserve originals and source project rules. Native ordered fields place Description after Datasheet, allowing a real hidden-later-field control.','cases':['sentinel-positive','hidden-later-field-negative','real-url-negative'],'wall_cpu_budget':120})
record={'status':'failed','passed':False,'observations':[]}
remaining=lambda:max(0,min(120-(time.monotonic()-start),120-(time.process_time()+f.child_cpu()-cpu)))
try:
 for case in ('sentinel-positive','hidden-later-field-negative','real-url-negative'):
  folder=out/case;shutil.copytree(src,folder/'candidate');board=folder/'candidate/usb_led.kicad_pcb';board.write_bytes(retained.read_bytes());tree=sx.read(board)
  if case!='sentinel-positive':
   ref='D1' if case=='hidden-later-field-negative' else 'J1'
   footprint=next(fp for fp in sx.children(tree,'footprint') if any(sx.unquote(n[1])=='Reference' and sx.unquote(n[2])==ref for n in sx.children(fp,'property')))
   key='Description' if case=='hidden-later-field-negative' else 'Datasheet'
   prop=next(n for n in sx.children(footprint,'property') if sx.unquote(n[1])==key)
   prop[2]='"OWNED-DELIBERATE-FIELD-MISMATCH"';sx.write(board,tree)
  before=p.tree_hash(board.parent);job=f.FloorJob(folder/'job',remaining(),remaining)
  digest,native=p.validate_candidate(job,tree,board,before,[])
  expected=dict(before);expected[board.name]=digest
  observed=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',board,job.out/'final-drc-input'/board.name,False,expected,schematic_parity=True)
  assert observed==native
  accepted=p.native_accepted(native)
  assert accepted==(case=='sentinel-positive')
  parity=f.read_json(job.out/'final-drc.json')['schematic_parity']
  sentinel=[n for n in parity if n.get('type')==fields.TYPE and n.get('description')=="Field 'Datasheet' differs (PCB: '~', Schematic: '')"]
  row={'case':case,'accepted':accepted,'candidate_sha256':digest,'native':native,'steps':job.steps,'sentinel_warning_count':len(sentinel)}
  if case=='hidden-later-field-negative':
   d1_uuid=sx.unquote(sx.one(footprint,'uuid')[1]);hidden=any(any(i.get('uuid')==d1_uuid for i in n['items']) for n in sentinel)
   assert hidden,'negative did not exercise a hidden later field mismatch'
   row['same_first_native_sentinel_hides_later_field_mismatch']=hidden
  record['observations'].append(row)
 record.update(status='qualified',passed=True)
except (Exception,KeyboardInterrupt) as exc:record['reason']=type(exc).__name__+': '+str(exc)
record.update(source_unchanged=p.tree_hash(src)==original_hashes,wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu)
if not record['source_unchanged'] or max(record['wall_seconds'],record['full_cpu_seconds'])>120:record['passed']=False
p.save_json(out/'result.json',record);print(json.dumps({k:record.get(k) for k in ('status','passed','reason','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
