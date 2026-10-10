"""Independent read-only control-gate audit; no KiCad or routing invocation."""
import copy,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,sexpr as sx,board_floor as g
helper=ROOT/'experiments/placement_production_controls_v1/driver.py'
spec=importlib.util.spec_from_file_location('placement_control_review',helper);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
positive_path=ROOT/'.runs/placement-production-native-001/result.json';failed_dir=ROOT/'.runs/placement-production-controls-native-001'
positive=json.loads(positive_path.read_text());source=Path(positive['source']);original=p.preflight(source)
inputs={'positive':positive_path.parent,'failed':failed_dir,'source':source.parent,'helpers':helper.parent,'core':ROOT/'autorouter'}
before={key:p.tree_hash(path) for key,path in inputs.items()}
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def rejects(name,call,match):
 try:call()
 except (p.Rejected,ValueError) as exc:check(name,match in str(exc));return
 raise AssertionError(name+' unexpectedly accepted')
checked=p.check_result(positive_path)
check('current complete production receipt passes',checked['current'] and checked['input_policy']=='placement-clearance-v1')
check('positive recorded committed core remains exact',all(p.sha(ROOT/name)==digest for name,digest in positive['tools']['implementation_sha256'].items()))
check('pinned original board and project match',p.sha(source)=='1e2216f05fd7540a2a4edf894a18addc389c056854bc6bb5fa2169f90753f7dd' and p.sha(source.with_suffix('.kicad_pro'))=='ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538')
check('original has eight unlocked reference routes and one area',len(p.routes(original))==8 and not any(p.locked(x) for x in p.routes(original)) and len(sx.children(original,'zone'))==1)
task=d.check_fixture_source(source,original,positive)
check('exact declared task hash reconstructed',g.sha((sx.dump(task)+'\n').encode())==positive['task_sha256']=='0144c92bb45a55b10b7e61fdc51754b15aed62a5afa1c744da05ce4127b34aa0')
check('task has no routes and immutable source fields unchanged',not p.routes(task) and p.immutable(task)==p.immutable(original))
check('saved export task equals reconstruction',sx.read(positive_path.parent/'floor-export-input'/source.name)==task)
bad=copy.deepcopy(positive);bad['task_sha256']='0'*64
rejects('stale task hash rejected',lambda:d.check_fixture_source(source,original,bad),'stripped task')
protected=copy.deepcopy(original);p.routes(protected)[0].append('locked')
rejects('protected source route rejected',lambda:d.check_fixture_source(source,protected,positive),'protected')
rejects('wrong source identity rejected',lambda:d.check_fixture_source(source.with_name('candidate.kicad_pcb'),original,positive),'owned fixture source')
nohash=copy.deepcopy(positive);nohash.pop('task_sha256')
rejects('missing outer production task hash rejected',lambda:d.check_fixture_source(source,original,nohash),'stripped task')
failed=json.loads((failed_dir/'summary.json').read_text())
check('failed001 explicitly remains pre-native failure',failed['status']=='failed' and failed['controls_passed'] is False and failed['native_executed'] is False and failed['steps']==[] and failed['cases']==[])
check('failed001 is exact obsolete predicate',failed['error']=='Rejected: expected original no-route/one-placement-area fixture differs')
check('failed001 contains no native process receipts',not list(failed_dir.rglob('*-process.json')))
check('fresh positive has zero findings and unchanged original ignored-check metadata',not positive['native']['findings'] and all(positive['native'][key]==0 for key in ('opens','blocking','warnings','exclusions')) and positive['source_drc']['ignored_checks']==positive['native']['ignored_checks'])
check('positive budgets account all declared stages',positive['wall_seconds']<=60 and positive['total_cpu_seconds']<=60 and len(positive['steps'])==8)
after={key:p.tree_hash(path) for key,path in inputs.items()}
check('all original evidence helper and core trees unchanged',before==after)
result={'scope':'Independent narrow helper-gate and existing raw receipt consistency; no new native execution','passed':all(x['passed'] for x in checks),'checks':checks,
 'bound_inputs':before,'positive_summary':{key:positive[key] for key in ('candidate_sha256','task_sha256','native_report_sha256','metrics','wall_seconds','total_cpu_seconds')},
 'failed_summary':failed,'conclusion':'No blocker found for committing the narrow harness fix and running fresh controls002. Actual invalid native controls remain unexecuted until that run.'}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'checks':len(checks),'driver_sha256':p.sha(helper),'audit_sha256':p.sha(OUT/'audit.json')},indent=2))
