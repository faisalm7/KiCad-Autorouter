"""Bounded repeated-sheet/unit identity proof, never routing admission.

SPDX-License-Identifier: GPL-3.0-or-later

This first pure slice consumes exact bytes. It neither reads files nor launches
tools. Shared evidence callers independently prove snapshots, actual Native
processes and fresh outputs. Default class identity is checked separately from
unchanged board rule floors; this proof cannot waive
engine constraints, original-design checks or final full-schematic DRC.
"""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
import re

from . import netclass as nc, preferences, schematic_classes as flat, sexpr as sx

POLICY = 'hierarchy-default-instance-unit-v2'
MAX_FILES = 16
MAX_INSTANCES = 64
MAX_DEPTH = 8
MAX_UNITS = 1024
MAX_POWER = 512
MAX_BYTES = flat.MAX_BYTES
_PIN = re.compile(r'[A-Za-z0-9_+\-]{1,32}')
_REF = re.compile(r'[A-Za-z#][A-Za-z0-9_#]{0,63}')
_DIMS = tuple(row[0] for row in nc._DIMENSIONS)


def _fail(message):
    raise ValueError('hierarchy parity: ' + message)


def _pin(value):
    if type(value) is not str or _PIN.fullmatch(value) is None:
        _fail('bounded literal pin required')
    return value


def _relative(value):
    flat._text(value, 'relative schematic path')
    path = PurePosixPath(value)
    if (path.is_absolute() or str(path) != value or path.suffix != '.kicad_sch'
            or any(part in {'.', '..', '~'} for part in path.parts)
            or any(char in value for char in ('\\', '$', ':'))):
        _fail('canonical in-project schematic path required')
    return path


def _ref(value):
    if type(value) is not str or _REF.fullmatch(value) is None:
        _fail('bounded literal reference required')
    return value


def _atoms(node, key):
    row = sx.one(node, key)
    if row is None or len(row) < 2 or any(type(x) is not str for x in row[1:]):
        _fail('missing atom list: ' + key)
    return [flat._atom(x, key) for x in row[1:]]


def _instance_paths(node, project, fields):
    group = sx.one(node, 'instances')
    if group is None or len(group) != 2:
        _fail('one project instance block required')
    item = group[1]
    if (type(item) is not list or len(item) < 3 or item[0] != 'project'
            or flat._atom(item[1], 'project') != project):
        _fail('instance project identity differs')
    result = {}
    for path in item[2:]:
        if type(path) is not list or len(path) != 2 + len(fields) or path[0] != 'path':
            _fail('unqualified instance path schema')
        flat._only(path, set(fields), start=2)
        name = flat._atom(path[1], 'instance path')
        if name in result:
            _fail('duplicate instance path')
        result[name] = {key: flat._single(path, key) for key in fields}
    return result


