"""Owned source-level netclass-intent counterexample; no source repair.

SPDX-License-Identifier: GPL-3.0-or-later
Derived from the owned four-copper pour fixture. The generated files carry
the same GPL grant. This is a diagnostic case, not an independent family.
"""
import json
import uuid
from autorouter import sexpr as sx
from experiments.four_copper_pour_support_v1 import fixture as base

STEM=base.STEM
FLAG_UUID=str(uuid.uuid5(uuid.UUID('ae980ad3-089a-4fdf-95b9-46b26bdf194e'),'class-flag'))

def files(with_directive=True):
    result=base.files()
    pro_name=STEM+'.kicad_pro';project=json.loads(result[pro_name])
    project['net_settings']['classes'].append(dict(name='CRITICAL',priority=0,
        track_width=.7,clearance=.5,via_diameter=1.4,via_drill=.6,tuning_profile=''))
    result[pro_name]=(json.dumps(project,sort_keys=True,indent=2)+'\n').encode()
    if with_directive:
        name=STEM+'.kicad_sch';tree=sx.parse(result[name].decode())
        tree.append(['netclass_flag','""',['length','2.54'],['shape','round'],
            ['at','38.1','40.64','90'],['effects',['font',['size','1.27','1.27']]],
            ['uuid',json.dumps(FLAG_UUID)],['property','"Netclass"','"CRITICAL"',
                ['at','35.56','39.94','90'],['hide','yes'],['effects',['font',['size','1.27','1.27']]]]])
        result[name]=(sx.dump(tree)+'\n').encode()
    return result
