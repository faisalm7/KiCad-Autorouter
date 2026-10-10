#!/usr/bin/env python3
"""Read-only KiCad geometry capability probe on immutable complete copies.

No DRC/refill/solver/save-board operation. Exported observations are NOT a
qualified proposal scene or accepted routing receipt. Native execution requires
an explicit invocation in a lead-assigned quiet slot.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import sys
import time
sys.dont_write_bytecode = True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contained_path(value, checkout, allowed_root, kind='file', allow_missing=False):
    """Authorize lexical containment and every in-checkout component before I/O.

    No resolve() on untrusted paths: it would follow a symlink before rejecting
    it. This is a foreground consistency guard, not protection from a malicious
    concurrent filesystem actor between lstat and open.
    """
    if not isinstance(value, (str, Path)) or not str(value):
        raise ValueError('invalid input path')
    raw=Path(value)
    if '..' in raw.parts:raise ValueError('parent traversal in input path')
    path=raw if raw.is_absolute() else checkout/raw
    try:
        relative=path.relative_to(checkout)
        path.relative_to(allowed_root)
    except ValueError:
        raise ValueError('path outside authorized subtree')
    current=checkout
    root_stat=os.lstat(checkout)
    if stat.S_ISLNK(root_stat.st_mode) or not stat.S_ISDIR(root_stat.st_mode):
        raise ValueError('checkout root must be a real directory')
    info=root_stat
    for index,part in enumerate(relative.parts):
        current=current/part
        try:info=os.lstat(current)
        except FileNotFoundError:
            if allow_missing and index==len(relative.parts)-1:return path
            raise ValueError('required input path missing')
        if stat.S_ISLNK(info.st_mode):raise ValueError('symlink component in input path')
        leaf=index==len(relative.parts)-1
        if not leaf and not stat.S_ISDIR(info.st_mode):raise ValueError('input ancestor is not a directory')
    if kind=='file' and not stat.S_ISREG(info.st_mode):raise ValueError('input is not a regular file')
    if kind=='directory' and not stat.S_ISDIR(info.st_mode):raise ValueError('input is not a directory')
    return path


def authorize_inputs(checkout, receipt, data):
    """Resolve only fixed local subtrees; no file content reads in this helper."""
    runs=checkout/'.runs';boards=checkout/'.data/boards'
    receipt=contained_path(receipt,checkout,runs)
    if receipt.name!='result.json':raise ValueError('receipt name must be result.json')
    source=contained_path(data['source'],checkout,boards)
    candidate=contained_path(data['candidate'],checkout,receipt.parent/'candidate')
    if source.suffix!='.kicad_pcb' or candidate!=receipt.parent/'candidate'/source.name:
        raise ValueError('receipt candidate is not its fixed task board')
    paths={'receipt':receipt,'source':source,'candidate':candidate,
           'source_project':source.with_suffix('.kicad_pro'),
           'candidate_project':candidate.with_suffix('.kicad_pro'),
           'snapshot':receipt.parent/'snapshot',
           'final_input':receipt.parent/'final-drc-input',
           'final_input_board':receipt.parent/'final-drc-input'/source.name,
           'final_report':receipt.parent/'final-drc.json',
           'final_binding':receipt.parent/'final-drc-binding.json'}
    for name,path in paths.items():
        allowed=boards if name.startswith('source') else runs
        contained_path(path,checkout,allowed,'directory' if name in ('snapshot','final_input') else 'file')
    return paths


def cleanup_stability(checkout, paths, watched, source_hashes, candidate_hashes,
                      authorized, prepared, tree_hasher, file_hasher=digest):
    if not authorized:return None,'path authorization did not complete; no cleanup input reads'
    if not prepared:return None,'preparation did not complete; unchanged input claim unavailable'
    try:
        # Reauthorize ALL roots/files before hashing any of them, so a replaced
        # ancestor symlink cannot send failure cleanup outside the task.
        for name,path in paths.items():
            allowed=checkout/'.data/boards' if name.startswith('source') else checkout/'.runs'
            contained_path(path,checkout,allowed,'directory' if name in ('snapshot','final_input') else 'file')
        for path in watched:contained_path(path,checkout,checkout/'.runs')
        stable=all(file_hasher(path)==value for path,value in watched.items())
        stable=stable and tree_hasher(paths['source'].parent)==source_hashes
        stable=stable and tree_hasher(paths['candidate'].parent)==candidate_hashes
        return stable,None if stable else 'authorized input hash changed'
    except Exception as exc:
        return False,'cleanup verification rejected: '+type(exc).__name__+': '+str(exc)


def inventory(root):
    result = {}
    total = 0
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink(): raise ValueError('symlink in input inventory')
        if p.is_file():
            total += p.stat().st_size
            if total > 100*1024*1024 or len(result) >= 2000: raise ValueError('input inventory cap')
            result[str(p.relative_to(root))] = digest(p)
    return result


def write_new(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2); f.write('\n')


def select_finding(report):
    findings = [f for f in report['violations'] if f.get('type') == 'starved_thermal']
    if len(findings) != 1 or findings[0].get('severity') != 'error' or findings[0].get('excluded', False):
        raise ValueError('requires one unexcluded blocking thermal finding')
    ids = [i['uuid'] for i in findings[0]['items']]
    if len(ids) != 2 or len(set(ids)) != 2: raise ValueError('thermal finding item identities ambiguous')
    return findings[0], ids


def xy(v):
    return [int(v.x), int(v.y)]


def uid(obj):
    return str(obj.m_Uuid.AsString())


def nearest(point, poly):
    best = float('inf')
    for a,b in zip(poly,poly[1:]+poly[:1]):
        x,y=b[0]-a[0],b[1]-a[1]
        q=x*x+y*y
        t=max(0.,min(1.,((point[0]-a[0])*x+(point[1]-a[1])*y)/q)) if q else 0.
        best=min(best,math.hypot(point[0]-a[0]-t*x,point[1]-a[1]-t*y))
    return best


def point_inside(point, poly):
    x,y=point;result=False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>y)!=(b[1]>y) and x<a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]):result=not result
    return result


def native_worker(board_path, request_path, output_path):
    checkout=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
    draft=checkout/'.runs/thermal-generalization-draft-001'
    request_path=contained_path(request_path,checkout,draft)
    root=request_path.parent
    if root.parent!=draft or Path(__file__).absolute().parent!=root:
        raise ValueError('worker must run from its new copied probe directory')
    board_path=contained_path(board_path,checkout,root/'native-input')
    contained_path(board_path.with_suffix('.kicad_pro'),checkout,root/'native-input')
    contained_path(root/'final-drc.json',checkout,root)
    output_path=contained_path(output_path,checkout,root,allow_missing=True)
    if board_path.parent != root/'native-input' or output_path.parent != root or output_path.exists():
        raise ValueError('worker requires isolated copied input and fresh sibling output')
    import pcbnew
    request=json.loads(request_path.read_text());before=inventory(board_path.parent)
    if before != request['candidate_files'] or digest(root/'final-drc.json') != request['final_drc_sha256']:
        raise ValueError('worker inputs differ from verified binding')
    raw_report=json.loads((root/'final-drc.json').read_text());finding,target_ids=select_finding(raw_report)
    if pcbnew.GetBuildVersion() != '10.0.0': raise ValueError('native version differs from pin')
    board=pcbnew.LoadBoard(str(board_path))
    if not board: raise ValueError('native load failed')
    board.SynchronizeNetsAndNetClasses(False)
    pads=list(board.GetPads());zones=list(board.Zones())
    if len(pads)>2048 or len(zones)>128: raise ValueError('native population cap')
    objects={}
    for obj in pads+zones: objects.setdefault(uid(obj),[]).append(obj)
    matched=[objects.get(i,[]) for i in target_ids]
    if any(len(v)!=1 for v in matched): raise ValueError('native thermal UUID not unique')
    target_pads=[v[0] for v in matched if isinstance(v[0],pcbnew.PAD)]
    target_zones=[v[0] for v in matched if isinstance(v[0],pcbnew.ZONE)]
    if len(target_pads)!=1 or len(target_zones)!=1: raise ValueError('finding does not bind exactly one native pad and zone')
    target,zone=target_pads[0],target_zones[0]
    errors=[]
    def observe(row,key,fn):
        try: row[key]=fn();return row[key]
        except Exception as exc:
            issue=key+': '+type(exc).__name__+': '+str(exc)[:240]
            row.setdefault('api_errors',[]).append(issue);errors.append(issue)
            return None
    layer_ids=[int(x) for x in zone.GetLayerSet().Seq() if pcbnew.IsCopperLayer(x)]
    layers=[{'id':l,'canonical':str(pcbnew.LayerName(l)),'board_name':str(board.GetLayerName(l))} for l in layer_ids]
    output={'schema':1,'kind':'native thermal geometry observations only','native_version':pcbnew.GetBuildVersion(),
        'units':'integer nanometres unless explicitly named otherwise','board_sha256':digest(board_path),
        'project_sha256':digest(board_path.with_suffix('.kicad_pro')),'finding':finding,
        'zone_uuid':uid(zone),'target_pad_uuid':uid(target),'net_code':int(zone.GetNetCode()),'net_name':str(zone.GetNetname()),
        'layers':layers,'source_unchanged':False,'board_saved':False,'refill_executed':False,'drc_executed':False,'solver_executed':False,
        'proposal_scene_qualified':False,'unsupported_reasons':[],'pads':[],'vias':[],'bodies':[]}
    if board.GetCopperLayerCount()!=2:output['unsupported_reasons'].append('board is not in narrow two-layer scope')
    if len(layer_ids)!=1:output['unsupported_reasons'].append('target zone has zero or multiple copper layers')
    if target.GetNetCode()<=0 or target.GetNetCode()!=zone.GetNetCode():output['unsupported_reasons'].append('target/zone native net mismatch')
    native_class=target.GetNet().GetNetClassSlow()
    output['class']={'name':str(native_class.GetName()),'width_nm':int(native_class.GetTrackWidth()),'clearance_nm':int(native_class.GetClearance()),'via_diameter_nm':int(native_class.GetViaDiameter()),'via_drill_nm':int(native_class.GetViaDrill())}
    observe(output,'native_max_error_nm',lambda:int(board.GetDesignSettings().m_MaxError))
    target_pos=xy(target.GetPosition());output['target_position_nm']=target_pos
    for pad in pads:
        row={'uuid':uid(pad),'net_code':int(pad.GetNetCode()),'net_name':str(pad.GetNetname()),'position_nm':xy(pad.GetPosition()),
             'footprint_uuid':uid(pad.GetParentFootprint()),'pad_number':str(pad.GetNumber()),'unsupported_reasons':[],
             'native_layer_geometry_qualified':False}
        row['logical_terminal']=[row['footprint_uuid'],row['pad_number']]
        observe(row,'orientation_degrees',lambda:float(pad.GetOrientationDegrees()))
        observe(row,'attribute',lambda:int(pad.GetAttribute()))
        observe(row,'is_pth',lambda:pad.GetAttribute()==pcbnew.PAD_ATTRIB_PTH)
        observe(row,'drill_size_nm',lambda:xy(pad.GetDrillSize()))
        observe(row,'drill_is_round',lambda:pad.GetDrillShape()==pcbnew.PAD_DRILL_SHAPE_CIRCLE)
        try:
            hole=pad.GetEffectiveHoleShape()
            row['effective_hole']={'start_nm':xy(hole.GetStart()),'end_nm':xy(hole.GetEnd()),'width_nm':int(hole.GetWidth())}
        except Exception as exc:
            issue='effective_hole: '+type(exc).__name__+': '+str(exc)[:240]
            row.setdefault('api_errors',[]).append(issue);errors.append(issue)
        row['layers']=[]
        for layer in layer_ids:
            layer_row={'id':layer,'canonical':str(pcbnew.LayerName(layer)),'on_layer':bool(pad.IsOnLayer(layer))}
            observe(layer_row,'flash_layer',lambda:bool(pad.FlashLayer(layer)))
            observe(layer_row,'shape_is_circle',lambda:pad.GetShape(layer)==pcbnew.PAD_SHAPE_CIRCLE)
            observe(layer_row,'size_nm',lambda:xy(pad.GetSize(layer)))
            observe(layer_row,'offset_nm',lambda:xy(pad.GetOffset(layer)))
            observe(layer_row,'shape_position_nm',lambda:xy(pad.ShapePos(layer)))
            row['layers'].append(layer_row)
        if not row.get('is_pth'):row['unsupported_reasons'].append('not standard plated-through pad')
        if not row.get('drill_is_round'):row['unsupported_reasons'].append('nonround or unavailable drill shape')
        h=row.get('effective_hole',{})
        if h.get('start_nm')!=row['position_nm'] or h.get('end_nm')!=row['position_nm']:row['unsupported_reasons'].append('effective drill is nonconcentric/slot/unavailable')
        for layer_row in row['layers']:
            if not layer_row.get('on_layer'):continue
            size=layer_row.get('size_nm',[])
            if not layer_row.get('shape_is_circle') or len(size)!=2 or size[0]!=size[1]:row['unsupported_reasons'].append('noncircular per-layer copper')
            if layer_row.get('shape_position_nm')!=row['position_nm'] or layer_row.get('offset_nm')!=[0,0]:row['unsupported_reasons'].append('copper/drill center offset or unavailable')
        row['unsupported_reasons'].append('native parameters observed; geometric certificate and drilled-body topology not yet proved')
        output['pads'].append(row)
    for track in board.GetTracks():
        if not isinstance(track,pcbnew.PCB_VIA):continue
        if len(output['vias'])>=2048:raise ValueError('via count cap')
        row={'uuid':uid(track),'net_code':int(track.GetNetCode()),'position_nm':xy(track.GetPosition()),'unsupported_reasons':[]}
        observe(row,'via_type',lambda:int(track.GetViaType()))
        observe(row,'drill_nm',lambda:int(track.GetDrillValue()))
        row['layer_membership']=[l for l in layer_ids if track.IsOnLayer(l)]
        output['vias'].append(row)
    total_points=0
    for layer in layer_ids:
        filled=zone.GetFilledPolysList(layer)
        count=int(filled.OutlineCount())
        if count>128:raise ValueError('zone outline count cap')
        for index in range(count):
            row={'native_outline_index':index,'layer_id':layer,'zone_uuid':uid(zone),'net_code':int(zone.GetNetCode()),
                 'holes_nm':[],'selected':False,'drills_accounted_for':False,'unsupported_reasons':[]}
            def contour(chain):
                nonlocal total_points
                n=int(chain.PointCount());total_points+=n
                if n>8192 or total_points>40000:raise ValueError('zone polygon point cap')
                return [xy(chain.CPoint(i)) for i in range(n)]
            row['outer_nm']=contour(filled.Outline(index))
            row['hole_count']=int(filled.HoleCount(index))
            if row['hole_count']>128:raise ValueError('polygon hole cap')
            for hole_index in range(row['hole_count']):row['holes_nm'].append(contour(filled.Hole(index,hole_index)))
            observe(row,'native_self_intersecting',lambda:bool(filled.IsPolygonSelfIntersecting(index)))
            observe(row,'native_outer_closed',lambda:bool(filled.Outline(index).IsClosed()))
            observe(row,'native_total_arc_count',lambda:int(filled.ArcCount()))
            observe(row,'native_island_flag',lambda:bool(zone.IsIsland(layer,index)))
            row['native_island_flag_interpretation']='observed only; not single-connection-island classification'
            row['repeated_vertices']=len(row['outer_nm'])-len({tuple(v) for v in row['outer_nm']})
            if row['hole_count']:row['unsupported_reasons'].append('explicit polygon holes outside draft proposal scope')
            if row.get('native_outer_closed') is not True:row['unsupported_reasons'].append('closed contour not demonstrated')
            if row.get('native_total_arc_count') != 0:row['unsupported_reasons'].append('arc-free native fill not demonstrated')
            if row['repeated_vertices']:row['unsupported_reasons'].append('repeated/fracture vertices')
            if row.get('native_self_intersecting') is not False:row['unsupported_reasons'].append('simple native contour not demonstrated')
            row['unsupported_reasons'].append('relation between body and all applicable drill cutouts not yet proved')
            poly=row['outer_nm']
            all_boundaries=[poly]+row['holes_nm']
            in_copper=point_inside(target_pos,poly) and not any(point_inside(target_pos,h) for h in row['holes_nm'])
            row['distance_to_target_nm']=0. if in_copper else min(nearest(target_pos,r) for r in all_boundaries)
            row['area_nm2']=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2
            row['geometric_selection_key']=[round(row['distance_to_target_nm'],3),row['area_nm2'],len(poly)]
            output['bodies'].append(row)
    # All considered bodies and reasons stay in output. No outline index chooses
    # candidates. Geometry-tied groups crossing the cap are excluded together.
    limit_radius=4*output['class']['width_nm']
    nearby=[r for r in output['bodies'] if r['distance_to_target_nm']<=limit_radius]
    nearby.sort(key=lambda r:r['geometric_selection_key'])
    selected=[];i=0
    while i<len(nearby):
        j=i+1
        while j<len(nearby) and nearby[j]['geometric_selection_key']==nearby[i]['geometric_selection_key']:j+=1
        group=nearby[i:j]
        if len(selected)+len(group)>8:
            for r in nearby[i:]:r['unsupported_reasons'].append('eight-body cap; geometry ties never split by identity')
            break
        for r in group:r['selected']=True
        selected.extend(group);i=j
    for row in output['bodies']:
        if row['distance_to_target_nm']>limit_radius:row['unsupported_reasons'].append('outside fixed four-class-width target neighborhood')
    output['body_selection']={'radius_nm':limit_radius,'cap':8,'considered':len(output['bodies']),'selected':len(selected),'policy':'distance to saved filled region, area, vertex count; retain all reasons; do not split ties by IDs'}
    output['unsupported_reasons'].append('read-only observations require separate scene/certificate qualification; no proposal emitted')
    output['api_error_count']=len(errors)
    output['source_unchanged']=inventory(board_path.parent)==before
    if not output['source_unchanged']:raise ValueError('native read-only input inventory changed')
    output['status']='observations_partial' if errors else 'observations_complete'
    write_new(output_path,output)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    root=next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
    sys.path.insert(0,str(root))
    from autorouter import pipeline as p,config as c,sexpr as sx
    import fcntl,signal
    started=time.monotonic();cpu_started=time.process_time();budget=20.
    directory=Path(__file__).resolve().parent
    out=contained_path(args.output,root,directory,kind='directory',allow_missing=True)
    if out.parent!=directory or out.exists():raise ValueError('output must be a fresh direct child of this draft directory')
    receipt=contained_path(args.receipt,root,root/'.runs')
    if receipt.name!='result.json':raise ValueError('receipt must be retained local .runs result.json')
    def interrupt(sig,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
    lock=root/'.runs/quality-experiment.lock'
    contained_path(lock,root,root/'.runs',allow_missing=True)
    with lock.open('a') as lockfile:
        fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
        job=p.Job(out,budget)
        summary={'schema':1,'status':'not_executed','native_executed':False,'solver_executed':False,'native_drc_executed':False,'board_saved':False,'routing_accepted':False,'proposal_scene_qualified':False,'wall_budget_seconds':budget,'cpu_budget_seconds':budget,'script_sha256':digest(__file__)}
        watched={};paths={};source=None;candidate=None;original_hashes=None;candidate_files=None
        authorized=False;prepared=False
        try:
            data=json.loads(receipt.read_text());base=receipt.parent
            paths=authorize_inputs(root,receipt,data)
            authorized=True
            candidate=paths['candidate'];source=paths['source'];original_hashes=data['source_hashes']
            if p.tree_hash(source.parent)!=original_hashes or p.tree_hash(base/'snapshot')!=original_hashes:raise ValueError('original source/snapshot changed')
            p.verify_candidate_files(candidate,original_hashes,data['candidate_sha256'])
            if p.immutable(sx.read(candidate))!=p.immutable(sx.read(source)):raise ValueError('immutable source geometry differs')
            native=p.parse_report(base/'final-drc.json',source.name)
            if native!=data['native'] or digest(base/'final-drc.json')!=data['native_report_sha256']:raise ValueError('final DRC receipt mismatch')
            if native['opens'] or native['exclusions'] or native['blocking']!=1:raise ValueError('probe requires sole blocking thermal, zero opens/exclusions')
            select_finding(json.loads((base/'final-drc.json').read_text()))
            candidate_files=p.tree_hash(candidate.parent)
            binding=json.loads((base/'final-drc-binding.json').read_text())
            if binding.get('source')!=str(candidate) or binding.get('input')!=str(paths['final_input_board']):raise ValueError('final DRC binding paths mismatch')
            if binding['before']!=candidate_files or p.tree_hash(paths['final_input'])!=binding['after'] or any(binding['after'].get(k)!=v for k,v in candidate_files.items()):raise ValueError('final DRC copied-input binding stale')
            tools=p.tool_manifest();watched={str(q):digest(q) for q in (receipt,base/'final-drc.json',base/'final-drc-binding.json',Path(__file__))}
            summary.update(status='prepared',tools=tools,receipt=str(receipt),receipt_sha256=digest(receipt),candidate_sha256=digest(candidate),source_files=original_hashes,candidate_files=candidate_files,watched_hashes=watched)
            shutil.copytree(candidate.parent,out/'native-input');shutil.copy2(__file__,out/'native_geometry_probe.py');shutil.copy2(base/'final-drc.json',out/'final-drc.json')
            write_new(out/'request.json',{'schema':1,'candidate_files':candidate_files,'final_drc_sha256':digest(base/'final-drc.json')})
            env={k:v for k,v in job.env.items() if not k.startswith('KICAD_') and k not in ('PYTHONPATH','PYTHONHOME')}
            for k in ('KICAD_CONFIG_HOME','KICAD_CACHE_HOME','KICAD_DOCUMENTS_HOME'):env[k]=job.env[k]
            (out/'tmp').mkdir();env.update(PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(out/'tmp'));job.env=env
            if p.tree_hash(out/'native-input')!=candidate_files:raise ValueError('copied input inventory mismatch')
            prepared=True
            job.deadline=started+budget-1.
            summary['native_executed']=True
            job.step('native-geometry-export',['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',c.PYTHON,'-B',out/'native_geometry_probe.py','--native-worker',out/'native-input'/source.name,out/'request.json',out/'geometry.json'])
            geometry=json.loads((out/'geometry.json').read_text())
            if geometry['board_sha256']!=digest(candidate) or not geometry['source_unchanged']:raise ValueError('native observation binding mismatch')
            if p.tree_hash(out/'native-input')!=candidate_files:raise ValueError('copied input changed')
            if p.tool_manifest()!=tools:raise ValueError('tool/code manifest changed')
            summary.update(status=geometry['status'],geometry_sha256=digest(out/'geometry.json'),api_error_count=geometry['api_error_count'],body_selection=geometry['body_selection'])
        except KeyboardInterrupt:summary.update(status='cancelled')
        except Exception as exc:summary.update(status='failed',reason=type(exc).__name__+': '+str(exc))
        finally:
            stable,cleanup_reason=cleanup_stability(root,paths,watched,original_hashes,candidate_files,
                authorized,prepared,p.tree_hash)
            summary['authorization_completed']=authorized
            summary['preparation_completed']=prepared
            summary['original_inputs_unchanged']=stable
            if cleanup_reason:summary['cleanup_verification_note']=cleanup_reason
            if stable is False:summary.update(status='invalidated')
            summary['steps']=job.steps
            summary['wall_seconds']=time.monotonic()-started
            summary['parent_cpu_seconds']=time.process_time()-cpu_started
            summary['child_cpu_seconds']=sum(s.get('cpu_seconds') or 0 for s in job.steps)
            summary['monitor_cpu_seconds']=sum(s.get('monitor_cpu_seconds') or 0 for s in job.steps)
            summary['total_cpu_seconds']=summary['parent_cpu_seconds']+summary['child_cpu_seconds']+summary['monitor_cpu_seconds']
            if summary['wall_seconds']>budget or summary['total_cpu_seconds']>budget:summary['status']='budget_exceeded'
            p.save_json(out/'summary.json',summary)
        print(json.dumps({k:summary[k] for k in ('status','native_executed','original_inputs_unchanged','wall_seconds','total_cpu_seconds')}))
        return 0 if summary['status'] in ('observations_complete','observations_partial') else 2


if __name__=='__main__':
    if len(sys.argv)==5 and sys.argv[1]=='--native-worker':
        native_worker(*sys.argv[2:])
    else:
        raise SystemExit(main())
