"""DRAFT: one isolated native parity-availability race; NOT executed by reviewer.

Read a retained accepted positive, then run only one fresh shared Job.drc stage.
Temporarily hide only its owned validation-copy schematic while KiCad executes.
This is a deliberately invalid availability control, never a route comparison.
"""
from pathlib import Path
import argparse,json,shutil,signal,sys,time
ROOT=Path(__file__).absolute().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,placement_clearance as pc,handoff as h
BASE=ROOT/'.runs/nus-native-paired-002/run/B2_portfolio/01-via_default/result.json'
STAGE='parity-unavailable-drc';SKIP='Failed to fetch schematic netlist for parity tests.'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).absolute()
    if ROOT/'.runs' not in out.parents or any(x.is_symlink() for x in (out,*out.parents)):raise p.Rejected('exclusive real local run output required')
    out.mkdir();owner={};h.capture_destination(owner,out)
    start=time.monotonic();cpu=time.process_time()+f.child_cpu();record={'schema':1,'status':'failed','passed':False,'native_control_executed':False,'full_pipeline_routing_receipt_created':False,'source_geometry_modified':False,'scope':'Deliberately unavailable owned validation-copy schematic during exactly one native DRC; before/after complete project restored. No native positive rerun, solver, export or route acceptance claim.'}
    def remaining():return min(30-(time.monotonic()-start),30-(time.process_time()+f.child_cpu()-cpu))
    def interrupted(signum,frame):raise KeyboardInterrupt
    previous={sig:signal.signal(sig,interrupted) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        p.check_result(BASE);baseline=f.read_json(BASE);source=Path(baseline['candidate']);baseline_before=pc.inventory(BASE.parent,max_bytes=32*1024**2)
        log_before=(BASE.parent/'final-drc.log').read_text()
        assert 'Found 5 schematic parity issues' in log_before and SKIP not in log_before
        assert baseline['accepted'] is True and baseline['schematic_parity']=='checked by final native DRC'
        assert [baseline['native'][k] for k in ('opens','blocking','warnings','exclusions')]==[0,0,10,0]
        shutil.copytree(source.parent,out/'candidate');board=out/'candidate'/source.name;before=pc.inventory(board.parent)
        assert before[source.name]==baseline['candidate_sha256'] and board.with_suffix('.kicad_sch').is_file() and not board.with_suffix('.sch').exists()
        p.save_json(out/'protocol.json',{'schema':1,'controller_sha256':p.sha(Path(__file__)),'baseline_receipt_sha256':p.sha(BASE),'baseline_candidate_sha256':baseline['candidate_sha256'],'baseline_complete_native_positive_reused':True,'source_hashes':before,'tools':p.tool_manifest(),'native_stages':['parity-unavailable-drc'],'wall_full_cpu_cap_seconds':30,'expected_defect':'Explicit native skipped-parity log plus ordinary native-accepted DRC must not be labelled checked; first execution is diagnostic and intentionally fails if existing Job.drc accepts it.'})
        class AvailabilityJob(p.Job):
            def step(self,name,argv,allowed=(0,)):
                if name!=STAGE:return super().step(name,argv,allowed)
                validation_board=Path(argv[-1]);sch=validation_board.with_suffix('.kicad_sch');held=self.out/'held-schematic.kicad_sch'
                assert '--schematic-parity' in [str(x) for x in argv] and sch.is_file() and not held.exists()
                original_bytes=pc.read_bytes(sch);sch.rename(held)
                try:return super().step(name,argv,allowed)
                finally:
                    if sch.exists():raise p.Rejected('native worker replaced deliberately absent schematic')
                    held.rename(sch)
                    assert pc.read_bytes(sch)==original_bytes
        job=AvailabilityJob(out/'job',remaining());job.env.update(LANG='C',LC_ALL='C')
        parsed=None;rejection=None
        try:parsed=job.drc(STAGE,board,schematic_parity=True)
        except p.Rejected as exc:rejection=str(exc)
        record['native_control_executed']=True
        raw=f.read_json(job.out/(STAGE+'.json'));native_log=(job.out/(STAGE+'.log')).read_text()
        assert SKIP in native_log and 'schematic parity issues' not in native_log,'control did not demonstrate native skipped parity'
        assert raw['schematic_parity']==[] and raw['source']==board.name and raw['kicad_version']=='10.0.0'
        binding=f.read_json(job.out/(STAGE+'-binding.json'))
        assert binding['before']==before and p.tree_hash(job.out/(STAGE+'-input'))==binding['after']
        p.check_drc_project(before,binding['after'],board.name)
        assert pc.inventory(board.parent)==before and pc.inventory(BASE.parent,max_bytes=32*1024**2)==baseline_before
        h.owned_destination(owner)
        native=p.parse_report(job.out/(STAGE+'.json'),board.name)
        record.update(native_parity_explicitly_skipped=True,native_report_sha256=p.sha(job.out/(STAGE+'.json')),native_log_sha256=p.sha(job.out/(STAGE+'.log')),native_counts={key:native[key] for key in ('opens','blocking','warnings','exclusions')},steps=job.steps,production_job_returned=parsed is not None,production_native_accepted=p.native_accepted(parsed) if parsed is not None else None,production_rejection=rejection,before_after_complete_schematic_preserved=True,baseline_unchanged=True)
        if parsed is not None:
            assert p.native_accepted(parsed),'control has another rejection; does not isolate parity availability'
            record.update(status='demonstrated_parity_availability_defect',passed=False)
        else:
            record.update(status='native_control_refused_diagnose_specific_rejection',passed=False)
    except (Exception,KeyboardInterrupt) as exc:record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',reason=type(exc).__name__+': '+str(exc))
    finally:
        try:
            record.update(wall_seconds=time.monotonic()-start,full_cpu_seconds=time.process_time()+f.child_cpu()-cpu)
            if max(record['wall_seconds'],record['full_cpu_seconds'])>30:record.update(passed=False,budget_exceeded=True)
            h.owned_destination(owner);p.save_json(out/'result.json',record)
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({key:record.get(key) for key in ('status','passed','reason','native_parity_explicitly_skipped','production_job_returned','production_native_accepted')}));return 2
if __name__=='__main__':raise SystemExit(main())
