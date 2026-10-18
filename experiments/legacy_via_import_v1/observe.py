"""Pinned KiCad observation and separate saved outputs; never alter source.

SPDX-License-Identifier: GPL-3.0-or-later
"""
import hashlib
import json
from pathlib import Path
import sys
import pcbnew

GETTERS = ('GetFrontCoveringMode', 'GetBackCoveringMode',
           'GetFrontPluggingMode', 'GetBackPluggingMode',
           'GetCappingMode', 'GetFillingMode')


def main():
    if pcbnew.GetBuildVersion() != '10.0.0':
        raise ValueError('exact pinned10.0.0 required')
    output = Path(sys.argv[1]);rows = []
    if not 1 <= len(sys.argv[2:]) <= 8:
        raise ValueError('bounded observer population required')
    for index, value in enumerate(sys.argv[2:]):
        path = Path(value)
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        board = pcbnew.LoadBoard(str(path))
        if board is None:
            raise RuntimeError('KiCad could not load owned control: ' + str(path))
        vias = [via for via in board.GetTracks() if isinstance(via, pcbnew.PCB_VIA)]
        saved = output.parent / ('saved-%02d.kicad_pcb' % index)
        if saved.exists():
            raise ValueError('fresh separate saved path required')
        pcbnew.SaveBoard(str(saved), board)
        rows.append({'source': str(path), 'sha256': before, 'source_saved': False,
                     'separate_saved_output': str(saved),
                     'separate_saved_sha256': hashlib.sha256(saved.read_bytes()).hexdigest(),
                     'vias': [{'uuid': str(via.m_Uuid.AsString()),
                               'mode_return_types': {key: type(getattr(via, key)()).__name__ for key in GETTERS}}
                              for via in vias]})
        if hashlib.sha256(path.read_bytes()).hexdigest() != before:
            raise RuntimeError('source changed during observation')
    with output.open('x') as stream:
        json.dump({'native_version': pcbnew.GetBuildVersion(), 'observations': rows}, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
