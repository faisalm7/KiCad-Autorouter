"""Synthetic complete receipt controls only; no native/process/solver execution."""
from pathlib import Path
import copy,hashlib,json,shutil,sys
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,routing_scope as rs,sexpr as sx,adapter as a
OWN=Path(__file__).resolve().parent;run=OWN/'receipt-seam/run';receipt=run/'result.json';scoped=run/'routing-scope-input.dsn';names=['SEL'];data=json.loads(receipt.read_text())
initial={str(x):p.sha(ROOT/x) for x in ['autorouter/pipeline.py','autorouter/routing_scope.py']};good={file:file.read_bytes() for file in [scoped,run/'task.dsn',run/'routing-preferences.json',run/'engine-process.json']};results=[]
def check(label,mutate=None,expected='reject'):
 for file,raw in good.items():file.write_bytes(raw)
 d=copy.deepcopy(data)
 if mutate:mutate(d)
 p.save_json(receipt,d)
 try:
  with patch('subprocess.run',side_effect=AssertionError('forbidden subprocess')),patch('subprocess.Popen',side_effect=AssertionError('forbidden subprocess')):v=p.check_result(receipt)
  outcome='current'
 except (p.Rejected,ValueError,KeyError,FileNotFoundError) as ex:outcome='reject';v={'type':type(ex).__name__,'reason':str(ex)}
 entry={'case':label,'outcome':outcome,'expected':expected,'matched':outcome==expected,'detail':v};results.append(entry);print(json.dumps(entry,sort_keys=True))
check('same stored selected/both-adapter controlling positive',expected='current')
def wrong_rule(d):
 tree=a._parse_dsn(scoped.read_text());row=sx.one(sx.one(tree,'network'),'class');sx.one(sx.one(row,'rule'),'width')[1]='100';scoped.write_bytes(a._dump_dsn(tree).encode());emitted,binding=rs.partition_dsn(scoped.read_bytes(),names);(run/'task.dsn').write_bytes(emitted);d['selected_dsn_binding']=binding;d['task_dsn_sha256']=p.sha(run/'task.dsn');d['adapter_transformations']['output_sha256']=binding['input_sha256']
check('same rehashed adapter width100 versus native200',wrong_rule)
for file,raw in good.items():file.write_bytes(raw)
p.save_json(receipt,data)
p.save_json(OWN/'receipt-width-postfix-results.json',{'native_validation_performed':False,'subprocesses_executed':0,'source_sha256_before':initial,'source_sha256_after':{x:p.sha(ROOT/x) for x in initial},'results':results})
