"""Small witnessed-eligibility controls, reusing the existing synthetic fixture. No JVM."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import test_selective as test
T=test.Controls;T.setUpClass();t=T();results=[]
for name in ('positive','zero_trace','nonnull_zero_outline','invalid_indexed','valid_flag_laundered','wrong_counts','before_after_drift'):
 o=t.observation()
 if name!='positive':
  for phase in ('predicates_before','predicates_after'):
   pred=o['case'][phase]
   if name=='zero_trace':next(r for r in pred['tree_entries'] if r['kind'].endswith('PolylineTrace')).update(shape_count=0,tile_shape_count=0,entry_count=None,valid=False)
   elif name=='nonnull_zero_outline':next(r for r in pred['tree_entries'] if r['kind'].endswith('ComponentOutline')).update(entry_count=0)
   elif name=='invalid_indexed':next(r for r in pred['tree_entries'] if r['valid']).update(valid=False)
   elif name=='valid_flag_laundered':pred['all_tree_entries_valid']=True
   elif name=='wrong_counts':pred.update(indexed_items=604,unindexed_zero_shape_outlines=618)
   elif name=='before_after_drift' and phase=='predicates_after':next(r for r in pred['tree_entries'] if r['valid']).update(shape_count=2,entry_count=2)
 try:t.check(o)
 except ValueError as exc:accepted=False;error=str(exc)
 else:accepted=True;error=None
 assert accepted==(name=='positive'),name
 results.append({'case':name,'accepted':accepted,'error':error})
paths=[ROOT/'experiments/pic_mixed_transport_probe_v1'/n for n in ('SelectiveAreaProbe.java','selective.py','test_selective.py')]
report={'passed':True,'scope':'Seven finite synthetic cases; no native/JVM execution','source_files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths},'cases':results}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
