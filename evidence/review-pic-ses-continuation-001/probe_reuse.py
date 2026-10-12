"""Actual cached-reuse branch with captured records mutated in memory; no workers."""
from pathlib import Path
import ast,copy,hashlib,json,sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from experiments.pic_mixed_transport_probe_v1 import driver as d
path=Path(d.__file__);code=path.read_bytes();node=next(n for n in ast.walk(ast.parse(code)) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='native_from_ses')
block=compile(ast.Module(body=node.body,type_ignores=[]),str(path),'exec')
protocol=d.base.decode(d.base.content(d.HERE/'SES_NATIVE_PROTOCOL.json'));run=ROOT/protocol['reuse_ses'];inventory=d.inventory(run);raw=d.base.content(run/'summary.json');prior=d.base.decode(raw)
for name,pin in protocol['basis'].items():
 assert d.base.content(ROOT/name,pin['bytes'],digest=True)==pin
before={'original':prior['runtime']['original'],'tools':prior['runtime']['tools'],'cached_ses_inventory':inventory,'sources':{str(d.HERE.relative_to(ROOT)/'MixedClassProbe.java'):d.base.content(d.HERE/'MixedClassProbe.java',digest=True)}}
assert before['tools']=={k:{z:v[z] for z in ('bytes','sha256')} for k,v in protocol['tools'].items()}
expected=d.base.decode(d.base.content(run/'expectations.json'));derived=d.base.content(run/'mixed.dsn');decode=d.base.decode
rows=[]
for variant in ('positive','old_status','old_process','old_cleanup','old_tool','old_java','old_frozen','old_original'):
 altered=copy.deepcopy(prior)
 if variant=='old_status':altered['status']='completed'
 if variant=='old_process':altered['steps'][1]['exit_code']=1
 if variant=='old_cleanup':altered['steps'][1]['cleanup_complete']=False
 if variant=='old_tool':altered['runtime']['tools']['jar']['sha256']='0'*64
 if variant=='old_java':altered['runtime']['sources'][str(d.HERE.relative_to(ROOT)/'MixedClassProbe.java')]['sha256']='0'*64
 if variant=='old_frozen':altered['frozen_evidence']['raw.ses']='0'*64
 if variant=='old_original':altered['runtime']['original']['pic_programmer.kicad_pro']='0'*64
 out=OUT/('reuse-'+variant);out.mkdir();record={}
 env={'ROOT':ROOT,'HERE':d.HERE,'protocol':protocol,'base':d.base,'before':before,'inventory':d.inventory,'derived':derived,'expected':expected,'out':out,'record':record,'capture':lambda:None}
 def altered_decode(data):return copy.deepcopy(altered) if data==raw else decode(data)
 with patch.object(d.base,'decode',altered_decode):
  try:exec(block,env);accepted=True;error=None
  except ValueError as exc:accepted=False;error=str(exc)
 assert accepted==(variant=='positive'),variant
 if accepted:
  assert record['ses_reuse']['new_writer_execution'] is False
  assert record['ses_reuse']['prior_run_wall_seconds']==prior['wall_seconds'] and record['ses_reuse']['prior_run_total_cpu_seconds']==prior['total_cpu_seconds']
  for name in ('observations.json','raw.ses'):assert (out/name).read_bytes()==(run/name).read_bytes()
 rows.append({'case':variant,'reuse_allowed':accepted,'error':error})
assert d.inventory(run)==inventory and path.read_bytes()==code
result={'passed':True,'scope':'Actual cached reuse branch; process records mutated only in memory; no whole controller or native/JVM run','driver_sha256':hashlib.sha256(code).hexdigest(),'protocol_sha256':hashlib.sha256((d.HERE/'SES_NATIVE_PROTOCOL.json').read_bytes()).hexdigest(),'all_protocol_basis_verified':True,'cache_unchanged':True,'cases':rows}
(OUT/'reuse-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
