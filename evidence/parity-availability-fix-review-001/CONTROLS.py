"""Narrow pure/read-only availability and declaration controls; no native/Git."""
from pathlib import Path
import copy,hashlib,inspect,json,subprocess,sys
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,schematic_field_evidence as e,floor_route as f,placement_clearance as pc
def require(value,message):
    if not value:raise ValueError(message)
def forbidden(*args,**kwargs):raise AssertionError('review cannot execute a subprocess/native/Git')
initial={'pipeline_sha256':p.sha(ROOT/'autorouter/pipeline.py'),'field_evidence_sha256':p.sha(ROOT/'autorouter/schematic_field_evidence.py')}
(HERE/'selected_parity_required-reviewed.py.txt').write_text(inspect.getsource(p.selected_parity_required))
directory=HERE/'synthetic-log';directory.mkdir();log=directory/'drc.log';log.write_text('Found 0 schematic parity issues\n')
process={'argv':['drc','--schematic-parity'],'log':str(log),'log_bytes':log.stat().st_size,'log_truncated':False};raw={'schematic_parity':[]}
with patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden):
    e.check_availability(directory,'drc',process,raw,required=True)
    missing=copy.deepcopy(process);missing['argv']=['drc']
    try:e.check_availability(directory,'drc',missing,raw,required=True)
    except p.Rejected as exc:flag_rejection=str(exc)
    else:raise ValueError('required flag silently lost')
    # Policy seam only: never fabricate a complete accepted native receipt.
    row={'scope':'whole_board_unlocked_routing','source':str(directory/'board.kicad_pcb'),'source_hashes':{'board.kicad_sch':'captured'},'schematic_parity':'checked by final native DRC','tools':{'implementation_sha256':{'autorouter/pipeline.py':initial['pipeline_sha256']}}}
    require(p.selected_parity_required(row) is True,'checked declaration not required')
    downgraded=copy.deepcopy(row);downgraded['schematic_parity']='not checked'
    historical_dispatch=p.selected_parity_required(downgraded)
    negative=ROOT/'.runs/parity-unavailable-native-002';record=f.read_json(negative/'result.json');job=negative/'job';report=f.read_json(job/'parity-unavailable-drc.json');step=record['steps'][0]
    before=pc.inventory(negative,with_directories=True)
    require(p.sha(job/'parity-unavailable-drc.json')==record['native_report_sha256'] and p.sha(job/'parity-unavailable-drc.log')==record['native_log_sha256'],'actual negative changed')
    require([record['native_counts'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,5,0],'actual skipped report counts differ')
    require(record['production_job_returned'] is True and record['production_native_accepted'] is True and record['passed'] is False,'original demonstrated failure rewritten')
    require(step['log_bytes']==len(pc.read_bytes(job/'parity-unavailable-drc.log')) and step['cleanup_complete'] is True,'actual negative process/log differs')
    try:e.check_availability(job,'parity-unavailable-drc',step,report,required=True)
    except p.Rejected as exc:actual_rejection=str(exc)
    else:raise ValueError('actual skipped parity accepted by fixed helper')
    require('skipped or unavailable' in actual_rejection,'actual native refused for another reason')
    binding=f.read_json(job/'parity-unavailable-drc-binding.json');board=Path(binding['input'])
    p.check_drc_project(binding['before'],binding['after'],board.name)
    require(p.tree_hash(board.parent)==binding['after'] and board.with_suffix('.kicad_sch').name in binding['before'],'complete restored native input differs')
    positives={}
    for relative in ('.runs/nus-native-paired-002/run/B1/result.json','.runs/nus-native-paired-002/run/C_feedback/result.json','.runs/nus-b2-portfolio-continuation-001/portfolio/03-via_high/result.json'):
        positives[relative]=p.check_result(ROOT/relative)
    require(pc.inventory(negative,with_directories=True)==before,'review mutated actual negative')
result={'schema':1,'native_execution':False,'subprocess_execution':False,'source_bindings_before':initial,'required_flag_rejection':flag_rejection,'complete_schematic_historical_declaration_downgrade':{'checked_required':True,'mutated_not_checked_required':historical_dispatch,'scope':'Policy dispatch seam only; current implementation marker supplied, no complete accepted-result bypass asserted.'},'actual_native_negative_rejection':actual_rejection,'actual_negative_hashes':{key:record[key] for key in ('native_report_sha256','native_log_sha256')},'existing_actual_positives_readback':positives,'actual_negative_unchanged':True}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
