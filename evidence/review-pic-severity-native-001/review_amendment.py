"""Pure review of v1.1 identity amendment against failed001, no native execution."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;RUN=ROOT/'.runs/pic-severity-controls-001'
NEW=ROOT/'experiments/pic_severity_controls_v1';OLD=RUN/'code/experiments/pic_severity_controls_v1'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(NEW))
from autorouter import placement_clearance as io,sexpr as sx
import fixture,checks
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
inventory=lambda p:io.inventory(p,max_bytes=20*1024**2,max_files=2048,max_entries=4096)
s=read(RUN/'summary.json');source=Path(s['source']);before=inventory(RUN);source_before=inventory(source.parent)
files=('driver.py','worker.py','fixture.py','checks.py','intent.py','test_controls.py','PROTOCOL.json','README.md','SOURCE-NOTES.md')
bindings={n:sha(NEW/n) for n in files};assertions=[]
def check(label,value):
    if not value:raise AssertionError(label)
    assertions.append(label)
tree=sx.read(source);table={json.loads(r[1]):(int(r[0]),json.loads(r[3]) if len(r)>3 else json.loads(r[1])) for r in sx.one(tree,'layers')[1:]}
check('all three ID/name pairs follow exact original layer table',checks.TEXT_LAYERS=={k:table[k] for k in ('Dwgs.User','Edge.Cuts','F.Fab')})
for name in ('fixture.py','intent.py','SOURCE-NOTES.md'):check(name+' unchanged bytes',sha(NEW/name)==sha(OLD/name))
def functions(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
oldf=functions(OLD/'driver.py');newf=functions(NEW/'driver.py')
check('driver lifecycle unchanged outside explicit protocol declaration',{k:v for k,v in oldf.items() if k!='protocol'}=={k:v for k,v in newf.items() if k!='protocol'})
check('severity target/residual predicate unchanged',functions(OLD/'checks.py')['predicate']==functions(NEW/'checks.py')['predicate'])
project=read(source.with_suffix('.kicad_pro'));synthetic={}
for row in s['cases']:
    name=row['case'];board,pro,scene=fixture.prepare(tree,project,name)
    check(name+' exact unchanged board bytes',board==(RUN/name/'observe-input'/source.name).read_bytes())
    check(name+' exact unchanged project recipe',pro==read(RUN/name/'observe-input'/source.with_suffix('.kicad_pro').name) and fixture.project_delta(project,pro,name)==row['project_delta'])
    obs=read(RUN/name/'observation.json')
    try:checks.observe(obs,scene,pro);missing_rejected=False
    except ValueError:missing_rejected=True
    check(name+' historical observation missing new ID remains rejected',missing_rejected)
    # New numeric fields are inferred only for this offline regression from the
    # source table. They are NOT an actual native GetLayer observation in001.
    expected={t['uuid']:t for t in scene['texts']}
    for text in obs['texts']:text['layer_id']=table[expected[text['uuid']]['layer']][0]
    check(name+' retained native identities plus explicit synthetic IDs pass',checks.observe(obs,scene,pro)['intent_and_geometry_observed'] is True)
    synthetic[name]=(obs,scene,pro)
for variant in ('wrong_id','boolean_id','wrong_alias','wrong_parent','wrong_profile','wrong_dimension','unexpected_composite','missing_composite','extra_class'):
    name='missing_default_profile' if variant in ('missing_composite','extra_class') else 'positive'
    obs,scene,pro=copy.deepcopy(synthetic[name])
    text=next(t for t in obs['texts'] if t['parent']=='board');ground=next(n for n in obs['nets'] if n['name']=='GND')
    if variant=='wrong_id':text['layer_id']=25
    if variant=='boolean_id':text['layer_id']=True
    if variant=='wrong_alias':text['layer']='Dwgs.User'
    if variant=='wrong_parent':text['parent']='footprint'
    if variant=='wrong_profile':ground['tuning_profile']='Wrong'
    if variant=='wrong_dimension':ground['width_nm']+=1
    if variant=='unexpected_composite':ground['class']='POWER,Default'
    if variant=='missing_composite':ground['class']='POWER'
    if variant=='extra_class':ground['class']='POWER,Default,Other'
    try:checks.observe(obs,scene,pro);rejected=False
    except ValueError:rejected=True
    check(variant+' rejected',rejected)
check('no author source changes during review',bindings=={n:sha(NEW/n) for n in files})
check('entire failed001 and original15 unchanged',before==inventory(RUN) and source_before==inventory(source.parent))
value={'schema':1,'status':'v1.1_amendment_source_review_cleared','native_executed':False,'native002_required':True,'historical001_still_failed':True,'source_files':bindings,'layer_mapping':checks.TEXT_LAYERS,'assertion_count':len(assertions),'assertions':assertions,'limitations':'Six positives use retained actual native observations with deliberately synthetic numeric layer IDs from the original file table. This exercises the new checker and exact composite label, not native GetLayer execution or retrospective001 qualification.'}
(OUT/'amendment-review.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'passed':True,'assertions':len(assertions),'old_run_unchanged':True,'native_execution':False}))
