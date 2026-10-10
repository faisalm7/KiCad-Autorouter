"""Pinned-Python nonsaving same-load intent observation; no DSN or routing."""
import hashlib,json,sys
from pathlib import Path
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/floor_context.py').is_file() and (p/'toolchain.lock.json').is_file())
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter import floor_context as fc,placement_clearance as io
LIMIT=20*1024*1024

def integer(v):
    if type(v) is not int or abs(v)>10**10:raise ValueError('native integer type/range differs')
    return v

def boolean(v):
    if type(v) is not bool:raise ValueError('native Boolean differs')
    return v

def point(v):return [integer(v.x),integer(v.y)]
def inventory(path):return io.inventory(path,max_bytes=LIMIT,max_files=2048,max_entries=4096)
def digest(path):return hashlib.sha256(io.read_bytes(path,LIMIT)).hexdigest()

def observe(native,pcbnew):
    modes={int(getattr(pcbnew,'PAD_DRILL_POST_MACHINING_MODE_'+name)):name for name in ('UNKNOWN','NOT_POST_MACHINED','COUNTERBORE','COUNTERSINK')}
    pads=[];footprints=[];routes=[];nets=[];texts=[]
    for fp in native.GetFootprints():
        if len(footprints)>=4:raise ValueError('footprint cap')
        footprints.append({'uuid':str(fp.m_Uuid.AsString()),'reference':str(fp.GetReference()),'position_nm':point(fp.GetPosition()),'layer':str(pcbnew.LayerName(fp.GetLayer()))})
    for pad in native.GetPads():
        if len(pads)>=4:raise ValueError('pad cap')
        if pad.GetShape(pcbnew.F_Cu)!=pcbnew.PAD_SHAPE_CIRCLE or pad.GetAttribute()!=pcbnew.PAD_ATTRIB_PTH:raise ValueError('ordinary circular PTH fixture required')
        post={}
        for side in ('Front','Back'):
            mode=integer(int(getattr(pad,'Get'+side+'PostMachiningMode')()))
            if mode not in modes:raise ValueError('unknown native machining enum')
            post[side.lower()]={'mode':modes[mode],'mode_value':mode,
                'size_nm':integer(getattr(pad,'Get'+side+'PostMachiningSize')()),'depth_nm':integer(getattr(pad,'Get'+side+'PostMachiningDepth')()),
                'angle_decidegrees':integer(getattr(pad,'Get'+side+'PostMachiningAngle')())}
        pads.append({'uuid':str(pad.m_Uuid.AsString()),'footprint_uuid':str(pad.GetParentFootprint().m_Uuid.AsString()),'reference':str(pad.GetParentFootprint().GetReference()),
            'number':str(pad.GetNumber()),'net':str(pad.GetNetname()),'position_nm':point(pad.GetPosition()),'size_nm':point(pad.GetSize(pcbnew.F_Cu)),
            'drill_nm':point(pad.GetDrillSize()),'layers':[name for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if pad.IsOnLayer(layer)],
            'post_machining':post,'affected_layers':[name for layer,name in ((pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')) if boolean(pad.IsBackdrilledOrPostMachined(layer))]})
    for track in native.GetTracks():
        if len(routes)>=2 or isinstance(track,(pcbnew.PCB_VIA,pcbnew.PCB_ARC)):raise ValueError('two straight tracks only')
        routes.append({'uuid':str(track.m_Uuid.AsString()),'net':str(track.GetNetname()),'width_nm':integer(track.GetWidth()),
            'start_nm':point(track.GetStart()),'end_nm':point(track.GetEnd()),'layer':str(pcbnew.LayerName(track.GetLayer()))})
    for name,net in native.GetNetsByName().items():
        if not str(name) or net.GetNetCode()<=0:continue
        if len(nets)>=2:raise ValueError('net cap')
        cls=net.GetNetClassSlow();nets.append({'name':str(name),'netcode':integer(net.GetNetCode()),'class':str(cls.GetName()),
            'width_nm':integer(cls.GetTrackWidth()),'clearance_nm':integer(cls.GetClearance()),'via_diameter_nm':integer(cls.GetViaDiameter()),'via_drill_nm':integer(cls.GetViaDrill()),
            'tuning_profile':str(cls.GetTuningProfile()),'has_tuning_profile':boolean(cls.HasTuningProfile())})
    def graphics(items,parent):
        count=0
        for item in items:
            count+=1
            if count>32:raise ValueError('drawing census cap')
            if item.Type()==pcbnew.PCB_TEXT_T:
                texts.append({'uuid':str(item.m_Uuid.AsString()),'text':str(item.GetText()),'layer':str(pcbnew.LayerName(item.GetLayer())),
                    'layer_id':integer(int(item.GetLayer())),'parent':parent})
    graphics(native.GetDrawings(),'board')
    for fp in native.GetFootprints():graphics(fp.GraphicalItems(),'footprint')
    if (len(pads),len(footprints),len(routes),len(nets),len(texts))!=(4,4,2,2,2):raise ValueError('fixed native census differs')
    if native.GetAreaCount()!=0:raise ValueError('fixture zones unexpected')
    settings=native.GetDesignSettings()
    return {'pads':sorted(pads,key=lambda x:x['uuid']),'footprints':sorted(footprints,key=lambda x:x['uuid']),
        'routes':sorted(routes,key=lambda x:x['uuid']),'nets':sorted(nets,key=lambda x:x['name']),'texts':sorted(texts,key=lambda x:x['uuid']),
        'floors_nm':{key:integer(getattr(settings,attr)) for key,attr in fc.FLOORS.items()}}

def collect(source,output):
    source,output=map(fc.canonical_path,(source,output));project=source.with_suffix('.kicad_pro')
    if source.parent.parent!=output.parent or output.exists() or not project.is_file():raise ValueError('fresh complete run-local paths required')
    before=inventory(source.parent)
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.0':raise ValueError('native version changed')
    native=pcbnew.LoadBoard(str(source))
    if not native or native.GetCopperLayerCount()!=2:raise ValueError('two copper layers required')
    native.SynchronizeNetsAndNetClasses(False)
    data=observe(native,pcbnew)
    after=inventory(source.parent)
    if after!=before:raise ValueError('native observer changed input project')
    result={'schema':1,'native_version':'10.0.0','units':'integer nanometres','source':str(source),'board_sha256':digest(source),'project_sha256':digest(project),
        'input_hashes_before':before,'input_hashes_after':after,'same_loaded_board':True,'board_saved':False,'dsn_exported':False,'routing_accepted':False,
        'schematic_parity_qualified':False,**data}
    raw=json.dumps(result,indent=2,allow_nan=False)+'\n'
    if len(raw.encode())>1024*1024:raise ValueError('observation cap')
    with output.open('x') as stream:stream.write(raw)
if __name__=='__main__':collect(*sys.argv[1:])
