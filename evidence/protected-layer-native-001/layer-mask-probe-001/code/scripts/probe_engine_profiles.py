#!/usr/bin/env python3
"""Verify routing-profile settings against the actual pinned local JAR.

Default mode is settings/parser reflection only, without a board. Explicit
--layer-mask additionally imports a fixed owned DSN; neither mode constructs a
routing job or launches a solver. Run outside measured benchmarks.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import sys

ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'autorouter/runner.py').is_file())
sys.path.insert(0,str(ROOT))
from autorouter import config as c, pipeline as p
from autorouter.runner import run


def expected_setting(key,raw):
    if key.endswith(('job_timeout','.timeout')): return raw
    if key.endswith('improvement_threshold'): return float(raw)*100
    if raw in ('true','false'): return raw=='true'
    return int(raw) if raw.isdigit() else raw


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,help='New direct child of project .runs')
    parser.add_argument('--layer-mask',action='store_true',help='Explicit four-case import-only global layer-mask probe; no routing')
    args=parser.parse_args(argv)
    if args.layer_mask:
        return layer_main(args.output)
    output=Path(args.output).absolute()
    if output.parent!=ROOT/'.runs' or output.exists() or output.is_symlink() or (ROOT/'.runs').is_symlink():
        raise p.Rejected('New project-local output required')
    if p.sha(c.JAR)!=c.JAR_SHA256:raise p.Rejected('Pinned JAR mismatch')
    profiles=[]
    assigned={}
    for remaining in (120,105,45,900):
        for profile in ('standard','tuned','completion-only'):
            for strict in (False,True):
                settings=p.engine_profile_settings(profile,remaining,strict_class_targets=strict)
                name=f'{profile}_remaining_{remaining}_strict_{strict}'
                assigned[name]=settings
                profiles.append({'name':name,'argv':['-de','probe.dsn','-do','probe.ses',*settings['argv']]})
    request={'timespans':['60s','30s','100s','90s','60','30','100','90','00:01:00','00:00:30','00:01:40','00:01:30'],
             'profiles':profiles}
    p.check_storage()
    output.mkdir();(output/'tmp').mkdir();(output/'java-home').mkdir()
    shutil.copy2(Path(__file__).with_name('EngineProfileProbe.java'),output/'EngineProfileProbe.java')
    shutil.copy2(__file__,output/'probe_engine_profiles.py')
    p.save_json(output/'request.json',request)
    p.save_json(output/'assigned-settings.json',assigned)
    before={str(path):p.sha(path) for path in (c.JAR,c.JAVA,ROOT/'autorouter/pipeline.py',Path(__file__),Path(__file__).with_name('EngineProfileProbe.java'))}
    argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(c.JAVA),'-Xms32m','-Xmx256m',
          '-XX:ActiveProcessorCount=1','-Djava.awt.headless=true','-Duser.home='+str(output/'java-home'),
          '-Djava.io.tmpdir='+str(output/'tmp'),'--class-path',str(c.JAR),str(output/'EngineProfileProbe.java'),
          str(output/'request.json'),str(output/'actual-settings.json')]
    process=run(argv,cwd=output,log=output/'probe.log',timeout=20)
    p.save_json(output/'process.json',process)
    report={'schema':1,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'input_hashes':before,'router_executed':False,'board_loaded':False,'passed':False,'process':process}
    checks=[]
    if process['status']=='success' and process['exit_code']==0 and process['cleanup_complete']:
        actual=json.loads((output/'actual-settings.json').read_text())
        for text,seconds in actual['timespans_to_seconds'].items():
            if text.endswith('s'):checks.append(seconds is None)
            elif ':' in text:checks.append(seconds==sum(int(part)*scale for part,scale in zip(text.split(':'),(3600,60,1))))
            else:checks.append(seconds==int(text))
        for row in actual['profiles']:
            expected=assigned[row['name']]
            checks.extend([row['effective_job_timeout_seconds']==expected['assigned_job_timeout_seconds'],
                           row['effective_optimizer_timeout_seconds']==expected['assigned_optimizer_timeout_seconds'],
                           row['autorouter_enabled'] is True,
                           row['optimizer_enabled']==(expected['profile']!='completion-only')])
            for flag in expected['argv']:
                key,raw=flag[2:].split('=',1)
                value=row['effective_requested_settings'][key]
                wanted=expected_setting(key,raw)
                checks.append(abs(value-wanted)<1e-6 if isinstance(wanted,float) else value==wanted)
                checks.append(key in row['parsed_cli_arguments'])
        checks.extend(p.sha(path)==digest for path,digest in before.items())
        report.update(passed=all(checks),checks=len(checks),checks_passed=sum(checks),profiles=len(actual['profiles']),
                      actual_settings_sha256=p.sha(output/'actual-settings.json'))
    p.save_json(output/'result.json',report)
    print(json.dumps({'passed':report['passed'],'receipt':str(output/'result.json')}))
    return 0 if report['passed'] else 1




# The optional import-only mode shares bounded IO/cancellation with the existing
# pinned importer. Default profile probing above keeps its original semantics.
LAYER_IDS=('source-all','front-only','back-only','reversed-mapping-negative')
LAYERS=('F.Cu','B.Cu')
DSN_REL='evidence/placement-production-native-001/native.dsn'
DSN_SHA='53bcbd2c1978ce85ffaeeabdc28adf0c590d786de63345ccfc1e23b4b61eeb22'
LAYER_MODE='import_only_layer_masks'
LAYER_SECONDS=60.0
LAYER_LIMIT=10*1024**2


def layer_helpers():
    from experiments.pic_padstack_import_probe_v1 import driver
    return driver


def build_layer_mask(entries, layer_order=LAYERS):
    """Map exact named Boolean entries into the unmodified physical order."""
    if tuple(layer_order)!=LAYERS: raise ValueError('actual F.Cu,B.Cu order required')
    if not isinstance(entries,(list,tuple)) or len(entries)!=2: raise ValueError('two named values required')
    values={}
    for row in entries:
        if not isinstance(row,(list,tuple)) or len(row)!=2: raise ValueError('name/value pair required')
        name,value=row
        if not isinstance(name,str) or name not in LAYERS or name in values or type(value) is not bool:
            raise ValueError('unique known layer and strict Boolean required')
        values[name]=value
    return [values[name] for name in LAYERS]


def layer_request(dsn):
    rows=[]
    for name,requested in zip(LAYER_IDS,(LAYERS,('F.Cu',),('B.Cu',),('F.Cu',))):
        order=tuple(reversed(LAYERS)) if name==LAYER_IDS[-1] else LAYERS
        # Deliberately wrong fourth vector: never passed through the safe builder.
        mask=[layer in requested for layer in order]
        argv=['--router.autorouter.enabled=false','--router.optimizer.enabled=false',
              '--router.layers.routable='+','.join(str(v).lower() for v in mask)]
        rows.append({'case':name,'requested_names':list(requested),'mapping_order':list(order),'mask':mask,'argv':argv})
    return {'schema':1,'mode':LAYER_MODE,'dsn':str(dsn),'dsn_sha256':DSN_SHA,'cases':rows}


def validate_layer_observations(actual, request):
    b=layer_helpers()
    eq=lambda a,c:b.canonical(a)==b.canonical(c)
    if not eq(request,layer_request(request.get('dsn'))): raise ValueError('fixed request differs')
    if (type(actual) is not dict or type(actual.get('schema')) is not int or actual['schema']!=1
            or actual.get('mode')!=LAYER_MODE or actual.get('input_sha256')!=DSN_SHA
            or any(actual.get(k) is not False for k in ('routing_executed','native_executed','layer_support_qualified'))):
        raise ValueError('observation scope/input differs')
    rows=actual.get('cases')
    if type(rows) is not list or [r.get('case') for r in rows if type(r) is dict]!=list(LAYER_IDS) or len(rows)!=4:
        raise ValueError('exact four case identities required')
    comparisons=[]
    for row,want in zip(rows,request['cases']):
        if (row.get('status')!='observed' or row.get('input_sha256')!=DSN_SHA or not eq(row.get('argv'),want['argv'])
                or row.get('parser_result_class')!='app.freerouting.io.BoardReadResult$Success'
                or type(row.get('parser_warnings')) is not list or any(type(x) is not str for x in row['parser_warnings'])):
            raise ValueError('import/CLI case did not match')
        sources=row.get('sources')
        classes=['app.freerouting.settings.sources.'+n for n in ('DefaultSettings','DsnFileSettings','CliSettings')]
        if (type(sources) is not list or len(sources)!=3 or [r.get('class') for r in sources]!=classes
                or any(type(r.get('priority')) is not int or type(r.get('name')) is not str or not r['name'] for r in sources)):
            raise ValueError('exact settings sources required')
        parsed=row.get('parsed_cli_arguments')
        expected=dict(flag[2:].split('=',1) for flag in want['argv'])
        if type(parsed) is not dict or not eq(parsed,expected): raise ValueError('parsed CLI differs')
        states=row.get('states')
        if type(states) is not list or [s.get('name') for s in states]!=['before_init','after_init','after_if_needed']:
            raise ValueError('all initialization boundaries required')
        physical=None
        for state in states:
            if (not eq(state.get('settings_layer_count'),2) or state.get('autorouter_enabled') is not False
                    or state.get('optimizer_enabled') is not False or state.get('ignored_netclasses') not in (None,[])):
                raise ValueError('enabled job/exclusions/layer count differs')
            flags=[{'index':i,'raw_routable':flag,'active':flag} for i,flag in enumerate(want['mask'])]
            if not eq(state.get('flags'),flags): raise ValueError('raw or accessor mask differs')
            board=state.get('board')
            expected_layers=[{'index':i,'name':name,'signal':True} for i,name in enumerate(LAYERS)]
            if (type(board) is not dict or board.get('bounded') is not True or not eq(board.get('layer_count'),2)
                    or not eq(board.get('layers'),expected_layers) or not eq(board.get('pin_count'),4)
                    or not eq(board.get('trace_count'),0) or not eq(board.get('via_count'),0)):
                raise ValueError('physical board layer/pin/route census differs')
            items=board.get('items'); count=board.get('item_count')
            if type(count) is not int or not 4<=count<=64 or type(items) is not list or len(items)!=count:
                raise ValueError('bounded full item census required')
            ids=[]
            for item in items:
                if (type(item) is not dict or type(item.get('id')) is not int or item['id']<=0
                        or type(item.get('class')) is not str or not item['class'].startswith('app.freerouting.board.')
                        or any(type(item.get(k)) is not int or item[k] not in (0,1) for k in ('first_layer','last_layer'))
                        or item['first_layer']>item['last_layer'] or type(item.get('nets')) is not list
                        or len(item['nets'])>8 or any(type(n) is not int or n not in (1,2) for n in item['nets'])):
                    raise ValueError('item identity/layer/net census malformed')
                ids.append(item['id'])
            if ids!=sorted(set(ids)): raise ValueError('duplicate or unordered item ids')
            if physical is None: physical=board
            elif not eq(physical,board): raise ValueError('board census changed during initialization')
        enabled=[name for name,flag in zip(LAYERS,want['mask']) if flag]
        accepted=enabled==want['requested_names']
        expected_acceptance=want['case']!=LAYER_IDS[-1]
        if accepted is not expected_acceptance: raise ValueError('semantic mapping control failed')
        comparisons.append({'case':want['case'],'mask_transport_observed':True,'enabled_names':enabled,
            'requested_names':want['requested_names'],'semantic_mapping_accepted':accepted,
            'expected_semantic_rejection':not expected_acceptance})
    return comparisons


def layer_source_paths():
    return [ROOT/p for p in ('scripts/probe_engine_profiles.py','scripts/EngineProfileProbe.java',
        'tests/test_layer_mask_probe.py','docs/layer-mask-probe.md','toolchain.lock.json',
        'experiments/pic_padstack_import_probe_v1/driver.py')]+sorted((ROOT/'autorouter').glob('*.py'))


def layer_runtime():
    b=layer_helpers(); git=b.head_witness()
    # Sample metadata first, then all material: no owned metadata read follows hashes.
    lock=b.decode(b.content(ROOT/'toolchain.lock.json',65536)); tools={}
    for name in ('java','freerouting'):
        pin=lock['tools'][name]; path=c.resolve_tool_path(pin['path'])
        got=b.content(path,pin['bytes'],digest=True)
        if got!={k:pin[k] for k in ('bytes','sha256')}: raise ValueError('pinned tool changed: '+name)
        tools[name]={'path':str(path),**got}
    if tools['freerouting']['sha256']!=c.JAR_SHA256: raise ValueError('engine pin differs')
    for name,path in (('python',Path(sys.executable).resolve()),('sandbox',Path('/usr/bin/sandbox-exec'))):
        tools[name]={'path':str(path),**b.content(path,16*1024**2,digest=True)}
    sources={str(path.relative_to(ROOT)):b.content(path,1024**2,digest=True) for path in layer_source_paths()}
    basis={}
    for relative,digest in LAYER_BASIS.items():
        row=b.content(ROOT/relative,1024**2,digest=True)
        if row['sha256']!=digest: raise ValueError('pinned source/API/DSN differs: '+relative)
        basis[relative]=row
    return {'tools':tools,'sources':sources,'basis':basis,'git':git}


def layer_publish(out,record,stable,account,remaining):
    import uuid
    b=layer_helpers(); path=out/'result.json'
    def invalidate():
        for current in (path,path.with_suffix('.json.partial')):
            if current.exists(): current.rename(out/('invalidated-'+uuid.uuid4().hex+'-'+current.name))
    try:
        stable(); account(); wanted=b.canonical(record); b.write(path,record); stable()
        if b.content(path)!=wanted or b.canonical(record)!=wanted: raise ValueError('canonical result changed during publication')
        remaining()
    except (Exception,KeyboardInterrupt) as exc:
        invalidate(); record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'invalidated',passed=False,
            observations_complete=False,layer_support_qualified=False,routing_accepted=False,
            final_validation_error=type(exc).__name__+': '+str(exc))
        record.setdefault('error',record['final_validation_error']); account()
        try:b.write(path,record)
        except (Exception,KeyboardInterrupt):invalidate()
    return record


def layer_experiment(output, *, started=None, cpu_started=None):
    import os, subprocess, time
    b=layer_helpers()
    if Path(__file__).resolve()!=ROOT/'scripts/probe_engine_profiles.py': raise ValueError('promoted committed helper required')
    started=time.monotonic() if started is None else started
    cpu_started=b.cpu() if cpu_started is None else cpu_started
    out=b.real(output)
    if out.parent!=ROOT/'.runs' or out.exists(): raise ValueError('fresh project .runs child required')
    out.mkdir(); before=None; frozen={}
    record={'schema':1,'mode':LAYER_MODE,'status':'preparing','passed':False,'observations_complete':False,
        'routing_accepted':False,'routing_executed':False,'native_executed':False,'layer_support_qualified':False,
        'budget_seconds':LAYER_SECONDS,'cpu_budget_seconds':LAYER_SECONDS,'max_output_bytes':LAYER_LIMIT,'steps':[],
        'accounting_point':'Sample before publication; final wall/full-CPU acceptance caps include all final checks.',
        'cpu_budget_enforcement':'Measured SELF plus waited CHILDREN; no hard CPU preemption.',
        'freshness_limit':'Finite bounded samples, not protection against arbitrary concurrent writers.'}
    def remaining():
        left=min(LAYER_SECONDS-(time.monotonic()-started),LAYER_SECONDS-(b.cpu()-cpu_started))
        if left<=0: raise TimeoutError('shared wall/full-CPU ceiling exceeded')
        return left
    def account():record.update(wall_seconds=time.monotonic()-started,total_cpu_seconds=b.cpu()-cpu_started)
    def capture():
        observed=b.inventory(out)
        if any(observed.get(k)!=v for k,v in frozen.items()): raise ValueError('previously captured evidence changed')
        frozen.update(observed)
    def stable():
        observed=b.inventory(out)
        if any(observed.get(k)!=v for k,v in frozen.items()): raise ValueError('captured evidence changed')
        if before is not None and layer_runtime()!=before: raise ValueError('runtime/source/tool/HEAD changed')
        observed=b.inventory(out)
        if any(observed.get(k)!=v for k,v in frozen.items()): raise ValueError('captured evidence changed after material checks')
        remaining()
    try:
        before=layer_runtime(); record['runtime']=before
        for relative,pin in before['sources'].items():
            raw=b.content(ROOT/relative,1024**2)
            proc=subprocess.run(['git','show',before['git']['head']+':'+relative],cwd=ROOT,capture_output=True,
                                timeout=min(3,remaining()),check=True)
            if proc.stdout!=raw or b.sha(raw)!=pin['sha256']: raise ValueError('commit exact helper/runtime bytes first')
            target=out/'code'/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        # All own metadata subprocesses have finished before material freshness.
        stable(); b.write(out/'runtime.json',before)
        (out/'fixture.dsn').write_bytes(b.content(ROOT/DSN_REL,65536))
        request=layer_request(out/'fixture.dsn'); b.write(out/'request.json',request)
        for name in ('home','tmp'):(out/name).mkdir()
        capture();stable()
        env={'HOME':str(out/'home'),'TMPDIR':str(out/'tmp'),'PATH':'/usr/bin:/bin','LANG':'C','LC_ALL':'C'}
        argv=[*b.SANDBOX,before['tools']['java']['path'],'-Xms32m','-Xmx256m','-XX:ActiveProcessorCount=1',
            '-Djava.awt.headless=true','-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
            '--class-path',before['tools']['freerouting']['path'],str(out/'code/scripts/EngineProfileProbe.java'),
            str(out/'request.json'),str(out/'observations.json'),'--layer-mask']
        record['requested_argv']=argv
        step=run(argv,cwd=out,log=out/'probe.log',timeout=remaining(),max_log_bytes=1024**2,env=env,
                 max_group_rss_bytes=1024**3,max_workdir_bytes=LAYER_LIMIT)
        step={**step,'cwd':str(out)} # runner receipt has argv/log, but no cwd field.
        record['steps'].append(step); b.write(out/'process.json',step)
        capture() # Complete stage evidence is frozen before any worker JSON parse.
        if step.get('status')=='cancelled':raise KeyboardInterrupt('owned import worker cancelled')
        if (step.get('status')!='success' or type(step.get('exit_code')) is not int or step['exit_code']!=0
                or step.get('cleanup_complete') is not True or step.get('argv')!=argv or step.get('cwd')!=str(out)):
            raise ValueError('worker process/command/cleanup failed')
        if step.get('log_truncated') is not False: raise ValueError('complete bounded worker log required')
        stable()
        actual=b.decode(b.content(out/'observations.json',262144))
        rows=validate_layer_observations(actual,request)
        record.update(status='completed',passed=True,observations_complete=True,case_comparison=rows,
                      observations_sha256=frozen['observations.json']['sha256'])
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
    record['frozen_evidence']=frozen
    return layer_publish(out,record,stable,account,remaining)


def layer_main(output):
    import fcntl,time
    b=layer_helpers();started=time.monotonic();cpu_started=b.cpu()
    with b.cancellation(),b.real(ROOT/'.runs/quality-experiment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=layer_experiment(output,started=started,cpu_started=cpu_started)
    print(json.dumps({k:result.get(k) for k in ('status','passed','observations_complete','wall_seconds','total_cpu_seconds')}))
    return 0 if result['passed'] else 1


# Exact cached primary/API basis; ignored evidence must be locally present.
LAYER_BASIS={'evidence/placement-production-native-001/native.dsn': '53bcbd2c1978ce85ffaeeabdc28adf0c590d786de63345ccfc1e23b4b61eeb22', '.runs/layer-mask-api-001/javap.log': 'c89b7c1c0e1b48664f8c6f255a56639052b98d007a796336e4939cf39800f213', '.runs/layer-mask-api-001/pins.json': '8547ea38cad2a83715d8dce431cb1a71262ca0e13c219ce6355f6ca50cf0a40f', '.runs/layer-mask-api-001/process.json': '645f53caf817e5d956fd1d3be5fded7363aad136bbae0deff35b60ae915f496c', '.runs/custom-pad-area-api-inspection-002/app.freerouting.io.specctra.DsnReader.txt': 'a18e3e6f89873fcc5dd896eb16d3f38643b2507297e69e978a34dfa28196f2bc', '.runs/custom-pad-area-api-inspection-004/app.freerouting.io.BoardReadResult$Success.txt': '60d804130f4c304a012e47a05b65f91d69a38550931fd7081e05c574199052b1', '.runs/custom-pad-area-api-inspection-001/app.freerouting.board.facade.BasicBoard.txt': '071fee199356b6778919a1de798e0b023386d1f8a85e00631481da218cbfee2e', '.runs/custom-pad-area-api-inspection-002/app.freerouting.board.model.items.Item.txt': '9e8ac9898b259be0427143d96b8eb53b044216000ae1b71feb5eb0d9a591cae4', '.runs/optimizer-budget-research-001/CliSettings.java': '1b12c96378205bd59c2b53b9a5c9e1736fa4536d0287a4131f71617a34e4feae', '.runs/optimizer-budget-research-001/ReflectionUtil.java': '8d41e0539b0e012c53657bd91e41e06d548b82ee6cf7fca054f48cf9f1d2d02e', '.runs/optimizer-budget-research-001/RouterSettings.java': 'e7ca5c594c5e44d705ec1c5513d74c773c58d7f986d3b21366959d8d1f45c259', '.runs/optimizer-budget-research-001/RoutingJobScheduler.java': 'd94f979b94e786ae486754ae236fbd40834bb54059ba8ecd22326234646e9b69', '.runs/optimizer-budget-research-001/SettingsMerger.java': '1ad469626a293c72fa8134cf317169f2460cb4af92a8519e73065be54d401a35', '.runs/baseline-strength-review-001/LayerSettings.java': '3fd4c9ee9791ba196c009fc856231923be6069b553896e62affca0c9e5a56eaf', '.runs/baseline-strength-review-001/DefaultSettings.java': 'c5917a76c094dee678b508f9e9de0b2f9e5e9fcf801807c52fc2a48d4b8ead0c'}

if __name__=='__main__':sys.exit(main())
