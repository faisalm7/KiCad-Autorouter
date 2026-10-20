"""Retain bounded existing GUI preparation metadata; execute no GUI or Native job."""
from pathlib import Path
import ast, datetime, hashlib, json, math, re, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, placement_clearance as io, provenance as pv
notes = ROOT/'evidence/gui-runtime056-089-preparation-001-notes'
target = ROOT/'evidence/gui-runtime056-089-preparation-001.json'
assert not notes.exists() and not target.exists()
refs = {}; files = []; material = []; total = 0
helper = ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper) == 'b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes = [n for n in ast.parse(helper.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == 'retain']
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(helper)+'::retain', 'exec'), globals())
timing = ROOT/'evidence/runtime050-native-milestone-002-notes/shared-helpers/report_current_comparison.py'
assert p.sha(timing) == 'aa630b7d0aad9e7a2356ddc0fbb03894578fd4bff9a601e9a04c104fed86c9f7'
nodes = [n for n in ast.parse(timing.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(timing)+'::cost', 'exec'), globals())
runtime = ROOT/'.runs/runtime-directory-056/runtime'
prepared = runtime/'.runs/gui-session089/prepared-state.json'
assert p.sha(prepared) == '1c1cde60088af1c96158450856cf84ef10214e972b200137d62df5b765e98722'
j = json.loads(prepared.read_bytes())
assert j['state'] == 'PREPARED_ONLY_NOT_EXECUTED' and j['actual_GUI_qualified'] is False and j['Native_executed'] is False
assert j['source_head'] == 'a03b5e8b6ae523d9f099cf211815900053629fe3'
assert p.sha(runtime/'runtime-distribution.json') == j['runtime_manifest_sha256'] == 'b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded'
roles = {}
for name, row in j['roles'].items():
    assert p.tree_hash(Path(row['source']).parent) == row['source_hashes']
    assert p.sha(Path(row['settings_path'])) == row['settings_sha256']
    roles[name] = {key:row[key] for key in ('source','inspection','method','settings','settings_path','settings_sha256','source_hashes')}
launcher = Path(j['launcher'])
for rel, digest_value in j['launcher_hashes'].items():
    assert p.sha(launcher.parent/rel) == digest_value
assert not list(Path(j['jobs']).iterdir())
for path, rel in ((prepared,'prepared-state.json'), (ROOT/'.runs/prepare-runtime056-gui089.py','prepare-runtime056-gui089.py'),
                  (ROOT/'.runs/prepare-runtime056-gui089.log','prepare-runtime056-gui089.log'),
                  (ROOT/'.runs/prepare-runtime056-gui089-time.log','prepare-runtime056-gui089-time.log'),
                  (launcher,'Launch Autorouter.command'), (launcher.parent/'install.json','install.json'), (Path(__file__),Path(__file__).name)):
    retain(path, Path(rel))
p.save_json(notes/'files.json', dict(schema=1, files=files, material=material))
p.save_json(target, dict(schema=1, kind='runtime056-gui089-prepared-only-access-gate-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_head=j['source_head'],
    runtime_manifest_sha256=j['runtime_manifest_sha256'], prepared_state_sha256=p.sha(prepared), roles=roles,
    launcher=j['launcher'], launcher_sha256=p.sha(launcher), jobs=j['jobs'], source_settings_unchanged=True,
    actual_GUI=False, actual_toolbar_launch=False, workflow_delivered=False, full_GUI_qualified=False,
    project_complete=False, Native_executed=False, preparation_cost=complete_cost(ROOT/'.runs/prepare-runtime056-gui089-time.log'),
    current_access_observation='Fresh CUA getApp of exact isolated KiCad bundle returned: The Mac is locked and automatic unlock could not unlock it. Earlier cgWindowNotFound remains a separate observed window failure, not proof of lock.',
    owner_action='One unlock request already pending; no repeat request or security/sleep change. Prepared056 jobs remain empty. Existing055 manager retained; close it normally when accessible before starting056 launcher.',
    historical_setup=dict(path='evidence/gui-runtime055-088-setup-gate-001.json', sha256=p.sha(ROOT/'evidence/gui-runtime055-088-setup-gate-001.json'), transfers_GUI_authority=False),
    native_prerequisites=[dict(path=name,sha256=p.sha(ROOT/name)) for name in ('evidence/runtime056-native-milestone-001.json','evidence/runtime056-ir-delivery-002.json')],
    limits='Preparation and hash replay only. No current toolbar/settings/refusal/routing/rendered review/choice/cancel/fresh-export/checked-opening or queued-callback GUI qualification. No standalone/cleanOS/Windows/electrical/engineer review claim.',
    backup_scope='Owned preparation metadata only; raw050-056/GUI remains Mac-only outside010. No new full restoration performed.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,prepared_only=True,actual_GUI=False)))