def _definition(node):
    """Prove pin membership from embedded common/unit/style definitions."""
    if len(node) < 2:
        _fail('embedded definition key missing')
    key = flat._atom(node[1], 'embedded key')
    flat._text(key, 'embedded key')
    if sx.one(node, 'extends') is not None:
        _fail('inherited embedded definition unsupported')
    power = sx.one(node, 'power')
    if power not in (None, ['power']):
        _fail('power definition schema differs')
    blocks = {}; styles = set(); prefixes = set()
    for sub in sx.children(node, 'symbol'):
        if len(sub) < 2:
            _fail('embedded unit key missing')
        name = flat._atom(sub[1], 'embedded unit')
        match = re.fullmatch(r'(.+)_([012])_([012])', name)
        if match is None:
            _fail('unqualified embedded unit/style')
        # Unit drawing names may omit the embedded key's library prefix. This
        # is only a literal suffix check, never library or alias resolution;
        # the complete lib_id/explicit lib_name and Native libsource join below
        # independently proves which definition belongs to the physical part.
        if key != match[1] and not key.endswith(':' + match[1]):
            _fail('embedded drawing prefix differs')
        prefixes.add(match[1])
        if len(prefixes) != 1:
            _fail('ambiguous embedded drawing prefixes')
        unit, style = map(int, match.groups()[1:])
        if (unit, style) in blocks:
            _fail('duplicate embedded unit/style')
        pins = []
        for pin in sx.children(sub, 'pin'):
            number = sx.one(pin, 'number')
            if number is None or len(number) < 2 or type(number[1]) is not str:
                _fail('embedded pin number missing')
            flat._only(number, {'effects'}, start=2)
            sx.one(number, 'effects')  # Reject duplicate presentation records.
            pins.append(_pin(flat._atom(number[1], 'pin number')))
        if len(pins) != len(set(pins)):
            _fail('duplicate pin within embedded unit/style')
        blocks[unit, style] = set(pins)
        if style:
            styles.add(style)
    units = {unit for unit, style in blocks if unit}
    # A saved single-unit part may put all pins in common unit0. Admit exactly
    # placed unit1/export A in that encoding; never invent a second unit.
    if not units:
        units = {1}
    if units not in ({1}, {1, 2}) or not styles:
        _fail('one or two embedded units required')
    memberships = {}; common_sets = []
    for style in sorted(styles):
        common = blocks.get((0, 0), set()) | blocks.get((0, style), set())
        common_sets.append(common)
        for unit in sorted(units):
            own = blocks.get((unit, 0), set()) | blocks.get((unit, style), set())
            if own & common:
                _fail('unit and common pin definitions overlap')
            pins = own | common
            if not pins or len(pins) > flat.MAX_TERMINALS:
                _fail('empty or excessive embedded unit')
            if unit in memberships and memberships[unit] != pins:
                _fail('drawing style changes terminal membership')
            memberships[unit] = pins
    if any(common != common_sets[0] for common in common_sets):
        _fail('drawing style changes common pins')
    common = common_sets[0]
    if units == {1, 2} and memberships[1] & memberships[2] != common:
        _fail('shared pins lack explicit common-unit definition')
    return {'key': key, 'units': memberships, 'common': common,
            'pins': set().union(*memberships.values()), 'power': power is not None}


def _closure(schematics, root_name):
    if (type(schematics) is not dict or not 1 <= len(schematics) <= MAX_FILES
            or sum(len(flat._raw(raw, 'schematic')) for raw in schematics.values()) > 100 * 1024**2):
        _fail('bounded exact schematic bytes required')
    trees = {}; folded = set()
    for name, raw in schematics.items():
        _relative(name)
        if name.casefold() in folded:
            _fail('case-aliased schematic paths')
        folded.add(name.casefold())
        tree = flat._tree(raw, 'schematic', 'kicad_sch')
        if sx.one(tree, 'version') != ['version', '20250114']:
            _fail('schematic version unqualified')
        pending = [tree]
        while pending:
            row = pending.pop()
            if row and row[0] in {'netclass_flag', 'bus_alias', 'group', 'variant'}:
                _fail('unsupported structural/class directive')
            pending.extend(x for x in row[1:] if type(x) is list)
        # Definition UUIDs are document-scoped. Actual saved projects can reuse
        # pin UUIDs in different documents. Full root/sheet/symbol/unit identity
        # below keeps those definitions distinct; no global flattening by UUID.
        # Reusing one document at two proven instance paths is also deliberate.
        all_ids = set()
        rows = [tree, *sx.children(tree, 'sheet'), *sx.children(tree, 'symbol')]
        rows += [pin for symbol in sx.children(tree, 'symbol') for pin in sx.children(symbol, 'pin')]
        for row in rows:
            uid = flat._uuid(flat._single(row, 'uuid'))
            if uid in all_ids:
                _fail('duplicate source definition UUID')
            all_ids.add(uid)
        trees[name] = tree
    if root_name not in trees:
        _fail('paired root schematic absent')
    root_uuid = flat._uuid(flat._single(trees[root_name], 'uuid'))
    instances = []; used = set()

    def visit(name, ids, names, stack):
        if name in stack or len(ids) > MAX_DEPTH or len(instances) >= MAX_INSTANCES:
            _fail('cyclic or excessive hierarchy')
        instance = {'file': name, 'ids': ids, 'names': names}
        instances.append(instance); used.add(name)
        children = sx.children(trees[name], 'sheet'); sibling_names = set()
        for sheet in children:
            props = flat._properties(sheet)
            child_name = flat._text(props.get('Sheetname'), 'sheet name')
            if ('/' in child_name or '\\' in child_name or child_name.casefold() in sibling_names):
                _fail('ambiguous sibling sheet name')
            sibling_names.add(child_name.casefold())
            rel = _relative(props.get('Sheetfile'))
            child = str(PurePosixPath(name).parent / rel)
            if child not in trees:
                _fail('hierarchy child absent from captured bytes')
            uid = flat._uuid(flat._single(sheet, 'uuid'))
            visit(child, (*ids, uid), (*names, child_name), (*stack, name))

    visit(root_name, (), (), ())
    if used != set(trees):
        _fail('captured schematic lies outside paired closure')
    paths = {}
    for instance in instances:
        paths.setdefault(instance['file'], set()).add('/' + '/'.join((root_uuid, *instance['ids'])))
    project = PurePosixPath(root_name).stem
    for name, tree in trees.items():
        for sheet in sx.children(tree, 'sheet'):
            rows = _instance_paths(sheet, project, ('page',))
            if set(rows) != paths[name] or any(not r['page'].isascii() or not r['page'].isdigit() or int(r['page']) <= 0 for r in rows.values()):
                _fail('sheet instance path/page census differs')
    return trees, instances, paths, root_uuid, project


