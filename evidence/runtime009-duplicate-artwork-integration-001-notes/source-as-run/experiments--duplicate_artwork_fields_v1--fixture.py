"""Owned duplicate-artwork field-census controls; not Native qualification.

SPDX-License-Identifier: GPL-3.0-or-later
This grant covers this factory and its generated artwork. Ordinary design
bytes come unchanged from the GPL native_schematic_toolchain_v1 factory.
That base was authored for1007; fresh production1000 qualification is pending.
No pcbnew, external libraries or third-party CAD are loaded by this factory.
"""
import hashlib
import json
from pathlib import Path
import uuid

from experiments.native_schematic_toolchain_v1 import fixture as base

STEM = base.STEM
MASKED_CASE = base.MASKED_CASE
CASES = ('positive', MASKED_CASE)
ART_NAMESPACE = uuid.UUID('a8ee20d1-87b8-45b5-95a0-21f1d2cc4af2')


def _uid(label):
    return str(uuid.uuid5(ART_NAMESPACE, label))


ART_UUIDS = tuple(_uid('artwork-' + str(index)) for index in range(2))


def source_factory_hashes():
    """Let a prospective controller freeze both authoring sources explicitly."""
    return {
        'experiments/native_schematic_toolchain_v1/fixture.py':
            hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),
        'experiments/duplicate_artwork_fields_v1/fixture.py':
            hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def _property(index, name, value, layer):
    return ('(property ' + json.dumps(name) + ' ' + json.dumps(value) +
            ' (at 0 0 0) (layer ' + json.dumps(layer) + ') (hide yes)'
            ' (uuid ' + json.dumps(_uid('art-' + str(index) + '-' + name)) +
            ') (effects (font (size 0.5 0.5) (thickness 0.1))))')


def artwork_bytes():
    """Two fixed padless footprints; only explicit Silk/Fab surfaces exist."""
    rows = []
    for index, (x, y) in enumerate((('7', '7'), ('23', '19'))):
        rows.append('(footprint "OwnedDuplicateArtwork" (layer "F.Cu")'
                    ' (uuid ' + json.dumps(ART_UUIDS[index]) + ')'
                    ' (at ' + x + ' ' + y + ')'
                    ' (attr board_only exclude_from_pos_files exclude_from_bom)')
        for name, value, layer in (
                ('Reference', 'G***', 'F.SilkS'),
                ('Value', 'OWNED_ARTWORK', 'F.Fab'),
                ('Datasheet', '', 'F.Fab'),
                ('Description', '', 'F.Fab')):
            rows.append(_property(index, name, value, layer))
        graphic_uuid = json.dumps(_uid('art-' + str(index) + '-graphic'))
        if index == 0:
            rows.append('(fp_poly (pts (xy -0.25 -0.25) (xy 0.25 -0.25)'
                        ' (xy 0.25 0.25) (xy -0.25 0.25))'
                        ' (stroke (width 0) (type solid)) (fill yes)'
                        ' (layer "F.SilkS") (uuid ' + graphic_uuid + '))')
        else:
            rows.append('(fp_rect (start -0.25 -0.25) (end 0.25 0.25)'
                        ' (stroke (width 0.1) (type solid)) (fill none)'
                        ' (layer "F.SilkS") (uuid ' + graphic_uuid + '))')
        rows.append(')')
    return ('\n'.join(rows) + '\n').encode('ascii')


def files(case):
    """Return the unchanged base packet with identical artwork in both cases.

    The only negative difference remains the base J1 Description value.
    Existing PCB bytes are retained as a prefix up to its closing root bracket;
    no ordinary component, route, zone or field is parsed and reserialized.
    """
    if case not in CASES:
        raise ValueError('unknown duplicate-artwork field-control case')
    positive = base.files('positive')
    result = base.files(case)
    pcb_name = STEM + '.kicad_pcb'
    if (set(result) != set(positive)
            or any(result[name] != positive[name]
                   for name in positive if name != pcb_name)):
        raise ValueError('base SCH/PRO/DRU/PRL must remain byte-identical')
    if case == MASKED_CASE:
        original = base.pcb_property('J1', 'Description', base.DESCRIPTION,
                                     'F.Fab').encode()
        changed = base.pcb_property('J1', 'Description',
                                    base.MASKED_DESCRIPTION, 'F.Fab').encode()
        if (result[pcb_name].count(changed) != 1
                or result[pcb_name].replace(changed, original, 1)
                != positive[pcb_name]):
            raise ValueError('negative must change only base J1 Description')
    board = result[pcb_name]
    if not board.endswith(b')\n'):
        raise ValueError('expected exact base closing root bracket/newline')
    if any(uid.encode('ascii') in board for uid in ART_UUIDS):
        raise ValueError('fresh artwork UUID collides with base source')
    result[pcb_name] = board[:-2] + b'\n' + artwork_bytes() + b')\n'
    return result
