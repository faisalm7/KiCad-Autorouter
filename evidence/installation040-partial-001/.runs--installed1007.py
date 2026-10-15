"""One fresh installed explicit1007 transport; existing helpers remain authority.
SPDX-License-Identifier: GPL-3.0-or-later
Draft: not executed. No production/default/GUI/benchmark admission.
"""
import time, resource
START=time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,sys
# This file is copied into the ordinary installed checkout's ignored scratch.
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx,board_floor as g,config as c
from experiments.native_schematic_transport_v1 import fixture
from scripts import install_smoke as install


def context(plan):
    if ROOT!=Path(plan['checkout']) or c.ROOT!=ROOT or Path(sys.executable)!=ROOT/'.venv/bin/python':
        raise p.Rejected('ordinary independent installed interpreter/context required')
    if Path(sys.prefix).resolve()!=ROOT/'.venv' or sys.prefix==sys.base_prefix:
        raise p.Rejected('independent installed venv required')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0] in {'autorouter','scripts','experiments','tests'} and getattr(module,'__file__',None):
            if not Path(module.__file__).resolve().is_relative_to(ROOT):raise p.Rejected('project import escaped installed checkout: '+name)
    listing=(Path(plan['installation'])/'03-source-files.log').read_text()
    selected=install.distribution_listing(listing)
    inventory_path=Path(plan['installation'])/'source-tracked.json'
    if p.sha(inventory_path)!=plan['source_inventory_sha256']:raise p.Rejected('installation source inventory changed')
    original=f.read_json(inventory_path)
    if install.tracked_inventory(ROOT,selected)!={n:original[n] for n in selected.split('\0') if n}:
        raise p.Rejected('installed complete distribution changed')
    if install.git_identity(ROOT,plan['git_head'])!=plan['installed_git_identity']:
        raise p.Rejected('installed Git identity changed')
    if p.sha(Path(__file__))!=plan['installed_companion_sha256']:raise p.Rejected('installed companion changed')
    for name,pin in plan['fixture_code_sha256'].items():
        if p.sha(ROOT/name)!=pin:raise p.Rejected('owned generator/protocol source changed')
    if {n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}!=plan['fixture_files_sha256']:
        raise p.Rejected('owned fixture packet differs')
    # Explicit caller-supplied typed context; never authorize from a route receipt.
    nt=p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    if nt.expected_version!='10.0.7':raise p.Rejected('exact explicit1007 required')
    original=Path(plan['original_jar']);copy=c.JAR
    if (not copy.is_relative_to(ROOT/'.tools') or copy.is_symlink() or original.is_symlink()
            or copy.stat().st_ino==original.stat().st_ino
            ):
        raise p.Rejected('independent copied engine required')
    if p.sha(copy)!=plan['jar_sha256'] or p.sha(original)!=plan['jar_sha256']:
        raise p.Rejected('pinned copied engine changed')
    return nt


