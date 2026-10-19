"""Small project-owned generated hierarchy data; never Native/routing evidence.

SPDX-License-Identifier: GPL-3.0-or-later
No demo-board geometry or schematic content is copied. The native-shaped rows
are constructed controls for identity joins, not an independent board family.
"""
import hashlib
import json
import uuid

from autorouter import sexpr as sx

STEM = 'owned_hierarchy'
ROOT_SCH = STEM + '.kicad_sch'
CHILD_SCH = 'child.kicad_sch'
SOURCE = '/owned/candidate/' + STEM + '.kicad_pcb'
SCHEMATIC_SOURCE = '/owned/class-input/' + ROOT_SCH
NAMESPACE = uuid.UUID('73fec129-cf26-42f5-babe-94fac1ff36c3')


def uid(name):
    return str(uuid.uuid5(NAMESPACE, name))


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def encoded(tree):
    return (sx.dump(tree) + '\n').encode()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(number, kind='passive'):
    return ['pin', kind, 'line', ['at', '0', '0', '0'], ['length', '2.54'],
            ['name', quote('P' + number), ['effects', ['font', ['size', '1.27', '1.27']]]],
            ['number', quote(number), ['effects', ['font', ['size', '1.27', '1.27']]]]]


def library(name, units, *, power=False):
    base = name.rsplit(':', 1)[-1]
    result = ['symbol', quote(name)]
    if power:
        result.append(['power'])
    result += [['in_bom', 'yes'], ['on_board', 'yes'],
               ['property', '"Reference"', '"#PWR"' if power else '"U"'],
               ['property', '"Value"', quote(base)],
               ['property', '"Footprint"', '""' if power else quote('Owned:' + base)]]
    for unit, numbers in units.items():
        for style in (1, 2):
            result.append(['symbol', quote('%s_%s_%s' % (base, unit, style)),
                           *[pin(number, 'power_in' if power or unit == 0 else 'passive')
                             for number in numbers]])
    return result


def symbol(name, lib, unit, package_pins, references, *, alias=None, power=False):
    # Placed multi-unit symbols deliberately list every package pin, as the
    # real KiCad source does. Unit membership must come from library+export.
    result = ['symbol', ['lib_id', quote(lib)]]
    if alias is not None:
        result.append(['lib_name', quote(alias)])
    result += [['at', '25.4', '25.4', '0'], ['unit', str(unit)],
               ['exclude_from_sim', 'no'], ['in_bom', 'yes'], ['on_board', 'yes'], ['dnp', 'no'],
               ['uuid', quote(uid(name))],
               ['property', '"Reference"', quote(references[0][1])],
               ['property', '"Value"', quote('PWR' if power else lib.rsplit(':', 1)[-1])],
               ['property', '"Footprint"', '""' if power else quote('Owned:' + lib.rsplit(':', 1)[-1])],
               *[['pin', quote(number), ['uuid', quote(uid(name + '/pin/' + number))]]
                 for number in package_pins],
               ['instances', ['project', quote(STEM),
                 *[['path', quote(path), ['reference', quote(reference)], ['unit', str(unit)]]
                   for path, reference in references]]]]
    return result


def footprint(reference, path, terminals, extras=()):
    result = ['footprint', '"Owned:Package"', ['layer', '"F.Cu"'],
              ['uuid', quote(uid('footprint/' + reference))], ['at', '20', '20'],
              ['property', '"Reference"', quote(reference)],
              ['property', '"Value"', '"Owned"'], ['path', quote(path)]]
    for index, (number, net) in enumerate([*terminals, *[(n, None) for n in extras]]):
        pad = ['pad', quote(number), 'thru_hole', 'circle', ['at', str(index * 2), '0'],
               ['size', '1.5', '1.5'], ['drill', '.8'], ['layers', '"*.Cu"', '"*.Mask"'],
               ['uuid', quote(uid('pad/%s/%s' % (reference, index)))]]
        if net is not None:
            pad.append(['net', quote(net)])
        result.append(pad)
    return result


