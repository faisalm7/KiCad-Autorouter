"""Apply the native pane only to the pinned isolated KiCad source checkout."""
import argparse
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
ASSETS = Path(__file__).resolve().parent
UPSTREAM_REVISION = 'e432beac2668303194ba2040274f9e5efe773fc0'
UPSTREAM = {'https://gitlab.com/kicad/code/kicad.git',
            'https://github.com/KiCad/kicad-source-mirror.git'}


def stage(source):
    if (source.resolve() != source or not source.is_relative_to(ROOT / '.tools')
            or not source.name.startswith('kicad-copperpath-')):
        raise ValueError('Use a dedicated .tools/kicad-copperpath-* upstream source checkout.')

    def git(*args):
        return subprocess.run(['git', '-C', str(source), *args], check=True,
                              timeout=15, capture_output=True, text=True).stdout.strip()

    if (git('rev-parse', '--show-toplevel') != str(source)
            or git('rev-parse', 'HEAD') != UPSTREAM_REVISION
            or git('remote', 'get-url', 'origin') not in UPSTREAM
            or git('status', '--porcelain')):
        raise ValueError('The isolated source must be the clean official KiCad 10.0.8 revision.')
    headers = dict(editor_pane='native_pane', pcb_move_review='pcb_move_review',
                   review_gate='review_gate', pcb_capture='pcb_capture')
    destinations = {ASSETS / (name + '.h'): source / 'include/widgets' / ('copperpath_' + mapped + '.h')
                    for name, mapped in headers.items()}
    if any(target.parent.resolve(strict=True) != target.parent or target.exists() or target.is_symlink()
           for target in destinations.values()):
        raise ValueError('A native header target is occupied or redirected.')
    patch = ASSETS / 'kicad-10.0.8-host.patch'
    git('apply', '--check', str(patch))
    for origin, target in destinations.items():
        with target.open('xb') as stream:
            stream.write(origin.read_bytes())
    git('apply', str(patch))
    return git('status', '--short')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    print(stage(args.source.absolute()))
