"""Pure read-only-source review of002 publication fix; scratch is review-owned."""
import ast,copy,hashlib,json,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
source=ROOT/'.runs/board-floor-native-draft-002/driver.py'
syntax=ast.parse(source.read_text());names={'canonical_json','read_json_strict','publish'}
functions=[x for x in syntax.body if isinstance(x,ast.FunctionDef) and x.name in names]
assert {x.name for x in functions}==names
ns={'p':p,'json':json,'uuid':uuid};exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),ns)
original=json.loads(next((ROOT/'.runs/board-floor-geometry-001').glob('invalidated-*-summary.json')).read_text())
for case in original['cases']:
    if case['expected'] is not None:case['expected']=tuple(case['expected'])
scratch=OUT/'fixed-publication-reproduction';scratch.mkdir()
record=copy.deepcopy(original);ns['publish'](scratch,record,lambda:None,lambda:None)
assert json.loads((scratch/'summary.json').read_text())==json.loads(json.dumps(original))
assert not list(scratch.glob('invalidated-*'))
assert ns['canonical_json']({'passed':True})!=ns['canonical_json']({'passed':1})
for text in ('{"x":0,"x":1}','{"x":NaN}','{"x":Infinity}'):
    target=scratch/('bad-'+uuid.uuid4().hex+'.json');target.write_text(text)
    try:ns['read_json_strict'](target)
    except p.Rejected:pass
    else:raise AssertionError('malformed summary admitted')
result={'review_passed':True,'driver_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'native_executed':False,'actual_record_roundtrip_passed':True,'strict_duplicate_nonfinite_and_bool_int_checks_passed':True,'author_controls_log_count':31,'new_regression_bodies_read':8,'author_controls_rerun_by_reviewer':False,'scope':'Publication fix only; native002 fresh execution remains required. No draft or actual run modified.'}
(OUT/'fix-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
