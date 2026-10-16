#!/usr/bin/env python3
"""Prepare a project-scoped current KiCad exec-plugin; never install globally."""
from pathlib import Path
import argparse,json,os,shlex,struct,sys,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter import config as c
from autorouter.local_settings import canonical

def icon_png(size):
    """Project-owned routing glyph; PNG encoded without imaging dependencies."""
    def pixel(x,y):
        x=x*24//size;y=y*24//size
        trace=(4<=x<=17 and 4<=y<=6 or 15<=x<=17 and 4<=y<=13 or
               8<=x<=17 and 11<=y<=13 or 8<=x<=10 and 11<=y<=19 or
               8<=x<=20 and 17<=y<=19)
        pad=any((x-a)**2+(y-b)**2<=5 for a,b in ((4,5),(20,18)))
        return bytes((55,210,140,255)) if trace or pad else bytes((0,0,0,0))
    raw=b''.join(b'\0'+b''.join(pixel(x,y) for x in range(size)) for y in range(size))
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')

def prepare(documents):
    documents=canonical(Path(documents).absolute())
    if documents.exists():raise ValueError('Use a fresh documents directory; existing configuration is never overwritten.')
    if not c.PYTHON.is_file() or not (c.ROOT/'autorouter/gui.py').is_file():
        raise ValueError('Qualified KiCad Python and the graphical controller are required.')
    plugin=documents/'KiCad/10.0/plugins/org.kicad.autorouter.local'
    plugin.mkdir(parents=True,mode=0o700)
    manifest=dict(identifier='org.kicad.autorouter.local',name='Local Autorouter',
        description='Offline routing and review in a separate project; save and close the source editor before routing.',
        runtime=dict(type='exec'),actions=[dict(identifier='route-separate',name='Autorouter: separate project',
            description='Configure, route, cancel and review a separate saved project.',
            entrypoint='launch-autorouter',scopes=['pcb'],**{'show-button':True,'icons-light':['route24.png','route48.png'],'icons-dark':['route24.png','route48.png']})])
    script='#!/bin/sh\nset -eu\nunset KICAD_API_SOCKET KICAD_API_TOKEN\ncd '+shlex.quote(str(c.ROOT))+'\nexec '+shlex.quote(str(c.PYTHON))+' -B -m autorouter.gui\n'
    for size in (24,48):(plugin/('route'+str(size)+'.png')).write_bytes(icon_png(size))
    (plugin/'plugin.json').write_text(json.dumps(manifest,indent=2)+'\n')
    launcher=plugin/'launch-autorouter';launcher.write_text(script);launcher.chmod(0o700)
    return dict(documents_home=str(documents),plugin=str(plugin),installed_globally=False,
                instructions='Launch an isolated KiCad session with KICAD_DOCUMENTS_HOME set to this documents_home. Enable the API only in that disposable session if needed. Use the PCB editor plugin action, then save and close the source editors before routing. No live board snapshot/application/undo is offered.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--documents',required=True)
    args=parser.parse_args()
    print(json.dumps(prepare(args.documents),indent=2))
if __name__=='__main__':main()
