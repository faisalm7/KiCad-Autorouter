"""Owned unlocked, split submicrometre copper with real routing gaps.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
The project GPL grant covers this factory and its generated design.
"""
import copy
import uuid
from pathlib import Path
from autorouter import pipeline as p, sexpr as sx
from experiments.legacy_via_import_v1 import fixture as base


def write(output,case='submicron'):
    if case not in ('submicron','alias-free-gap'):raise ValueError('unknown owned task-copper control')
    material = base.files('legacy-omitted')
    name = 'owned1007-transport.kicad_pcb'
    tree = sx.parse(material[name].decode())
    for route in p.routes(tree):
        route[:] = [n for n in route if not isinstance(n, list) or not n or n[0] != 'locked']
    track = next(n for n in sx.children(tree, 'segment') if sx.one(n, 'layer') == ['layer', '"F.Cu"'])
    other = copy.deepcopy(track)
    sx.one(track, 'end')[1:] = ['19.000001', '16']
    sx.one(other, 'start')[1:] = ['19.000001', '16']
    sx.one(other, 'uuid')[1] = '"da42fa51-087f-57a7-9092-a58ce1fdc138"'
    tree.append(other)
    if case=='alias-free-gap':
        # Give new board-only composition controls literal field parity. The
        # earlier owned base deliberately exercised '~'/empty equivalence;
        # that narrow qualifier does not cover extra board-only footprints.
        # Retained003 remains refused, with all six warnings visible.
        for fp in sx.children(tree,'footprint'):
            for prop in sx.children(fp,'property'):
                if len(prop)>2 and sx.unquote(prop[1])=='Datasheet':prop[2]='""'
        # KEEP now has a real gap between exact fixed copper endpoints. The
        # second through-hole pad still binds to the unchanged schematic.
        sx.one(other,'start')[1]='21.000001'
        back=next(n for n in sx.children(tree,'segment') if sx.one(n,'layer')==['layer','"B.Cu"'])
        sx.one(back,'end')[1]='19'
        back.append(['locked','yes'])
        via=sx.children(tree,'via')[0]
        # Use the pinned writer's field order in this newly authored control.
        # Earlier001 remains retained: an end-appended free group correctly
        # failed our still-strict non-UUID record comparison after serialization.
        via.insert(via.index(sx.one(via,'net')),['free','yes'])
        for index,uid in enumerate(('6a81484c-cb63-55d4-905f-1ab750f66b74','c1d2dc56-31ac-54df-9b31-a3aeac1195e8')):
            tree.append(sx.parse('(footprint "owned_task_copper_mark" (layer "F.Cu") '
                '(uuid "'+uid+'") (at '+str(10+index*3)+' 28) '
                '(property "Reference" "MARK" (at 0 0) (layer "F.Fab") '
                '(effects (font (size 1 1) (thickness 0.15)))) '
                '(property "Value" "OwnedMark" (at 0 0) (layer "F.Fab") '
                '(effects (font (size 1 1) (thickness 0.15)))) '
                '(attr board_only exclude_from_pos_files exclude_from_bom) '
                '(fp_rect (start -0.5 -0.5) (end 0.5 0.5) '
                '(stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd") '
                '(uuid "'+str(uuid.uuid5(uuid.UUID(uid),'courtyard'))+'")) '
                '(embedded_fonts no))'))
    material[name] = (sx.dump(tree)+'\n').encode()
    output = Path(output); output.mkdir(exist_ok=False)
    for key, value in material.items():
        with (output/key).open('xb') as stream: stream.write(value)
    return output/name
