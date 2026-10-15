"""Fresh owned non-strict branch control, GPL-3.0-or-later.

Creation-only variant; never write/repair a prior source or reinterpret results.
Only authored min_track_width changes .25→0; PCB/SCH/PRL bytes stay exact.
The grant of the owned base generator covers these generated design files.
"""
import copy,json
from experiments.free_angle_baseline_v1 import fixture as base
STEM=base.STEM
SOURCE_ID='owned-free-angle-native-v2-nonstrict-fanout-control'


def files():
    result=base.files();old=json.loads(result[STEM+'.kicad_pro']);new=copy.deepcopy(old)
    rules=new['board']['design_settings']['rules']
    if rules['min_track_width']!=.25:raise ValueError('owned base minimum changed')
    default=new['net_settings']['classes']
    if len(default)!=1 or default[0]['name']!='Default' or default[0]['track_width']!=.3 or default[0]['priority']!=2147483647:
        raise ValueError('owned Default targets/priority changed')
    rules['min_track_width']=0
    restored=copy.deepcopy(new);restored['board']['design_settings']['rules']['min_track_width']=.25
    if restored!=old:raise ValueError('variant changed another authored value')
    result[STEM+'.kicad_pro']=(json.dumps(new,sort_keys=True,indent=2)+'\n').encode()
    return result
