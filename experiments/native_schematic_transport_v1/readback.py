"""Missing-only pure validation of retained1007 transport; no Native rerun.

SPDX-License-Identifier: GPL-3.0-or-later
The original001failure and002invalidated canonical outcome remain unchanged.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,time
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx
from experiments.native_schematic_transport_v1 import fixture
PROTOCOL=ROOT/'.runs/native-schematic-transport-readback-preparation-001/protocol.json'
PIN='20dbdce779d165abc83181e479a8020a595b645324aae3299bc34417714d6b88'


def reference():
    if p.sha(PROTOCOL)!=PIN:raise p.Rejected('fixed002 readback protocol changed')
    prior=f.read_json(PROTOCOL);root=Path(prior['root']);archive=Path(prior['archived_receipt'])
    if p.tree_hash(root)!=prior['inventory'] or p.sha(archive)!=prior['archived_receipt_sha256']:
        raise p.Rejected('completed002 material changed')
    if f.read_json(root/'result.json').get('passed') is not False or f.read_json(root/'native/route/result.json').get('accepted') is not False:
        raise p.Rejected('original002 failure relabeled')
    return prior,root,archive


def experiment(output):
    started,parent,children=time.monotonic(),time.process_time(),f.child_cpu()
    prior,root,archive=reference();previous=prior['prior_charged_enclosure_costs']
    proof=ROOT/'.runs/kicad-1007-bundle-qualification-001/result.json'
    if p.sha(proof)!='26564ecd90268e463760270902d302445d9b0e6859105d3ed06e5976a8989c73':raise p.Rejected('caller Native authority changed')
    nt=p.ExperimentalNativeToolchain.from_record(f.read_json(proof)['experimental_native_toolchain'])
    output=Path(output)
    if output!=ROOT/'.runs/native-schematic-transport-readback-execution-001/readback' or output.exists() or output.is_symlink():raise p.Rejected('fixed fresh readback output required')
    output.mkdir();owner={};h.capture_destination(owner,output)
    # Only the read-only Git identity command used by tool_manifest may launch.
    real_run=subprocess.run
    def readonly(argv,*args,**kwargs):
        if argv!=['git','rev-parse','HEAD'] or Path(kwargs.get('cwd',''))!=ROOT:raise p.Rejected('pure reader attempted a worker')
        return real_run(argv,*args,**kwargs)
    subprocess.run=readonly
    tools=p.tool_manifest(native_toolchain=nt);code={str(x):p.sha(x) for x in Path(__file__).resolve().parent.glob('*.py')}
    data=f.read_json(archive);route=archive.parent
    record=dict(schema=1,accepted=False,passed=False,status='failed',production_admitted=False,normal_route_accepted=False,
        tools=tools,code_sha256=code,reference_protocol_sha256=PIN,prior_charged_enclosure_costs=previous,
        route_original_status=f.read_json(route/'result.json')['status'],archived_pre_readback_receipt_sha256=p.sha(archive),
        actual_native_source_head=data['tools']['git_head'],current_checker_source_head=tools['git_head'],
        scope='Only missing shared uncached readback after actual source/export/class/JAR/SES/import/refill/fullSCH/field/metrics workers completed. No new Native/JVM. Canonical002 staysinvalidated; prior001inputfailure staysfailed. Qualifies retained owned transport/evidence under corrected checker, not current producer success/production/userGUI/installation/routingquality.')
    try:
        checked=p.check_result(archive,native_toolchain=nt,experimental_schematic_parity=True)
        source=Path(data['source']);candidate=Path(data['candidate']);original=p.preflight(source)
        if p.tree_hash(source.parent)!={n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}:raise p.Rejected('retained source differs from corrected owned packet')
        protected=p.protected_for_record(data,original);current=sx.read(candidate)
        if len(protected)!=1 or any(n not in p.routes(current) for n in protected):raise p.Rejected('locked source route changed')
        if len(p.routes(current))<=len(protected) or data['source_drc']['opens']!=1 or data['native']['opens'] or data['native']['blocking']:
            raise p.Rejected('actual sourceopen to new route prediction failed')
        default_refused=False;canonical_refused=False
        try:p.check_result(archive)
        except p.Rejected:default_refused=True
        try:p.check_result(route/'result.json',native_toolchain=nt,experimental_schematic_parity=True)
        except p.Rejected:canonical_refused=True
        if not default_refused or not canonical_refused:raise p.Rejected('experimental/default or failed canonical bypass')
        record.update(passed=True,status='completed',transport_evidence_qualified=True,shared_readback=checked,
            default_reader_refused=True,original_invalidated_receipt_refused=True,
            source_native_counts={k:data['source_drc'][k] for k in ('opens','blocking','warnings','exclusions')},
            final_native_counts={k:data['native'][k] for k in ('opens','blocking','warnings','exclusions')},
            final_candidate_sha256=p.sha(candidate),metrics=data['metrics'],worker_count=len(data['steps']),
            native_worker_count=sum(s['name']!='engine' for s in data['steps']),engine_worker_count=1,
            complete_field_components=data['native']['field_parity']['qualification']['component_count'])
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='failed',error=type(exc).__name__+': '+str(exc))
    def remaining():return min(58-(time.monotonic()-started),58-(time.process_time()-parent+f.child_cpu()-children),178-previous['wall_seconds']-(time.monotonic()-started),178-previous['full_cpu_seconds']-(time.process_time()-parent+f.child_cpu()-children))
    def stable():
        h.owned_destination(owner);reference()
        if p.tool_manifest(native_toolchain=nt)!=tools or any(p.sha(Path(n))!=pin for n,pin in code.items()):raise p.Rejected('pure reader code/tools changed')
        if record['passed']:p.check_experimental_local_settings(route,data,nt)
    def account():
        record.update(wall_seconds=time.monotonic()-started,full_cpu_seconds=time.process_time()-parent+f.child_cpu()-children,publication_allowance_seconds=2)
        if remaining()<=0:record.update(passed=False,status='budget_exceeded')
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(json.dumps({k:record.get(k) for k in ('passed','status','metrics','error','wall_seconds','full_cpu_seconds')}))
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();raise SystemExit(0 if experiment(args.output)['passed'] else 2)
