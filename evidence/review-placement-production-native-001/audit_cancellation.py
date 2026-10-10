"""Saved cancellation and initial pre-native failure audit; no native execution."""
from pathlib import Path
import hashlib,json,math,subprocess
import audit_fixture as a
from autorouter import pipeline as p, floor_route as f, placement_clearance as pc, sexpr as sx
ROOT,HERE=a.ROOT,a.HERE

def main():
    fixture=a.read(a.RUN/'result.json');source=Path(fixture['source']);source_before=a.inventory(source.parent);records=[]
    script='experiments/placement_production_controls_v1/cancellation.py'
    original_script=subprocess.run(['git','show',a.HEAD+':'+script],cwd=ROOT,capture_output=True,check=True,timeout=5).stdout
    for suffix,sig in [('int','SIGINT'),('term','SIGTERM')]:
        directory=ROOT/('.runs/placement-production-cancellation-'+suffix+'-001');before=a.inventory(directory)
        control=a.read(directory/'control.json');run=directory/'route';result=a.read(run/'result.json');engine=a.read(run/'engine-process.json');prefix=sig+': '
        a.ok(prefix+'actual completed cancellation and immutablesource/core',control['status']=='passed' and control['passed'] is True and control['source_hashes']==source_before and control['tools']==fixture['tools'] and result['tools']==fixture['tools'])
        a.ok(prefix+'exact committed helper',control['script_sha256']==hashlib.sha256(original_script).hexdigest()==a.sha(ROOT/script))
        a.ok(prefix+'all nine declared observations true',len(control['checks'])==9 and all(value is True for value in control['checks'].values()))
        a.ok(prefix+'exact CLI requested newpolicy',control['argv'][1:]==['-m','autorouter','route',str(source),'--output',str(run),'--seconds','60','--adapter','both','--profile','completion-only','--guidance','placement-clearance-v1'] and control['cli_exit_code']==2)
        a.ok(prefix+'actual engine observation bound to CLI child/group',control['observed_owned_engine']=={'pid':engine['pid'],'ppid':control['cli_pid'],'pgid':engine['pid']} and control['signals']==[{'pid':control['cli_pid'],'signal':sig,'elapsed_seconds':control['signals'][0]['elapsed_seconds']}] and control['engine_log_bytes_at_signal']>0)
        a.ok(prefix+'signal occurred after engine observation before controlfinished',0<control['engine_observed_elapsed_seconds']<=control['signals'][0]['elapsed_seconds']<control['wall_seconds']<15)
        a.ok(prefix+'retained process reports requested cancellation andcleanup',engine['status']=='cancelled' and engine['exit_code']==-9 and engine['cancel_signal']==sig and engine['cleanup_complete'] is True and control['remaining_owned_engine_group']==[])
        a.ok(prefix+'canonical receipt rejected andcleanlinessfalse',result['schema']==3 and result['input_policy']=='placement-clearance-v1' and result['accepted'] is False and result['whole_project_drc_clean'] is False and result['status']=='cancelled' and control['route_status']=='cancelled' and control['route_accepted'] is False)
        a.ok(prefix+'bound raw receipt process and CLIlog hashes',control['route_receipt']=={'path':str(run/'result.json'),'sha256':a.sha(run/'result.json')} and control['engine_receipt']=={'path':str(run/'engine-process.json'),'sha256':a.sha(run/'engine-process.json'),'data':engine} and control['cli_log_sha256']==a.sha(directory/'cli.log'))
        a.ok(prefix+'source and task only currentcontrolled output',a.inventory(run/'snapshot')==source_before and a.inventory(source.parent)==source_before and a.sha(run/'candidate'/source.name)==result['task_sha256'])
        a.ok(prefix+'cancelled duringengine before importorfinalDRC', [s['name'] for s in result['steps']]==['source-drc','floor-export','engine'] and not (run/'final-drc.json').exists() and not (run/'imported.kicad_pcb').exists())
        pc.check_freeze(run,result);pc.check_chain(run,result);a.CHECKS.append(prefix+'raw floor placement planning task and committed freeze fully rederived')
        f.process_check(run,result,'floor-export',f.context_argv('export',run/'floor-export-input'/source.name,run/'floor-export-context.json',run/'native.dsn',run/'placement-area-context.json'))
        a.CHECKS.append(prefix+'same-load exporterprocess exact argv bound')
        a.ok(prefix+'actual engine argv matches fixed assignedsettings',engine['argv']==f.engine_argv(run,result['engine_budget']['argv']) and engine['cwd']==str(run) and engine['name']=='engine')
        steps=result['steps'];a.ok(prefix+'full routeCPU sums andceilings',result['budget_seconds']==result['cpu_budget_seconds']==60 and result['wall_seconds']<60 and result['total_cpu_seconds']<60 and math.isclose(result['total_cpu_seconds'],sum(result[k] for k in ('parent_cpu_seconds','child_cpu_seconds','monitor_cpu_seconds','control_child_cpu_seconds')),abs_tol=1e-8) and math.isclose(result['child_cpu_seconds'],sum(s['cpu_seconds'] for s in steps),abs_tol=1e-8))
        try:p.check_result(run/'result.json')
        except p.Rejected as exc:a.ok(prefix+'production checkerrefuses cancelledreceipt',str(exc)=='receipt is not an accepted routing result')
        else:raise AssertionError('cancelled receipt accepted')
        a.ok(prefix+'all saved route receipts remainnegative',all(a.read(path).get('accepted') is not True for path in run.glob('*result*.json')))
        a.ok(prefix+'complete actual artifacts unchanged by audit',before==a.inventory(directory))
        records.append({'signal':sig,'control_sha256':a.sha(directory/'control.json'),'route_receipt_sha256':a.sha(run/'result.json'),'engine_receipt_sha256':a.sha(run/'engine-process.json'),'control_wall_seconds':control['wall_seconds'],'route_wall_seconds':result['wall_seconds'],'route_total_cpu_seconds':result['total_cpu_seconds'],'run_inventory':before,'limitation':'Saved immediate PID/group absence observation only; not a new OS query or persistent monitor. Control wrapper does not record aggregate CPU, so no independent total-wrapper CPU claim.'})
    failed=ROOT/'.runs/placement-production-controls-native-001';before=a.inventory(failed);data=a.read(failed/'summary.json')
    a.ok('first five-control invocation retainedpre-native harnessfailure',data['status']=='failed' and data['controls_passed'] is False and data['native_executed'] is False and data['new_engine_execution'] is False and data['cases']==[] and data['steps']==[] and data['error']=='Rejected: expected original no-route/one-placement-area fixture differs')
    original=sx.read(source);a.ok('failed no-route assumption disproved by actual original eight reference routes',len(p.routes(original))==8)
    a.ok('failed run onlysummary andunchanged',list(before)==['summary.json'] and before==a.inventory(failed))
    a.ok('original fixture source remainsunchanged',source_before==a.inventory(source.parent))
    output={'schema':1,'audit_passed':True,'native_engine_network_executed':False,'check_count':len(a.CHECKS),'checks':a.CHECKS,'cancellation':records,'pre_native_failed_control':{'summary_sha256':a.sha(failed/'summary.json'),'status':data['status'],'error':data['error'],'native_executed':False,'wall_seconds':data['wall_seconds'],'total_cpu_seconds':data['total_cpu_seconds']},'scope':'Two engine-stage cancellation observations passed; first five-control harness failed before native. Future corrected controls not read or qualified.'}
    with (HERE/'cancellation-audit.json').open('x') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps({'audit_passed':True,'check_count':len(a.CHECKS),'output':str(HERE/'cancellation-audit.json')}))
if __name__=='__main__':main()
