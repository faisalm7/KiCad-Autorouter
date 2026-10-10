"""Isolated single-Default native export-context qualification; no routing/DRC.

Run from the repository root with --out .runs/NEW_NAME, only after lead review.
Three read/export workers share one 30s wall/CPU diagnostic ceiling. A passing
probe does not qualify transformed DSN, via import, geometry safety or routing.
"""
from __future__ import annotations
import argparse
import copy
import datetime
from decimal import Decimal
import fcntl
import hashlib
import json
from pathlib import Path
import re
import resource
import shutil
import signal
import sys
import time
import uuid

FLOORS = {'min_track_width':'m_TrackMinWidth','min_clearance':'m_MinClearance',
          'min_via_diameter':'m_ViasMinSize','min_through_hole_diameter':'m_MinThroughDrill',
          'min_via_annular_width':'m_ViasMinAnnularWidth'}
CLASS_VALUES = {'width_nm':'track_width','clearance_nm':'clearance',
                'via_diameter_nm':'via_diameter','via_drill_nm':'via_drill'}
PROJECT_SHA='ea1bc47355f707e1c4743af3e1c29e939bb5eaf4621c071bdac3841c43545538'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_worker(board_path,dsn_path,context_path):
    import pcbnew
    board_path,dsn_path,context_path=map(Path,(board_path,dsn_path,context_path))
    if (board_path.parent.name!='native-input' or dsn_path.parent!=board_path.parent.parent or
            context_path.parent!=dsn_path.parent or dsn_path.exists() or context_path.exists()):
        raise ValueError('native worker requires isolated fresh case outputs')
    project=board_path.with_suffix('.kicad_pro')
    before={'board_sha256':digest(board_path),'project_sha256':digest(project) if project.is_file() else None}
    board=pcbnew.LoadBoard(str(board_path))
    if not board or pcbnew.GetBuildVersion()!='10.0.0' or board.GetCopperLayerCount()!=2:
        raise ValueError('requires pinned native10.0.0 and two layers')
    board.SynchronizeNetsAndNetClasses(False)
    settings=board.GetDesignSettings()
    floors={key:getattr(settings,attr) for key,attr in FLOORS.items()}
    if any(type(v) is not int or v<0 for v in floors.values()):raise ValueError('malformed native floor')
    pads=[]
    for pad in board.GetPads():
        layers=[name for layer,name in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if pad.IsOnLayer(layer)]
        pos=pad.GetPosition()
        pads.append({'uuid':str(pad.m_Uuid.AsString()),'reference':str(pad.GetParentFootprint().GetReference()),
                     'number':str(pad.GetNumber()),'netcode':pad.GetNetCode(),'net':str(pad.GetNetname()),
                     'copper_layers':layers,'position_nm':[pos.x,pos.y]})
    counts={}
    for pad in pads:
        if pad['netcode']>0 and pad['copper_layers']:counts[pad['net']]=counts.get(pad['net'],0)+1
    nets=[]
    for name,net in board.GetNetsByName().items():
        if not str(name) or net.GetNetCode()<=0:continue
        cls=net.GetNetClassSlow()
        nets.append({'name':str(name),'netcode':net.GetNetCode(),'class':str(cls.GetName()),
                     'width_nm':cls.GetTrackWidth(),'clearance_nm':cls.GetClearance(),
                     'via_diameter_nm':cls.GetViaDiameter(),'via_drill_nm':cls.GetViaDrill(),
                     'copper_pad_count':counts.get(str(name),0)})
    if not nets or not pcbnew.ExportSpecctraDSN(board,str(dsn_path)):raise ValueError('native DSN export failed')
    after={'board_sha256':digest(board_path),'project_sha256':digest(project) if project.is_file() else None}
    if before!=after:raise ValueError('native export changed board/project')
    context={'context_schema':1,'native_version':pcbnew.GetBuildVersion(),'units':'integer nanometres',
             'source':str(board_path),**before,'dsn_sha256':digest(dsn_path),'floors_nm':floors,
             'nets':sorted(nets,key=lambda r:r['name']),'pads':sorted(pads,key=lambda r:r['uuid']),
             'board_saved':False,'solver_executed':False,'drc_executed':False,
             'routing_accepted':False,'production_support_qualified':False}
    with context_path.open('x') as f:json.dump(context,f,indent=2);f.write('\n')


def nm(value):
    if isinstance(value,bool):raise ValueError('boolean dimension')
    number=Decimal(str(value))*1000000
    if not number.is_finite() or number<0 or number!=number.to_integral_value():raise ValueError('nonintegral dimension')
    return int(number)


