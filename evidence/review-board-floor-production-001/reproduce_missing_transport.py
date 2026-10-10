"""Reproduce R2 using a copied synthetic fixture; no native execution."""
from pathlib import Path
import sys,json
review=Path(__file__).resolve().parent;snap=review/'snapshot-002'
sys.path[:0]=[str(snap),str(snap/'tests')]
import test_board_floor_policy as test
case=test.FloorReceipt('test_complete_synthetic_floor_receipt');case.setUp()
try:
    result=case.check()
    print(json.dumps({'check_result':result,'retained':{name:(case.out/name).exists() for name in ['routes.ses','imported.kicad_pcb','source-drc.json','source-drc-binding.json','refill-drc.json','refill-drc-binding.json','refill/fixture.kicad_pcb']},'argv':{stage['name']:stage['argv'] for stage in case.data['steps'] if stage['name'] in {'source-drc','refill-drc'}}},indent=2))
finally:case.doCleanups()
