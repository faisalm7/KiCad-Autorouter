"""Offline audit of announced-complete production fixture; no native/engine calls.

Writes only its own write-once audit output. Git blob reads are the sole subprocess.
This checks retained evidence consistency, not authentication or new native proof.
"""
from pathlib import Path
import ast,collections,copy,hashlib,json,math,os,stat,subprocess,sys
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p, sexpr as sx, board_floor as g, floor_route as f, placement_clearance as pc
RUN=ROOT/'.runs/unknown-policy-native-001'
HEAD='d97314ff033b696df9b6660bba534e8a6851d080'
CANDIDATE='e897b0ea8224ca58c9baf62143d3393ead367cdbed85338fdbe762da611e0542'
CHECKS=[]
def ok(name,value):
    if not value:raise AssertionError(name)
    CHECKS.append(name)
def sha(path):
    path=Path(path)
    if any(x.is_symlink() for x in (path,*path.parents)):raise ValueError('symlink input')
    before=path.stat();h=hashlib.sha256()
    if not stat.S_ISREG(before.st_mode) or before.st_size>512*1024*1024:raise ValueError('bounded regular input required')
    with path.open('rb') as stream:
        total=0
        for chunk in iter(lambda:stream.read(65536),b''):
            total+=len(chunk)
            if total>before.st_size:raise ValueError('input grew')
            h.update(chunk)
    after=path.stat()
    if total!=before.st_size or (before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('input changed')
    return h.hexdigest()
def inventory(root):
    root=Path(root);pending=[root];result={};entries=0;total=0
    while pending:
        folder=pending.pop()
        if any(x.is_symlink() for x in (folder,*folder.parents)):raise ValueError('symlink directory')
        with os.scandir(folder) as iterator:
            for item in iterator:
                entries+=1
                if entries>4000 or item.is_symlink():raise ValueError('inventory entry limit/symlink')
                if item.is_dir(follow_symlinks=False):pending.append(Path(item.path));continue
                if not item.is_file(follow_symlinks=False) or len(result)>=2000:raise ValueError('inventory file type/count')
                total+=item.stat(follow_symlinks=False).st_size
                if total>100*1024*1024:raise ValueError('inventory byte cap')
                result[str(Path(item.path).relative_to(root))]=sha(item.path)
    return dict(sorted(result.items()))
def read(path):return f.read_json(path)
def ast_diff(a,b,address=()):
    if isinstance(a,list) and isinstance(b,list):
        if len(a)!=len(b):return [(address,'length',len(a),len(b))]
        return [entry for i,(x,y) in enumerate(zip(a,b)) for entry in ast_diff(x,y,address+(i,))]
    return [] if a==b else [(address,a,b)]
def nm(value,multiplier=1000000):
    value=Decimal(value)*multiplier
    if value!=value.to_integral_value():raise ValueError('noninteger nm')
    return int(value)
def ses_transport(board):
    routes=sx.one(sx.read(RUN/'routes.ses'),'routes');ok('SES resolution exact um10',sx.one(routes,'resolution')==['resolution','um','10'])
    _,resolve=g.source_net_identity(board)
    def segment(net,layer,width,a,b):return(net,layer,width,*sorted((tuple(a),tuple(b))))
    expected=[];expected_vias=[];actual=[];actual_vias=[]
    for net in sx.one(routes,'network_out')[1:]:
        for wire in sx.children(net,'wire'):
            path=sx.one(wire,'path');points=[[nm(path[i],100),-nm(path[i+1],100)] for i in range(3,len(path),2)]
            expected.extend(segment(sx.unquote(net[1]),sx.unquote(path[1]),nm(path[2],100),a,b) for a,b in zip(points,points[1:]))
        for via in sx.children(net,'via'):
            ok('SES exact derived via padstack',sx.unquote(via[1])=='Via[0-1]_1500:300_um')
            expected_vias.append((sx.unquote(net[1]),nm(via[2],100),-nm(via[3],100),1500000,300000))
    for item in p.routes(board):
        net=resolve(sx.one(item,'net'))
        if item[0]=='segment':actual.append(segment(net,sx.unquote(sx.one(item,'layer')[1]),nm(sx.one(item,'width')[1]),[nm(x) for x in sx.one(item,'start')[1:]],[nm(x) for x in sx.one(item,'end')[1:]]))
        elif item[0]=='via':
            ok('final via spans unchanged two copper layers',sx.one(item,'layers')==['layers','"F.Cu"','"B.Cu"'])
            xy=sx.one(item,'at')[1:3];actual_vias.append((net,*[nm(x) for x in xy],nm(sx.one(item,'size')[1]),nm(sx.one(item,'drill')[1])))
        else:raise AssertionError('unqualified generated route')
    ok('every final segment exactly transported from SES',collections.Counter(expected)==collections.Counter(actual))
    ok('every final via exactly transported from SES',collections.Counter(expected_vias)==collections.Counter(actual_vias))
    return len(actual),len(actual_vias)
def main():
    before=inventory(RUN);data=read(RUN/'result.json');source=Path(data['source']);source_before=inventory(source.parent)
    root_readback=ROOT/'.runs/unknown-policy-native-001-readback.json';root_readback_hash=sha(root_readback)
    ok('announced exact head and candidate',data['tools']['git_head']==HEAD and data['candidate_sha256']==CANDIDATE)
    ok('strict new accepted production schema',data['schema']==3 and data['input_policy']=='placement-clearance-v1' and data['accepted'] is True and data['status']=='routing_accepted')
    ok('sole supported scope/settings',data['adapter']=='both' and data['engine_profile']=='completion-only' and data['scoring_variant']=='via_default' and data['scope']=='whole_board_unlocked_routing' and data['baseline']=='completion_only_probe' and data['planning_parameters']=={'clearance_margin_nm':20000,'scoring_variant':'via_default','via_costs':50,'plane_via_costs':5})
    candidate=Path(data['candidate']);board=sx.read(candidate);original=sx.read(source);task=g.task_from_source(original)
    ok('complete immutable original snapshot source binding',source_before==data['source_hashes']==inventory(RUN/'snapshot'))
    ok('candidate project differs solely by board file',inventory(candidate.parent)=={**source_before,source.name:CANDIDATE})
    ok('original immutable semantic geometry preserved',p.immutable(original)==p.immutable(board))
    ok('original source matches tracked owned fixture',hashlib.sha256(subprocess.run(['git','show',HEAD+':'+str(source.relative_to(ROOT))],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout).hexdigest()==source_before[source.name])
    ok('task stripped only declared routes and derived fill',(sx.dump(task)+'\n').encode()==pc.read_bytes(RUN/'floor-export-input'/source.name) and not p.routes(task))
    areas=pc.narrow_source(original);ok('one allallowed enabled SHEETNAME original area',len(areas)==1 and areas[0]['is_rule_area'] and areas[0]['placement_enabled'] and areas[0]['placement_source_type']=='SHEETNAME' and not any(areas[0]['disallow'].values()))
    export=read(RUN/'floor-export-context.json');area=read(RUN/'placement-area-context.json');final=read(RUN/'floor-final-context.json')
    ok('same-load floor area context exact source/project/DSN/input bindings',all(export[k]==area[k] for k in ('source','board_sha256','project_sha256','dsn_sha256','input_hashes_before','input_hashes_after','board_saved','native_version','units')) and export['routes']==[] and area['footprint_zone_count']==area['footprint_rulearea_count']==0)
    ok('native pad/net/preferences/floors unchanged at final',all(export[k]==final[k] for k in ('pads','nets','floors_nm')))
    ok('native context raw original preferences retained',all(n['width_nm']==200000 and n['clearance_nm']==200000 and n['via_diameter_nm']==600000 and n['via_drill_nm']==300000 for n in export['nets']))
    outputs,composition=pc.derive_chain(RUN,source.name,data['source_hashes'])
    ok('entire chain bytes and composition independently rederived',composition==read(RUN/'placement-policy.json') and all(pc.read_bytes(RUN/name)==raw for name,raw in outputs.items()))
    raw=g._parse_dsn(pc.read_bytes(RUN/'native.dsn').decode());floor=g._parse_dsn(pc.read_bytes(RUN/'floor-guided.dsn').decode());placed=g._parse_dsn(pc.read_bytes(RUN/'placement-guided.dsn').decode());planned=g._parse_dsn(pc.read_bytes(RUN/'planning-guided.dsn').decode())
    expected=copy.deepcopy(floor);structure=sx.one(expected,'structure');keepouts=sx.children(structure,'keepout');structure[:]=[x for x in structure if x not in keepouts]
    ok('two attributed keepouts only placement AST removals',len(keepouts)==2 and expected==placed and composition['removal']['removed_count']==2 and {x['source_zone_uuid'] for x in composition['removal']['removed']}=={areas[0]['uuid']})
    diffs=ast_diff(placed,planned);ok('exact three atoms300to320um only planning edit',len(diffs)==3 and all(a=='300' and b=='320' for _,a,b in diffs))
    ok('fixture both adapter is exact planned bytes',pc.read_bytes(RUN/'planning-guided.dsn')==pc.read_bytes(RUN/'task.dsn'))
    contract=read(RUN/'floor-policy.json');ok('original floor contract remains separate authoritativepolicy',contract['policy']=='board-floors-v1' and contract['transformation']['derived_nm']=={'width_nm':300000,'clearance_nm':300000,'via_diameter_nm':1500000,'via_drill_nm':300000})
    f.audit_transport(RUN,data,task,candidate);CHECKS.append('saved import/sourceDRC/refill exact transport reconstruction')
    segments,vias=ses_transport(board);ok('owned requiredvia actual result seven segments onevia',segments==7 and vias==1)
    native=p.parse_report(RUN/'final-drc.json',candidate.name);ok('final raw DRC clean original severities',native==data['native'] and p.native_accepted(native) and native['findings']==[] and all(native[x]==0 for x in ('opens','blocking','warnings','exclusions')) and len(native['ignored_checks'])==7)
    ok('source and final ignored checks unchanged',native['ignored_checks']==data['source_drc']['ignored_checks'])
    ok('actual final native input bound to emitted hash',sha(candidate)==CANDIDATE==sha(RUN/'final-drc-input'/candidate.name) and data['native_report_sha256']==sha(RUN/'final-drc.json'))
    metrics=read(RUN/'metrics.json');length=sum(math.dist([float(x) for x in sx.one(item,'start')[1:]],[float(x) for x in sx.one(item,'end')[1:]]) for item in p.routes(board) if item[0]=='segment')
    ok('native quality metrics independently matched geometric lengths',metrics==data['metrics'] and metrics['vias']==vias and math.isclose(metrics['track_length_mm'],length,abs_tol=1e-10) and metrics['pads']==metrics['footprints']==4 and metrics['copper_layers']==2 and metrics['zones']==1)
    steps=data['steps'];ok('eight sequential exact stages', [s['name'] for s in steps]==['source-drc','floor-export','engine','import','refill-drc','floor-final','final-drc','metrics'] and all(s['exit_code']==0 and s['status']=='success' and s['cleanup_complete'] is True for s in steps))
    settings=data['engine_budget'];ok('explicit50/5 and no width reduction in actual engine',set(['--router.scoring.via_costs=50','--router.scoring.plane_via_costs=5','--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0','--router.optimizer.enabled=false'])<=set(steps[2]['argv']) and settings['assigned_job_timeout_seconds']==16)
    for key,stepkey in [('child_cpu_seconds','cpu_seconds'),('monitor_cpu_seconds','monitor_cpu_seconds')]:ok(key+' exact actualstep sum',math.isclose(data[key],sum(s[stepkey] for s in steps),abs_tol=1e-8))
    ok('full CPU components and60second caps',data['budget_seconds']==data['cpu_budget_seconds']==60 and 0<data['wall_seconds']<=60 and 0<data['total_cpu_seconds']<=60 and math.isclose(data['total_cpu_seconds'],sum(data[k] for k in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds')),abs_tol=1e-8) and sum(s['wall_seconds'] for s in steps)<=data['wall_seconds'])
    frozen=read(RUN/'placement-source-freeze.json')
    for relative,digest in frozen['files_sha256'].items():
        blob=subprocess.run(['git','show',HEAD+':'+relative],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
        ok('exact committed runtime '+relative,hashlib.sha256(blob).hexdigest()==digest==sha(ROOT/relative))
        retained=RUN/'placement-toolchain.lock.json' if relative=='toolchain.lock.json' else RUN/'code'/Path(relative).name
        ok('retained runtime '+relative,sha(retained)==digest)
    for filename,digest in data['tools']['files'].items():ok('exact installed tool binary hash '+Path(filename).name,sha(filename)==digest)
    tree=ast.parse(pc.read_bytes(RUN/'code/floor_context.py'));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
    ok('frozen worker one LoadBoard and one ExportSpecctraDSN site',sum(n.func.attr=='LoadBoard' for n in calls)==1 and sum(n.func.attr=='ExportSpecctraDSN' for n in calls)==1)
    verdict=p.check_result(RUN/'result.json');ok('standalone pure schema3 readback matches lead',verdict==read(root_readback) and verdict['current'] is True and verdict['input_policy']=='placement-clearance-v1' and verdict['applied'] is False)
    from extra import audit_extra
    extra=audit_extra(ROOT,RUN,data,read,sha,inventory,ok)
    ok('all original source fixture evidence and rootreadback unchanged',before==inventory(RUN) and source_before==inventory(source.parent) and root_readback_hash==sha(root_readback))
    result={'schema':1,'audit_passed':True,'scope':'announced-complete unchanged owned fixture native compatibility after unknown-finding policy fix; no comparative claim','native_engine_network_executed':False,'checks':CHECKS,'check_count':len(CHECKS),'extra':extra,'git_head':HEAD,'result_sha256':sha(RUN/'result.json'),'candidate_sha256':CANDIDATE,'native_report_sha256':sha(RUN/'final-drc.json'),'source_hashes':source_before,'run_inventory':before,'root_readback_sha256':root_readback_hash,'check_result':verdict,'native':native,'metrics':metrics,'dsndelta':{'removed_keepouts':2,'changed_clearance_atoms':3,'clearance_um_before':300,'clearance_um_after':320},'wall_seconds':data['wall_seconds'],'total_cpu_seconds':data['total_cpu_seconds'],'limits':'No new native run or human validation. Fixture outside population. Stored totals precede final publication; frozen code has later cap/freshness checks, not independently timed by this audit. 20um is a conservative policy, not universal geometric bound.'}
    with (HERE/'audit.json').open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','source_hashes','run_inventory','native','check_result')},indent=2))
if __name__=='__main__':main()
