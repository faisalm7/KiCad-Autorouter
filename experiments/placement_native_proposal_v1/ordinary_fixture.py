"""Owned ordinary-format SMD placement task; no third-party CAD is copied.

SPDX-License-Identifier: GPL-3.0-or-later
Authoring a new fixture is not removal of routes from an existing input. The
complete schematic, fixed terminals, locked trace and zone remain explicit.
"""
import json
from pathlib import Path
import re
import uuid

from autorouter import sexpr as sx
from . import multipad_fixture as base

STEM = 'owned-placement-ordinary'
NS = uuid.UUID('79121cfb-c4b7-4f13-969c-a2620aebf366')


def uid(value):
    return str(uuid.uuid5(NS, value))


def remap(raw):
    text = raw.decode().replace(base.STEM, STEM).replace(base.SOURCE_ID, 'owned-ordinary-front-placement-v1')
    return re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                  lambda match: uid(match.group()), text).encode()


def selected():
    return [uid(base.uid(ref + '-footprint')) for ref in ('J1', 'J2')]


def board():
    tree = sx.parse(remap((sx.dump(base.board()) + '\n').encode()).decode())
    for fp in sx.children(tree, 'footprint'):
        ref = base.reference(fp)
        if ref not in ('J1', 'J2', 'J5'):
            continue
        court = sx.one(fp, 'fp_rect'); fp.remove(court)
        if ref in ('J1', 'J2'):
            angle = '90' if ref == 'J1' else '270'
            sx.one(fp, 'at').append(angle)
            sx.one(fp, 'attr')[1:] = ['smd']
            for index, pad in enumerate(sx.children(fp, 'pad')):
                pad[2:4] = ['smd', 'roundrect']
                sx.one(pad, 'at')[1:] = ['-0.825' if index == 0 else '0.825', '0', angle]
                sx.one(pad, 'size')[1:] = ['0.8', '0.95']
                pad.remove(sx.one(pad, 'drill'))
                sx.one(pad, 'layers')[1:] = ['"F.Cu"', '"F.Paste"', '"F.Mask"']
                pad.append(['roundrect_rratio', '0.25'])
            vertices = [('-1.48','-0.73'), ('1.48','-0.73'), ('1.48','0.73'), ('-1.48','0.73')]
        else:
            # Fixed obstacle: non-centred and slightly sloped courtyard. Its
            # conservative envelope must not be snapped or centred on the anchor.
            vertices = [('-1.3','-1.3'), ('1.5','-1.3'), ('1.45','1.3'), ('-1.3','1.3')]
        for index, start in enumerate(vertices):
            end = vertices[(index + 1) % len(vertices)]
            fp.append(['fp_line', ['start', *start], ['end', *end],
                ['stroke', ['width', '0.05'], ['type', 'default']], ['layer', '"F.CrtYd"'],
                ['uuid', json.dumps(uid(ref + '-court-' + str(index)))]])
        fp.append(['fp_line', ['start', '-0.4', '-0.4'], ['end', '0.4', '-0.4'],
            ['stroke', ['width', '0.1'], ['type', 'default']], ['layer', '"F.Fab"'],
            ['uuid', json.dumps(uid(ref + '-fab-line'))]])
    tree.append(['gr_text', '"Owned ordinary geometry task"', ['at', '20', '3', '0'],
        ['layer', '"F.SilkS"'], ['uuid', json.dumps(uid('board-note'))],
        ['effects', ['font', ['size', '0.7', '0.7'], ['thickness', '0.12']]]])
    return tree


def files():
    values = {name.replace(base.STEM, STEM): remap(raw) for name, raw in base.files().items()}
    values[STEM + '.kicad_pcb'] = (sx.dump(board()) + '\n').encode()
    return values


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
