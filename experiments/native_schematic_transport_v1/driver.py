"""One owned explicit1007 export/JAR/SES/fullSCH transport experiment.

SPDX-License-Identifier: GPL-3.0-or-later
No production admission, new-board family, routing-quality or speedup claim.
"""
from pathlib import Path
import argparse,hashlib,json,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx,board_floor as g
from experiments.native_schematic_transport_v1 import fixture
from experiments.native_schematic_toolchain_v1.driver import PREREQUISITES


REFERENCE=ROOT/'.runs/native-schematic-transport-followup-preparation-001/protocol.json'
REFERENCE_SHA256='33f1c2d5d8bd11faacace7628351b49384517b450b61db91494ef51acf07b8a0'

def reference():
    if p.sha(REFERENCE)!=REFERENCE_SHA256:raise p.Rejected('fixed failed001 protocol changed')
    prior=f.read_json(REFERENCE);root=Path(prior['previous'])
    if (p.sha(root/'result.json')!=prior['receipt_sha256'] or p.tree_hash(root)!=prior['inventory']):
        raise p.Rejected('failed001 evidence changed')
    row=f.read_json(root/'result.json')
    if row.get('passed') is not False or row.get('accepted') is not False:raise p.Rejected('failed001 outcome changed')
    costs={'wall_seconds':row['wall_seconds']+2,'full_cpu_seconds':row['full_cpu_seconds']+2,'publication_allowance_seconds_each':2}
    if costs!=prior['prior_charged_enclosure_costs']:raise p.Rejected('failed001 costs changed')
    return root,costs


def experiment(output):
    started,parent,children=time.monotonic(),time.process_time(),f.child_cpu()
    output=Path(output)
    prior_root,previous=reference()
    if (output.parent!=ROOT/'.runs/native-schematic-transport-execution-002'
            or output.name!='native' or output.exists() or output.is_symlink()):
        raise p.Rejected('fixed fresh owned experiment destination required')
    for name,pin in PREREQUISITES.items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('qualified toolchain/area prerequisite changed')
    prior=ROOT/'evidence/native-schematic-hidden1007-001.json'
    if p.sha(prior)!='9449c811978a23aa763aa10d340fa4a7bc3f3ea1a982b1e414d5b329f26d8290':
        raise p.Rejected('qualified full schematic/PRL/masked-control evidence changed')
    proof=f.read_json(ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json')
    nt=p.ExperimentalNativeToolchain.from_record(proof['experimental_native_toolchain'])
    tools=p.tool_manifest(native_toolchain=nt)
    code={str(n.relative_to(ROOT)):p.sha(n) for n in Path(__file__).resolve().parent.glob('*.py')}
    output.mkdir();owner={};h.capture_destination(owner,output)
    source=output/'source';fixture.write_project(source);board=source/(fixture.STEM+'.kicad_pcb')
    hashes={n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}
    if p.tree_hash(source)!=hashes:raise p.Rejected('new owned source packet differs')
    for name,raw in fixture.files().items():
        old=(prior_root/'native/source'/name).read_bytes()
        if name.endswith(('.kicad_pcb','.kicad_sch')):
            if old!=b'; SPDX-License-Identifier: GPL-3.0-or-later\n'+raw or sx.parse(old.decode())!=sx.parse(raw.decode()):raise p.Rejected('correction changed original design')
        elif raw!=old:raise p.Rejected('correction changed original rules or PRL')
    original=p.preflight(board);protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    if len(protected)!=1 or not p.locked(protected[0]):raise p.Rejected('expected exact protected copper missing')
    record={'schema':1,'accepted':False,'passed':False,'status':'failed','production_admitted':False,
            'source_id':fixture.SOURCE_ID,'source_files':hashes,'source_board':str(board),'tools':tools,
            'fixture_code_sha256':code,'route_budget_seconds':120,'whole_wall_full_cpu_cap_seconds':170,
            'prior_charged_enclosure_costs':previous,'prerequisites':PREREQUISITES,'full_schematic_prerequisite_sha256':p.sha(prior),
            'scope':'Newly authored owned six-terminal/three-net transport only. No DRU from creation; all original PRO rules preserved. Actual Native source open must become new generated copper while locked KEEP/GND zone/fullSCH/PRL/class/SES/refill/source checks remain. Source/route/failures and enclosing costs all retained; no comparative quality or production support claim.'}
    try:
        routed=p.route(board,output/'route',seconds=120,native_toolchain=nt,experimental_schematic_parity=True)
        record['route_receipt_sha256']=p.sha(output/'route/result.json')
        record['route_status']=routed.get('status');record['route_accepted']=routed.get('accepted')
        if routed.get('accepted') is not True:raise p.Rejected('new explicit route failed: '+str(routed.get('reason',routed.get('status'))))
        checked=p.check_result(output/'route/result.json',native_toolchain=nt,experimental_schematic_parity=True)
        # The source DRC supplies the real disconnected Native negative control;
        # do not repeat an already completed native worker to repair reporting.
        source_native=routed['source_drc'];final=routed['native']
        if not source_native['opens'] or final['opens'] or final['blocking']:
            raise p.Rejected('source-to-final connectivity prediction not observed')
        candidate=Path(routed['candidate']);current=sx.read(candidate)
        if len(p.routes(current))<=len(protected) or any(n not in p.routes(current) for n in protected):
            raise p.Rejected('no new routing or protected source changed')
        generated=[n for n in p.routes(current) if n not in protected]
        _,resolve=g.source_net_identity(current)
        if not any(resolve(sx.one(n,'net'))=='ROUTE' for n in generated):raise p.Rejected('missing new ROUTE copper')
        default_refused=False
        try:p.check_result(output/'route/result.json')
        except p.Rejected:default_refused=True
        if not default_refused:raise p.Rejected('default reader admitted explicit experimental result')
        record.update(passed=True,status='completed',readback=checked,default_reader_refused=True,
            source_native_counts={k:source_native[k] for k in ('opens','blocking','warnings','exclusions')},
            final_native_counts={k:final[k] for k in ('opens','blocking','warnings','exclusions')},
            final_candidate_sha256=p.sha(candidate),metrics=routed['metrics'],protected_routes=len(protected),
            generated_routes=len(generated),worker_count=len(routed['steps']))
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
    material=f.evidence_inventory(output)
    def remaining():return min(168-previous['wall_seconds']-(time.monotonic()-started),168-previous['full_cpu_seconds']-(time.process_time()-parent+f.child_cpu()-children))
    def stable():
        h.owned_destination(owner)
        reference()
        if p.tool_manifest(native_toolchain=nt)!=tools or any(p.sha(ROOT/n)!=pin for n,pin in code.items()):raise p.Rejected('experiment tool/code/HEAD changed')
        if p.tree_hash(source)!=hashes or f.evidence_inventory(output)!=material:raise p.Rejected('experiment source/completed material changed')
        if record['passed']:
            p.check_experimental_local_settings(output/'route',routed,nt)
    def account():
        record.update(wall_seconds=time.monotonic()-started,full_cpu_seconds=time.process_time()-parent+f.child_cpu()-children,
                      publication_allowance_seconds=2)
        if remaining()<=0:record.update(passed=False,status='budget_exceeded')
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner))
    print(json.dumps({k:record.get(k) for k in ('passed','status','source_native_counts','final_native_counts','metrics','error','wall_seconds','full_cpu_seconds')}))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if experiment(args.output)['passed'] else 2)
