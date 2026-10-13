"""Only a synthetic shared Job.drc log/report seam; no native proof."""
from pathlib import Path
import json,subprocess,sys
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
project=HERE/'pure-fixture';project.mkdir()
board=project/'board.kicad_pcb';board.write_text('(kicad_pcb (version 20250120))\n')
board.with_suffix('.kicad_sch').write_text('(kicad_sch (version 20250114))\n');board.with_suffix('.kicad_pro').write_text('{}\n')
job=p.Job(HERE/'pure-job',30)
def emitted(name,argv,allowed=(0,)):
    path=Path(argv[argv.index('--output')+1])
    p.save_json(path,{'$schema':'https://schemas.kicad.org/drc.v1.json','kicad_version':'10.0.0','source':board.name,'violations':[],'unconnected_items':[],'schematic_parity':[],'ignored_checks':[],'included_severities':['error','warning','exclusion']})
    (job.out/(name+'.log')).write_text('Failed to fetch schematic netlist for parity tests.\nFound 0 violations\nFound 0 unconnected items\n')
    return {'exit_code':0,'status':'success','cleanup_complete':True}
with patch.object(job,'step',side_effect=emitted),patch.object(subprocess,'run',side_effect=AssertionError('no process')),patch.object(subprocess,'Popen',side_effect=AssertionError('no process')):
    native=job.drc('drc',board,schematic_parity=True)
result={'schema':1,'synthetic':True,'native_execution':False,'native_reported_unavailability_in_synthetic_log':True,'job_returned':True,'native_accepted':p.native_accepted(native),'declaration':p.parity_declaration(board,p.tree_hash(board.parent)),'native':native,'scope':'Demonstrates unchecked shared Job.drc/report declaration branch; not a valid schematic, actual native skip or complete accepted routing receipt.'}
(HERE/'pure-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,sort_keys=True))
