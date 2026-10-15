"""Unexecuted original-only worker fragment; caller owns frozen enclosure/publication.

SPDX-License-Identifier: GPL-3.0-or-later
No CLI, Native result, source repair or production admission is supplied here.
"""
from pathlib import Path
import hashlib
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
from autorouter import sexpr as sx, local_settings as ls
from data import fetch
from experiments.hfe_original_native_v1 import driver as original
from experiments.original_project_native_v1.driver import route_records
from experiments.placement_handoff_native_v1.driver import copy_bytes

ROOT = original.ROOT
BINDING = Path(__file__).with_name('SOURCE_BINDING.json')


def capture():
    """Existing local manifest verifier only; never fetch, stage or execute data."""
    spec = f.read_json(BINDING)
    if p.sha(ROOT/'data/sources.json') != spec['manifest_sha256']:
        raise p.Rejected('frozen full managed manifest changed')
    manifest = fetch.load_manifest()
    if (manifest['commit'] != spec['source_commit']
            or manifest['repository'] != spec['repository']):
        raise p.Rejected('fixed official source revision differs')
    source = ROOT/spec['source_relative']
    before = io.inventory(source, max_bytes=8*1024**2, max_files=64, max_entries=128)
    files = {}
    for row in manifest['files']:
        if row['project_id'] != spec['project_id']:
            continue
        path = fetch.safe_destination(row['destination'])
        name = str(path.relative_to(source))
        if name in files:
            raise p.Rejected('duplicate source destination')
        raw = io.read_bytes(path, 8*1024**2)
        fetch.verify_bytes(raw, row)
        files[name] = raw
    pins = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    if (pins != spec['source_files_sha256'] or before != pins
            or len(files) != 52 or sum(map(len, files.values())) != 4384337
            or io.inventory(source, max_bytes=8*1024**2, max_files=64, max_entries=128) != before
            or p.sha(ROOT/'data/sources.json') != spec['manifest_sha256']):
        raise p.Rejected('complete immutable source/notice packet differs')
    return spec, files


def observe(job, tools):
    """Use a caller-owned existing BoundJob; return record + late stage check.

    Caller must pin this fragment/binding, default1000 tools, all current code,
    HEAD/tools and source before/after; own the quality lane, whole cost and
    material/literal publication through existing HFE/f.publish scaffolding.
    This fragment does not create its own lifecycle, runner or protocol.
    """
    if (not isinstance(job, original.BoundJob) or job.native_toolchain is not None
            or p.experimental_native_version(job.native_toolchain) != '10.0.0'
            or job.protect_local_settings is not True
            or job.experimental_schematic_parity is not False):
        raise p.Rejected('existing owned protected default1000 BoundJob required')
    if p.tool_manifest(native_toolchain=job.native_toolchain) != tools:
        raise p.Rejected('caller frozen tool/implementation context differs')
    spec, files = capture()
    copy_bytes(files, job.out/'original')
    board = job.out/'original'/(spec['stem']+'.kicad_pcb')
    source = sx.read(board)
    routes = route_records(source)
    if len(routes) != spec['source_routes'] or len(routes) != 3188:
        raise p.Rejected('complete original route UUID census differs')
    record = dict(schema=1, accepted=False, passed=False, status='failed',
        production_support_qualified=False, routing_executed=False,
        observation_complete=False, tools=tools, steps=job.steps,
        source_commit=spec['source_commit'], source_hashes=spec['source_files_sha256'],
        source_file_count=52, source_bytes=4384337, source_route_count=len(routes))
    stages = []
    candidate = None
    try:
        saved = job.out/'saved'
        copy_bytes(files, saved)
        savedboard = saved/board.name
        before = p.tree_hash(saved)
        stages.append(('original-refill', savedboard, savedboard, True, before, False, None))
        refill = job.drc('original-refill', savedboard, save=True)
        stages[-1] = (*stages[-1][:-1], refill)
        emitted = sx.read(savedboard)
        record.update(native_saved_nonfill_ast_equal=p.immutable(source)==p.immutable(emitted),
            native_saved_route_records_equal=routes==route_records(emitted))
        candidate = job.out/'candidate'/board.name
        copy_bytes(files, candidate.parent)
        sx.write(candidate, p.transplant_fill(source, emitted))
        if p.immutable(sx.read(candidate)) != p.immutable(source) or route_records(sx.read(candidate)) != routes:
            raise p.Rejected('original shell/all original routes changed')
        p.verify_candidate_files(candidate, spec['source_files_sha256'], p.sha(candidate))
        before = p.tree_hash(candidate.parent)
        stages.append(('original-final', candidate, job.out/'original-final-input'/board.name, False, before, True, None))
        final = job.drc('original-final', candidate, schematic_parity=True)
        stages[-1] = (*stages[-1][:-1], final)
        record.update(observation_complete=True, original_native=refill, parity_native=final,
            final_candidate=str(candidate), final_candidate_sha256=p.sha(candidate),
            final_native_report_sha256=p.sha(job.out/'original-final.json'),
            original_shell_nonfill_ast_equal=True, all_original_route_records_exact=True,
            native_routing_scope_accepted=p.native_accepted(final),
            passed=True, status='completed',
            native_rejection_reasons=p.native_rejection_reasons(final),
            passed_scope='Completed original-only observation; never routing or production acceptance')
    except (Exception, KeyboardInterrupt) as exc:
        cancelled = isinstance(exc, KeyboardInterrupt) or any(row.get('status')=='cancelled' for row in job.steps)
        record.update(passed=False, status='cancelled' if cancelled else 'failed', error=type(exc).__name__+': '+str(exc))
    record['raw_reports'] = {}
    try:
        for name, *_ in stages: record['raw_reports'][name] = original.raw_stage(job, name)
    except KeyboardInterrupt as exc:
        record.update(passed=False,status='cancelled',error=type(exc).__name__+': '+str(exc))
    record['stage_bindings'] = [dict(name=name,source=str(src),input=str(inp),saved=saved,before=before,schematic_parity=parity)
        for name,src,inp,saved,before,parity,native in stages]


    def check():
        return read_observation(job.out, record, tools)
    try:
        check()
    except (Exception, KeyboardInterrupt) as exc:
        cancelled = isinstance(exc, KeyboardInterrupt) or any(row.get('status')=='cancelled' for row in job.steps)
        record.update(passed=False, native_routing_scope_accepted=False,
            status='cancelled' if cancelled else 'failed',
            error='shared original readback: '+type(exc).__name__+': '+str(exc))
    return record, check


