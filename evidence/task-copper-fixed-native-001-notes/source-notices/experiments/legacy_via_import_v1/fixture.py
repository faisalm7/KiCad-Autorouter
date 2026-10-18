"""Owned legacy/modern manufacturing controls; not validation evidence.

SPDX-License-Identifier: GPL-3.0-or-later
Copyright (C) 2026 KiCad-Autorouter contributors.
The grant covers this factory and generated designs. See COPYING.
Reuses the owned complete-schematic transport factory without external CAD.
"""
from pathlib import Path
import copy
import json
from autorouter import sexpr as sx
from experiments.native_schematic_transport_v1 import fixture as base

FIELDS = (['capping', 'yes'], ['covering', ['front', 'yes'], ['back', 'yes']],
          ['plugging', ['front', 'yes'], ['back', 'yes']],
          ['filling', 'yes'])
CASES = ('legacy-omitted', 'modern-inherited', 'legacy-explicit')


def files(case):
    if case not in CASES:
        raise ValueError('unknown manufacturing control')
    material = base.files()
    name = base.STEM + '.kicad_pcb'
    tree = sx.parse(material[name].decode())
    # Enabled board defaults deliberately distinguish OFF from inheritance.
    sx.one(tree, 'setup').extend(copy.deepcopy(FIELDS))
    via = sx.parse('(via (at 19 16) (size 0.8) (drill 0.4) '
                   '(layers "F.Cu" "B.Cu") (net "KEEP") (locked yes) '
                   '(uuid "a567a8a3-e7c4-5ec0-a699-a6906cab23be"))')
    if case == 'legacy-explicit':
        index = via.index(sx.one(via, 'net'))
        via[index:index] = copy.deepcopy(FIELDS)
    tree.append(via)
    tree.append(sx.parse('(segment (start 12 16) (end 26 16) (width 0.3) '
                         '(layer "B.Cu") (net "KEEP") (locked yes) '
                         '(uuid "60f5bb37-9a30-53c6-91cd-d22c228bb19d"))'))
    if case.startswith('legacy-'):
        sx.one(tree, 'version')[1] = '20241229'
        names = {'"ROUTE"': '1', '"KEEP"': '2', '"GND"': '3'}
        for fp in sx.children(tree, 'footprint'):
            for pad in sx.children(fp, 'pad'):
                node = sx.one(pad, 'net');node.insert(1, names[node[1]])
        for node in sx.children(tree, 'segment') + sx.children(tree, 'via') + sx.children(tree, 'zone'):
            net = sx.one(node, 'net')
            if node[0] == 'zone':node.append(['net_name', net[1]])
            net[1] = names[net[1]]
        index = tree.index(sx.one(tree, 'setup')) + 1
        tree[index:index] = [['net', code, net] for net, code in names.items()]
    material[name] = (sx.dump(tree) + '\n').encode()
    project = json.loads(material[base.STEM + '.kicad_pro'])
    # Native control003 demonstrated that missing schema metadata runs legacy
    # migration and discards these authored class dimensions. Declare the tested
    # schema in new controls; never repair retained input files in place.
    project['net_settings']['meta'] = {'version': 3}
    material[base.STEM + '.kicad_pro'] = (json.dumps(project, indent=2, sort_keys=True) + '\n').encode()
    return material


def write(output, case):
    output = Path(output)
    output.mkdir(exist_ok=False)
    for name, raw in files(case).items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
