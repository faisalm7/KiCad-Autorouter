"""Unqualified experimental task-connectivity hint; never routing acceptance.

Initial complete net population max64 reuses the existing selected partition.
This does not change public preferences, original class assignment or terminals.
Use saved refill plus fresh original-shell DRC and shared process/readback proof.
"""
from __future__ import annotations

import copy
import hashlib
import re
from pathlib import Path

from . import board_floor as g, floor_route as f, pipeline as p
from . import routing_scope as rs, sexpr as sx
from .adapter import _parse_dsn
from .placement_clearance import read_bytes

POLICY = 'experimental-native-connected-nets-v1'
MAX_NETS = 64  # Initial six-net prototype; CellScan85 is explicitly unqualified.
MAX_ITEMS = 10000
RECORD_FILE = 'task-connectivity.json'
STAGE = 'refill-drc'


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _raw(tree):
    return (sx.dump(tree) + '\n').encode()


def _board(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= sx.MAX_BYTES:
        raise p.Rejected('bounded nonempty connectivity PCB required')
    tree = sx.parse(raw.decode('utf-8'))
    if not tree or tree[0] != 'kicad_pcb':
        raise p.Rejected('connectivity PCB required')
    return tree


def _uuid(node):
    return rs._uuid(sx.one(node, 'uuid'))[1].lower()


def _index(task):
    """Every UUID is unique; only exact pad/zone/route/footprint endpoints resolve."""
    # Initial task_pads maps outer copper only. Refuse broader stackups and
    # nested zones rather than claiming a complete terminal/fill witness there.
    tables = sx.children(task, 'layers')
    if len(tables) != 1:
        raise p.Rejected('connectivity requires exact two outer copper layers')
    copper, seen_ids, seen_names = [], set(), set()
    for row in tables[0][1:]:
        if (type(row) is not list or len(row) not in (3, 4)
                or any(type(x) is not str for x in row) or not row[0].isdigit()):
            raise p.Rejected('unqualified connectivity layer declaration')
        name = sx.unquote(row[1])
        if row[0] in seen_ids or name in seen_names:
            raise p.Rejected('duplicate connectivity layer identity')
        seen_ids.add(row[0]); seen_names.add(name)
        if name.endswith('.Cu') or row[2] in {'signal', 'power', 'mixed', 'jumper'}:
            if row[2] not in {'signal', 'power', 'mixed'}:
                raise p.Rejected('unqualified connectivity copper type')
            copper.append((row[0], name))
        elif row[2] != 'user':
            raise p.Rejected('unknown connectivity layer semantics')
    if copper != [('0', 'F.Cu'), ('2', 'B.Cu')]:
        raise p.Rejected('connectivity requires exact two outer copper layers')
    if any(sx.children(fp, 'zone') for fp in sx.children(task, 'footprint')):
        raise p.Rejected('connectivity footprint zones are unqualified')
    names, resolve = g.source_net_identity(task)
    if not 1 <= len(names) <= MAX_NETS:
        raise p.Rejected('experimental complete net population requires max64')
    all_ids = set()
    def visit(node):
        if type(node) is not list:
            return
        tags = sx.children(node, 'uuid')
        if tags:
            identity = _uuid(node)
            if identity in all_ids:
                raise p.Rejected('ambiguous connectivity UUID')
            all_ids.add(identity)
            if len(all_ids) > MAX_ITEMS:
                raise p.Rejected('connectivity UUID population exceeded')
        for child in node[1:]:
            visit(child)
    visit(task)
    pads = g.task_pads(task)
    endpoints, terminals, nets_by_ref, groups, identities = {}, {}, {}, {}, {}
    for identity, row in pads.items():
        endpoints[identity.lower()] = {row['net']} if row['net'] else set()
        if row['net']:
            nets_by_ref.setdefault(row['reference'], set()).add(row['net'])
        if row['net'] and row['copper_layers']:
            if not row['reference'] or not row['number']:
                raise p.Rejected('ambiguous connectivity terminal identity')
            token = row['reference'] + '-' + row['number']
            identity = (row['reference'], row['number'])
            if token in identities and identities[token] != identity:
                raise p.Rejected('ambiguous connectivity DSN terminal')
            identities[token] = identity
            # Native exports repeated same-net pads as base, base@1, ... .
            # Their order is irrelevant to whole-net activity; retain one
            # token per physical pad and refuse reserved-name collisions.
            if '@' in row['reference'] or '@' in row['number']:
                raise p.Rejected('reserved connectivity terminal alias')
            group = groups.setdefault(token, [])
            if group and group[0] != row['net']:
                raise p.Rejected('ambiguous repeated connectivity terminal net')
            group.append(row['net'])
    for token, nets in groups.items():
        for index, name in enumerate(nets):
            alias = token if index == 0 else token + '@' + str(index)
            if alias in terminals:
                raise p.Rejected('ambiguous connectivity DSN terminal')
            terminals[alias] = name
    for fp in sx.children(task, 'footprint'):
        endpoints[_uuid(fp)] = nets_by_ref.get(_reference(fp), set())
    zones = [*sx.children(task, 'zone'),
             *(z for fp in sx.children(task, 'footprint') for z in sx.children(fp, 'zone'))]
    for node in [*zones, *p.routes(task)]:
        name = resolve(sx.one(node, 'net'), owner=node)
        endpoints[_uuid(node)] = {name} if name else set()
    if any(value not in names for value in terminals.values()):
        raise p.Rejected('terminal net outside complete native identities')
    return names, endpoints, terminals


def _reference(fp):
    rows = [row for row in sx.children(fp, 'property')
            if len(row) >= 3 and sx.unquote(row[1]) == 'Reference']
    if len(rows) != 1:
        raise p.Rejected('ambiguous connectivity footprint reference')
    return sx.unquote(rows[0][2])


def _dsn_members(raw, names, terminals):
    if type(raw) is not bytes or not 0 < len(raw) <= 20 * 1024**2:
        raise p.Rejected('bounded connectivity DSN required')
    network = sx.one(_parse_dsn(raw.decode()), 'network')
    if network is None:
        raise p.Rejected('connectivity DSN network absent')
    net_rows = sx.children(network, 'net')
    if len(net_rows) != len(names):
        raise p.Rejected('DSN complete net population differs')
    found, pins = set(), {}
    for net in net_rows:
        if len(net) != 3 or type(net[1]) is not str or not isinstance(net[2], list) or net[2][0] != 'pins':
            raise p.Rejected('unqualified connectivity DSN net grammar')
        name = sx.unquote(net[1])
        if name in found or name not in names:
            raise p.Rejected('DSN complete net identity differs')
        found.add(name)
        for atom in net[2][1:]:
            if type(atom) is not str:
                raise p.Rejected('unqualified connectivity DSN terminal')
            pin = sx.unquote(atom)
            if pin in pins or terminals.get(pin) != name:
                raise p.Rejected('DSN terminal identity or net differs')
            pins[pin] = name
    if found != names or pins != terminals:
        raise p.Rejected('DSN omitted or added original terminals')
    # Run the existing complete class/reference/alias/rule-preservation guard,
    # without using the returned serialization for the all-active comparator.
    rs.partition_dsn(raw, sorted(names))
    return network


def derive(original_bytes, task_bytes, filled_bytes, native, native_dsn,
           source_hashes, *, source_name, report_sha256):
    """Pure hint derivation; native summary provenance is mandatory in readback()."""
    original, task, filled = map(_board, (original_bytes, task_bytes, filled_bytes))
    if any(sx.children(fp, 'zone') for fp in sx.children(original, 'footprint')):
        raise p.Rejected('connectivity footprint zones are unqualified')
    expected = g.task_from_source(original)  # Explicitly refuses protected source.
    if task_bytes != _raw(expected):
        raise p.Rejected('task differs from all-unprotected-routes-stripped source')
    if p.immutable(task) != p.immutable(filled) or p.routes(task) != p.routes(filled):
        raise p.Rejected('saved refill changed task geometry or protected routing')
    if (type(source_hashes) is not dict or not 1 <= len(source_hashes) <= 2000
            or source_hashes.get(source_name) != _sha(original_bytes)
            or any(type(k) is not str or type(v) is not str or re.fullmatch('[0-9a-f]{64}', v) is None
                   for k, v in source_hashes.items())
            or type(report_sha256) is not str or re.fullmatch('[0-9a-f]{64}', report_sha256) is None):
        raise p.Rejected('connectivity original-project/report pins differ')
    # Opens are expected on the stripped task. Admit exactly those ordinary,
    # unexcluded error findings as classifier input; original final acceptance
    # continues to call native_accepted without any such exception.
    expected_open_reasons = {'native opens=' + str(native.get('opens')),
                             'native error finding: unconnected_items',
                             'policy-critical native finding: unconnected_items (error)'}
    reasons = [reason for reason in p.native_rejection_reasons(native)
               if reason not in expected_open_reasons]
    if reasons:
        raise p.Rejected('task connectivity native scope unavailable: ' + '; '.join(reasons))
    names, endpoints, terminals = _index(filled)
    network = _dsn_members(native_dsn, names, terminals)
    opens = [finding for finding in native['findings'] if finding['type'] == 'unconnected_items']
    if len(opens) != native['opens'] or len(opens) > MAX_ITEMS:
        raise p.Rejected('complete task open population differs')
    active = set()
    for finding in opens:
        if finding['severity'] != 'error' or finding.get('excluded', False):
            raise p.Rejected('task connectivity open was weakened or excluded')
        items = finding['items']
        if len(items) != 2:
            raise p.Rejected('unqualified task connectivity endpoint population')
        resolved, seen = set(), set()
        for item in items:
            identity = item.get('uuid') if type(item) is dict else None
            if type(identity) is not str or identity.lower() in seen:
                raise p.Rejected('ambiguous task connectivity endpoint')
            seen.add(identity.lower())
            values = endpoints.get(identity.lower(), set())
            if len(values) != 1:
                raise p.Rejected('unmapped, null or ambiguous task connectivity endpoint')
            resolved.update(values)
        if len(resolved) != 1:
            raise p.Rejected('mixed-net task connectivity endpoints')
        active.update(resolved)
    if not active:
        raise p.Rejected('all-connected no-engine path not qualified')
    record = {'schema': 1, 'policy': POLICY, 'routing_accepted': False,
              'original_sha256': _sha(original_bytes), 'task_sha256': _sha(task_bytes),
              'filled_task_sha256': _sha(filled_bytes), 'native_report_sha256': report_sha256,
              'native_dsn_sha256': _sha(native_dsn), 'source_hashes': copy.deepcopy(source_hashes),
              'source_name': source_name, 'all_names': sorted(names), 'active_names': sorted(active),
              'inactive_names': sorted(names - active), 'complete_terminal_count': len(terminals),
              'terminal_sha256': _sha(f.canonical(terminals).encode()),
              'native_network_sha256': _sha(f.canonical(network).encode()),
              'mapped_open_count': len(opens), 'engine_profile': 'completion-only',
              'engine_requirements': {'fanout': False, 'optimizer': False,
                                      'automatic_neckdown': False, 'neck_width_um': 0},
              'reference_routes_used_for_selection': False,
              'scope': 'whole_board_unlocked_routing',
              'eligibility_basis': 'absence of exact mapped opens in fresh original-shell DRC after saved refill; hint only'}
    return record


def partition(native_dsn, engine_dsn, record):
    """Adapted geometry may differ; original net/class/terminal rules may not."""
    if (record.get('policy') != POLICY or record.get('native_dsn_sha256') != _sha(native_dsn)
            or type(record.get('all_names')) is not list or not 1 <= len(record['all_names']) <= MAX_NETS
            or record['all_names'] != sorted(set(record['all_names']))
            or record.get('active_names') != sorted(set(record.get('active_names', [])))
            or not record.get('active_names')
            or not set(record.get('active_names', [])) <= set(record['all_names'])
            or record.get('inactive_names') != sorted(set(record['all_names']) - set(record['active_names']))):
        raise p.Rejected('stale or malformed task connectivity record')
    native_network = sx.one(_parse_dsn(native_dsn.decode()), 'network')
    engine_network = sx.one(_parse_dsn(engine_dsn.decode()), 'network')
    if native_network != engine_network or _sha(f.canonical(native_network).encode()) != record['native_network_sha256']:
        raise p.Rejected('connected-net adapter changed terminal/class constraints')
    if not record['inactive_names']:
        return engine_dsn, {'input_sha256': _sha(engine_dsn), 'output_sha256': _sha(engine_dsn),
                            'engine_argument': None, 'ignored_engine_classes': [],
                            'all_nets_and_pins_retained': True, 'class_rules_copied_exactly': True}
    return rs.partition_dsn(engine_dsn, record['active_names'])


def verify_record(record, **materials):
    """Exact fresh recomputation used by the mandatory shared readback seam."""
    result = derive(**materials)
    if f.canonical(record) != f.canonical(result):
        raise p.Rejected('connected-net classification changed or missing')
    return result


def engine_settings(remaining_seconds, partition_binding):
    settings = p.engine_profile_settings('completion-only', remaining_seconds, strict_class_targets=True)
    argument = partition_binding['engine_argument']
    if argument is not None:
        if not argument.startswith('--router.autorouter.ignore_net_classes='):
            raise p.Rejected('invalid connectivity engine activity argument')
        settings['argv'].append(argument)
    return settings


def readback(directory, data, source, task, refill, candidate, native_dsn):
    """Require saved refill, exact original shell and its fresh final Native.

    Native may serialize an older task differently. Its saved file is retained
    as evidence, never substituted for original intent or the final report.
    """
    directory, source, task, refill, candidate, native_dsn = map(
        Path, (directory, source, task, refill, candidate, native_dsn))
    hashes = data['source_hashes']
    if p.tree_hash(source.parent) != hashes:
        raise p.Rejected('connected-net source project changed')
    p.preflight(source)
    before = {**hashes, source.name: _sha(read_bytes(task))}
    f.check_drc_stage(directory, data, STAGE, refill, refill, True, before, sandboxed=False)
    expected = _raw(p.transplant_fill(sx.read(task), sx.read(refill)))
    if read_bytes(candidate) != expected:
        raise p.Rejected('connected-net original-shell reconstruction differs')
    digest = _sha(expected)
    p.verify_candidate_files(candidate, hashes, digest)
    native = f.check_drc_stage(directory, data, 'final-drc', candidate,
        directory / 'final-drc-input' / source.name, False,
        {**hashes, source.name: digest},
        schematic_parity=source.with_suffix('.kicad_sch').name in hashes,
        sandboxed=False)
    # Initial comparator uses production-pinned10.0.0. Toolchain migration and
    # experimental10.0.7 area qualification are separate and must not bleed in.
    report = directory / 'final-drc.json'
    report_digest = _sha(read_bytes(report))
    if (data.get('native_witness') != 'saved-refill-and-final-original-shell-v1'
            or data.get('original_shell_sha256') != digest
            or data.get('task_native_report_sha256') != report_digest
            or f.canonical(data.get('task_native')) != f.canonical(native)):
        raise p.Rejected('connected-net final native witness claims differ')
    retained = f.read_json(directory / RECORD_FILE)
    result = verify_record(retained, original_bytes=read_bytes(source), task_bytes=read_bytes(task),
                           filled_bytes=read_bytes(candidate), native=native,
                           native_dsn=read_bytes(native_dsn, 20 * 1024**2), source_hashes=hashes,
                           source_name=source.name, report_sha256=report_digest)
    if f.canonical(data.get('native_connected_classification')) != f.canonical(result):
        raise p.Rejected('connected-net classification changed or missing')
    f.process_check(directory, data, 'task-export',
        [str(p.c.PYTHON), str(p.c.ROOT / 'autorouter/native.py'),
         'export', str(task), str(native_dsn)])
    return result
