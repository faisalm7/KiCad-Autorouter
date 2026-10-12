"""Small saved-byte/mocked metadata falsifiers; never launches KiCad or a JVM."""
from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
sys.path[:0]=[str(ROOT/'experiments/pic_mixed_transport_probe_v1'),str(ROOT)]
import test_local_transport as tests
import test_draft
import transport
d=test_draft.driver
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source={str(p.relative_to(ROOT)):sha(p) for p in d.source_paths()}
tests.LocalTransport.setUpClass();test=tests.LocalTransport()
semantic=[]
for change in ('unchanged','census','failed_tree_entry','wrong_target_audit','wrong_row_audit'):
    data=test.synthetic()
    for row in data['cases']:
        if change=='census':row['state']['census']['clearance_classes']=5
        if change=='failed_tree_entry':row['local_override']['tree_entry_checks']=[{'id':row['local_override']['changed_item_ids'][0],'valid':False}]
        if change=='wrong_target_audit':row['local_override']['targets']=[{'reference':'wrong','number':'9','net':'other','pin_id':-1,'area_id':-2}]
        if change=='wrong_row_audit':row['local_override']['raw_row']=[{'other_class':3,'layer':0,'raw_board_units':2800,'raw_um':280.0}]
    try:
        result=transport.validate_local(data,test.expected);accepted=all(x['observed'] for x in result);error=None
    except Exception as exc:accepted=False;error=type(exc).__name__+': '+str(exc)
    semantic.append({'change':change,'accepted':accepted,'error':error})

scratch=OUT/'runtime-002';scratch.mkdir()
helper=scratch/'helper.py';tool=scratch/'tool';original=scratch/'original'
cached=scratch/'.runs/pic-mixed-transport-probe-005';cached.mkdir(parents=True);(cached/'observed').write_text('fixed')
protocol={'tools':{'python':{'path':str(tool),'bytes':1}},'basis':{},'mode':'local250','reuse_native':'.runs/pic-mixed-transport-probe-005'}
real_inventory=d.inventory
def source_binding():return {'original':sha(original)},original.stat().st_size
runtime=[]
for mutation in (None,'helper','tool','original'):
    for p in (helper,tool,original):p.write_bytes(b'A')
    with ExitStack() as stack:
        stack.enter_context(patch.object(d,'ROOT',scratch))
        stack.enter_context(patch.object(d,'source_paths',lambda:[helper]))
        stack.enter_context(patch.object(d.base,'head_witness',lambda:{'head':'0'*40}))
        stack.enter_context(patch.object(d.original,'source_binding',source_binding))
        baseline=d.runtime(protocol)
        def late_inventory(path):
            result=real_inventory(path)
            if path==cached and mutation is not None:{'helper':helper,'tool':tool,'original':original}[mutation].write_bytes(b'B')
            return result
        stack.enter_context(patch.object(d,'inventory',late_inventory))
        sampled=d.runtime(protocol)
        unchanged=(sampled==baseline)
        runtime.append({'mutation':mutation or 'none','witness_still_equal':unchanged,
            'actual_material_changed':any(p.read_bytes()!=b'A' for p in (helper,tool,original))})
assert source=={str(p.relative_to(ROOT)):sha(p) for p in d.source_paths()}
record={'scope':'Pure checker and real tiny-file metadata probes; no native/JVM/network execution. No actual cached005 data modified.',
    'source_sha256':source,'semantic':semantic,'runtime':runtime,'author_source_unchanged':True}
(OUT/'probe-002.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'semantic':semantic,'runtime':runtime}))