def _symbols(trees, instances, paths, root_uuid, project):
    components = {}; powers = []; refs = set()
    definitions_seen = 0; library_pins = 0; placed_units = 0; expanded_pins = 0
    for name, tree in trees.items():
        lib = sx.one(tree, 'lib_symbols')
        if lib is None:
            _fail('embedded library absent')
        definitions = {}
        for row in lib[1:]:
            if type(row) is not list or not row or row[0] != 'symbol':
                _fail('embedded library schema differs')
            definition = _definition(row)
            definitions_seen += 1; library_pins += len(definition['pins'])
            if definitions_seen > flat.MAX_COMPONENTS or library_pins > flat.MAX_TERMINALS:
                _fail('embedded definition/terminal census limit')
            if definition['key'] in definitions:
                _fail('duplicate embedded key')
            definitions[definition['key']] = definition
        for symbol in sx.children(tree, 'symbol'):
            props = flat._properties(symbol)
            uid = flat._uuid(flat._single(symbol, 'uuid'))
            lib_id = flat._single(symbol, 'lib_id')
            alias = sx.one(symbol, 'lib_name')
            key = flat._single(symbol, 'lib_name') if alias is not None else lib_id
            if key not in definitions:
                _fail('embedded symbol identity unresolved')
            definition = definitions[key]
            unit_text = flat._single(symbol, 'unit')
            if unit_text not in {'1', '2'} or int(unit_text) not in definition['units']:
                _fail('placed unit differs from embedded definition')
            unit = int(unit_text)
            if (sx.one(symbol, 'on_board') != ['on_board', 'yes']
                    or sx.one(symbol, 'dnp') not in (None, ['dnp', 'no'])):
                _fail('off-board/DNP source unit unsupported')
            pins = [_pin(flat._atom(row[1], 'placed pin')) for row in sx.children(symbol, 'pin') if len(row) == 3]
            if (len(pins) != len(sx.children(symbol, 'pin')) or len(pins) != len(set(pins))
                    or set(pins) not in (definition['pins'], definition['units'][unit])):
                _fail('placed/embedded terminal census differs')
            bindings = _instance_paths(symbol, project, ('reference', 'unit'))
            if set(bindings) != paths[name]:
                _fail('symbol instance closure differs')
            for instance in (r for r in instances if r['file'] == name):
                placed_units += 1; expanded_pins += len(pins)
                if placed_units > MAX_UNITS or expanded_pins > flat.MAX_TERMINALS:
                    _fail('expanded source unit/terminal census limit')
                full = '/' + '/'.join((root_uuid, *instance['ids']))
                bound = bindings[full]; ref = _ref(bound['reference'])
                if bound['unit'] != unit_text:
                    _fail('instance/placed unit differs')
                footprint = props.get('Footprint')
                if type(footprint) is not str:
                    _fail('explicit footprint property required')
                member = dict(uuid=uid, unit=unit, path=full, file=name)
                if definition['power']:
                    if footprint != '' or ref.casefold() in refs or len(powers) >= MAX_POWER:
                        _fail('ambiguous power-only identity')
                    refs.add(ref.casefold()); powers.append(dict(reference=ref, **member))
                    continue
                if not footprint or ref.startswith('#'):
                    _fail('physical footprint identity required')
                prior = components.get(ref)
                identity = (name, instance['ids'], key, lib_id, alias is not None, footprint)
                if prior is None:
                    if ref.casefold() in refs or len(components) >= flat.MAX_COMPONENTS:
                        _fail('duplicate/aliased or excessive physical reference')
                    refs.add(ref.casefold())
                    prior = dict(identity=identity, definition=definition, units={}, ids=instance['ids'], names=instance['names'], footprint=footprint, lib_id=lib_id, alias=alias is not None, key=key)
                    components[ref] = prior
                if prior['identity'] != identity or unit in prior['units']:
                    _fail('units span identities or duplicate unit')
                prior['units'][unit] = member
    if not components:
        _fail('no physical components')
    for comp in components.values():
        if set(comp['units']) != set(comp['definition']['units']):
            _fail('incomplete physical unit census')
    return components, powers


