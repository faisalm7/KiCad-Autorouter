from pathlib import Path
import json,sys,datetime
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,placement_clearance as io
packet=ROOT/'evidence/thermal-native-identity-components-001.json';r=f.read_json(packet);idx=ROOT/r['files_index']['path'];index=f.read_json(idx);notes=idx.parent
r['shared_retained_DRC_readbacks']=sum(len(f.read_json(ROOT/('.runs/thermal-native-identity-'+k+'-readback-001.json'))['checked_DRC_records']) for k in ('legacy0','native7','invalid7','cancel7'));assert r['shared_retained_DRC_readbacks']==11
r['accounting']=r['accounting'].replace('Harness prep .32/.30 and .49/.46','Harness prep complete exits .44/.42 and .61/.55')
r['curation_prepublication_correction']='Derived shared-reader stage count corrected from12 to actual11 before audit/publication; complete-exit harness-preparation costs corrected to their retained time logs. Native data, controllers, attempts and results unchanged. No curation/native rerun.'
r['text_curation_complete_wall_seconds']=.61;r['text_curation_complete_CPU_seconds']=.42
for path in (ROOT/'.runs/full-integration-168-time.log',ROOT/'.runs/curate-thermal-native-identity-components-001-time.log',ROOT/'.runs/curate-thermal-native-identity-components-001.log',Path(__file__)):
 raw=io.read_bytes(path,1024**2);raw.decode('utf-8');dest=notes/'curation'/path.name;dest.parent.mkdir(exist_ok=True)
 with dest.open('xb') as s:s.write(raw)
 row=dict(path=str(dest.relative_to(ROOT)),bytes=len(raw),sha256=p.sha(dest));index['files'].append(row);index['material'].append(dict(original=str(path.relative_to(ROOT)),retained=row['path'],bytes=row['bytes'],sha256=row['sha256']));r['files'].append(row)
p.save_json(idx,index);r['files_index']['sha256']=p.sha(idx);p.save_json(packet,r)
review=f.read_json(ROOT/'.runs/thermal-native-identity-component-review-001.json');review['review_authority']='Independent AI source/evidence review, not human engineer review.';review['public_component_packet']=dict(path=str(packet.relative_to(ROOT)),sha256=p.sha(packet))
p.save_json(ROOT/'evidence/thermal-native-identity-component-review-001.json',review)
print(json.dumps(dict(readbacks=r['shared_retained_DRC_readbacks'],packet_sha256=p.sha(packet),files=len(r['files']))))
