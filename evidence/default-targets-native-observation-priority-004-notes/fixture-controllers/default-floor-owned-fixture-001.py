"""Prepare owned prospective Default-floor/via controls; never call Native.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
The repository grant covers this adaptation and all generated project files.
"""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, netclass as nc, sexpr as sx

FACTORY = ROOT / 'experiments/native_schematic_transport_v1/fixture.py'
FACTORY_SHA = 'fd6b36d6bb8a80d816208c48ade32e93b194a2fd919b8dfbb0c8a7371acbb4dd'
LICENSE = ROOT / 'experiments/native_schematic_transport_v1/COPYING'
LICENSE_SHA = '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986'
OUTPUT = ROOT / '.runs/default-floor-owned-controls-001'
NS = uuid.UUID('dbf3efb1-07a9-4a6d-8ad8-b5f3e09ffbea')
RAW_CLASS = {'track_width': .2, 'clearance': .1, 'via_diameter': .6, 'via_drill': .3}
HARD = {'min_track_width': .3, 'min_clearance': .2, 'min_via_diameter': .9,
        'min_through_hole_diameter': .4, 'min_via_annular_width': .25}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def props(node):
    rows = sx.children(node, 'property')
    result = {sx.unquote(row[1]): row for row in rows}
    assert len(result) == len(rows)
    return result


def ref(node):
    return sx.unquote(props(node)['Reference'][2])


def replace_atoms(node, replacements):
    if type(node) is list:
        return [replace_atoms(value, replacements) for value in node]
    for old, new in replacements.items():
        node = node.replace(old, new)
    return node


def uuid_atoms(node):
    result = set()
    def walk(value):
        if type(value) is not list:
            return
        if value and value[0] == 'uuid':
            assert len(value) == 2
            result.add(sx.unquote(value[1]))
        for child in value:
            walk(child)
    walk(node)
    return result


