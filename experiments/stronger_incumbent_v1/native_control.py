"""Fresh owned C-incumbent integration control; existing Native/PRL helpers.

No getter/corner repeat, benchmark, new support, or default-promotion claim.
"""
import time, resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, hashlib, json, sys
ROOT = next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
from autorouter import pipeline as p, floor_route as f, strategy as s, sexpr as sx, local_settings as ls, placement_clearance as io, handoff as h
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.fanout_baseline_v1 import clearance_fixture as fixture, clearance_control as old
from experiments.native_paired_v1.observations import require
PREP = ROOT/'.runs/stronger-incumbent-native-preparation-001'
PROTOCOL = PREP/'protocol.json'
OUT = ROOT/'.runs/stronger-incumbent-native-001'
INNER, WHOLE = 120, 180

def context(plan, pin=None):
    shared.clean(plan['git_head'])
    require(plan['kind']=='fresh-stronger-pruning-incumbent-v1' and plan['policy']==s.STRONG_INCUMBENT_POLICY
        and plan['limits']=={'inner_seconds':INNER, 'whole_wall_full_cpu_seconds':WHOLE}, 'control policy differs')
    require(p.tool_manifest()==plan['tools'] and p.tree_hash(PREP/'source')==plan['source_sha256']
        and all(p.sha(ROOT/n)==v for n,v in plan['code_sha256'].items()), 'control source/tools differ')
    require({n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}==plan['source_sha256'], 'owned recipe differs')
    if pin is not None:require(p.sha(PROTOCOL)==pin and f.read_json(PROTOCOL)==plan, 'frozen protocol differs')

def prepare(head):
    shared.clean(head); tools=p.tool_manifest(); require(tools['git_head']==head, 'exact source checkpoint required')
    PREP.mkdir(); copy_bytes(fixture.files(),PREP/'source')
    source=PREP/'source'/(fixture.STEM+'.kicad_pcb'); original=p.preflight(source)
    protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original)
    require(len(protected)==len(p.routes(original))==1 and p.netclass_policy(source) is None
        and p.minimum_width_guard(source,'both') is None, 'owned non-strict KEEP source differs')
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),
        'experiments/fanout_baseline_v1/clearance_fixture.py','experiments/fanout_baseline_v1/fixture.py',
        'experiments/fanout_baseline_v1/clearance_control.py','experiments/free_angle_baseline_v1/fixture.py',
        'experiments/placement_handoff_native_v1/driver.py','experiments/hfe_original_native_v1/driver.py',
        'experiments/native_paired_v1/observations.py'}
    names.update(str(Path(module.__file__).relative_to(ROOT)) for module in (fixture.base,fixture.base.base,fixture.base.base.base))
    plan=dict(schema=1,kind='fresh-stronger-pruning-incumbent-v1',policy=s.STRONG_INCUMBENT_POLICY,
        git_head=head,tools=tools,source_sha256=p.tree_hash(source.parent),protected_ast=protected,
        limits={'inner_seconds':INNER,'whole_wall_full_cpu_seconds':WHOLE},
        code_sha256={n:p.sha(ROOT/n) for n in sorted(names)})
    context(plan); p.save_json(PROTOCOL,plan)
    print(f.canonical(dict(prepared=True,protocol_sha256=p.sha(PROTOCOL))))

def check_positive(plan):
    path=OUT/'route/result.json'; record=f.read_json(path); pin=p.sha(path); material=shared.material(path.parent)
    require(record.get('accepted') is True and record.get('status')=='routing_accepted'
        and record.get('source')==str(OUT/'source'/(fixture.STEM+'.kicad_pcb'))
        and record.get('tools')==plan['tools'] and record.get('source_hashes')==plan['source_sha256']
        and record.get('budget_seconds')==record.get('cpu_budget_seconds')==INNER
        and record.get('proposal_policy')=='chains' and record.get('incumbent_policy')==plan['policy'], 'fresh C outcome differs')
    checked=p.check_result(path); require(checked['current'] is True, 'C shared reader refused')
    candidate=Path(record['candidate']); original=sx.read(OUT/'source'/candidate.name)
    require(p.immutable(sx.read(candidate))==p.immutable(original)
        and all(r in p.routes(sx.read(candidate)) for r in plan['protected_ast']), 'C original geometry/KEEP differs')
    native=record['native']; fields=native.get('field_parity',{}).get('qualification',{})
    require(p.native_accepted(native) and native['warnings']==6 and native['exclusions']==0
        and record.get('schematic_parity')=='checked by final native DRC'
        and fields.get('component_count')==6 and fields.get('compared_field_count')==18, 'C final fullSCH evidence differs')
    require(p.sha(candidate)==record['candidate_sha256'] and p.sha(path.parent/'final-drc.json')==record['native_report_sha256'], 'C final hash differs')
    require(p.sha(path)==pin and shared.material(path.parent)==material, 'C evidence changed during readback')
    ls.check_normal_policy(path.parent,record,max_bytes=128*1024**2,max_files=2048)
    return record

