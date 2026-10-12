"""Direct routing lifecycle checks, reusing the existing representation validators."""
import copy
import json
import math
from autorouter.preferences import _parse as parse_settings
from experiments.pic_mixed_transport_probe_v1 import selective as s, transport, ses_checks

ROUTE_KINDS={'app.freerouting.board.trace.PolylineTrace','app.freerouting.board.model.items.Via'}

def static_state(state, *, renumber=False):
    """Exclude only changing ordinary routes/connectivity; keep all observed constraints."""
    result=copy.deepcopy(state)
    result['items']=[v for v in result['items'] if v['kind'] not in ROUTE_KINDS]
    result['census']['items']=len(result['items'])
    result['census']['traces']=result['census']['vias']=0
    pins={p['id']:[p['reference'],p['number']] for p in result['pins']}
    for section in ('items','pins','areas'):
        for row in result[section]:
            row.pop('contacts')
            if renumber:row.pop('id')
            if renumber and 'foreign_pin_predicates' in row:
                for predicate in row['foreign_pin_predicates']:
                    predicate['pin_identity']=pins[predicate.pop('pin_id')]
                row['foreign_pin_predicates'].sort(key=s.canonical)
        result[section].sort(key=s.canonical)
    for net in result['nets']:
        net.pop('connected_sets')
        if renumber:net.pop('terminal_ids');net.pop('number')
    if renumber:result['nets'].sort(key=lambda row:row['name'])
    return result

def adapter_projection(state, retained, receipt):
    """Remove only verified new rectangles and the one suppressed engine plane.

    The original native zone is preserved separately. Prior ordinary obstacle
    contours were not captured; their original DSN AST and observed metadata
    remain exact, with fresh geometry captured before and after this routing.
    """
    rows=state.get('adapter_obstacles')
    if (not isinstance(rows,list) or len(rows)!=33 or type(state.get('adapter_obstacle_count')) is not int
            or state['adapter_obstacle_count']!=33):raise ValueError('complete adapter obstacle census required')
    identities=s.by_id(rows,'adapter obstacles');items=s.by_id(state['items'],'items')
    kind='app.freerouting.board.model.items.ObstacleArea'
    if set(identities)!={i for i,r in items.items() if r['kind']==kind}:raise ValueError('adapter obstacle item census differs')
    for row in rows:
        if any(row.get(k)!=v for k,v in items[row['id']].items()):raise ValueError('adapter obstacle identity differs')
    changes=receipt['adapter']['transformations']
    rectangles=[r for r in changes if r['kind']=='native_graphic_bbox_keepout']
    if len(rectangles)!=19 or receipt['adapter']['planes_removed']!=1:raise ValueError('finite adapter transform differs')
    matched=set();scale=ses_checks.number(state['board_units_per_um']);origin=state['board_origin_dsn_um']
    for rect in rectangles:
        x0,y0,x1,y1=map(ses_checks.number,rect['rect_um'])
        ring=s.canonical(sorted([[str(x.normalize()),str(y.normalize())] for x,y in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))]))
        matches=[]
        for row in rows:
            if row.get('ring_um') is None or row.get('layer')!=rect['dsn_layer']:continue
            actual=s.canonical(sorted([[str(ses_checks.number(x).normalize()),str(ses_checks.number(y).normalize())] for x,y in row['ring_um']]))
            if actual==ring:matches.append(row)
        if len(matches)!=1 or matches[0]['id'] in matched:raise ValueError('exact adapter rectangle not uniquely imported')
        row=matches[0];matched.add(row['id'])
        allowed_borders={'app.freerouting.geometry.planar.'+name for name in ('IntBox','IntOctagon','Simplex','PolygonShape')}
        layer=state['layers'].index(row['layer'])
        if (row['holes']!=0 or row.get('hole_shapes')!=[] or row.get('ring_unavailable') is not False
                or type(row.get('corner_count')) is not int or row['corner_count']!=4
                or row.get('border_class') not in allowed_borders or len(row['ring_board_integer'])!=4
                or len(row.get('ring_classes',[]))!=4 or any(k!='app.freerouting.geometry.planar.IntPoint' for k in row['ring_classes'])
                or row['nets'] or row['fixed']!='SYSTEM_FIXED' or row['clearance_class_index']!=1
                or any(type(row.get(k)) is not int or row[k]!=layer for k in ('layer_index','first_layer','last_layer'))
                or ses_checks.canonical_ring([[ses_checks.number(x) for x in point] for point in row['ring_um']])!=ses_checks.canonical_ring([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])):
            raise ValueError('adapter rectangle constraints differ')
        for point,um in zip(row['ring_board_integer'],row['ring_um']):
            if (not isinstance(point,list) or len(point)!=2 or any(type(x) is not int for x in point)
                    or [ses_checks.number(x)/scale+ses_checks.number(o) for x,o in zip(point,origin)]!=list(map(ses_checks.number,um))):
                raise ValueError('adapter rectangle exact integer witness differs')
    corrected=copy.deepcopy(state);corrected.pop('adapter_obstacles');corrected.pop('adapter_obstacle_count')
    corrected['items']=[r for r in corrected['items'] if r['id'] not in matched]
    prior=copy.deepcopy(retained)
    planes=[a for a in prior['areas'] if a['nets']==['GND'] and a['fixed']=='SYSTEM_FIXED']
    if len(planes)!=1:raise ValueError('one retained GND plane required')
    pid=planes[0]['id'];prior['areas']=[a for a in prior['areas'] if a['id']!=pid]
    prior['items']=[a for a in prior['items'] if a['id']!=pid];prior['census']['areas']-=1
    ground=[n for n in prior['nets'] if n['name']=='GND']
    if len(ground)!=1 or ground[0]['contains_plane'] is not True:raise ValueError('original engine plane status differs')
    ground[0]['contains_plane']=False
    s.equal(static_state(corrected,renumber=True),static_state(prior,renumber=True),'corrected adapter changed other imported constraints')
    return sorted(matched)


