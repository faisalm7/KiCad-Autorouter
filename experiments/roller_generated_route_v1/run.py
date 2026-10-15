"""One bounded sequential launch; a fresh diagnostic, never product admission."""
import time,resource
START=time.monotonic()
_usage=resource.getrusage(resource.RUSAGE_CHILDREN)
CPU=time.process_time()+_usage.ru_utime+_usage.ru_stime
from pathlib import Path
import json,signal,sys,math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h
from autorouter.runner import run
HERE=Path(__file__).resolve().parent

def audit_material(spec,spec_raw,output,actor_raw,tools,*,tool_reader=None):
    """Final callback first, then bind all original and completed material."""
    from experiments.roller_generated_route_v1 import driver as d
    current=(p.tool_manifest if tool_reader is None else tool_reader)()
    d.need(current==tools,'final tool/code/HEAD changed')
    actor=f.read_json(output/'result.json')
    d.need(type(actor)is dict and type(actor.get('schema'))is int and actor['schema']==1 and actor.get('kind')=='roller_generated_route_diagnostic'
        and actor.get('status')=='completed' and actor.get('qualified')is True
        and actor.get('accepted')is False and actor.get('production_support_qualified')is False
        and actor.get('tools')==tools and actor.get('protocol_sha256')==d.digest(spec_raw),
        'completed diagnostic identity or proof differs')
    for key in ('charged_wall_seconds','charged_full_cpu_seconds'):
        value=actor.get(key)
        d.need(type(value)in (int,float) and math.isfinite(value) and 0<=value<=120,'invalid actor resource accounting')
    expected={**tools['implementation_sha256'],**spec['code_sha256'],
        str((HERE/'protocol.json').relative_to(ROOT)):d.digest(spec_raw),
        'toolchain.lock.json':p.sha(ROOT/'toolchain.lock.json')}
    d.need(actor.get('runtime_source_sha256')==expected,'committed runtime closure differs')
    for name,pin in expected.items():d.need(p.sha(ROOT/name)==pin,'final source changed: '+name)
    d.need(d.inventory(d.SOURCE)==spec['source_inventory'],'original creator project changed')
    for name,pins in spec['retained_inventories'].items():
        d.need(d.inventory(ROOT/name)==pins,'retained evidence changed: '+name)
    d.need(d.witness(output)==actor.get('completed_material'),'completed Native/candidate material changed')
    d.need(d.io.read_bytes(HERE/'protocol.json')==spec_raw
        and d.io.read_bytes(output/'result.json')==actor_raw,'protocol or actor receipt changed after final callback')
    return actor

def main():
    if sys.argv[1:]!=['--run-native']:
        raise SystemExit('Only --run-native after review, checkpoint and backup is supported')
    from experiments.roller_generated_route_v1 import driver as d
    spec_raw=d.io.read_bytes(HERE/'protocol.json');spec=f.read_json(HERE/'protocol.json')
    if spec.get('status')!='prospectively_frozen' or spec.get('outer_driver_sha256')!=p.sha(__file__):
        raise p.Rejected('prospective outer-driver pin differs')
    output=ROOT/spec['output'];out=ROOT/spec['outer_output'];out.mkdir(mode=0o700)
    before=p.tool_manifest()
    argv=[str(ROOT/'.venv/bin/python'),'-B',str(HERE/'driver.py'),'--run-native','--output',str(output)]
    timeout=115-(time.monotonic()-START)
    d.need(timeout>0,'outer startup exhausted its budget')
    result=run(argv,cwd=out,log=out/'command.log',timeout=timeout,
        max_log_bytes=128*1024,max_workdir_bytes=2*1024**2,max_group_rss_bytes=4*1024**3)
    actor_raw=d.io.read_bytes(output/'result.json') if (output/'result.json').is_file() else None
    actor=None;final_error=None
    try:
        d.need(actor_raw is not None,'actor receipt missing')
        actor=audit_material(spec,spec_raw,output,actor_raw,before)
    except (Exception,KeyboardInterrupt) as exc:
        actor=None
        final_error=type(exc).__name__+': '+str(exc)
    wall=time.monotonic()-START;cpu=h.cpu_seconds()-CPU
    charged_wall=max(wall+2,actor.get('charged_wall_seconds',0) if actor else 0)
    charged_cpu=max(cpu+2,actor.get('charged_full_cpu_seconds',0) if actor else 0)
    receipt=dict(schema=1,kind='roller-generated-route-native-execution',process=result,
        actor_sha256=d.digest(actor_raw) if actor_raw is not None else None,protocol_sha256=p.sha(HERE/'protocol.json'),
        controller_sha256=p.sha(__file__),tools=before,final_material_error=final_error,
        final_material_verified=final_error is None,
        wall_seconds=wall,full_cpu_seconds=cpu,publication_bootstrap_allowance_seconds=2,
        charged_wall_seconds=charged_wall,charged_full_cpu_seconds=charged_cpu,
        independent_reader_reserve_seconds=3,
        qualified=bool(actor and actor.get('qualified') is True and actor.get('accepted') is False
            and actor.get('production_support_qualified') is False
            and result['status']=='success' and result['exit_code']==0 and result['cleanup_complete'] is True
            and result['log_truncated'] is False and final_error is None
            and charged_wall+3<=120 and charged_cpu+3<=120),
        scope='One fresh generated-route diagnostic; all raw failures and engineering costs retained separately. No B0/B1/B2/C comparison, production support, family independence or physical approval.')
    p.save_json(out/'execution.json',receipt)
    print(json.dumps({k:receipt[k] for k in ('qualified','charged_wall_seconds','charged_full_cpu_seconds','final_material_error')}))
    return 0 if receipt['qualified'] else 2

if __name__=='__main__':
    def stop(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,stop)
    raise SystemExit(main())
