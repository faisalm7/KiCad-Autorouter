"""Owned importer inputs authored at creation, never benchmark source repairs.

SPDX-License-Identifier: GPL-3.0-or-later
The grant covers all generated design files. Reuses the owned full-SCH grammar.
"""
import json
import re
import uuid
from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as base

CASES = ('literal300', 'underscore300', 'literal250')
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')
NS = uuid.UUID('865834ce-8a75-4d9b-b2c1-6c5e3d970f53')


def files(case):
    if case not in CASES:
        raise ValueError('fixed owned named-edge case required')
    stem = 'owned-named-edge-' + case
    def authored(raw):
        text = raw.decode().replace(base.STEM, stem).replace(base.SOURCE_ID, stem + '-v1')
        return UUID.sub(lambda match: str(uuid.uuid5(NS, case + ':' + match.group())), text).encode()
    result = {name.replace(base.STEM, stem): authored(raw) for name, raw in base.files().items()}
    name = stem + '.kicad_pcb'; tree = sx.parse(result[name].decode())
    # This is a fresh no-zone parser/importer source packet, not a routed board
    # with a zone removed. No routing/DRC comparison uses these authored inputs.
    tree[:] = [node for node in tree if not isinstance(node, list) or not node or node[0] != 'zone']
    result[name] = (sx.dump(tree) + '\n').encode()
    project = json.loads(result[stem + '.kicad_pro'])
    project['board']['design_settings']['rules']['min_copper_edge_clearance'] = .25 if case == 'literal250' else .3
    named = 'Power_A' if case == 'underscore300' else 'Power'
    project['net_settings'].update(meta={'version': 5}, netclass_assignments=None,
        classes=[dict(name='Default', priority=2147483647, track_width=.3, clearance=.2,
                      via_diameter=.8, via_drill=.4, tuning_profile=''),
                 dict(name=named, priority=0, track_width=.4, clearance=.25,
                      via_diameter=1.2, via_drill=.5, tuning_profile='')],
        netclass_patterns=[dict(pattern='ROUTE', netclass=named)])
    result[stem + '.kicad_pro'] = (json.dumps(project, sort_keys=True, indent=2) + '\n').encode()
    return result
