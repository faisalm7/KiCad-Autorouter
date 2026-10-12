from pathlib import Path
import time,resource
start=time.monotonic();cpu0=time.process_time()
import hashlib,json,sys
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root));sys.path.insert(0,str(root/'experiments/custom_pad_area_probe_v1'));sys.path.insert(0,str(root/'experiments/pic_custom_observer_v1'))
from experiments.pic_mixed_transport_probe_v1 import transport
from experiments.pic_custom_observer_v1 import mapping,driver as original
from autorouter import sexpr as sx,placement_clearance as io
source=root/'.runs/pic-mixed-transport-probe-005';out=root/'.runs/pic-mixed-transport-005-reanalysis-001';out.mkdir()
raw=io.inventory(source,max_bytes=64*1024**2,max_files=2000,max_entries=4000)
summary=json.loads((source/'summary.json').read_text());assert summary['status']=='failed'
assert all(raw.get(k)==v for k,v in summary['frozen_evidence'].items())
source_hashes,_=original.source_binding();assert source_hashes==summary['runtime']['original']
board=source/'observe-input'/original.SOURCE.name
notes=mapping.source_notes(sx.read(board),json.loads(board.with_suffix('.kicad_pro').read_text()))
derived,expected=transport.derive((source/'native.dsn').read_bytes(),json.loads((source/'context.json').read_text()),json.loads((source/'custom.json').read_text()),notes)
assert derived==(source/'mixed.dsn').read_bytes()
old=json.loads((source/'expectations.json').read_text());diff=[]
for name,row in expected['nets'].items():
 want=old['nets'][name]
 assert {k:v for k,v in row.items() if k not in ('class','dsn_class')}=={k:v for k,v in want.items() if k!='class'}
 assert row['dsn_class']==want['class']
 assert row['class']==('default' if want['class']=='kicad_default' else want['class'])
 if row['class']!=want['class']:diff.append(name)
assert len(diff)==109
assert {k:v for k,v in expected.items() if k!='nets'}=={k:v for k,v in old.items() if k!='nets'}
comparisons=transport.validate(json.loads((source/'observations.json').read_text()),expected)
assert all(r['observed'] for r in comparisons)
assert io.inventory(source,max_bytes=64*1024**2,max_files=2000,max_entries=4000)==raw
assert original.source_binding()[0]==source_hashes
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'schema':1,'analysis':'exposed posthoc class-namespace correction, not a new native run',
 'original_status':'failed','original_summary_sha256':sha(source/'summary.json'),'original_native_head':summary['runtime']['git']['head'],
 'original_native_wall_seconds':summary['wall_seconds'],'original_native_full_cpu_seconds':summary['total_cpu_seconds'],
 'analysis_source_sha256':sha(Path(__file__)),'transport_sha256':sha(Path(transport.__file__)),
 'input_inventory':raw,'original_source_unchanged':True,'raw_run_unchanged':True,
 'correction':'Native Default -> unchanged DSN kicad_default -> pinned imported runtime default; POWER unchanged. Only expectation namespace changes.',
 'changed_default_labels':len(diff),'derived_dsn_unchanged':True,'comparison':comparisons,
 'routing_executed':False,'ses_executed':False,'native_executed':False,'initialized_rules_qualified':False,
 'mixed_clearance_equivalence_qualified':False,'routing_accepted':False,'production_support_qualified':False,
 'analysis_wall_seconds':time.monotonic()-start,'analysis_cpu_seconds':time.process_time()-cpu0,
 'limitations':'All original failures and287engine fixed-clearance warnings remain. Reciprocal anchor contacts do not establish pairwise/local clearance equivalence, exact trace union or SES survival.'}
for name,value in [('expectations.json',expected),('analysis.json',record)]:
 (out/name).write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ('original_status','changed_default_labels','derived_dsn_unchanged','analysis_wall_seconds','analysis_cpu_seconds')}))
