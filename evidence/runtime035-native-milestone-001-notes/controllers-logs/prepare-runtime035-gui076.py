"""Prepare fresh GUI076 fixtures/launcher only; no GUI or Native qualification.

Adapted from prepare-runtime033-gui074.py. Run only after the separate committed
035 build, full178 and install008 pass. Existing033/074 and original projects
are read-only inputs. No tools, archives, candidate boards or libraries copied.
"""
from pathlib import Path
import datetime, json, os, shutil, sys, time

START = time.monotonic()
ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT/'.runs/runtime-directory-035/runtime'
assert runtime.is_dir(), 'runtime035 must be built and qualified first'
sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, preferences as pref, provenance as pv
from autorouter import floor_route as f, placement_clearance as pc, handoff as h, gui
from autorouter.runner import run

HEAD = '7edc7229ea905e6734bf6cec8ff926a92e6a8613'
GUI = '93963f6a68d3269042298b6a2d374ffbfa18a86315c2ee30cb9cf02d7caf709e'
PIPELINE = '8a0276c178649ff76383865e125c63803a71a15b144ac29905a0c072c67480af'
assert c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
assert h.real_path(runtime) == runtime
prerequisites = {}
for name in ('full-integration-178', 'install-distribution-native-008'):
    receipt = ROOT/'.runs'/name/'execution.json'
    data = f.read_json(receipt)
    assert data.get('passed') is True
    assert data.get('sources_unchanged', data.get('source_unchanged')) is True
    assert data['process']['cleanup_complete'] is True and data['process']['log_truncated'] is False
    prerequisites[str(receipt)] = p.sha(receipt)
install = f.read_json(ROOT/'.runs/install-distribution-native-008/execution.json')
assert install['child_receipt'] == str(runtime.parent/'result.json')
assert p.sha(runtime.parent/'result.json') == install['child_receipt_sha256']
tools = p.tool_manifest(); manifest = runtime/pv.MANIFEST; manifest_pin = p.sha(manifest)
assert tools['git_head'] == HEAD and tools['source_provenance']['kind'] == pv.KIND
assert tools['source_provenance']['manifest_sha256'] == manifest_pin
assert tools['source_provenance']['native_version'] == '10.0.7'
assert f.read_json(manifest)['build_source']['git_head'] == HEAD
for name, digest in (('autorouter/gui.py', GUI), ('autorouter/pipeline.py', PIPELINE)):
    assert p.sha(runtime/name) == tools['implementation_sha256'][name] == digest

references = {
    'partial': (ROOT/'.runs/runtime033-ordinary-partial2Cu-001/protocol.json',
        'e542752678a3005a20f06ea2833673c8c9ff01f5b4d99b4ba1de7cecdd7003dc'),
    'repair': (ROOT/'.runs/runtime033-interf-current-comparison-001/population.json',
        '8ae47cf2d28bfdd63a349364e9c814fb60a0d36d99d11c80dc1658bbcc66b33e'),
    'four_copper': (ROOT/'.runs/runtime033-ordinary-whole4Cu-001/protocol.json',
        '6c991bd99927d03bb9a1170bf27a729cc97616d46ee6e99151ab26ca6a7cc84c'),
}
sources = {}
for label, (path, pin) in references.items():
    assert p.sha(path) == pin
    data = f.read_json(path); board = h.real_path(data['source']); hashes = data['source_hashes']
    assert pc.inventory(board.parent) == hashes
    sources[label] = dict(board=board, hashes=hashes, protocol=str(path), protocol_sha256=pin)
partial = sources['partial']; repair = sources['repair']; four = sources['four_copper']
assert partial['board'] == ROOT/'.runs/task-copper-fixed-alias-native-004/source/owned1007-transport.kicad_pcb'
assert partial['hashes'][partial['board'].name] == '62cb74bf329f3eb259b595881a24ef2ac320b930ca738f732461ca38831f0128'
assert four['board'] == ROOT/'.runs/runtime-directory-019/source-matching/owned-four-copper-forced-inner.kicad_pcb'
assert four['hashes'][four['board'].name] == '1fe544f2ace54e74bb48e88633ae6688a48ba32dee33d1737c93a2fe9dca883e'
assert repair['board'] == ROOT/'.data/boards/kicad-interf-u/interf_u.kicad_pcb'
assert len(repair['hashes']) == 25 and repair['hashes'][repair['board'].name] == 'a740ce7fde77ab6af191e23ece21e57d36bb3c29325879248520dcd9ab47b57e'
assert shutil.disk_usage(ROOT).free > 2*1024**3
session = runtime/'.runs/gui-session076'; launcher = runtime/'.runs/gui-launcher076'
assert h.real_path(session, existing=False) == session and h.real_path(launcher, existing=False) == launcher
assert not os.path.lexists(session) and not os.path.lexists(launcher)
session.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, session)
for label in ('project', 'inspection'):
    shutil.copytree(partial['board'].parent, session/label)
    assert pc.inventory(session/label) == partial['hashes']
