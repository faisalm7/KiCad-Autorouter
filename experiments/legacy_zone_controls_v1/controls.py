"""Three fixed owned smoke cases; no general compatibility/admission policy."""
import copy,json
from decimal import Decimal
from autorouter import pipeline as p,sexpr as sx,board_floor as g
CASES=('assigned_gnd','assigned_padless','net_zero')
PADLESS='OWNED_PADLESS'
ZONE_UUID='5a4bb95a-e244-41cb-b650-8e9f3573eb0f'


def derive(board,project,case):
    if case not in CASES:raise p.Rejected('unknown fixed zone case')
    tree=sx.parse(board.decode());zones=sx.children(tree,'zone')
    if len(zones)!=1 or sx.one(zones[0],'uuid')!=['uuid',json.dumps(ZONE_UUID)] or sx.one(zones[0],'net')!=['net','"GND"']:
        raise p.Rejected('base smoke zone differs')
    original=copy.deepcopy(tree);zone=zones[0];net=sx.one(zone,'net');net_index=zone.index(net)
    if case=='assigned_padless':net[1]=json.dumps(PADLESS)
    if case=='net_zero':zone.remove(net)  # KiCad10 writer omits net for netcode0.
    # Only this exact node may differ. Preserve original positive board bytes.
    restored=copy.deepcopy(tree);restored_zone=sx.children(restored,'zone')[0]
    if case=='net_zero':restored_zone.insert(net_index,copy.deepcopy(net))
    elif case=='assigned_padless':sx.one(restored_zone,'net')[1]='"GND"'
    if restored!=original:raise p.Rejected('unexpected fixture geometry edit')
    settings=json.loads(project);before=copy.deepcopy(settings)
    if settings!={'meta':{'filename':'smoke.kicad_pro','version':1}}:raise p.Rejected('base smoke project differs')
    settings['board']={'design_settings':{'rule_severities':{'zone_has_empty_net':'error'}}}
    if {k:v for k,v in settings.items() if k!='board'}!=before:raise p.Rejected('unexpected project delta')
    return (board if case=='assigned_gnd' else (sx.dump(tree)+'\n').encode()),(json.dumps(settings,indent=2)+'\n').encode()


def historical_violation(code,pad_count):
    if type(code) is not int:raise p.Rejected('native net code is not an integer')
    if code>0:
        if type(pad_count) is not int or pad_count<0:raise p.Rejected('native pad count is not nonnegative integer')
    elif pad_count is not None:raise p.Rejected('count must not be requested for nonpositive net')
    return code<0 or (code>0 and pad_count==0)


def evaluate(case,board,context,observation):
    if case not in CASES:raise p.Rejected('unknown fixed zone case')
    if (observation.get('schema')!=1 or type(observation.get('schema')) is not int
            or observation.get('connectivity_build_succeeded') is not True
            or observation.get('footprint_zone_count')!=0 or type(observation.get('footprint_zone_count')) is not int):
        raise p.Rejected('connectivity build/zone scope differs')
    tree=sx.parse(board.decode());expected=g.task_pads(tree)
    positions={}
    for fp in sx.children(tree,'footprint'):
        at=sx.one(fp,'at')
        if len(at)!=3:raise p.Rejected('fixed fixture transform differs')
        for pad in sx.children(fp,'pad'):
            if sx.one(pad,'at')!=['at','0','0']:raise p.Rejected('fixed pad offset differs')
            positions[sx.unquote(sx.one(pad,'uuid')[1])]=[int(Decimal(x)*1000000) for x in at[1:]]
    pads=observation.get('pads')
    if not isinstance(pads,list) or len(pads)!=6 or len({x['uuid'] for x in pads})!=6:raise p.Rejected('native pad census differs')
    if {r['uuid']:{k:r[k] for k in ('reference','number','net','copper_layers')} for r in pads}!=expected:raise p.Rejected('native pad identity differs')
    if {r['uuid']:r['position_nm'] for r in pads}!=positions:raise p.Rejected('native pad positions differ')
    if sorted(pads,key=lambda r:r['uuid'])!=sorted(context['pads'],key=lambda r:r['uuid']):raise p.Rejected('same-load pad contexts differ')
    nets={r['name']:r['netcode'] for r in context['nets']}
    names={'GND','SIGNAL_A','SIGNAL_B'}|({PADLESS} if case=='assigned_padless' else set())
    if set(nets)!=names or len(context['nets'])!=len(names) or len(set(nets.values()))!=len(nets) or any(type(code) is not int or code<=0 for code in nets.values()):raise p.Rejected('native net census differs')
    if context['routes']!=[]:raise p.Rejected('unexpected native routes')
    for pad in pads:
        if type(pad['netcode']) is not int or pad['netcode']!=nets.get(pad['net']):raise p.Rejected('native pad code differs')
    rows=observation.get('zones')
    if not isinstance(rows,list) or len(rows)!=1:raise p.Rejected('native zone census differs')
    zone=rows[0];name={'assigned_gnd':'GND','assigned_padless':PADLESS,'net_zero':''}[case]
    code=nets[name] if name else 0;count={'assigned_gnd':2,'assigned_padless':0,'net_zero':None}[case]
    expected_zone={'uuid':ZONE_UUID,'is_copper':True,'is_rule_area':False,'layers':[{'id':2,'name':'B.Cu'}],
        'netcode':code,'net':name,'pad_count':count,'outline_nm':[[6000000,6000000],[44000000,6000000],[44000000,34000000],[6000000,34000000]],'closed':True,'holes':0,'arc_count':0}
    # Exact canonical comparison keeps bool distinct from numeric values.
    if json.dumps(zone,sort_keys=True)!=json.dumps(expected_zone,sort_keys=True):raise p.Rejected('native zone identity/geometry/count differs')
    violated=historical_violation(code,count)
    if violated!=(case=='assigned_padless'):raise p.Rejected('historical control predicate differs')
    return {'predicate_matched':True,'historical_violation':violated,'historical_guard_accepts':not violated,'zone_uuid':ZONE_UUID,'net':name,'native_netcode':code,'native_pad_count':count,'routing_accepted':False}
