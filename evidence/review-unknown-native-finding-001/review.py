"""Independent offline scoped review. No native tools, engine or source mutation."""
import ast, copy, hashlib, json, subprocess, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
OUT=Path(__file__).resolve().parent

def read(path):
    path=Path(path)
    assert not path.is_symlink() and path.stat().st_size<8*1024**2
    with path.open('rb') as f: raw=f.read(8*1024**2+1)
    assert len(raw)<=8*1024**2
    return raw

def sha(raw): return hashlib.sha256(raw).hexdigest()
def node(tree,name):return next(n for n in tree.body if getattr(n,'name',None)==name)
def expression(tree,name):
    return next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
def write(path,d):
    with path.open('x') as f:json.dump(d,f,indent=2,sort_keys=True);f.write('\n')

current=read(ROOT/'autorouter/pipeline.py')
old=subprocess.run(['git','show','HEAD:autorouter/pipeline.py'],cwd=ROOT,capture_output=True,check=True,timeout=3).stdout
head=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True,timeout=3).stdout.strip()
a,b=ast.parse(old),ast.parse(current)
checks={name:ast.dump(node(a,name))==ast.dump(node(b,name)) for name in ('parse_report','preflight','native_accepted')}
checks.update({name+'_unchanged':ast.dump(expression(a,name))==ast.dump(expression(b,name)) for name in ('KNOWN_CHECKS','CRITICAL_CHECKS','CRITICAL_FINDINGS')})
assert all(checks.values())
base=json.loads(read(ROOT/'.runs/unknown-native-finding-root-001/before.json'))
mutated=base['mutated_native']; saved=copy.deepcopy(mutated)
assert not p.native_accepted(mutated) and mutated==saved
mutations=[]
for severity in ('error','warning','exclusion'):
    d=copy.deepcopy(mutated);d['findings'][0]['severity']=severity
    previous=copy.deepcopy(d);reasons=p.native_rejection_reasons(d)
    assert any(r.startswith('unknown native finding semantics:')for r in reasons) and d==previous
    mutations.append({'severity':severity,'rejected':True,'native_evidence_unchanged':True,'reasons':reasons})
rows=[]
for name in ('pic-core-placement-regression-001','placement-production-multichannel-001','portfolio-paired-001/C_feedback','thermal-paired-001/C_thermal'):
    receipt=ROOT/'.runs'/name/'result.json';raw=read(receipt);d=json.loads(raw)
    matches=[]
    for f in receipt.parent.glob('*.json'):
        if f.name=='result.json':continue
        data=read(f)
        if sha(data)==d['native_report_sha256']:matches.append(f)
    assert len(matches)==1,(name,matches)
    report=matches[0];reportbytes=read(report)
    derived=p.parse_report(report,Path(d['candidate']).name)
    assert derived==d['native'] and p.native_accepted(derived)
    assert read(report)==reportbytes and read(receipt)==raw
    rows.append({'receipt':str(receipt.relative_to(ROOT)),'receipt_sha256':sha(raw),'native_report':str(report.relative_to(ROOT)),'native_report_sha256':sha(reportbytes),'finding_types':dict(Counter(x['type']for x in derived['findings'])),'counts':{k:derived[k]for k in ('opens','blocking','warnings','exclusions')},'raw_rederived_equal':True,'central_policy_accepts':True,'unknown_types':sorted({x['type']for x in derived['findings']}-p.KNOWN_CHECKS-{'padstack_invalid'})})
assert read(ROOT/'autorouter/pipeline.py')==current
write(OUT/'review.json',{'schema':1,'status':'scoped_review_clear','native_executed':False,'engine_executed':False,'full_check_result_repeated':False,'head':head,'pipeline_sha256':sha(current),'prior_committed_pipeline_sha256':sha(old),'ast_compatibility_checks':checks,'before_mutation_receipt_sha256':sha(read(ROOT/'.runs/unknown-native-finding-root-001/before.json')),'mutations':mutations,'accepted_raw_reports':rows,'limitations':['Offline stored-report compatibility only; root owns fresh native validation.','Known project-setting keys are a deliberately conservative allowlist, not exhaustive KiCad finding semantics. Unknown future/other type fails closed.','No source severity key admission or four currently unknown project keys qualification.']})
print(json.dumps({'status':'scoped_review_clear','actual_reports':len(rows),'pipeline_sha256':sha(current)}))
