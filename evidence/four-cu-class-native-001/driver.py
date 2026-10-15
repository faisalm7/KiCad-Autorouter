"""Prospective sequential default1000/explicit1007 owned4Cu transport controls.
SPDX-License-Identifier: GPL-3.0-or-later
No support admission, HFE repair, dataset-family or comparative routing claim.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,fcntl,hashlib,json,math,os,signal,stat,sys,uuid
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,board_floor as g,local_settings as ls
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as original
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.four_copper_class_transport_v1 import forced_inner as fixture
PREP=ROOT/'.runs/four-cu-class-native-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/four-cu-class-native-001';VERSIONS=('native1000','native1007')
PROOF=original.PROOF;PROOF_PIN=original.PROOF_PIN
NATIVE1007={'schema':1,'mode':'experimental-native-qualification','expected_version':'10.0.7','tools':{
 'cli':{'path':str(ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents/MacOS/kicad-cli'),'sha256':'0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'},
 'python':{'path':str(ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9'),'sha256':'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'},
 'pcbnew':{'path':str(ROOT/'.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so'),'sha256':'610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}
LIMIT=128*1024**2;CASE=210;WHOLE=450
LIMITS=dict(route_wall_full_cpu_seconds=120,case_wall_full_cpu_seconds=CASE,whole_wall_full_cpu_seconds=WHOLE,
    scratch_bytes=LIMIT,case_group_rss_bytes=4*1024**3,inner_native_group_rss_bytes=2*1024**3,log_bytes=256*1024,publication_allowance_seconds=2)


def nt_for(label):
    if label not in VERSIONS:raise p.Rejected('fixed independent toolchain case required')
    return None if label=='native1000' else p.ExperimentalNativeToolchain.from_record(NATIVE1007)


def context(plan,pin=None):
    original.clean(plan['git_head'])
    if (plan.get('schema')!=1 or type(plan.get('schema'))is not int or plan.get('kind')!='owned-four-cu-dual-native-v1'
            or plan.get('status')!='frozen_for_lead_execution' or plan.get('versions')!=list(VERSIONS)
            or plan.get('native_toolchains')!={'native1000':None,'native1007':NATIVE1007}
            or plan.get('limits')!=LIMITS or plan.get('source_id')!=fixture.SOURCE_ID or plan.get('source_stem')!=fixture.STEM
            or plan.get('required_new_inner_nets')!=list(fixture.REQUIRED_NEW_INNER_ROUTE_NETS)
            or plan.get('expected_source_opens')!=2 or plan.get('signed_bundle_proof_sha256')!=PROOF_PIN):
        raise p.Rejected('fixed quad protocol policy/context differs')
    if pin is not None and (p.sha(PROTOCOL)!=pin or f.canonical(f.read_json(PROTOCOL))!=f.canonical(plan)):raise p.Rejected('frozen quad protocol changed')
    if p.sha(PROOF)!=PROOF_PIN or f.read_json(PROOF)['experimental_native_toolchain']!=NATIVE1007:raise p.Rejected('signed comparison proof changed')
    if {n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}!=plan['source_sha256'] or p.tree_hash(PREP/'source')!=plan['source_sha256']:
        raise p.Rejected('frozen owned factory/source differs')
    if any(p.sha(ROOT/n)!=value for n,value in plan['code_sha256'].items()):raise p.Rejected('quad implementation changed')
    for label in VERSIONS:
        if p.tool_manifest(**({'native_toolchain':nt_for(label)} if label=='native1007' else {}))!=plan['tools'][label]:raise p.Rejected('frozen toolchain/source differs')


def prepare(head):
    original.clean(head)
    if p.sha(PROOF)!=PROOF_PIN or f.read_json(PROOF)['experimental_native_toolchain']!=NATIVE1007:raise p.Rejected('signed1007 proof differs')
    PREP.mkdir();copy_bytes(fixture.files(),PREP/'source');source=PREP/'source'/(fixture.STEM+'.kicad_pcb')
    tree=p.preflight(source);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},tree)
    _,resolve=g.source_net_identity(tree)
    if (len(protected)!=fixture.EXPECTED_SOURCE_ROUTE_COUNT or len(p.routes(tree))!=len(protected)
            or any(not p.locked(row) or resolve(sx.one(row,'net'))!='KEEP' for row in protected)):
        raise p.Rejected('fixed authored protected KEEP census differs')
    tools={label:p.tool_manifest(**({'native_toolchain':nt_for(label)} if label=='native1007' else {})) for label in VERSIONS}
    if any(value['git_head']!=head for value in tools.values()):raise p.Rejected('intended clean checkpoint differs')
    names=set(tools['native1000']['implementation_sha256'])|set(tools['native1007']['implementation_sha256'])|{
        str(Path(__file__).relative_to(ROOT)),str(Path(fixture.__file__).relative_to(ROOT)),str(Path(fixture.base.__file__).relative_to(ROOT)),
        str(Path(fixture.base.base.__file__).relative_to(ROOT)),'experiments/hfe_original_native_v1/driver.py','experiments/original_project_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    plan=dict(schema=1,kind='owned-four-cu-dual-native-v1',status='frozen_for_lead_execution',git_head=head,
        versions=list(VERSIONS),native_toolchains={'native1000':None,'native1007':NATIVE1007},tools=tools,
        source_sha256=p.tree_hash(source.parent),source_id=fixture.SOURCE_ID,source_stem=fixture.STEM,
        protected_ast=protected,required_new_inner_nets=list(fixture.REQUIRED_NEW_INNER_ROUTE_NETS),expected_source_opens=2,
        code_sha256={name:p.sha(ROOT/name) for name in sorted(names)},signed_bundle_proof_sha256=PROOF_PIN,
        limits=LIMITS,
        missing_support_gate='Separate actual inner-only/PTH observer proof is lead-owned; this driver does not execute or qualify it.',
        scope='Two independent same-source owned4Cu class routes, default1000 then explicit1007, plus same-original-rule invalid-copper DRC per version. No prior workers/history repair, HFE or production support admission, family, GUI, physical or comparative claim.')
    context(plan)
    plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);pin=p.sha(PROTOCOL)
    print(f.canonical(dict(prepared=True,protocol=str(PROTOCOL),protocol_sha256=pin,new_native_execution=False)))


def final_events(case,nt):
    """Repeat shared field/whole-worker guards, then current PRL flags last."""
    path=case/'route/result.json'
    if path.is_file():
        routed=f.read_json(path)
        if routed.get('accepted') is True:p.check_experimental_local_settings(case/'route',routed,nt)
    folders=((case/'route',('source-drc','refill-drc','final-drc')),(case/'invalid-job',('invalid-final',)))
    for folder,names in folders:
        for name in names:
            binding=folder/(name+'-binding.json');process=folder/(name+'-process.json')
            if binding.is_file() and process.is_file():
                raw=f.read_json(process)
                # A failed/cancelled worker is retained negative evidence, never
                # a completed Native acceptance or an exact successful PRL event.
                if raw.get('status')=='success' or raw.get('status')=='nonzero_exit' and raw.get('exit_code')==5:
                    ls.check_event(folder,f.read_json(binding),raw)


def invalid_control(case,positive,plan,nt,remaining,attempt):
    """Add one declared cross-net segment; original shell/rules/protection stay exact."""
    candidate=Path(positive['candidate']);bad=case/'invalid'/(fixture.STEM+'.kicad_pcb')
    copy_bytes(io.inventory(candidate.parent,contents=True),bad.parent)
    tree=sx.read(bad);added=['segment',['start','12','10'],['end','12','24'],['width','0.4'],['layer','"F.Cu"'],['net','"ROUTE"'],
        ['uuid',json.dumps(str(uuid.uuid5(uuid.UUID('bbfa598d-3724-430d-bdf1-a8b9ceded881'),case.name)))]]
    original_tree=sx.read(candidate);tree.append(added);sx.write(bad,tree)
    if sx.read(bad)!=original_tree+[added] or p.immutable(tree)!=p.immutable(original_tree) or any(row not in p.routes(tree) for row in plan['protected_ast']):raise p.Rejected('invalid control changed undeclared source geometry')
    p.verify_candidate_files(bad,plan['source_sha256'],p.sha(bad));before=p.tree_hash(bad.parent)
    job=original.BoundJob(case/'invalid-job',CASE,remaining,native_toolchain=nt,protect_local_settings=True,experimental_schematic_parity=nt is not None)
    attempt.update(candidate=str(bad),before=before,steps=job.steps)
    copy_bytes({Path(name).name:io.read_bytes(ROOT/name,1024**2) for name in plan['tools'][case.name]['implementation_sha256']},job.out/'code')
    data=dict(schema=1,tools=plan['tools'][case.name],steps=job.steps,source_hashes=before)
    native=job.drc('invalid-final',bad,schematic_parity=True)
    replay=f.check_drc_stage(job.out,data,'invalid-final',bad,job.out/'invalid-final-input'/bad.name,False,before,
        schematic_parity=True,native_toolchain=nt,experimental_schematic_parity=nt is not None)
    if f.canonical(native)!=f.canonical(replay) or p.native_accepted(native) or native['blocking']<1 or not any(row.get('type')=='shorting_items' and row.get('severity')=='error' for row in native['findings']):raise p.Rejected('same-rule actual shorting negative not observed')
    ls.check_normal_policy(job.out,data,max_bytes=LIMIT,max_files=2048,native_toolchain=nt)
    return dict(passed=True,candidate=str(bad),candidate_sha256=p.sha(bad),added_ast=added,before=before,
        report_sha256=p.sha(job.out/'invalid-final.json'),native=native,steps=job.steps)


def worker(plan,pin,label):
    context(plan,pin);nt=nt_for(label);case=OUT/label;case.mkdir();owner={};h.capture_destination(owner,case)
    def remaining():return min(CASE-2-(time.monotonic()-START),CASE-2-(cpu()-CPU0))
    copy_bytes(io.inventory(PREP/'source',contents=True),case/'source');board=case/'source'/(fixture.STEM+'.kicad_pcb')
    copy_bytes({name:io.read_bytes(ROOT/name,1024**2) for name in plan['code_sha256']},case/'control-code')
    kwargs={} if nt is None else dict(native_toolchain=nt,experimental_schematic_parity=True)
    record=dict(schema=1,accepted=False,passed=False,status='failed',production_support_qualified=False,source_id=plan['source_id'],
        version=label,tools=plan['tools'][label],protocol_sha256=pin,route_budget_seconds=120,observer_support_qualified=False,scope=plan['scope'])
    routed=None;negative=None;attempt={'passed':False,'steps':[]};record['invalid_copper_attempt']=attempt
    try:
        routed=p.route(board,case/'route',seconds=120,**kwargs)
        if routed.get('accepted') is not True:raise p.Rejected('independent route refused: '+str(routed.get('reason',routed.get('status'))))
        checked=p.check_result(case/'route/result.json',**kwargs);tree=sx.read(Path(routed['candidate']));_,resolve=g.source_net_identity(tree)
        generated=[row for row in p.routes(tree) if row not in plan['protected_ast']]
        vias=[row for row in generated if row[0]=='via'];inner={resolve(sx.one(row,'net')) for row in generated if row[0] in ('segment','arc') and sx.one(row,'layer') in (['layer','"In1.Cu"'],['layer','"In2.Cu"'])}
        route_vias=[row for row in vias if resolve(sx.one(row,'net'))=='ROUTE']
        if (checked.get('current') is not True or routed['source_hashes']!=plan['source_sha256'] or p.tree_hash(board.parent)!=plan['source_sha256']
                or routed.get('schematic_parity')!='checked by final native DRC' or routed['source_drc']['opens']!=2 or routed['source_drc']['blocking']
                or not p.native_accepted(routed['native']) or routed['native']['exclusions']!=0
                or any(row.get('type')=='net_conflict' for row in routed['native']['findings'])
                or routed['native'].get('field_parity',{}).get('qualification',{}).get('component_count')!=6
                or p.immutable(sx.read(board))!=p.immutable(tree) or any(row not in p.routes(tree) for row in plan['protected_ast'])
                or routed['metrics']['version']!=p.experimental_native_version(nt) or routed['metrics']['copper_layers']!=4):raise p.Rejected('same-source fullSCH/protected/metrics proof failed')
        if any(sx.one(row,'layers')!=['layers','"F.Cu"','"B.Cu"'] for row in vias):raise p.Rejected('generated via is not a full through span')
        if nt is not None:
            try:p.check_result(case/'route/result.json')
            except p.Rejected:pass
            else:raise p.Rejected('default reader admitted explicit1007 route')
        geometry=len(route_vias)>=2 and set(plan['required_new_inner_nets'])<=inner
        record.update(route_transport_complete=True,geometry_complete=geometry,source_native=routed['source_drc'],final_native=routed['native'],
            route_receipt_sha256=p.sha(case/'route/result.json'),final_candidate_sha256=routed['candidate_sha256'],metrics=routed['metrics'],
            generated_through_vias=len(vias),route_through_vias=len(route_vias),inner_route_nets=sorted(inner),protected_routes=len(plan['protected_ast']),readback=checked)
        negative=invalid_control(case,routed,plan,nt,remaining,attempt);record['invalid_copper']=negative;attempt['passed']=True
        record.update(passed=geometry,status='completed' if geometry else 'observed_narrower')
    except (Exception,KeyboardInterrupt) as exc:
        cancelled=isinstance(exc,KeyboardInterrupt) or bool(routed and routed.get('status')=='cancelled') or any(row.get('status')=='cancelled' for row in attempt['steps'])
        record.update(passed=False,status='cancelled' if cancelled else 'failed',error=type(exc).__name__+': '+str(exc))
    witness=original.material(case);record['completed_evidence']=witness
    def stable():
        h.owned_destination(owner);context(plan,pin)
        if p.tree_hash(board.parent)!=plan['source_sha256'] or original.material(case)!=witness:raise p.Rejected('case source/completed material changed')
        if record.get('route_transport_complete'):
            if p.check_result(case/'route/result.json',**kwargs).get('current') is not True:raise p.Rejected('late shared route replay refused')
        if negative is not None:
            data=dict(steps=negative['steps'])
            checked=f.check_drc_stage(case/'invalid-job',data,'invalid-final',Path(negative['candidate']),case/'invalid-job/invalid-final-input'/board.name,False,negative['before'],
                schematic_parity=True,native_toolchain=nt,experimental_schematic_parity=nt is not None)
            if f.canonical(checked)!=f.canonical(negative['native']):raise p.Rejected('late actual invalid Native changed')
        final_events(case,nt)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    f.publish(case,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return f.read_json(case/'result.json')


def execute(plan,pin):
    context(plan,pin);OUT.mkdir();owner={};h.capture_destination(owner,OUT)
    prior=plan['preparation_costs']
    if (type(prior)is not dict or set(prior)!={'wall_seconds','full_cpu_seconds','publication_allowance_seconds'}
            or prior['publication_allowance_seconds']!=2 or type(prior['publication_allowance_seconds'])is not int
            or any(type(prior[k])not in (int,float) or not math.isfinite(prior[k]) or prior[k]<0 for k in ('wall_seconds','full_cpu_seconds'))):raise p.Rejected('finite actual preparation costs required')
    prepwall=prior['wall_seconds']+2;prepcpu=prior['full_cpu_seconds']+2
    def remaining():return min(WHOLE-2-prepwall-(time.monotonic()-START),WHOLE-2-prepcpu-(cpu()-CPU0))
    rows=[];fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for label in VERSIONS:
            if remaining()<=0:rows.append(dict(version=label,passed=False,status='not_run',reason='whole budget'));continue
            process=run([*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),'--mode','worker','--source-head',plan['git_head'],'--protocol-sha256',pin,'--version',label],
                cwd=OUT,log=OUT/(label+'.log'),timeout=min(CASE,remaining()),max_log_bytes=256*1024,max_workdir_bytes=LIMIT,max_group_rss_bytes=4*1024**3)
            path=OUT/label/'result.json';child=f.read_json(path) if path.is_file() else None
            childpin=p.sha(path) if child is not None else None;literal=f.canonical(child) if child is not None else None
            bound=bool(child and original.material(OUT/label)==child.get('completed_evidence') and p.sha(path)==childpin and f.canonical(f.read_json(path))==literal)
            passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False and child.get('tools')==plan['tools'][label]
                and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
            rows.append(dict(version=label,passed=passed,process=process,child=child,child_receipt_sha256=childpin,child_literal=literal,child_completed_evidence_bound=bound,log_sha256=p.sha(OUT/(label+'.log'))))
            if process['status']=='cancelled' or child and child.get('status')=='cancelled':break
        record=dict(schema=1,accepted=False,passed=len(rows)==2 and all(row['passed'] for row in rows),status='completed' if len(rows)==2 and all(row['passed'] for row in rows) else 'failed',
            production_support_qualified=False,observer_support_qualified=False,protocol_sha256=pin,git_head=plan['git_head'],rows=rows,preparation_costs=prior,scope=plan['scope'])
        if any(row.get('process',{}).get('status')=='cancelled' or row.get('child',{}) and row['child'].get('status')=='cancelled' for row in rows):record.update(passed=False,status='cancelled')
        witness=original.material(OUT);record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner);context(plan,pin)
            if original.material(OUT)!=witness:raise p.Rejected('whole completed dual-case material changed')
            for row in rows:
                child=row.get('child')
                if child is not None:
                    case=OUT/row['version'];path=case/'result.json'
                    if not row['child_completed_evidence_bound'] or original.material(case)!=child['completed_evidence'] or p.sha(path)!=row['child_receipt_sha256'] or f.canonical(f.read_json(path))!=row['child_literal']:raise p.Rejected('published child witness/literal changed')
            for row in rows:
                if (row.get('child') or {}).get('route_transport_complete'):final_events(OUT/row['version'],nt_for(row['version']))
        def account():
            record.update(wall_seconds=prepwall+time.monotonic()-START,full_cpu_seconds=prepcpu+cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        return f.read_json(OUT/'result.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--mode',choices=('prepare','run','worker'),default='run');parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256');parser.add_argument('--version',choices=VERSIONS);args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    if args.mode=='prepare':prepare(args.source_head)
    else:
        plan=f.read_json(PROTOCOL);pin=p.sha(PROTOCOL)
        if plan.get('kind')!='owned-four-cu-dual-native-v1' or plan.get('git_head')!=args.source_head:raise p.Rejected('exact frozen intended protocol required')
        if args.protocol_sha256!=pin:raise p.Rejected('explicit frozen protocol pin required')
        row=worker(plan,pin,args.version) if args.mode=='worker' else execute(plan,pin)
        print(f.canonical({k:row.get(k) for k in ('passed','status','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if row.get('passed') is True and row.get('status')=='completed' else 2)
