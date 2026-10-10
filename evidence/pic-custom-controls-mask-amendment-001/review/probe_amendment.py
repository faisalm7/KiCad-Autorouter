"""Read saved actual findings; mutate in memory only. No native execution."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[1]
module_path=Path(sys.argv[1]).resolve();result_path=Path(sys.argv[2]).resolve()
sys.path.insert(0,str(module_path.parent));sys.path.insert(1,str(ROOT))
spec=importlib.util.spec_from_file_location('reviewed_checks',module_path);checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
run=ROOT/'.runs/pic-custom-native-controls-001';summary_path=run/'summary.json';before=hashlib.sha256(summary_path.read_bytes()).hexdigest();summary=json.loads(summary_path.read_text());results=[];bound={}
def derive(raw):
 findings=raw['violations']+raw['unconnected_items']+raw['schematic_parity']
 return {'opens':len(raw['unconnected_items']),'blocking':sum(v['severity']=='error' for v in raw['violations']+raw['schematic_parity']),'warnings':sum(v['severity']=='warning' for v in findings),'exclusions':sum(v['severity']=='exclusion' or v.get('excluded',False) for v in findings),'ignored_checks':raw['ignored_checks'],'findings':findings}
for row in summary['cases']:
 path=run/(row['variant']+'-'+row['case'])/'original-drc.json';saved=path.read_bytes();bound[str(path.relative_to(run))]=hashlib.sha256(saved).hexdigest();actual=json.loads(saved)
 if row['case']!='foreign_intrusion':scenarios=[('unchanged_other_case',True)]
 else:scenarios=[('actual_primary_and_mask',True),('primary_only',True),('clearance_primary_and_mask',True),('mask_only',False),('two_mask_companions',False),('missing_primary_item',False),('missing_mask_item',False),('primary_warning',False),('primary_excluded',False),('wrong_primary_pair',False),('wrong_mask_pair',False),('mask_extra_uuid',False),('mask_duplicate_uuid',False),('primary_duplicate_uuid',False),('excluded_mask',False),('unrelated_error',False),('unrelated_open',False),('unknown_warning',False),('critical_warning',False),('wrong_section_primary',False)]
 for name,want in scenarios:
  raw=copy.deepcopy(actual);primary=next((v for v in raw['violations'] if v['type']=='shorting_items'),None);mask=next((v for v in raw['violations'] if v['type']=='solder_mask_bridge'),None)
  if name=='primary_only':raw['violations'].remove(mask)
  if name=='clearance_primary_and_mask':primary['type']='clearance'
  if name=='mask_only':raw['violations'].remove(primary)
  if name=='two_mask_companions':raw['violations'].append(copy.deepcopy(mask))
  if name=='missing_primary_item':primary['items'].pop()
  if name=='missing_mask_item':mask['items'].pop()
  if name=='primary_warning':primary['severity']='warning'
  if name=='primary_excluded':primary['excluded']=True
  if name=='wrong_primary_pair':primary['items'][0]['uuid']='unrelated'
  if name=='wrong_mask_pair':mask['items'][0]['uuid']='unrelated'
  if name=='mask_extra_uuid':mask['items'].append({'uuid':'unrelated'})
  if name=='mask_duplicate_uuid':mask['items'].append(copy.deepcopy(mask['items'][0]))
  if name=='primary_duplicate_uuid':primary['items'].append(copy.deepcopy(primary['items'][0]))
  if name=='excluded_mask':mask['excluded']=True
  if name=='unrelated_error':raw['violations'].append({'type':'track_width','severity':'error','items':[{'uuid':'unrelated'}]})
  if name=='unrelated_open':raw['unconnected_items'].append({'type':'unconnected_items','severity':'error','items':[{'uuid':'unrelated'}]})
  if name=='unknown_warning':raw['violations'].append({'type':'unknown_provider','severity':'warning','items':[]})
  if name=='critical_warning':raw['violations'].append({'type':'padstack_invalid','severity':'warning','items':[]})
  if name=='wrong_section_primary':raw['violations'].remove(primary);raw['unconnected_items'].append(primary)
  native=derive(raw);snapshot=copy.deepcopy((native,raw,row['scene']));error=None
  try:got,hits=checks.predicate(row['case'],native,raw,row['scene'],summary['original_observed_effective_ignored_checks'])
  except Exception as exc:got=False;hits=[];error=type(exc).__name__+': '+str(exc)
  unchanged=snapshot==(native,raw,row['scene'])
  results.append({'variant':row['variant'],'case':row['case'],'mutation':name,'expected':want,'got':got,'matched_findings':len(hits),'error':error,'inputs_unchanged':unchanged,'passed':got is want and unchanged})
assert hashlib.sha256(summary_path.read_bytes()).hexdigest()==before
assert all(hashlib.sha256((run/name).read_bytes()).hexdigest()==sha for name,sha in bound.items())
record={'schema':1,'scope':'Offline exposed-protocol reinterpretation and synthetic mutations of saved actual findings; original failed001 is unchanged; no fresh native qualification.','checks_sha256':hashlib.sha256(module_path.read_bytes()).hexdigest(),'summary_sha256':before,'original_status':summary['status'],'original_controls_passed':summary['controls_passed'],'bound_reports':bound,'cases':results,'all_passed':all(x['passed'] for x in results),'native_executed':False}
result_path.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'cases':len(results),'all_passed':record['all_passed'],'unexpected':[x for x in results if not x['passed']]}))