def component(reference, stamps, sheet_name, sheet_path, lib, part, units, *, footprint_name=None):
    footprint_name = 'Owned:' + part if footprint_name is None else footprint_name
    return ['comp', ['ref', quote(reference)], ['value', quote(part)],
            ['footprint', quote(footprint_name)], ['description', '"Owned test"'],
            ['fields', ['field', ['name', '"Footprint"'], quote(footprint_name)]],
            ['libsource', ['lib', quote(lib)], ['part', quote(part)], ['description', '"Owned test"']],
            ['sheetpath', ['names', quote(sheet_name)], ['tstamps', quote(sheet_path)]],
            ['tstamps', *[quote(stamp) for stamp in stamps]],
            ['units', *[['unit', ['name', quote(name)], ['pins',
                        *[['pin', ['num', quote(number)]] for number in numbers]]]
                       for name, numbers in units]]]


def case():
    root_id, child_id = uid('root'), uid('child')
    sheet_ids = {name: uid('sheet/' + name) for name in ('A', 'B')}
    root_path = '/' + root_id
    children = [('/' + root_id + '/' + sheet_ids[name], name) for name in ('A', 'B')]
    root = ['kicad_sch', ['version', '20250114'], ['generator', '"owned-test"'],
            ['uuid', quote(root_id)], ['lib_symbols',
             library('Owned:RootTerm', {1: ['1']}), library('Owned:Power', {1: ['1']}, power=True)]]
    for number, (path, name) in enumerate(children, 2):
        root.append(['sheet', ['at', '20', '20'], ['size', '10', '10'],
            ['uuid', quote(sheet_ids[name])], ['property', '"Sheetname"', quote(name)],
            ['property', '"Sheetfile"', quote(CHILD_SCH)],
            ['instances', ['project', quote(STEM), ['path', quote(root_path), ['page', quote(str(number))]]]]])
    root += [symbol('root/X', 'Owned:RootTerm', 1, ['1'], [(root_path, 'X1')]),
             symbol('root/P', 'Owned:Power', 1, ['1'], [(root_path, '#PWR01')], power=True)]
    child = ['kicad_sch', ['version', '20250114'], ['generator', '"owned-test"'],
             ['uuid', quote(child_id)], ['lib_symbols', library('Owned:Dual', {0: ['3'], 1: ['1'], 2: ['2']}),
              library('AliasJack', {1: ['R', 'T']}), library('Owned:Power', {1: ['1']}, power=True)]]
    child += [symbol('child/U/1', 'Owned:Dual', 1, ['1', '2', '3'],
                     [(path, 'U' + str(index)) for index, (path, _) in enumerate(children, 1)]),
              symbol('child/U/2', 'Owned:Dual', 2, ['1', '2', '3'],
                     [(path, 'U' + str(index)) for index, (path, _) in enumerate(children, 1)]),
              symbol('child/J', 'Owned:Jack', 1, ['R', 'T'],
                     [(path, 'J' + str(index)) for index, (path, _) in enumerate(children, 1)], alias='AliasJack'),
              symbol('child/P', 'Owned:Power', 1, ['1'],
                     [(path, '#PWR0' + str(index + 1)) for index, (path, _) in enumerate(children, 1)], power=True)]
    board = ['kicad_pcb', ['version', '20260206'], ['generator', '"owned-test"'],
             ['layers', ['0', '"F.Cu"', 'signal'], ['2', '"B.Cu"', 'signal']],
             ['setup', ['stackup', ['layer', '"F.Cu"', ['type', '"copper"']],
                                  ['layer', '"B.Cu"', ['type', '"copper"']]]],
             footprint('X1', '/' + uid('root/X'), [('1', 'GND')])]
    netlist = ['export', ['version', '"E"'], ['design', ['source', quote(SCHEMATIC_SOURCE)],
               ['date', '"2026-10-19T00:00:00"'], ['tool', '"Eeschema 10.0.7"'],
               ['sheet', ['number', '"1"'], ['name', '"/"'], ['tstamps', '"/"']]],
               ['components', component('X1', [uid('root/X')], '/', '/', 'Owned', 'RootTerm', [('A', ['1'])])],
               ['groups'], ['variants'], ['libparts'], ['libraries'], ['nets']]
    nets = {'GND': [('X1', '1')]}
    for index, name in enumerate(('A', 'B'), 1):
        sheet_path = '/' + sheet_ids[name] + '/'
        sx.one(netlist, 'design').append(['sheet', ['number', quote(str(index + 1))],
                     ['name', quote('/' + name + '/')], ['tstamps', quote(sheet_path)]])
        u, j = 'U' + str(index), 'J' + str(index)
        a, b = '/' + name + '/SIG_A', '/' + name + '/SIG_B'
        board += [footprint(u, '/' + sheet_ids[name] + '/' + uid('child/U/1'),
                            [('1', a), ('2', b), ('3', 'GND')]),
                  footprint(j, '/' + sheet_ids[name] + '/' + uid('child/J'), [('R', a), ('T', 'GND')], ['MP', 'MP'])]
        sx.one(netlist, 'components').extend([
            component(u, [uid('child/U/1'), uid('child/U/2')], '/' + name + '/', sheet_path,
                      'Owned', 'Dual', [('A', ['1', '3']), ('B', ['2', '3'])]),
            component(j, [uid('child/J')], '/' + name + '/', sheet_path, '', 'AliasJack', [('A', ['R', 'T'])],
                      footprint_name='Owned:Jack')])
        nets['GND'] += [(u, '3'), (j, 'T')]
        nets[a], nets[b] = [(u, '1'), (j, 'R')], [(u, '2')]
    for code, (name, terminals) in enumerate(nets.items(), 1):
        sx.one(netlist, 'nets').append(['net', ['code', quote(str(code))], ['name', quote(name)],
             ['class', '"Default"'], *[['node', ['ref', quote(ref)], ['pin', quote(number)],
                ['pinfunction', quote('P' + number + '_' + number)], ['pintype', '"passive"']]
                for ref, number in terminals]])
    project = {'net_settings': {'meta': {'version': 4}, 'netclass_assignments': None,
        'netclass_patterns': [], 'net_colors': None, 'classes': [{'name': 'Default', 'priority': 2147483647,
        'track_width': .2, 'clearance': .2, 'via_diameter': .6, 'via_drill': .3}]},
        'board': {'design_settings': {'rules': {'min_track_width': .3, 'min_clearance': .3,
        'min_via_diameter': 1.5, 'min_through_hole_diameter': .3}}}}
    dimensions = dict(width_nm=200000, clearance_nm=200000, via_diameter_nm=600000, via_drill_nm=300000)
    native = {'schema': 1, 'native_version': '10.0.7', 'units': 'integer nanometres',
        'resolution': 'BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()',
        'source': SOURCE, 'board_saved': False, 'nets': [dict(name=name, netcode=code,
         copper_pad_count=len(terminals), **dimensions, **{'class': 'Default'},
         parameter_parents={key: dict(name='Default', value_nm=value, specified=True, priority=2147483647)
                            for key, value in dimensions.items()})
         for code, (name, terminals) in enumerate(nets.items(), 1)]}
    return dict(board=board, project=project, schematics={ROOT_SCH: root, CHILD_SCH: child},
                netlist=netlist, native=native, source=SOURCE, schematic_source=SCHEMATIC_SOURCE)


