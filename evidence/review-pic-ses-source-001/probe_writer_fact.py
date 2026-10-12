"""Execute the actual SES branch through its first rejected validation; no workers."""
from pathlib import Path
import ast,hashlib,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d
path=ROOT/'experiments/pic_mixed_transport_probe_v1/driver.py';raw=path.read_bytes();tree=ast.parse(raw)
branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='ses_roundtrip')
writer={'executed':True,'returned':True,'closed':True,'bytes':1,'sha256':'mocked'}
observed={'ses_executed':True,'cases':[{}, {'ses':writer}]};record={};space={'observed':observed,'record':record,'expected':{},'transport':d.transport}
with patch.object(d.transport,'validate_local',side_effect=ValueError('controlled later correspondence failure')):
 try:exec(compile(ast.Module(body=branch.body,type_ignores=[]),str(path),'exec'),space)
 except ValueError as exc:reason=str(exc)
 else:raise AssertionError('expected controlled rejection')
assert record['ses_executed'] is True and record['writer']==writer
assert path.read_bytes()==raw
result={'passed':True,'driver_sha256':hashlib.sha256(raw).hexdigest(),'scope':'Actual SES branch, first validator mocked to fail; no full controller/native/JVM execution','observed_writer_fact_retained':record,'rejection':reason}
(HERE/'writer-fact.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