def _board(tree, components):
    version = sx.one(tree, 'version')
    if version not in (['version', '20241229'], ['version', '20260206']):
        _fail('board version unqualified')
    if sx.children(tree, 'module'):
        _fail('legacy footprint representation unsupported')
    numeric = version == ['version', '20241229']; codes = {}; names = set()
    for net in sx.children(tree, 'net'):
        if not numeric or len(net) != 3 or any(type(x) is not str for x in net):
            _fail('board net table/version differs')
        code = net[1]; name = flat._atom(net[2], 'board net')
        if (not code.isascii() or not code.isdigit() or str(int(code)) != code
                or code in codes or name.casefold() in names
                or (code == '0') != (name == '')):
            _fail('ambiguous board net code/name')
        if code != '0':
            flat._text(name, 'board net')
        codes[code] = name; names.add(name.casefold())
    if numeric and (codes.get('0') != '' or len(codes) > flat.MAX_NETS + 1):
        _fail('bounded board net0 table required')
    from .layer_policy import NONCOPPER, _two_copper_table
    # Source-all identity proof additionally observes the five original user
    # layers in the retained source. This does not broaden explicit route-layer
    # restriction, which still calls the unchanged narrower version/table gate.
    noncopper = {**NONCOPPER, '47': 'User.5', '49': 'User.6',
                 '51': 'User.7', '53': 'User.8', '55': 'User.9'}
    _two_copper_table(tree, noncopper=noncopper)
    partitions = {}; terminals = set(); extras = []; found = set(); uuids = set()
    for fp in sx.children(tree, 'footprint'):
        ref = _ref(flat._properties(fp).get('Reference'))
        if ref not in components or ref in found:
            _fail('unmatched or duplicate footprint')
        comp = components[ref]; found.add(ref)
        uid = flat._uuid(flat._single(fp, 'uuid'))
        if uid in uuids:
            _fail('duplicate PCB UUID')
        uuids.add(uid)
        member_paths = {'/' + '/'.join((*comp['ids'], unit['uuid']))
                        for unit in comp['units'].values()}
        if flat._single(fp, 'path') not in member_paths:
            _fail('footprint instance/group path differs')
        if sx.children(fp, 'net_tie_pad_groups'):
            _fail('net ties remain unsupported')
        connected = set()
        for pad in sx.children(fp, 'pad'):
            if len(pad) < 4 or pad[2] not in {'smd', 'thru_hole'}:
                _fail('ordinary copper pad required')
            pin = _pin(flat._atom(pad[1], 'pad number'))
            pad_id = flat._uuid(flat._single(pad, 'uuid'))
            if pad_id in uuids or len(uuids) > flat.MAX_TERMINALS + flat.MAX_COMPONENTS:
                _fail('duplicate or excessive PCB UUID')
            uuids.add(pad_id)
            layers = _atoms(pad, 'layers')
            if not any(name.endswith('.Cu') for name in layers):
                _fail('copper pad layer required')
            net = sx.one(pad, 'net')
            if net is None:
                if pin in comp['definition']['pins']:
                    _fail('library terminal has no PCB net')
                extras.append(dict(reference=ref, footprint_uuid=uid, pad_uuid=pad_id, number=pin,
                                   pad_sha256=flat._sha(sx.dump(pad).encode())))
                continue
            if numeric:
                if (len(net) != 3 or any(type(x) is not str for x in net)
                        or net[1] == '0' or net[1] not in codes
                        or flat._atom(net[2], 'PCB net') != codes[net[1]]):
                    _fail('pad/source net code-name binding differs')
                name = codes[net[1]]
            else:
                name = flat._text(flat._single(pad, 'net'), 'PCB net')
            terminal = (ref, pin)
            if pin not in comp['definition']['pins'] or terminal in terminals:
                _fail('unknown or duplicate connected PCB terminal')
            connected.add(pin); terminals.add(terminal)
            partitions.setdefault(name, set()).add(terminal)
        if connected != comp['definition']['pins']:
            _fail('PCB/library connected terminal census differs')
    if found != set(components) or not 1 <= len(partitions) <= flat.MAX_NETS:
        _fail('PCB component/net census differs')
    if numeric and set(codes.values()) - {''} != set(partitions):
        _fail('board net table/terminal census differs')
    if len({name.casefold() for name in partitions}) != len(partitions):
        _fail('case-aliased PCB net labels')
    return partitions, terminals, sorted(extras, key=lambda row: row['pad_uuid'])


