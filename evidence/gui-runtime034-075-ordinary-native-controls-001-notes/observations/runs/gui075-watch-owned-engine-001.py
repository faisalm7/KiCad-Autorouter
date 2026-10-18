"""Finite075 read-only process oracle; GUI/runner alone owns cancellation.

Usage: python3 -B THIS --workspace autorouter-gui-<32hex>
    --role ordinary|recovery --output ABSOLUTE_FRESH075_OBSERVATION.json
No invocation/phase is qualified by preparing this helper. Recovery observations
require a saved incumbent before an owned repair/final-validation worker.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, re, shlex, subprocess, sys, time

START = time.monotonic(); CPU0 = time.process_time()
ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.runs/runtime-directory-034/runtime'
BASE = RUNTIME / '.runs/gui-session075'
HEAD = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
MANIFEST = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
PROTOCOL = BASE / 'recovery-controls-001/protocol-required-001.json'
PROTOCOL_SHA = 'e2c1f3b0deec7d535e140657456c5b7acced6e1c2608efbe1e9bb69a6ebdbf5c'
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, handoff as h, placement_clearance as io

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--workspace', required=True, help='Exact075 workspace basename, never a receipt selector')
ap.add_argument('--role', required=True, choices=('ordinary', 'recovery'))
ap.add_argument('--output', type=Path, required=True)
a = ap.parse_args()
assert re.fullmatch(r'autorouter-gui-[0-9a-f]{32}', a.workspace)
workspace = h.real_path(BASE / 'jobs' / a.workspace)
output = h.real_path(a.output, existing=False)
assert output.is_absolute() and output.parent == BASE and not output.exists()
assert p.c.ROOT == RUNTIME and p.c.NATIVE_VERSION == '10.0.7'
assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST and p.sha(PROTOCOL) == PROTOCOL_SHA
prepared_path = BASE / 'prepared-state.json'; prepared = f.read_json(prepared_path)
prepared_pin = p.sha(prepared_path); protocol = f.read_json(PROTOCOL)
assert prepared['source_head'] == protocol['source_head'] == HEAD
assert prepared['runtime_manifest_sha256'] == protocol['runtime_manifest_sha256'] == MANIFEST
assert prepared['recovery_protocol'] == str(PROTOCOL) and prepared['recovery_protocol_sha256'] == PROTOCOL_SHA
tools = p.tool_manifest(); assert tools == prepared['tools']
assert tools['git_head'] == HEAD and tools['source_provenance']['git_head'] == HEAD
assert tools['source_provenance']['kind'] == 'runtime-directory-v1'
assert tools['source_provenance']['manifest_sha256'] == MANIFEST
repair = protocol['recovery']['repair']; source = Path(repair['source'])
assert source == BASE / 'recovery-controls-001/repair/project/interf_u.kicad_pcb'
hashes = repair['source_hashes']; assert len(hashes) == 25
assert p.tree_hash(source.parent) == p.tree_hash(Path(repair['original_source']).parent) == hashes
declared = protocol['ordinary_cancel'] if a.role == 'ordinary' else repair
assert declared['source'] == str(source) and declared['method'] == ('route' if a.role == 'ordinary' else 'recover')
settings_path = workspace / 'settings.json'; settings = f.read_json(settings_path)
assert settings == declared['settings']
assert settings == dict(schema=1, scope='whole_board_unlocked_routing', seconds=90 if a.role == 'ordinary' else 420,
                       adapter='both', profile='standard', guidance='native', layers='source_all', scoring_preference=None)
settings_pin = p.sha(settings_path); owner = {}; h.capture_destination(owner, workspace)
root = workspace / 'route'
cli = [str(RUNTIME / '.venv/bin/python'), '-B', '-m', 'autorouter', declared['method'], str(source)]
cli += (['--settings', str(settings_path)] if a.role == 'ordinary' else ['--seconds', str(settings['seconds'])])
cli += ['--output', str(root)]
app = p.c.CLI.parents[2]; manager = str(app / 'Contents/MacOS/kicad')
result = None; incumbent = None; polls = 0; query_error = None

def words(command):
    try: return shlex.split(command)
    except ValueError: return []

def saved_incumbent():
    path = root / 'incumbent/result.json'
    if not path.is_file(): return None
    raw = io.read_bytes(path, 1024**2); data = f.read_json(path)
    assert hashlib.sha256(raw).hexdigest() == p.sha(path)
    assert data['source'] == str(source) and data['source_hashes'] == hashes and data['tools'] == tools
    assert data['scope'] == 'whole_board_unlocked_routing' and data['engine_profile'] == 'standard' and data['adapter'] == 'both'
    assert data['status'] in ('routing_accepted', 'drc_rejected') and type(data['accepted']) is bool
    assert data['accepted'] is (data['status'] == 'routing_accepted')
    candidate = Path(data['candidate']); assert candidate == root / 'incumbent/candidate' / source.name
    assert p.sha(candidate) == data['candidate_sha256']
    assert p.sha(root / 'incumbent/final-drc.json') == data['native_report_sha256']
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), raw_utf8=raw.decode('utf8'),
        status=data['status'], accepted=data['accepted'], candidate=str(candidate), candidate_sha256=data['candidate_sha256'],
        native_report_sha256=data['native_report_sha256'], source_hashes=hashes,
        scope='Exact saved receipt/selection pins only; no fresh Native run or new acceptance by this observer.')

def phase(argv):
    if not argv: return None
    if a.role == 'ordinary':
        if (argv[0] == str(p.c.JAVA) and '-jar' in argv and '-de' in argv and '-do' in argv
                and argv[argv.index('-jar') + 1] == str(p.c.JAR)
                and argv[argv.index('-de') + 1] == str(root / 'task.dsn')
                and argv[argv.index('-do') + 1] == str(root / 'routes.ses')):
            return 'ordinary-engine'
        return None
    if (len(argv) == 9 and Path(argv[0]).resolve() == p.c.PYTHON.resolve()
            and argv[1:3] == ['-B', str(root / 'recovery/worker.py')]
            and argv[3:] == [str(root / 'recovery/input' / source.name), str(root / 'recovery/request.json'),
                str(root / 'recovery/geometry.json'), '10.0.7', str(p.c.PYTHON), str(p.c.PCBNEW)]):
        return 'repair-thermal-geometry'
    if (argv[:3] != [str(p.c.CLI), 'pcb', 'drc'] or '--output' not in argv
            or argv.index('--output') + 1 >= len(argv)): return None
    report = argv[argv.index('--output') + 1]
    for name in ('refill-drc', 'final-drc'):
        if report == str(root / (name + '.json')): return 'parent-final-validation-' + name
        for index in range(1, 5):
            if report == str(root / 'recovery' / ('trial-%02d' % index) / (name + '.json')):
                return 'repair-trial-%02d-' % index + name
    return None

while time.monotonic() - START < 45 and polls < 900:
    if a.role == 'recovery' and incumbent is None: incumbent = saved_incumbent()
    try:
        raw = subprocess.check_output(['/bin/ps', '-axo', 'pid=,ppid=,pgid=,command='],
                                      timeout=min(2, max(.001, 45 - (time.monotonic() - START))))
    except subprocess.TimeoutExpired:
        query_error = 'Bounded ps query timed out; no observed-phase claim.'
        break
    assert len(raw) <= 1024**2
    processes = {}
    for line in raw.decode().splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) == 4: processes[int(parts[0])] = (int(parts[1]), int(parts[2]), parts[3])
    polls += 1
    owners = set()
    for pid, (parent, group, command) in processes.items():
        argv = words(command)
        if (len(argv) == 4 and argv[-3:] == ['-B', '-m', 'autorouter.gui']
                and Path(argv[0]).name == 'Python' and Path(argv[0]).is_relative_to(app)
                and parent in processes and processes[parent][2] == manager): owners.add(pid)
    assert owners, 'No current owned selected-KiCad GUI ancestry found'
    cli_pids = {pid for pid, (_, _, command) in processes.items() if words(command) == cli}
    for pid, (parent, group, command) in processes.items():
        if str(workspace) not in command: continue
        observed = phase(words(command))
        if observed is None or a.role == 'recovery' and incumbent is None: continue
        chain = []; current = pid
        while current in processes and len(chain) < 16:
            chain.append(current)
            if current in owners: break
            current = processes[current][0]
        if chain[-1] not in owners or not any(q in cli_pids for q in chain): continue
        result = dict(schema=1, actual_process_observed=True, actual_engine_observed=a.role == 'ordinary',
            actual_recovery_process_observed=a.role == 'recovery', role=a.role, observed_phase=observed,
            PID=pid, PPID=parent, PGID=group, owned_ancestry=chain, argv_text=command,
            argv_text_sha256=hashlib.sha256(command.encode()).hexdigest(), expected_CLI_argv=cli,
            workspace=str(workspace), observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            incumbent=incumbent, scope='One actual process snapshot under exact owned CLI/GUI ancestry. No signal, cancellation, cleanup, acceptance or all-phase guarantee.')
        break
    if result is not None: break
    time.sleep(min(.05, max(0, 45 - (time.monotonic() - START))))
if result is None:
    result = dict(schema=1, actual_process_observed=False, actual_engine_observed=False,
        actual_recovery_process_observed=False, role=a.role, workspace=str(workspace), incumbent=incumbent,
        query_error=query_error,
        scope='No eligible owned process observed within finite45second bound; no cancellation-phase claim.')
assert h.owned_destination(owner) == workspace and p.sha(settings_path) == settings_pin
assert p.sha(PROTOCOL) == PROTOCOL_SHA and p.sha(prepared_path) == prepared_pin
assert p.sha(RUNTIME / 'runtime-distribution.json') == MANIFEST and p.tool_manifest() == tools
assert p.tree_hash(source.parent) == p.tree_hash(Path(repair['original_source']).parent) == hashes
if result['actual_process_observed']: assert p.tree_hash(root / 'snapshot') == hashes
if incumbent is not None: assert p.sha(Path(incumbent['path'])) == incumbent['sha256']
result.update(runtime=str(RUNTIME), source_head=HEAD, runtime_manifest_sha256=MANIFEST,
    source=str(source), source_hashes=hashes, settings=settings, settings_sha256=settings_pin,
    recovery_protocol_sha256=PROTOCOL_SHA, observer_sha256=p.sha(Path(__file__)),
    observer_wall_seconds=time.monotonic() - START, observer_parent_CPU_seconds=time.process_time() - CPU0,
    polls=polls, ps_child_CPU_seconds=None,
    accounting='Oracle overhead separate. ps child CPU not instrumented, notzero; enclosing complete-exit accounting remains required. No routing-speed claim.')
with output.open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
print(json.dumps(result), flush=True)