(session/'jobs').mkdir(mode=0o700)
settings = pref.validate(dict(pref.DEFAULTS, scope='partial_completion', seconds=90))
p.save_json(session/'route-settings.json', settings)
controls = session/'recovery-controls-001'; controls.mkdir(mode=0o700)
recovery = {}
for label, source, seconds, expected in (
        ('repair', repair, 420, 'fresh validated repair or truthful refusal; no assumed completion'),
        ('no-repair', partial, 90, 'fresh validated incumbent; no repair if unnecessary'),
        ('unsupported4Cu', four, 90, 'GUI refusal before workspace or worker creation')):
    directory = controls/label; directory.mkdir(mode=0o700)
    shutil.copytree(source['board'].parent, directory/'project')
    assert pc.inventory(directory/'project') == source['hashes']
    chosen = pref.validate(dict(pref.DEFAULTS, scope='whole_board_unlocked_routing', seconds=seconds))
    gui.check_thermal_settings(chosen)
    p.save_json(directory/'route-settings.json', chosen)
    recovery[label] = dict(source=str(directory/'project'/source['board'].name),
        original_source=str(source['board']), source_hashes=source['hashes'],
        source_protocol=source['protocol'], source_protocol_sha256=source['protocol_sha256'],
        method='recover', settings=chosen, settings_path=str(directory/'route-settings.json'),
        settings_sha256=p.sha(directory/'route-settings.json'), output_parent=str(session/'jobs'),
        whole_method_seconds=seconds, additional_export_seconds=gui.export_validation_seconds(seconds),
        required_observation=expected, actual_GUI_qualified=False)
required = dict(schema=1, state='PREPARED_ONLY_NOT_EXECUTED', source_head=HEAD,
    runtime_manifest_sha256=manifest_pin, ordinary_method='route', ordinary_settings=settings,
    ordinary_required_roles=['positive', 'high_budget', 'source_control', 'settings_control',
                             'export_control', 'cancel', 'reject'],
    recovery=recovery, recovery_required_roles=['repair', 'no-repair', 'incompatible_settings_refusal',
        'unsupported4Cu_refusal_before_workspace', 'cancel_with_incumbent_retained'],
    ordinary_cancel=dict(method='route', source=recovery['repair']['source'],
        settings=pref.validate(dict(pref.DEFAULTS, seconds=90)),
        scope='Reuse the original Interf copy for an observable ordinary engine interval; no source mutation.'),
    recovery_settings_refusal_examples=[dict(scope='partial_completion'), dict(profile='tuned'),
        dict(adapter='none'), dict(layers=['F.Cu']), dict(scoring_preference='via_low'), dict(seconds=89)],
    recovery_cancel_scope='Use a fresh recovery job. Observe its saved incumbent receipt and an owned active '
        'repair/final-validation process before Cancel, then retain that exact incumbent, actual process/journal '
        'cleanup, rejected/cancelled parent and absence of accepted export. No all-phase or SIGINT-only claim.',
    preserved_boundaries='Exact source/protected/rule/fullSCH and own fresh Native proof; explicit review intent; '
        'no stale/cancel/invalid fallback or electrical claim. Recover budgets cover the whole method; '
        'export remains separate. Actual observed cancellation phase only; forced queued race not presumed.',
    repair_source_rights=f.read_json(references['repair'][0])['source_rights'],
    owned_source_rights='Original project-owned fixtures; same exact source bytes as frozen033 protocols.',
    actual_GUI_qualified=False, Native_qualified=False, project_complete=False)
p.save_json(controls/'protocol-required-001.json', required)
env = {key:value for key,value in os.environ.items()
       if key not in ('PYTHONPATH','PYTHONHOME','KICAD_API_SOCKET','KICAD_API_TOKEN')}
env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')
process = run([*f.SANDBOX, str(runtime/'.venv/bin/python'), '-B', str(runtime/'scripts/install_gui.py'),
    '--output', str(launcher)], cwd=session, env=env, log=session/'prepare-launcher.log', timeout=30,
    max_log_bytes=512*1024, max_workdir_bytes=128*1024**2, max_group_rss_bytes=1024**3)
p.save_json(session/'prepare-launcher-process.json', process)
assert process['status'] == 'success' and process['exit_code'] == 0
assert process['cleanup_complete'] is True and process['log_truncated'] is False
assert h.owned_destination(owner) == session and p.sha(manifest) == manifest_pin and p.tool_manifest() == tools
for source in sources.values(): assert pc.inventory(source['board'].parent) == source['hashes']
for path, pin in prerequisites.items(): assert p.sha(Path(path)) == pin
for path, pin in references.values(): assert p.sha(path) == pin
record = dict(schema=1, recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    source_head=HEAD, runtime_manifest_sha256=manifest_pin, tools=tools,
    source=str(session/'project'/partial['board'].name), source_hashes=partial['hashes'],
    inspection=str(session/'inspection'/partial['board'].with_suffix('.kicad_pro').name),
    settings=settings, settings_path=str(session/'route-settings.json'),
    settings_sha256=p.sha(session/'route-settings.json'), jobs=str(session/'jobs'),
    launcher=str(launcher/'Launch Autorouter.command'), prerequisites_sha256=prerequisites,
    recovery_protocol=str(controls/'protocol-required-001.json'),
    recovery_protocol_sha256=p.sha(controls/'protocol-required-001.json'),
    preparation_wall_seconds_before_publication=time.monotonic()-START,
    actual_GUI_qualified=False, Native_qualified=False, project_complete=False,
    scope='Prepared fresh035/076 ordinary partial90 and separate experimental recovery fixtures only. '
        'All inputs are original source copies, never routed candidates. Historical033/074 and034/075 unchanged. '
        'GUI/native/no-repair/invalid/cancel qualification and measured complete exit costs remain required.')
p.save_json(session/'prepared-state.json', record)
print(json.dumps(record))