def read_observation(job_out, record, tools):
    """Pure retained replay through shared stage/source/PRL helpers; no worker."""
    job_out=ls.canonical(Path(job_out));spec,files=capture()
    if (record.get('accepted') is not False or record.get('production_support_qualified') is not False
            or record.get('routing_executed') is not False or record.get('tools')!=tools
            or record.get('source_hashes')!=spec['source_files_sha256']
            or record.get('source_commit')!=spec['source_commit'] or record.get('source_file_count')!=52
            or record.get('source_bytes')!=4384337 or record.get('source_route_count')!=3188):
        raise p.Rejected('fixed original-only default1000 identity differs')
    if p.tool_manifest()!=tools:raise p.Rejected('current default1000 tool/code differs')
    board=job_out/'original'/(spec['stem']+'.kicad_pcb');source=sx.read(board)
    if p.tree_hash(board.parent)!=spec['source_files_sha256'] or len(route_records(source))!=3188:
        raise p.Rejected('all52 original source/all3188routes differ')
    if record.get('observation_complete') is not True:
        if record.get('passed') is True:raise p.Rejected('incomplete diagnostic cannot pass')
        return False  # Entire failure material/process/raw reports are bound by caller witness.
    saved=job_out/'saved'/board.name;candidate=job_out/'candidate'/board.name
    emitted=sx.read(saved)
    if (record.get('native_saved_nonfill_ast_equal') is not (p.immutable(source)==p.immutable(emitted))
            or record.get('native_saved_route_records_equal') is not (route_records(source)==route_records(emitted))
            or record.get('original_shell_nonfill_ast_equal') is not True or record.get('all_original_route_records_exact') is not True):
        raise p.Rejected('saved serializer/original-shell observation differs')
    expected=p.transplant_fill(source,emitted)
    if sx.read(candidate)!=expected or p.immutable(expected)!=p.immutable(source) or route_records(expected)!=route_records(source):
        raise p.Rejected('exact original shell/Nativefill/all route records changed')
    p.verify_candidate_files(candidate,spec['source_files_sha256'],record['final_candidate_sha256'])
    before_final=dict(spec['source_files_sha256']);before_final[board.name]=record['final_candidate_sha256']
    stages=[dict(name='original-refill',source=str(saved),input=str(saved),saved=True,before=spec['source_files_sha256'],schematic_parity=False),
        dict(name='original-final',source=str(candidate),input=str(job_out/'original-final-input'/board.name),saved=False,before=before_final,schematic_parity=True)]
    if record.get('stage_bindings')!=stages:raise p.Rejected('exact two original Native stage bindings differ')
    from autorouter import schematic_field_evidence as fields
    required={'original-refill','original-final'}
    if fields.has_fields(record['parity_native']['findings']):required.update(fields.names('original-final'))
    if (len(record['steps'])!=len(required) or {row.get('name') for row in record['steps']}!=required
            or any(row.get('cwd')!=str(job_out) for row in record['steps'])):
        raise p.Rejected('original-only process population differs')
    for row,key in zip(stages,('original_native','parity_native')):
        replay=f.check_drc_stage(job_out,record,row['name'],Path(row['source']),Path(row['input']),row['saved'],row['before'],
            schematic_parity=row['schematic_parity'],native_toolchain=None,experimental_schematic_parity=False)
        if f.canonical(replay)!=f.canonical(record[key]):raise p.Rejected('original shared Native stage replay differs')
    if (p.sha(candidate)!=record['final_candidate_sha256'] or p.sha(job_out/'original-final.json')!=record['final_native_report_sha256']
            or record['native_routing_scope_accepted'] is not p.native_accepted(record['parity_native'])
            or record['native_rejection_reasons']!=p.native_rejection_reasons(record['parity_native'])):
        raise p.Rejected('final candidate/report/Native outcome differs')
    if capture()!=(spec,files):raise p.Rejected('acquired originals changed late')
    ls.check_normal_policy(job_out,record,max_bytes=128*1024**2,max_files=2048,native_toolchain=None)
    return True