def make(factory, label):
    stem = 'owned-default-floor-' + label.lower()
    source_id = 'owned-default-floor-via-control-001-' + label
    base = factory.files()
    board = sx.parse(base[factory.STEM + '.kicad_pcb'].decode())
    schematic = sx.parse(base[factory.STEM + '.kicad_sch'].decode())
    old_ids = uuid_atoms(board) | uuid_atoms(schematic)
    replacements = {old: str(uuid.uuid5(NS, label + ':' + old)) for old in sorted(old_ids)}
    replacements.update({factory.SOURCE_ID: source_id, factory.STEM: stem})
    board = replace_atoms(board, replacements)
    schematic = replace_atoms(schematic, replacements)
    original = copy.deepcopy(board)
    footprints = {ref(fp): fp for fp in sx.children(board, 'footprint')}
    symbols = {ref(symbol): symbol for symbol in sx.children(schematic, 'symbol')}
    assert set(footprints) == set(symbols) == {'J1', 'J2', 'J3', 'J4', 'J5', 'J6'}
    for name, side in (('J1', 'F'), ('J2', 'B')):
        fp = footprints[name]
        footprint_id = 'owned_default_floor_smd_' + side.lower()
        fp[1] = json.dumps(footprint_id)
        sx.one(fp, 'layer')[1] = json.dumps(side + '.Cu')
        sx.one(fp, 'attr')[:] = ['attr', 'smd']
        for prop in props(fp).values():
            layer = sx.one(prop, 'layer')
            assert layer is not None and sx.unquote(layer[1]).startswith('F.')
            layer[1] = json.dumps(side + '.' + sx.unquote(layer[1])[2:])
            if side == 'B':
                effects = sx.one(prop, 'effects')
                assert sx.one(effects, 'justify') is None
                effects.append(['justify', 'mirror'])
        for item in sx.children(fp, 'fp_rect'):
            sx.one(item, 'layer')[1] = json.dumps(side + '.CrtYd')
        pad = sx.children(fp, 'pad')
        assert len(pad) == 1 and pad[0][2:4] == ['thru_hole', 'circle']
        pad = pad[0]; pad[2:4] = ['smd', 'rect']
        pad.remove(sx.one(pad, 'drill'))
        sx.one(pad, 'layers')[:] = ['layers', *[json.dumps(side + '.' + ending) for ending in ('Cu', 'Paste', 'Mask')]]
        props(fp)['Value'][2] = json.dumps(footprint_id)
        props(symbols[name])['Value'][2] = json.dumps(footprint_id)
        props(symbols[name])['Footprint'][2] = json.dumps(footprint_id)
    if label == '4Cu':
        table = sx.one(board, 'layers')
        assert table[1:3] == [['0', '"F.Cu"', 'signal'], ['2', '"B.Cu"', 'signal']]
        table[1:3] = [[str(number), json.dumps(name), 'signal']
                      for number, name in zip(nc.FOUR_COPPER_IDS, nc.FOUR_COPPER_NAMES)]
        assert nc.four_copper_source_layers(board) == list(nc.FOUR_COPPER_NAMES)
    else:
        from autorouter.layer_policy import _source_layers
        assert _source_layers(board) == [['0', 'F.Cu'], ['2', 'B.Cu']]
    # The existing PTH geometry, KEEP track and GND zone are never edited.
    originals = {ref(fp): fp for fp in sx.children(original, 'footprint')}
    for name in ('J3', 'J4', 'J5', 'J6'):
        assert footprints[name] == originals[name]
    assert p.routes(board) == p.routes(original)
    assert sx.children(board, 'zone') == sx.children(original, 'zone')
    protected = [node for node in p.routes(board) if p.locked(node)]
    assert len(protected) == len(p.routes(board)) == 1
    assert protected[0][0] == 'segment' and sx.one(protected[0], 'width') == ['width', '0.3']
    assert sx.one(protected[0], 'net') == ['net', '"KEEP"']
    # Pin/ref/path/field identity stays paired. These are pure source checks,
    # not a fabricated Native netlist or proof of native schematic parity.
    for name, fp in footprints.items():
        symbol = symbols[name]
        assert sx.one(fp, 'path') == ['path', json.dumps('/' + sx.unquote(sx.one(symbol, 'uuid')[1]))]
        for key in ('Reference', 'Value', 'Description', factory.FIELD):
            assert props(fp)[key][2] == props(symbol)[key][2]
        assert fp[1] == props(symbol)['Footprint'][2]
        assert len(sx.children(symbol, 'pin')) == 1 and sx.children(symbol, 'pin')[0][1] == '"1"'
    route_pads = [pad for fp in footprints.values() for pad in sx.children(fp, 'pad')
                  if sx.one(pad, 'net') == ['net', '"ROUTE"']]
    assert len(route_pads) == 2
    assert [sx.one(pad, 'layers') for pad in route_pads] == [
        ['layers', '"F.Cu"', '"F.Paste"', '"F.Mask"'],
        ['layers', '"B.Cu"', '"B.Paste"', '"B.Mask"']]
    assert all(sx.one(pad, 'drill') is None and pad[2:4] == ['smd', 'rect'] for pad in route_pads)
    project = json.loads(base[factory.STEM + '.kicad_pro'])
    before_project = copy.deepcopy(project)
    project['meta']['filename'] = stem + '.kicad_pro'
    project['net_settings']['classes'][0].update(RAW_CLASS)
    project['board']['design_settings']['rules'].update(HARD)
    assert project['board']['design_settings']['rule_severities'] == before_project['board']['design_settings']['rule_severities']
    assert project['board']['design_settings']['drc_exclusions'] == []
    assert set(project['net_settings']['classes'][0]) == set(before_project['net_settings']['classes'][0])
    prl = json.loads(base[factory.STEM + '.kicad_prl']); prl['meta']['filename'] = stem + '.kicad_prl'
    material = {stem + '.kicad_pcb': (sx.dump(board) + '\n').encode(),
                stem + '.kicad_sch': (sx.dump(schematic) + '\n').encode(),
                stem + '.kicad_pro': (json.dumps(project, indent=2, sort_keys=True) + '\n').encode(),
                stem + '.kicad_prl': (json.dumps(prl, indent=2, sort_keys=True) + '\n').encode()}
    return material, stem, source_id, protected[0]