def effective(value):
    if set(value)!={'configuration_json','layers_json','board_specific_costs_applied'} or type(value['board_specific_costs_applied']) is not bool:
        raise ValueError('effective settings witness schema/types differ')
    def decode(raw):
        if type(raw) is not str:raise ValueError('settings JSON string required')
        return parse_settings(raw.encode('utf-8'),65536)
    config=decode(value['configuration_json']);layers=decode(value['layers_json'])
    if (not isinstance(config,dict) or not isinstance(layers,list) or len(layers)!=2
            or any(not isinstance(layer,dict) or layer.get('routable') is not True for layer in layers)):
        raise ValueError('exact two active routing layers required')
    return {'configuration':config,'layers':layers,'board_specific_costs_applied':value['board_specific_costs_applied']}

def compare(observed,expected,retained_selective,*,native_diagnostic=False,adapter_receipt=None):
    if (type(observed.get('schema')) is not int or observed['schema']!=1 or observed.get('mode')!='selective_route_diagnostic'
            or observed.get('status')!='observed' or observed.get('routing_executed') is not True
            or observed.get('ses_executed') is not True or type(observed.get('cancel_before_routing')) is not bool):
        raise ValueError('complete direct pipeline observation required')
    row=observed['case']
    transport.validate_local_rows([row],expected,(False,))
    if adapter_receipt is not None and row.get('plane_suppressed') is not True:raise ValueError('explicit adapter plane mode required')
    s.transition(row,plane_suppressed=adapter_receipt is not None)
    for key in ('route_geometry_before_local','route_geometry','route_geometry_after_selective'):
        if row[key]!={'trace_count':0,'via_count':0,'traces':[],'vias':[]}:
            raise ValueError('ordinary reference route leaked into solver input')
    if adapter_receipt is None:
        s.equal(static_state(row['state_after_selective'],renumber=True),
                static_state(retained_selective['case']['state_after_selective'],renumber=True),
                'stripped import changed nonrouting constraints')
    else:
        adapter_projection(row['state_after_selective'],retained_selective['case']['state_after_selective'],adapter_receipt)
    before=row['state_after_selective'];after=observed['final_state'];geometry=observed['final_geometry']
    s.equal(static_state(before),static_state(after),'routing changed nonrouting constraints')
    loaded=effective(observed['settings_loaded']);enabled=effective(observed['settings_enabled']);final=effective(observed['settings_final'])
    expected_enabled=copy.deepcopy(loaded)
    if expected_enabled['configuration']['autorouter']['enabled'] is not False:raise ValueError('router enabled before explicit transition')
    expected_enabled['configuration']['autorouter']['enabled']=True
    s.equal(enabled,expected_enabled,'enabling router changed other settings')
    s.equal(final,enabled,'pipeline changed frozen routing settings')
    config=enabled['configuration']
    if (config['autorouter']['algorithm']!='freerouting-router' or config['autorouter']['max_passes']!=30
            or config['optimizer']['enabled'] is not False or config['fanout']['enabled'] is not False
            or config['automatic_neckdown'] is not False or config['neck_width_um']!=0
            or config['plane_as_obstacle'] is not False or config['plane_nets']!=[] or type(config['max_threads']) is not int or config['max_threads']!=1
            or type(config['autorouter']['max_passes']) is not int):
        raise ValueError('completion-only settings differ')
    action=observed['routing']
    if (action.get('pipeline_invoked') is not True or action.get('pipeline_returned') is not True
            or action.get('uses_final_job_board') is not True or action.get('cooperative_deadline_seconds')!=60
            or type(action.get('cooperative_deadline_seconds')) is not int
            or type(action.get('wall_seconds')) not in (int,float) or not math.isfinite(action['wall_seconds']) or not 0<=action['wall_seconds']<=90
            or type(action.get('board_object_replaced')) is not bool
            or type(action.get('stop_requested')) is not bool or type(action.get('cooperative_deadline_reached')) is not bool):
        raise ValueError('direct synchronous pipeline lifecycle incomplete')
    if action['cooperative_deadline_reached'] and not action['stop_requested']:raise ValueError('deadline stop witness contradicts stop state')
    if observed['cancel_before_routing']:
        if action['stop_requested'] is not True or geometry['traces'] or geometry['vias']:
            raise ValueError('cancelled pipeline generated ordinary copper')
    nets={net['name']:net for net in after['nets']}
    for route in geometry['traces']+geometry['vias']:
        if len(route['nets'])!=1 or type(route['clearance_class_index']) is not int:raise ValueError('generated route net/class differs')
        net=nets[route['nets'][0]]
        want=net['trace_clearance_class'] if route in geometry['traces'] else net['default_item_classes']['VIA']
        if route['clearance_class_index']!=want:raise ValueError('generated route bypasses original clearance class')
    for trace in geometry['traces']:
        if len(trace['nets'])!=1 or trace['width_um']!=expected['nets'][trace['nets'][0]]['width_um']:
            raise ValueError('generated route width differs from original class')
    writer=observed['writer']
    s.equal(writer['state_after_ses'],after,'SES write changed final board')
    s.equal(writer['route_geometry_after_ses'],geometry,'SES write changed final routing')
    if not native_diagnostic:
        s.route_geometry(geometry,after)
        s.predicates(observed['final_predicates'],after,geometry)
    return {'lifecycle_verified':True,'ordinary_seed_routes':0,'final_traces':len(geometry['traces']),
            'final_vias':len(geometry['vias']),'geometry_verified':not native_diagnostic,'cancel_control':observed['cancel_before_routing'],
            'routing_accepted':False,'production_support_qualified':False}
