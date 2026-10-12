import sys
from pathlib import Path
here=Path(__file__).resolve().parent
exec((here/'probe.py').read_text().split('cases=')[0])

def routing_positive():
 value,expected=fixture.synthetic();value['cancel_before_routing']=False;value['routing'].update(stop_requested=False,wall_seconds=0.2,board_object_replaced=False)
 old=fixture.retained['case'];route=copy.deepcopy(old['route_geometry_after_selective']['traces'][0]);rid=route['id']
 item=copy.deepcopy(next(r for r in old['state_after_selective']['items'] if r['id']==rid));item['contacts']=[];route['contacts']=[]
 state=value['final_state'];state['items'].append(item);state['census']['traces']=1;state['census']['items']+=1
 value['final_geometry']={'trace_count':1,'via_count':0,'traces':[route],'vias':[]}
 pred=value['final_predicates'];op=old['predicates_after'];pred['tree_entries'].append(copy.deepcopy(next(r for r in op['tree_entries'] if r['id']==rid)))
 pred['indexed_items']+=1;pred['route_count']=1;pred['item_count']+=1
 for a in pred['areas']:
  a['routes']=[copy.deepcopy(next(r for r in next(x for x in op['areas'] if x['id']==a['id'])['routes'] if r['id']==rid))]
 query=copy.deepcopy(next(r for r in op['trace_queries'] if r['id']==rid));ids={r['id'] for r in state['items']}
 for key in ('raw_overlap_ids','flag_filtered_overlap_ids'):query[key]=[i for i in query[key] if i in ids]
 pred['trace_queries']=[query];pred['trace_shape_count']=query['shape_count']
 value['writer']={'state_after_ses':copy.deepcopy(state),'route_geometry_after_ses':copy.deepcopy(value['final_geometry'])}
 return value,expected

def layer_negative(v):
 r=v['final_geometry']['traces'][0];i=next(x for x in v['final_state']['items'] if x['id']==r['id'])
 r.update(layer_index=-1,first_layer=-1,last_layer=-1,layer='bottom_layer');i.update(first_layer=-1,last_layer=-1)
 for a in v['final_predicates']['areas']:a['routes'][0]['shares_layer']=False

def wrong_class(v):
 r=v['final_geometry']['traces'][0];r['clearance_class_index']=0
 next(x for x in v['final_state']['items'] if x['id']==r['id'])['clearance_class_index']=0

rows=[]
for name,change in [('synthetic_generated_positive',lambda v:None),('negative_layer_index',layer_negative),('null_route_clearance_class',wrong_class)]:
 v,e=routing_positive();change(v);v['writer']={'state_after_ses':copy.deepcopy(v['final_state']),'route_geometry_after_ses':copy.deepcopy(v['final_geometry'])}
 try:r=c.compare(v,e,fixture.retained);rows.append({'case':name,'accepted':True,'result':r})
 except Exception as ex:rows.append({'case':name,'accepted':False,'error':type(ex).__name__+': '+str(ex)})
Path(sys.argv[1]).write_text(json.dumps({'scope':'Synthetic new trace built from retained actual002 geometry; never routing evidence','source_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest(),'results':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
