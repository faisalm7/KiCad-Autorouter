"""One pinned Native load for the prospective contact/DSN observation.

SPDX-License-Identifier: GPL-3.0-or-later
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import native, config as c
from experiments.net_tie_contact_v1 import observer


def main():
    import _pcbnew
    if (native.pcbnew.GetBuildVersion() != '10.0.0'
            or Path(sys.executable).resolve() != c.PYTHON.resolve()
            or Path(_pcbnew.__file__).resolve() != c.PCBNEW.resolve()):
        raise RuntimeError('exact production Native/Python binding required')
    source, dsn, output = map(Path, sys.argv[1:])
    before = (native.file_hash(source), native.file_hash(source.with_suffix('.kicad_pro')))
    board = native.pcbnew.LoadBoard(str(source))
    if not board: raise RuntimeError('Native board load failed')
    mapping = native.netclasses(board, str(source), before)
    record = observer.observe_and_export(board, source, dsn, native.pcbnew,
                                         mapping=mapping, before=before)
    record['native_netclasses'] = mapping
    with output.open('x') as stream:
        json.dump(record, stream, indent=2, allow_nan=False); stream.write('\n')


if __name__ == '__main__': main()
