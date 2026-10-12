"""Two finite native controls for shared failure evidence; no routing or PAW retry."""
from pathlib import Path
import json,shutil,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, floor_route as f, handoff as h
receipt=ROOT/'.runs/default-tuning-native-001/result.json';r=json.loads(receipt.read_bytes());p.check_result(receipt)
candidate=Path(r['candidate']);before=h.pc.inventory(receipt.parent,max_bytes=h.EVIDENCE_BYTES,max_files=4000,max_entries=8000)
out=ROOT/'.runs/native-drc-failure-evidence-control-001';out.mkdir(exist_ok=False)
start=time.monotonic();cpu=h.cpu_seconds();remaining=lambda:max(0,min(30-(time.monotonic()-start),30-(h.cpu_seconds()-cpu)))
job=f.FloorJob(out/'work',30,remaining)
positive=job.drc('positive',candidate)
assert p.native_accepted(positive) and positive['warnings']==0
negative=out/'legacy-prl-input';shutil.copytree(candidate.parent,negative)
prl=json.loads((ROOT/'.runs/review-render-fixture-002/before/fixture.kicad_prl').read_bytes())
prl['meta']['version']=3;prl['board']['visible_items']=[]
prl_path=negative/candidate.with_suffix('.kicad_prl').name
assert not prl_path.exists();prl_path.write_text(json.dumps(prl,indent=2)+'\n')
source_before=h.pc.inventory(negative);caught=None
try:job.drc('legacy-prl',negative/candidate.name)
except p.Rejected as exc:caught=str(exc)
assert caught=='native DRC modified input or rules: '+prl_path.name,caught
failure=json.loads((job.out/'legacy-prl-failure.json').read_bytes());binding=json.loads((job.out/'legacy-prl-binding.json').read_bytes())
assert failure['passed'] is False and failure['phase']=='project_preservation'
assert failure['binding']==binding and binding['before']==failure['validation_copy_before']==source_before
assert [name for name in source_before if binding['after'].get(name)!=source_before[name]]==[prl_path.name]
assert set(binding['after'])==set(source_before)
for name,entry in failure['artifacts'].items():assert entry and p.sha(job.out/name)==entry['sha256']
actual=p.parse_report(job.out/'legacy-prl.json',candidate.name);assert p.native_accepted(actual) and actual['warnings']==0
assert h.pc.inventory(negative)==source_before
assert h.pc.inventory(receipt.parent,max_bytes=h.EVIDENCE_BYTES,max_files=4000,max_entries=8000)==before
assert remaining()>0
value={'schema':1,'passed':True,'source_receipt':str(receipt),'source_receipt_sha256':p.sha(receipt),'source_candidate_sha256':p.sha(candidate),'positive':positive,'negative_raw_native':actual,'negative_guard':caught,'failure_record_sha256':p.sha(job.out/'legacy-prl-failure.json'),'inputs_unchanged':True,'wall_seconds':time.monotonic()-start,'total_cpu_seconds':h.cpu_seconds()-cpu,'steps':job.steps,'source_sha256':{str(x.relative_to(ROOT)):p.sha(x) for x in sorted((ROOT/'autorouter').glob('*.py'))},'script_sha256':p.sha(Path(__file__)),'scope':'Actual unchanged positive plus owned synthetic old-PRL migration rejection. Native findings alone do not override original-input preservation. No PAW rerun or routing gain.'}
value['files']=h.pc.inventory(out,max_bytes=32*1024**2,max_files=2000,max_entries=4000)
(out/'summary.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({'passed':True,'positive_opens':positive['opens'],'negative_guard':caught,'wall_seconds':value['wall_seconds'],'cpu_seconds':value['total_cpu_seconds']}))
