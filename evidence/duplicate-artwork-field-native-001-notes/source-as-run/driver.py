"""Bounded Native field-census prerequisite; no routing or net-tie admission.

Uses the shared validator, bounded Job, stage reader and publication helper.
SPDX-License-Identifier: GPL-3.0-or-later
"""
import time, resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
import argparse, fcntl, importlib.util, json, os, signal, stat, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, sexpr as sx, schematic_field_evidence as fields
from experiments.hfe_original_native_v1.driver import BoundJob, material
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.duplicate_artwork_fields_v1 import fixture
BASE_HEAD='2f21e0beed8f3c2cd37178371bbb9ae69971caa4'

def prepare(folder):
    folder.mkdir();tools=p.tool_manifest()
    if subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=normal'],cwd=ROOT,timeout=10).strip():raise p.Rejected('clean checkpoint required')
    old=subprocess.check_output(['git','show',BASE_HEAD+':autorouter/schematic_field_evidence.py'],cwd=ROOT,timeout=10)
    copy_bytes({'previous-field-evidence.py':old},folder/'control')
    for case in fixture.CASES:copy_bytes(fixture.files(case),folder/case)
    extra=['experiments/duplicate_artwork_fields_v1/driver.py','experiments/duplicate_artwork_fields_v1/fixture.py',
           'experiments/native_schematic_toolchain_v1/fixture.py','experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py']
    plan=dict(schema=1,tools=tools,code_sha256={n:p.sha(ROOT/n) for n in extra},
        source_hashes={case:p.tree_hash(folder/case) for case in fixture.CASES},previous_source_sha256=p.sha(folder/'control/previous-field-evidence.py'),
        previous_source_head=BASE_HEAD,limits=dict(wall_full_cpu_seconds=120,worker_seconds=110,group_rss_bytes=2*1024**3,logs=256*1024,scratch_bytes=128*1024**2),
        scope='Owned field-census positive and hidden ordinary Description negative on actual production10.0.0. Exact two padless same-reference artwork members. Original constraints/fullSCH/refill/protected copper required. Retain all findings. No engine/DSN/net-tie/hierarchy/platform/routing-quality admission.',
        preparation_costs=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2))
    p.save_json(folder/'protocol.json',plan);print(json.dumps(dict(prepared=True,native_executed=False)))

