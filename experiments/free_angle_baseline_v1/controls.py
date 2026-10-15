"""One owned stock-angle qualification, using existing Native/process readers.
SPDX-License-Identifier: GPL-3.0-or-later
No comparative gain, family, GUI, physical approval or default promotion.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,os,signal,stat,sys,uuid
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,board_floor as g,local_settings as ls,adapter as dsn,engine_angle as angle,chain_proposals as cp
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.free_angle_baseline_v1 import fixture
PREP=ROOT/'.runs/free-angle-native-preparation-003';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/free-angle-native-enclosure-003/native';WHOLE=180.;ROUTE=120.


def account_delivery(record,wall,full,available):
    """Shared publisher calls this again after any late invalidation."""
    record.update(wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2)
    if available<=0 and record.get('status')!='cancelled':record.update(passed=False,status='budget_exceeded')
    if record.get('status')!='completed':record['passed']=False


def cancelled_execution(routed,root):
    if routed and routed.get('status')=='cancelled':return True
    # Only the bounded, owned material population; never infer cancellation
    # from an arbitrary exception or a normal rejected Native negative.
    return any(f.read_json(root/name).get('status')=='cancelled'
        for name in io.inventory(root,max_bytes=128*1024**2,max_files=2048,max_entries=4096)
        if name.endswith('-process.json'))


def context(plan,pin=None):
    shared.clean(plan['git_head'])
    if (plan.get('kind')!='owned-stock-free-angle-native-v1' or plan.get('limits')!={'whole_wall_full_cpu':WHOLE,'route_wall_full_cpu':ROUTE,'publication':2}
            or plan.get('profile')!=angle.PROFILE or plan.get('source_id')!=fixture.SOURCE_ID
            or p.tool_manifest()!=plan['tools'] or p.tree_hash(PREP/'source')!=plan['source_sha256']
            or {n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}!=plan['source_sha256']
            or any(p.sha(ROOT/n)!=value for n,value in plan['code_sha256'].items())):
        raise p.Rejected('frozen owned free-angle context differs')
    retained=plan.get('retained_positive')
    if retained is not None and (p.sha(Path(retained['receipt']))!=retained['receipt_sha256'] or p.tree_hash(Path(retained['receipt']).parent)!=retained['material_sha256']):raise p.Rejected('retained complete positive changed')
    if any(p.sha(ROOT/n)!=value for n,value in plan.get('prior_attempts',{}).get('files_sha256',{}).items()):raise p.Rejected('retained prior attempt changed')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):
        raise p.Rejected('frozen angle protocol differs')


def prepare(head):
    shared.clean(head);PREP.mkdir();copy_bytes(fixture.files(),PREP/'source')
    board=PREP/'source'/(fixture.STEM+'.kicad_pcb');tree=p.preflight(board)
    protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},tree)
    if len(protected)!=1 or len(p.routes(tree))!=1:raise p.Rejected('one authored locked trace required')
    names=set(p.tool_manifest()['implementation_sha256'])|{
        str(Path(__file__).relative_to(ROOT)),str(Path(fixture.__file__).relative_to(ROOT)),str(Path(fixture.base.__file__).relative_to(ROOT)),
        'experiments/free_angle_baseline_v1/AngleObservation.java','experiments/free_angle_baseline_v1/enclosure.py','experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind='owned-stock-free-angle-native-v1',git_head=head,profile=angle.PROFILE,
        source_id=fixture.SOURCE_ID,source_sha256=p.tree_hash(board.parent),protected_ast=protected,
        tools=p.tool_manifest(),code_sha256={n:p.sha(ROOT/n) for n in sorted(names)},
        limits={'whole_wall_full_cpu':WHOLE,'route_wall_full_cpu':ROUTE,'publication':2},
        scope='One owned exposed oblique-terminal stock tuned-free-angle route/fullSCH Native positive and physical-short negative. Four actual pinned-JAR loader observations on immutable actual engine input. No new comparative result or default/CLI/GUI/installed/human qualification.')
    old=ROOT/'.runs/free-angle-native-enclosure-002/result.json'
    failed=f.read_json(old);positive=old.parent/'native/route/result.json';routed=f.read_json(positive)
    if failed.get('passed') is not False or failed.get('status')!='failed' or routed.get('accepted') is not True:raise p.Rejected('retained002failed outer/valid positive differs')
    p.check_result(positive)
    if routed['source_hashes']!=plan['source_sha256'] or routed['tools']['implementation_sha256']!=plan['tools']['implementation_sha256'] or routed['tools']['files']!=plan['tools']['files']:raise p.Rejected('retained positive source or core/tool implementation differs')
    plan['retained_positive']=dict(receipt=str(positive),receipt_sha256=p.sha(positive),material_sha256=p.tree_hash(positive.parent))
    plan['scope']='Missing-only four actual JAR-loader observations and original-rule physical-short negative from exact retained002fullSCH/protected/non45 Native positive. No engine/source/refill/final-positive Native rerun; complete prior001002costs charged including declared probe allowance. No quality/default/family/GUI/installation/release claim.'
    plan['prior_attempts']=dict(files_sha256={str(old.relative_to(ROOT)):p.sha(old)},
        wall_seconds=failed['wall_seconds']+2,full_cpu_seconds=failed['full_cpu_seconds']+2,
        scope='Actual complete failed002outer already includes001/probe/preparation; charge it once+2publication. Prior probeCPU remains unmeasured; inherited2s allowance is declaration, not measurement.')
    context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),sha256=p.sha(PROTOCOL),native_executed=False)))


def loaders(plan,routed,remaining):
    folder=OUT/'loader';job=shared.BoundJob(folder,WHOLE,remaining,protect_local_settings=True)
    route=Path(routed['candidate']).parent.parent
    base=io.read_bytes(route/'task.dsn',angle.MAX_BYTES);none=io.read_bytes(route/angle.INPUT,angle.MAX_BYTES)
    tree=dsn._parse_dsn(base.decode());explicit=sx.parse(sx.dump(tree));sx.one(explicit,'structure').append(['snap_angle','fortyfive_degree'])
    malformed=sx.parse(sx.dump(tree));sx.one(malformed,'structure').append(['snapAngle','none'])
    samples={'omitted45':(base,'45',0),'canonicalNone':(none,'none',0),
        'explicit45':(dsn._dump_dsn(explicit).encode(),'45',0),'misspelledNone':(dsn._dump_dsn(malformed).encode(),'none',1)}
    java=ROOT/'experiments/free_angle_baseline_v1/AngleObservation.java';rows=[]
    for name,(raw,expected,exitcode) in samples.items():
        path=folder/(name+'.dsn');path.write_bytes(raw);pin=p.sha(path)
        step=job.step(name,[str(p.c.JAVA),'-Xms64m','-Xmx512m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','--class-path',str(p.c.JAR),str(java),str(path),expected],allowed=(exitcode,))
        text=io.read_bytes(folder/(name+'.log'),256*1024).decode()
        if exitcode==0:
            observed=json.loads(text.splitlines()[-1])
            if observed.get('input_sha256')!=pin or observed.get('loaded_angle')!=('NONE' if expected=='none' else 'FORTYFIVE_DEGREE') or observed.get('parse_warnings')!=[]:
                raise p.Rejected('actual loaded angle observation differs')
        elif 'loaded mode differs: FORTYFIVE_DEGREE' not in text:raise p.Rejected('misspelled angle control lacks actual45 refusal')
        if p.sha(path)!=pin:raise p.Rejected('loader input changed')
        rows.append(dict(name=name,input_sha256=pin,expected=expected,expected_exit=exitcode,step=step))
    if p.sha(route/angle.INPUT)!=hashlib.sha256(none).hexdigest() or p.sha(route/'task.dsn')!=hashlib.sha256(base).hexdigest():
        raise p.Rejected('actual routed engine input changed during loader checks')
    return rows


def negative(plan,routed,remaining,*,output=None):
    base=OUT if output is None else h.real_path(Path(output))
    if output is not None and (base==ROOT/'.runs' or not base.is_relative_to(ROOT/'.runs')):
        raise p.Rejected('negative output must be an owned canonical project .runs directory')
    board=base/'invalid'/(fixture.STEM+'.kicad_pcb');copy_bytes(io.inventory(Path(routed['candidate']).parent,contents=True),board.parent)
    tree=sx.read(board);prior=sx.read(board);added=['segment',['start','12','10'],['end','12','16'],['width','0.3'],['layer','"F.Cu"'],['net','"ROUTE"'],['uuid',json.dumps(str(uuid.uuid5(fixture.NS,'physical-short')))]]
    tree.append(added);sx.write(board,tree)
    if sx.read(board)!=prior+[added] or p.immutable(tree)!=p.immutable(prior) or any(row not in p.routes(tree) for row in plan['protected_ast']):
        raise p.Rejected('physical short changed undeclared geometry/protection')
    p.verify_candidate_files(board,plan['source_sha256'],p.sha(board));before=p.tree_hash(board.parent)
    job=shared.BoundJob(base/'invalid-job',WHOLE,remaining,protect_local_settings=True)
    copy_bytes({Path(n).name:io.read_bytes(ROOT/n,1024**2) for n in plan['tools']['implementation_sha256']},job.out/'code')
    data=dict(schema=1,steps=job.steps,source_hashes=before,tools=plan['tools'])
    native=job.drc('invalid-final',board,schematic_parity=True)
    checked=f.check_drc_stage(job.out,data,'invalid-final',board,job.out/'invalid-final-input'/board.name,False,before,schematic_parity=True)
    if f.canonical(native)!=f.canonical(checked) or p.native_accepted(native) or native['blocking']<1 or not any(row['severity']=='error' and row['type']=='shorting_items' for row in native['findings']):
        raise p.Rejected('same-original-rule physical short was not rejected natively')
    ls.check_normal_policy(job.out,data,max_bytes=128*1024**2,max_files=2048)
    return dict(candidate=str(board),candidate_sha256=p.sha(board),added_ast=added,before=before,native=native,report_sha256=p.sha(job.out/'invalid-final.json'),steps=job.steps)


def execute(plan,pin):
    context(plan,pin);OUT.mkdir();owner={};h.capture_destination(owner,OUT)
    prior=plan['preparation_costs']
    def remaining():return min(WHOLE-2-prior['wall_seconds']-2-(time.monotonic()-START),WHOLE-2-prior['full_cpu_seconds']-2-(cpu()-CPU0))
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane lock required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        record=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],tools=plan['tools'],protocol_sha256=pin,scope=plan['scope'])
        routed=None;bad=None
        try:
            positive=Path(plan['retained_positive']['receipt']);routed=f.read_json(positive)
            if routed.get('accepted') is not True:raise p.Rejected('owned stock free-angle route refused: '+str(routed.get('reason',routed.get('status'))))
            checked=p.check_result(positive);tree=sx.read(Path(routed['candidate']));_,resolve=g.source_net_identity(tree)
            oblique=[]
            for row in p.routes(tree):
                if row[0]!='segment' or row in plan['protected_ast'] or resolve(sx.one(row,'net'))!='ROUTE':continue
                a,b=cp.xy(sx.one(row,'start')),cp.xy(sx.one(row,'end'));dx,dy=abs(b[0]-a[0]),abs(b[1]-a[1])
                if min(dx,dy)>100000 and abs(dx-dy)>100000:oblique.append(row)
            if (checked.get('current') is not True or not oblique or routed['source_hashes']!=plan['source_sha256']
                    or routed.get('schematic_parity')!='checked by final native DRC' or routed['source_drc']['opens']!=1
                    or routed['source_drc']['blocking'] or not p.native_accepted(routed['native'])
                    or routed['native'].get('field_parity',{}).get('qualification',{}).get('component_count')!=6
                    or any(row not in p.routes(tree) for row in plan['protected_ast'])):
                raise p.Rejected('original/fullSCH/protected/non45 behavior control incomplete')
            record.update(positive=dict(receipt=str(positive),receipt_sha256=p.sha(positive),retained_material_sha256=plan['retained_positive']['material_sha256'],candidate_sha256=routed['candidate_sha256'],native=routed['native'],metrics=routed['metrics'],non45_route_segments=oblique,readback=checked))
            record['loader_observations']=loaders(plan,routed,remaining);bad=negative(plan,routed,remaining);record['physical_short']=bad
            record.update(passed=True,status='completed')
        except (Exception,KeyboardInterrupt) as exc:
            record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or cancelled_execution(routed,OUT) else 'failed',error=type(exc).__name__+': '+str(exc))
        witness=shared.material(OUT);record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if shared.material(OUT)!=witness:raise p.Rejected('completed angle evidence changed')
            if routed and routed.get('accepted') is True:p.check_result(positive)
            if bad is not None:
                observed=f.check_drc_stage(OUT/'invalid-job',dict(steps=bad['steps']),'invalid-final',Path(bad['candidate']),OUT/'invalid-job/invalid-final-input'/Path(bad['candidate']).name,False,bad['before'],schematic_parity=True)
                if f.canonical(observed)!=f.canonical(bad['native']):raise p.Rejected('late physical-short evidence changed')
            if p.tree_hash(PREP/'source')!=plan['source_sha256']:raise p.Rejected('original source changed')
            if shared.material(OUT)!=witness:raise p.Rejected('completed angle evidence changed late')
            # Current PRL protections last, after material/tool/code reads.
            if routed and routed.get('accepted') is True:
                ls.check_normal_policy(positive.parent,routed,max_bytes=128*1024**2,max_files=2048)
            if bad is not None:
                ls.check_normal_policy(OUT/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
        def account():
            account_delivery(record,prior['wall_seconds']+2+time.monotonic()-START,prior['full_cpu_seconds']+2+cpu()-CPU0,remaining())
        f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        return f.read_json(OUT/'result.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--prepare',action='store_true');mode.add_argument('--run-native',action='store_true');parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,cancel)
    if args.prepare:prepare(args.source_head)
    elif args.run_native:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if args.protocol_sha256!=pin or plan.get('git_head')!=args.source_head:raise p.Rejected('exact frozen head/protocol required')
        result=execute(plan,pin);print(f.canonical({k:result.get(k) for k in ['passed','status','wall_seconds','full_cpu_seconds','error']}));raise SystemExit(0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2)
    else:parser.error('explicit --prepare or --run-native required')
