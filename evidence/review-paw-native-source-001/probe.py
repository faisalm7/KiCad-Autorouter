"""Actual controller, copied input files, fabricated native stages; no native/Git."""
from pathlib import Path
import hashlib,json,sys
from unittest import mock
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'source'))
import test_driver as t
import driver as d
OUT=HERE/'probe-001';OUT.mkdir()
rows=[]
for profile,mutation in [('lipo',None),('paw3395',None),('paw3395','source'),('paw3395','report'),('paw3395','stage_log')]:
    case=profile+'-'+(mutation or 'positive');area=OUT/case;area.mkdir();events=[];size=d.size
    def scan(path):
        n=size(path)
        if mutation and (Path(path)/'summary.json').exists() and not events:
            if mutation=='source':target=area/'unchanged/.data/expansion005/paw3395/paw3395.kicad_pro'
            elif mutation=='report':target=Path(path)/'original-drc.json'
            else:target=Path(path)/'observe.log'
            before=t.digest(target);target.write_bytes(target.read_bytes()+b'\n');events.append({'path':str(target),'before':before,'after':t.digest(target)})
        return n
    with mock.patch.object(d,'size',side_effect=scan):
        result=t.flow_case(area,'unchanged',source_profile=profile)
    path=area/'unchanged/.runs/out/summary.json';saved=d.read(path)
    expected=mutation is None
    assert saved['observations_complete'] is expected,(case,saved)
    assert saved['routing_accepted'] is False and saved['format_support_qualified'] is False and saved['dependency_complete'] is False
    assert bool(events) is bool(mutation)
    assert result['mock_native_stages']==2
    if mutation:assert list(path.parent.glob('invalidated-*-summary.json'))
    rows.append({'case':case,'expected_complete':expected,'status':saved['status'],'observations_complete':saved['observations_complete'],'error':saved.get('error'),'events':events,'canonical_sha256':t.digest(path),'mock_native_stages':2,'actual_native_processes':0,'passed':True})
    print(case,saved['status'],saved.get('error'))
(HERE/'probe-results.json').write_text(json.dumps({'scope':'Pure final-size boundary injections on exact frozen controller; no native or Git execution','rows':rows,'passed':True},indent=2)+'\n')