def _netlist(tree, components, instances, schematic_source, native_version):
    flat._only(tree, {'version', 'design', 'components', 'groups', 'variants', 'libparts', 'libraries', 'nets'})
    if flat._single(tree, 'version') != 'E':
        _fail('native netlist version differs')
    if sx.one(tree, 'groups') != ['groups'] or sx.one(tree, 'variants') != ['variants']:
        _fail('native group/variant semantics unsupported')
    if sx.one(tree, 'libparts') is None or sx.one(tree, 'libraries') is None:
        _fail('native library sections missing')
    design = sx.one(tree, 'design')
    if design is None or flat._single(design, 'source') != schematic_source or flat._single(design, 'tool') != 'Eeschema ' + native_version:
        _fail('native source/tool differs')
    expected = {('/' + '/'.join(r['names']) + ('/' if r['names'] else ''), '/' + '/'.join(r['ids']) + ('/' if r['ids'] else '')) for r in instances}
    observed = set(); pages = set()
    for sheet in sx.children(design, 'sheet'):
        key = (flat._single(sheet, 'name'), flat._single(sheet, 'tstamps'))
        page = flat._single(sheet, 'number')
        if key in observed or page in pages or not page.isascii() or not page.isdigit() or int(page) <= 0:
            _fail('native sheet identity/page duplicate')
        observed.add(key); pages.add(page)
    if observed != expected:
        _fail('native sheet instance closure differs')
    section = sx.one(tree, 'components')
    if section is None:
        _fail('native component section missing')
    flat._only(section, {'comp'}); seen = set(); declared = set()
    for row in section[1:]:
        ref = _ref(flat._single(row, 'ref'))
        if ref not in components or ref in seen:
            _fail('unknown or duplicate native component')
        comp = components[ref]; seen.add(ref)
        if flat._single(row, 'footprint') != comp['footprint']:
            _fail('native/source footprint metadata differs')
        # Pinned10.0.7 makeSymbols chooses the lowest UUID as primary, then
        # emits extra UUIDs before that primary. Our explicit one/two-unit
        # scope therefore has descending UUID order, independently of A/B.
        # Unit-number/pin membership and the exact instance/library join below
        # remain separate requirements; stamp order is not a unit index.
        stamps = sorted((unit['uuid'] for unit in comp['units'].values()), reverse=True)
        if _atoms(row, 'tstamps') != stamps:
            _fail('native unit UUID order/census differs')
        path = sx.one(row, 'sheetpath')
        if path is None or (flat._single(path, 'names'), flat._single(path, 'tstamps')) != ('/' + '/'.join(comp['names']) + ('/' if comp['names'] else ''), '/' + '/'.join(comp['ids']) + ('/' if comp['ids'] else '')):
            _fail('native component sheet instance differs')
        libsource = sx.one(row, 'libsource')
        if libsource is None:
            _fail('native library source missing')
        lib, part = flat._single(libsource, 'lib'), flat._single(libsource, 'part')
        if (comp['alias'] and (lib != '' or part != comp['key'])
                or not comp['alias'] and lib + ':' + part != comp['lib_id']):
            _fail('native/embedded library identity differs')
        units = sx.one(row, 'units'); unit_seen = set()
        if units is None:
            _fail('native unit census absent')
        flat._only(units, {'unit'})
        for unit in units[1:]:
            letter = flat._single(unit, 'name')
            if letter not in {'A', 'B'} or letter in unit_seen:
                _fail('native unit identity duplicate/unsupported')
            unit_seen.add(letter); number = ord(letter) - ord('A') + 1
            pins = sx.one(unit, 'pins')
            if pins is None:
                _fail('native unit pins missing')
            flat._only(pins, {'pin'})
            values = [_pin(flat._single(pin, 'num')) for pin in pins[1:]]
            if len(values) != len(set(values)) or set(values) != comp['definition']['units'].get(number):
                _fail('native/embedded unit pin membership differs')
        if unit_seen != {chr(64 + i) for i in comp['units']}:
            _fail('native/source unit census differs')
        declared.update((ref, pin) for pin in comp['definition']['pins'])
    if seen != set(components):
        _fail('native physical component census differs')
    nets = sx.one(tree, 'nets')
    if nets is None:
        _fail('native nets missing')
    flat._only(nets, {'net'}); result = {}; used = set(); codes = set(); folded = set()
    for net in nets[1:]:
        flat._only(net, {'code', 'name', 'class', 'node'})
        name = flat._text(flat._single(net, 'name'), 'native net')
        code = flat._pin(flat._single(net, 'code'))
        if code in codes or name.casefold() in folded or flat._single(net, 'class') != 'Default':
            _fail('native net/class identity differs')
        codes.add(code); folded.add(name.casefold()); terminals = set()
        for node in sx.children(net, 'node'):
            terminal = (_ref(flat._single(node, 'ref')), _pin(flat._single(node, 'pin')))
            if terminal not in declared or terminal in used:
                _fail('unknown or duplicate native terminal')
            terminals.add(terminal); used.add(terminal)
        if not terminals or len(result) >= flat.MAX_NETS:
            _fail('empty or excessive native nets')
        result[name] = terminals
    if used != declared:
        _fail('native complete terminal census differs')
    return result, used


