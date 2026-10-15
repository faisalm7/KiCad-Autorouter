"""Fresh installed4Cu transport; same041 helpers, two separately bounded cases.
SPDX-License-Identifier: GPL-3.0-or-later
Draft only. Default1000 partial KEEP control and explicit1007 whole control.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,hashlib,json,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,sexpr as sx,board_floor as g,config as c
from experiments.four_copper_class_transport_v1 import forced_inner as fixture
from scripts import install_smoke as install
VERSIONS=('default1000_partial','explicit1007_whole')


def source_files(version):
    """New owned variant authored from creation; no executed input is edited."""
    if version not in VERSIONS:raise p.Rejected('fixed installed4Cu case required')
    files=fixture.files()
    if version=='default1000_partial':
        tree=sx.parse(files[fixture.STEM+'.kicad_pcb'].decode());routes=p.routes(tree)
        bridge=[row for row in routes if row[0]=='segment' and sx.one(row,'layer')==['layer','"B.Cu"'] and sx.one(row,'start')==['start','12','16'] and sx.one(row,'end')==['end','26','16']]
        if len(routes)!=10 or len(bridge)!=1 or any(not p.locked(row) for row in routes):raise p.Rejected('authored source bridge identity differs')
        bridge[0].remove(['locked','yes'])
        if sum(p.locked(row) for row in routes)!=9:raise p.Rejected('exact one newly authored unlocked bridge required')
        files[fixture.STEM+'.kicad_pcb']=(sx.dump(tree)+'\n').encode()
    return files


def context(plan):
    version=plan['version']
    if version not in VERSIONS:raise p.Rejected('fixed installed4Cu version required')
    if ROOT!=Path(plan['checkout']) or c.ROOT!=ROOT or Path(sys.executable)!=ROOT/'.venv/bin/python':raise p.Rejected('independent installed interpreter/context required')
    if Path(sys.prefix).resolve()!=ROOT/'.venv' or sys.prefix==sys.base_prefix:raise p.Rejected('independent installed venv required')
    for name,module in tuple(sys.modules.items()):
        if name.split('.')[0] in {'autorouter','scripts','experiments','tests'} and getattr(module,'__file__',None) and not Path(module.__file__).resolve().is_relative_to(ROOT):raise p.Rejected('project import escaped installed checkout: '+name)
    listing=(Path(plan['installation'])/'03-source-files.log').read_text();selected=install.distribution_listing(listing)
    inventory_path=Path(plan['installation'])/'source-tracked.json'
    if p.sha(inventory_path)!=plan['source_inventory_sha256']:raise p.Rejected('installation source inventory changed')
    original=f.read_json(inventory_path)
    if install.tracked_inventory(ROOT,selected)!={n:original[n] for n in selected.split('\0') if n}:raise p.Rejected('installed complete distribution changed')
    if install.git_identity(ROOT,plan['git_head'])!=plan['installed_git_identity']:raise p.Rejected('installed Git identity changed')
    if p.sha(Path(__file__))!=plan['installed_companion_sha256']:raise p.Rejected('installed companion changed')
    if any(p.sha(ROOT/name)!=pin for name,pin in plan['fixture_code_sha256'].items()):raise p.Rejected('owned factory changed')
    if {n:hashlib.sha256(raw).hexdigest() for n,raw in source_files(version).items()}!=plan['fixture_files_sha256']:raise p.Rejected('owned source variant differs')
    nt=None if version=='default1000_partial' else p.ExperimentalNativeToolchain.from_record(plan['native_toolchain'])
    if (nt is None and plan['native_toolchain'] is not None) or nt is not None and nt.expected_version!='10.0.7':raise p.Rejected('exact caller Native context required')
    original_jar=Path(plan['original_jar']);copy=c.JAR
    if not copy.is_relative_to(ROOT/'.tools') or copy.is_symlink() or original_jar.is_symlink() or copy.stat().st_ino==original_jar.stat().st_ino:raise p.Rejected('independent copied engine required')
    if p.sha(copy)!=plan['jar_sha256'] or p.sha(original_jar)!=plan['jar_sha256']:raise p.Rejected('pinned copied engine changed')
    return nt


def read_transport(plan):
    """Existing installed full semantic reader; no Native/engine worker."""
    nt=context(plan);version=plan['version'];kwargs={} if nt is None else dict(native_toolchain=nt,experimental_schematic_parity=True)
    out=Path(plan['native_output']);receipt=out/'route/result.json';material=f.evidence_inventory(out)
    data=f.read_json(receipt);source=out/'source'/(fixture.STEM+'.kicad_pcb');candidate=Path(data['candidate'])
    if data.get('tools')!=plan['native_tools'] or data.get('source')!=str(source) or data.get('budget_seconds')!=120 or data.get('cpu_budget_seconds')!=120:raise p.Rejected('installed source/budget/tool provenance differs')
    if p.tree_hash(source.parent)!=plan['fixture_files_sha256'] or data['source_hashes']!=plan['fixture_files_sha256']:raise p.Rejected('fresh complete source packet changed')
    if not source.with_suffix('.kicad_sch').is_file() or source.with_suffix('.kicad_dru').exists():raise p.Rejected('complete SCH/no-DRU owned source required')
    original=sx.read(source);current=sx.read(candidate);protected=p.protected_for_record(data,original)
    if len(protected)!=10 or len(p.routes(original))!=10 or sum(p.locked(row) for row in protected)!=(9 if nt is None else 10) or any(row not in p.routes(current) for row in protected):raise p.Rejected('all ten original KEEP routes, including authored unlocked bridge, must remain exact')
    if data.get('scope')!=('partial_completion' if nt is None else 'whole_board_unlocked_routing'):raise p.Rejected('fixed partial/whole scope differs')
    if p.immutable(original)!=p.immutable(current):raise p.Rejected('source invariants changed')
    generated=[row for row in p.routes(current) if row not in protected];_,resolve=g.source_net_identity(current)
    vias=[row for row in generated if row[0]=='via'];route_vias=[row for row in vias if resolve(sx.one(row,'net'))=='ROUTE']
    inner={resolve(sx.one(row,'net')) for row in generated if row[0] in ('segment','arc') and sx.one(row,'layer') in (['layer','"In1.Cu"'],['layer','"In2.Cu"'])}
    if any(sx.one(row,'layers')!=['layers','"F.Cu"','"B.Cu"'] for row in vias) or len(route_vias)<2 or not {'ROUTE','GND'}<=inner:raise p.Rejected('actual new inner ROUTE+GND and two ROUTE through-vias required')
    checked=p.check_result(receipt,**kwargs)
    if checked.get('current') is not True or data.get('accepted') is not True:raise p.Rejected('fresh installed producer/shared readback failed')
    default_refused=False
    if nt is not None:
        if data.get('production_admitted') is not False:raise p.Rejected('explicit route admission marker differs')
        try:p.check_result(receipt)
        except p.Rejected:default_refused=True
        if not default_refused:raise p.Rejected('default checker admitted explicit1007 result')
    native=data['native'];before=data['source_drc']
    if before['opens']!=2 or before['blocking'] or not p.native_accepted(native) or any(row.get('type')=='net_conflict' for row in native['findings']):raise p.Rejected('unchanged original two opens to fullSCH-connected prediction failed')
    if native.get('field_parity',{}).get('qualification',{}).get('component_count')!=6:raise p.Rejected('complete six-component effective-field proof required')
    if data['metrics']!=f.read_json(receipt.parent/'metrics.json') or data['metrics']['version']!=p.experimental_native_version(nt) or data['metrics']['copper_layers']!=4:raise p.Rejected('actual four-copper metrics differ')
    if p.sha(candidate)!=data['candidate_sha256'] or p.sha(receipt.parent/'final-drc.json')!=data['native_report_sha256']:raise p.Rejected('candidate/final report hash differs')
    p.check_resource_accounting(data);context(plan)
    if f.evidence_inventory(out)!=material:raise p.Rejected('completed transport changed during readback')
    p.check_experimental_local_settings(receipt.parent,data,nt)
    return dict(passed=True,version=version,route_scope=data['scope'],route_receipt_sha256=p.sha(receipt),candidate_sha256=data['candidate_sha256'],final_report_sha256=data['native_report_sha256'],source_sha256=data['source_hashes'],source_native_counts={k:before[k] for k in ('opens','blocking','warnings','exclusions')},final_native_counts={k:native[k] for k in ('opens','blocking','warnings','exclusions')},metrics=data['metrics'],worker_count=len(data['steps']),protected_routes=10,original_unlocked_routes=1 if nt is None else 0,generated_routes=len(generated),route_through_vias=len(route_vias),inner_route_nets=sorted(inner),complete_field_components=6,default_reader_refused=default_refused,material=material,shared_readback=checked,production_admitted=False)


def execute(plan):
    nt=context(plan);out=Path(plan['native_output'])
    if out!=ROOT/('.runs/installation042-'+plan['version']+'/native') or out.exists() or out.is_symlink():raise p.Rejected('fresh fixed installed case destination required')
    out.mkdir();owner={};h.capture_destination(owner,out);source=out/'source';source.mkdir()
    for name,raw in source_files(plan['version']).items():
        with (source/name).open('xb') as stream:stream.write(raw)
    if p.tree_hash(source)!=plan['fixture_files_sha256']:raise p.Rejected('fresh authored source differs')
    kwargs={} if nt is None else dict(native_toolchain=nt,experimental_schematic_parity=True)
    tools=p.tool_manifest(**kwargs_for_tools(nt))
    if tools!=plan['native_tools']:raise p.Rejected('frozen installed toolchain differs')
    config_before=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA)
    record=dict(schema=1,accepted=False,passed=False,status='failed',production_admitted=False,version=plan['version'],git_head=plan['git_head'],tools=tools,route_budget_seconds=120,scope=plan['scope'])
    routed=None
    try:
        routed=p.route(source/(fixture.STEM+'.kicad_pcb'),out/'route',seconds=120,keep_existing=nt is None,**kwargs)
        if routed.get('accepted') is not True:raise p.Rejected('fresh installed producer refused: '+str(routed.get('reason',routed.get('status'))))
        record.update(passed=True,status='completed',transport=read_transport(plan))
    except (Exception,KeyboardInterrupt) as exc:
        cancelled=isinstance(exc,KeyboardInterrupt) or bool(routed and (routed.get('status')=='cancelled' or any(row.get('status')=='cancelled' for row in routed.get('steps',[]))))
        record.update(passed=False,status='cancelled' if cancelled else 'failed',error=type(exc).__name__+': '+str(exc))
    material=f.evidence_inventory(out);record['completed_evidence']=material
    def remaining():return min(174-(time.monotonic()-START),174-(cpu()-CPU0))
    def stable():
        h.owned_destination(owner);context(plan)
        if p.tool_manifest(**kwargs_for_tools(nt))!=tools or config_before!=(c.CLI,c.PYTHON,c.PCBNEW,c.JAR,c.JAVA):raise p.Rejected('installed tools/config changed')
        if p.tree_hash(source)!=plan['fixture_files_sha256'] or f.evidence_inventory(out)!=material:raise p.Rejected('source/completed installed transport changed')
        if record['passed']:p.check_experimental_local_settings(out/'route',f.read_json(out/'route/result.json'),nt)
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
        if remaining()<=0 and record['status']=='completed':record.update(passed=False,status='budget_exceeded')
        if record['status']!='completed':record['passed']=False
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(out/'result.json')
    if f.canonical(stored)!=f.canonical(record):raise p.Rejected('installed child stored snapshot differs')
    return stored


def kwargs_for_tools(nt):return {} if nt is None else dict(native_toolchain=nt)


if __name__=='__main__':
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--protocol-sha256',required=True)
    args=parser.parse_args();plan=f.read_json(args.protocol)
    if p.sha(args.protocol)!=args.protocol_sha256:raise p.Rejected('frozen protocol changed')
    row=execute(plan);print(json.dumps({k:row[k] for k in ('passed','status','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if row['passed'] and row['status']=='completed' else 2)
