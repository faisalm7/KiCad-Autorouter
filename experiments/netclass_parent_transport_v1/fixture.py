"""Deterministic owned scalar-parent transport controls; no native claim."""
import copy,hashlib,json,uuid
from pathlib import Path
from autorouter import sexpr as sx,pipeline as p
from experiments.licensed_acquisition_v1 import fetch as io

ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
SEED='tests/fixtures/board-floor'
NS=uuid.UUID('5eceb4ac-5a96-499e-9fc3-87a59a6a9804')
PINS={
 'fixture.kicad_pcb':(6103,'dc396dfab9dfbd51a0d75cc8d8457b91c3dbac55358c0f5f84dca83dea97ee38'),
 'fixture.kicad_pro':(15273,'ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538'),
 'PROVENANCE.md':(1249,'5fc68baee38443283014e7f8d7a81ef08cce191e7944206c5678d51ede824dea'),
 '_licenses/LICENSE.README':(2386,'837b45ba5235fd506f60f906b2f68820ccb16a154568eac19f5d3615cb9ee05d'),
 '_licenses/LICENSE.CC-BY-SA-4.0':(15164,'00ba11b9a22d453aed299954eaca389d8efef441a4673d84e2dc4ae10ebc7ca5'),
}
PAIRS=(('POWER','/PWR_PAIR','10','F.Cu','B.Cu'),('SIGNAL','/SIG_PAIR','20','F.Cu','F.Cu'),('Default','/DEFAULT_PAIR','30','F.Cu','F.Cu'))

def uid(name):return str(uuid.uuid5(NS,name))
def digest(raw):return hashlib.sha256(raw).hexdigest()

def fixture(tree,project,*,protected=False):
    """Derive owned geometry and classes without mutating either seed input."""
    if type(protected) is not bool:raise ValueError('explicit protected boolean required')
    t=copy.deepcopy(tree);pro=copy.deepcopy(project)
    t[:]=[n for n in t if not isinstance(n,list) or not n or n[0] not in {'footprint','zone','net',*p.ROUTES}]
    for pair,(_,net,y,left,right) in enumerate(PAIRS):
        for side,(x,layer) in enumerate((('10',left),('40',right))):
            label=str(pair*2+side+1);back=layer=='B.Cu';face='B' if back else 'F'
            props=[]
            for key,value,prop_layer in [('Reference','J'+label,face+'.SilkS'),('Value','netclass_transport_terminal',face+'.Fab'),('Datasheet','',face+'.Fab'),('Description','',face+'.Fab')]:
                effects=['effects',['font',['size','1.27','1.27']]]
                if back:effects.append(['justify','mirror'])
                props.append(['property',json.dumps(key),json.dumps(value),['at','0','0','0'],['layer',json.dumps(prop_layer)],['hide','yes'],['uuid',json.dumps(uid('property:'+label+':'+key))],effects])
            t.append(['footprint','"netclass_transport_terminal"',['layer',json.dumps(layer)],['uuid',json.dumps(uid('fp:'+label))],['at',x,y],*props,
                ['duplicate_pad_numbers_are_jumpers','no'],['pad','"1"','smd','rect',['at','0','0'],['size','2','2'],['uuid',json.dumps(uid('pad:'+label))],['layers',json.dumps(layer),json.dumps(face+'.Paste'),json.dumps(face+'.Mask')],['net',json.dumps(net)]],['embedded_fonts','no'],['attr','smd']])
    if protected:
        t.append(['segment',['start','10','10'],['end','15','10'],['width','0.6'],['layer','"F.Cu"'],['net','"/PWR_PAIR"'],['uuid',json.dumps(uid('protected-power-track'))],['locked','yes']])
    default=copy.deepcopy(pro['net_settings']['classes'][0])
    default.update(name='Default',priority=2147483647,track_width=0.4,clearance=0.35,via_diameter=1.5,via_drill=0.6)
    # Other dimensions intentionally unspecified in the nondefault classes.
    pro['net_settings']['classes']=[default,{'name':'POWER','priority':1,'track_width':0.6,'clearance':0.35,'via_diameter':1.5,'via_drill':0.6},
        {'name':'SIGNAL','priority':0,'track_width':0.5,'clearance':0.35,'via_diameter':1.5,'via_drill':0.6}]
    pro['net_settings']['netclass_assignments']=None
    pro['net_settings']['netclass_patterns']=[{'netclass':'POWER','pattern':'/PWR_*'},{'netclass':'SIGNAL','pattern':'/SIG_*'}]
    return t,pro

def prepare(*,protected=False):
    """Read pinned seeds; return (notice-bearing relative byte map, recipe)."""
    source=io.contained(ROOT,ROOT/io.safe(SEED));files={}
    for name,(size,sha) in PINS.items():
        raw=io.bounded(io.contained(source,source/io.safe(name)),cap=size)
        if len(raw)!=size or digest(raw)!=sha:raise ValueError('stale board-floor seed: '+name)
        files[name]=raw
    original=sx.parse(files['fixture.kicad_pcb'].decode());project=io.decode(files['fixture.kicad_pro'])
    tree,pro=fixture(original,project,protected=protected)
    files['fixture.kicad_pcb']=(sx.dump(tree)+'\n').encode()
    files['fixture.kicad_pro']=(json.dumps(pro,indent=2)+'\n').encode()
    recipe={'schema':1,'recipe':'owned-netclass-parent-transport-v1','variant':'protected' if protected else 'unprotected',
        'seed':SEED,'seed_files':{n:{'bytes':b,'sha256':h} for n,(b,h) in PINS.items()},
        'attribution':{'geometry':'owned project GPL-3.0 derivative of board-floor geometry','settings':'derived KiCad multichannel demo CC-BY-SA-4.0; original notices retained byte-exact'},
        'schematic':{'available':False,'path':None,'parity_unavailable':True},
        'geometry_changes':'replace four seed terminals with three isolated pad pairs; no zones or advanced features; optional original locked POWER segment',
        'project_changes':['net_settings.classes','net_settings.netclass_assignments','net_settings.netclass_patterns'],
        'source_floors':copy.deepcopy(project['board']['design_settings']['rules']),
        'classes':copy.deepcopy(pro['net_settings']['classes']),'patterns':copy.deepcopy(pro['net_settings']['netclass_patterns']),
        'pairs':[{'class':cls,'net':net,'positions_mm':[[10,int(y)],[40,int(y)]],'layers':[a,b]} for cls,net,y,a,b in PAIRS],
        'requires_power_layer_transition':True,'native_composite_names_expected_not_observed':['POWER,Default','SIGNAL,Default'],
        'protected_route':{'uuid':uid('protected-power-track'),'net':'/PWR_PAIR','length_mm':5,'width_mm':0.6,'layer':'F.Cu'} if protected else None,
        'immutable_geometry_sha256':digest(sx.dump(p.immutable(tree)).encode()),
        'files':{n:{'bytes':len(raw),'sha256':digest(raw)} for n,raw in files.items()},'native_accepted':False}
    return files,recipe
