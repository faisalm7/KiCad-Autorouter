"""One frozen flat-class positive; reuse the actual retained mismatch.

SPDX-License-Identifier: GPL-3.0-or-later
Production guard unchanged. No engine or routing acceptance.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in(resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,json,sys,os,stat,fcntl,signal
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx,placement_clearance as io,config as c
from experiments.hfe_original_native_v1.driver import BoundJob,clean,material
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.net_tie_contact_v1.driver import replay_candidate
from experiments.flat_class_parity_v1 import fixture,compare
STEM=fixture.old.STEM

def negative_inputs():
    receipt,route,packet=fixture.retained();parent=receipt.parent
    native=io.read_bytes(parent/'final-netclasses.json');netlist=io.read_bytes(parent/'final-drc-fields.net')
    proof=f.read_json(parent/'final-drc-fields-proof.json')
    if (proof!=route['native']['field_parity']
            or p.sha(parent/'final-drc-fields.net')!=route['native']['field_parity']['netlist_sha256']
            or p.sha(parent/'final-netclasses.json')!='9b410a543addb6dcdb2e8c2be340bdfcb1e76a4f0aa864b7c6ac3e2fa5d92b77'):
        raise p.Rejected('retained Native netlist/map proof changed')
    observed=json.loads(native)
    return packet,native,netlist,observed['source'],str(Path(route['candidate']).parent.parent/'final-drc-input'/(STEM+'.kicad_sch'))

def mismatch(packet,native,netlist,source,sch_source):
    try:compare.derive(netlist,packet[STEM+'.kicad_pcb'],packet[STEM+'.kicad_pro'],native,source=source,schematic_source=sch_source,schematic_raw=packet[STEM+'.kicad_sch'])
    except compare.ClassIdentityMismatch as exc:
        # Schema/source/partition failures do not qualify the historical control.
        if exc.net!='ROUTE' or exc.schematic_class!='CRITICAL,POWER,Default' or exc.pcb_class!='POWER,Default':raise p.Rejected('different retained class mismatch')
        return dict(refused=True,kind=type(exc).__name__,reason=str(exc))
    raise p.Rejected('retained class false acceptance was not specifically refused')

def replay_class_proof(path,record,derived):
    if p.sha(path)!=record['class_parity_sha256'] or f.read_json(path)!=derived:
        raise p.Rejected('class parity proof bytes or derivation changed')

def prepare(folder,head):
    clean(head);folder.mkdir();tools=p.tool_manifest();packet=fixture.files();copy_bytes(packet,folder/'positive')
    board=folder/'positive'/(STEM+'.kicad_pcb')
    try:p.preflight(board)
    except p.Rejected as exc:
        reason=str(exc)
        if 'netclass_flag unsupported' not in reason:raise p.Rejected('different unchanged production guard: '+reason)
    else:raise p.Rejected('production class guard changed before qualification')
    neg=negative_inputs();check=mismatch(*neg);copy_bytes(neg[0],folder/'retained-negative')
    copy_bytes({'native.json':neg[1],'schematic.net':neg[2]},folder/'retained-negative-observation')
    code={str(path.relative_to(ROOT)):p.sha(path)for path in Path(__file__).parent.iterdir()if path.is_file()}
    for name in ('experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py','experiments/net_tie_contact_v1/driver.py','experiments/schematic_class_intent_v1/fixture.py','experiments/four_copper_pour_support_v1/fixture.py','experiments/four_copper_class_transport_v1/forced_inner.py'):
        code[name]=p.sha(ROOT/name)
    plan=dict(schema=1,git_head=head,tools=tools,code_sha256=code,input_sha256=p.tree_hash(folder),negative_source=neg[3],negative_schematic_source=neg[4],retained_specific_mismatch=check,unchanged_production_refusal=reason,accepted=False,limits=dict(total_wall_full_cpu_seconds=120,native_worker_seconds=110,outer_scratch_bytes=20*1024**2,polled_rss_bytes=2*1024**3,per_step_logs_bytes=256*1024),preparation_costs=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0),scope='One new owned matching POWER directive derived from exact old routed fixture, all existing copper protected. One actual positive refill/final fullSCH/netlist/class map; retained original CRITICAL mismatch reused, not rerun. Class fidelity prerequisite only; production guard/engine/routing admission unchanged. Research/authoring/review costs separate and unmeasured.')
    p.save_json(folder/'protocol.json',plan);print(json.dumps({'prepared':True,'Native_executed':False,'protocol_sha256':p.sha(folder/'protocol.json')}))

def execute(folder,output):
    plan=f.read_json(folder/'protocol.json');pin=p.sha(folder/'protocol.json')
    def current():
        clean(plan['git_head'])
        if p.tool_manifest()!=plan['tools'] or p.sha(folder/'protocol.json')!=pin or any(p.sha(ROOT/name)!=sha for name,sha in plan['code_sha256'].items()):raise p.Rejected('frozen source/runtime/protocol changed')
        frozen=p.tree_hash(folder);frozen.pop('protocol.json')
        if frozen!=plan['input_sha256']:raise p.Rejected('frozen control input changed')
    current();output.mkdir();owner={};h.capture_destination(owner,output)
    def remaining():return min(110-(time.monotonic()-START),110-(cpu()-CPU0),118-plan['preparation_costs']['wall_seconds']-(time.monotonic()-START),118-plan['preparation_costs']['full_cpu_seconds']-(cpu()-CPU0))
    record=dict(schema=1,passed=False,accepted=False,status='failed',routing_accepted=False,production_admitted=False,class_parity_qualified=False,retained_negative_control_passed=False,protocol_sha256=pin,tools=plan['tools'],scope=plan['scope'])
    def interrupted(signum,frame):raise KeyboardInterrupt('diagnostic terminated')
    for sig in(signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+')as lock:
        if not stat.S_ISREG(os.fstat(lock.fileno()).st_mode) or os.fstat(lock.fileno()).st_nlink!=1:raise p.Rejected('shared Native lane invalid')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        contexts=[]
        try:
            source=folder/'positive'/(STEM+'.kicad_pcb');original=sx.read(source);before=p.tree_hash(source.parent);protected=p.routes(original)
            candidate=output/'candidate'/source.name;copy_bytes(io.inventory(source.parent,contents=True),candidate.parent)
            job=BoundJob(output/'job',min(110,remaining()),remaining,protect_local_settings=True);record['steps']=job.steps
            digest,native=p.validate_candidate(job,original,candidate,before,protected)
            ctx=(job,original,candidate,before,protected,digest,native);replay_candidate(*ctx);contexts.append(ctx)
            if not p.native_accepted(native) or native['warnings']!=6 or len(native['ignored_checks'])!=2:raise p.Rejected('matching control Native findings differ')
            mapped=job.out/'final-netclasses.json'
            audit=p.audit_candidate_netclasses(candidate,protected,f.read_json(mapped));audit['native_map_file_sha256']=p.sha(mapped)
            if audit!=f.read_json(job.out/'final-netclass-audit.json'):raise p.Rejected('shared final class audit differs')
            netlist=job.out/'final-drc-fields.net';sch_path=job.out/'final-drc-input'/candidate.with_suffix('.kicad_sch').name
            def positive():return compare.derive(io.read_bytes(netlist),io.read_bytes(candidate),io.read_bytes(candidate.with_suffix('.kicad_pro')),io.read_bytes(mapped),source=str(candidate),schematic_source=str(sch_path),schematic_raw=io.read_bytes(sch_path))
            proof=positive();p.save_json(output/'class-parity.json',proof)
            neg_packet=io.inventory(folder/'retained-negative',contents=True)
            neg_args=(neg_packet,io.read_bytes(folder/'retained-negative-observation/native.json'),io.read_bytes(folder/'retained-negative-observation/schematic.net'),plan['negative_source'],plan['negative_schematic_source'])
            negative=mismatch(*neg_args)
            record.update(passed=True,status='completed',class_parity_qualified=True,retained_negative_control_passed=True,native=native,candidate=str(candidate),candidate_sha256=digest,class_parity_sha256=p.sha(output/'class-parity.json'),retained_negative=negative,protected_routes=len(protected))
        except(Exception,KeyboardInterrupt)as exc:
            record.update(passed=False,status='cancelled'if isinstance(exc,KeyboardInterrupt)else'failed',reason=type(exc).__name__+': '+str(exc))
        witness=material(output);record['completed_evidence']=witness
        def stable():
            current();h.owned_destination(owner)
            for ctx in contexts:replay_candidate(*ctx)
            if record['passed']:
                f.process_check(job.out,{'steps':job.steps},'final-netclasses',[*f.SANDBOX,str(c.PYTHON),str(ROOT/'autorouter/native.py'),'netclasses',str(candidate),str(mapped)])
                replay_class_proof(output/'class-parity.json',record,positive())
                if mismatch(*neg_args)!=record['retained_negative']:raise p.Rejected('class parity replay differs')
            if material(output)!=witness:raise p.Rejected('completed diagnostic material changed')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,preparation_costs=plan['preparation_costs'])
            if remaining()<=0:record.update(status='budget_exceeded',passed=False)
            if record['status']!='completed':record.update(passed=False,class_parity_qualified=False,retained_negative_control_passed=False)
        f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(output/'result.json');print(json.dumps({k:stored.get(k)for k in('passed','status','reason','wall_seconds','full_cpu_seconds')}));return 0 if stored['passed']is True and stored['status']=='completed'else 2

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['prepare','run']);ap.add_argument('--preparation',type=Path,required=True);ap.add_argument('--output',type=Path);ap.add_argument('--head');a=ap.parse_args()
    if a.mode=='prepare':prepare(a.preparation.absolute(),a.head)
    else:raise SystemExit(execute(a.preparation.absolute(),a.output.absolute()))
