"""Independent pure predicates and real-file publication boundaries; no native."""
import hashlib,json,sys
from pathlib import Path
from unittest import mock
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'snapshot-final'));sys.path.insert(1,str(BASE.parents[1]))
import checks,driver as d
scene={'pads':[{'id':'CONCAVE','uuid':'concave'},{'id':'CONVEX','uuid':'convex'}], 'tracks':[{'id':'CONTACT_TRACK','uuid':'contact'},{'id':'FOREIGN_TRACK','uuid':'foreign'}]}
rows=[]
for case in ('positive','false_hull','foreign_intrusion'):
 for warning in (None,'lib_footprint_issues','unknown_provider','missing_tuning_profile','padstack_invalid'):
  raw={'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[]}
  if case=='false_hull':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[{'uuid':'concave'},{'uuid':'contact'}]}]
  if case=='foreign_intrusion':raw['violations']=[{'type':'clearance','severity':'error','items':[{'uuid':'concave'},{'uuid':'foreign'}]}]
  if warning:raw['violations'].append({'type':warning,'severity':'warning','items':[]})
  findings=raw['violations']+raw['unconnected_items'];native={'opens':len(raw['unconnected_items']),'blocking':sum(v['severity']=='error' for v in raw['violations']),'warnings':sum(v['severity']=='warning' for v in findings),'exclusions':0,'ignored_checks':[],'findings':findings}
  got=checks.predicate(case,native,raw,scene,[])[0];want=warning in (None,'lib_footprint_issues')
  rows.append({'case':case,'warning':warning,'predicate':got,'expected':want,'passed':got is want})
publication=[]
for case in ('unchanged','canonical_late','returned_late','expired_late','cancelled_late','correction_failed'):
 out=BASE/'publication'/case;out.mkdir(parents=True,exist_ok=False)
 record={'status':'controls_passed','controls_passed':True,**d.FALSE_CLAIMS};state={'injected':False,'left':1};real_size=d.size;real_save=d.p.save_json
 def size(path):
  if case!='unchanged' and not state['injected']:
   state['injected']=True
   if case=='canonical_late':value=d.read(out/'summary.json');value['controls_passed']=False;real_save(out/'summary.json',value)
   elif case=='returned_late':record['geometry_qualified']=True
   elif case=='expired_late':state['left']=0
   else:raise KeyboardInterrupt
  return real_size(path)
 def save(path,value):
  if case=='correction_failed' and state['injected']:raise OSError('simulated corrective publication failure')
  return real_save(path,value)
 with mock.patch.object(d,'size',side_effect=size),mock.patch.object(d.p,'save_json',side_effect=save):
  returned=d.publish(out,record,lambda:None,lambda:None,lambda:state['left'])
 canonical=d.read(out/'summary.json') if (out/'summary.json').exists() else None
 okay=returned['controls_passed'] is (case=='unchanged') and (canonical is None if case=='correction_failed' else canonical==returned) and returned['geometry_qualified'] is False
 publication.append({'case':case,'passed':okay,'returned':returned,'canonical':canonical,'injected':state['injected'],'archived':len(list(out.glob('invalidated-*')))})
result={'schema':1,'scope':'Independent synthetic finding predicates and actual tiny output files at mocked final publication boundaries; no native/engine/GUI process.','source_hashes':{n:hashlib.sha256((BASE/'snapshot-final'/n).read_bytes()).hexdigest() for n in ('driver.py','checks.py')},'predicate_cases':rows,'publication_cases':publication,'all_passed':all(r['passed'] for r in rows+publication)}
(BASE/'final-probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'predicate_cases':len(rows),'publication_cases':len(publication),'all_passed':result['all_passed']}))
if not result['all_passed']:raise SystemExit(1)
