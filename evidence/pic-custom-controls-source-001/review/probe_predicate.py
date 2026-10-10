"""Synthetic predicate falsifier only: no native process or geometry proof."""
import copy,hashlib,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'snapshot-subset-001'))
sys.path.insert(1,str(BASE.parents[1]))
import checks
scene={'pads':[{'id':'CONCAVE','uuid':'concave'},{'id':'CONVEX','uuid':'convex'}], 'tracks':[{'id':'CONTACT_TRACK','uuid':'contact'},{'id':'FOREIGN_TRACK','uuid':'foreign'}]}
def run(case,warning):
 raw={'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[]}
 if case=='false_hull':raw['unconnected_items']=[{'type':'unconnected_items','severity':'error','items':[{'uuid':'concave'},{'uuid':'contact'}]}]
 if case=='foreign_intrusion':raw['violations']=[{'type':'clearance','severity':'error','items':[{'uuid':'concave'},{'uuid':'foreign'}]}]
 if warning:raw['violations'].append({'type':warning,'severity':'warning','items':[]})
 findings=raw['violations']+raw['unconnected_items']
 native={'opens':len(raw['unconnected_items']),'blocking':sum(v['severity']=='error' for v in raw['violations']),'warnings':sum(v['severity']=='warning' for v in findings),'exclusions':0,'ignored_checks':[],'findings':findings}
 answer,hits=checks.predicate(case,native,raw,scene,[])
 return {'case':case,'warning':warning,'predicate':answer,'expected_target_findings':len(hits),'raw':raw,'native':native}
if __name__=='__main__':
 rows=[run(case,w) for case in ('positive','false_hull','foreign_intrusion') for w in (None,'lib_footprint_issues','unknown_provider','missing_tuning_profile','padstack_invalid')]
 result={'synthetic_only':True,'native_execution':False,'reviewed_checks_sha256':hashlib.sha256(Path(checks.__file__).read_bytes()).hexdigest(),'rows':rows}
 (BASE/'predicate-probe-001.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps([{k:r[k] for k in ('case','warning','predicate')} for r in rows],indent=2))
