"""Frozen same-account environment qualification of an installed-existing050 copy.

No build, new base interpreter, GUI, fresh-OS or standalone claim. The
lead must freeze a separate caller protocol and enforce complete exit <=300s
wall/full CPU. A fresh venv and install copy are prerequisite setup costs.
This parent owns one fresh runtime/.runs subtree; external tools stay fixed.
"""
import time
import resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from pathlib import Path
import argparse, fcntl, hashlib, json, os, re, signal, stat, sys
ADMIN = Path(__file__).resolve().parents[1]
RUNTIME = ADMIN/'.runs/runtime050 fresh install 001'
ORIGINAL = ADMIN/'.runs/runtime-directory-050/runtime'
ORIGINAL_MANIFEST = 'c037a58401e7c55c070ecd6be87820371a9e5150122f62a77173889997e42fe8'
QUALIFICATION = ADMIN/'.runs/runtime050-install-existing-qualification-001'
HEAD = 'aa0072c6b3d8090de2603e5ecb42a95968fb873b'
KIND = 'runtime050-install-existing-clean-environment-v1'
LIMITS = dict(whole_wall_full_CPU_seconds=300, doctor_seconds=30, inner_watchdog_seconds=255,
              inner_wall_full_CPU_seconds=240, route_seconds=90, export_seconds=90,
              aggregate_bytes=768*1024**2, group_RSS_bytes=4*1024**3, log_bytes=512*1024)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--protocol',type=Path,required=True);ap.add_argument('--protocol-sha256',required=True)
    args=ap.parse_args();protocol=args.protocol
    if type(args.protocol_sha256)is not str or re.fullmatch('[0-9a-f]{64}',args.protocol_sha256)is None:
        raise ValueError('exact caller protocol SHA256 required')
    if protocol!=QUALIFICATION/'protocol.json':raise ValueError('fixed qualification protocol required')
    if (not protocol.is_absolute() or protocol.resolve()!=protocol
            or any(x.is_symlink() for x in (protocol,*protocol.parents))):raise ValueError('real absolute caller protocol required')
    info=protocol.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or not 0<info.st_size<=1024**2:raise ValueError('bounded single-link caller protocol required')
    raw=protocol.read_bytes()
    if len(raw)!=info.st_size or hashlib.sha256(raw).hexdigest()!=args.protocol_sha256:raise ValueError('independently frozen caller protocol SHA required')
    plan=json.loads(raw)
    if type(plan)is not dict or plan.get('runtime')!=str(RUNTIME):raise ValueError('exact fresh050 root required')
    MANIFEST=plan.get('runtime_manifest_sha256')
    if type(MANIFEST)is not str or re.fullmatch('[0-9a-f]{64}',MANIFEST)is None:
        raise ValueError('caller-pinned actual new manifest SHA256 required')
    sys.path.insert(0,str(RUNTIME));sys.dont_write_bytecode=True
    from autorouter import config as c,pipeline as p,floor_route as f,handoff as h
    from autorouter import provenance as pv,preferences as pref,placement_clearance as pc,sexpr as sx
    from autorouter import review_export as ex,local_settings as local
    from autorouter.runner import run
    def require(ok,message):
        if not ok:raise p.Rejected(message)
    require(c.ROOT==RUNTIME and Path(sys.prefix).resolve()==RUNTIME/'.venv'
        and Path(sys.executable).absolute()==RUNTIME/'.venv/bin/python' and sys.prefix!=sys.base_prefix
        and sys.version_info[:3]==(3,11,9),
        'invoke with exact fresh-root050 independent interpreter')
    require(f.read_json(protocol)==plan,'strict caller protocol JSON required')
    require(Path(__file__).absolute()==ADMIN/'.runs/qualify-runtime050-install-existing-environment-001.py'
        and plan.get('controller')==str(Path(__file__).absolute()) and p.sha(Path(__file__))==plan.get('controller_sha256'), 'exact parent controller pin required')
    require(plan.get('schema')==1 and type(plan['schema'])is int and plan.get('kind')==KIND
        and f.canonical(plan.get('limits'))==f.canonical(LIMITS) and plan.get('source_head')==HEAD
        and plan.get('runtime_manifest_sha256')==MANIFEST, 'exact050 installed-copy protocol/limits required')
    fixed={
        'assessment':ADMIN/'evidence/runtime050-native-milestone-002.json',
        'enclosure':ADMIN/'.runs/enclose-runtime030-ordinary-workflow-002.py',
        'driver':ADMIN/'scripts/qualify_runtime_workflow.py',
        'tools_defaults':QUALIFICATION/'tools-defaults.json',
        'query_preparation':QUALIFICATION/'preparation.json',
        'query_process':QUALIFICATION/'tools-defaults-process.json',
        'settings':QUALIFICATION/'settings.json',
        'original_manifest':ORIGINAL/'runtime-distribution.json',
        'installation_record':RUNTIME/'.runs/install-existing-runtime-001.json',
        'installer':ADMIN/'scripts/prepare_runtime.py',
    }
    for name,path in fixed.items():
        require(plan.get(name+'_path')==str(path) and h.real_path(path)==path
            and type(plan.get(name+'_sha256'))is str
            and re.fullmatch('[0-9a-f]{64}',plan[name+'_sha256'])is not None
            and p.sha(path)==plan[name+'_sha256'],'frozen '+name+' prerequisite differs')
    require(plan['assessment_sha256']=='1d0d2019d5505f1fad0134cc2163b3337ce227e1b8d841c8c3c8a81e21a94934'
        and plan['original_manifest_sha256']==ORIGINAL_MANIFEST
        and plan['enclosure_sha256']=='69d87dee41f94fe9e479e505093914325ed653cbb0cd58c9545272afefc1d59c'
        and plan['driver_sha256']=='0b1a3bc61e576d6475a4c922a7727b7831ccf28f3e0a9d2d80b557e3c1964034'
        and plan['settings_sha256']=='a73292826f5de5a992d4d04ec85ced90ecac269556f72b35180f610e79866a65',
        'exact demonstrated source/helpers/settings required')
    query=f.read_json(fixed['tools_defaults']);preparation=f.read_json(fixed['query_preparation'])
    query_process=f.read_json(fixed['query_process']);milestone=f.read_json(fixed['assessment'])
    require(preparation.get('runtime_manifest_sha256')==MANIFEST and preparation.get('source_head')==HEAD
        and preparation['preparation']['tools_query_sha256']==plan['tools_defaults_sha256']
        and preparation['preparation']['tools_query_process_sha256']==plan['query_process_sha256']
        and query_process.get('status')=='success' and query_process.get('exit_code')==0
        and query_process.get('cleanup_complete')is True and query_process.get('log_truncated')is False
        and query_process.get('log')==str(fixed['tools_defaults'])
        and query.get('runtime')==str(RUNTIME) and query.get('prefix')==str(RUNTIME/'.venv')
        and query.get('interpreter')==str(RUNTIME/'.venv/bin/python'),
        'fresh independent050 query provenance required')
    original_record=f.read_json(fixed['original_manifest'])
    original_implementation={name:pin for name,pin in original_record['immutable_files_sha256'].items()
                             if name.startswith('autorouter/')}
    original_identity=pv._runtime_identity(ORIGINAL,original_implementation)
    require(original_identity['manifest_sha256']==ORIGINAL_MANIFEST
        and original_identity['git_head']==HEAD,'original050 artifact is no longer bound')
    require(milestone.get('schema')==1 and type(milestone['schema'])is int
        and milestone.get('kind')=='runtime050-seven-completed-native-workflows-v1'
        and milestone.get('source_head')==HEAD and milestone.get('runtime_manifest_sha256')==ORIGINAL_MANIFEST
        and len(original_record['immutable_files_sha256'])==54
        and milestone['Native_cohort_passed']is True and milestone['full199']['passed']is True
        and milestone['invalid_controls']['passed']is True and len(milestone['cases'])==7
        and {row['case'] for row in milestone['cases']}=={'ordinary-whole4Cu', 'improve-floor2Cu', 'ordinary-hierarchy2Cu', 'ordinary-npth2Cu', 'improve-pour-only', 'ordinary-alias2Cu', 'improve-fractional'},
        'completed050 source provenance prerequisites required; not new-root Native proof')
    installation=f.read_json(fixed['installation_record'])
    require(installation.get('kind')=='existing-runtime-installation-record-v1'
        and installation.get('record_is_authoritative')is False
        and installation.get('source_root')==str(ORIGINAL)
        and installation.get('source_manifest_sha256')==ORIGINAL_MANIFEST
        and installation.get('destination_root')==str(RUNTIME)
        and installation.get('destination_manifest_sha256')==MANIFEST
        and installation.get('installer')==dict(path=str(fixed['installer']),
            sha256=plan['installer_sha256'],bytes=fixed['installer'].stat().st_size),
        'descriptive old/new-root installation record differs')
    def runtime_bound():
        require(pv._runtime_identity(ORIGINAL,original_implementation)==original_identity
            and f.read_json(RUNTIME/pv.MANIFEST)=={**original_record,'root':str(RUNTIME)}
            and pv._runtime_identity(RUNTIME,original_implementation)==plan['tools']['source_provenance'],
            'exact original population/build/lock/version/engine or new-root identity changed')
    runtime_bound()
    tools=plan['tools'];require(tools==query['tools'] and query['defaults']==dict(pref.DEFAULTS),'caller tools/default query differs')
    settings=dict(schema=1,scope='partial_completion',seconds=90,adapter='both',profile='standard',guidance='native',layers='source_all',scoring_preference=None)
    require(plan.get('settings')==settings and pref.load(fixed['settings']).parsed==settings,'exact ordinary partial90 settings required')
    source=ADMIN/'.runs/task-copper-fixed-alias-native-004/source/owned1007-transport.kicad_pcb'
    require(plan.get('source')==str(source) and h.real_path(source)==source,'exact external owned partial source required')
    hashes=plan['source_hashes'];require(pc.inventory(source.parent)==hashes,'caller original source hashes differ')
    require(p.check_schematic_class_support(source,class_context=None)is None,'unflagged schematic required')
    original=p.preflight(source,task_scope='partial_completion',class_context=None);protected=p.routes(original)
    require(len(protected)==4 and type(plan.get('protected_routes'))is int and plan['protected_routes']==4
        and plan.get('expected_Native_counts')==[0,0,0,0]
        and all(type(value)is int for value in plan['expected_Native_counts']),
        'all four original routes/full Native counts required')
    out=RUNTIME/'.runs/clean-env-partial-delivery-001'
    require(plan.get('output')==str(out) and h.real_path(out,existing=False)==out and not os.path.lexists(out),'fresh exact common output required')
    env=dict(HOME=str(out/'home'),TMPDIR=str(out/'tmp')+'/',PATH='/usr/bin:/bin:/usr/sbin:/sbin',
        USER='faisal',LOGNAME='faisal',LANG='C',LC_ALL='C',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PIP_NO_INDEX='1')
    require(plan.get('child_environment')==env,'exact caller-frozen minimal child environment required')
    manifest=RUNTIME/pv.MANIFEST;venv=RUNTIME/'.venv';venv_pins={str(path):p.sha(path) for path in (venv/'bin/python',venv/'pyvenv.cfg')}
    require(plan.get('venv_sha256')==venv_pins and plan.get('base_prefix')==sys.base_prefix=='/Users/faisal/.pyenv/versions/3.11.9','same existing3.11.9 base dependency required')
    require(p.sha(manifest)==MANIFEST and p.tool_manifest()==tools and tools['source_provenance']['kind']==pv.KIND
        and tools['git_head']==HEAD and tools['kicad']=='10.0.7','fresh-root050 runtime/tools differ')
    lockfd=os.open(ADMIN/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(lockfd,'r+') as lane:
        info=os.fstat(lane.fileno());require(stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_uid==os.getuid(),'owned existing shared experiment lock required')
        fcntl.flock(lane,fcntl.LOCK_EX|fcntl.LOCK_NB)
        out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out)
        for name in ('home','tmp'):(out/name).mkdir(mode=0o700)
        (out/'caller-protocol.json').write_bytes(raw);(out/'settings.json').write_bytes(pc.read_bytes(fixed['settings']))
        inner=dict(schema=1,kind='frozen-runtime050-install-existing-ordinary-workflow-clean-environment',runtime=str(RUNTIME),source_head=HEAD,
            runtime_manifest_sha256=MANIFEST,source=str(source),source_hashes=hashes,settings=settings,
            settings_sha256=plan['settings_sha256'],enclosure_sha256=plan['enclosure_sha256'],driver_sha256=plan['driver_sha256'],
            output=str(out/'workflow'),expected_counts=[0,0,0,0],expected_protected_count=4,
            budgets=dict(route=90,export=90,whole_wall_CPU=240,outer_watchdog=255),
            scope='Fresh installed-existing050 root with spaces; same-account ordinary partial2Cu delivery. No build/GUI/freshOS/external-dependency relocation/standalone claim.')
        p.save_json(out/'protocol.json',inner);inner_pin=p.sha(out/'protocol.json');steps=[];completed=None
        report=dict(schema=1,kind=KIND,status='failed',controls_passed=False,workflow_delivered=False,accepted=False,
            production_admitted=False,actual_GUI=False,human_review=False,runtime=str(RUNTIME),source_head=HEAD,
            runtime_manifest_sha256=MANIFEST,protocol_sha256=args.protocol_sha256,controller_sha256=plan['controller_sha256'],
            tools=tools,source=str(source),source_hashes=hashes,settings=settings,protected_routes=4,
            original_runtime=str(ORIGINAL),original_manifest_sha256=ORIGINAL_MANIFEST,
            installation_record_sha256=plan['installation_record_sha256'],installation_record_is_authoritative=False,
            explicit_child_environment=env,venv_sha256=venv_pins,base_prefix=sys.base_prefix,python_version=sys.version,inner_protocol_sha256=inner_pin,
            limits=LIMITS,processes=steps,external_complete_exit_required=True,
            scope='Installed-existing050 root/startup/environment axis only; immutable source map unchanged. Same user/base Python/external tools; no GUI/freshOS/account/dependency relocation/standalone/quality claim. Setup costs separate.')
        def remaining():return min(300-(time.monotonic()-START),300-(cpu()-CPU0))
        def material():
            files=pc.inventory(out,max_bytes=LIMITS['aggregate_bytes'],max_files=16000,max_entries=32000)
            return {name:pin for name,pin in files.items() if name not in ('result.json','result.json.partial')
                and not name.startswith(('invalidated-result-','interrupted-result-'))}
        def fresh():
            runtime_bound()
            require(h.owned_destination(owner)==out and h.real_path(protocol)==protocol and p.sha(protocol)==args.protocol_sha256
                and p.sha(out/'caller-protocol.json')==args.protocol_sha256 and p.sha(Path(__file__))==plan['controller_sha256']
                and p.sha(manifest)==MANIFEST and p.tool_manifest()==tools,'caller/controller/runtime/tool freshness differs')
            for name,path in fixed.items():require(p.sha(path)==plan[name+'_sha256'],'prerequisite changed: '+name)
            for path,pin in venv_pins.items():require(p.sha(path)==pin,'existing interpreter identity changed')
            for item in steps:
                require(p.sha(out/(item['name']+'.log'))==item['log_sha256']
                    and f.read_json(out/(item['name']+'-process.json'))==item['process'],'parent process/log evidence changed')
            require(pc.inventory(source.parent)==hashes and p.sha(out/'settings.json')==plan['settings_sha256']
                and p.sha(out/'protocol.json')==inner_pin,'source/settings/inner protocol changed')
            for name,module in tuple(sys.modules.items()):
                if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):require(Path(module.__file__).resolve().is_relative_to(RUNTIME),'module escaped runtime: '+name)
            current=material()
            require(completed is None or current==completed,'completed common output material changed')
            require(remaining()>0,'whole300 wall/fullCPU exhausted')
        def command(name,argv,seconds):
            fresh();require(remaining()>15,'insufficient final readback reserve')
            result=run([*f.SANDBOX,*map(str,argv)],cwd=out,env=env,log=out/(name+'.log'),
                timeout=min(seconds,remaining()-12),max_log_bytes=LIMITS['log_bytes'],
                max_group_rss_bytes=LIMITS['group_RSS_bytes'],max_workdir_bytes=LIMITS['aggregate_bytes'])
            p.save_json(out/(name+'-process.json'),result);steps.append(dict(name=name,process=result,log_sha256=p.sha(out/(name+'.log'))))
            if result.get('status')=='cancelled':raise KeyboardInterrupt
            require(result.get('status')=='success' and result.get('exit_code')==0
                and result.get('cleanup_complete')is True and result.get('log_truncated')is False,name+' failed/incomplete')
            return result
        def check_delivery():
            execution=f.read_json(out/'execution.json');child=f.read_json(out/'workflow/result.json')
            require(execution.get('controls_passed')is True and execution.get('workflow_delivered')is True
                and execution.get('protocol_sha256')==inner_pin and execution.get('child_sha256')==p.sha(out/'workflow/result.json')
                and max(execution['complete_wall_seconds'],execution['complete_full_CPU_seconds'])<=240,'complete inner qualification failed')
            process=execution['process'];require(process['status']=='success' and process['exit_code']==0
                and process['cleanup_complete']is True and process.get('log_truncated')is False,'inner driver cleanup failed')
            workspace=h.real_path(child['workspace']);require(workspace.parent==out/'workflow' and workspace.name.startswith('autorouter-gui-'),'workflow workspace escaped')
            require(child.get('status')=='completed' and child.get('workflow_delivered')is True and child.get('accepted')is False
                and child.get('actual_GUI')is False and child.get('human_review')is False and child.get('tools')==tools
                and child.get('source')==str(source) and child.get('source_hashes')==hashes and child.get('settings')==settings
                and child.get('settings_path')==str(out/'settings.json') and child.get('settings_sha256')==plan['settings_sha256']
                and child.get('driver_sha256')==plan['driver_sha256'],'actual workflow source/settings/tools differ')
            require([x['stage'] for x in child['processes']]==['preview','route','review','choice','export','verify_export'],'all six actual CLI stages required')
            commands=dict(preview='preview',route='route',review='review-copy',choice='review-choice',export='review-export',verify_export='review-export-check')
            for stage in child['processes']:
                process=stage['process'];log=out/'workflow'/(stage['stage']+'.log')
                require(process['exit_code']==0 and process['cancel_requested']is False and process['log_truncated']is False
                    and process['argv'][:5]==[str(venv/'bin/python'),'-B','-m','autorouter',commands[stage['stage']]]
                    and log.stat().st_size==process['log_bytes']<=LIMITS['log_bytes']
                    and p.sha(log)==stage['log_sha256'],'CliJob stage failed, cancelled, argv/log changed or truncated')
            route_path=workspace/'route/result.json';export_path=workspace/'export/export.json'
            with p.validation_readback_session():
                require(p.check_result(route_path).get('current')is True and ex.check_export(export_path).get('current')is True,'ordinary central current readback failed')
            route=f.read_json(route_path);exported=f.read_json(export_path)
            require(route['accepted']is True and route['status']=='routing_accepted' and exported['export_accepted']is True
                and route['source']==str(source) and exported['inputs']['source']==str(source)
                and exported['inputs']['receipt']==str(route_path) and exported['inputs']['receipt_sha256']==p.sha(route_path)
                and exported['original_geometry_and_routing_unchanged']is True
                and route['scope']=='partial_completion' and route['engine_profile']=='standard' and route['adapter']=='both'
                and route['scoring_variant']is None and route['budget_seconds']==route['cpu_budget_seconds']==90
                and exported['budget_seconds']==90 and route['metrics']['copper_layers']==2
                and route['candidate_sha256']==exported['candidate_sha256'],'ordinary positive/profile/budget/candidate contract differs')
            for data in (route,exported):
                require(data['source_hashes']==hashes and data['tools']==tools
                    and data['schematic_parity']=='checked by final native DRC'
                    and [data['native'][key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,0,0], 'own final Native/fullSCH/source proof differs')
                candidate=h.real_path(data['candidate']);p.verify_candidate_files(candidate,hashes,data['candidate_sha256'])
                tree=sx.read(candidate);require(p.immutable(tree)==p.immutable(original) and all(x in p.routes(tree) for x in protected),'original design/protected4 changed')
            pairs=[];preview=f.read_json(workspace/'review/review.json')['preview'];plot=workspace/'review/plot-work'
            for step in preview['steps']:
                require(step['cwd']==str(plot),'plot worker escaped')
                process=f.process_check(plot,preview,step['name'],step['argv'])
                pairs.append((plot,f.read_json(plot/(step['name']+'-input-binding.json')),process))
            return workspace,route,exported,pairs
        try:
            command('doctor',['/bin/sh','-c','cd "$1"; shift; exec "$@"','sh',RUNTIME,venv/'bin/python','-B','-m','autorouter','doctor'],30)
            doctor=f.read_json(out/'doctor.log');report['doctor']=doctor
            require(doctor.get('ready')is True and doctor['checks']['runtime_provenance']['identity']==tools['source_provenance'],'fresh-root050 doctor not ready')
            command('workflow',[venv/'bin/python','-B',fixed['enclosure'],'--protocol',out/'protocol.json'],255)
            workspace,route,exported,pairs=check_delivery()
            report.update(status='completed',controls_passed=True,workflow_delivered=True,workspace=str(workspace),
                route_receipt_sha256=p.sha(workspace/'route/result.json'),export_receipt_sha256=p.sha(workspace/'export/export.json'),
                candidate_sha256=route['candidate_sha256'],Native_counts=[0,0,0,0],all_four_original_routes_preserved=True)
        except (Exception,KeyboardInterrupt) as exc:
            report.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed',error=type(exc).__name__+': '+str(exc))
        completed=material();report['completed_evidence_sha256']=completed
        def final_check():
            fresh()
            if report['status']!='completed':return
            workspace,route,exported,pairs=check_delivery()
            require(p.sha(workspace/'route/result.json')==report['route_receipt_sha256']
                and p.sha(workspace/'export/export.json')==report['export_receipt_sha256']
                and route['candidate_sha256']==report['candidate_sha256'],'published final route/export identity changed')
            fresh()  # Last complete source/tool/material callback precedes every final PRL event.
            local.check_final_events([(workspace/'route',route),(workspace/'export/validation',exported)],c.CLI,pairs=pairs)
        def account():
            report.update(sampled_wall_seconds=time.monotonic()-START,sampled_full_CPU_seconds=cpu()-CPU0,
                accounting_point='Sample precedes final publication/readback; whole300 includes them and actual exit requires lead external accounting.')
            if remaining()<=0:report.update(status='budget_exceeded')
            if report['status']!='completed':report.update(controls_passed=False,workflow_delivered=False)
        f.publish(out,report,fresh,account,remaining,owned=lambda:h.owned_destination(owner),final_check=final_check)
        print(json.dumps({key:report.get(key) for key in ('status','controls_passed','workflow_delivered','error','reason','sampled_wall_seconds','sampled_full_CPU_seconds')}))
        return 0 if report['status']=='completed' and report['controls_passed'] else 2


if __name__=='__main__':
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    raise SystemExit(main())