def audit_context(context,project,expected_board_sha,expected_project_sha):
    if (context.get('context_schema')!=1 or context.get('native_version')!='10.0.0' or
            context.get('units')!='integer nanometres' or context.get('board_saved') is not False):
        raise ValueError('native context identity mismatch')
    if context.get('board_sha256')!=expected_board_sha or context.get('project_sha256')!=expected_project_sha:
        raise ValueError('missing or different complete original project attachment')
    net_settings=project['net_settings'];classes=net_settings['classes']
    if (len(classes)!=1 or classes[0]['name']!='Default' or net_settings.get('netclass_patterns') or
            net_settings.get('netclass_assignments')):raise ValueError('outside explicit single-Default scope')
    floors={key:nm(project['board']['design_settings']['rules'][key]) for key in FLOORS}
    if context.get('floors_nm')!=floors:raise ValueError('loaded native floors differ from original complete project')
    expected={key:nm(classes[0][value]) for key,value in CLASS_VALUES.items()}
    nets=context.get('nets');pads=context.get('pads')
    if not isinstance(nets,list) or not nets or not isinstance(pads,list):raise ValueError('missing native inventories')
    if len({r['name'] for r in nets})!=len(nets) or len({r['uuid'] for r in pads})!=len(pads):
        raise ValueError('duplicate native identity')
    for row in nets:
        if row['class']!='Default' or any(type(row.get(k)) is not int or row[k]!=v for k,v in expected.items()):
            raise ValueError('native raw class differs from original Default')
        count=sum(p['netcode']>0 and bool(p['copper_layers']) and p['net']==row['name'] for p in pads)
        if row['copper_pad_count']!=count:raise ValueError('native terminal count mismatch')
    return {'passed':True,'raw_class_nm':expected,'native_floors_nm':floors,'native_nets':len(nets),
            'native_pads':len(pads),'below_floor_fields':[key for key,floor in
                [('width_nm','min_track_width'),('clearance_nm','min_clearance'),
                 ('via_diameter_nm','min_via_diameter'),('via_drill_nm','min_through_hole_diameter')]
                if expected[key]<floors[floor]],'routing_accepted':False}


def audit_native_pad_identities(context,task):
    from autorouter import sexpr as sx
    nets={n[1]:sx.unquote(n[2]) for n in sx.children(task,'net') if len(n)==3}
    expected={};references=set()
    for fp in sx.children(task,'footprint'):
        props=[n for n in sx.children(fp,'property') if sx.unquote(n[1])=='Reference']
        if len(props)!=1:raise ValueError('missing/ambiguous original footprint reference')
        ref=sx.unquote(props[0][2])
        if ref in references:raise ValueError('duplicate original footprint reference')
        references.add(ref)
        for pad in sx.children(fp,'pad'):
            uid=sx.unquote(sx.one(pad,'uuid')[1]);net=sx.one(pad,'net')
            name=(sx.unquote(net[2]) if len(net)==3 else nets.get(net[1],sx.unquote(net[1]))) if net else ''
            layers=[sx.unquote(v) for v in sx.one(pad,'layers')[1:]]
            copper=[layer for layer in ('F.Cu','B.Cu') if layer in layers or '*.Cu' in layers]
            if uid in expected:raise ValueError('duplicate original pad UUID')
            expected[uid]={'reference':ref,'number':sx.unquote(pad[1]),'net':name,'copper_layers':copper}
    observed={}
    for pad in context['pads']:
        if pad['uuid'] in observed:raise ValueError('duplicate native pad UUID')
        observed[pad['uuid']]={key:pad[key] for key in ('reference','number','net','copper_layers')}
    if observed!=expected:raise ValueError('native pad identity/net/layer inventory differs from exact task')
    return {'passed':True,'pad_count':len(expected),'scope':'UUID/reference/pad-number/net/copper-layer identity; no geometry normalization qualification'}


