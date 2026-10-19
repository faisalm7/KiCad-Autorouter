"""Finite read-only receipt forecast enclosure; PREPARED, do not auto-run."""
from pathlib import Path
import argparse,hashlib,json,math,os,resource,stat,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
from autorouter.runner import run
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
CHILD=ROOT/'.runs/forecast-runtime041-capacity-receipt-001.py'
CHILD_SHA='838097f4d316d631f15870d8124e798493cb38c329f0523e611d7bc09bf80c08'
BACKUP_SHA='a74350a473b2788f85ac6681dba74760681817a3ae122327c16d3e9932472477'
RUNNER_SHA='050cf3ef88baf6c2efcc00e575d6d1f4c82b73ad084b6499f265e8fca9c17c8e'

def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))

def completed_report(path, source_head):
    """A successful process without its exact bounded report is not a pass."""
    def unique(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('Duplicate forecast report key')
            result[key]=value
        return result
    def number(text):
        value=float(text)
        if not math.isfinite(value):raise ValueError('Nonfinite forecast report number')
        return value
    def constant(text):raise ValueError('Nonfinite forecast report constant')
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        before=os.fstat(stream.fileno())
        assert stat.S_ISREG(before.st_mode) and before.st_nlink==1 and 0<before.st_size<=64*1024
        raw=stream.read(64*1024+1);after=os.fstat(stream.fileno())
    assert len(raw)==before.st_size and after.st_nlink==1
    assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns)
    report=json.loads(raw.decode('utf8'),object_pairs_hook=unique,parse_float=number,parse_constant=constant)
    assert type(report) is dict and type(report.get('schema')) is int and report['schema']==1
    assert report.get('forecast_completed') is True and report.get('status')=='read_only_forecast_completed_not_backup'
    assert report.get('source_head')==source_head and report.get('production_caps_restored') is True
    assert all(report.get(key) is False for key in ('backup_created','archive_created','restoration_performed','native_executed','Git_executed','subprocess_executed_by_child','exclusions_added','authoritative_backup_or_release_qualification'))
    assert report.get('scopes')==['.runs','.data','.local-reference']
    assert all(type(report.get(key)) is dict for key in ('inventory','compact_delta','receipt_forecast','restore_capacity','end_to_end_capacity'))
    return report,hashlib.sha256(raw).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-head',required=True)
    parser.add_argument('--writers-idle',action='store_true')
    parser.add_argument('--tracked-stat-index')
    parser.add_argument('--tracked-stat-sha256')
    args=parser.parse_args()
    assert args.writers_idle and sys.platform=='darwin'
    assert H(CHILD)==CHILD_SHA and H(ROOT/'scripts/backup.py')==BACKUP_SHA and H(ROOT/'autorouter/runner.py')==RUNNER_SHA
    assert (args.tracked_stat_index is None)==(args.tracked_stat_sha256 is None)
    out=ROOT/'.runs/runtime041-capacity-receipt-001'
    assert not os.path.lexists(out);out.mkdir()
    start=time.monotonic();cpu0=cpu()
    argv=[str(ROOT/'.venv/bin/python'),'-B',str(CHILD),'--output',str(out/'forecast.json'),'--source-head',args.source_head,'--writers-idle']
    if args.tracked_stat_index is not None:
        argv+=['--tracked-stat-index',str(Path(args.tracked_stat_index).absolute()),'--tracked-stat-sha256',args.tracked_stat_sha256]
    pins=dict(child=CHILD_SHA,backup=BACKUP_SHA,runner=RUNNER_SHA,self=H(Path(__file__)))
    with (out/'protocol.json').open('x') as f:
        json.dump(dict(schema=1,source_head=args.source_head,writers_idle_asserted=True,source_sha256=pins,child_argv=argv,limits=dict(whole_wall_seconds=600,whole_CPU_acceptance_seconds=600,child_alarm_seconds=590,group_RSS_bytes=2*1024**3,output_bytes=64*1024**2,log_bytes=64*1024**2),scope='Forecast only; no Native/GUI/Git/archive/restore/capture. No production limits changed.'),f,indent=2);f.write('\n')
    process=run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',*argv],cwd=out,log=out/'command.log',timeout=max(.001,600-(time.monotonic()-start)),max_log_bytes=64*1024**2,max_workdir_bytes=64*1024**2,max_group_rss_bytes=2*1024**3)
    report_valid=False;report_sha=None;report_error=None
    try:
        _,report_sha=completed_report(out/'forecast.json',args.source_head)
        report_valid=H(out/'forecast.json')==report_sha
    except Exception as exc:report_error=type(exc).__name__+': '+str(exc)
    stable=H(CHILD)==CHILD_SHA and H(ROOT/'scripts/backup.py')==BACKUP_SHA and H(ROOT/'autorouter/runner.py')==RUNNER_SHA and H(Path(__file__))==pins['self']
    record=dict(schema=1,process=process,sources_unchanged=stable,wall_seconds=time.monotonic()-start,full_CPU_seconds=cpu()-cpu0,forecast_sha256=report_sha,forecast_report_valid=report_valid,forecast_report_error=report_error,passed=False,backup_created=False,restoration_performed=False,scope='passed means the bounded forecast completed, never backup/restore or resource-cap qualification; external whole-process timing remains separate.')
    record['passed']=report_valid and stable and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and not process['log_truncated'] and record['wall_seconds']<=600 and record['full_CPU_seconds']<=600
    with (out/'execution.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
    print(json.dumps(record))
    return 0 if record['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
