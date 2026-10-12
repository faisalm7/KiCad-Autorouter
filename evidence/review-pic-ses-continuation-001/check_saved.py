"""Offline saved001 geometry/reuse audit; no compiler, JVM, KiCad, or subprocess."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d,ses_checks as c
RUN=ROOT/'.runs/pic-custom-ses-roundtrip-001';pins=d.inventory(RUN);original=d.inventory(d.original.SOURCE.parent)
record=d.base.decode(d.base.content(RUN/'summary.json'));observed=d.base.decode(d.base.content(RUN/'observations.json',4*1024**2))
expected=d.base.decode(d.base.content(RUN/'expectations.json'));raw=d.base.content(RUN/'raw.ses');dsn=d.base.content(RUN/'mixed.dsn')
assert record['status']=='failed' and record['error']=='ValueError: engine route shape metadata differs'
assert all(pins[k]==v for k,v in record['frozen_evidence'].items())
assert original==record['runtime']['original']==d.inventory(RUN/'observe-input')
assert [r['name'] for r in record['steps']]==['compile','import'] and record['native_process_executed'] is False
for row in record['steps']:
 assert row['status']=='success' and row['exit_code']==0 and row['cleanup_complete'] is True
 assert d.base.decode(d.base.content(RUN/(row['name']+'-process.json')))=={k:v for k,v in row.items() if k!='name'}
assert observed['ses_executed'] is True and observed['cases'][1]['ses']==record['writer']
assert record['writer']['sha256']==hashlib.sha256(raw).hexdigest() and record['writer']['bytes']==len(raw)
oldpath=RUN/'code/experiments/pic_mixed_transport_probe_v1/ses_checks.py';spec=importlib.util.spec_from_file_location('old_ses_checks',oldpath);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
rows=[]
for case in observed['cases']:
 assert case['route_geometry_before_local']==case['route_geometry']
 try:old.geometry_check(case['route_geometry'],case['state'])
 except ValueError as exc:old_error=str(exc)
 else:raise AssertionError('original guard must reproduce actual failure')
 c.geometry_check(case['route_geometry'],case['state'])
 bad=copy.deepcopy(case['route_geometry']);track=next(t for t in bad['traces'] if t['width_um']==431.8);track['width_um']=431.800001
 try:c.geometry_check(bad,case['state'])
 except ValueError:tiny_change_rejected=True
 else:raise AssertionError('changed width accepted')
 rows.append({'plane_as_obstacle':case['requested_obstacle'],'original_guard_error':old_error,'corrected_guard_pass':True,'changed_431_800001_rejected':tiny_change_rejected,'trace_count':len(case['route_geometry']['traces']),'via_count':len(case['route_geometry']['vias'])})
source=d.sx.read(d.original.SOURCE)
try:
 _,audit=c.audit(raw,dsn,expected,source,observed['cases'][1]['route_geometry']);error=None
except ValueError as exc:audit=None;error=str(exc)
assert d.inventory(RUN)==pins and d.inventory(d.original.SOURCE.parent)==original
result={'no_native_or_jvm':True,'original_run_unchanged':True,'original_project_unchanged':True,'original_status':record['status'],'prior_wall_seconds':record['wall_seconds'],'prior_full_cpu_seconds':record['total_cpu_seconds'],'summary_sha256':pins['summary.json'],'raw_ses_bytes':len(raw),'raw_ses_sha256':hashlib.sha256(raw).hexdigest(),'geometry':rows,'transport_audit':audit,'audit_error':error,'checker_sha256':hashlib.sha256(Path(c.__file__).read_bytes()).hexdigest()}
(OUT/sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='transport_audit'}))
