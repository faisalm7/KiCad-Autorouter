"""Prospective project-owned4Cu Native-parent class transport; no Native claim.

SPDX-License-Identifier: GPL-3.0-or-later
Derived from native_schematic_transport_v1.fixture, whose GPL grant covers
its generated design files. This derivative factory/design is GPL-3.0-or-later.
See COPYING. New authored source identity/UUID namespace, not an external board.
"""
import json
from pathlib import Path
import re
import uuid
from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as base
SOURCE_ID='owned-four-copper-parent-class-v1'
STEM='owned-four-copper-class'
NS=uuid.UUID('41df6e55-919d-4bef-884d-89c5a0771330')
FOOTPRINT='owned_four_copper_terminal'
LIB_ID='OwnedFourCopper:Terminal'
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


def authored(raw):
    text=raw.decode().replace(base.SOURCE_ID,SOURCE_ID).replace(base.STEM,STEM).replace(base.FOOTPRINT,FOOTPRINT).replace(base.LIB_ID,LIB_ID)
    return UUID.sub(lambda match:str(uuid.uuid5(NS,match.group())),text).encode()


def files():
    """Fresh4-file source; no zone/DRU, no external acquisition or old-board edit."""
    result={name.replace(base.STEM,STEM):authored(raw) for name,raw in base.files().items()}
    board=sx.parse(result[STEM+'.kicad_pcb'].decode());layers=sx.one(board,'layers')
    layers[1:3]=[['0','"F.Cu"','signal'],['4','"In1.Cu"','signal'],['6','"In2.Cu"','signal'],['2','"B.Cu"','signal']]
    board[:]=[node for node in board if not isinstance(node,list) or not node or node[0]!='zone']
    for fp in sx.children(board,'footprint'):
        ref=next(sx.unquote(row[2]) for row in sx.children(fp,'property') if sx.unquote(row[1])=='Reference')
        if ref not in ('J1','J2'):continue
        back=ref=='J2';face='B' if back else 'F';layer=face+'.Cu'
        sx.one(fp,'layer')[1]=json.dumps(layer);sx.one(fp,'attr')[:]=['attr','smd']
        for prop in sx.children(fp,'property'):
            row=sx.one(prop,'layer');row[1]=json.dumps(sx.unquote(row[1]).replace('F.',face+'.'))
            if back:sx.one(prop,'effects').append(['justify','mirror'])
        sx.one(sx.one(fp,'fp_rect'),'layer')[1]=json.dumps(face+'.CrtYd')
        pad=sx.one(fp,'pad');pad[2]='smd';pad[:]=[row for row in pad if not isinstance(row,list) or not row or row[0]!='drill']
        sx.one(pad,'layers')[:]=['layers',json.dumps(layer),json.dumps(face+'.Paste'),json.dumps(face+'.Mask')]
    pro=json.loads(result[STEM+'.kicad_pro'])
    default=pro['net_settings']['classes'][0];default['priority']=2147483647
    pro['net_settings']['classes']=[default,
        dict(name='POWER',priority=1,track_width=.4,clearance=.25,via_diameter=1.2,via_drill=.5),
        dict(name='SIGNAL',priority=0,track_width=.35,clearance=.2,via_diameter=1.0,via_drill=.4)]
    pro['net_settings']['netclass_patterns']=[dict(pattern='ROU*',netclass='POWER'),dict(pattern='GN*',netclass='SIGNAL')]
    result[STEM+'.kicad_pcb']=(sx.dump(board)+'\n').encode()
    result[STEM+'.kicad_pro']=(json.dumps(pro,sort_keys=True,indent=2)+'\n').encode()
    return result


def write_project(output):
    output=Path(output)
    if (not output.is_absolute() or output.exists() or output.is_symlink() or '..' in output.parts
            or output.parent.resolve()!=output.parent or not output.parent.is_dir()):
        raise ValueError('fresh canonical absolute output with existing parent required')
    payload=files();output.mkdir()
    for name,raw in payload.items():
        with (output/name).open('xb') as stream:stream.write(raw)
