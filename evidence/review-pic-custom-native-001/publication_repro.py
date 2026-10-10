"""Tiny publication-only mocks. No native, engine, metadata or source mutation."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
DRAFT=ROOT/'.runs/pic-custom-observer-draft-001'
sys.dont_write_bytecode=True
sys.path.insert(0,str(DRAFT))
spec=importlib.util.spec_from_file_location('pic_driver_review',DRAFT/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
rows=[]
for case in ('unchanged','canonical_mutation','budget_during_scan','record_mutation'):
    out=HERE/('publication-001-'+case);out.mkdir()
    record={'status':'observations_complete','observations_complete':True,'routing_accepted':False}
    exhausted=False
    def size(_):
        global exhausted
        if case=='canonical_mutation':
            altered=dict(record, routing_accepted=True)
            (out/'summary.json').write_text(json.dumps(altered))
        elif case=='budget_during_scan':exhausted=True
        elif case=='record_mutation':record['routing_accepted']=True
        return 1
    with mock.patch.object(d,'size',side_effect=size):
        returned=d.publish(out,record,lambda:None,lambda:None,lambda:0 if exhausted else 1)
    raw=json.loads((out/'summary.json').read_text())
    rows.append({'case':case,'returned':returned,'canonical':raw,'exhausted':exhausted,
                 'negative_correctly_invalidated':case=='unchanged' or raw.get('observations_complete') is False})
result={'driver_sha256':hashlib.sha256((DRAFT/'driver.py').read_bytes()).hexdigest(),'native_executed':False,'source_modified':False,'cases':rows}
(HERE/'publication-reproduction-001.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