def _classes(raw, source, board_raw, project_raw, project, partitions, native_version):
    native = preferences._parse(flat._raw(raw, 'native map'), MAX_BYTES)
    required = {'schema', 'native_version', 'units', 'resolution', 'source', 'board_sha256', 'project_sha256', 'board_saved', 'nets'}
    if (type(native) is not dict or set(native) not in (required, required | {'effective_floors_nm'})
            or type(native.get('schema')) is not int or native['schema'] != 1
            or native.get('native_version') != native_version or native.get('units') != 'integer nanometres'
            or native.get('resolution') != flat._RESOLUTION or native.get('source') != source
            or native.get('board_sha256') != flat._sha(board_raw) or native.get('project_sha256') != flat._sha(project_raw)
            or native.get('board_saved') is not False):
        _fail('native class map source/schema differs')
    if 'effective_floors_nm' in native:
        from .netclass_native import validate_floors
        validate_floors(native['effective_floors_nm'], project)
    cls = project['net_settings']['classes'][0]
    priority = cls.get('priority')
    if type(priority) is not int or not 0 <= priority <= 2147483647:
        _fail('explicit Default priority required')
    rows = native['nets']; found = set(); codes = set(); result = []
    if type(rows) is not list or len(rows) != len(partitions):
        _fail('native class net census differs')
    for row in rows:
        if type(row) is not dict or set(row) != {'name', 'netcode', 'copper_pad_count', 'class', 'parameter_parents', *_DIMS}:
            _fail('native class row schema differs')
        name = row['name']; code = row['netcode']
        if (type(name) is not str or name not in partitions or name in found
                or type(code) is not int or code <= 0 or code in codes
                or row['class'] != 'Default' or type(row['copper_pad_count']) is not int
                or row['copper_pad_count'] != len(partitions[name])):
            _fail('native class identity/pad census differs')
        found.add(name); codes.add(code)
        for native_key, source_key, floor_key in nc._DIMENSIONS:
            if type(row[native_key]) is not int or row[native_key] != nc._millimetres_to_nm(cls.get(source_key)):
                _fail('native scalar differs from unchanged Default definition')
        nc._check_parameter_parents(row, cls)
        result.append(dict(net=name, terminals=[list(x) for x in sorted(partitions[name])],
                           class_identity='Default', effective_nm={key: row[key] for key in _DIMS}, parameter_parents=row['parameter_parents']))
    return sorted(result, key=lambda row: row['net'])


