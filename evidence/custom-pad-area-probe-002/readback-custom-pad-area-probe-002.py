import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'experiments/custom_pad_area_probe_v1'))
import driver as d
out=R/'.runs/custom-pad-area-probe-002';r=d.decode(d.content(out/'summary.json'))
assert r['observations_complete'] and r['expected_observations_match']
assert {k:v for k,v in d.inventory(out).items()if k!='summary.json'}==r['frozen_evidence']
observed=d.decode(d.content(out/'observations.json'));expected=d.decode(d.content(out/'expectations.json'))
comparison=d.validate_observation(observed,expected);print(type(comparison));assert comparison==r['case_comparison']
for rel,row in r['runtime']['sources'].items():assert d.content(R/rel,digest=True)==row
v={'schema':1,'readback_only':True,'passed':True,'summary_sha256':d.content(out/'summary.json',digest=True)['sha256'],'observations_sha256':d.content(out/'observations.json',digest=True)['sha256'],'frozen_files':len(r['frozen_evidence']),'source_bindings':len(r['runtime']['sources']),'case_comparison':comparison,'custom_pad_support_qualified':False,'routing_accepted':False}
p=R/'.runs/custom-pad-area-probe-002-readback.json';assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v for k,v in v.items()if k!='case_comparison'}))
