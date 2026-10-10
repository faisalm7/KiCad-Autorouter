"""Tiny real-file publication falsifier; no native, subprocess, or network."""
import hashlib, importlib.util, json, sys
from pathlib import Path
from unittest import mock
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
AUTHOR=ROOT/'.runs/pic-severity-controls-draft-002'
sys.path.insert(0,str(AUTHOR))
spec=importlib.util.spec_from_file_location('severity_review_driver',AUTHOR/'driver.py')
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
OUT=Path(__file__).resolve().parent/'publication-002'
OUT.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for variant in ('unchanged','late_source','late_report'):
    case=OUT/variant;case.mkdir();out=case/'out';out.mkdir()
    source=case/'original.kicad_pro';source.write_text('{"original":true}\n')
    report=out/'raw-report.json';report.write_text('{"violations":[]}\n')
    frozen={source:sha(source),report:sha(report)}
    record={'status':'controls_passed','controls_passed':True,**d.FALSE_CLAIMS}
    calls=[]
    def stable():
        calls.append('stable')
        if any(sha(p)!=h for p,h in frozen.items()):raise d.p.Rejected('material changed')
    real_size=d.size
    def final_scan(path):
        measured=real_size(path)
        if variant!='unchanged':
            target=source if variant=='late_source' else report
            target.write_bytes(target.read_bytes()+b' ')
        calls.append('size')
        return measured
    with mock.patch.object(d,'size',side_effect=final_scan):
        result=d.publish(out,record,stable,lambda:None,lambda:1)
    results.append({'case':variant,'returned_controls_passed':result['controls_passed'],
        'canonical_controls_passed':d.read(out/'summary.json')['controls_passed'],
        'source_unchanged':sha(source)==frozen[source],'report_unchanged':sha(report)==frozen[report],
        'calls':calls,'expected_controls_passed':variant=='unchanged'})
receipt={'source':str(AUTHOR/'driver.py'),'source_sha256':sha(AUTHOR/'driver.py'),
    'scope':'Only publication flow, real tiny files, mocked final scan timing; no native validation claim.',
    'cases':results}
(OUT/'results.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
