"""Focused synthetic publication reproduction; no native/engine execution."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import importlib.util,json,tempfile
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('paired_controls',ROOT/'tests/test_paired.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
output=Path(__file__).resolve().parent;original_temp=tempfile.TemporaryDirectory
results=[]
for mode in ('over_cap','cancelled'):
    case=t.PairedControls('test_final_publication_crossing_cap_corrects_main_receipt')
    with patch.object(t.tempfile,'TemporaryDirectory',side_effect=lambda:original_temp(dir=output,prefix='paired-synthetic-')):case.setUp()
    try:
        case.shared=(95.,95.) if mode=='over_cap' else (10.,8.)
        if mode=='over_cap':case.c_cost=(10.,10.)
        save=t.m.p.save_json;injected=[False]
        def inject(path,data):
            save(path,data)
            if path.name=='paired-summary.json' and not injected[0]:
                injected[0]=True
                if mode=='over_cap':case.wall+=6.;case.cpu+=6.
                else:raise KeyboardInterrupt
        with patch.object(t.m.q,'observations',return_value=[{'final_delivery_accepted':True,'description':'synthetic observation'}]),patch.object(t.m.p,'save_json',side_effect=inject):
            returned=t.m.experiment(case.out)
        saved=json.loads((case.out/'paired-summary.json').read_text());row=saved['results'][1]
        results.append({'injection':mode,'status':saved['status'],'row_accepted':row['accepted'],'comparisons':saved['comparisons'],'observations':row['observations'],'inconsistent_observation_acceptance':row['accepted'] is False and any(o.get('final_delivery_accepted') is True for o in row['observations'])})
    finally:case.doCleanups()
record={'kind':'pure synthetic injected-clock/cancellation controls; no native evidence','script_sha256':t.m.p.sha(ROOT/'scripts/experiment_paired.py'),'findings':results,'scope':'Main paired acceptance and comparisons correctly reject both controls. Observation final_delivery_accepted metadata remains true after publication invalidation/cancellation; clear it whenever invalidating a row.','other_review':'Sequential execution, full frontier binding, wrapper/code/source freeze, conservative shared overhead charged to each arm and postpublication main acceptance caps inspected; no additional blocking finding.'}
(output/'paired-review.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
