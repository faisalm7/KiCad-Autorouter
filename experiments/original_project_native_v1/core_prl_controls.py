"""Actual opt-in Job PRL boundary controls; no format or routing admission.

The exact already acquired PAW original supplies a positive and a deliberately
opened MISO net. Existing native/process/readback/publication helpers own checks.
No reference routing is supplied to an optimizer; no engine or acquisition runs.
"""
from pathlib import Path
import argparse, copy, hashlib, shutil, sys, time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, placement_clearance as io, sexpr as sx
from experiments.licensed_acquisition_v2 import native_snapshot as source
from experiments.original_project_native_v1.driver import copy_bytes, route_records
SECONDS=90; LIMIT=20*1024**2


def experiment(output):
    output=Path(output)
    if (not output.is_absolute() or output.resolve()!=output or output.parent!=ROOT/'.runs'
            or output.exists() or output.is_symlink()):raise p.Rejected('fresh direct canonical controls output required')
    started=time.monotonic();cpu=time.process_time()+f.child_cpu()
    output.mkdir();owner={};h.capture_destination(owner,output)
    captured=source.capture();copy_bytes(captured,output/'original')
    original_board=output/'original/paw3395.kicad_pcb';original=sx.read(original_board)
    source_hashes=p.tree_hash(original_board.parent);tools=p.tool_manifest();completed={};rows=[]
    extra=('experiments/original_project_native_v1/core_prl_controls.py','experiments/original_project_native_v1/driver.py',
           'experiments/placement_handoff_native_v1/driver.py','experiments/licensed_acquisition_v2/native_snapshot.py',
           'experiments/licensed_acquisition_v2/protocol.json','experiments/licensed_acquisition_v1/fetch.py')
    code={name:io.read_bytes(ROOT/name) for name in (*tools['implementation_sha256'],*extra)}
    copy_bytes(code,output/'code')
    record=dict(schema=1,kind='core_job_prl_boundary_controls',status='incomplete',accepted=False,
        production_admitted=False,controls_passed=False,budget_seconds=SECONDS,cpu_budget_seconds=SECONDS,
        retained_output_cap_bytes=LIMIT,tools=tools,source_hashes=source_hashes,cases=rows,
        worker_caps=dict(output_bytes=512*1024**2,group_rss_bytes=4*1024**3,log_bytes=2000000),
        code_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in code.items()},
        scope='New explicit core Job opt-in boundary on immutable original PAW and deliberately MISO-open owned candidate; actual savedrefill/originalshell/fullSCH. No new GET/export/engine or format/production/routing-quality/pedigree/physical approval.')
    def remaining():return max(0,min(SECONDS-(time.monotonic()-started),SECONDS-(time.process_time()+f.child_cpu()-cpu)))
    def stable():
        h.owned_destination(owner)
        if remaining()<=0:raise p.Rejected('core PRL controls wall/fullCPU budget exhausted')
        if source.capture()!=captured or p.tree_hash(original_board.parent)!=source_hashes or p.tool_manifest()!=tools:
            raise p.Rejected('core PRL original/runtime changed')
        if source_hashes!={name:hashlib.sha256(raw).hexdigest() for name,raw in captured.items()}:
            raise p.Rejected('core PRL capture to original copy differs')
        if p.tree_hash(output/'code')!=record['code_sha256']:raise p.Rejected('retained core PRL code differs')
        if any(p.sha(ROOT/name)!=pin for name,pin in record['code_sha256'].items()):raise p.Rejected('core PRL code changed')
        for directory,pins in completed.items():
            if io.evidence_inventory(directory)!=pins:raise p.Rejected('completed core PRL case changed')
        io.inventory(output,max_bytes=LIMIT,max_files=2500,max_entries=5000)
    def account():
        record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=time.process_time()+f.child_cpu()-cpu,
                      within_budget=remaining()>0)
        if record['status']!='completed' or not record['within_budget']:record['controls_passed']=False
    try:
        try:p.preflight(original_board)
        except p.Rejected as exc:record['source_static_supported']=False;record['source_static_refusal']=str(exc)
        else:record['source_static_supported']=True
        stable()
        for case in ('positive','miso_open'):
            stable();job=f.FloorJob(output/case,remaining(),remaining,protect_local_settings=True)
            candidate=job.out/'candidate'/original_board.name;shutil.copytree(original_board.parent,candidate.parent)
            if case=='miso_open':
                modified=copy.deepcopy(original)
                codes={sx.unquote(n[2]):n[1] for n in sx.children(original,'net')};code=codes['MISO']
                removed=[n for n in p.routes(modified) if sx.one(n,'net')==['net',code]]
                if not removed:raise p.Rejected('controlled MISO routes absent')
                for n in removed:modified.remove(n)
                sx.write(candidate,modified)
            row=dict(case=case,passed=False,steps=job.steps)
            before={**source_hashes,candidate.name:p.sha(candidate)}
            rows.append(row)
            try:
                digest,native=p.validate_candidate(job,original,candidate,source_hashes,[])
                refill=job.out/'refill'/candidate.name
                saved=f.check_drc_stage(job.out,row,'refill-drc',refill,refill,True,before)
                final_input=job.out/'final-drc-input'/candidate.name
                final=f.check_drc_stage(job.out,row,'final-drc',candidate,final_input,False,{**source_hashes,candidate.name:digest},schematic_parity=True)
                if f.canonical(native)!=f.canonical(final):raise p.Rejected('core final report differs')
                p.check_legacy_zone_evidence(job.out,original,candidate,implementation=tools['implementation_sha256'])
                expected=p.native_accepted(native) if case=='positive' else not p.native_accepted(native) and native['opens']>0
                row.update(candidate_sha256=digest,native=native,saved_native=saved,
                    native_report_sha256=p.sha(job.out/'final-drc.json'),legacy_witness=f.read_json(job.out/'legacy-zone-witness.json'),
                    all_original_routes_exact=route_records(sx.read(candidate))==route_records(original),
                    source_prl_flags=original_board.with_suffix('.kicad_prl').stat().st_flags,
                    candidate_prl_flags=candidate.with_suffix('.kicad_prl').stat().st_flags,
                    passed=bool(expected))
                if row['source_prl_flags']!=0 or row['candidate_prl_flags']!=0:raise p.Rejected('core PRL flags not restored')
                if case=='positive' and not row['all_original_routes_exact']:raise p.Rejected('positive control original routing changed')
            except (Exception,KeyboardInterrupt) as exc:
                row.update(passed=False,error=type(exc).__name__+': '+str(exc));raise
            finally:p.save_json(job.out/'control.json',row)
            completed[job.out]=io.evidence_inventory(job.out);stable()
        record.update(status='completed',controls_passed=len(rows)==2 and all(row['passed'] for row in rows),
            completed_evidence={str(directory):pins for directory,pins in completed.items()})
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc),controls_passed=False)
    f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    return record


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run-native',action='store_true');parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if not args.run_native:parser.error('explicit Native required')
    result=experiment(args.output);print({k:result.get(k)for k in ('status','controls_passed','error','wall_seconds','total_cpu_seconds')});raise SystemExit(0 if result['controls_passed']else 2)
