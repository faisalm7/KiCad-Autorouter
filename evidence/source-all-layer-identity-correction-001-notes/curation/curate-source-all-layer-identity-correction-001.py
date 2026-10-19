"""Retain the bounded source correction and constructed tests, no Native execution."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,placement_clearance as io
notes=ROOT/'evidence/source-all-layer-identity-correction-001-notes';output=ROOT/'evidence/source-all-layer-identity-correction-001.json'
assert not notes.exists() and not output.exists()
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
functions=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree','cost')]
exec(compile(ast.Module(body=functions,type_ignores=[]),str(helper),'exec'),globals())
review=ROOT/'.runs/source-all-layer-identity-review-001.json';review_data=json.loads(review.read_bytes())
for name,digest in review_data['source_sha256'].items():assert p.sha(ROOT/name)==digest
for suffix in ('targeted-001','targeted-002','readback-001','readback-002'):
 for extension in ('log','time'):
  name='source-all-layer-identity-'+suffix+'.'+extension;retain(ROOT/'.runs'/name,Path('checks')/name)
for name in ('native7-source-all-alias-correction-plan-001.json','native7-source-all-alias-correction-plan-amendment-001.json','source-all-layer-identity-review-001.json'):
 retain(ROOT/'.runs'/name,Path('plan-and-review')/name)
retain(ROOT/'.runs/native7-source-all-alias-controls-001/fixture-preparation.json',Path('plan-and-review/owned-fixture-preparation.json'))
retain(Path(__file__),Path('curation')/Path(__file__).name);retain(helper,Path('curation/retention-helper030.py'))
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='source-all-signal-layer-identity-source-correction',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,accepted=False,Native_executed=False,installed_qualified=False,actual_GUI=False,human_review=False,source_and_test_sha256=review_data['source_sha256'],mechanism='Source-all2Cu display names bind original canonical IDs/order/signal types to same-load Native standard/display/enabled/lookups and exact exported DSN labels/indices. No source or DSN renaming; candidate layer table and protected/original design fences retained.',review=review_data,checks=dict(targeted001=dict(passed=False,tests=133,cost=cost(ROOT/'.runs/source-all-layer-identity-targeted-001.time'),reason='One faulty swap_rows test mutation did not swap due dynamic target-index evaluation; test fixed only, failure preserved.'),targeted002=dict(passed=True,tests=161,cost=cost(ROOT/'.runs/source-all-layer-identity-targeted-002.time')),readback001=dict(passed=False,cost=cost(ROOT/'.runs/source-all-layer-identity-readback-001.time'),reason='Direct module invocation missed legacy fixture import path; no test executed.'),readback002=dict(passed=True,tests=24,cost=cost(ROOT/'.runs/source-all-layer-identity-readback-002.time'),invocation='unittest discover -s tests -p test_validation_readback.py')),unchanged='Canonical2Cu/4Cu headers, source rules, types, stackup, labels, explicit masks, closed class consumers and B1 default. NUS mixed/power remains unsupported; alias+padless/class combinations fail closed/unqualified.',remaining=['Fresh full185/install013/runtime040 after committed source.','Actual owned aliases/both-sides/protected-via Native six-stage control and unchanged Sonde90/export90; actual short/protected change controls.','Fresh changed-build GUI, final installed fair comparison/breadth, untouched confirmation, Windows safeguards/Native, restoration headroom, authorized engineer/physical validation.'],accounting='All failed invocations retained separately; tests overlap and do not measure routing quality. Whole authoring/research/AI review CPU unknown, not zero. No Native/engine execution by curation.',rights='Project-owned source/test/control metadata and logs, GPL-3.0-or-later. No NUS geometry, private boards, engine/app binaries or bulk data.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
p.save_json(output,record);print(json.dumps(dict(files=len(files),bytes=total,packet_sha256=p.sha(output))))
