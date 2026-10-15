"""Prospective owned4Cu source with ordinary protected outer copper curtains.

SPDX-License-Identifier: GPL-3.0-or-later
Derivative of the owned four_copper_class_transport_v1 fixture; generated design
files have that factory's GPL grant. No rule/keepout/layer-policy relaxation.
AST-reviewed only: source Native validity and routing remain unexecuted.
"""
import json
from pathlib import Path
import uuid
from autorouter import sexpr as sx
from experiments.four_copper_class_transport_v1 import fixture as base

SOURCE_ID='owned-four-copper-forced-inner-v1'
STEM='owned-four-copper-forced-inner'
FOOTPRINT='owned_four_copper_forced_inner_terminal'
LIB_ID='OwnedFourCopperForcedInner:Terminal'
NS=uuid.UUID('96783b68-2622-4695-9b9d-55634ddae913')
EXPECTED_SOURCE_ROUTE_COUNT=10
REQUIRED_NEW_INNER_ROUTE_NETS=('ROUTE','GND')


def authored(raw):
    text=raw.decode().replace(base.SOURCE_ID,SOURCE_ID).replace(base.STEM,STEM).replace(base.FOOTPRINT,FOOTPRINT).replace(base.LIB_ID,LIB_ID)
    return base.UUID.sub(lambda match:str(uuid.uuid5(NS,match.group())),text).encode()


def segment(start,end,layer,label):
    return ['segment',['start',*start],['end',*end],['width','0.3'],
            ['layer',json.dumps(layer)],['net','"KEEP"'],['locked','yes'],
            ['uuid',json.dumps(str(uuid.uuid5(NS,label)))]]


def files():
    result={name.replace(base.STEM,STEM):authored(raw) for name,raw in base.files().items()}
    board=sx.parse(result[STEM+'.kicad_pcb'].decode())
    # KEEP already joins the two PTH pads with an authored F.Cu locked segment.
    # This ordinary B.Cu bridge joins the B curtain to those SAME source pads.
    board.append(segment(('12','16'),('26','16'),'B.Cu','back-keep-bridge'))
    corners=(('19','6.5'),('19.4','6.5'),('19.4','29.5'),('19','29.5'))
    for layer in ('F.Cu','B.Cu'):
        for index,start in enumerate(corners):
            board.append(segment(start,corners[(index+1)%4],layer,'curtain:'+layer+':'+str(index)))
    result[STEM+'.kicad_pcb']=(sx.dump(board)+'\n').encode()
    return result


def write_project(output):
    output=Path(output)
    if (not output.is_absolute() or output.exists() or output.is_symlink() or '..' in output.parts
            or output.parent.resolve()!=output.parent or not output.parent.is_dir()):
        raise ValueError('fresh canonical absolute output with existing parent required')
    output.mkdir()
    for name,raw in files().items():
        with (output/name).open('xb') as stream:stream.write(raw)
