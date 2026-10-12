"""Pure disposable-DSN graphics adapter proof; no router/native execution."""
import copy,hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import adapter as a,sexpr as sx,pipeline as p
OUT=Path(__file__).parent;RUN=ROOT/'.runs/pic-selective-routing-native-001'
def pin(path):
 raw=path.read_bytes();return {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def main():
 inputs=[RUN/n for n in ('summary.json','routing-native/final-drc.json','cached-native/context.json','cached-native/native.dsn','mixed.dsn','unrouted.dsn','observe-input/pic_programmer.kicad_pcb','observe-input/pic_programmer.kicad_pro')]
 inputs += [ROOT/n for n in ('autorouter/adapter.py','autorouter/floor_context.py','autorouter/floor_route.py','autorouter/board_floor.py','experiments/pic_mixed_transport_probe_v1/transport.py')]
 before={str(x.relative_to(ROOT)):pin(x) for x in inputs}
 report=json.loads((RUN/'routing-native/final-drc.json').read_text());summary=json.loads((RUN/'summary.json').read_text());context=json.loads((RUN/'cached-native/context.json').read_text())
 parsed=p.parse_report(RUN/'routing-native/final-drc.json','pic_programmer.kicad_pcb');assert parsed==summary['native_routing']['final_native']
 original=sx.read(RUN/'observe-input/pic_programmer.kicad_pcb');text={sx.unquote(sx.one(n,'uuid')[1]):n for n in sx.children(original,'gr_text')}
 errors=[v for v in report['violations'] if v['severity']=='error'];assert len(errors)==3
 matches=[]
 for e in errors:
  i=next(i for i in e['items'] if i['uuid'] in text);node=text[i['uuid']];xy=list(map(float,sx.one(node,'at')[1:3]));assert xy==[i['pos']['x'],i['pos']['y']]
  candidates=[index for index,o in enumerate(context['obstacles']) if o['layer']=='top_layer' and o['bbox_mm'][0]<=xy[0]<=o['bbox_mm'][2] and o['bbox_mm'][1]<=xy[1]<=o['bbox_mm'][3]]
  assert len(candidates)==1
  matches.append({'finding':e,'original_text_uuid':i['uuid'],'original_text':sx.unquote(node[1]),'original_layer':sx.unquote(sx.one(node,'layer')[1]),'context_bbox_index':candidates[0],'context_bbox':context['obstacles'][candidates[0]],'identity_scope':'Source UUID/position exact; retained native bounding-box rows have no UUID, association uses unique enclosing native rectangle and original position.'})
 raw=(RUN/'unrouted.dsn').read_bytes();proposal=OUT/'graphics-only-proposal.dsn';proposal.write_bytes(raw)
 transforms=a.adapt_dsn(proposal,'graphics',copy.deepcopy(context['obstacles']))
 old=a._parse_dsn(raw.decode());new=a._parse_dsn(proposal.read_text());old_structure=sx.one(old,'structure');structure=sx.one(new,'structure')
 inserted=[n for n in sx.children(structure,'keepout') if sx.unquote(n[1]).startswith(a._KEEP_OUT_PREFIX)]
 assert len(inserted)==19 and len(transforms)==19
 reverse=copy.deepcopy(new);rs=sx.one(reverse,'structure');rs[:]=[n for n in rs if n not in inserted];assert reverse==old
 assert sx.children(structure,'plane')==sx.children(old_structure,'plane') and len(sx.children(structure,'plane'))==1
 wires=sx.children(sx.one(new,'wiring'),'wire');assert len(wires)==2 and all(sx.one(w,'polygon') and sx.one(w,'type')==['type','protect'] for w in wires)
 assert not sx.children(sx.one(new,'wiring'),'via')
 census={}
 for name in ('cached-native/native.dsn','mixed.dsn','unrouted.dsn'):
  tree=a._parse_dsn((RUN/name).read_text());st=sx.one(tree,'structure');census[name]={'structure_keepouts':len(sx.children(st,'keepout')),'planes':len(sx.children(st,'plane')),'layers':[sx.unquote(x[1]) for x in sx.children(st,'layer')]}
 assert all(pin(ROOT/name)==value for name,value in before.items())
 result={'schema':1,'scope':'Read-only diagnosis and pure graphics-only transform on a disposable DSN; no native or solver result',
 'native_counts':{k:parsed[k] for k in ('opens','blocking','warnings','exclusions')},'missing_connection':report['unconnected_items'],
 'error_matches':matches,'native_graphic_count':len(context['obstacles']),'native_graphic_layers':dict(Counter(o['layer'] for o in context['obstacles'])),
 'dsn_census':census,'proof':{'added_keepouts':19,'reverse_entire_ast_equal':True,'native_original_plane_preserved':True,'two_protected_custom_bodies_preserved':True,'ordinary_routes':0,'rules_network_library_placement_layers_exact':True},
 'transformations':transforms,'proposal':pin(proposal),'inputs':before,'inputs_unchanged':True,'native_executed':False,'solver_executed':False}
 (OUT/'facts.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('native_counts','native_graphic_count','native_graphic_layers','dsn_census','proof','inputs_unchanged')},indent=2))
if __name__=='__main__':main()
