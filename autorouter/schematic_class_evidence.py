"""Shared narrow flat-class observations; no routing or guard waiver.

SPDX-License-Identifier: GPL-3.0-or-later

Actual worker execution belongs to the supplied bounded Job. This helper uses
the existing source inventory, process reader and PRL lifecycle. The caller must
still prove original/source/snapshot freshness and enforce the supported task
context. Replaying a task observation never reads its now-overwritten candidate
PCB: exact task bytes must be reconstructed by the central routing reader.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

from . import config as c, floor_route as f, handoff as h, local_settings as local
from . import placement_clearance as pc, preferences, schematic_classes as q, sexpr as sx

CONTEXT = 'native-route-flat-classes-v1'
MAX_PROJECT_BYTES = 100 * 1024 * 1024
MAX_PROJECT_FILES = 2000
MAX_PROJECT_ENTRIES = 4000
MAX_LOG_BYTES = 512 * 1024
STAGES = ('task', 'final')


def _fail(message):
    raise ValueError('schematic class evidence: ' + message)


def _stage(stage):
    if type(stage) is not str or stage not in STAGES:
        _fail('literal task/final stage required')
    return stage


def record_key(stage):
    return 'schematic_class_' + _stage(stage)


def step_name(stage):
    return _stage(stage) + '-classes-netlist'


def paths(directory, stage):
    stage = _stage(stage); directory = Path(directory)
    return {'input': directory/(stage+'-classes-input'),
            'netlist': directory/(stage+'-classes.net'),
            'binding': directory/(stage+'-classes-binding.json'),
            'proof': directory/(stage+'-classes-proof.json')}


def present(directory, data, stage):
    """Detect orphaned observation material as well as advertised metadata."""
    files = [*paths(directory, stage).values(),
             Path(directory)/(step_name(stage)+'-process.json'),
             Path(directory)/(step_name(stage)+'.log')]
    steps = data.get('steps', [])
    return (record_key(stage) in data
        or any(path.exists() or path.is_symlink() for path in files)
        or type(steps) is list and any(type(row) is dict and row.get('name') == step_name(stage) for row in steps))


def check_local_settings(directory, stage):
    """Repeat non-byte guard state after a caller's final freshness witness.

    This alone is not proof validation. Call only after check and an unchanged
    complete evidence witness have already bound the saved protection record.
    """
    files = paths(directory, stage); binding = _json(files['binding'])
    board = Path(binding['input'])
    if board.parent != files['input']:
        _fail('class guard input path differs')
    local.check_preserved(board.with_suffix('.kicad_prl'), binding['before'], binding['protection'])


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(path):
    return preferences._parse(pc.read_bytes(path, q.MAX_BYTES), q.MAX_BYTES)


def _inventory(path):
    return pc.inventory(path, max_bytes=MAX_PROJECT_BYTES,
                        max_files=MAX_PROJECT_FILES, max_entries=MAX_PROJECT_ENTRIES)


def requirement(board):
    """Return None or a source-bound pending check, never Native qualification.

    Scan only the finite current project. Other captured schematics cannot hide
    a class flag or hierarchy outside the paired root. No source file changes.
    """
    board = local.canonical(Path(board))
    if board.suffix != '.kicad_pcb':
        _fail('paired native PCB required')
    captured = _inventory(board.parent)
    if board.name not in captured:
        _fail('paired PCB is missing from captured project')
    paired = board.with_suffix('.kicad_sch')
    flagged = []
    for name, digest in captured.items():
        if Path(name).suffix.casefold() != '.kicad_sch':
            continue
        raw = pc.read_bytes(board.parent/name, q.MAX_BYTES)
        if _sha(raw) != digest:
            _fail('schematic changed during requirement scan')
        tree = q._tree(raw, 'schematic', 'kicad_sch')
        version = sx.one(tree, 'version')
        if (version is None or len(version) != 2 or type(version[1]) is not str
                or len(version[1]) != 8 or not version[1].isascii()
                or not version[1].isdecimal() or int(version[1]) <= 0):
            _fail('malformed source schematic version')
        pending = [tree]; has_flag = False
        while pending:
            node = pending.pop()
            if node and node[0] == 'sheet':
                _fail('schematic hierarchy remains unsupported')
            if node and node[0] == 'netclass_flag':
                has_flag = True
            pending.extend(child for child in node[1:] if type(child) is list)
        if has_flag:
            flagged.append(name)
    if not flagged:
        if _inventory(board.parent) != captured:
            _fail('source changed during requirement scan')
        return None
    if flagged != [paired.name]:
        _fail('class flags outside the paired flat root remain unsupported')
    raw_board = pc.read_bytes(board, q.MAX_BYTES)
    raw_project = pc.read_bytes(board.with_suffix('.kicad_pro'), q.MAX_BYTES)
    raw_schematic = pc.read_bytes(paired, q.MAX_BYTES)
    configured, known, policy = q._source_classes(preferences._parse(raw_project, q.MAX_BYTES))
    symbols, flags = q._source_schematic(q._tree(raw_schematic, 'schematic', 'kicad_sch'), configured)
    tree = q._tree(raw_board, 'board', 'kicad_pcb')
    # Reuse the exact2/4Cu identity qualification, without Native execution.
    table = sx.one(tree, 'layers', [])
    copper = [row for row in table[1:] if type(row) is list and len(row) > 2
              and type(row[1]) is str and sx.unquote(row[1]).endswith('.Cu')]
    if len(copper) == 4:
        q.nc.four_copper_source_layers(tree)
    else:
        from .layer_policy import _source_layers
        _source_layers(tree)
    partitions, terminals = q._board_partitions(tree, symbols)
    if (_inventory(board.parent) != captured
            or any(captured.get(path.name) != _sha(raw) for path, raw in
                   ((board, raw_board), (board.with_suffix('.kicad_pro'), raw_project), (paired, raw_schematic)))):
        _fail('original source changed during requirement qualification')
    return {'schema': 1, 'context': CONTEXT, 'status': 'pending_native_class_parity',
        'native_validation_performed': False, 'class_parity_qualified': False,
        'accepted': False, 'routing_accepted': False, 'production_qualified': False,
        'source': str(board), 'source_hashes': captured, 'class_flags': flags,
        'source_class_policy': policy, 'known_class_identities': sorted(known),
        'components': len(symbols), 'terminals': len(terminals), 'nets': len(partitions)}


def _expected_files(data, board_raw, source, project_raw, schematic_raw):
    if type(data) is not dict:
        _fail('routing data object required')
    before = data.get('source_hashes')
    if (type(before) is not dict or not before or len(before) > MAX_PROJECT_FILES
            or any(type(name) is not str or type(value) is not str
                   or q.fields.SHA.fullmatch(value) is None for name, value in before.items())):
        _fail('complete original source hashes required')
    board = Path(source)
    if board.name not in before:
        _fail('original board missing from source hashes')
    expected = dict(before); expected[board.name] = _sha(board_raw)
    for name, raw in ((board.with_suffix('.kicad_pro').name, project_raw),
                      (board.with_suffix('.kicad_sch').name, schematic_raw)):
        if expected.get(name) != _sha(raw):
            _fail('passed original companion bytes differ')
    return expected


def _map_path(directory, stage, native_map):
    expected = directory/('export-netclasses.json' if stage == 'task' else 'final-netclasses.json')
    if Path(native_map) != expected:
        _fail('existing Native class-map path differs')
    local.canonical(expected)
    return expected


def _companions(source, project_raw, schematic_raw):
    """These files stay immutable even when the historical task PCB changes."""
    board = Path(source)
    if (pc.read_bytes(board.with_suffix('.kicad_pro'), q.MAX_BYTES) != project_raw
            or pc.read_bytes(board.with_suffix('.kicad_sch'), q.MAX_BYTES) != schematic_raw):
        _fail('current original candidate companions changed')


def _worker(directory, data, name, base_argv):
    """Bind the exact worker, using the shared task-export command grammar.

    Class parity proves this map's source and process, not copper admission.
    The central import contract independently requires the captured producer's
    paired protection flags; historical unflagged exports retain their proof.
    Never normalize the actual argv stored in the binding/process witness.
    """
    process_path = directory/(name+'-process.json')
    raw = pc.read_bytes(process_path, q.MAX_BYTES); process = preferences._parse(raw, q.MAX_BYTES)
    if type(process) is not dict:
        _fail('process object required')
    argv = process.get('argv')
    matches = argv in (base_argv, [*f.SANDBOX, *base_argv])
    if name == 'export':
        from .adapter import native_command_parser
        parsed = native_command_parser(with_task_copper=True)(argv, 'export')
        matches = parsed is not None and parsed[0] == base_argv
    if not matches:
        _fail('actual process command differs: ' + name)
    checked = f.process_check(directory, data, name, argv)
    log = directory/(name+'.log'); log_raw = pc.read_bytes(log, MAX_LOG_BYTES)
    if (checked.get('log') != str(log) or type(checked.get('log_bytes')) is not int
            or checked['log_bytes'] != len(log_raw) or checked.get('log_truncated') is not False):
        _fail('process log differs or truncated: ' + name)
    if pc.read_bytes(process_path, q.MAX_BYTES) != raw:
        _fail('process journal changed during replay: ' + name)
    return {'process_sha256': _sha(raw), 'log_sha256': _sha(log_raw),
            'log_bytes': len(log_raw), 'argv': argv}


def _rederive(directory, data, stage, *, board_raw, source, project_raw,
              schematic_raw, native_map):
    files = paths(directory, stage); stage = _stage(stage)
    source_path = q._path(source, '.kicad_pcb')
    if Path(source) != directory/'candidate'/source_path.name:
        _fail('Native map source must be this job candidate')
    for raw, label in ((board_raw, 'board'), (project_raw, 'project'), (schematic_raw, 'schematic')):
        q._raw(raw, label)
    expected = _expected_files(data, board_raw, source, project_raw, schematic_raw)
    _companions(source, project_raw, schematic_raw)
    binding_raw = pc.read_bytes(files['binding'], q.MAX_BYTES)
    binding = preferences._parse(binding_raw, q.MAX_BYTES)
    native_map = _map_path(directory, stage, native_map)
    native_raw = pc.read_bytes(native_map, q.MAX_BYTES)
    netlist_raw = pc.read_bytes(files['netlist'], q.MAX_BYTES)
    input_board = files['input']/source_path.name
    netlist_argv = [str(c.CLI), 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
                    '--output', str(files['netlist']), str(input_board.with_suffix('.kicad_sch'))]
    observed = _worker(directory, data, step_name(stage), netlist_argv)
    map_name = 'export' if stage == 'task' else 'final-netclasses'
    map_argv = [str(c.PYTHON), str(c.ROOT/'autorouter/native.py'),
        'export' if stage == 'task' else 'netclasses', source,
        str(directory/'task.dsn') if stage == 'task' else str(native_map)]
    if stage == 'task':
        map_argv.append(str(native_map))
    map_worker = _worker(directory, data, map_name, map_argv)
    before = _inventory(files['input'])
    if before != expected:
        _fail('retained class input copy differs from exact task/final bytes')
    if (pc.read_bytes(input_board, q.MAX_BYTES) != board_raw
            or pc.read_bytes(input_board.with_suffix('.kicad_pro'), q.MAX_BYTES) != project_raw
            or pc.read_bytes(input_board.with_suffix('.kicad_sch'), q.MAX_BYTES) != schematic_raw):
        _fail('retained class input byte binding differs')
    required = {'schema', 'context', 'stage', 'source', 'input', 'before', 'after',
                'native_map', 'native_map_sha256', 'netlist_sha256',
                'observation_worker', 'map_worker', 'protection'}
    if (type(binding) is not dict or set(binding) != required
            or type(binding.get('schema')) is not int or binding['schema'] != 1
            or binding.get('context') != CONTEXT or binding.get('stage') != stage
            or binding.get('source') != source or binding.get('input') != str(input_board)
            or binding.get('before') != expected or binding.get('after') != expected
            or binding.get('native_map') != str(native_map)
            or binding.get('native_map_sha256') != _sha(native_raw)
            or binding.get('netlist_sha256') != _sha(netlist_raw)
            or binding.get('observation_worker') != observed or binding.get('map_worker') != map_worker):
        _fail('class observation source/process/output binding differs')
    local.check_preserved(input_board.with_suffix('.kicad_prl'), expected, binding['protection'])
    qualification = q.derive(netlist_raw, board_raw, project_raw, native_raw, source=source,
        schematic_source=str(input_board.with_suffix('.kicad_sch')), schematic_raw=schematic_raw)
    proof = {'schema': 1, 'context': CONTEXT, 'stage': stage,
             'binding_sha256': _sha(binding_raw), 'qualification': qualification}
    # Repeat the bounded mutable-file witnesses after all pure/tool/process
    # reads. Original source/candidate freshness remains the central caller's job.
    if (_inventory(files['input']) != before
            or pc.read_bytes(files['binding'], q.MAX_BYTES) != binding_raw
            or pc.read_bytes(native_map, q.MAX_BYTES) != native_raw
            or pc.read_bytes(files['netlist'], q.MAX_BYTES) != netlist_raw
            or _worker(directory, data, step_name(stage), netlist_argv) != observed
            or _worker(directory, data, map_name, map_argv) != map_worker):
        _fail('class evidence changed during replay')
    local.check_preserved(input_board.with_suffix('.kicad_prl'), expected, binding['protection'])
    _companions(source, project_raw, schematic_raw)
    return proof


def check(directory, data, stage, *, board_raw, source, project_raw,
          schematic_raw, native_map):
    """Recompute actual stored proof; no Native execution or candidate read.

    ``data`` must contain steps, original source_hashes and the metadata returned
    by collect under record_key(stage). The central reader reconstructs task
    bytes and independently proves the original source and final candidate.
    """
    directory = local.canonical(Path(directory)); files = paths(directory, stage)
    raw = pc.read_bytes(files['proof'], q.MAX_BYTES)
    expected = {'schema': 1, 'context': CONTEXT, 'stage': stage,
                'file': files['proof'].name, 'sha256': _sha(raw)}
    metadata = data.get(record_key(stage)) if type(data) is dict else None
    if (type(metadata) is not dict or set(metadata) != set(expected)
            or any(type(metadata[key]) is not type(value) or metadata[key] != value
                   for key, value in expected.items())):
        _fail('missing, downgraded or changed class-proof metadata')
    proof = _rederive(directory, data, stage, board_raw=board_raw, source=source,
        project_raw=project_raw, schematic_raw=schematic_raw, native_map=native_map)
    if f.canonical(preferences._parse(raw, q.MAX_BYTES)) != f.canonical(proof):
        _fail('stored class proof differs from rederived observation')
    if pc.read_bytes(files['proof'], q.MAX_BYTES) != raw:
        _fail('class proof changed during replay')
    return proof


def collect(job, stage, board, native_map):
    """One guarded SCH export using an already observed task/final PCB map.

    Source copies, worker costs and all failure artifacts belong to job.out.
    Never annotate this SCH worker with the DRC local_settings_policy: its
    separate binding records the same real PRL guard without changing DRC census.
    """
    stage = _stage(stage); directory = local.canonical(Path(job.out))
    board = local.canonical(Path(board)); files = paths(directory, stage)
    if (getattr(job, 'protect_local_settings', None) is not True
            or h.owned_destination(job._local_settings_owner) != directory
            or board.parent != directory/'candidate'):
        _fail('class observation requires the existing owned guarded candidate Job')
    if requirement(board) is None:
        _fail('class observation without a required source flag')
    native_map = _map_path(directory, stage, native_map)
    captured = _inventory(board.parent)
    board_raw = pc.read_bytes(board, q.MAX_BYTES)
    project_raw = pc.read_bytes(board.with_suffix('.kicad_pro'), q.MAX_BYTES)
    schematic_raw = pc.read_bytes(board.with_suffix('.kicad_sch'), q.MAX_BYTES)
    native_raw = pc.read_bytes(native_map, q.MAX_BYTES)
    # Fail on an already wrong/missing map before starting the SCH worker.
    configured, known, _ = q._source_classes(preferences._parse(project_raw, q.MAX_BYTES))
    q._native_map(preferences._parse(native_raw, q.MAX_BYTES), str(board),
                  board_raw, project_raw, preferences._parse(project_raw, q.MAX_BYTES), known)
    if any(path.exists() or path.is_symlink() for path in files.values()):
        _fail('fresh class observation paths required')
    shutil.copytree(board.parent, files['input'])
    if _inventory(files['input']) != captured or _inventory(board.parent) != captured:
        _fail('source changed during class observation copy')
    input_board = files['input']/board.name
    argv = [str(c.CLI), 'sch', 'export', 'netlist', '--format', 'kicadsexpr',
            '--output', str(files['netlist']), str(input_board.with_suffix('.kicad_sch'))]
    state = {'complete': False}; start = len(job.steps)
    with local.preserve(input_board.with_suffix('.kicad_prl'), directory, job._local_settings_owner,
                        cleanup_complete=lambda: state['complete']) as protection:
        try:
            job.step(step_name(stage), argv)
        finally:
            added = job.steps[start:]
            state['complete'] = (len(added) == 1 and added[0].get('name') == step_name(stage)
                and added[0].get('cwd') == str(directory) and added[0].get('cleanup_complete') is True)
    after = _inventory(files['input'])
    if after != captured or _inventory(board.parent) != captured:
        _fail('class observation changed copied/original candidate inputs')
    if pc.read_bytes(native_map, q.MAX_BYTES) != native_raw:
        _fail('Native class map changed during SCH export')
    data = {'steps': job.steps, 'source_hashes': captured}
    observed = _worker(directory, data, step_name(stage), argv)
    map_name = 'export' if stage == 'task' else 'final-netclasses'
    map_argv = [str(c.PYTHON), str(c.ROOT/'autorouter/native.py'),
        'export' if stage == 'task' else 'netclasses', str(board),
        str(directory/'task.dsn') if stage == 'task' else str(native_map)]
    if stage == 'task': map_argv.append(str(native_map))
    map_worker = _worker(directory, data, map_name, map_argv)
    binding = {'schema': 1, 'context': CONTEXT, 'stage': stage, 'source': str(board),
        'input': str(input_board), 'before': captured, 'after': after,
        'native_map': str(native_map), 'native_map_sha256': _sha(native_raw),
        'netlist_sha256': _sha(pc.read_bytes(files['netlist'], q.MAX_BYTES)),
        'observation_worker': observed, 'map_worker': map_worker, 'protection': protection}
    from .pipeline import save_json
    save_json(files['binding'], binding)
    proof = _rederive(directory, data, stage, board_raw=board_raw, source=str(board),
        project_raw=project_raw, schematic_raw=schematic_raw, native_map=native_map)
    save_json(files['proof'], proof)
    metadata = {'schema': 1, 'context': CONTEXT, 'stage': stage,
                'file': files['proof'].name, 'sha256': _sha(pc.read_bytes(files['proof'], q.MAX_BYTES))}
    data[record_key(stage)] = metadata
    check(directory, data, stage, board_raw=board_raw, source=str(board), project_raw=project_raw,
          schematic_raw=schematic_raw, native_map=native_map)
    if _inventory(board.parent) != captured or h.owned_destination(job._local_settings_owner) != directory:
        _fail('source or Job ownership changed during class-proof publication')
    return metadata