def read_transport(plan):
    """Pure retained check; caller may refuse every subprocess before calling."""
    nt=context(plan);out=Path(plan['native_output']);receipt=out/'route/result.json'
    material=f.evidence_inventory(out)
    data=f.read_json(receipt);source=out/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate'])
    if data.get('tools')!=plan['native_tools']:raise p.Rejected('current installed implementation/tool provenance differs')
    if data.get('source')!=str(source) or data.get('budget_seconds')!=120 or data.get('cpu_budget_seconds')!=120:
        raise p.Rejected('installed transport source/budget differs')
    if p.tree_hash(source.parent)!=plan['fixture_files_sha256'] or data['source_hashes']!=plan['fixture_files_sha256']:
        raise p.Rejected('fresh complete owned source packet changed')
    if not source.with_suffix('.kicad_sch').is_file() or source.with_suffix('.kicad_dru').exists():
        raise p.Rejected('fixed complete SCH/no-DRU authored fixture required')
    original=sx.read(source);current=sx.read(candidate)
    protected=p.protected_for_record(data,original)
    if len(protected)!=1 or not p.locked(protected[0]) or any(x not in p.routes(current) for x in protected):
        raise p.Rejected('protected KEEP route changed')
    if p.immutable(original)!=p.immutable(current):raise p.Rejected('source invariants changed')
    generated=[x for x in p.routes(current) if x not in protected];_,resolve=g.source_net_identity(current)
    if not generated or not any(resolve(sx.one(x,'net'))=='ROUTE' for x in generated):raise p.Rejected('new ROUTE copper absent')
    checked=p.check_result(receipt,native_toolchain=nt,experimental_schematic_parity=True)
    if checked.get('current') is not True or data.get('accepted') is not True or data.get('production_admitted') is not False:
        raise p.Rejected('fresh explicit producer/shared readback failed')
    default_refused=False
    try:p.check_result(receipt)
    except p.Rejected:default_refused=True
    if not default_refused:raise p.Rejected('default checker admitted experimental result')
    native=data['native'];before=data['source_drc']
    if before['opens']!=1 or native['opens'] or native['blocking'] or native['exclusions']:
        raise p.Rejected('owned sourceopen to final connected prediction failed')
    if native['warnings']!=6 or native['field_parity']['qualification']['component_count']!=6:
        raise p.Rejected('full six-component effective-field/warning population differs')
    if data['metrics']!=f.read_json(receipt.parent/'metrics.json') or data['metrics']['version']!='10.0.7':
        raise p.Rejected('actual exact-version metrics differ')
    if p.sha(candidate)!=data['candidate_sha256'] or p.sha(receipt.parent/'final-drc.json')!=data['native_report_sha256']:
        raise p.Rejected('candidate/final report hash differs')
    p.check_resource_accounting(data);p.check_experimental_local_settings(receipt.parent,data,nt)
    # Shared check_result replays complete argv/process/source/class/alias/import,
    # saved refill, fullSCH, effective fields, PRL and final/metric bindings.
    context(plan)
    if f.evidence_inventory(out)!=material:raise p.Rejected('completed transport changed during readback')
    return dict(passed=True,route_receipt_sha256=p.sha(receipt),candidate_sha256=data['candidate_sha256'],
        final_report_sha256=data['native_report_sha256'],source_sha256=data['source_hashes'],
        source_native_counts={k:before[k] for k in ('opens','blocking','warnings','exclusions')},
        final_native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},
        metrics=data['metrics'],worker_count=len(data['steps']),protected_routes=1,
        generated_routes=len(generated),complete_field_components=6,default_reader_refused=True,
        material=material,shared_readback=checked,production_admitted=False)


def execute(plan):
    nt=context(plan);out=Path(plan['native_output'])
    if out!=ROOT/'.runs/installation040-explicit1007/native' or out.exists() or out.is_symlink():
        raise p.Rejected('one fresh installed native destination required')
    out.mkdir();owner={};h.capture_destination(owner,out)
    source=out/'source';fixture.write_project(source)
    if p.tree_hash(source)!=plan['fixture_files_sha256']:raise p.Rejected('fresh authored source differs')
    tools=p.tool_manifest(native_toolchain=nt)
    if tools!=plan['native_tools']:raise p.Rejected('frozen installed toolchain differs')
    config_before=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA)
    record=dict(schema=1,accepted=False,passed=False,status='failed',production_admitted=False,
        git_head=plan['git_head'],tools=tools,route_budget_seconds=120,
        scope='One required installed explicit1007 API fullSCH/protected-copper/ordinary-zone transport; independent distribution venv/copied JAR, no default/production/customDRU/GUI/physical/comparative admission.')
    try:
        result=p.route(source/(fixture.STEM+'.kicad_pcb'),out/'route',seconds=120,
            native_toolchain=nt,experimental_schematic_parity=True)
        if result.get('accepted') is not True:raise p.Rejected('new installed producer refused: '+str(result.get('reason',result.get('status'))))
        verified=read_transport(plan)
        record.update(passed=True,status='completed',transport=verified)
    except (Exception,KeyboardInterrupt) as exc:
        record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
    material=f.evidence_inventory(out)
    def remaining():return min(174-(time.monotonic()-START),174-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner);context(plan)
        if p.tool_manifest(native_toolchain=nt)!=tools or config_before!=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA):
            raise p.Rejected('installed tools/config changed')
        if p.tree_hash(source)!=plan['fixture_files_sha256'] or f.evidence_inventory(out)!=material:
            raise p.Rejected('source/completed installed transport changed')
        if record['passed']:p.check_experimental_local_settings(out/'route',f.read_json(out/'route/result.json'),nt)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0:record.update(passed=False,status='budget_exceeded')
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return f.read_json(out/'result.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True)
    args=parser.parse_args();plan=f.read_json(args.protocol)
    if p.sha(args.protocol)!=args.protocol_sha256:raise p.Rejected('frozen protocol changed')
    row=execute(plan);print(json.dumps({k:row[k] for k in ('passed','status','wall_seconds','full_cpu_seconds')}))
    raise SystemExit(0 if row['passed'] else 2)
