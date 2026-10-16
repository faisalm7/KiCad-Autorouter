"""Prospective fresh owned strict global-width C control; no quality claim.

Reuses the existing stronger-incumbent control, shared Native/PRL lifecycle
and BoundJob. No prior solver, getter, corner or physical-short rerun.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
from decimal import Decimal
from urllib.parse import urlparse,unquote
import argparse,copy,hashlib,inspect,json,signal,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,strategy as s,sexpr as sx,local_settings as ls,placement_clearance as io,handoff as h,board_floor as g,adapter as dsn
from experiments.hfe_original_native_v1 import driver as shared
from experiments.placement_handoff_native_v1.driver import copy_bytes
from experiments.native_paired_v1.observations import require
from experiments.fanout_baseline_v1.continuation import require_width300
from experiments.stronger_incumbent_v1 import global_width_fixture as fixture
from scripts.probe_engine_profiles import expected_setting
PREP=ROOT/'.runs/global-min-width-native-preparation-001';PROTOCOL=PREP/'protocol.json'
OUT=ROOT/'.runs/global-min-width-native-001'
COMMAND=ROOT/'.runs/run-global-min-width-native-command-001.py'
POLICY='free-angle-clearance20-global-width-v2'
WIDTH_POLICY='original-global-minimum-width-v1'
INNER,WHOLE,READ_RESERVE=120,180,30
LIMITS=dict(inner_seconds=INNER,whole_wall_full_cpu_seconds=WHOLE,reader_reserved_seconds=READ_RESERVE)
STRICT=('--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0')

def context(plan,pin=None):
    shared.clean(plan['git_head'])
    require(plan['kind']=='fresh-owned-global-minimum-width-v1' and plan['policy']==POLICY
        and getattr(s,'STRONG_WIDTH_INCUMBENT_POLICY',None)==POLICY and plan['global_width_policy']==WIDTH_POLICY
        and plan['limits']==LIMITS and plan['tools']['kicad']=='10.0.0','control policy differs')
    require(p.tool_manifest()==plan['tools'] and p.tree_hash(PREP/'source')==plan['source_sha256']
        and all(p.sha(ROOT/n)==v for n,v in plan['code_sha256'].items()),'control source/tools differ')
    require({n:hashlib.sha256(raw).hexdigest() for n,raw in fixture.files().items()}==plan['source_sha256'],'owned recipe differs')
    if pin is not None:require(p.sha(PROTOCOL)==pin and f.canonical(f.read_json(PROTOCOL))==f.canonical(plan),'frozen protocol differs')

def check_command_enclosure(expected_head,protocol_pin):
 directory=ROOT/'.runs/global-min-width-command-001/run';path=directory/'execution.json'
 receipt_pin=p.sha(path);envelope=f.read_json(path);literal=f.canonical(envelope);step=envelope['process']
 log_pin=p.sha(directory/'command.log')
 expected=[str(ROOT/'.venv/bin/python'),'-B',str(Path(__file__)),
  '--mode','run','--source-head',expected_head,'--protocol-sha256',protocol_pin]
 require(envelope.get('mode')=='run' and envelope.get('source_head')==expected_head and envelope.get('passed') is True
  and envelope.get('module_sha256')==p.sha(Path(__file__))
  and envelope.get('controller_sha256')==p.sha(COMMAND)
  and envelope.get('log_sha256')==log_pin,'exact exited control envelope/source/log differs')
 require(step.get('argv')==expected and step.get('cwd')==str(directory) and step.get('status')=='success'
  and type(step.get('exit_code'))is int and step['exit_code']==0 and step.get('cleanup_complete') is True
  and step.get('log_truncated') is False and step.get('log')==str(directory/'command.log')
  and type(step.get('log_bytes'))is int and step['log_bytes']==(directory/'command.log').stat().st_size,
  'exact exited control argv/cwd/cleanup/log identity differs')
 require(p.sha(path)==receipt_pin and f.canonical(f.read_json(path))==literal and p.sha(directory/'command.log')==log_pin,
  'control envelope changed during adoption')
 return receipt_pin,literal,log_pin

def prepare(head):
    shared.clean(head);tools=p.tool_manifest();require(tools['git_head']==head,'exact source checkpoint required')
    require(getattr(s,'STRONG_WIDTH_INCUMBENT_POLICY',None)==POLICY
        and '_engine_global_width_policy' in inspect.signature(p.route).parameters,'prospective private policy not integrated')
    PREP.mkdir();copy_bytes(fixture.files(),PREP/'source')
    source=PREP/'source'/(fixture.STEM+'.kicad_pcb');original=p.preflight(source)
    protected=p.protected_for_record({'scope':'whole_board_unlocked_routing'},original);width=p.minimum_width_guard(source,'both')
    require(len(protected)==len(p.routes(original))==1 and p.netclass_policy(source) is None
        and width==dict(policy='original-positive-minimum-no-automatic-neckdown-v1',min_track_width_mm=.2,
            original_project_sha256=p.sha(source.with_suffix('.kicad_pro'))),'owned strict KEEP source differs')
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),str(Path(fixture.__file__).relative_to(ROOT)),
        str(COMMAND.relative_to(ROOT)),'.runs/read-global-min-width-native-001.py',
        '.runs/run-global-min-width-native-readback-001.py','experiments/stronger_incumbent_v1/native_control.py',
        'experiments/fanout_baseline_v1/continuation.py','experiments/placement_handoff_native_v1/driver.py',
        'experiments/hfe_original_native_v1/driver.py','experiments/native_paired_v1/observations.py',
        'scripts/probe_engine_profiles.py','scripts/EngineProfileProbe.java'}
    names.update(str(Path(module.__file__).relative_to(ROOT)) for module in (fixture.base,fixture.base.base,fixture.base.base.base,fixture.base.base.base.base))
    plan=dict(schema=1,kind='fresh-owned-global-minimum-width-v1',policy=POLICY,global_width_policy=WIDTH_POLICY,
        git_head=head,tools=tools,source_sha256=p.tree_hash(source.parent),protected_ast=protected,minimum_width_guard=width,
        limits=LIMITS,code_sha256={n:p.sha(ROOT/n) for n in sorted(names)})
    context(plan);plan['preparation_costs']=dict(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
    p.save_json(PROTOCOL,plan);print(f.canonical(dict(prepared=True,protocol_sha256=p.sha(PROTOCOL))))

def check_positive(plan):
    path=OUT/'route/result.json';record=f.read_json(path);pin=p.sha(path);literal=f.canonical(record);material=shared.material(path.parent)
    source=OUT/'source'/(fixture.STEM+'.kicad_pcb');width=p.minimum_width_guard(source,'both')
    require(record.get('accepted') is True and record.get('status')=='routing_accepted'
        and record.get('source')==str(source) and record.get('tools')==plan['tools']
        and record.get('source_hashes')==plan['source_sha256'] and record.get('engine_profile')=='tuned'
        and record.get('budget_seconds')==record.get('cpu_budget_seconds')==INNER
        and record.get('proposal_policy')=='chains' and record.get('incumbent_policy')==POLICY,'fresh strict C outcome differs')
    checked=p.check_result(path);require(checked['current'] is True,'C shared reader refused')
    incdir=path.parent/'incumbent';inc=f.read_json(incdir/'result.json');budget=inc['engine_budget'];engine=f.read_json(incdir/'engine-process.json')
    require(s.check_incumbent_policy(path.parent,record,inc)==POLICY and inc.get('engine_profile')=='tuned-free-angle'
        and inc.get('scoring_variant')=='via_default' and inc.get('engine_global_width_policy')==WIDTH_POLICY
        and budget.get('global_width_policy')==WIDTH_POLICY and budget.get('strict_class_targets') is True
        and inc.get('minimum_width_guard')==width==plan['minimum_width_guard']
        and inc.get('engine_fanout_override') is False and inc.get('engine_optimizer_override') is False
        and inc.get('engine_planning_clearance_margin_nm')==20000,'fresh child strict original-width configuration differs')
    require(all(budget['argv'].count(flag)==engine['argv'].count(flag)==1 for flag in STRICT)
        and budget['argv'].count('--router.optimizer.enabled=false')==engine['argv'].count('--router.optimizer.enabled=false')==1,
        'strict three flags/optimizer flag missing or duplicated')
    require(5<=inc['budget_seconds']<=INNER-25 and inc['cpu_budget_seconds']==inc['budget_seconds']
        and record.get('finalization_reserve_seconds')==record.get('finalization_cpu_reserve_seconds')==25
        and [dict(step,phase='incumbent') for step in inc['steps']]==[step for step in record['steps'] if step.get('phase')=='incumbent'],
        'fresh child assignment or charged journal differs')
    p.check_engine_profile_record(inc,incdir)
    # Authored Default is.30. Native export, corrected task and margin input
    # must retain its300um widths; the new policy never rewrites a width.
    for name in ('native.dsn','task.dsn','engine-free-angle.dsn'):
        require_width300(dsn._parse_dsn(io.read_bytes(incdir/name).decode()))
    candidate=Path(record['candidate']);original=sx.read(source);current=sx.read(candidate)
    require(p.immutable(current)==p.immutable(original) and all(r in p.routes(current) for r in plan['protected_ast']),
        'C original geometry/KEEP differs')
    native=record['native'];fields=native.get('field_parity',{}).get('qualification',{})
    require(p.native_accepted(native) and native['warnings']==6 and native['exclusions']==0
        and record.get('schematic_parity')=='checked by final native DRC'
        and fields.get('component_count')==6 and fields.get('compared_field_count')==18
        and inc['source_drc']['opens']==1 and inc['source_drc']['blocking']==0,'C final/source fullSCH evidence differs')
    require(p.sha(candidate)==record['candidate_sha256'] and p.sha(path.parent/'final-drc.json')==record['native_report_sha256'],
        'C final hash differs')
    require(p.sha(path)==pin and f.canonical(f.read_json(path))==literal and shared.material(path.parent)==material,'C evidence changed')
    ls.check_normal_policy(path.parent,record,max_bytes=128*1024**2,max_files=2048)
    return record

def getter_request():
    inc=f.read_json(OUT/'route/incumbent/result.json')
    return dict(timespans=[],profiles=[dict(name='fresh-strict-global-width',argv=inc['engine_budget']['argv'])])

def getter_argv(folder):
    return [str(p.c.JAVA),'-Xms32m','-Xmx256m','-XX:ActiveProcessorCount=1','-Djava.awt.headless=true',
        '-Duser.home='+str(folder/'java-home'),'-Djava.io.tmpdir='+str(folder/'java-tmp'),'--class-path',str(p.c.JAR),
        str(folder/'source/EngineProfileProbe.java'),str(folder/'request.json'),str(folder/'actual-settings.json')]

def observe_settings(plan,job):
    for name in ('java-home','java-tmp'):(job.out/name).mkdir()
    copy_bytes({name:io.read_bytes(ROOT/'scripts'/name,1024**2) for name in ('EngineProfileProbe.java','probe_engine_profiles.py')},job.out/'source')
    p.save_json(job.out/'request.json',getter_request());step=job.step('strict-settings',getter_argv(job.out))
    row=dict(steps=[step],request_sha256=p.sha(job.out/'request.json'),actual_sha256=p.sha(job.out/'actual-settings.json'),
        observer_sha256=p.sha(job.out/'source/EngineProfileProbe.java'),jar_sha256=p.sha(p.c.JAR),java_sha256=p.sha(p.c.JAVA))
    check_settings(plan,row);return row

def check_settings(plan,row):
    folder=OUT/'strict-settings-job';inc=f.read_json(OUT/'route/incumbent/result.json');budget=inc['engine_budget'];request=getter_request()
    require(len(row['steps'])==1 and f.read_json(folder/'request.json')==request
        and row['request_sha256']==p.sha(folder/'request.json') and row['actual_sha256']==p.sha(folder/'actual-settings.json')
        and row['observer_sha256']==p.sha(folder/'source/EngineProfileProbe.java')==p.sha(ROOT/'scripts/EngineProfileProbe.java')
        and row['jar_sha256']==p.sha(p.c.JAR)==plan['tools']['files'][str(p.c.JAR)]
        and row['java_sha256']==p.sha(p.c.JAVA)==plan['tools']['files'][str(p.c.JAVA)],'one pinned actual settings request/source differs')
    f.process_check(folder,dict(steps=row['steps']),'strict-settings',[*f.SANDBOX,*getter_argv(folder)])
    actual=f.read_json(folder/'actual-settings.json');profiles=actual.get('profiles');jar=urlparse(actual.get('jar_code_source',''))
    require(actual.get('timespans_to_seconds')=={} and type(profiles) is list and len(profiles)==1
        and jar.scheme=='file' and jar.netloc=='' and Path(unquote(jar.path)).resolve()==p.c.JAR.resolve(),
        'one actual pinned-JAR settings profile required')
    settings=profiles[0];flags=budget['argv'];parsed=dict(flag[2:].split('=',1) for flag in flags)
    expected_parsed=dict(parsed)
    # The pinned CLI parser stores the fraction as its internal percent string,
    # exactly as the existing effective-setting probe already verifies.
    key='router.optimizer.improvement_threshold'
    if key in expected_parsed:expected_parsed[key]=str(expected_setting(key,parsed[key]))
    require(settings.get('name')==request['profiles'][0]['name'] and settings.get('argv')==flags
        and settings.get('parsed_cli_arguments')==expected_parsed and settings.get('autorouter_enabled') is True
        and settings.get('optimizer_enabled') is False
        and settings.get('effective_job_timeout_seconds')==budget['assigned_job_timeout_seconds']
        and settings.get('effective_optimizer_timeout_seconds')==budget['assigned_optimizer_timeout_seconds'],
        'actual strict getter parse/timeouts/optimizer differs')
    effective=settings['effective_requested_settings']
    require(set(effective)==set(parsed),'complete requested-settings population differs')
    for key,raw in parsed.items():
        wanted=expected_setting(key,raw);value=effective[key]
        require((type(value) in (int,float) and abs(value-wanted)<1e-9) if type(wanted) in (int,float) else type(value) is type(wanted) and value==wanted,
            'actual effective requested setting differs: '+key)
    require(effective['router.automatic_neckdown'] is False and effective['router.fanout.enabled'] is False
        and type(effective['router.neck_width_um']) in (int,float) and effective['router.neck_width_um']==0
        and effective['router.optimizer.enabled'] is False,'actual False/False/0 strict settings absent')

def narrowed(tree):
    result=copy.deepcopy(tree);_,resolve=g.source_net_identity(result);changed=[]
    for node in p.routes(result):
        if node[0]!='segment' or resolve(sx.one(node,'net'))!='ROUTE':continue
        width=sx.one(node,'width');require(Decimal(width[1])>=Decimal('.2'),'positive signal already below original minimum')
        changed.append(dict(uuid=sx.unquote(sx.one(node,'uuid')[1]),before_width=width[1],after_width='0.1'))
        width[1]='0.1';break
    require(len(changed)==1,'one fresh positive signal segment required')
    return result,changed

def undersized(plan,routed,job,*,output=None):
    output=OUT if output is None else Path(output)
    board=output/'undersized'/Path(routed['candidate']).name
    copy_bytes(io.inventory(Path(routed['candidate']).parent,contents=True),board.parent)
    expected,changed=narrowed(sx.read(board));sx.write(board,expected)
    require(p.immutable(expected)==p.immutable(sx.read(Path(routed['candidate'])))
        and all(row in p.routes(expected) for row in plan['protected_ast']),'undersized case changed source shell/KEEP')
    p.verify_candidate_files(board,plan['source_sha256'],p.sha(board));before=p.tree_hash(board.parent)
    copy_bytes({Path(n).name:io.read_bytes(ROOT/n,1024**2) for n in plan['tools']['implementation_sha256']},job.out/'code')
    native=job.drc('undersized-final',board,schematic_parity=True)
    row=dict(candidate=str(board),candidate_sha256=p.sha(board),report_sha256=p.sha(job.out/'undersized-final.json'),
        positive_candidate_sha256=routed['candidate_sha256'],positive_receipt_sha256=p.sha(OUT/'route/result.json'),
        changed=changed,before=before,native=native,steps=job.steps)
    check_negative(plan,row,output=output);return row

def check_negative(plan,row,*,output=None):
    output=OUT if output is None else Path(output)
    folder=output/'undersized-job';board=Path(row['candidate']);positive=f.read_json(OUT/'route/result.json')
    expected,changed=narrowed(sx.read(Path(positive['candidate'])))
    require(board==output/'undersized'/(fixture.STEM+'.kicad_pcb') and sx.read(board)==expected and row['changed']==changed
        and row['positive_candidate_sha256']==positive['candidate_sha256']==p.sha(Path(positive['candidate']))
        and row['positive_receipt_sha256']==p.sha(OUT/'route/result.json'),'same-original width-only falsifier differs')
    p.verify_candidate_files(board,plan['source_sha256'],row['candidate_sha256'])
    data=dict(schema=1,steps=row['steps'],source_hashes=row['before'],tools=plan['tools'])
    native=f.check_drc_stage(folder,data,'undersized-final',board,folder/'undersized-final-input'/board.name,False,row['before'],schematic_parity=True)
    badids={item['uuid'] for item in changed};fields=native.get('field_parity',{}).get('qualification',{})
    require(native==row['native'] and not p.native_accepted(native) and native['opens']==0 and native['blocking']>0
        and any(item['severity']=='error' and item['type']=='track_width' and any(n.get('uuid') in badids for n in item.get('items',[])) for item in native['findings'])
        and native['ignored_checks']==positive['native']['ignored_checks'] and native['warnings']==6 and native['exclusions']==0
        and fields.get('component_count')==6 and fields.get('compared_field_count')==18,'actual width-specific fullSCH Native falsifier incomplete')
    require(p.sha(board)==row['candidate_sha256'] and p.sha(folder/'undersized-final.json')==row['report_sha256'],'width falsifier hash differs')
    ls.check_normal_policy(folder,data,max_bytes=128*1024**2,max_files=2048)

def execute(plan,pin):
    context(plan,pin);OUT.mkdir();copy_bytes(io.inventory(PREP/'source',contents=True),OUT/'source')
    owner={};h.capture_destination(owner,OUT);routed=None;job=None;getter_job=None
    report=dict(schema=1,accepted=False,passed=False,status='failed',git_head=plan['git_head'],protocol_sha256=pin,
        complete_external_cost_qualification_required=True,
        scope='Fresh owned strict global-minimum-width C + same-original undersized trace only. No physical-short rerun, benchmark/gain/support/default/GUI/physical claim.')
    prep=plan['preparation_costs']
    require(all(type(prep.get(k)) in (int,float) and 0<=prep[k]<WHOLE for k in ('wall_seconds','full_cpu_seconds'))
        and prep.get('publication_allowance_seconds')==2,'bounded preparation cost required')
    def remaining():return min(WHOLE-prep['wall_seconds']-2-(time.monotonic()-START),WHOLE-prep['full_cpu_seconds']-2-(cpu()-CPU0))-READ_RESERVE-2
    def stable():
        h.owned_destination(owner);context(plan,pin)
        require(p.tree_hash(OUT/'source')==plan['source_sha256'],'control source changed')
        if report.get('passed'):
            require(shared.material(OUT)==report['completed_evidence'],'completed control material changed')
            positive=f.read_json(OUT/'route/result.json');bad=report['undersized']
            require(p.sha(OUT/'route/result.json')==report['positive']['receipt_sha256'],'positive receipt changed')
            check_settings(plan,report['strict_settings'])
            require(shared.material(OUT)==report['completed_evidence'],'completed material changed during settings replay')
            ls.check_normal_policy(OUT/'route',positive,max_bytes=128*1024**2,max_files=2048)
            ls.check_normal_policy(OUT/'undersized-job',dict(schema=1,steps=bad['steps'],source_hashes=bad['before'],tools=plan['tools']),max_bytes=128*1024**2,max_files=2048)
    def account():
        report.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,reader_reserved_seconds=READ_RESERVE)
        if remaining()<=0 and report['status']!='cancelled':report.update(status='budget_exceeded',passed=False)
        if report['status']!='completed':report['passed']=False
    try:
        routed=s.prune(OUT/'source'/(fixture.STEM+'.kicad_pcb'),OUT/'route',INNER,
            proposal_policy='chains',incumbent_scoring='via_default',_incumbent_policy=POLICY)
        require(routed['accepted'] is True,'fresh strict C candidate rejected: '+str(routed.get('reason',routed['status'])))
        positive=check_positive(plan)
        report['positive']={k:positive[k] for k in ('candidate_sha256','native_report_sha256','native','metrics','improvements')}
        report['positive']['receipt_sha256']=p.sha(OUT/'route/result.json')
        getter_job=shared.BoundJob(OUT/'strict-settings-job',WHOLE,remaining,protect_local_settings=True)
        report['strict_settings']=observe_settings(plan,getter_job)
        job=shared.BoundJob(OUT/'undersized-job',WHOLE,remaining,protect_local_settings=True)
        report['undersized']=undersized(plan,positive,job);check_negative(plan,report['undersized']);check_positive(plan)
        report.update(status='completed',passed=True)
    except (Exception,KeyboardInterrupt) as exc:
        cancelled=isinstance(exc,KeyboardInterrupt) or routed and (routed.get('status')=='cancelled' or any(x.get('status')=='cancelled' for x in routed.get('steps',[]))) or any(item and any(x.get('status')=='cancelled' for x in item.steps) for item in (job,getter_job))
        report.update(status='cancelled' if cancelled else 'failed',passed=False,error=type(exc).__name__+': '+str(exc))
    report['completed_evidence']=shared.material(OUT)
    f.publish(OUT,report,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
    print(f.canonical({k:report.get(k) for k in ('passed','status','error','wall_seconds','full_cpu_seconds')}))
    return report

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['prepare','run'],required=True);ap.add_argument('--source-head',required=True);ap.add_argument('--protocol-sha256')
    args=ap.parse_args();handlers={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
    def interrupted(*_):raise KeyboardInterrupt
    try:
        for sig in handlers:signal.signal(sig,interrupted)
        with p.validation_readback_session():
            if args.mode=='prepare':prepare(args.source_head);return
            plan=f.read_json(PROTOCOL);require(plan['git_head']==args.source_head and args.protocol_sha256==p.sha(PROTOCOL),'wrong checkpoint/protocol');context(plan,args.protocol_sha256)
            result=execute(plan,args.protocol_sha256)
            raise SystemExit(0 if result['passed'] and result['status']=='completed' else 130 if result['status']=='cancelled' else 2)
    finally:
        for sig,handler in handlers.items():signal.signal(sig,handler)
if __name__=='__main__':main()
