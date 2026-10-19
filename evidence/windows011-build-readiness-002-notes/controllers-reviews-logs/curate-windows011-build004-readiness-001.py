"""Retain the bounded build-only contract; no Windows execution."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
notes=ROOT/'evidence/windows011-build-readiness-002-notes';packet=ROOT/'evidence/windows011-build-readiness-002.json'
assert not notes.exists() and not packet.exists()
review=ROOT/'.runs/windows011-build004-contract-review-001.json';assert p.sha(review)=='1afcaf2e449c884119da881d198bb47d01c0aa70d6aa6bef83cbc9d51704c335'
v=f.read_json(review);plan=ROOT/'scripts/windows_native_slice/persistent_guard_build_protocol004.json'
assert p.sha(plan)==v['protocol']['sha256']=='1e77ac76423031bfc606a35d02ee69bb84f596679250e85d33c2eb046e4ac3ae'
for row in v['protocol']['pins']:assert p.sha(ROOT/row['path'])==row['sha256']==row['frozen_sha256']
assert p.sha(ROOT/v['workflow']['path'])==v['workflow']['sha256']
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
names=['windows011-build004-contract-review-001.json','freeze-windows011-build004-001.py','freeze-windows011-build004-001-command.log','freeze-windows011-build004-001-time.log','curate-windows011-policy-attempt002-001-command.log','curate-windows011-policy-attempt002-001-time.log','update-windows011-closed-plan-001.py','record-runtime035-continuation007-001.py']
for name in names:retain(ROOT/'.runs'/name,Path('controllers-reviews-logs')/name)
retain(Path(__file__),Path('controllers-reviews-logs')/Path(__file__).name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(packet,dict(schema=1,kind='Windows011-build004-distinct-NULL-only-readiness',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prospective_only=True,project_complete=False,Windows_support=False,Native_admitted=False,
 protocol=dict(path=str(plan.relative_to(ROOT)),sha256=p.sha(plan)),source_files_sha256=f.read_json(plan)['source_files_sha256'],workflow=v['workflow'],
 decision='One targeted build-null regression of demonstrated C4389 after auditedpush/readback and fresh public/sequential preflight. Both real-policy011 attempts failed; the two-attempt policy protocol is closed. No third policy attempt or Native admission.',
 source_review=dict(path=str(review.relative_to(ROOT)),sha256=p.sha(review),scope='Separate AI source/contract review, not Windows execution or human review.'),
 costs=dict(freeze_wall_seconds=0.09,freeze_CPU_seconds=0.05,actual002_curation_wall_seconds=0.24,actual002_curation_CPU_seconds=0.17,authoring_research_AI_review_whole_CI_CPU=None),
 runtime_protection='No /WX/cap/custody/control weakening or runner completion policy change. Sourcebase580 is historical; exact futurecommit/protocolSHA supplied externally. Workflow fixedbuild-null; retained direct API sid-canary exists but is not selected or authorized by this record.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
print(json.dumps(dict(files=len(files),bytes=total,executed=False)))
