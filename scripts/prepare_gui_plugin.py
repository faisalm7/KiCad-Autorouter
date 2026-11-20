#!/usr/bin/env python3
"""Prepare a project-scoped current KiCad exec-plugin; never install globally."""
from pathlib import Path
import argparse,json,os,shlex,stat,struct,sys,zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter import config as c
from autorouter.local_settings import canonical


def toolbar_board(socket_url, token):
    """Read only the PCB identity from the KiCad instance that ran this action."""
    # Never discover a default server or accept a TCP endpoint. The official
    # client requires the ipc:// prefix even when KiCad supplied a bare path.
    socket_path = Path(socket_url.removeprefix('ipc://'))
    if not token or not socket_path.is_absolute():
        raise ValueError('No local KiCad toolbar connection.')
    info = socket_path.lstat()
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('Expected the current user’s KiCad socket.')
    from kipy import KiCad
    from kipy.proto.common.types import DocumentType
    from autorouter.gui import saved_project_board

    editor = KiCad(socket_path='ipc://' + str(socket_path), kicad_token=token, timeout_ms=1500)
    documents = editor.get_open_documents(DocumentType.DOCTYPE_PCB)
    if len(documents) != 1 or documents[0].type != DocumentType.DOCTYPE_PCB:
        raise ValueError('Expected one PCB from the invoking KiCad editor.')
    document = documents[0]
    folder = Path(document.project.path)
    filename = Path(document.board_filename)
    if (not folder.is_absolute() or not filename.name or filename.suffix != '.kicad_pcb'
            or (not filename.is_absolute() and filename != Path(filename.name))
            or document.project.name != filename.stem):
        raise ValueError('The KiCad board and project identities differ.')
    board = saved_project_board(folder / filename)
    if board.parent != canonical(folder):
        raise ValueError('The PCB is outside the invoking KiCad project.')
    return board


def launch_toolbar(checked_launcher=None):
    from autorouter.gui import child_environment
    socket = os.environ.pop('KICAD_API_SOCKET', '')
    token = os.environ.pop('KICAD_API_TOKEN', '')
    argv = [str(c.PYTHON), '-B', '-m', 'autorouter.gui']
    try:
        board = toolbar_board(socket, token)
    except Exception:
        # Do not display IPC diagnostics that might include the endpoint or
        # any session token. The blank picker grants no source authority.
        argv += ['--toolbar-unavailable']
    else:
        if checked_launcher is not None:
            from autorouter import live_move
            try:
                session, lease = live_move.start(checked_launcher, board, (socket, token))
            except Exception:
                # An unsupported live start retains the existing saved-project handoff.
                pass
            else:
                with lease:
                    live_move.workspace(session)
                return
        argv += ['--toolbar-project', str(board.with_suffix('.kicad_pro'))]
    os.chdir(c.ROOT)
    os.execve(c.PYTHON, argv, child_environment())


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

def prepare(documents, *, checked_launcher=None):
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
    script = ('#!/bin/sh\nset -eu\nunset PYTHONPATH PYTHONHOME\nexport PYTHONNOUSERSITE=1\ncd '
              + shlex.quote(str(c.ROOT)) + '\nexec ' + shlex.quote(str(c.ROOT / '.venv/bin/python'))
              + ' -B ' + shlex.quote(str(c.ROOT / 'scripts/prepare_gui_plugin.py')) + ' --from-toolbar'
              + (' --checked-launcher ' + shlex.quote(str(checked_launcher)) if checked_launcher is not None else '')
              + '\n')
    for size in (24,48):(plugin/('route'+str(size)+'.png')).write_bytes(icon_png(size))
    (plugin/'plugin.json').write_text(json.dumps(manifest,indent=2)+'\n')
    launcher=plugin/'launch-autorouter';launcher.write_text(script);launcher.chmod(0o700)
    return dict(documents_home=str(documents),plugin=str(plugin),installed_globally=False,
                instructions='Launch an isolated KiCad session with KICAD_DOCUMENTS_HOME set to this documents_home. Enable the API only in that disposable session if needed. Use the PCB editor plugin action, then save and close the source editors before routing. No live board snapshot/application/undo is offered.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--documents'); mode.add_argument('--from-toolbar', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--checked-launcher', help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.from_toolbar: launch_toolbar(args.checked_launcher)
    else: print(json.dumps(prepare(args.documents),indent=2))
if __name__=='__main__':main()
