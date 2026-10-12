"""Existing synthetic receipt fixture with actual checker, no native workers."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,sexpr as sx,floor_route as f
HERE=Path(__file__).resolve().parent;OUT=HERE/sys.argv[1];OUT.mkdir(exist_ok=False)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
source=(ROOT/'tests/test_result.py').read_text().replace('scratch = ROOT / ".cache" / "result-tests"','scratch = REVIEW_SCRATCH')
ns={'__file__':str(ROOT/'tests/test_result.py'),'__name__':'existing_receipt_fixture','REVIEW_SCRATCH':OUT}
exec(compile(source,'<existing-result-fixture-scratch-only>','exec'),ns)
pins={str(path.relative_to(ROOT)):sha(path) for path in (ROOT/'autorouter').glob('*.py')};rows=[]
for mutation in (None,'candidate_board','task_dsn'):
    case=ns['ResultFreshnessTests']();case.setUp();case.temp._finalizer.detach()
    # Add exact UUIDs to existing synthetic tracks in all four copies, then bind.
    tree=sx.read(case.source)
    for index,route in enumerate(p.routes(tree)):route.append(['uuid','"route-'+str(index)+'"'])
    for board in (case.source,case.candidate,case.run/'snapshot'/case.source.name,case.run/'final-drc-input'/case.source.name):sx.write(board,tree)
    hashes=p.tree_hash(case.source_dir);candidate_sha=sha(case.candidate)
    case.data.update(source_hashes=hashes,candidate_sha256=candidate_sha)
    case.binding.update(before=hashes,after=hashes)
    (case.run/'final-drc-binding.json').write_text(json.dumps(case.binding))
    case.data['steps'][0]['validated_input_sha256']=candidate_sha
    for name,field in [('native.dsn','native_dsn_sha256'),('task.dsn','task_dsn_sha256')]:
        shutil.copyfile(ROOT/'evidence/placement-production-native-001/native.dsn',case.run/name);case.data[field]=sha(case.run/name)
    overrides={'profile':'completion-only','layers':['F.Cu']};effective=pref.resolve(overrides=overrides)
    p.capture_preferences(case.data,case.run,{'captured':None,'snapshot':pref.snapshot(overrides=overrides),'effective':effective})
    case.data.update(adapter='none',engine_profile='completion-only',scoring_variant=None)
    contract=p.layer_contract(case.run,case.source,effective)
    case.data.update(layer_binding=contract['binding'],layer_audit=p.audit_layer_contract(case.candidate,contract))
    settings=p.engine_profile_settings('completion-only',100);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
    settings['argv'].append(contract['binding']['engine_argument'])
    process={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,'argv':p.engine_argv(case.run,settings['argv']),'cwd':str(case.run),'wall_seconds':0,'cpu_seconds':0,'monitor_cpu_seconds':0}
    case.data.update(engine_budget=settings);case.data['steps'].insert(0,process)
    (case.run/'engine-process.json').write_text(json.dumps(process));case.save_receipt()
    original=f.read_json;trigger=[];reads=[]
    def inventory(path):
        value=original(path)
        if Path(path)==case.run/'engine-process.json':reads.append(True)
        if mutation and Path(path)==case.run/'engine-process.json' and len(reads)==2 and not trigger:
            trigger.append(True)
            targets={'candidate_board':case.candidate,'source_project':case.source.with_suffix('.kicad_pro'),'candidate_project':case.candidate.with_suffix('.kicad_pro'),'snapshot_project':(case.run/'snapshot'/case.source.name).with_suffix('.kicad_pro'),'final_input_project':(case.run/'final-drc-input'/case.source.name).with_suffix('.kicad_pro'),'source_board':case.source,'task_dsn':case.run/'task.dsn','native_report':case.native,'layer_audit':case.receipt}
            target=targets[mutation]
            if mutation=='candidate_board':
                changed=sx.read(target);sx.one(p.routes(changed)[-1],'layer')[1]='"B.Cu"';sx.write(target,changed)
            elif mutation.endswith('_project'):target.write_text('{"board":{"design_settings":{"rule_severities":{"clearance":"ignore"}}}}\n')
            elif mutation=='layer_audit':
                data=json.loads(target.read_text());data['layer_audit']['policy']='changed';target.write_text(json.dumps(data))
            else:target.write_bytes(target.read_bytes()+b'\n')
        return value
    with patch.object(f,'read_json',inventory):
        try:result=p.check_result(case.receipt);outcome={'current':result['current']}
        except Exception as exc:outcome={'current':False,'error':type(exc).__name__+': '+str(exc)}
    rows.append({'mutation':mutation,'triggered':bool(trigger),'root':str(case.root),**outcome})
assert pins=={str(path.relative_to(ROOT)):sha(path) for path in (ROOT/'autorouter').glob('*.py')}
report={'scope':'Synthetic native records; complete actual central checker; no native validation claim','source_pins':pins,'source_unchanged':True,'rows':rows}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