def audit_raw_dsn(tree,context,project):
    from autorouter import sexpr as sx
    from autorouter.adapter import _check_units
    _check_units(tree)
    network,structure,library,placement=[sx.one(tree,key) for key in ('network','structure','library','placement')]
    if any(v is None for v in (network,structure,library,placement)):raise ValueError('missing DSN section')
    if any(not isinstance(n,list) or not n or n[0] not in {'net','class'} for n in network[1:]):raise ValueError('unknown network scope')
    raw={key:nm(project['net_settings']['classes'][0][value]) for key,value in CLASS_VALUES.items()}
    rules=sx.one(structure,'rule')
    if rules!=['rule',['width',str(raw['width_nm']//1000)],['clearance',str(raw['clearance_nm']//1000)],
               ['clearance',str(raw['clearance_nm']//4000),['type','smd_smd']]]:
        raise ValueError('unexpected pinned global raw guidance syntax or value')
    classes=sx.children(network,'class')
    if len(classes)!=1 or sx.unquote(classes[0][1])!='kicad_default':raise ValueError('unexpected exported class')
    cls=classes[0]
    if any(isinstance(x,list) and x[0] not in {'rule','circuit'} for x in cls[2:]):raise ValueError('class override')
    members=[sx.unquote(x) for x in cls[2:] if isinstance(x,str)]
    if len(set(members))!=len(members) or set(members)!={n['name'] for n in context['nets']}:raise ValueError('class membership differs')
    if sx.one(cls,'rule')!=rules[:3]:raise ValueError('class rules differ from original preferences')
    via_id='Via[0-1]_'+str(raw['via_diameter_nm']//1000)+':'+str(raw['via_drill_nm']//1000)+'_um'
    if sx.one(structure,'via')!=['via','"'+via_id+'"'] or sx.one(cls,'circuit')!=['circuit',['use_via','"'+via_id+'"']]:
        raise ValueError('unexpected selected via declaration')
    stacks=sx.children(library,'padstack');stack_ids=[sx.unquote(x[1]) for x in stacks]
    if len(set(stack_ids))!=len(stack_ids):raise ValueError('duplicate library padstack')
    selected=next((s for s in stacks if sx.unquote(s[1])==via_id),None)
    expected=['padstack','"'+via_id+'"',['shape',['circle','F.Cu',str(raw['via_diameter_nm']//1000)]],
              ['shape',['circle','B.Cu',str(raw['via_diameter_nm']//1000)]],['attach','off']]
    if selected!=expected:raise ValueError('unexpected via shape/encoded drill')
    if sx.one(tree,'wiring')!=['wiring']:raise ValueError('task still has route wiring')
    if {sx.unquote(n[1]) for n in sx.children(structure,'layer')}!={'F.Cu','B.Cu'}:raise ValueError('unexpected layers')
    # All connected pin identities must resolve to one native pad and one placed
    # library pin. This is an identity audit, not a pad shape/coordinate proof.
    image_rows=sx.children(library,'image')
    images={sx.unquote(n[1]):n for n in image_rows}
    if len(images)!=len(image_rows):raise ValueError('duplicate library image')
    placed={}
    for comp in sx.children(placement,'component'):
        image=sx.unquote(comp[1])
        if image not in images:raise ValueError('unknown placed image')
        pins=sx.children(images[image],'pin')
        pin_ids=[sx.unquote(next(x for x in pin[2:] if isinstance(x,str))) for pin in pins]
        # PIN grammar can contain a leading (rotate ...) before its string ID.
        if len(set(pin_ids))!=len(pin_ids):raise ValueError('duplicate library pin identity')
        for place in sx.children(comp,'place'):
            ref=sx.unquote(place[1])
            if ref in placed:raise ValueError('duplicate reference placement')
            placed[ref]={'image':image,'pins':set(pin_ids)}
    native={}
    for pad in context['pads']:
        if pad['netcode']<=0 or not pad['copper_layers']:continue
        ref,num=pad['reference'],pad['number']
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*',ref) or not re.fullmatch(r'[A-Za-z0-9_]+',num):
            raise ValueError('connected identity requires explicit escaping qualification')
        token=ref+'-'+num
        if token in native:raise ValueError('duplicate connected reference/pad identity')
        if ref not in placed or num not in placed[ref]['pins']:raise ValueError('native terminal absent from placed library image')
        native[token]=pad
    observed={}
    for net in sx.children(network,'net'):
        if len(net)!=3 or not isinstance(net[2],list) or net[2][0]!='pins':raise ValueError('net override or malformed pins')
        for atom in net[2][1:]:
            token=sx.unquote(atom)
            if token in observed or token not in native:raise ValueError('duplicate/unknown DSN terminal')
            if native[token]['net']!=sx.unquote(net[1]):raise ValueError('terminal net changed')
            observed[token]=native[token]['uuid']
    if set(observed)!=set(native):raise ValueError('native connected terminal missing from DSN')
    rule_paths=[]
    def walk(node,path=()):
        if not isinstance(node,list) or not node:return
        path=path+(node[0],)
        if node[0]=='rule':rule_paths.append(path)
        if node[0] in {'region','class_class','layer_rule','clearance_class','via_rule','group','fromto'}:
            raise ValueError('unsupported additional routing-rule scope')
        for child in node[1:]:
            if isinstance(child,list):walk(child,path)
    walk(tree)
    if sorted(rule_paths)!=sorted([('pcb','structure','rule'),('pcb','network','class','rule')]):raise ValueError('unexpected rule scope')
    return {'passed':True,'connected_terminal_count':len(observed),'terminal_to_uuid':observed,
            'native_raw_targets_preserved':True,'board_floor_compliant':False,
            'raw_global_rules':rules,'raw_class_rules':sx.one(cls,'rule'),'via_id':via_id,
            'rule_paths':rule_paths,'limitations':['No transformed-guidance audit or via SES import.',
                'Connected pin identity only; physical pad coordinates/shapes not independently certified.',
                'Observed raw-rule inventory only; full future transformation grammar not qualified.']}


def cpu():
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+child.ru_utime+child.ru_stime


def disposable_task(tree):
    from autorouter import pipeline as p,sexpr as sx
    task=copy.deepcopy(tree)
    if any(p.locked(n) for n in p.routes(task)):raise ValueError('protected routes outside this diagnostic scope')
    task[:]=[n for n in task if not isinstance(n,list) or not n or n[0] not in p.ROUTES]
    for zone in sx.children(task,'zone'):
        zone[:]=[n for n in zone if not isinstance(n,list) or not n or n[0] not in p.DERIVED_ZONE]
    if p.immutable(task)!=p.immutable(tree):raise ValueError('task reconstruction changed immutable geometry')
    return task


def preserve_partial(out):
    partial=Path(out)/'summary.json.partial'
    if partial.is_symlink():raise ValueError('symlinked partial receipt')
    if partial.exists():
        destination=Path(out)/('interrupted-summary-'+uuid.uuid4().hex+'.partial')
        if destination.exists():raise ValueError('partial receipt collision')
        partial.rename(destination)


def experiment(out,root):
    sys.path.insert(0,str(root))
    from autorouter import config as c,pipeline as p,sexpr as sx,adapter
    start=time.monotonic();start_cpu=cpu();out=Path(out).absolute()
    if root!=c.ROOT or out.parent!=root/'.runs' or out.exists() or any(x.is_symlink() for x in (out,*out.parents)):
        raise ValueError('requires current local checkout and new direct .runs child')
    source_dir=root/'.data/boards/kicad-multichannel'; source=source_dir/'multichannel_mixer.kicad_pcb'
    fixture=root/'fixtures/smoke/smoke.kicad_pcb'
    for path in (source_dir,fixture,root/'data/sources.json'):
        if any(x.is_symlink() for x in (path,*path.parents)):raise ValueError('symlink in reference path')
    before=p.tree_hash(source_dir);manifest_path=root/'data/sources.json'
    expected={str(Path(v['destination']).relative_to('boards/kicad-multichannel')):v['sha256']
              for v in json.loads(manifest_path.read_text())['files'] if v.get('project_id')=='kicad-multichannel'}
    if before!=expected or before.get(source.with_suffix('.kicad_pro').name)!=PROJECT_SHA:
        raise ValueError('original acquisition inventory or full project changed')
    if source.with_suffix('.kicad_dru').exists():raise ValueError('custom rules outside probe')
    project=json.loads(source.with_suffix('.kicad_pro').read_text())
    source_tree=p.preflight(source)
    if any(p.locked(n) for n in p.routes(source_tree)):raise ValueError('protected routes outside proposed floor scope')
    fixture_sha=p.sha(fixture)
    tools=p.tool_manifest();script_sha=p.sha(__file__);p.check_storage()
    job=p.Job(out,max(.01,30-(time.monotonic()-start)))
    record={'schema':1,'purpose':'B1 native Default floor/context/terminal export qualification only',
            'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds_ceiling':30,
            'cpu_budget_enforcement':'postcompletion acceptance cap; no total-CPU preemption',
            'tools':tools,'script_sha256':script_sha,'source_hashes':before,'source_manifest_sha256':p.sha(manifest_path),
            'fixture_sha256':fixture_sha,'controls_passed':False,'cases':[],
            'routing_accepted':False,'production_support_qualified':False,'solver_executed':False,'drc_executed':False}
    shutil.copy2(__file__,out/'probe.py');shutil.copytree(source_dir,out/'snapshot')
    (out/'code').mkdir()
    for path in (root/'autorouter').glob('*.py'):shutil.copy2(path,out/'code'/path.name)
    env={k:v for k,v in job.env.items() if not k.startswith('KICAD_') and k not in {'PYTHONPATH','PYTHONHOME'}}
    for key in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):env[key]=job.env[key]
    (out/'tmp').mkdir();env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'));job.env=env
    def account():
        record.update(steps=job.steps,wall_seconds=time.monotonic()-start,cpu_seconds=cpu()-start_cpu)
        if record['wall_seconds']>30 or record['cpu_seconds']>30:record.update(controls_passed=False,budget_exceeded=True)
    try:
        if p.tree_hash(out/'snapshot')!=before or p.sha(out/'probe.py')!=script_sha:raise ValueError('snapshot changed')
        for name in ('source_stripped','owned_fixture','owned_fixture_missing_project'):
            entry={'case':name,'passed':False};record['cases'].append(entry)
            case=out/name;case.mkdir();input_dir=case/'native-input'
            shutil.copytree(source_dir,input_dir,ignore=(lambda path,names:[source.with_suffix('.kicad_pro').name]
                            if Path(path)==source_dir else []) if name.endswith('missing_project') else None)
            task=disposable_task(source_tree if name=='source_stripped' else sx.read(fixture))
            board=input_dir/source.name;sx.write(board,task)
            input_before=p.tree_hash(input_dir);entry['input_before']=input_before
            dsn=case/'native.dsn';context_path=case/'native-context.json'
            job.step(name,['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',
                          c.PYTHON,out/'probe.py','--native-worker',board,dsn,context_path])
            entry['input_after']=p.tree_hash(input_dir)
            if entry['input_after']!=input_before:raise ValueError('native worker changed project inventory')
            context=json.loads(context_path.read_text());entry['native_context_sha256']=p.sha(context_path);entry['dsn_sha256']=p.sha(dsn)
            if context['dsn_sha256']!=entry['dsn_sha256']:raise ValueError('raw DSN binding changed')
            try:entry['context_audit']=audit_context(context,project,p.sha(board),PROJECT_SHA)
            except ValueError as exc:
                entry['context_rejection']=str(exc)
                if name!='owned_fixture_missing_project':raise
            if name=='owned_fixture_missing_project':
                entry['observed_floor_differences']={k:context['floors_nm'][k] for k in FLOORS if context['floors_nm'][k]!=nm(project['board']['design_settings']['rules'][k])}
                entry['passed']=bool(entry.get('context_rejection') and context['project_sha256'] is None and entry['observed_floor_differences'])
            else:
                entry['pad_identity_audit']=audit_native_pad_identities(context,task)
                entry['raw_dsn_audit']=audit_raw_dsn(adapter._parse_dsn(dsn.read_text()),context,project)
                entry['passed']=True
            p.save_json(out/'summary.json',record)
        if p.tool_manifest()!=tools or p.sha(__file__)!=script_sha:raise ValueError('tools/code changed during context probe')
        if p.tree_hash(source_dir)!=before or p.tree_hash(out/'snapshot')!=before or p.sha(fixture)!=fixture_sha:
            raise ValueError('original source or fixture changed')
        record['original_inputs_unchanged']=True
        record['controls_passed']=all(x['passed'] for x in record['cases'])
    except (Exception,KeyboardInterrupt) as exc:
        record.update(controls_passed=False,error=type(exc).__name__+': '+str(exc))
    try:
        preserve_partial(out);account();p.save_json(out/'summary.json',record)
        if time.monotonic()-start>30 or cpu()-start_cpu>30:account();p.save_json(out/'summary.json',record)
    except KeyboardInterrupt:
        record.update(controls_passed=False,error='KeyboardInterrupt during publication')
        preserve_partial(out)
        account();p.save_json(out/'summary.json',record)
    return record


def main():
    if len(sys.argv)>1 and sys.argv[1]=='--native-worker':
        if len(sys.argv)!=5:raise ValueError('native worker argument count')
        return native_worker(*sys.argv[2:])
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=Path.cwd().resolve()
    if not (root/'AGENTS.md').is_file() or not (root/'autorouter/pipeline.py').is_file():parser.error('run from local project root')
    def interrupted(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    lock=root/'.runs/quality-experiment.lock'
    if any(x.is_symlink() for x in (lock,*lock.parents)):parser.error('symlinked experiment lock path')
    with lock.open('a') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=experiment(args.out,root)
    print(json.dumps({'controls_passed':result['controls_passed'],'output':str(args.out)}))
    raise SystemExit(0 if result['controls_passed'] else 1)

if __name__=='__main__':main()