def arguments(value, *, refresh_hashes=True):
    board, project = encoded(value['board']), json_bytes(value['project'])
    native = dict(value['native'])
    if refresh_hashes:
        native.update(board_sha256=digest(board), project_sha256=digest(project))
    return dict(raw_netlist=encoded(value['netlist']), board_raw=board, project_raw=project,
                native_raw=json_bytes(native), source=value['source'], schematic_source=value['schematic_source'],
                schematics={name: encoded(tree) for name, tree in value['schematics'].items()})


def numeric_20241229(value, *, explicit_zero=False):
    """Give this owned fixture the exact older code/name representation.

    This constructs alternative test inputs; it never converts a real source
    project or asserts that rewritten inputs are valid evidence for originals.
    """
    board = value['board']
    sx.one(board, 'version')[1] = '20241229'
    codes = {row['name']: row['netcode'] for row in value['native']['nets']}
    board.extend([['net', '0', '""'],
                  *[['net', str(code), quote(name)] for name, code in codes.items()]])
    for fp in sx.children(board, 'footprint'):
        for pad in sx.children(fp, 'pad'):
            net = sx.one(pad, 'net')
            if net is not None:
                name = sx.unquote(net[1])
                net[:] = ['net', str(codes[name]), quote(name)]
            elif explicit_zero:
                pad.append(['net', '0', '""'])
    return value
