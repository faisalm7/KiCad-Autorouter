"""Pure mocked-stage interruption control. No native/engine subprocesses."""
import sys,importlib.util,json,tempfile
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[1];DRAFT=ROOT/'.runs/baseline-strength-review-001/prototype'
sys.path.insert(0,str(ROOT))
import autorouter,scripts

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module);return module
p=load('autorouter.pipeline',DRAFT/'autorouter/pipeline.py');autorouter.pipeline=p
m=load('scripts.experiment_portfolio',DRAFT/'scripts/experiment_portfolio.py');scripts.experiment_portfolio=m
t=load('portfolio_review_controls',DRAFT/'tests/test_portfolio.py')
real_temp=tempfile.TemporaryDirectory
with patch.object(t.tempfile,'TemporaryDirectory',side_effect=lambda:real_temp(dir=OUT,prefix='control-')):
    c=t.PortfolioControls();c.setUp()
    try:
        real_save=p.save_json
        def write(path,value):
            real_save(path,value)
            if path.name=='portfolio-summary.json' and value.get('comparison_eligible'):
                c.cpu=120.1
                raise KeyboardInterrupt('injected cancellation after final accepted save and before postwrite caps')
        escaped=False
        try:
            with patch.object(p,'save_json',side_effect=write):m.experiment(c.out)
        except KeyboardInterrupt:escaped=True
        saved=json.loads((c.out/'portfolio-summary.json').read_text())
        receipt={'kind':'mocked-stage final-publication cancellation control, not native evidence','escaped_keyboard_interrupt':escaped,'comparison_eligible_on_disk':saved['comparison_eligible'],'status_on_disk':saved['status'],'sampled_cpu_on_disk':saved['total_cpu_seconds'],'actual_injected_cpu':c.cpu,'trials':len(c.calls),'defect_reproduced':escaped and saved['comparison_eligible']}
        (OUT/'reproduction.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
    finally:c.doCleanups()
