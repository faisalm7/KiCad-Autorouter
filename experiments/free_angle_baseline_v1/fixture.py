"""Owned oblique-terminal Native control, GPL-3.0-or-later.

The grant covers the generator and its generated design files. This is a fresh
exposed synthetic design, derived only from the project's owned primitives.
No external board or inherited rule is repaired or relaxed. See COPYING.
"""
import json
import re
import uuid
from pathlib import Path
from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as base

STEM='owned-free-angle'
SOURCE_ID='owned-free-angle-native-v1'
NS=uuid.UUID('2cf04845-c9bf-4b50-a39d-a3fc39260beb')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


def files():
    def authored(raw):
        text=raw.decode().replace(base.SOURCE_ID,SOURCE_ID).replace(base.STEM,STEM)
        return UUID.sub(lambda m:str(uuid.uuid5(NS,m.group())),text).encode()
    result={name.replace(base.STEM,STEM):authored(raw) for name,raw in base.files().items()}
    tree=sx.parse(result[STEM+'.kicad_pcb'].decode())
    target=[fp for fp in sx.children(tree,'footprint') if any(sx.unquote(p[1])=='Reference' and sx.unquote(p[2])=='J2' for p in sx.children(fp,'property'))]
    assert len(target)==1
    # New creation: ROUTE endpoints(12,10)->(26,13), neither axis nor45deg.
    sx.one(target[0],'at')[1:]=['26','13']
    pro=json.loads(result[STEM+'.kicad_pro'])
    pro['net_settings']['meta']={'version':5}
    for cls in pro['net_settings']['classes']:cls['tuning_profile']=''
    result[STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode()
    result[STEM+'.kicad_pro']=(json.dumps(pro,sort_keys=True,indent=2)+'\n').encode()
    return result


def write_project(output):
    output=Path(output)
    if (not output.is_absolute() or output.exists() or output.is_symlink()
            or output.parent.resolve()!=output.parent or not output.parent.is_dir() or '..' in output.parts):
        raise ValueError('fresh canonical absolute output required')
    material=files();output.mkdir()
    for name,raw in material.items():
        with (output/name).open('xb') as stream:stream.write(raw)
