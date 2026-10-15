"""One sequential bounded fullSCH/fields diagnostic via existing shared runner."""
import time,resource
START=time.monotonic()
def cpu():
    own=resource.getrusage(resource.RUSAGE_SELF);child=resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime+own.ru_stime+child.ru_utime+child.ru_stime
CPU0=cpu()
from pathlib import Path
import fcntl,json,os,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file());sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
from autorouter.runner import run
from experiments.native_schematic_toolchain_v1.continuation import reference_records,REFERENCE
from autorouter import schematic_field_evidence as fields
_,historical_record,previous=reference_records()
out=ROOT/'.runs/native-schematic-hidden-execution-001';out.mkdir();owner={};h.capture_destination(owner,out);tools=p.tool_manifest()
expected_code={str(path):p.sha(path) for path in Path(__file__).resolve().parent.glob('*.py')}
expected_case_paths={str(out/'native'/(version+'-hidden_later_description')) for version in ('10.0.0','10.0.7')}
lockpath=ROOT/'.runs/quality-experiment.lock'
if any(x.is_symlink() for x in (lockpath,*lockpath.parents)):raise p.Rejected('shared lock alias')
fd=os.open(lockpath,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
with os.fdopen(fd,'r+') as lock:
    info=os.fstat(lock.fileno())
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary exclusive shared lock required')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    process=run([str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'experiments/native_schematic_toolchain_v1/continuation.py'),'--run-native','--output',str(out/'native')],cwd=out,log=out/'command.log',timeout=max(.001,188-previous['wall_seconds']-(time.monotonic()-START)),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
    current=p.tool_manifest()==tools
    child_path=out/'native/result.json'
    child_record=f.read_json(child_path) if child_path.is_file() else None
    child_material=p.tree_hash(out/'native') if (out/'native').is_dir() else None
    child_complete=(child_record is not None and child_record.get('status')=='completed' and child_record.get('controls_passed') is True
        and child_record.get('code_sha256')==expected_code and set(child_record.get('completed_evidence',{}))==expected_case_paths
        and {(row.get('version'),row.get('case')) for row in child_record.get('cases',[])}=={(v,'hidden_later_description') for v in ('10.0.0','10.0.7')}
        and len(child_record.get('cases',[]))==2 and all(row.get('checks',{}).get('passed') is True
        and row.get('same_actual_findings_as_prior_positive') is True for row in child_record['cases']))
    wall=time.monotonic()-START;full=cpu()-CPU0
    passed=child_complete and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated'] and current and max(wall+previous['wall_seconds'],full+previous['full_cpu_seconds'])+2<=190
    record=dict(schema=1,accepted=False,status='completed' if passed else 'failed',passed=passed,source_current=current,process=process,tools=tools,git_head=tools['git_head'],controller_sha256=p.sha(Path(__file__)),log_sha256=p.sha(out/'command.log'),wall_seconds=wall,full_cpu_seconds=full,publication_allowance_seconds=2,whole_wall_full_cpu_cap_seconds=190,prior_charged_enclosure_costs=previous,child_material_sha256=child_material,expected_code_sha256=expected_code,child_receipt_sha256=p.sha(child_path) if child_record else None,scope='Only2newDescriptionnegatives with4completedindividualNative002controls reusedwithoutworkers. Allfailed001/002enclosurecosts plus2tail each carry into cumulative190wall/fullCPUcap; unchanged original rules/PRL/refill/fullSCH/version/process/fields retained. Originalaggregate002staysfailed, no normalrouting/engine/gain claim.')
    def remaining():return max(0,min(188-previous['wall_seconds']-(time.monotonic()-START),188-previous['full_cpu_seconds']-(cpu()-CPU0)))
    def stable():
        h.owned_destination(owner)
        if p.tool_manifest()!=tools or p.sha(Path(__file__))!=record['controller_sha256']:raise p.Rejected('frozen enclosure source changed')
        if p.sha(out/'command.log')!=record['log_sha256']:raise p.Rejected('Native enclosure log changed')
        if child_record is None or f.canonical(f.read_json(out/'native/result.json'))!=f.canonical(child_record):raise p.Rejected('child published receipt changed')
        if child_record.get('code_sha256')!=expected_code or any(p.sha(Path(name))!=pin for name,pin in expected_code.items()):raise p.Rejected('child captured source differs')
        declared=child_record.get('completed_evidence')
        if type(declared) is not dict or set(declared)!=expected_case_paths:raise p.Rejected('child completed case population differs')
        for name,inventory in declared.items():
            if p.tree_hash(Path(name))!=inventory:raise p.Rejected('child cases differ from published completion inventory')
        if child_material is None or p.tree_hash(out/'native')!=child_material:raise p.Rejected('child Native receipt or artifacts changed during outer publication')
        reference_records()
        for row in historical_record['cases']+(child_record['cases'] if child_record else []):
            root=(REFERENCE/'native' if row in historical_record['cases'] else out/'native')/(row['version']+'-'+row['case'])/'native'
            for stage in ('refill-drc','final-drc'):
                binding=f.read_json(root/(stage+'-binding.json'))
                fields.check_local_settings(root,stage,binding)
        if remaining()<=0:raise p.Rejected('whole enclosure budget exhausted')
    def account():
        record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        record['passed']=bool(passed and record['status']=='completed' and remaining()>0)
    record['cost_scope']='Current enclosure samples before shared guarded publication; prior001/002samples+2each plus current whole callbacks/literal readbacks remain under188s wall/fullCPU with2s final allowance within190s. No comparative routing budget or speedup claim.'
    f.publish(out,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(json.dumps({k:record[k] for k in ('passed','source_current','status','wall_seconds','full_cpu_seconds')}));raise SystemExit(0 if record['passed'] else 2)
