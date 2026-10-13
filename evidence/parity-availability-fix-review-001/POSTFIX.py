"""Two provenance-dispatch seams only; not complete native receipts."""
from pathlib import Path
import inspect,json,sys
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
row={'scope':'whole_board_unlocked_routing','source':'/owned/board.kicad_pcb','source_hashes':{'board.kicad_sch':'bound'},'schematic_parity':'not checked'}
cases={}
for name,code in [('current-marker',b'fields.check_availability(self.out,name,result'),('historical-no-marker',b'pre-availability worker fixture')]:
    directory=HERE/name;(directory/'code').mkdir(parents=True);(directory/'code/pipeline.py').write_bytes(code)
    try:value=p.selected_parity_required(row,directory);cases[name]={'required':value,'rejected':None}
    except p.Rejected as exc:cases[name]={'required':None,'rejected':str(exc)}
assert 'requires schematic parity declaration' in cases['current-marker']['rejected']
assert cases['historical-no-marker']['required'] is False
(HERE/'selected_parity_required-fixed.py.txt').write_text(inspect.getsource(p.selected_parity_required))
result={'schema':1,'native_execution':False,'cases':cases,'final_pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'final_field_evidence_sha256':p.sha(ROOT/'autorouter/schematic_field_evidence.py'),'scope':'Retained-code marker policy seams; synthetic marker files do not qualify complete native receipts.'}
(HERE/'POSTFIX.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
