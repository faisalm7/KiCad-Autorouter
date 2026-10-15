"""Complete existing-runner enclosure for the single owned angle control.
SPDX-License-Identifier: GPL-3.0-or-later
Includes preparation, actual descendant CPU and publication/checking tail.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,local_settings as ls
from autorouter.runner import run
from experiments.hfe_original_native_v1 import driver as shared
from experiments.free_angle_baseline_v1 import controls as c
OUT=ROOT/'.runs/free-angle-native-enclosure-001';CAP=200.


def execute(head,pin):
    plan=f.read_json(c.PROTOCOL);c.context(plan,pin)
    if plan['git_head']!=head or c.OUT.exists() or c.OUT.is_symlink():raise p.Rejected('frozen head and fresh Native destination required')
    prior=plan['preparation_costs'];prewall=prior['wall_seconds']+2;precpu=prior['full_cpu_seconds']+2
    if prior.get('publication_allowance_seconds')!=2 or min(prewall,precpu)<2:raise p.Rejected('preparation charge differs')
    OUT.mkdir();owner={};h.capture_destination(owner,OUT);selfpin=p.sha(Path(__file__))
    def remaining():return min(CAP-2-prewall-(time.monotonic()-START),CAP-2-precpu-(cpu()-CPU0))
    argv=[*f.SANDBOX,str(ROOT/'.venv/bin/python'),'-B',str(Path(c.__file__)),'--run-native','--source-head',head,'--protocol-sha256',pin]
    process=run(argv,cwd=OUT,log=OUT/'command.log',timeout=max(.001,remaining()),max_log_bytes=256*1024,max_workdir_bytes=128*1024**2,max_group_rss_bytes=4*1024**3)
    path=c.OUT/'result.json';child=f.read_json(path) if path.is_file() else None
    childpin=p.sha(path) if child is not None else None
    material=p.tree_hash(c.OUT) if c.OUT.is_dir() else None;logpin=p.sha(OUT/'command.log')
    bound=bool(child and child.get('completed_evidence')==shared.material(c.OUT))
    passed=bool(bound and child.get('passed') is True and child.get('status')=='completed' and child.get('accepted') is False
        and process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] is True and process['log_truncated'] is False)
    cancelled=process['status']=='cancelled' or child is not None and child.get('status')=='cancelled'
    record=dict(schema=1,kind='actual-complete-owned-stock-free-angle-native-v1',accepted=False,passed=passed,status='completed' if passed else 'cancelled' if cancelled else 'failed',
        git_head=head,protocol_sha256=pin,controller_sha256=selfpin,process=process,child_receipt_sha256=childpin,
        child_material_sha256=material,child_completed_evidence_bound=bound,log_sha256=logpin,preparation_costs=prior,whole_wall_full_cpu_cap_seconds=CAP,
        scope='One exposed owned oblique control; actual complete process including preparation and all loader/Native/publication tails reached. Diagnostic qualification only, no quality/family/GUI/install/human/release claim. Child timing is partial; use these complete outer charges.')
    def stable():
        h.owned_destination(owner);c.context(plan,pin)
        if p.sha(Path(__file__))!=selfpin or p.sha(OUT/'command.log')!=logpin or (c.OUT.is_dir() and p.tree_hash(c.OUT)!=material):raise p.Rejected('complete enclosure material changed')
        if child is not None and p.sha(path)!=childpin:raise p.Rejected('child receipt changed')
        if child is not None and child.get('positive'):
            ls.check_normal_policy(c.OUT/'route',f.read_json(c.OUT/'route/result.json'),max_bytes=128*1024**2,max_files=2048)
        if child is not None and child.get('physical_short'):
            bad=child['physical_short']
            ls.check_normal_policy(c.OUT/'invalid-job',dict(steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
    def account():
        c.account_delivery(record,prewall+time.monotonic()-START,precpu+cpu()-CPU0,remaining())
    f.publish(OUT,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    result=f.read_json(OUT/'result.json');print(f.canonical({k:result.get(k) for k in ['passed','status','wall_seconds','full_cpu_seconds','child_completed_evidence_bound']}))
    return 0 if result.get('passed') is True and result.get('status')=='completed' else 130 if result.get('status')=='cancelled' else 2


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True);parser.add_argument('--protocol-sha256',required=True);args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in [signal.SIGINT,signal.SIGTERM]:signal.signal(sig,cancel)
    raise SystemExit(execute(args.source_head,args.protocol_sha256))