def main():
    assert sha(FACTORY.read_bytes()) == FACTORY_SHA and sha(LICENSE.read_bytes()) == LICENSE_SHA
    assert OUTPUT.parent.resolve() == OUTPUT.parent
    resumed_empty = OUTPUT.exists()
    if resumed_empty:
        # Preparation001 failed its pure layer-return assertion before creating
        # any project. Preserve that log/source; reuse only its still-empty root.
        assert OUTPUT.is_dir() and not OUTPUT.is_symlink() and not list(OUTPUT.iterdir())
        failure = ROOT / '.runs/default-floor-owned-fixture-prepare-001-time.log'
        assert 'assert _source_layers(board)' in failure.read_text() and 'AssertionError' in failure.read_text()
    spec = importlib.util.spec_from_file_location('owned_transport_factory', FACTORY)
    factory = importlib.util.module_from_spec(spec); spec.loader.exec_module(factory)
    if not resumed_empty: OUTPUT.mkdir()
    cases = []
    for label in ('2Cu', '4Cu'):
        material, stem, source_id, track = make(factory, label)
        folder = OUTPUT / ('source-' + label); folder.mkdir()
        for name, raw in material.items():
            with (folder / name).open('xb') as stream: stream.write(raw)
        # Normal source preflight only; neither imports pcbnew nor runs a worker.
        p.preflight(folder / (stem + '.kicad_pcb'),
                    task_scope=('whole_board_unlocked_routing', 'native', 'source_all'))
        actual = {name: sha((folder / name).read_bytes()) for name in material}
        assert actual == {name: sha(raw) for name, raw in material.items()}
        cases.append({'label': label, 'source': str(folder / (stem + '.kicad_pcb')),
                      'source_id': source_id, 'source_hashes': actual,
                      'source_files': 4, 'protected_count': 1,
                      'protected_record': track,
                      'protected_record_sha256': sha((sx.dump(track) + '\n').encode()),
                      'pure_preflight': 'passed; no Native/API or electrical claim',
                      'prospective_scope': 'normal selected10.0.7 source_all whole or partial; original locked KEEP retained',
                      'expected_new_route': 'Connecting only ROUTE front-SMD J1 to back-SMD J2 requires a layer transition; no ROUTE PTH/source via exists. Blind/microvias forbidden. Actual through-via and acceptance must be observed, not assumed.'})
    receipt = {'schema': 1, 'kind': 'owned-Default-floor-required-via-fixture-preparation',
               'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'generator_sha256': sha(Path(__file__).read_bytes()),
               'base_factory': {'path': str(FACTORY.relative_to(ROOT)), 'sha256': FACTORY_SHA,
                                'grant': 'GPL-3.0-or-later factory and generated designs',
                                'license': str(LICENSE.relative_to(ROOT)), 'license_sha256': LICENSE_SHA},
               'raw_Default_mm': RAW_CLASS, 'original_global_floors_mm': HARD,
               'prospective_derived_targets_nm': {'width_nm': 300000, 'clearance_nm': 200000,
                                                   'via_diameter_nm': 900000, 'via_drill_nm': 400000},
               'cases': cases, 'Native_execution': False, 'routing_accepted': False,
               'production_qualified': False, 'benchmark_or_independent_family': False,
               'history_untouched': True,
               'preparation001': 'Pure layer helper returned ID/name pairs, not only names; assertion failed before source creation. Original generator/log retained; only still-empty owned root reused, no project overwritten.' if resumed_empty else 'No prior output existed.',
               'scope': 'Owned prospective Native qualification controls for demonstrated dimension/import/protection failure class only. PCB/SCH variants are paired at creation; other PTHs, source KEEP geometry and GND zone retained modulo new per-case UUID namespace. Original rules/severities retained except explicitly authored class/five floors.',
               'remaining': ['Lead full factory/source review', 'Actual Native source export/map/full schematic observation',
                             'Actual routing/import/refill/final validation, original/protected comparison and cancellation controls'],
               'warnings': 'Source and candidates may produce warnings, incompletion or failure. No expected Native count or success is asserted.',
               'cost': 'Preparation exit measured separately in raw time log; interactive authoring CPU unmetered, notzero.'}
    with (OUTPUT / 'construction.json').open('x') as stream:
        json.dump(receipt, stream, indent=2); stream.write('\n')
    assert sha(FACTORY.read_bytes()) == FACTORY_SHA
    print(json.dumps({'output': str(OUTPUT), 'construction_sha256': sha((OUTPUT / 'construction.json').read_bytes()),
                      'cases': [{'label': item['label'], 'source': item['source'], 'files': 4} for item in cases],
                      'Native_execution': False}))


if __name__ == '__main__':
    main()
