"""Retain shared benchmark-administration qualification, including draft defects."""
from pathlib import Path
import ast, datetime, hashlib, json, math, re, sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, placement_clearance as io, provenance as pv
notes=ROOT/'evidence/current-comparison-native-cohort-056-001-notes'
target=ROOT/'evidence/current-comparison-native-cohort-056-001.json'
assert not notes.exists() and not target.exists()
refs={};files=[];material=[];total=0
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py'
assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
nodes=[n for n in ast.parse(helper.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='retain']
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(helper)+'::retain','exec'),globals())
timing=ROOT/'evidence/runtime050-native-milestone-002-notes/shared-helpers/report_current_comparison.py'
assert p.sha(timing)=='aa630b7d0aad9e7a2356ddc0fbb03894578fd4bff9a601e9a04c104fed86c9f7'
nodes=[n for n in ast.parse(timing.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in ('require','digest','complete_cost')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(timing)+'::cost','exec'),globals())
names=['scripts/freeze_current_comparison.py','tests/test_comparison_freezer.py',
       'scripts/report_current_comparison.py','tests/test_current_comparison_report.py']
pins={name:p.sha(ROOT/name) for name in names}
review_path=ROOT/'.runs/current-comparison-native-cohort-review-056-003.json'
review=json.loads(review_path.read_bytes())
assert review['source_only'] is True and review['human_review'] is False
assert review['no_concrete_bypass_found'] is True and review['files_sha256']==pins
readback=ROOT/'.runs/current-comparison-native-cohort-readback-056-003.log'
assert json.loads(readback.read_bytes())['passed'] is True
tests={}
for label in ('freezer','reporter'):
    attempt='003' if label=='freezer' else '001'
    timepath=ROOT/'.runs'/('current-comparison-'+label+'-targeted-056-'+attempt+'-time.log')
    text=timepath.read_text();assert '\nOK\n' in text and not re.search(r'\n(?:FAILED|ERROR):',text)
    count=re.findall(r'Ran ([0-9]+) tests in ',text);assert len(count)==1
    tests[label]=dict(passed=True,tests=int(count[0]),complete_cost=complete_cost(timepath))
queue=[]
for path in [review_path,readback,ROOT/'.runs/current-comparison-native-cohort-readback-056-003-time.log',
             ROOT/'.runs/current-comparison-native-cohort-readback-056-001-provenance.json']:
    queue.append((path,Path('qualification')/path.name))
for label,attempts in (('freezer',('001','002','003')),('reporter',('001',))):
    for attempt in attempts:
        for suffix in ('.log','-time.log'):
            path=ROOT/'.runs'/('current-comparison-'+label+'-targeted-056-'+attempt+suffix)
            queue.append((path,Path('tests')/path.name))
for suffix in ('.log','-time.log'):
    path=ROOT/'.runs'/('current-comparison-native-cohort-readback-056-001'+suffix)
    queue.append((path,Path('draft001')/path.name))
for number in ('001','002'):
    for path in (ROOT/'.runs'/('current-comparison-admission-draft-'+number)).iterdir():
        queue.append((path,Path('draft'+number)/path.name))
for suffix in ('.log','-time.log'):
    path=ROOT/'.runs'/('current-comparison-native-cohort-readback-056-002'+suffix)
    queue.append((path,Path('draft002')/path.name))
for name in names:queue.append((ROOT/name,Path('final-source')/name))
queue.append((Path(__file__),Path('administration')/Path(__file__).name))
for path,name in queue:retain(path,name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
p.save_json(target,dict(schema=1,kind='current-selected7-CLI-cohort-comparison-administration-qualification-v1',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),project_complete=False,
    Native_executed=False,actual_GUI=False,source_sha256=pins,tests=tests,
    final_retained_metadata_readback=dict(passed=True,complete_cost=complete_cost(ROOT/'.runs/current-comparison-native-cohort-readback-056-003-time.log')),
    independent_AI_review=review,
    draft001=dict(scope='Successful but insufficient27 freezer/22 reporter tests and real retained-metadata readback; no benchmark arm frozen or run under this draft.',
        defects=['Counts alone did not apply the product Native acceptance policy, including critical ignored checks and field warnings.',
                 'Registered case labels lacked actual retained routing contract/score binding.'],
        disposition='Correct shared metadata gate and retain regressions before prospective execution; runtime/native validators unchanged.',
        freezer_test_cost=complete_cost(ROOT/'.runs/current-comparison-freezer-targeted-056-001-time.log'),
        metadata_readback_cost=complete_cost(ROOT/'.runs/current-comparison-native-cohort-readback-056-001-time.log')),
    draft002=dict(tests_passed=30,freezer_test_cost=complete_cost(ROOT/'.runs/current-comparison-freezer-targeted-056-002-time.log'),real_metadata_readback_passed=False,metadata_readback_cost=complete_cost(ROOT/'.runs/current-comparison-native-cohort-readback-056-002-time.log'),reason='Real retained056 metadata rejected because engine settings precede four I/O args rather than ending argv. Independent source review also found Improve parent key presence contradicted the actual forbidden-key contract. Fix both fixture assumptions before any experiment, preserving the failed readback; no Native rerun.'),
    current_runtime=dict(source_head='a03b5e8b6ae523d9f099cf211815900053629fe3',manifest_sha256='b018b1bc6487183b000de62b743bd143cd2dddca71afe29428cadbd4cfdccded',runtime_rebuilt=False,
        prerequisite=dict(path='evidence/runtime056-native-milestone-001.json',sha256=p.sha(ROOT/'evidence/runtime056-native-milestone-001.json'))),
    scope='Shared freezer/reporter extend improve-v2 only to explicit current positive seven/eleven-case Native CLI cohort lineage. No GUI/thermal admission or old042/050 contract change. The experiment itself is not yet frozen/executed; actual Native acceptance for every new final remains mandatory.',
    accounting='All tests, failed-draft review/readback and final readback are additional to Native qualification and the future comparison. Source authoring and AI review are additional and partly unmetered, notzero.',
    retention='Owned scripts/tests/logs and metadata only; foreign CAD/raw findings/tools excluded. Raw remains Mac-only/outside010, not a full restoration or release.',
    files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json'))))
print(json.dumps(dict(files=len(files),bytes=total,tests=tests,Native_executed=False)))
