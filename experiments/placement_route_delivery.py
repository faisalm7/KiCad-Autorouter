"""Bounded placement-to-route qualification using the existing installed workflow.

Reads a frozen plan and an independently checked placement proposal. This is
software-test selection/acceptance intent, not a GUI or human approval path.
No new routing, validation, warning, snapshot or process implementation lives
here: the shared placement reader and existing six-stage qualifier remain in use.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import time

START=time.monotonic()
def cpu():
    return sum(r.ru_utime+r.ru_stime for r in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
ROOT=Path(__file__).resolve().parents[1]
SELF=Path(__file__).resolve()
ENCLOSURE=ROOT/'.runs/enclose-runtime044-workflow-001.py'
QUALIFIER=ROOT/'scripts/qualify_runtime_workflow.py'


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol',required=True)
    ap.add_argument('--protocol-sha256',required=True)
    ap.add_argument('--execute',action='store_true')
    args=ap.parse_args(argv)
    protocol=Path(args.protocol).resolve();base=protocol.parent
    if not base.is_relative_to(ROOT/'.runs'):
        raise ValueError('Owned project experiment protocol required')
    raw=protocol.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.protocol_sha256:
        raise ValueError('Frozen delivery protocol differs')
    plan=json.loads(raw)
    runtime=Path(plan['runtime'])
    sys.dont_write_bytecode=True;sys.path[:0]=[str(runtime),str(ROOT)]
    from autorouter import config as c,pipeline as p,floor_route as f,gui,preferences as pref,handoff as h
    from autorouter.runner import run
    from experiments.placement_native_evidence import check
    from scripts.backup import require_headroom
    if c.ROOT!=runtime or Path(sys.prefix).resolve()!=runtime/'.venv':
        raise ValueError('Qualified installed interpreter/runtime required')
    protocol=h.real_path(protocol);base=h.real_path(base)
    out=h.real_path(plan['output'],existing=False)
    if out.parent!=runtime/'.runs':
        raise ValueError('Fresh installed experiment output required')

    def witness():
        return check(plan['placement_output'],runtime,plan['placement_protocol'],plan['placement_scope'])

    def fresh():
        if p.sha(protocol)!=args.protocol_sha256 or p.sha(SELF)!=plan['invoker_sha256']:
            raise ValueError('Delivery controller or plan changed')
        if p.sha(ENCLOSURE)!=plan['enclosure_sha256'] or p.sha(QUALIFIER)!=plan['driver_sha256']:
            raise ValueError('Shared qualifier changed')
        if p.sha(runtime/'runtime-distribution.json')!=plan['runtime_manifest_sha256']:
            raise ValueError('Installed runtime changed')
        if p.sha(base/'settings.json')!=plan['settings_sha256'] or pref.resolve(pref.load(base/'settings.json'))!=plan['settings']:
            raise ValueError('Routing settings changed')
        if plan['settings']!=dict(pref.DEFAULTS,scope='partial_completion',seconds=90) or plan['budgets']!=dict(route=90,export=90):
            raise ValueError('Prospective default90/90 bounds differ')
        if plan['method']!='route' or plan['expected_counts']!=[0,0,0,0] or plan['expected_protected_count']!=1:
            raise ValueError('Prospective complete protected-task acceptance differs')
        actual=witness()
        if actual!=plan['placement'] or plan['source']!=actual['candidate'] or plan['source_hashes']!=actual['source_hashes']:
            raise ValueError('Placement proposal, source or evidence changed')
        for name,digest in plan['prior_research_pins'].items():
            if p.sha(h.real_path(ROOT/name))!=digest:
                raise ValueError('Retained prior research evidence changed')
        return actual

    fd=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(fd,'r+') as lane:
        info=os.fstat(lane.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:
            raise ValueError('Unexpected shared execution lane identity')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fresh()
        space=require_headroom(runtime,512*1024**2,'one installed placement-to-route delivery')
        if out.exists() or any((base/name).exists() for name in ('enclosure','execution.json','handoff.json','outer.log','outer-process.json')):
            raise ValueError('Use a fresh output; previous work cannot be overwritten')
        if not args.execute:
            print(json.dumps(dict(prepared=True,placement_current=True,Native_executed=False,space_plan=space)))
            return 0
        process=run([str(ROOT/'.venv/bin/python'),'-B',str(ENCLOSURE),'--protocol',str(protocol)],
            cwd=base,env=gui.child_environment(),log=base/'outer.log',timeout=max(.001,238-(time.monotonic()-START)),
            max_log_bytes=512*1024,max_group_rss_bytes=4*1024**3,max_workdir_bytes=512*1024**2)
        p.save_json(base/'outer-process.json',process)
        execution=None;error=None
        try:
            fresh()
            execution=f.read_json(base/'execution.json')
        except (Exception,KeyboardInterrupt) as exc:
            error=type(exc).__name__+': '+str(exc)
        wall,cost=time.monotonic()-START,cpu()-CPU0
        passed=bool(error is None and execution and execution['controls_passed'] is True
            and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True
            and process['log_truncated'] is False and max(wall,cost)+1<=240)
        record=dict(schema=1,demonstration_delivered=passed,accepted=False,human_approval=False,actual_GUI=False,
            comparison_claim=False,source=plan['source'],source_hashes=plan['source_hashes'],plan_sha256=args.protocol_sha256,
            error=error,execution_sha256=p.sha(base/'execution.json') if execution else None,
            placement=plan['placement'],routing_workflow_wall_seconds=wall,routing_workflow_cpu_seconds=cost,
            publication_allowance_seconds=1,routing_total_limit_seconds=240,routing_controller_exit_not_measured=True,
            software_test_selection_intent=True,space_plan=space,prior_research_pins=plan['prior_research_pins'],
            Native_counts=execution.get('Native_counts') if execution else None,
            scope='One exposed owned multipad placement proposal, reviewed before installed default routing and fresh Native export; no human, GUI, electrical or comparative claim.')
        p.save_json(base/'handoff.json',record)
        print(json.dumps({k:record[k] for k in ('demonstration_delivered','error','Native_counts','routing_workflow_wall_seconds','routing_workflow_cpu_seconds')}))
        return 0 if passed else 2


if __name__=='__main__':
    raise SystemExit(main())