def execute(folder,out):
    plan=f.read_json(folder/'protocol.json');pin=p.sha(folder/'protocol.json')
    def current():
        if p.sha(folder/'protocol.json')!=pin or p.tool_manifest()!=plan['tools']:raise p.Rejected('protocol/runtime changed')
        if any(p.sha(ROOT/n)!=v for n,v in plan['code_sha256'].items()):raise p.Rejected('control code changed')
        if any(p.tree_hash(folder/case)!=v for case,v in plan['source_hashes'].items()):raise p.Rejected('original control source changed')
        if p.sha(folder/'control/previous-field-evidence.py')!=plan['previous_source_sha256']:raise p.Rejected('previous producer changed')
    current();out.mkdir();owner={};h.capture_destination(owner,out)
    prep=plan['preparation_costs']
    def remaining():return min(110-(time.monotonic()-START),110-(cpu()-CPU0),118-prep['wall_seconds']-2-(time.monotonic()-START),118-prep['full_cpu_seconds']-2-(cpu()-CPU0))
    record=dict(schema=1,accepted=False,passed=False,status='failed',tools=plan['tools'],protocol_sha256=pin,cases={},scope=plan['scope'])
    def interrupted(signum,frame):raise KeyboardInterrupt('diagnostic termination requested')
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared Native lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            spec=importlib.util.spec_from_file_location('autorouter._previous_field_evidence',folder/'control/previous-field-evidence.py')
            previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
            for case in fixture.CASES:
                caseout=out/case;caseout.mkdir();source=folder/case/(fixture.STEM+'.kicad_pcb')
                candidate=caseout/'candidate'/source.name;copy_bytes(fixture.files(case),candidate.parent)
                before=plan['source_hashes'][case];assert p.tree_hash(candidate.parent)==before
                original=sx.read(source);protected=[r for r in p.routes(original) if p.locked(r)]
                job=BoundJob(caseout/'job',min(110,remaining()),remaining,protect_local_settings=True)
                digest,native=p.validate_candidate(job,original,candidate,before,protected)
                refill_input=job.out/'refill'/source.name
                refill_native=f.check_drc_stage(job.out,{'steps':job.steps},'refill-drc',refill_input,refill_input,True,before)
                final_input=job.out/'final-drc-input'/source.name
                observed=f.check_drc_stage(job.out,{'steps':job.steps},'final-drc',candidate,final_input,False,
                    {**before,source.name:digest},schematic_parity=True)
                if observed!=native:raise p.Rejected('shared final-stage readback differs')
                raw=f.read_json(job.out/'final-drc.json');proof=f.read_json(fields.paths(job.out,'final-drc')[2])
                census=proof.get('board_only_field_census',{})
                if census.get('policy')!='source-bound-padless-field-census-v2' or census.get('complete_footprint_count')!=6 or census.get('compared_footprint_count')!=4 or {r['uuid'] for r in census.get('artwork',[])}!=set(fixture.ART_UUIDS):raise p.Rejected('actual complete duplicate-artwork census absent')
                if census.get('duplicate_artwork_reference_groups')!=[{'folded_reference':'g***','uuids':sorted(fixture.ART_UUIDS)}]:raise p.Rejected('duplicate artwork group proof differs')
                warnings=[r for r in raw['schematic_parity'] if r['type']==fields.TYPE]
                ordinary={fixture.base.uid(ref+'-footprint') for ref,*_ in fixture.base.TERMINALS}
                if len(warnings)!=4 or {r['items'][0]['uuid'] for r in warnings}!=ordinary or any(r['description']!="Field 'Datasheet' differs (PCB: '~', Schematic: '')" for r in warnings):raise p.Rejected('actual conditional Datasheet bridge was not exercised')
                if case=='positive':
                    if not p.native_accepted(native) or not fields.qualified(native):raise p.Rejected('owned positive did not qualify')
                    observation=f.read_json(fields.paths(job.out,'final-drc')[1]);netlist=fields.paths(job.out,'final-drc')[0].read_text()
                    try:previous.project_board_only_fields(sx.read(final_input),netlist,observation,raw)
                    except ValueError as exc:
                        old_refusal=str(exc)
                        if old_refusal!='unique source footprint references required':raise p.Rejected('previous producer refused for a different reason') from exc
                    else:raise p.Rejected('previous duplicate-reference refusal not reproduced')
                else:
                    old_refusal=None
                    if p.native_accepted(native) or fields.qualified(native) or 'Description' not in proof['qualification'].get('reason',''):raise p.Rejected('ordinary hidden Description mismatch escaped')
                if p.immutable(original)!=p.immutable(sx.read(candidate)) or any(r not in p.routes(sx.read(candidate)) for r in protected):raise p.Rejected('original geometry/protected copper changed')
                p.verify_candidate_files(candidate,before,digest)
                record['cases'][case]=dict(native_accepted=p.native_accepted(native),native=native,refill_native=refill_native,final_candidate_sha256=digest,
                    final_report_sha256=p.sha(job.out/'final-drc.json'),field_proof_sha256=p.sha(fields.paths(job.out,'final-drc')[2]),
                    previous_source_refusal=old_refusal,steps=job.steps,source_unchanged=p.tree_hash(source.parent)==before)
            record.update(passed=True,status='completed')
        except (Exception,KeyboardInterrupt) as exc:record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
        witness=material(out);record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner);current()
            if material(out)!=witness:raise p.Rejected('completed Native evidence changed')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,preparation_costs=prep)
            if remaining()<=0:record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    stored=f.read_json(out/'result.json');print(json.dumps({k:stored.get(k) for k in ('passed','status','reason','wall_seconds','full_cpu_seconds')}))
    return 0 if stored.get('passed') is True and stored.get('status')=='completed' else 2

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run']);parser.add_argument('--preparation',type=Path,required=True);parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    args.preparation=args.preparation.absolute()
    if args.output is not None:args.output=args.output.absolute()
    if args.mode=='prepare':prepare(args.preparation)
    else:
        if args.output is None:parser.error('--output required')
        raise SystemExit(execute(args.preparation,args.output))
