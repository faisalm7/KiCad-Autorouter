"""One frozen five-file acquisition or read-only source inspection; no Native."""
import argparse, hashlib, json, os, resource, stat, sys, time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT))
from experiments.licensed_acquisition_v1 import fetch as f

def cpu():
    r=resource.getrusage(resource.RUSAGE_SELF);return r.ru_utime+r.ru_stime

def write(name,data):
    with (HERE/name).open('x') as stream:json.dump(data,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n')

def owned(path,identity=None,directory=False):
    f.contained(ROOT,path);s=path.lstat()
    if s.st_uid!=os.getuid() or not (stat.S_ISDIR(s.st_mode) if directory else stat.S_ISREG(s.st_mode) and s.st_nlink==1):raise ValueError('owned regular material required')
    value=(s.st_dev,s.st_ino,s.st_uid)
    if identity is not None and value!=identity:raise ValueError('owned identity replaced')
    return value

def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['acquire','inspect']);ap.add_argument('--protocol-sha256',required=True);a=ap.parse_args()
    raw=f.bounded(HERE/'protocol.json',65536)
    if f.sha(raw)!=a.protocol_sha256:raise ValueError('protocol hash')
    plan=f.decode(raw);data=Path(plan['destination']);started=time.monotonic();cpu_start=cpu()
    freeze=f.decode(f.bounded(HERE/'execution-freeze.json',65536))
    def stable():
        owned(HERE,directory=True)
        if f.sha(f.bounded(HERE/'protocol.json',65536))!=a.protocol_sha256:raise ValueError('protocol changed')
        for name,digest in freeze['material_sha256'].items():
            path=ROOT/f.safe(name);owned(path)
            if f.sha(f.bounded(path))!=digest:raise ValueError('implementation changed: '+name)
    stable()
    if a.phase=='acquire':
        if data.exists():raise ValueError('exclusive source destination already exists')
        if plan['expected_files']!=5 or plan['expected_bytes']!=871730 or len(plan['rows'])!=5:raise ValueError('fixed population')
        data.mkdir(mode=0o700);(data/'Hardware').mkdir(mode=0o700)
        ids={data:owned(data,directory=True),data/'Hardware':owned(data/'Hardware',directory=True)}
        rec=dict(schema=1,kind=plan['kind'],status='running',accepted=False,Native=False,engine=False,GUI=False,comparison_ready=False,independent_family_established=False,split='development-exposed',protocol_sha256=a.protocol_sha256,repository=plan['repository'],commit=plan['commit'],requests=[],files={},source_exact=False)
        def remaining():
            left=min(90-(time.monotonic()-started),60-(cpu()-cpu_start))
            if left<=0:raise TimeoutError('whole acquisition wall/fullCPU exhausted')
            return left
        try:
            for row in plan['rows']:
                stable();remaining()
                for path,identity in ids.items():owned(path,identity,directory=True)
                req={'source_path':row['source_path']};rec['requests'].append(req)
                received=sum(x.get('received_bytes',0) for x in rec['requests'])
                raw=f.fetch_one(row,req,data/f.safe(row['source_path']),plan['caps']['network_bytes']-received,remaining)
                rec['files'][row['source_path']]=f.payload(row,raw)
            expected={'schema':1,'files':dict(sorted(rec['files'].items())),'directories':['Hardware'],'file_count':5,'bytes':871730}
            f.inventory(data,expected,cap=1048576);stable();remaining()
            for path,identity in ids.items():owned(path,identity,directory=True)
            for name in rec['files']:os.chmod(data/f.safe(name),0o400)
            os.chmod(data/'Hardware',0o500);os.chmod(data,0o500)
            f.inventory(data,expected,cap=1048576)
            rec.update(status='acquired_unqualified',source_exact=True,source_inventory=expected)
        except BaseException as exc:
            rec.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
        finally:
            rec.update(wall_seconds=time.monotonic()-started,cpu_seconds=cpu()-cpu_start,requests_actual=len(rec['requests']),received_bytes=sum(x.get('received_bytes',0) for x in rec['requests']),additional_authoring_cost='unknown, not zero')
            write('acquisition.json',rec)
        print(json.dumps({k:rec[k] for k in ('status','requests_actual','received_bytes','source_exact','wall_seconds','cpu_seconds')}))
        return
    acq=f.decode(f.bounded(HERE/'acquisition.json',65536))
    if acq['status']!='acquired_unqualified' or acq['source_exact'] is not True:raise ValueError('complete originals required')
    before=f.inventory(data,acq['source_inventory'],cap=1048576)
    from autorouter import sexpr as sx,pipeline as p
    pcb=data/'Hardware/SparkFun_Qwiic_Current_Sensor_INA2XX.kicad_pcb';sch=pcb.with_suffix('.kicad_sch');pro=pcb.with_suffix('.kicad_pro')
    t=sx.read(pcb);s=sx.read(sch);project=f.decode(f.bounded(pro,1048576))
    def walk(node):
        if type(node) is list:
            yield node
            for x in node:
                if type(x) is list:yield from walk(x)
    def vals(node,key):return [sx.unquote(x) for x in sx.one(node,key,[])[1:] if type(x) is str]
    fps=sx.children(t,'footprint');pads=[pad for fp in fps for pad in sx.children(fp,'pad')]
    settings=project.get('board',{}).get('design_settings',{});netsettings=project.get('net_settings',{})
    layers=[row for row in sx.one(t,'layers',[])[1:] if type(row) is list]
    symbols=sx.children(s,'symbol');sheetfiles=[sx.unquote(n[2]) for n in walk(s) if n and n[0]=='property' and len(n)>2 and sx.unquote(n[1])=='Sheetfile']
    dep=[{'kind':n[0],'path':sx.unquote(n[1])} for n in walk(t) if n and n[0]=='model' and len(n)>1]
    properties=[sx.unquote(n[2]) for n in walk(s) if n and n[0]=='property' and len(n)>2]
    explicit=[]
    import re
    for n in list(walk(t))+list(walk(s)):
        if n and n[0] in {'gr_text','text','property'}:
            for atom in n[1:]:
                if type(atom) is str:
                    v=sx.unquote(atom)
                    if re.search(r'(?i)impedance|differential|length.?match|return.?path|kelvin|shunt|current|timing|high.?speed|controlled',v):explicit.append(v[:400])
    def topology(tree):
        groups={};uuids=set();terminals=0
        for fp in sx.children(tree,'footprint'):
            ref=next((sx.unquote(n[2]) for n in sx.children(fp,'property') if len(n)>2 and sx.unquote(n[1])=='Reference'),None)
            if ref is None:ref=next((sx.unquote(n[2]) for n in sx.children(fp,'fp_text') if len(n)>2 and n[1]=='reference'),'')
            if vals(fp,'uuid'):uuids.add(vals(fp,'uuid')[0])
            for pad in sx.children(fp,'pad'):
                net=sx.one(pad,'net',[])
                if len(net)<2 or net[1] in {'0','""'}:continue
                groups.setdefault(net[-1],[]).append((ref,sx.unquote(pad[1])));terminals+=1
        parts=sorted(sorted(g) for g in groups.values());return f.sha(json.dumps(parts,separators=(',',':')).encode()),terminals,len(groups),uuids
    sig,termcount,netcount,uuids=topology(t);comparisons=[]
    current=f.decode(f.bounded(ROOT/'.runs/runtime042-unrelated-development-sources-001.json',65536))
    for label,row in current['families'].items():
        path=Path(row['source']);raw=f.bounded(path);expected=row['source_hashes'][path.name]
        if f.sha(raw)!=expected:raise ValueError('exposed source changed: '+label)
        other=sx.parse(raw.decode());osig,ot,on,ou=topology(other)
        comparisons.append(dict(family=label,source_sha256=expected,exact_partition_match=sig==osig,terminals=ot,nets=on,shared_footprint_UUIDs=len(uuids&ou)))
    preflight={}
    for label,context in [('ordinary_native_whole','native-route-flat-classes-v1'),('Improve_flat_source',None)]:
        try:p.preflight(pcb,task_scope=('whole_board_unlocked_routing','native','source_all'),class_context=context);preflight[label]={'pure_static_pass':True}
        except (ValueError,p.Rejected) as exc:preflight[label]={'pure_static_pass':False,'reason':str(exc)}
    rec=dict(schema=1,kind='read-only-ina2xx-source-eligibility-inspection-v1',protocol_sha256=a.protocol_sha256,acquisition_sha256=f.sha(f.bounded(HERE/'acquisition.json',65536)),status='completed',decision='defer',accepted=False,Native=False,engine=False,GUI=False,comparison_ready=False,independent_family_established=False,split='development-exposed',source_hashes=before['files'],pcb_format=vals(t,'version'),schematic_format=vals(s,'version'),copper_layers=[row for row in layers if len(row)>1 and re.fullmatch(r'(F|B|In[0-9]+)\.Cu',sx.unquote(row[1]))],footprints=len(fps),pads=len(pads),pad_types=dict((kind,sum(len(pad)>2 and pad[2]==kind for pad in pads)) for kind in sorted({pad[2] for pad in pads if len(pad)>2})),pad_shapes=sorted({pad[3] for pad in pads if len(pad)>3}),route_counts={kind:len(sx.children(t,kind)) for kind in ['segment','via','arc']},locked_routes=sum(p.locked(n) for n in p.routes(t)),zones=len(sx.children(t,'zone')),rule_areas=sum(bool(sx.children(n,'keepout')) for n in walk(t)),net_tie_footprints=sum(bool(sx.children(fp,'net_tie_pad_groups')) for fp in fps),schematic_root_symbols=len(symbols),schematic_child_files=sheetfiles,schematic_netclass_flags=sum(n and n[0]=='netclass_flag' for n in walk(s)),native_classes=netsettings.get('classes'),netclass_patterns=netsettings.get('netclass_patterns'),netclass_assignments=netsettings.get('netclass_assignments'),original_design_rules=settings.get('rules'),drc_exclusions=settings.get('drc_exclusions'),nonblocking_critical_severities={k:v for k,v in settings.get('rule_severities',{}).items() if k in p.CRITICAL_CHECKS and v!='error'},external_model_declarations=dep,explicit_source_requirement_text=sorted(set(explicit)),pure_source_preflight=preflight,ancestry=dict(candidate_partition_sha256=sig,connected_pad_occurrences=termcount,connected_nets=netcount,comparisons=comparisons,limit='Only exact reference/pad net-partition and footprint UUID screen against two known exposed families. Differing signatures and publisher do not prove independent pedigree; no reference route used.'),requirements_unknown=['Inline shunt-current/Kelvin, allowable current, thermal, sense-path and physical/electrical fitness are not established by net names, static grammar or DRC.','External stock libraries/models/artwork title chains and provenance remain unqualified.','No Native source, full-schematic/parity, refill, original/protected final candidate or delivery proof exists for this source.'],rights=plan['rights'],additional_authoring_cost='unknown, not zero')
    from autorouter import netclass as nc, netclass_native as nn
    copper_check={}
    try:
        if len(rec['copper_layers'])==2:
            identities,aliases=nn.source_all_two_copper_layers(t);copper_check=dict(pure_static_pass=True,identity=identities,display_aliases=aliases)
        elif len(rec['copper_layers'])==4:
            identities=nc.four_copper_source_layers(t);copper_check=dict(pure_static_pass=True,identity=identities)
        else:raise ValueError('not two/four copper')
    except ValueError as exc:copper_check=dict(pure_static_pass=False,reason=str(exc))
    defs={sx.unquote(n[1]) for n in sx.children(sx.one(s,'lib_symbols',[]),'symbol')}
    used={vals(n,'lib_id')[0] for n in symbols if vals(n,'lib_id')}
    models=[x['path'] for x in dep]
    areas=[]
    for owner in [t,*fps]:
        for zone in sx.children(owner,'zone'):
            if sx.children(zone,'keepout'):areas.append(dict(owner='root' if owner is t else 'footprint',layers=vals(zone,'layer') or vals(zone,'layers'),flags={n[0]:n[1:] for n in sx.one(zone,'keepout')[1:] if type(n) is list and n}))
    rec.update(canonical_source_all_layers=copper_check,schematic_closure=dict(root_sheet_only=not sx.children(s,'sheet'),embedded_definitions=len(defs),placed_lib_ids=len(used),missing_embedded_lib_ids=sorted(used-defs),listed_local_tables_or_child_schematics=False,Native_parity='NOTRUN'),rule_area_details=areas,custom_pad_count=sum(len(pad)>3 and pad[3]=='custom' for pad in pads),jumpers_or_net_ties=[dict(reference=next((sx.unquote(n[2]) for n in sx.children(fp,'property') if len(n)>2 and sx.unquote(n[1])=='Reference'),''),library_id=sx.unquote(fp[1]),net_tie_groups=sx.children(fp,'net_tie_pad_groups')) for fp in fps if sx.children(fp,'net_tie_pad_groups') or 'jumper' in sx.unquote(fp[1]).lower()],external_models_summary=dict(declarations=len(models),unique=len(set(models)),absolute_unique=sum(x.startswith('/') for x in set(models)),acquired=0),eligible_family_count=0,independent_family_claim=False)
    rec['blockers']=[row['reason'] for row in preflight.values() if not row['pure_static_pass']]
    if not copper_check['pure_static_pass']:rec['blockers'].append(copper_check['reason'])
    if sheetfiles:rec['blockers'].append('unacquired child schematic closure')
    if used-defs:rec['blockers'].append('missing embedded symbol definitions')
    if not rec['blockers']:
        rec['decision']='eligible_to_installed_preflight_only_not_comparison_ready'
    rec['source_declaration_limit']='Matched source text is retained verbatim locally with no electrical inference; README expressly describes inline shunt-current measurement. No rated current/Kelvin adequacy proved.'

    stable();f.inventory(data,before,cap=1048576)
    rec.update(source_unchanged=True,wall_seconds=time.monotonic()-started,cpu_seconds=cpu()-cpu_start)
    write('inspection.json',rec)
    print(json.dumps({k:rec[k] for k in ['status','decision','pcb_format','footprints','pads','pure_source_preflight','source_unchanged','wall_seconds','cpu_seconds']}))
if __name__=='__main__':main()
