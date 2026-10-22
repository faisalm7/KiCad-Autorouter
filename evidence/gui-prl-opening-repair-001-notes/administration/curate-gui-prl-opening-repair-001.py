"""Retain the opening regression and partial GUI089 using shared text helpers."""
from pathlib import Path
import ast,datetime,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
from scripts import report_current_comparison as shared
notes=ROOT/'evidence/gui-prl-opening-repair-001-notes';target=ROOT/'evidence/gui-prl-opening-repair-001.json'
assert not notes.exists() and not target.exists();refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('retain','tree')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
probe=ROOT/'.runs/gui089-queued-metadata-probe-001';counter=f.read_json(probe/'result.json')
assert p.sha(probe/'result.json')=='bec7a89a000288f52059e7902872d4aa4c243d71c48a2267db228439cb1d2cc1'
assert counter['probe_execution_passed'] is True and counter['actual_GUI'] is False
passed=ROOT/'.runs/gui-prl-opening-targeted-002';process=f.read_json(passed/'process.json')
assert process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated']
assert 'Ran 88 tests' in (passed/'command.log').read_text() and (passed/'command.log').read_text().rstrip().endswith('OK')
failed=f.read_json(ROOT/'.runs/gui-prl-opening-targeted-001/process.json');assert failed['status']=='disk_limit' and failed['exit_code'] is None
tree(probe,Path('counterexample'));tree(passed,Path('targeted002'));tree(ROOT/'.runs/gui-prl-opening-targeted-001',Path('failed-preflight001'))
partial=ROOT/'.runs/gui-runtime056-089-partial-20261021-001';tree(partial,Path('actual-GUI089-partial'))
runtime=ROOT/'.runs/runtime-directory-056/runtime';g=runtime/'.runs/gui-session089'
assert not list((g/'jobs').iterdir());assert (g/'gui089-saved-settings-001.json').read_bytes()==(g/'route-settings.json').read_bytes()
retain(g/'gui089-saved-settings-001.json',Path('actual-GUI089-partial/saved-settings.json'))
for name in ('gui-prl-opening-targeted-001.log','gui-prl-opening-targeted-001-time.log','gui-prl-opening-targeted-002.log','gui-prl-opening-targeted-002-time.log','gui-runtime056-089-launch-20261021-001.log','gui-runtime056-089-launch-20261021-001-time.log','runtime056-resume-20261021-001.json'):
    retain(ROOT/'.runs'/name,Path('administration')/name)
retain(Path(__file__),Path('administration')/Path(__file__).name)
pins={name:p.sha(ROOT/name) for name in ('autorouter/gui.py','autorouter/local_settings.py','tests/test_gui_export_inspection.py')}
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='queued-opening-retained-PRL-metadata-repair-with-partial-GUI089-v1',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,release_qualified=False,Native_executed=False,GUI_qualified=False,runtime056_unchanged=True,runtime056_manifest_sha256='b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded',counterexample=dict(result_sha256=p.sha(probe/'result.json'),cases=['same-byte hardlink1to2','same-byte flags0toUF_IMMUTABLE'],scope='Constructed actual callback body with mocked reader/opener, no wx/Native/real opening. Existing Native PRL policy refused while queued callback opened the mock; byte negative and unchanged positive behave as recorded.'),repair='Reuse one current-metadata helper for regular canonical single-link zero-flags PRLs in existing Native replay and final GUI fence. Retained bounded bytes/directories/exact receipt still checked first; no Native acceptance cache or guard weakening.',implementation_sha256=pins,targeted=dict(passed=True,tests=88,complete_cost=shared.complete_cost(ROOT/'.runs/gui-prl-opening-targeted-002-time.log'),scope='Unit/callback regression only, not actual GUI/Native qualification.'),failed_targeted_preflight001=dict(complete_cost=shared.complete_cost(ROOT/'.runs/gui-prl-opening-targeted-001-time.log'),cause='Runner monitored full checkout rather than finite log directory and refused before test spawn.002 uses the established full-suite log-directory monitoring pattern with child chdir, same resource bounds. No cap raise or Native rerun.'),actual_GUI089_partial=dict(toolbar_launched_current_runtime=True,initial_closed_ack_refused=True,loaded_original_partial90=True,saved_preset_bytes_match=True,routing_jobs=0,complete_launcher_cost=shared.complete_cost(ROOT/'.runs/gui-runtime056-089-launch-20261021-001-time.log'),scope='Actual CUA launch/setup/inspection/toolbar/refusal/load/save observations only. Stopped before routing after reproduced correctness gap. Manager and idle router closed normally; next changed candidate needs fresh qualification.'),independent_AI_review=dict(reviewer='/root/context_reuse_skeptic',source_only=True,no_concrete_issue_found=True,source_pins=pins,limits='No tests/Native/GUI execution or human approval by reviewer; atomic editor loading remains outside scope.'),next_gate='Audit/commit source correction, build a new immutable candidate and run meaningful full Native/install/GUI qualification. Do not mutate056 or transfer its GUI authority.',rights='Owned code/fixtures/diagnostic text only; no private or foreign CAD or tool binaries. New raw remains Mac-only/outside010; no full restoration.',accounting='Complete exits retained once. Counterexample.42wall/.30CPU from its own recorded exit; launcher interactive interval is not route compute. Authoring/AI review/interactive UI and curation add costs; unknown is notzero.',files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,targeted_tests=88,Native=False,GUI_complete=False)))
