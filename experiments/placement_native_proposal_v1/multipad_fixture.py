"""Owned complete-schematic selected-placement task with retained locked copper.

SPDX-License-Identifier: GPL-3.0-or-later
The grant covers this factory and generated designs. Reuses the owned transport
grammar, with a distinct identity and explicit two-pin ROUTE_A/ROUTE_B connectors.
It never reads or changes an existing project or removes authored copper.
"""
import copy
import json
from pathlib import Path
import uuid

from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as base

STEM = 'owned-placement-multipad'
SOURCE_ID = 'owned-selected-multipad-preserved-copper-v1'
LIB_ID = 'OwnedPlacement:Dual'
FOOTPRINT = 'owned_placement_dual'
NS = uuid.UUID('0551126a-e711-4c43-998a-be345d59295b')


def uid(label):
    return str(uuid.uuid5(NS, label))


def quote(value):
    return json.dumps(value)


def remap(value):
    if isinstance(value, list):
        return [remap(v) for v in value]
    text = sx.unquote(value)
    # Also remap hierarchical paths, keeping PCB/schematic identity aligned.
    for ref in ('J1', 'J2', 'J3', 'J4', 'J5', 'J6'):
        for suffix in ('footprint', 'courtyard', 'pad', 'symbol', 'label', 'schematic-pin'):
            text = text.replace(base.uid(ref + '-' + suffix), uid(ref + '-' + suffix))
        for name in ('Reference', 'Value', 'Datasheet', 'Description', base.FIELD):
            key = ref + '-property-' + name
            text = text.replace(base.uid(key), uid(key))
    for key in ('schematic-root', 'edge', 'gnd-zone', 'protected-keep-track'):
        text = text.replace(base.uid(key), uid(key))
    text = text.replace(base.SOURCE_ID, SOURCE_ID).replace(base.STEM, STEM)
    return quote(text) if value.startswith('"') else text


def reference(node):
    return next(sx.unquote(row[2]) for row in sx.children(node, 'property')
                if sx.unquote(row[1]) == 'Reference')


def field(node, name, value):
    row = next(row for row in sx.children(node, 'property') if sx.unquote(row[1]) == name)
    row[2] = quote(value)


def board():
    tree = remap(sx.parse(base.board().decode()))
    for fp in sx.children(tree, 'footprint'):
        ref = reference(fp)
        if ref not in ('J1', 'J2'):
            continue
        fp[1] = quote(FOOTPRINT)
        field(fp, 'Value', FOOTPRINT)
        field(fp, 'Description', 'Project-owned two-pin placement connector')
        court = sx.one(fp, 'fp_rect')
        sx.one(court, 'start')[1:] = ['-2.8', '-1.3']
        sx.one(court, 'end')[1:] = ['2.8', '1.3']
        template = sx.one(fp, 'pad')
        fp.remove(template)
        for index, (offset, net) in enumerate((('-1.27', 'ROUTE_A'), ('1.27', 'ROUTE_B')), 1):
            pad = copy.deepcopy(template)
            pad[1] = quote(str(index))
            sx.one(pad, 'at')[1:] = [offset, '0']
            sx.one(pad, 'net')[1:] = [quote(net)]
            sx.one(pad, 'pinfunction')[1] = quote(str(index))
            sx.one(pad, 'uuid')[1] = quote(uid(ref + '-pad-' + str(index)))
            fp.append(pad)
    return tree


def schematic():
    tree = remap(sx.parse(base.schematic().decode()))
    library = sx.one(tree, 'lib_symbols')
    dual = copy.deepcopy(sx.children(library, 'symbol')[0])
    dual[1] = quote(LIB_ID)
    field(dual, 'Value', FOOTPRINT)
    field(dual, 'Footprint', FOOTPRINT)
    field(dual, 'Description', 'Project-owned two-pin placement connector')
    units = sx.children(dual, 'symbol')
    units[0][1] = quote('Dual_0_1')
    units[1][1] = quote('Dual_1_1')
    template = sx.one(units[1], 'pin')
    units[1].remove(template)
    for index, local_y in ((1, '1.27'), (2, '-1.27')):
        pin = copy.deepcopy(template)
        sx.one(pin, 'at')[1:] = ['-2.54', local_y, '0']
        sx.one(pin, 'name')[1] = sx.one(pin, 'number')[1] = quote(str(index))
        units[1].append(pin)
    library.append(dual)
    for ref, _, _, _, x, y, pin_x in base.TERMINALS[:2]:
        instance = next(row for row in sx.children(tree, 'symbol') if reference(row) == ref)
        sx.one(instance, 'lib_id')[1] = quote(LIB_ID)
        field(instance, 'Value', FOOTPRINT)
        field(instance, 'Footprint', FOOTPRINT)
        field(instance, 'Description', 'Project-owned two-pin placement connector')
        old_pin = sx.one(instance, 'pin')
        instance.remove(old_pin)
        for index in (1, 2):
            instance.append(['pin', quote(str(index)), ['uuid', quote(uid(ref + '-schematic-pin-' + str(index)))]])
        label = next(row for row in sx.children(tree, 'global_label')
                     if sx.unquote(sx.one(row, 'uuid')[1]) == uid(ref + '-label'))
        tree.remove(label)
        # Schematic local +Y is upward; sheet coordinate +Y is downward.
        from decimal import Decimal
        for index, (offset, net) in enumerate((('-1.27', 'ROUTE_A'), ('1.27', 'ROUTE_B')), 1):
            new = copy.deepcopy(label)
            new[1] = quote(net)
            sx.one(new, 'at')[1:] = [pin_x, str(Decimal(y) + Decimal(offset)), '0']
            sx.one(new, 'uuid')[1] = quote(uid(ref + '-label-' + str(index)))
            tree.append(new)
    return tree


def files():
    project = json.loads(base.project())
    project['meta']['filename'] = STEM + '.kicad_pro'
    prl = json.loads(base.files()[base.STEM + '.kicad_prl'])
    prl['meta']['filename'] = STEM + '.kicad_prl'
    return {STEM + '.kicad_pcb': (sx.dump(board()) + '\n').encode(),
            STEM + '.kicad_sch': (sx.dump(schematic()) + '\n').encode(),
            STEM + '.kicad_pro': (json.dumps(project, sort_keys=True, indent=2) + '\n').encode(),
            STEM + '.kicad_prl': (json.dumps(prl, sort_keys=True, indent=2) + '\n').encode()}


def write_project(output):
    output = Path(output)
    if not output.is_absolute() or output.exists() or output.is_symlink() or output.parent.resolve() != output.parent:
        raise ValueError('Fresh canonical project directory required')
    material = files()
    output.mkdir(mode=0o700)
    for name, raw in material.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
    return output / (STEM + '.kicad_pcb')