def check_negative(plan, row):
    folder=OUT/'invalid-job'; board=Path(row['candidate'])
    data=dict(schema=1,steps=row['steps'],source_hashes=row['before'],tools=plan['tools'])
    checked=f.check_drc_stage(folder,data,'invalid-final',board,folder/'invalid-final-input'/board.name,False,row['before'],schematic_parity=True)
    require(checked==row['native'] and not p.native_accepted(checked) and checked['blocking']>0
        and p.sha(board)==row['candidate_sha256'] and p.sha(folder/'invalid-final.json')==row['report_sha256'], 'actual short proof differs')
    ls.check_normal_policy(folder,data,max_bytes=128*1024**2,max_files=2048)

def execute(plan,pin):
    context(plan,pin); OUT.mkdir(); copy_bytes(io.inventory(PREP/'source',contents=True),OUT/'source')
    owner={};h.capture_destination(owner,OUT)
    report=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],protocol_sha256=pin,
        scope='Fresh owned C integration and same-original short only; no benchmark/support/GUI/physical claim.')
    def remaining():return WHOLE-max(time.monotonic()-START,cpu()-CPU0)-2
    def stable():
        h.owned_destination(owner);context(plan,pin)
        require(p.tree_hash(OUT/'source')==plan['source_sha256'],'control source changed')
        if report.get('passed'):
            require(shared.material(OUT)==report['completed_evidence'],'completed control material changed')
            positive=f.read_json(OUT/'route/result.json')
            require(p.sha(OUT/'route/result.json')==report['positive']['receipt_sha256'],'positive receipt changed')
            ls.check_normal_policy(OUT/'route',positive,max_bytes=128*1024**2,max_files=2048)
            bad=report['physical_short']
            ls.check_normal_policy(OUT/'invalid-job',dict(schema=1,steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
    def account():
        report.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0)
        if remaining()<=0:report.update(status='budget_exceeded',passed=False)
        if report['status']!='completed':report['passed']=False
    try:
        with p.validation_readback_session():
            routed=s.prune(OUT/'source'/(fixture.STEM+'.kicad_pcb'),OUT/'route',INNER,
                proposal_policy='chains',incumbent_scoring='via_default',_incumbent_policy=plan['policy'])
            require(routed['accepted'] is True,'fresh C candidate rejected: '+str(routed.get('reason',routed['status'])))
            positive=check_positive(plan)
            report['positive']={k:positive[k] for k in ('candidate_sha256','native_report_sha256','native','metrics','improvements')}
            report['positive']['receipt_sha256']=p.sha(OUT/'route/result.json')
            report['physical_short']=old.physical_short(plan,positive,remaining,output=OUT)
            check_negative(plan,report['physical_short']); check_positive(plan)
        report.update(status='completed',passed=True)
    except (Exception,KeyboardInterrupt) as exc:
        report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',passed=False,error=type(exc).__name__+': '+str(exc))
    report['completed_evidence']=shared.material(OUT)
    f.publish(OUT,report,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(f.canonical({k:report.get(k) for k in ('passed','status','error','wall_seconds','full_cpu_seconds')}))
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['prepare','run'],required=True);ap.add_argument('--source-head',required=True);ap.add_argument('--protocol-sha256')
    args=ap.parse_args()
    if args.mode=='prepare':prepare(args.source_head);return
    plan=f.read_json(PROTOCOL);require(plan['git_head']==args.source_head,'wrong checkpoint');context(plan,args.protocol_sha256)
    raise SystemExit(0 if execute(plan,args.protocol_sha256)['passed'] else 2)
if __name__=='__main__':main()
