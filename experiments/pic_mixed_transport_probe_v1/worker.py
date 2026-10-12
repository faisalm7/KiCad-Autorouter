"""Same-load original PIC observation; no saving, routing or acceptance."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import floor_context as fc
from experiments.pic_custom_observer_v1 import worker as original

def optional(call):
    """No SWIG pointer/repr/int coercion is evidence of optional conversion."""
    try:value=call()
    except Exception as exc:return {'status':'unsupported','error_type':type(exc).__name__}
    if value is None:return {'status':'observed','value_nm':None}
    if type(value) is int and 0<=value<=10**9:return {'status':'observed','value_nm':value}
    return {'status':'unsupported','return_type':type(value).__name__}

def clearances(board,pcbnew):
    rows=[]
    for pad in board.GetPads():
        if len(rows)>=512:raise ValueError('native pad bound')
        own=[]
        for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')):
            if not pad.IsOnLayer(layer):continue
            value=pad.GetOwnClearance(layer)
            if type(value) is not int or not 0<=value<=10**9:raise ValueError('own-clearance integer/range unsupported')
            own.append({'layer':name,'value_nm':value})
        fp=pad.GetParentFootprint();nc=pad.GetNetClassSlow()
        rows.append({'uuid':str(pad.m_Uuid.AsString()),'reference':str(fp.GetReference()),'number':str(pad.GetNumber()),
            'net':str(pad.GetNetname()),'netclass':str(nc.GetName()),'class_clearance_nm':int(nc.GetClearance()),
            'own':own,'pad_local':optional(pad.GetLocalClearance),'footprint_local':optional(fp.GetLocalClearance),
            'pad_override':optional(lambda:pad.GetClearanceOverrides(None))})
    if len(rows)!=247 or len({r['uuid'] for r in rows})!=247:raise ValueError('original pad identity population differs')
    return sorted(rows,key=lambda r:r['uuid'])

def callback(report):
    state={}
    diagnostic=report.with_name('clearance-initialization.json')
    if diagnostic.exists() or diagnostic.is_symlink():raise ValueError('fresh initialization observation required')
    def save():
        raw=(json.dumps(state,sort_keys=True,allow_nan=False)+'\n').encode()
        if len(raw)>2*1024**2:raise ValueError('initialization observation bound')
        partial=diagnostic.with_suffix('.json.partial');partial.write_bytes(raw);partial.replace(diagnostic)
    def observe(board,pcbnew):
        if not state:
            try:
                state['pre_initialization']=clearances(board,pcbnew);save()
                # Cached exact helper source explicitly calls InitEngine before RunTests.
                result=pcbnew.WriteDRCReport(board,str(report),pcbnew.EDA_UNITS_MM,True)
                state['initialization_return_type']=type(result).__name__
                state['initialization_returned']=result if type(result) is bool else None;save()
                if type(result) is not bool or result is not True:raise ValueError('explicit same-board DRC initialization/report failed')
                if report.is_symlink() or not report.is_file() or not 0<report.stat().st_size<=2*1024**2:raise ValueError('native initialization report bound')
                raw=report.read_bytes()
                if len(raw)>2*1024**2:raise ValueError('native initialization report growth')
                state.update(report_sha256=hashlib.sha256(raw).hexdigest(),report_bytes=len(raw));save()
            except Exception as exc:
                state['initialization_error_type']=type(exc).__name__;save();raise
        return {**original.observe(board,pcbnew),'clearance_observation':{**state,
            'post_initialization':clearances(board,pcbnew),'pairwise_rules_qualified':False,
            'interpretation':'Own-clearance cache queries only; local optionals may be unsupported. Text report is retained, not a routing acceptance report.'}}
    return observe

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=5:raise ValueError('source/context/DSN/custom/report required')
    source,context,dsn,custom,report=map(Path,args)
    if report.parent!=context.parent or report.exists() or report.is_symlink():raise ValueError('fresh adjacent initialization report required')
    fc.collect('export',source,context,dsn,observation_output=custom,observer=callback(report))

if __name__=='__main__':main()
