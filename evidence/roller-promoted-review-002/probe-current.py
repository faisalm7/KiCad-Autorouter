"""Actual publication-tail source seams; fabricated controls, zero native/Git."""
import ast,copy,hashlib,json,sys,time,types
from pathlib import Path
from unittest.mock import patch
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
HERE=Path(__file__).resolve().parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import floor_route as f,pipeline as p,handoff as h
SOURCE=ROOT/'experiments/roller_support_v1/driver.py';OLD=ROOT/'.runs/roller-support-draft-001/driver.py'
raw=SOURCE.read_text();oldraw=OLD.read_text()
def function(text):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='_experiment')
current=function(raw);old=function(oldraw)
account_node=next(n for n in current.body if isinstance(n,ast.FunctionDef) and n.name=='account')
def extract_tail(node):
    for i,n in enumerate(node.body):
        if isinstance(n,ast.Expr) and ast.unparse(n).startswith('f.publish('):return node.body[i:]
    raise AssertionError('tail missing')

def case(name,*,old_tail=False,write_failure=False,fixed_account=False):
    out=HERE/(name+'-002');out.mkdir();bound=out/'retained-source';bound.write_bytes(b'pinned')
    record={'accepted':False,'controls_passed':True,'status':'controls_passed','whole_project_drc_clean':False}
    lifecycle={};h.capture_destination(lifecycle,out);injections=[];published=False
    def stable():
        if bound.read_bytes()!=b'pinned':raise p.Rejected('retained source changed')
    def owned():h.owned_destination(lifecycle)
    def size(path):
        if published and not write_failure and not injections:
            bound.write_bytes(b'changed during final size');injections.append('late-size-mutation')
        return 1
    def publish(*args,**kwargs):
        nonlocal published
        result=f.publish(*args,**kwargs);published=True;return result
    values={'f':types.SimpleNamespace(publish=publish),'p':p,'h':h,'time':time,'start':time.monotonic(),'cpu0':h.cpu_seconds(),'record':record,'out':out,
            'job':types.SimpleNamespace(steps=[]),'remaining':lambda:120.,'LIMIT':32*1024**2,'SECONDS':120.,'size':size,'stable':stable,'owned':owned}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(account_node)],type_ignores=[])),str(SOURCE),'exec'),values)
    if fixed_account:
        original_account=values['account']
        def account():
            original_account()
            if record['status'] in ('invalidated','cancelled','failed','budget_exceeded'):record['controls_passed']=False
        values['account']=account
    tail=extract_tail(old if old_tail else current)
    node=ast.FunctionDef(name='finish',args=ast.arguments(posonlyargs=[],args=[],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(tail),decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(SOURCE),'exec'),values)
    save=p.save_json;first=True
    def writer(path,value):
        nonlocal first
        save(path,value)
        if write_failure and first and path.name=='result.json':first=False;injections.append('one-time publication OSError after write');raise OSError('deliberate failed final publication')
    with patch.object(p,'save_json',side_effect=writer):result=values['finish']()
    disk=f.read_json(out/'result.json')
    return {'case':name,'returned_status':result['status'],'returned_controls_passed':result['controls_passed'],'disk_status':disk['status'],'disk_controls_passed':disk['controls_passed'],'source_changed':bound.read_bytes()!=b'pinned','injections':injections,'invalidated_positive_records':sorted(x.name for x in out.glob('invalidated-result-*')),'native_executions':0}
rows=[case('original-late-size',old_tail=True),case('current-late-size'),case('current-publication-failure',write_failure=True),case('proposed-account-fix-publication-failure',write_failure=True,fixed_account=True)]
assert rows[0]['disk_controls_passed'] is True and rows[0]['source_changed']
assert rows[1]['disk_status']=='invalidated' and rows[1]['disk_controls_passed'] is False
assert rows[2]['disk_status']=='invalidated' and rows[2]['disk_controls_passed'] is False
assert rows[3]['disk_status']=='invalidated' and rows[3]['disk_controls_passed'] is False
(HERE/'current-results.json').write_text(json.dumps({'schema':1,'promoted_driver_sha256':hashlib.sha256(raw.encode()).hexdigest(),'old_author_driver_sha256':hashlib.sha256(oldraw.encode()).hexdigest(),'scope':'Exact extracted source tails and current actual account; fabricated completed controls with actual shared publisher; no native/solver/Git','rows':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
