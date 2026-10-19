"""Pure, bounded class-parity prerequisite, never a routing acceptance decision.

SPDX-License-Identifier: GPL-3.0-or-later

``derive`` consumes exact bytes, not paths to open. Its caller must independently
bind actual pinned Native workers, argv, source snapshots, outputs and freshness.
This module performs no Native execution, file I/O, source repair or admission.

Initial scope: flat modern owned-style schematics; ordinary distinct numbered
pins/pads; every component pin assigned to exactly one PCB/SCH net; the existing
explicit Native-parent PRO policy with only four dimensional class parameters.
Class identity is Default or an exact configured NAME,Default literal. Arbitrary
encoded names are never split to infer their constituents or semantic meaning.
All four scalar parents must be the explicit source definition. Composite
multi-nondefault inheritance, aliases, hierarchy, no-connect/padless terminals,
additional class parameters and electrical suitability remain unsupported.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import PurePosixPath
import re

from autorouter import config as c, netclass as nc, preferences, schematic_fields as fields
from autorouter import sexpr as sx

POLICY = 'flat-class-parity-prerequisite-v1'
MAX_BYTES = 8 * 1024 * 1024
MAX_COMPONENTS = 512
MAX_TERMINALS = 4096
MAX_NETS = 1024
MAX_FLAGS = 64
_REF = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,63}')
_PIN = re.compile(r'[1-9][0-9]{0,4}')
_NAME = re.compile(r'[A-Za-z_][A-Za-z0-9_]{0,63}')
_DIMS = ('width_nm', 'clearance_nm', 'via_diameter_nm', 'via_drill_nm')
_CLASS_FIELDS = {'name', 'priority', 'track_width', 'clearance', 'via_diameter',
                 'via_drill', 'tuning_profile'}
_RESOLUTION = 'BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()'


class ClassIdentityMismatch(ValueError):
    """Exact joined-partition mismatch, distinct from schema/binding refusal.

    An unknown SCH encoding is retained literally, never decoded or admitted.
    This exception is raised only after the complete terminal bijection and PCB
    original-PRO/Native parent proof have passed.
    """
    code = 'class_identity_mismatch'

    def __init__(self, net, terminals, schematic_class, pcb_class,
                 schematic_identity_in_scope, partition_count):
        self.net = net
        self.terminals = tuple(sorted(terminals))
        self.schematic_class = schematic_class
        self.pcb_class = pcb_class
        self.schematic_identity_in_scope = schematic_identity_in_scope
        self.partition_count = partition_count
        super().__init__('flat class parity: class_identity_mismatch on ' + net
                         + ': SCH=' + repr(schematic_class) + ', PCB=' + repr(pcb_class))


def _fail(reason):
    raise ValueError('flat class parity: ' + reason)


def _raw(raw, label):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_BYTES:
        _fail('bounded nonempty bytes required: ' + label)
    return raw


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _tree(raw, label, root):
    try:
        tree = sx.parse(_raw(raw, label).decode('utf-8'))
    except (UnicodeError, ValueError) as exc:
        _fail(label + ' parse failed: ' + str(exc))
    if not tree or tree[0] != root:
        _fail('unexpected ' + label + ' root')
    return tree


def _text(value, label):
    if (type(value) is not str or not value or value != value.strip()
            or len(value.encode('utf-8')) > 256
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        _fail('unqualified text: ' + label)
    return value


def _atom(value, label):
    if type(value) is not str:
        _fail('string atom required: ' + label)
    return fields.atom(value)


def _single(node, key):
    value = sx.one(node, key)
    if value is None or len(value) != 2 or type(value[1]) is not str:
        _fail('missing or malformed ' + key)
    return _atom(value[1], key)


def _only(node, allowed, *, start=1):
    if any(type(child) is not list or not child or child[0] not in allowed
           for child in node[start:]):
        _fail('unknown schema below ' + str(node[0]))


def _ref(value):
    if type(value) is not str or _REF.fullmatch(value) is None:
        _fail('unqualified component reference')
    return value


def _pin(value):
    if type(value) is not str or _PIN.fullmatch(value) is None:
        _fail('canonical positive numbered pin required')
    return value


def _uuid(value):
    if type(value) is not str or fields.UUID.fullmatch(value) is None:
        _fail('canonical UUID required')
    return value


def _path(value, suffix):
    _text(value, 'source path')
    path = PurePosixPath(value)
    if (not path.is_absolute() or '..' in path.parts or str(path) != value
            or path.suffix != suffix):
        _fail('canonical absolute source path required')
    return path


def _properties(owner):
    result = {}; folded = set()
    for row in sx.children(owner, 'property'):
        if len(row) < 3:
            _fail('malformed source property')
        key = _atom(row[1], 'property name')
        if not key or key.casefold() in folded:
            _fail('missing or duplicate source property')
        result[key] = _atom(row[2], key)
        folded.add(key.casefold())
    return result


def _source_classes(project):
    if type(project) is not dict:
        _fail('original project object required')
    settings = project.get('net_settings')
    if (type(settings) is not dict or set(settings) !=
            {'classes', 'meta', 'netclass_assignments', 'netclass_patterns'}
            or settings.get('meta') != {'version': 5}
            or type(settings['meta'].get('version')) is not int):
        _fail('unqualified original class settings schema')
    policy = nc.qualify_parent_project(project)
    configured = {}
    for cls in settings['classes']:
        if type(cls) is not dict or set(cls) != _CLASS_FIELDS:
            _fail('unqualified source class fields')
        name = cls['name']
        if type(name) is not str or _NAME.fullmatch(name) is None:
            _fail('ambiguous source class namespace')
        if cls['tuning_profile'] != '' or type(cls['tuning_profile']) is not str:
            _fail('class tuning intent unsupported')
        configured[name] = cls
    # Construct only the exact encodings already qualified by the existing
    # pinned single-parent policy. Do not decode arbitrary GetName strings.
    known = {'Default': configured['Default']}
    known.update({name + ',Default': cls for name, cls in configured.items()
                  if name != 'Default'})
    return configured, known, policy


def _source_schematic(tree, configured):
    if sx.one(tree, 'version') != ['version', '20250114']:
        _fail('flat source schematic version unqualified')
    pending = [tree]
    flags = []
    while pending:
        node = pending.pop()
        if node and node[0] == 'sheet':
            _fail('hierarchy remains unsupported')
        if node and node[0] == 'netclass_flag':
            props = _properties(node)
            if (set(props) != {'Netclass'} or props['Netclass'] not in configured
                    or len(flags) >= MAX_FLAGS):
                _fail('unknown or unqualified schematic class flag')
            flags.append(props['Netclass'])
        pending.extend(child for child in node[1:] if type(child) is list)
    if not flags:
        _fail('this prerequisite requires an explicit schematic class flag')
    symbols = sx.children(tree, 'symbol')
    if not 1 <= len(symbols) <= MAX_COMPONENTS:
        _fail('source component population outside scope')
    result = {}; folded = set(); ids = set(); pin_ids = set()
    for symbol in symbols:
        ref = _ref(_properties(symbol).get('Reference'))
        uid = _uuid(_single(symbol, 'uuid'))
        if ref.casefold() in folded or uid in ids:
            _fail('duplicate or aliased source symbol identity')
        if (sx.one(symbol, 'unit') != ['unit', '1']
                or sx.one(symbol, 'on_board') != ['on_board', 'yes']):
            _fail('one on-board source unit per component required')
        pins = []
        for pin in sx.children(symbol, 'pin'):
            if len(pin_ids) >= MAX_TERMINALS:
                _fail('source terminal ceiling')
            if len(pin) != 3 or sx.one(pin, 'uuid') is None:
                _fail('unqualified source symbol pin schema')
            pins.append(_pin(_atom(pin[1], 'symbol pin')))
            pin_uid = _uuid(_single(pin, 'uuid'))
            if pin_uid in pin_ids or pin_uid in ids or pin_uid == uid:
                _fail('duplicate or aliased source pin UUID')
            pin_ids.add(pin_uid)
        if not pins or len(pins) != len(set(pins)):
            _fail('missing or duplicate source symbol pin')
        if uid in pin_ids:
            _fail('source symbol/pin UUID collision')
        result[ref] = {'uuid': uid, 'pins': set(pins)}
        folded.add(ref.casefold()); ids.add(uid)
    return result, sorted(flags)


def _board_partitions(tree, symbols):
    if sx.one(tree, 'version') != ['version', '20260206']:
        _fail('modern board version unqualified')
    if sx.children(tree, 'net') or sx.children(tree, 'module'):
        _fail('numeric/legacy board net representation unsupported')
    fps = sx.children(tree, 'footprint')
    if not 1 <= len(fps) <= MAX_COMPONENTS:
        _fail('board component population outside scope')
    partitions = {}; terminals = set(); refs = set(); folded = set(); ids = set(); pad_ids = set()
    for fp in fps:
        ref = _ref(_properties(fp).get('Reference'))
        uid = _uuid(_single(fp, 'uuid'))
        if ref.casefold() in folded or uid in ids or ref not in symbols:
            _fail('duplicate, aliased or unmatched footprint')
        if _single(fp, 'path') != '/' + symbols[ref]['uuid']:
            _fail('footprint/source symbol identity differs')
        if sx.children(fp, 'net_tie_pad_groups'):
            _fail('net ties remain outside this prerequisite')
        pads = sx.children(fp, 'pad'); pinset = set()
        if not pads:
            _fail('padless footprints remain unsupported')
        for pad in pads:
            if (len(pad) < 4 or pad[2] not in {'smd', 'thru_hole'}
                    or type(pad[1]) is not str):
                _fail('ordinary copper pad required')
            pin = _pin(_atom(pad[1], 'pad number'))
            terminal = (ref, pin)
            if terminal in terminals or len(terminals) >= MAX_TERMINALS:
                _fail('duplicate or excessive PCB terminal')
            pad_uid = _uuid(_single(pad, 'uuid'))
            if pad_uid in pad_ids or pad_uid in ids or pad_uid == uid:
                _fail('duplicate or aliased PCB pad UUID')
            pad_ids.add(pad_uid)
            layers = sx.one(pad, 'layers')
            if (layers is None or any(type(x) is not str for x in layers[1:])
                    or not any(_atom(x, 'pad layer').endswith('.Cu')
                               for x in layers[1:])):
                _fail('unqualified copper pad layers')
            name = _text(_single(pad, 'net'), 'PCB net')
            partitions.setdefault(name, set()).add(terminal)
            terminals.add(terminal); pinset.add(pin)
        if pinset != symbols[ref]['pins']:
            _fail('source symbol/PCB pin census differs')
        if uid in pad_ids:
            _fail('PCB footprint/pad UUID collision')
        refs.add(ref); folded.add(ref.casefold()); ids.add(uid)
    if refs != set(symbols) or not 1 <= len(partitions) <= MAX_NETS:
        _fail('incomplete board/source component or net census')
    if len({name.casefold() for name in partitions}) != len(partitions):
        _fail('case-aliased PCB net labels unsupported')
    return partitions, terminals


def _netlist_partitions(tree, schematic_source, symbols):
    _only(tree, {'version', 'design', 'components', 'groups', 'variants',
                 'libparts', 'libraries', 'nets'})
    for key in ('groups', 'variants', 'libparts', 'libraries'):
        if sx.one(tree, key) is None:
            _fail('incomplete native export sections')
    if sx.one(tree, 'groups') != ['groups'] or sx.one(tree, 'variants') != ['variants']:
        _fail('group/variant export semantics unqualified')
    if _single(tree, 'version') != 'E':
        _fail('native export version differs')
    design = sx.one(tree, 'design')
    if design is None:
        _fail('native design metadata absent')
    _only(design, {'source', 'date', 'tool', 'sheet'})
    if (_single(design, 'source') != schematic_source
            or _single(design, 'tool') != 'Eeschema ' + c.NATIVE_VERSION):
        _fail('native schematic source/tool differs')
    sheets = sx.children(design, 'sheet')
    if (len(sheets) != 1 or _single(sheets[0], 'number') != '1'
            or _single(sheets[0], 'name') != '/'
            or _single(sheets[0], 'tstamps') != '/'):
        _fail('native flat single-sheet identity required')
    section = sx.one(tree, 'components')
    if section is None:
        _fail('native component section absent')
    _only(section, {'comp'})
    if not 1 <= len(section[1:]) <= MAX_COMPONENTS:
        _fail('native component population outside scope')
    refs = set(); folded = set(); declared = set()
    for comp in section[1:]:
        _only(comp, {'ref', 'value', 'footprint', 'description', 'fields',
                     'libsource', 'property', 'sheetpath', 'tstamps', 'units'})
        ref = _ref(_single(comp, 'ref'))
        if ref.casefold() in folded or ref not in symbols:
            _fail('duplicate, aliased or unmatched native component')
        if _single(comp, 'tstamps') != symbols[ref]['uuid']:
            _fail('native/source symbol identity differs')
        sheetpath = sx.one(comp, 'sheetpath')
        if sheetpath is None:
            _fail('native component sheet path absent')
        _only(sheetpath, {'names', 'tstamps'})
        if _single(sheetpath, 'names') != '/' or _single(sheetpath, 'tstamps') != '/':
            _fail('native component is not flat')
        units = sx.one(comp, 'units')
        if units is None or len(units) != 2 or type(units[1]) is not list or units[1][0] != 'unit':
            _fail('one native unit per component required')
        unit = units[1]; _only(unit, {'name', 'pins'})
        if _single(unit, 'name') != 'A':
            _fail('native unit identity unqualified')
        pins = sx.one(unit, 'pins')
        if pins is None:
            _fail('native unit pin census absent')
        if len(pins[1:]) != len(symbols[ref]['pins']):
            _fail('native/source component pin population differs')
        _only(pins, {'pin'}); numbers = []
        for row in pins[1:]:
            _only(row, {'num'}); numbers.append(_pin(_single(row, 'num')))
        if len(numbers) != len(set(numbers)) or set(numbers) != symbols[ref]['pins']:
            _fail('native/source component pin census differs')
        declared.update((ref, number) for number in numbers)
        refs.add(ref); folded.add(ref.casefold())
    if refs != set(symbols):
        _fail('native/source component census differs')
    section = sx.one(tree, 'nets')
    if section is None:
        _fail('native nets absent')
    _only(section, {'net'})
    if not 1 <= len(section[1:]) <= MAX_NETS:
        _fail('native net population outside scope')
    result = {}; used = set(); codes = set(); folded = set()
    for net in section[1:]:
        _only(net, {'code', 'name', 'class', 'node'})
        code = _pin(_single(net, 'code'))
        name = _text(_single(net, 'name'), 'schematic net')
        identity = _text(_single(net, 'class'), 'schematic class')
        if code in codes or name.casefold() in folded:
            _fail('duplicate or aliased native net')
        terminals = set()
        for row in sx.children(net, 'node'):
            _only(row, {'ref', 'pin', 'pinfunction', 'pintype'})
            terminal = (_ref(_single(row, 'ref')), _pin(_single(row, 'pin')))
            if terminal not in declared or terminal in used:
                _fail('unknown, duplicate or aliased native terminal')
            if len(used) >= MAX_TERMINALS:
                _fail('native terminal ceiling')
            terminals.add(terminal); used.add(terminal)
        if not terminals:
            _fail('empty schematic net unsupported')
        result[name] = {'terminals': terminals, 'class': identity}
        codes.add(code); folded.add(name.casefold())
    if used != declared:
        _fail('incomplete native terminal census')
    return result, used


def _native_map(native, source, board_raw, project_raw, project, known):
    required = {'schema', 'native_version', 'units', 'resolution', 'source',
                'board_sha256', 'project_sha256', 'board_saved', 'nets'}
    headers = (required, required | {'copper_layers'}, required | {'effective_floors_nm'},
               required | {'copper_layers', 'effective_floors_nm'})
    if (type(native) is not dict or set(native) not in headers
            or type(native.get('schema')) is not int or native['schema'] != 1
            or native.get('native_version') != c.NATIVE_VERSION
            or native.get('units') != 'integer nanometres'
            or native.get('resolution') != _RESOLUTION
            or native.get('source') != source
            or native.get('board_sha256') != _sha(board_raw)
            or native.get('project_sha256') != _sha(project_raw)
            or native.get('board_saved') is not False):
        _fail('PCB native map schema/source/hash differs')
    if 'effective_floors_nm' in native:
        from .netclass_native import validate_floors
        validate_floors(native['effective_floors_nm'], project)
    rows = native.get('nets')
    if type(rows) is not list or not 1 <= len(rows) <= MAX_NETS:
        _fail('PCB native net census outside scope')
    expected = {'name', 'netcode', 'copper_pad_count', 'class', 'parameter_parents', *_DIMS}
    folded = set()
    for row in rows:
        if type(row) is not dict or set(row) != expected:
            _fail('PCB native net row schema differs')
        name = _text(row['name'], 'PCB native net')
        if name.casefold() in folded or type(row['class']) is not str or row['class'] not in known:
            _fail('duplicate/aliased native net or unqualified class identity')
        folded.add(name.casefold())
        parents = row.get('parameter_parents')
        if type(parents) is not dict or set(parents) != set(_DIMS):
            _fail('all four scalar parents required')
    # Existing original-PRO dimensions, priorities, source parents, floors and
    # canonical4Cu observations remain authoritative. This launches no worker.
    nc.audit_native(native, project, parent_policy=True)
    return {row['name']: row for row in rows}


def derive(raw_netlist, board_raw, project_raw, native_raw, *, source,
           schematic_source, schematic_raw):
    """Return a class-only proof or raise ValueError; never accept a board.

    Every payload is bytes, including the native JSON map, so duplicate keys and
    exact file hashes remain checkable. ``source`` and ``schematic_source`` are
    explicit canonical absolute paths; different staging parents are permitted
    only with the same stem. The caller proves their frozen snapshot relation.
    """
    board_path = _path(source, '.kicad_pcb')
    sch_path = _path(schematic_source, '.kicad_sch')
    if board_path.stem != sch_path.stem:
        _fail('PCB/schematic source stem differs')
    for raw, label in ((project_raw, 'project'), (native_raw, 'native map')):
        _raw(raw, label)
    # Reuse the existing duplicate-key/nonfinite/UTF8 strict byte parser without
    # applying preferences semantics to either original project or Native map.
    project = preferences._parse(project_raw, MAX_BYTES)
    native = preferences._parse(native_raw, MAX_BYTES)
    configured, known, policy = _source_classes(project)
    symbols, flags = _source_schematic(_tree(schematic_raw, 'schematic', 'kicad_sch'), configured)
    board_tree = _tree(board_raw, 'board', 'kicad_pcb')
    # Reuse the existing exact physical-layer scopes; a4Cu map cannot lose its
    # layer observation and masquerade as a2Cu class observation.
    if type(native) is dict and 'copper_layers' in native:
        nc.four_copper_source_layers(board_tree)
    else:
        from autorouter.layer_policy import _source_layers
        _source_layers(board_tree)
    board, pcb_terminals = _board_partitions(board_tree, symbols)
    schematic, sch_terminals = _netlist_partitions(
        _tree(raw_netlist, 'netlist', 'export'), schematic_source, symbols)
    if pcb_terminals != sch_terminals:
        _fail('complete PCB/schematic terminal census differs')
    native_rows = _native_map(native, source, board_raw, project_raw, project, known)
    if set(native_rows) != set(board):
        _fail('PCB native/source net census differs')
    by_partition = {frozenset(row['terminals']): (name, row)
                    for name, row in schematic.items()}
    if len(by_partition) != len(schematic):
        _fail('duplicate schematic terminal partition')
    joined = []
    for name, terminals in sorted(board.items()):
        found = by_partition.pop(frozenset(terminals), None)
        if found is None:
            _fail('PCB/schematic terminal partition differs')
        sch_name, sch = found; observed = native_rows[name]
        if sch_name != name:
            _fail('partition matched but net label differs')
        if observed['copper_pad_count'] != len(terminals):
            _fail('PCB native/source pad census differs')
        joined.append((name, terminals, sch, observed))
    if by_partition:
        _fail('unmatched schematic terminal partition')
    comparisons = []
    for name, terminals, sch, observed in joined:
        if sch['class'] != observed['class']:
            raise ClassIdentityMismatch(name, terminals, sch['class'], observed['class'],
                                        sch['class'] in known, len(joined))
        if sch['class'] not in known:
            _fail('unqualified equal class identity')
        comparisons.append({'net': name, 'terminals': [list(x) for x in sorted(terminals)],
            'class': observed['class'], 'effective_nm': {k: observed[k] for k in _DIMS},
            'parameter_parents': copy.deepcopy(observed['parameter_parents'])})
    return {'schema': 1, 'policy': POLICY, 'native_version': c.NATIVE_VERSION,
        'class_parity_qualified': True, 'accepted': False, 'routing_accepted': False,
        'production_qualified': False, 'native_execution_performed_by_comparator': False,
        'source': source, 'schematic_source': schematic_source,
        'sha256': {'board': _sha(board_raw), 'project': _sha(project_raw),
            'schematic': _sha(schematic_raw), 'netlist': _sha(raw_netlist),
            'native_map': _sha(native_raw)},
        'source_class_policy': policy, 'class_flags': flags,
        'known_class_identities': sorted(known), 'components': len(symbols),
        'terminals': len(pcb_terminals), 'nets': len(comparisons),
        'partitions': comparisons}
