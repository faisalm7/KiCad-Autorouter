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

CLASS_SOURCE='BOARD.GetNetsByName -> NETINFO_ITEM.GetNetClassSlow'
CLASS_MEANING='Net metadata class preference; not a pad-local, own-clearance, or pairwise rule result.'

def clearances(board,pcbnew,*,api_types=None):
    # Use the same str(wxString) convention as qualified floor_context.collect.
    # Actual003 did not record whether its strict key or code type guard failed.
    # Codes/clearances remain primitive integers; no optional/SWIG coercion.
    classes={};codes=set();types=[] if api_types is None else api_types
    for raw_name,net in board.GetNetsByName().items():
        if len(types)>=fc.LIMITS['nets']:raise ValueError('native net metadata population bound')
        code=net.GetNetCode()
        raw_types={'key':type(raw_name).__name__,'netcode':type(code).__name__}
        observed={'raw_return_types':raw_types,'status':'pending'};types.append(observed)
        if type(code) is not int:raise ValueError('native netcode type differs: '+type(code).__name__)
        observed['netcode']=code
        if code<=0:
            observed['status']='skipped_nonpositive';continue
        name=str(raw_name);observed['name']=name
        if not name:
            observed['status']='skipped_empty_name';continue
        if name in classes or code in codes:raise ValueError('native net metadata identity differs')
        cls=net.GetNetClassSlow();raw_types['class_object']=type(cls).__name__
        raw_label=cls.GetName();raw_types['class_label']=type(raw_label).__name__
        label=str(raw_label);clearance=cls.GetClearance();raw_types['class_clearance']=type(clearance).__name__
        if not label or type(clearance) is not int or not 0<=clearance<=10**9:
            raise ValueError('native assigned netclass metadata unsupported; label type='+type(raw_label).__name__+'; clearance type='+type(clearance).__name__)
        classes[name]={'netcode':code,'netclass':label,'class_clearance_nm':clearance,
                       'net_metadata_return_types':dict(raw_types)};codes.add(code)
        observed.update(status='observed',netclass=label)
    rows=[]
    for pad in board.GetPads():
        if len(rows)>=512:raise ValueError('native pad bound')
        own=[]
        for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')):
            if not pad.IsOnLayer(layer):continue
            value=pad.GetOwnClearance(layer)
            if type(value) is not int or not 0<=value<=10**9:raise ValueError('own-clearance integer/range unsupported')
            own.append({'layer':name,'value_nm':value})
        fp=pad.GetParentFootprint();raw_name=pad.GetNetname();code=pad.GetNetCode()
        if type(code) is not int:raise ValueError('native pad netcode type differs: '+type(code).__name__+'; name type='+type(raw_name).__name__)
        name=str(raw_name)
        if name:
            metadata=classes.get(name)
            if metadata is None or metadata['netcode']!=code:raise ValueError('assigned pad net metadata differs')
            status='observed'
        else:
            if code!=0:raise ValueError('netless pad netcode differs')
            metadata={'netcode':0,'netclass':None,'class_clearance_nm':None,'net_metadata_return_types':None};status='unavailable_netless'
        rows.append({'uuid':str(pad.m_Uuid.AsString()),'reference':str(fp.GetReference()),'number':str(pad.GetNumber()),
            'net':name,**metadata,'pad_net_return_types':{'name':type(raw_name).__name__,'netcode':type(code).__name__},
            'class_metadata':{'status':status,'source':CLASS_SOURCE,'meaning':CLASS_MEANING},
            'own':own,'pad_local':optional(pad.GetLocalClearance),'footprint_local':optional(fp.GetLocalClearance),
            'pad_override':optional(lambda:pad.GetClearanceOverrides(None))})
    if len(rows)!=247 or len({r['uuid'] for r in rows})!=247:raise ValueError('original pad identity population differs')
    return sorted(rows,key=lambda r:r['uuid'])

OBSERVATION_SCOPE='Same LoadBoard own/local/class queries; initialization success and pairwise rule enforcement are unqualified.'

def observation_reference(observed):
    # Keep full rows/type observations in the bounded sidecar. Binding a compact
    # reference avoids duplicating them in floor_context's existing1MiB output.
    raw=(json.dumps(observed,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode()
    return {k:observed[k] for k in ('scope','initialization_qualified','pairwise_rules_qualified','drc_report_executed')} | {
        'observation_sha256':hashlib.sha256(raw).hexdigest()}

def callback(diagnostic):
    if diagnostic.exists() or diagnostic.is_symlink():raise ValueError('fresh clearance observation required')
    state={};calls=0
    def save():
        raw=(json.dumps(state,sort_keys=True,allow_nan=False)+'\n').encode()
        if len(raw)>2*1024**2:raise ValueError('clearance observation bound')
        partial=diagnostic.with_suffix('.json.partial');partial.write_bytes(raw);partial.replace(diagnostic)
    def observe(board,pcbnew):
        nonlocal calls
        if calls>=2:raise ValueError('exactly two export observations allowed')
        stage=('before_export','after_export')[calls];calls+=1
        observed={'scope':OBSERVATION_SCOPE,'initialization_qualified':False,'pairwise_rules_qualified':False,
                  'drc_report_executed':False,'api_types':[]}
        state[stage]=observed
        try:
            observed['rows']=clearances(board,pcbnew,api_types=observed['api_types']);save()
            geometry=original.observe(board,pcbnew)
        except Exception as exc:
            observed['error_type']=type(exc).__name__;save();raise
        # No WriteDRCReport: actual004 crashed in that call. LoadBoard's cached
        # InitEngine source catches exceptions; its success is not inferred.
        return {**geometry,'clearance_observation':observation_reference(observed)}
    return observe

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=5:raise ValueError('source/context/DSN/custom/clearance-observation required')
    source,context,dsn,custom,diagnostic=map(Path,args)
    if diagnostic.parent!=context.parent or diagnostic in (context,dsn,custom) or diagnostic.exists() or diagnostic.is_symlink():
        raise ValueError('fresh distinct adjacent clearance observation required')
    fc.collect('export',source,context,dsn,observation_output=custom,observer=callback(diagnostic))

if __name__=='__main__':main()
