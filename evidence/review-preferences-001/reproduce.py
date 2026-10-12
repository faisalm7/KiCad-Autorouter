"""Tiny real-file receipt controls; all worker/native stages are explicitly mocked."""
from pathlib import Path
import sys,json,copy,hashlib,shutil,time
from unittest.mock import patch
from contextlib import ExitStack
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,preferences as pref,config as c
HERE=Path(__file__).resolve().parent
OUT=HERE/sys.argv[1];OUT.mkdir(exist_ok=False)
original_sha=p.sha

def alias_case(label,extra):
    out=OUT/label;out.mkdir()
    preset=out/'preset.json';preset.write_text(json.dumps(dict(pref.DEFAULTS)))
    captured=pref.load(preset);request={'captured':captured,'snapshot':pref.snapshot(captured),'effective':pref.resolve(captured)}
    record={};p.capture_preferences(record,out,request)
    record.update(scope='whole_board_unlocked_routing',budget_seconds=120,cpu_budget_seconds=120,adapter='none',engine_profile='standard',scoring_variant=None)
    settings=p.engine_profile_settings('standard',100);settings.update(outer_task_wall_budget_seconds=120,outer_task_cpu_budget_seconds=120)
    argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),'-Xms128m','-Xmx2g','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-jar',str(c.JAR),'--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','-da','--user_data_path='+str(out/'engine-config'),'--logging.file.enabled=false',*settings['argv'],'-de',str(out/'task.dsn'),'-do',str(out/'routes.ses'),*extra]
    process={'name':'engine','status':'success','exit_code':0,'cleanup_complete':True,'argv':argv,'cwd':str(out)}
    record.update(engine_budget=settings,steps=[process]);(out/'engine-process.json').write_text(json.dumps(process));(out/'receipt.json').write_text(json.dumps(record))
    try:p.check_preferences_record(out,record);outcome={'accepted_by_preference_binding':True}
    except Exception as exc:outcome={'accepted_by_preference_binding':False,'error':type(exc).__name__+': '+str(exc)}
    return {'case':label,'extra':extra,**outcome}

class FakeJob:
    def __init__(self,out,seconds):
        self.out=Path(out);self.out.mkdir();self.steps=[];self.started=time.monotonic();self.deadline=self.started+seconds;self.cpu_started=time.process_time()
    def drc(self,*args):return {'warnings':0,'findings':[]}
    def step(self,name,argv,*args,**kwargs):
        row={'name':name,'argv':[str(v) for v in argv],'cwd':str(self.out),'status':'success','exit_code':0,'cleanup_complete':True,'cpu_seconds':0.0,'monitor_cpu_seconds':0.0,'wall_seconds':0.0,'max_rss_bytes':0}
        self.steps.append(row);(self.out/(name+'-process.json')).write_text(json.dumps(row));(self.out/'routes.ses').write_text('(session fake)');return row
    def native(self,name,mode,*args):
        if mode=='export':Path(args[1]).write_text('(pcb fake)')
        elif mode=='import':shutil.copyfile(args[0],args[1])
        elif mode=='metrics':Path(args[1]).write_text(json.dumps({'version':'10.0.0'}))
        else:raise AssertionError(mode)

def native_case(label,mutation):
    out=OUT/label;out.mkdir();source=out/'project';shutil.copytree(ROOT/'fixtures/smoke',source)
    preset=out/'preset.json';preset.write_text(json.dumps(dict(pref.DEFAULTS)))
    run=out/'run';save=p.save_json
    def fake_validation(job,original,candidate,before,protected):
        (job.out/'final-drc.json').write_text('{}')
        return original_sha(candidate),{'warnings':0,'findings':[]}
    def saved(path,record):
        save(path,record)
        if Path(path)==run/'result.json' and record.get('accepted') and mutation=='interrupt_after_positive_write':raise KeyboardInterrupt('owned pure control')
    def checker(path):
        if mutation=='canonical_after_checker':
            value=json.loads(Path(path).read_text());value['engine_profile']='tuned';Path(path).write_text(json.dumps(value))
        return {'current':True}
    result=None;error=None
    with ExitStack() as stack:
        for name,value in [('Job',FakeJob),('sha',lambda path:c.JAR_SHA256 if Path(path)==c.JAR else original_sha(path)),('check_storage',lambda:None),('tool_manifest',lambda:{}),('validate_candidate',fake_validation),('native_rejection_reasons',lambda native:[]),('native_accepted',lambda native:True),('check_result',checker),('save_json',saved)]:stack.enter_context(patch.object(p,name,value))
        try:result=p.route(source/'smoke.kicad_pcb',run,settings_path=preset)
        except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    canonical=json.loads((run/'result.json').read_text()) if (run/'result.json').is_file() else None
    return {'case':label,'mutation':mutation,'error':error,'returned_accepted':result.get('accepted') if result else None,'canonical_accepted':canonical.get('accepted') if canonical else None,'canonical_profile':canonical.get('engine_profile') if canonical else None,'returned_profile':result.get('engine_profile') if result else None}

rows=[alias_case('binding_unchanged',[]),alias_case('optimizer_alias',['--optimizer.enabled=false']),alias_case('short_pass_alias',['-mp','999']),alias_case('scoring_alias',['--optimizer-scoring-version=v1'])]
rows += [native_case('native_unchanged',None),native_case('native_interrupt','interrupt_after_positive_write'),native_case('native_canonical_mutation','canonical_after_checker')]
report={'schema':1,'scope':'Real tiny files; fake worker/native stages/checker, no routing/native qualification. Alias binder is real.','source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('autorouter/pipeline.py','autorouter/floor_route.py','autorouter/preferences.py')},'rows':rows}
(OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
