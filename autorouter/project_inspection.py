"""Read-only saved-project Native inspection using the existing validation core.

This report describes the source, including expected unrouted connections.
It never authorizes a candidate or waives the route/export validators.
"""
from __future__ import annotations

import math
from pathlib import Path
import signal
import time

from . import pipeline as p, floor_route as f, handoff as h, config as c
from . import placement_clearance as pc
from .runner import elapsed_time

POLICY = 'saved-project-native-inspection-v1'
PLACEMENT_POLICY = 'saved-project-native-placement-inspection-v1'
MAX_SECONDS = 90


def _seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or not 5 <= value <= MAX_SECONDS:
        raise ValueError('Inspection budget must be finite 5–90 seconds.')
    return float(value)


def inspect(board, output, seconds=60, *, placement_context=False):
    """Inspect a new copy with actual refill/full-schematic DRC; no source writes."""
    from .design_intent import inspect_project
    from .gui import source_inventory
    seconds = _seconds(seconds)
    if type(placement_context) is not bool or placement_context and c.NATIVE_VERSION != '10.0.7':
        raise ValueError('Explicit placement inspection requires pinned Native10.0.7.')
    started, parent_started, children_started = elapsed_time(), time.process_time(), f.child_cpu()
    board = h.real_path(board); output = h.real_path(output, existing=False)
    if output == board.parent or board.parent in output.parents:
        raise ValueError('Inspection output must be outside the saved source project.')
    if output.exists():
        raise ValueError('Use a new inspection output directory.')
    static = inspect_project(board)
    before = static['source_hashes']
    tools = p.tool_manifest()
    p.check_storage(active_root=output)
    # Job owns all Native processes, copies, local settings and cancellation.
    job = p.Job(output, seconds, protect_local_settings=True)
    job.deadline = started + seconds
    snapshot = output / 'snapshot' / board.name
    record = dict(schema=1, policy=PLACEMENT_POLICY if placement_context else POLICY, source=str(board), source_hashes=before,
                  static=static, tools=tools, accepted=False, status='inspection_failed',
                  native_validation_performed=False, budget_seconds=seconds,
                  cpu_budget_seconds=seconds)
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    def interrupted(*_):
        raise KeyboardInterrupt
    try:
        for sig in previous:
            signal.signal(sig, interrupted)
        pc.copy_project(board.parent, snapshot.parent)
        if source_inventory(snapshot) != before or source_inventory(board) != before:
            raise ValueError('Source changed during inspection capture.')
        native = job.drc('source-drc', snapshot, schematic_parity=True)
        record.update(native=native, steps=job.steps, native_validation_performed=True)
        checked = f.check_drc_stage(output, record, 'source-drc', snapshot,
            output / 'source-drc-input' / board.name, False, before,
            schematic_parity=True, sandboxed=False)
        if f.canonical(checked) != f.canonical(native):
            raise ValueError('Native inspection readback differs.')
        if placement_context:
            from . import local_settings as local
            path = output / 'placement-context.json'
            state = {'complete': False}; start = len(job.steps)
            with local.preserve(snapshot.with_suffix('.kicad_prl'), output, job._local_settings_owner,
                                cleanup_complete=lambda: state['complete']) as protection:
                try:
                    job.native('placement-context', 'placement-context', snapshot, path)
                finally:
                    steps = job.steps[start:]
                    state['complete'] = (len(steps) == 1 and steps[0].get('name') == 'placement-context'
                                         and steps[0].get('cleanup_complete') is True)
            record.update(steps=job.steps,
                          placement_context=dict(file=path.name, sha256=p.sha(path),
                              local_settings_policy=local.JOB_POLICY, protection=protection,
                              process_sha256=p.sha(output/'placement-context-process.json')))
            check_placement_context(output, record, snapshot, before)
        if source_inventory(board) != before or source_inventory(snapshot) != before:
            raise ValueError('Source changed during Native inspection.')
        if p.tool_manifest() != tools:
            raise ValueError('Inspection runtime changed.')
        elapsed = elapsed_time() - started
        costs = p.sequential_cpu_components(time.process_time() - parent_started,
                                            f.child_cpu() - children_started, job.steps)
        if elapsed > seconds or costs['total_cpu_seconds'] > seconds or job.remaining() <= 0:
            raise ValueError('Inspection exhausted its whole wall/CPU budget.')
        record.update(status='inspection_ready', wall_seconds=elapsed, **costs,
            native_report_sha256=p.sha(output / 'source-drc.json'),
            note='Unrouted connections are routing demand, not by themselves an invalid source design. '
                 'Warnings and other findings remain visible. This is inspection, not acceptance.')
        p.check_resource_accounting(record)
    except (Exception, KeyboardInterrupt) as exc:
        record.update(status='inspection_cancelled' if isinstance(exc, KeyboardInterrupt) else 'inspection_failed',
                      reason=type(exc).__name__ + ': ' + str(exc), steps=job.steps,
                      wall_seconds=elapsed_time() - started)
        try:
            record.update(p.sequential_cpu_components(time.process_time() - parent_started,
                          f.child_cpu() - children_started, job.steps))
        except Exception as cost_error:
            record['resource_accounting_error'] = str(cost_error)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    h.owned_destination(job._local_settings_owner)
    p.save_json(output / 'inspection.json', record)
    return record


