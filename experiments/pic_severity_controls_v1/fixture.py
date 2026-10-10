"""Owned two-net diagnostic scenes; original board/project never overwritten."""
import copy,json,uuid
from decimal import Decimal
from autorouter import sexpr as sx

CASES=('positive','missing_named_profile','missing_default_profile','board_edge_text','footprint_edge_text','pad_front_counterbore')
PROFILE='MissingOwnedProfile'
NS=uuid.UUID('c17c9104-a1df-4461-aea5-3af269e81c2d')
def uid(name):return str(uuid.uuid5(NS,name))
def q(text):return json.dumps(text)
def mm(n):return str(Decimal(n)/1000000)
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)

def prepare(original,project,case):
    if case not in CASES:raise ValueError('unknown fixed case')
    classes=project['net_settings']['classes']
    by_name={row['name']:row for row in classes}
    if len(classes)!=2 or set(by_name)!={'Default','POWER'} or any(row.get('tuning_profile')!='' for row in classes):raise ValueError('fixed original classes differ')
    if project.get('tuning_profiles')!={'meta':{'version':0},'tuning_profiles_impedance_geometric':[]}:raise ValueError('original empty profile definitions differ')
    changed=copy.deepcopy(project);target_class=None
    if case in ('missing_named_profile','missing_default_profile'):
        target_class='POWER' if case=='missing_named_profile' else 'Default'
        next(row for row in changed['net_settings']['classes'] if row['name']==target_class)['tuning_profile']=PROFILE
    # Keep all setup/stackup/layers from the pinned source. Only the new owned
    # geometry is authored; no originals or original exclusions/severities change.
    board=['kicad_pcb',*[copy.deepcopy(sx.one(original,k)) for k in ('version','generator','generator_version','general','paper','layers','setup')]]
    scene={'case':case,'pads':[],'tracks':[],'texts':[], 'target_class':target_class,'profile':PROFILE if target_class else '',
           'board_saved':False,'routing_accepted':False,'schematic_parity_qualified':False}
    for i,(net,x,y) in enumerate((('GND',10,10),('GND',30,10),('SIGNAL_A',10,20),('SIGNAL_A',30,20))):
        ref='P'+str(i+1);fpuid=uid('fp'+str(i));puid=uid('pad'+str(i))
        fp=['footprint',q('OwnedSeverity_'+ref),['layer',q('F.Cu')],['uuid',q(fpuid)],['at',str(x),str(y)],
            ['property',q('Reference'),q(ref),['at','0','-3'],['layer',q('F.Fab')],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],
            ['property',q('Value'),q('OwnedSeverity'),['at','0','3'],['layer',q('F.Fab')],['hide','yes'],['effects',['font',['size','1','1'],['thickness','0.15']]]],['attr','through_hole']]
        pad=['pad',q('1'),'thru_hole','circle',['at','0','0'],['size','3','3'],['drill','0.6'],['layers',q('*.Cu'),q('*.Mask')],['net',q(net)],['uuid',q(puid)]]
        post=case=='pad_front_counterbore' and i==2
        if post:pad.append(['front_post_machining','counterbore',['size','1.2'],['depth','0.2']])
        fp.append(pad)
        scene['pads'].append({'uuid':puid,'footprint_uuid':fpuid,'reference':ref,'number':'1','net':net,'position_nm':[x*1000000,y*1000000],'post_machined':post})
        if i==0:
            layer='Edge.Cuts' if case=='footprint_edge_text' else 'F.Fab'
            fp.append(['fp_text','user',q('Owned footprint text'),['at','0','5'],['layer',q(layer)],['uuid',q(uid('fptext'))],['effects',['font',['size','1','1'],['thickness','0.15']]]])
            scene['texts'].append({'uuid':uid('fptext'),'text':'Owned footprint text','layer':layer,'parent':'footprint'})
        board.append(fp)
    for net,y,width in (('GND',10,'0.8'),('SIGNAL_A',20,'0.5')):
        row={'uuid':uid('track'+net),'net':net,'start_nm':[10000000,y*1000000],'end_nm':[30000000,y*1000000],'width_nm':int(Decimal(width)*1000000),'layer':'F.Cu'}
        scene['tracks'].append(row)
        board.append(['segment',['start','10',str(y)],['end','30',str(y)],['width',width],['layer',q('F.Cu')],['net',q(net)],['uuid',q(row['uuid'])]])
    layer='Edge.Cuts' if case=='board_edge_text' else 'Dwgs.User'
    board.append(['gr_text',q('Owned board text'),['at','20','5'],['layer',q(layer)],['uuid',q(uid('boardtext'))],['effects',['font',['size','1','1'],['thickness','0.15']]]])
    scene['texts'].append({'uuid':uid('boardtext'),'text':'Owned board text','layer':layer,'parent':'board'})
    for i,(a,b) in enumerate((((0,0),(40,0)),((40,0),(40,30)),((40,30),(0,30)),((0,30),(0,0)))):
        board.append(['gr_line',['start',*map(str,a)],['end',*map(str,b)],['stroke',['width','0.05'],['type','default']],['layer',q('Edge.Cuts')],['uuid',q(uid('edge'+str(i)))]])
    return (sx.dump(board)+'\n').encode(),changed,scene

def project_delta(original,changed,case):
    expected=copy.deepcopy(original)
    if case in ('missing_named_profile','missing_default_profile'):
        name='POWER' if case=='missing_named_profile' else 'Default'
        next(row for row in expected['net_settings']['classes'] if row['name']==name)['tuning_profile']=PROFILE
    if expected!=changed:raise ValueError('project changed beyond declared copied profile value')
    return [] if changed==original else [{'path':['net_settings','classes',next(i for i,r in enumerate(original['net_settings']['classes']) if r['name']==name),'tuning_profile'],'before':'','after':PROFILE}]
