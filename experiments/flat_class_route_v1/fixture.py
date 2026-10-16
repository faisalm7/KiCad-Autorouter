"""Owned class-aware routing tasks; no source-design repair.

SPDX-License-Identifier: GPL-3.0-or-later
Generated files carry the same GPL grant. These variants share the exposed
four-copper fixture family and must never count as independent benchmark boards.
Unlike the prior already-routed prerequisite, ROUTE begins open and the ten
locked KEEP segments remain protected. No rule, pad, layer or route is relaxed.
"""
from autorouter import sexpr as sx
from experiments.schematic_class_intent_v1 import fixture as original

STEM = original.STEM


def files(*, clean_fields=False, mismatch=False):
    if type(clean_fields) is not bool or type(mismatch) is not bool:
        raise ValueError('literal fixture choices required')
    packet = original.files()
    if not mismatch:
        name = STEM + '.kicad_sch'; tree = sx.parse(packet[name].decode())
        flag = sx.one(tree, 'netclass_flag')
        sx.one(flag, 'property')[2] = '"POWER"'
        packet[name] = (sx.dump(tree) + '\n').encode()
    if clean_fields:
        name = STEM + '.kicad_pcb'; tree = sx.parse(packet[name].decode())
        for footprint in sx.children(tree, 'footprint'):
            prop = next(row for row in sx.children(footprint, 'property')
                        if sx.unquote(row[1]) == 'Datasheet')
            if sx.unquote(prop[2]) != '~':
                raise ValueError('exact owned placeholder required')
            prop[2] = '""'
        packet[name] = (sx.dump(tree) + '\n').encode()
    return packet
