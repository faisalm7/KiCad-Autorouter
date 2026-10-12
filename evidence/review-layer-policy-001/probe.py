"""Small layer-scope falsifiers; no filesystem writes outside this review."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import sexpr as sx
DRAFT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'.runs/layer-policy-draft-001'
OUT=Path(__file__).resolve().parent/(sys.argv[2] if len(sys.argv)>2 else 'original-results.json')
mod=DRAFT/'autorouter/layer_policy.py';spec=importlib.util.spec_from_file_location('review_layer_policy',mod);lp=importlib.util.module_from_spec(spec);spec.loader.exec_module(lp)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
source=(ROOT/'tests/fixtures/board-floor/fixture.kicad_pcb').read_bytes();dsn=(ROOT/'evidence/placement-production-native-001/native.dsn').read_bytes();tree=sx.parse(source.decode());rows=[]
raw=lambda t:(sx.dump(t)+'\n').encode()
seg=lambda:sx.parse('(segment (start 0 0) (end 2 0) (width .2) (layer "F.Cu") (net "SIGNAL_A") (uuid "new"))')
via=lambda:sx.parse('(via (at 2 0) (size .8) (drill .4) (layers "F.Cu" "B.Cu") (net "SIGNAL_A") (uuid "via"))')
for name in ['positive_front','back_new','via_front','spoof_new_locked_back','renamed_technical','interleaved_source','unknown_segment_field','missing_segment_width','custom_via_padstack']:
 original=copy.deepcopy(tree);candidate=copy.deepcopy(tree);names=['F.Cu'];scope='whole_board_unlocked_routing'
 if name=='interleaved_source':
  layers=sx.one(original,'layers');layers[2:4]=[layers[3],layers[2]];candidate=copy.deepcopy(original)
 elif name=='renamed_technical':
  layers=sx.one(original,'layers');layers[3][1]='"In1.Cu"';candidate=copy.deepcopy(original)
 else:
  route=via() if name in ('via_front','custom_via_padstack') else seg()
  if name in ('back_new','spoof_new_locked_back'):sx.one(route,'layer')[1]='"B.Cu"'
  if name=='spoof_new_locked_back':route.append(['locked','yes'])
  if name=='unknown_segment_field':route.append(['future_route_layer','"B.Cu"'])
  if name=='missing_segment_width':route.remove(sx.one(route,'width'))
  if name=='custom_via_padstack':
   names=['F.Cu','B.Cu'];route.append(['padstack',['mode','custom'],['layer','"B.Cu"',['size','.6']]])
  candidate.append(route)
 kw=dict(scope=scope,engine_profile='completion-only',guidance_policy='native')
 try:
  binding=lp.bind(raw(original),dsn,dsn,names,**kw);result=lp.audit_candidate(raw(original),raw(candidate),dsn,dsn,binding,allowed_names=names,**kw)
  ok=True;error=None
 except Exception as exc:ok=False;error=type(exc).__name__+': '+str(exc);result=None
 rows.append({'case':name,'layer_scope_passed':ok,'error':error,'acceptance_flags':None if result is None else {k:result[k] for k in ('routing_accepted','native_validation_performed')}})
OUT.write_text(json.dumps({'source_sha256':sha(mod),'scope':'Pure helper only; malformed full geometry is not a demonstrated native acceptance bypass.','cases':rows},indent=2)+'\n')
print(json.dumps(rows))
