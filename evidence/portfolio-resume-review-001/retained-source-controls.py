"""Reuse existing synthetic continuation fixtures; preserve original raw pair."""
import copy, importlib.util, json, subprocess
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).absolute().parent
spec=importlib.util.spec_from_file_location('owned_controls', HERE/'controls.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
m,p=c.m,c.p

def case(name, mutation):
    t=c.fixture.ResumeControls('test_resume_only_unattempted_variants_and_preserve_prior_contract')
    with patch.object(c.fixture.legacy.tempfile,'TemporaryDirectory',side_effect=lambda:c.RetainedTemporaryDirectory(HERE/name)):
        t.setUp()
    try:
        # Make the old frozen-code copy exactly correspond to its old contract.
        for relative,raw in [(m.RESUME_SCRIPT,b'old checker'),('core',b'unchanged core')]:
            target=t.old/'frozen-code'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            t.oldf['files_sha256'][relative]=p.sha(target)
        protocol=json.loads((t.old/'protocol.json').read_text());protocol['freeze']=copy.deepcopy(t.oldf);p.save_json(t.old/'protocol.json',protocol)
        old=json.loads((t.old/'portfolio-summary.json').read_text());old['protocol_sha256']=p.sha(t.old/'protocol.json');p.save_json(t.old/'portfolio-summary.json',old)
        invoice=json.loads((t.base/'B2_portfolio-invocation.json').read_text());invoice['result_sha256']=p.sha(t.old/'portfolio-summary.json')
        p.save_json(t.base/'B2_portfolio-invocation.json',invoice);p.save_json(t.base/'paired-summary.json',{'results':[invoice]})
        paired=json.loads((t.base/'protocol.json').read_text());paired['freeze']=copy.deepcopy(t.oldf);p.save_json(t.base/'protocol.json',paired)
        t.plan['artifacts']={name:p.sha(Path(name)) for name in t.plan['artifacts']};t.planpin=t.save_plan()
        mismatches_before=[rel for rel,h in t.oldf['files_sha256'].items() if p.sha(t.old/'frozen-code'/rel)!=h]
        if mutation=='before-start':(t.old/'frozen-code/core').write_bytes(b'tampered historical copy')
        saved=p.save_json
        def write(path,value):
            if mutation=='late-and-corrective-fails' and path.name=='portfolio-summary.json' and value.get('status')=='invalidated':
                raise OSError('corrective write refused after actual retained-tree rejection')
            saved(path,value)
            if mutation=='late-and-corrective-fails' and path.name=='portfolio-summary.json' and value.get('comparison_eligible') is True:
                (t.old/'frozen-code/core').write_bytes(b'tampered historical copy')
        failure=None;result=None
        with patch.object(p,'save_json',side_effect=write):
            try:result=t.resumed()
            except BaseException as exc:failure=type(exc).__name__+': '+str(exc)
        disk=json.loads((t.out/'portfolio-summary.json').read_text())
        return {'mutation':mutation,'mismatches_before':mismatches_before,
                'mismatches_after':[rel for rel,h in t.oldf['files_sha256'].items() if p.sha(t.old/'frozen-code'/rel)!=h],
                'failure':failure,'returned_eligible':None if result is None else result['comparison_eligible'],
                'disk_eligible':disk['comparison_eligible'],'disk_status':disk['status'],
                'calls':t.calls,'all_plan_artifact_pins_unchanged':all(p.sha(Path(name))==h for name,h in t.plan['artifacts'].items())}
    finally:t.doCleanups()

with patch.object(subprocess,'run',side_effect=c.forbidden),patch.object(subprocess,'Popen',side_effect=c.forbidden):
    result={name:case(name,mutation) for name,mutation in [('retained-positive','none'),('retained-initial-mutation','before-start'),('retained-late-corrective-failure','late-and-corrective-fails')]}
oldroot=c.ROOT/'.runs/nus-native-paired-002/run/B2_portfolio'
oldprotocol=json.loads((oldroot/'protocol.json').read_text())
result['actual_original_frozen_code_mismatches']=[rel for rel,h in oldprotocol['freeze']['files_sha256'].items() if p.sha(oldroot/'frozen-code'/rel)!=h]
result['source_sha256']=p.sha(c.ROOT/'.runs/portfolio-resume-draft-001/experiment_portfolio.py')
(HERE/'retained-source-controls.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,indent=2,sort_keys=True))
