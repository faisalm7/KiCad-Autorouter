"""Retain the bounded negative finding using shared final-stage readback."""
from pathlib import Path
from types import SimpleNamespace
import sys,json,hashlib,shutil,time,resource
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,sexpr as sx
from experiments.net_tie_contact_v1 import driver as d
base=ROOT/'.runs/net-tie-contact-native-001';outer=json.loads((base/'result.json').read_text());r=json.loads((base/'native/result.json').read_text());protocol=json.loads((base/'preparation/protocol.json').read_text())
assert outer['passed']is False and outer['status']=='failed' and r['status']=='observed_unqualified' and r['passed']is False
out=ROOT/'evidence/net-tie-contact-native-001-notes';out.mkdir()
files={'enclosure-result.json':base/'result.json','native-result.json':base/'native/result.json','protocol.json':base/'preparation/protocol.json','whole-command.log':ROOT/'.runs/net-tie-contact-native-001-command.log','whole-time.log':ROOT/'.runs/net-tie-contact-native-001-time.log','prepare.log':base/'prepare.log','native.log':base/'native.log','enclosure.py':ROOT/'.runs/run-net-tie-contact-native-001.py'}
cases={}
for case,item in r['cases'].items():
 assert item['control_passed']is False and item['observation_complete']is False
 source=d.board_path(base/'preparation'/case,case);candidate=base/'native'/case/'candidate'/source.name
 job=SimpleNamespace(out=base/'native'/case/'job',steps=item['steps'])
 d.replay_candidate(job,sx.read(source),candidate,p.tree_hash(source.parent),p.routes(sx.read(source)),item['candidate_sha256'],item['native'])
 assert not (base/'native'/case/'observed.dsn').exists() and not (base/'native'/case/'observation.json').exists()
 for path in job.out.iterdir():
  if path.is_file() and path.suffix in {'.json','.log','.net'}:files[case+'--'+path.name]=path
 if case!='original':
  for path in candidate.parent.iterdir():
   if path.is_file():files[case+'--candidate--'+path.name]=path
 n=item['native'];cases[case]=dict(candidate=str(candidate.relative_to(ROOT)),candidate_sha256=item['candidate_sha256'],native={k:n[k]for k in ('opens','blocking','warnings','exclusions','ignored_checks','findings')},control_passed=False,reason=item['reason'],shared_final_and_refill_readback=True,source_packet_sha256=protocol['source_hashes'][case],protected_routes=len(p.routes(sx.read(source))))
files['SparkFun-LICENSE.md']=ROOT/'.data/corpus-expansion-audit-001/sparkfun__SparkFun_Ambient_Light_Sensor-VEML7700/LICENSE.md'
rows=[]
for name,src in files.items():
 dst=out/name;shutil.copyfile(src,dst);raw=dst.read_bytes();rows.append(dict(path=str(dst.relative_to(ROOT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),source=str(src.relative_to(ROOT))))
(out/'ATTRIBUTION.md').write_text('Original-board diagnostic data derives from SparkFun Electronics, SparkFun Ambient Light Sensor VEML7700: https://github.com/sparkfun/SparkFun_Ambient_Light_Sensor-VEML7700 . Exact retained source hashes are in protocol.json and the prospective record. Hardware/report derivatives are CC BY-SA4.0: https://creativecommons.org/licenses/by-sa/4.0/ . SparkFun LICENSE is retained. Changes: Native refill and diagnostic projection only; no source repair or endorsement. Original CAD is not redistributed here. Owned controls and project code are GPL-3.0-or-later.\n')
record=dict(schema=1,kind='actual-bounded-net-tie-prerequisite-deferred',native_executed=True,engine_executed=False,qualified=False,accepted=False,production_admitted=False,source_head=protocol['git_head'],prospective='evidence/net-tie-contact-prospective-001.json',protocol_sha256=p.sha(base/'preparation/protocol.json'),outer_status=outer['status'],child_status=r['status'],whole_costs=dict(external_wall_seconds=16.74,external_full_cpu_seconds=14.13,scope='Includes preparation, all three cases, failed workers and final shared publication; child times are subsets, not added twice.',research_authoring_independent_review_cpu_seconds=None),cases=cases,decision='DEFER; no Native retry or production guard change. Original has independent immutable-footprint courtyard conflicts. Group container unavailable; no pointer/ownership workaround or inferred substitute.',observed_binding_failure='All three GetNetTiePadGroups() calls return noniterable SwigPyObject. Subsequent map/GetNetTiePads, contact and DSN stages were not reached, not proven unavailable.',outside_short_frozen_control='Controller stopped at observation before its type check. Independent raw-readback review finds tracks_crossing/hole_clearance/solder_mask_bridge outside the predeclared clearance/shorting_items types, despite pinned item UUID sets. Do not broaden retrospectively or call it a passed control.',actual_contact_or_dsn_proof=False,shared_native_readback=True,skeptical_review='Separate read-only AI review confirmed actual raw findings, source/code/final bindings and all-false flags. No human/electrical/physical review.',unchanged_runtime='010/source5d85f5f1 remains qualified in its existing scope. No added family/completion/quality gain.',backup_cutoff='010capture8250c18e predates this Native run. Current raw source already captured; these new reports/candidates are not retroactively included. New-target full restoration remains disk-headroom blocked.',files=rows)
(ROOT/'evidence/net-tie-contact-native-001.json').write_text(json.dumps(record,indent=2)+'\n')
for row in rows:assert p.sha(ROOT/row['path'])==row['sha256']
print(json.dumps({'curated':True,'cases':len(cases),'files':len(rows),'bytes':sum(row['bytes']for row in rows),'native_control_pass':False}))
