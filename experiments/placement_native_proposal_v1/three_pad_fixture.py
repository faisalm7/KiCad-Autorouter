"""Owned three-terminal placement task with a complete saved schematic.

SPDX-License-Identifier: GPL-3.0-or-later
Reuse owned geometry and an unrelated locked trace. No licensed board is edited.
"""
import copy

from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as transport
from . import multipad_fixture as components, ordinary_fixture as ordinary

STEM = 'owned-placement-three-pad'
FOOTPRINT = 'owned_placement_three'
LIB_ID = 'OwnedPlacement:Three'
DESCRIPTION = 'Project-owned three-terminal placement connector'


def files():
    material = {name.replace(ordinary.STEM, STEM): raw.replace(ordinary.STEM.encode(), STEM.encode())
                for name, raw in ordinary.files().items()}
    board_name, sch_name = STEM + '.kicad_pcb', STEM + '.kicad_sch'
    board, schematic = (sx.parse(material[name].decode()) for name in (board_name, sch_name))
    for footprint in sx.children(board, 'footprint'):
        footprint.append(['duplicate_pad_numbers_are_jumpers', 'no'])
        ref = components.reference(footprint)
        if ref not in ('J1', 'J2'):
            continue
        footprint[1] = components.quote(FOOTPRINT)
        components.field(footprint, 'Value', FOOTPRINT)
        components.field(footprint, 'Description', DESCRIPTION)
        for line in sx.children(footprint, 'fp_line'):
            if sx.one(line, 'layer') == ['layer', '"F.CrtYd"']:
                for endpoint in ('start', 'end'):
                    location = sx.one(line, endpoint)
                    location[2] = '-2.05' if location[2].startswith('-') else '2.05'
        pad = copy.deepcopy(sx.children(footprint, 'pad')[0])
        pad[1] = '"3"'
        sx.one(pad, 'at')[1:3] = ['0', '1.5']
        sx.one(pad, 'net')[1] = '"ROUTE_C"'
        sx.one(pad, 'pinfunction')[1] = '"3"'
        sx.one(pad, 'uuid')[1] = components.quote(ordinary.uid('three-pad-' + ref))
        footprint.append(pad)

    library = sx.one(schematic, 'lib_symbols')
    symbol = next(row for row in sx.children(library, 'symbol') if sx.unquote(row[1]) == components.LIB_ID)
    symbol[1] = components.quote(LIB_ID)
    components.field(symbol, 'Value', FOOTPRINT)
    components.field(symbol, 'Footprint', FOOTPRINT)
    components.field(symbol, 'Description', DESCRIPTION)
    body, pins = sx.children(symbol, 'symbol')
    body[1], pins[1] = '"Three_0_1"', '"Three_1_1"'
    pin = copy.deepcopy(sx.children(pins, 'pin')[0])
    sx.one(pin, 'at')[2] = '0'
    sx.one(pin, 'number')[1] = sx.one(pin, 'name')[1] = '"3"'
    pins.append(pin)
    for ref, _, _, _, _, y, pin_x in transport.TERMINALS[:2]:
        instance = next(row for row in sx.children(schematic, 'symbol') if components.reference(row) == ref)
        sx.one(instance, 'lib_id')[1] = components.quote(LIB_ID)
        components.field(instance, 'Value', FOOTPRINT)
        components.field(instance, 'Footprint', FOOTPRINT)
        components.field(instance, 'Description', DESCRIPTION)
        instance.append(['pin', '"3"', ['uuid', components.quote(ordinary.uid('three-pin-' + ref))]])
        label = copy.deepcopy(next(row for row in sx.children(schematic, 'global_label')
                                   if sx.unquote(row[1]) == 'ROUTE_A'))
        label[1] = '"ROUTE_C"'
        sx.one(label, 'at')[1:] = [pin_x, y, '0']
        sx.one(label, 'uuid')[1] = components.quote(ordinary.uid('three-label-' + ref))
        schematic.append(label)
    material[board_name] = (sx.dump(board) + '\n').encode()
    material[sch_name] = (sx.dump(schematic) + '\n').encode()
    return material
