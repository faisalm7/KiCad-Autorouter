"""Owned synthetic4Cu layer-refusal control; prepare/review before execution.

Main mode runs only through the existing90s independent enclosure004. Native
writer mode only changes copper count on its exact fresh owned clone. Original
2Cu inputs are immutable. No engine, GUI interaction or acceptance/export.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, resource, shutil, signal, sys, time

START = time.monotonic()
def cpu():
    return sum(q.ru_utime + q.ru_stime for q in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
RUNTIME = Path(__file__).resolve().parents[1]
HEAD = 'd64e5f1c9e35552eb2eeca93c71c5683fd09c37c'
MANIFEST = '65aa2eb27ac5c61ce96a771bb6d8a65f923220e464886fb43d789377e4c61d5b'
NAME = 'qualify-gui075-direct-four-copper-001.py'
OUTPUT_NAME = 'native7-comparison-control-gui075-direct4Cu-001'
sys.path.insert(0, str(RUNTIME)); sys.dont_write_bytecode = True

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

if len(sys.argv) > 1 and sys.argv[1] == '--native-write':
    assert len(sys.argv) == 6
    runtime, board, before_pin, receipt = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])
    assert runtime == RUNTIME and board == runtime / '.runs' / OUTPUT_NAME / 'project/owned1007-transport.kicad_pcb'
    assert receipt == runtime / '.runs' / OUTPUT_NAME / 'validation/writer-native.json' and not receipt.exists()
    assert digest(runtime / 'runtime-distribution.json') == MANIFEST and digest(board) == before_pin
    import pcbnew, _pcbnew
    from autorouter import config as c
    assert c.ROOT == runtime and c.NATIVE_VERSION == pcbnew.GetBuildVersion() == '10.0.7'
    assert Path(sys.executable).resolve() == c.PYTHON.resolve() and Path(_pcbnew.__file__).resolve() == c.PCBNEW.resolve()
    loaded = pcbnew.LoadBoard(str(board)); assert loaded and loaded.GetCopperLayerCount() == 2
    loaded.SetCopperLayerCount(4)
    pcbnew.SaveBoard(str(board), loaded)
    saved = pcbnew.LoadBoard(str(board)); assert saved and saved.GetCopperLayerCount() == 4
    data = dict(schema=1, native_version=pcbnew.GetBuildVersion(), native_python=str(Path(sys.executable).resolve()),
        native_pcbnew=str(Path(_pcbnew.__file__).resolve()), board=str(board), before_sha256=before_pin,
        after_sha256=digest(board), before_copper_layers=2, after_copper_layers=4,
        operation='LoadBoard fresh clone; SetCopperLayerCount(4); SaveBoard only that new clone; reload count4')
    with receipt.open('x') as stream: json.dump(data, stream, indent=2); stream.write('\n')
    raise SystemExit(0)

from autorouter import pipeline as p, floor_route as f, handoff as h, placement_clearance as io
from autorouter import gui, local_settings as local

def require(value, message):
    if not value: raise p.Rejected(message)

def execute(protocol_path, protocol_pin):
    protocol_path = h.real_path(protocol_path); raw = io.read_bytes(protocol_path, 1024**2)
    require(hashlib.sha256(raw).hexdigest() == protocol_pin, 'frozen caller protocol differs')
    plan = f.read_json(protocol_path); out = Path(plan['output'])
    require(plan['kind'] == 'gui075-owned-synthetic-four-copper-layer-refusal-v1'
        and plan['runtime'] == str(RUNTIME) and p.c.ROOT == RUNTIME and plan['source_head'] == HEAD
        and plan['runtime_manifest_sha256'] == digest(RUNTIME / 'runtime-distribution.json') == MANIFEST
        and plan['whole_wall_full_cpu_seconds'] == 90 and plan['native_job_seconds'] == 30
        and plan['expected_diagnostic_opens'] == 2 and plan['pass_key'] == 'control_passed'
        and plan['controller_args'] == [] and out == RUNTIME / '.runs' / OUTPUT_NAME,
        'exact034 synthetic layer-control contract required')
    require(Path(__file__) == Path(plan['controller']) == RUNTIME / '.runs' / NAME
        and digest(Path(__file__)) == plan['controller_sha256']
        and Path(sys.executable).absolute() == RUNTIME / '.venv/bin/python'
        and Path(sys.prefix).resolve() == RUNTIME / '.venv' and sys.prefix != sys.base_prefix,
        'exact copied controller and034 interpreter required')
    tools = p.tool_manifest(); require(tools == plan['tools'] and tools['git_head'] == HEAD, 'selected runtime tools differ')
    parent_plan = Path(plan['prepared_protocol_path'])
    require(digest(parent_plan) == plan['prepared_protocol_sha256'], '075 source authority changed')
    declared = f.read_json(parent_plan)['recovery']['no-repair']
    source = h.real_path(plan['source']); hashes = plan['source_hashes']; external = Path(declared['original_source'])
    require(str(source) == declared['source'] and hashes == declared['source_hashes']
        and p.tree_hash(source.parent) == p.tree_hash(external.parent) == hashes,
        'exact pristine075 no-repair original source required')
    settings = plan['settings']
    require(settings == dict(schema=1, scope='whole_board_unlocked_routing', seconds=90, adapter='both',
        profile='standard', guidance='native', layers='source_all', scoring_preference=None), 'fixed recover settings required')
    require(not out.exists() and out.parent.is_dir(), 'fresh output required')
    out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out)
    (out / 'protocol.json').write_bytes(raw)
    fixture = out / 'project' / source.name; shutil.copytree(source.parent, fixture.parent)
    destination = out / 'request-output'; destination.mkdir()
    job = p.Job(out / 'validation', 30, protect_local_settings=True)
    report = dict(schema=1, kind=plan['kind'], status='failed', control_passed=False, accepted=False,
        production_admitted=False, routing_accepted=False, export_accepted=False, actual_GUI=False, human_review=False,
        runtime=str(RUNTIME), source_head=HEAD, runtime_manifest_sha256=MANIFEST, tools=tools,
        protocol_sha256=protocol_pin, source=str(source), source_hashes=hashes,
        fixture=str(fixture), settings=settings, steps=job.steps, native_job_seconds=30,
        whole_wall_full_cpu_seconds=90, expected_diagnostic_opens=2,
        scope='New owned synthetic negative fixture only. No original-board constraint relaxation or routing-quality comparison.')
    fixture_hashes = None; native = None; stage_before = None
    def remaining(): return min(88 - (time.monotonic() - START), 88 - (cpu() - CPU0))
    def native_cpu(): return sum((s.get('cpu_seconds') or 0) + (s.get('monitor_cpu_seconds') or 0) for s in job.steps)
    def stable():
        require(h.owned_destination(owner) == out and digest(protocol_path) == protocol_pin
            and digest(out / 'protocol.json') == protocol_pin and digest(Path(__file__)) == plan['controller_sha256']
            and digest(RUNTIME / 'runtime-distribution.json') == MANIFEST and digest(parent_plan) == plan['prepared_protocol_sha256']
            and p.tool_manifest() == tools and p.tree_hash(source.parent) == p.tree_hash(external.parent) == hashes,
            'source/runtime/protocol/controller changed')
        if fixture_hashes is not None: require(p.tree_hash(fixture.parent) == fixture_hashes, 'synthetic source changed after freeze')
        require(remaining() > 0 and native_cpu() <= 30, 'whole or Native control budget exhausted')
    try:
        job.step('write-four-copper', [*f.SANDBOX, p.c.PYTHON, '-B', Path(__file__), '--native-write',
            RUNTIME, fixture, hashes[source.name], job.out / 'writer-native.json'])
        writer = f.read_json(job.out / 'writer-native.json')
        require(writer['after_sha256'] == p.sha(fixture) and writer['before_sha256'] == hashes[source.name]
            and writer['after_copper_layers'] == 4, 'own Native writer proof differs')
        fixture_hashes = p.tree_hash(fixture.parent)
        require(all(fixture_hashes[name] == pin for name, pin in hashes.items() if name != source.name)
            and set(fixture_hashes) == set(hashes), 'original project/rules/schematic/PRL bytes changed')
        require(p.check_schematic_class_support(fixture, class_context=None) is None, 'synthetic source must have no schematic class flags')
        p.preflight(fixture)
        job.native('fixture-metrics', 'metrics', fixture, out / 'fixture-metrics.json')
        metrics = f.read_json(out / 'fixture-metrics.json'); require(metrics['copper_layers'] == 4, 'well-formed four-copper fixture required')
        native = job.drc('fixture-full-drc', fixture, schematic_parity=True)
        stage_before = dict(fixture_hashes)
        require(f.check_drc_stage(job.out, report, 'fixture-full-drc', fixture,
            job.out / 'fixture-full-drc-input' / source.name, False, stage_before,
            schematic_parity=True, sandboxed=False) == native, 'own full-schematic diagnostic proof differs')
        require(native['opens'] == 2, 'expected source opens differ; no clean-board claim')
        before = io.inventory(destination)
        try:
            gui.Request(str(fixture), str(destination), json.dumps(settings), True, 'recover').prepare()
        except ValueError as exc:
            require(str(exc) == 'Experimental thermal recovery supports two source copper layers only; no layers were changed.',
                'different refusal did not demonstrate direct layer guard: ' + str(exc))
            report['refusal'] = str(exc)
        else: raise p.Rejected('four-copper recovery Request unexpectedly created a workspace')
        require(before == io.inventory(destination) == {}, 'static refusal created a workspace')
        stable()
        report.update(status='completed', control_passed=True, original_2Cu_source_unchanged=True,
            copied_project_rules_schematic_PRL_unchanged=True, fixture_hashes=fixture_hashes, writer=writer,
            metrics=metrics, source_native_diagnostic=native, all_findings_retained=True,
            source_diagnostic_is_not_clean=True, refusal_before_workspace=True, actual_GUI_layer_click_performed=False)
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed', control_passed=False,
            error=type(exc).__name__ + ': ' + str(exc))
    report['evidence_sha256'] = f.evidence_inventory(out)
    def account():
        report.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_CPU_seconds=cpu()-CPU0,
            Native_waited_worker_CPU_seconds=native_cpu(), publication_allowance_seconds=2, external_complete_exit_required=True)
        if remaining() <= 0 or native_cpu() > 30: report.update(status='budget_exceeded', control_passed=False)
        if report['status'] != 'completed': report['control_passed'] = False
    def final_check():
        stable()
        require(f.evidence_inventory(out) == report['evidence_sha256'], 'complete evidence changed')
        if native is not None:
            require(f.check_drc_stage(job.out, report, 'fixture-full-drc', fixture,
                job.out / 'fixture-full-drc-input' / source.name, False, stage_before,
                schematic_parity=True, sandboxed=False) == native, 'final diagnostic changed')
        stable(); require(f.evidence_inventory(out) == report['evidence_sha256'], 'final material changed')
        if native is not None: local.check_final_events([(job.out, dict(steps=job.steps, native=native))], p.c.CLI)
    f.publish(out, report, stable, account, remaining, owned=lambda:h.owned_destination(owner), final_check=final_check)
    print(json.dumps({key:report.get(key) for key in ('status','control_passed','error','refusal')}))
    return 0 if report['control_passed'] and report['status'] == 'completed' else 2

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--protocol', type=Path, required=True)
    ap.add_argument('--protocol-sha256', required=True); args = ap.parse_args()
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, interrupted)
    raise SystemExit(execute(args.protocol, args.protocol_sha256))
