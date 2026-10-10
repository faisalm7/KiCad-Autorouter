"""Read-only current source gate observations. Native support remains unqualified."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p
HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
core={f:sha(ROOT/f)for f in ('autorouter/pipeline.py','autorouter/sexpr.py','autorouter/netclass.py')}
rows=[]
for suffix in ('ideal-diode/Hardware/SparkFun_Ideal_Diode_Breakout.kicad_pcb','hstx-pth/Hardware/SparkFun_HSTX_PTH_Breakout.kicad_pcb','olimex-ice40-dio/ICE40-DIO_Rev_A.kicad_pcb'):
    board=ROOT/'.data/expansion004'/suffix;project=board.parent
    before=p.tree_hash(project)
    try:p.preflight(board);status='preflight_eligible';reason=None
    except p.Rejected as exc:status='unsupported';reason=str(exc)
    assert p.tree_hash(project)==before
    rows.append({'board':str(board.relative_to(ROOT)),'board_sha256':sha(board),'project_file_sha256':{n:v for n,v in before.items()if n.endswith(('.pro','.kicad_pro','.kicad_dru'))},'status':status,'exact_reason':reason,'project_bytes_unchanged':True})
assert core=={f:sha(ROOT/f)for f in core}
with (HERE/'current-preflight-001.json').open('x') as f:
    json.dump({'schema':1,'native_executed':False,'engine_executed':False,'no_source_changes':True,'source_hashes':core,'boards':rows,'scope':'Current production preflight observed verbatim; dependency/rights/ancestry gaps remain independent; no native eligibility inferred.'},f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps(rows,indent=2))