def _project(project_raw):
    project = preferences._parse(flat._raw(project_raw, 'project'), MAX_BYTES)
    policy = nc.qualify_project(project)
    settings = project.get('net_settings')
    if (policy.get('mode') != 'single_default' or type(settings) is not dict
            or settings.get('netclass_assignments') not in (None, {}) or settings.get('netclass_patterns') not in (None, [])
            or len(settings['classes']) != 1 or settings['classes'][0]['name'] != 'Default'):
        _fail('only explicit single Default without assignments/patterns')
    return project, policy


def source_requirement(board_raw, project_raw, *, source, schematics,
                       native_version='10.0.7'):
    """Static source prerequisite only; actual task/final Native proof is pending."""
    board_path = flat._path(source, '.kicad_pcb')
    if type(schematics) is not dict or native_version != '10.0.7':
        _fail('exact schematic map and selected10.0.7 required')
    schematics = schematics.copy(); project, policy = _project(project_raw)
    trees, instances, paths, root_uuid, project_name = _closure(schematics, board_path.with_suffix('.kicad_sch').name)
    if len(instances) < 2:
        _fail('this policy requires a repeated or hierarchical source')
    components, powers = _symbols(trees, instances, paths, root_uuid, project_name)
    board, terminals, extras = _board(flat._tree(board_raw, 'board', 'kicad_pcb'), components)
    return dict(schema=1, policy=POLICY, status='pending_native_class_parity',
        native_validation_performed=False, class_parity_qualified=False,
        accepted=False, routing_accepted=False, production_qualified=False,
        source=source, source_class_policy=policy, class_flags=[], known_class_identities=['Default'],
        components=len(components), terminals=len(terminals), nets=len(board), instances=len(instances),
        partitions={name: [list(x) for x in sorted(terminals)] for name, terminals in sorted(board.items())},
        schematic_hashes={name: flat._sha(raw) for name, raw in sorted(schematics.items())})


def derive(raw_netlist, board_raw, project_raw, native_raw, *, source,
           schematic_source, schematics, native_version='10.0.7'):
    """Return source-derived identity proof only; every acceptance flag is false."""
    if type(schematics) is not dict:
        _fail('exact schematic byte mapping required')
    # An exact dict copy keeps the parse and final hashes on the same immutable
    # byte values if a caller replaces entries in its own mapping during work.
    schematics = schematics.copy()
    board_path = flat._path(source, '.kicad_pcb')
    sch_path = flat._path(schematic_source, '.kicad_sch')
    if board_path.stem != sch_path.stem or native_version != '10.0.7':
        _fail('source stem or Native version unqualified')
    project, policy = _project(project_raw)
    trees, instances, paths, root_uuid, project_name = _closure(schematics, sch_path.name)
    components, powers = _symbols(trees, instances, paths, root_uuid, project_name)
    board, terminals, extras = _board(flat._tree(board_raw, 'board', 'kicad_pcb'), components)
    schematic, declared = _netlist(flat._tree(raw_netlist, 'netlist', 'export'), components, instances, schematic_source, native_version)
    if terminals != declared or board != schematic or len(terminals) > flat.MAX_TERMINALS:
        _fail('complete PCB/SCH net terminal partitions differ')
    classes = _classes(native_raw, source, board_raw, project_raw, project, board, native_version)
    return dict(schema=1, policy=POLICY, native_version=native_version,
        class_parity_qualified=True, accepted=False, routing_accepted=False, production_qualified=False,
        native_execution_performed_by_comparator=False, source=source, schematic_source=schematic_source,
        sha256=dict(board=flat._sha(board_raw), project=flat._sha(project_raw), netlist=flat._sha(raw_netlist), native_map=flat._sha(native_raw),
                    schematics={name: flat._sha(raw) for name, raw in sorted(schematics.items())}),
        source_class_policy=policy, board_floors_waived=False, components=len(components), terminals=len(terminals), nets=len(board), instances=len(instances),
        root_uuid=root_uuid, instance_bindings=[dict(file=r['file'], sheet_uuids=list(r['ids']), sheet_names=list(r['names'])) for r in instances],
        component_bindings=[dict(reference=ref, footprint=comp['footprint'], embedded_key=comp['key'], lib_id=comp['lib_id'],
            units=[comp['units'][i] for i in sorted(comp['units'])]) for ref, comp in sorted(components.items())],
        power_only_bindings=sorted(powers, key=lambda row: (row['path'], row['uuid'])), unconnected_pads=extras, partitions=classes)