def check(path):
    """Replay shared Native/source checks; never treat this as routing acceptance."""
    from .gui import source_inventory
    from .design_intent import inspect_project
    path = h.real_path(path); directory = path.parent
    record = f.read_json(path)
    fields = {'schema','policy','source','source_hashes','static','tools','accepted','status',
        'native_validation_performed','budget_seconds','cpu_budget_seconds','native','steps',
        'wall_seconds','parent_cpu_seconds','child_cpu_seconds','control_child_cpu_seconds',
        'monitor_cpu_seconds','total_cpu_seconds','native_report_sha256','note'}
    placement_context = type(record) is dict and record.get('policy') == PLACEMENT_POLICY
    if placement_context:
        fields.add('placement_context')
    if (type(record) is not dict or set(record) != fields or type(record.get('schema')) is not int
            or record.get('schema') != 1 or record.get('policy') not in (POLICY, PLACEMENT_POLICY)
            or record.get('status') != 'inspection_ready' or record.get('accepted') is not False
            or record.get('native_validation_performed') is not True):
        raise ValueError('A completed saved-project inspection is required.')
    budget = _seconds(record.get('budget_seconds'))
    for key in ('wall_seconds', 'total_cpu_seconds'):
        value = record.get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= budget:
            raise ValueError('Inspection cost/budget evidence differs.')
    if record.get('cpu_budget_seconds') != budget:
        raise ValueError('Inspection CPU budget differs.')
    p.check_resource_accounting(record)
    source = h.real_path(record['source'])
    before = record['source_hashes']; material = h.evidence_witness(directory)
    if source_inventory(source) != before or source_inventory(directory / 'snapshot' / source.name) != before:
        raise ValueError('Inspected source changed; inspect it again.')
    if f.canonical(inspect_project(source)) != f.canonical(record.get('static')):
        raise ValueError('Static project findings changed.')
    p.check_recorded_tool_pins(record['tools'])
    native = f.check_drc_stage(directory, record, 'source-drc', directory / 'snapshot' / source.name,
        directory / 'source-drc-input' / source.name, False, before,
        schematic_parity=True, sandboxed=False)
    if (f.canonical(native) != f.canonical(record.get('native'))
            or p.sha(directory / 'source-drc.json') != record.get('native_report_sha256')):
        raise ValueError('Inspection findings changed.')
    if placement_context:
        check_placement_context(directory, record, directory / 'snapshot' / source.name, before)
    if source_inventory(source) != before or h.evidence_witness(directory) != material:
        raise ValueError('Inspection source or evidence changed during readback.')
    return record


def check_placement_context(directory, record, snapshot, hashes):
    """Replay a same-source Native capture through the existing process proof."""
    from . import placement_annotations as annotations
    from . import local_settings as local
    from .gui import source_inventory
    if c.NATIVE_VERSION != '10.0.7':
        raise ValueError('Pinned Native placement context version differs.')
    reference = record.get('placement_context')
    expected_keys = {'file','sha256','local_settings_policy','protection','process_sha256'}
    if (type(reference) is not dict or set(reference) != expected_keys
            or reference['file'] != 'placement-context.json'
            or reference['sha256'] != p.sha(directory/'placement-context.json')
            or reference['local_settings_policy'] != local.JOB_POLICY
            or reference['process_sha256'] != p.sha(directory/'placement-context-process.json')):
        raise ValueError('Placement context reference changed.')
    data = f.read_json(directory / 'placement-context.json')
    fields = {'schema','kind','native_version','source','board_sha256','project_sha256',
              'schematic_sha256','board_saved','context'}
    if (type(data) is not dict or set(data) != fields or type(data['schema']) is not int
            or data['schema'] != 1 or data['kind'] != 'autorouter.native-placement-context.v1'
            or data['native_version'] != '10.0.7' or data['source'] != str(snapshot)
            or data['board_saved'] is not False
            or any(data[key] != hashes[snapshot.with_suffix(suffix).name] for key,suffix in (
                ('board_sha256','.kicad_pcb'),('project_sha256','.kicad_pro'),('schematic_sha256','.kicad_sch')))):
        raise ValueError('Placement context source binding differs.')
    context = annotations.validate(data['context'])
    if context['source_board_sha256'] != data['board_sha256']:
        raise ValueError('Placement annotation source differs.')
    f.process_check(directory, record, 'placement-context',
        [str(c.PYTHON), str(c.ROOT/'autorouter/native.py'), 'placement-context', str(snapshot), str(directory/'placement-context.json')])
    local.check_preserved(snapshot.with_suffix('.kicad_prl'), hashes, reference['protection'])
    if source_inventory(snapshot) != hashes:
        raise ValueError('Placement snapshot changed during geometry readback.')
    return context
