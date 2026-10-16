"""Fresh project-owned positive-global-minimum fixture; GPL-3.0-or-later.

Creation only. No prior source/result is read, repaired or rewritten.
"""
import copy,json,re,uuid
from experiments.fanout_baseline_v1 import clearance_fixture as base
STEM='owned-global-min-width'
SOURCE_ID='owned-global-min-width-v1'
NS=uuid.UUID('eb58511e-84a9-41c0-a116-f732a5758317')
UUID=re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')

def files():
    def authored(raw):
        text=raw.decode().replace(base.SOURCE_ID,SOURCE_ID).replace(base.STEM,STEM)
        return UUID.sub(lambda m:str(uuid.uuid5(NS,m.group())),text).encode()
    result={name.replace(base.STEM,STEM):authored(raw) for name,raw in base.files().items()}
    project=json.loads(result[STEM+'.kicad_pro']);old=copy.deepcopy(project)
    rules=project['board']['design_settings']['rules'];classes=project['net_settings']['classes']
    if rules['min_track_width']!=0 or rules['min_clearance']!=.2:
        raise ValueError('owned base original minima changed')
    if (len(classes)!=1 or classes[0]['name']!='Default' or classes[0]['track_width']!=.3
            or classes[0]['clearance']!=.2 or classes[0]['priority']!=2147483647):
        raise ValueError('owned Default width/clearance/priority changed')
    rules['min_track_width']=.2
    restored=copy.deepcopy(project);restored['board']['design_settings']['rules']['min_track_width']=0
    if restored!=old:raise ValueError('creation changed another project value')
    result[STEM+'.kicad_pro']=(json.dumps(project,sort_keys=True,indent=2)+'\n').encode()
    if set(result)!={STEM+x for x in ('.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_prl')}:
        raise ValueError('complete four-file owned fixture required')
    return result
