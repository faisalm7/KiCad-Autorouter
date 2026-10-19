"""Two frozen ordinary runtime035 partial2Cu Native invalid controls.

Copy into runtime/.runs and execute with its independent interpreter and a
separately frozen --protocol/--protocol-sha256. Ordinary whole/partial positive
prerequisites, external originals, scope/settings/tools and exact paths are
caller-declared, never selected from retained receipts. Existing shared180s
wall/full-CPU enclosure is mandatory. No engine, export, admission or GUI claim.
"""
import time
import resource
START = time.monotonic()
def cpu():
    return sum(x.ru_utime+x.ru_stime for x in
        (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
from decimal import Decimal
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import signal
import sys
import uuid
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import config as c,pipeline as p,floor_route as f,handoff as h
from autorouter import review_export as ex,placement_clearance as pc,sexpr as sx
from autorouter import provenance as pv,local_settings as local
CONTROLLER = 'qualify-runtime035-ordinary-native-invalid-001.py'
HEAD = '7edc7229ea905e6734bf6cec8ff926a92e6a8613'
MANIFEST = '8f0c455d7db2beb64e23283081fe788cfc26ee4d49cd95c8fd152b8e45ccb677'
KIND = 'runtime035-ordinary-Native-invalid-controls-v1'

def require(condition,message):
    if not condition:raise p.Rejected(message)
def real(value,*,existing=True):
    value=Path(value);require(value.is_absolute(),'absolute qualification paths required')
    return h.real_path(value,existing=existing)

def execute(protocol_path,protocol_sha256):
    protocol_path=real(protocol_path);raw_protocol=pc.read_bytes(protocol_path,1024*1024)
    require(hashlib.sha256(raw_protocol).hexdigest()==protocol_sha256,'separately frozen negative protocol hash required')
    plan=f.read_json(protocol_path)
    require(type(plan)is dict and type(plan.get('schema'))is int and plan['schema']==1
        and plan.get('kind')==KIND and plan.get('whole_wall_full_cpu_seconds')==180
        and plan.get('controller_args')==[] and plan.get('pass_key')=='control_passed'
        and plan.get('scope')=='partial_completion' and plan.get('profile')=='standard'
        and plan.get('adapter')=='both' and 'scoring_variant' in plan and plan['scoring_variant']is None
        and plan.get('route_seconds')==90 and plan.get('protected_routes')==4,
        'exact ordinary partial/standard90/both/scoringNone/protected4 contract required')
    runtime=real(plan['runtime']);self_path=real(Path(__file__).absolute())
    require(runtime==ROOT==c.ROOT and Path(sys.prefix).resolve()==runtime/'.venv'
        and sys.prefix!=sys.base_prefix and Path(sys.executable).absolute()==runtime/'.venv/bin/python'
        and self_path==runtime/'.runs'/CONTROLLER
        and p.sha(self_path)==plan['helper_sha256']==plan['controller_sha256'],
        'exact copied controller/runtime independent interpreter required')
    manifest=runtime/pv.MANIFEST;tools=p.tool_manifest()
    require(c.NATIVE_VERSION=='10.0.7' and tools==plan['tools'] and tools.get('kicad')=='10.0.7'
        and tools.get('git_head')==plan.get('source_head')==HEAD
        and tools.get('source_provenance',{}).get('kind')==pv.KIND
        and tools['source_provenance'].get('native_version')=='10.0.7'
        and p.sha(manifest)==plan.get('runtime_manifest_sha256')==MANIFEST
        and tools['source_provenance'].get('manifest_sha256')==MANIFEST,
        'exact035 committed selected7 runtime/tools/manifest required')
    pins=[];positives={}
    def positive(label,scope,seconds,count,counts,layers):
        item=plan[label+'_positive'];paths={}
        for name in ('protocol','execution','result','route','export'):
            path=real(item[name+'_path']);pin=item[name+'_sha256']
            require(p.sha(path)==pin,'frozen '+label+' '+name+' changed');pins.append((path,pin));paths[name]=path
        caller=f.read_json(paths['protocol']);execution=f.read_json(paths['execution'])
        source=real(item['source']);hashes=item['source_hashes']
        output=real(item['output']);workspace=real(item['workspace'])
        settings=dict(schema=1,scope=scope,seconds=seconds,adapter='both',profile='standard',
                      guidance='native',layers='source_all',scoring_preference=None)
        require(output==runtime/'.runs'/('production-'+label+'-delivery-'+('002' if label=='whole4Cu' else '001'))
            and workspace.parent==output and workspace.name.startswith('autorouter-gui-')
            and paths['result']==output/'result.json' and paths['route']==workspace/'route/result.json'
            and paths['export']==workspace/'export/export.json', 'caller-declared positive paths differ')
        require(caller.get('kind')=='frozen-runtime033-ordinary-workflow' and caller.get('schema')==1
            and caller.get('runtime')==str(runtime) and caller.get('source_head')==HEAD
            and caller.get('runtime_manifest_sha256')==MANIFEST and caller.get('source')==str(source)
            and caller.get('source_hashes')==hashes and caller.get('settings')==settings
            and caller.get('output')==str(output) and caller.get('expected_counts')==counts
            and caller.get('expected_protected_count')==count
            and caller.get('budgets',{}).get('route')==seconds and caller['budgets'].get('export')==seconds,
            'separately frozen '+label+' caller contract differs')
        settings_path=paths['protocol'].parent/'settings.json'
        require(p.sha(settings_path)==caller['settings_sha256'],'frozen positive settings changed')
        pins.append((settings_path,caller['settings_sha256']))
        data=f.read_json(paths['result']);prior=f.read_json(paths['route']);exported=f.read_json(paths['export'])
        require(execution.get('controls_passed')is True and execution.get('workflow_delivered')is True
            and execution.get('protocol_sha256')==item['protocol_sha256']
            and execution.get('child_receipt')==str(paths['result']) and execution.get('child_sha256')==item['result_sha256']
            and data.get('workflow_delivered')is True and data.get('status')=='completed'
            and data.get('accepted')is False and data.get('actual_GUI')is False and data.get('human_review')is False
            and data.get('source')==str(source) and data.get('source_hashes')==hashes and data.get('tools')==tools
            and data.get('workspace')==str(workspace) and data.get('settings')==settings
            and data.get('settings_path')==str(settings_path) and data.get('settings_sha256')==caller['settings_sha256']
            and data.get('driver_sha256')==caller['driver_sha256']
            and data.get('route_receipt_sha256')==item['route_sha256'], 'exact completed ordinary positive required')
        with p.validation_readback_session():
            checked=p.check_result(paths['route']);checked_export=ex.check_export(paths['export'])
        require(checked.get('current')is True and checked.get('applied')is False
            and checked_export.get('current')is True and checked_export.get('export_accepted')is True
            and checked_export.get('applied')is False and exported.get('export_accepted')is True
            and exported.get('original_geometry_and_routing_unchanged')is True, 'ordinary current route/export required')
        require(prior.get('source')==str(source) and prior.get('source_hashes')==hashes and pc.inventory(source.parent)==hashes
            and prior.get('scope')==scope and prior.get('accepted')is True and prior.get('status')=='routing_accepted'
            and prior.get('engine_profile')=='standard' and prior.get('adapter')=='both'
            and prior.get('scoring_variant')is None and prior.get('budget_seconds')==prior.get('cpu_budget_seconds')==seconds
            and prior.get('baseline')==p.engine_baseline('standard','both') and prior.get('tools')==tools
            and prior.get('metrics',{}).get('copper_layers')==layers
            and all(row.get('schematic_parity')=='checked by final native DRC' for row in (prior,exported))
            and all([row['native'][key] for key in ('opens','blocking','warnings','exclusions')]==counts for row in (prior,exported)),
            'positive ordinary scope/profile/Native/fullSCH proof differs')
        positives[label]=dict(item=item,paths=paths,output=output,workspace=workspace,source=source,hashes=hashes,
            prior=prior,exported=exported,material=pc.inventory(output,max_bytes=256*1024**2,max_files=8000,max_entries=16000))
    positive('whole4Cu','whole_board_unlocked_routing',120,10,[0,0,6,0],4)
    positive('partial2Cu','partial_completion',90,4,[0,0,0,0],2)
    partial=positives['partial2Cu'];source=real(plan['source']);source_hashes=plan['source_hashes']
    require(source==partial['source'] and source_hashes==partial['hashes'] and pc.inventory(source.parent)==source_hashes,
            'separately declared unchanged external partial source required')
    require(p.check_schematic_class_support(source,class_context=None)is None,'only unflagged partial schematic supported')
    original=p.preflight(source,task_scope='partial_completion',class_context=None)
    protected=p.routes(original)
    require(len(protected)==4 and any(route[0]=='segment' and p.locked(route) for route in protected),
            'all four original partial routes including locked segment must be protected')
    prior=partial['prior'];candidate=real(prior['candidate'])
    require(candidate==partial['workspace']/'route/candidate'/source.name and p.sha(candidate)==prior['candidate_sha256'],
            'positive partial candidate identity differs')
    p.verify_candidate_files(candidate,source_hashes,prior['candidate_sha256'])
    out=real(plan['output'],existing=False)
    require(out==runtime/'.runs/native7-comparison-control-runtime035-invalid-001' and not out.exists()
            and out.parent.is_dir(),'fresh exact ordinary invalid-control output required')
    out.mkdir(mode=0o700);owner={};h.capture_destination(owner,out)
    (out/'protocol.json').write_bytes(raw_protocol)
    cases=[];stages=[]
    report=dict(schema=1,kind=KIND,accepted=False,routing_accepted=False,export_accepted=False,
        production_admitted=False,Native_product_admission=False,control_passed=False,status='failed',
        actual_GUI=False,human_review=False,runtime=str(runtime),runtime_manifest_sha256=MANIFEST,
        source_head=HEAD,tools=tools,helper_sha256=plan['helper_sha256'],protocol_sha256=protocol_sha256,
        source=str(source),source_hashes=source_hashes,scope='partial_completion',profile='standard',adapter='both',
        scoring_variant=None,route_seconds=90,protected_routes=4,cases=cases,whole_wall_full_cpu_budget_seconds=180,
        prerequisites={label:item['item'] for label,item in positives.items()},
        claims_limit='Two owned-copy invalid controls only; shared actual Native and invariant rejection. No engine, accepted route/export, GUI, physical or routing-quality claim.')
    def remaining():return min(178-(time.monotonic()-START),178-(cpu()-CPU0))
    def stable():
        require(h.owned_destination(owner)==out and p.sha(self_path)==plan['helper_sha256']
            and p.sha(protocol_path)==protocol_sha256 and p.sha(out/'protocol.json')==protocol_sha256
            and p.sha(manifest)==MANIFEST and p.tool_manifest()==tools,'controller/protocol/runtime/tools changed')
        for path,pin in pins:require(p.sha(path)==pin,'positive prerequisite pin changed')
        for item in positives.values():
            require(pc.inventory(item['source'].parent)==item['hashes']
                and pc.inventory(item['output'],max_bytes=256*1024**2,max_files=8000,max_entries=16000)==item['material'],
                'positive prerequisite or original source changed')
        for name,module in tuple(sys.modules.items()):
            if name.split('.')[0]=='autorouter' and getattr(module,'__file__',None):
                require(Path(module.__file__).resolve().is_relative_to(runtime),'module outside runtime: '+name)
        require(remaining()>0,'whole wall/full-CPU cap exhausted')

    def new_case(label, seconds):
        stable(); require(remaining() > 20, 'insufficient Native/control publication reserve')
        directory = out / label; directory.mkdir()
        row = dict(label=label, control_observed=False, routing_accepted=False, accepted=False,
                   production_admitted=False, source=str(source), source_hashes=source_hashes,
                   protected_routes=4, before_candidate_sha256=prior['candidate_sha256'])
        cases.append(row)
        job = p.Job(directory / 'validation', min(seconds, remaining() - 10), protect_local_settings=True)
        row['steps'] = job.steps
        copied = job.out / 'candidate' / source.name
        shutil.copytree(candidate.parent, copied.parent)
        (directory / 'before-candidate.kicad_pcb').write_bytes(pc.read_bytes(copied))
        return directory, row, job, copied

    def check_native(job, name, board, before, native, *, saved=False):
        target = job.out / 'refill' / board.name if saved else job.out / (name + '-input') / board.name
        require(f.check_drc_stage(job.out, {'steps': job.steps}, name, board, target, saved, before,
                    schematic_parity=not saved, sandboxed=False) == native, 'own Native stage proof differs')
        stages.append((job, name, board, target, saved, before, native))

    def partial_short():
        directory, row, job, copied = new_case('partial-short', 100)
        bad = sx.read(copied)
        from autorouter import board_floor as g
        _, resolve = g.source_net_identity(bad)
        require(any(resolve(sx.one(pad, 'net')) == 'ROUTE' for fp in sx.children(bad, 'footprint')
                    for pad in sx.children(fp, 'pad')), 'bound ROUTE terminal required')
        segment = ['segment', ['start', '12', '10'], ['end', '12', '16'], ['width', '0.4'],
                   ['layer', '"F.Cu"'], ['net', '"ROUTE"'], ['uuid', json.dumps(str(uuid.uuid4()))]]
        segment = p.convert_route_nets(segment, ['kicad_pcb'], bad)
        require(resolve(sx.one(segment, 'net')) == 'ROUTE', 'short mutation changed net identity')
        bad.append(segment); sx.write(copied, bad)
        require(p.immutable(bad) == p.immutable(original) and all(route in p.routes(bad) for route in protected),
                'short control must preserve design and all four protected records')
        row['mutation'] = dict(added_segment=segment, pre_native_sha256=p.sha(copied))
        (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        final_hash, native = p.validate_candidate(job, original, copied, source_hashes, protected,
                                                  schematic_parity=True, class_context=None)
        row.update(native=native, candidate=str(copied), candidate_sha256=final_hash,
                   native_report_sha256=p.sha(job.out / 'final-drc.json'))
        require(not p.native_accepted(native) and native['blocking'] > 0
                and 'shorting_items' in {finding['type'] for finding in native['findings']},
                'actual original-rule Native short finding required')
        before = dict(source_hashes); before[copied.name] = final_hash
        check_native(job, 'final-drc', copied, before, native)
        refill_before = dict(source_hashes); refill_before[copied.name] = row['mutation']['pre_native_sha256']
        refill_native = p.parse_report(job.out / 'refill-drc.json', copied.name)
        check_native(job, 'refill-drc', job.out / 'refill' / copied.name, refill_before, refill_native, saved=True)
        require(all(route in p.routes(sx.read(copied)) for route in protected), 'protected source copper changed')
        (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        row.update(control_observed=True, rejection='actual original-rule full-schematic Native short')

    def protected_width():
        directory, row, job, copied = new_case('partial-protected-width', 60)
        chosen = next(route for route in protected if route[0]=='segment' and p.locked(route)); bad = sx.read(copied)
        changed = next(route for route in p.routes(bad) if route == chosen)
        width = sx.one(changed, 'width'); old = width[1]; value = Decimal(old)
        require(value.is_finite() and value > 0, 'positive exact protected width required')
        width[1] = format(value + Decimal('0.000001'), 'f'); sx.write(copied, bad)
        restored = sx.read(copied)
        restored_route = next(route for route in p.routes(restored) if sx.one(route, 'uuid') == sx.one(chosen, 'uuid'))
        sx.one(restored_route, 'width')[1] = old
        require(restored == sx.read(candidate) and p.immutable(bad) == p.immutable(original),
                'width control must change exactly one protected width atom')
        invalid_pin = p.sha(copied)
        row['mutation'] = dict(uuid=sx.one(chosen, 'uuid')[1], before_mm=old, after_mm=width[1],
                               added_nanometres=1, pre_native_sha256=invalid_pin)
        (directory / 'invalid-before-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        native = job.drc('diagnostic-full-drc', copied, schematic_parity=True)
        row.update(native=native, candidate=str(copied), candidate_sha256=invalid_pin,
                   native_report_sha256=p.sha(job.out / 'diagnostic-full-drc.json'))
        before = dict(source_hashes); before[copied.name] = invalid_pin
        check_native(job, 'diagnostic-full-drc', copied, before, native)
        steps_before = len(job.steps)
        try:
            p.validate_candidate(job, original, copied, source_hashes, protected,
                                 schematic_parity=True, class_context=None)
        except p.Rejected as exc:
            require(str(exc) == 'protected route changed', 'unexpected protected-control refusal: ' + str(exc))
            row['rejection'] = str(exc)
        else: raise p.Rejected('protected-width mismatch was admitted')
        require(len(job.steps) == steps_before and p.sha(copied) == invalid_pin,
                'protected refusal must precede further Native normalization')
        (directory / 'after-native.kicad_pcb').write_bytes(pc.read_bytes(copied))
        row.update(Native_diagnostic_routing_accepted=p.native_accepted(native),
                   no_additional_native_after_invariant_refusal=True)
        require(p.native_accepted(native)
                and [native[key] for key in ('opens','blocking','warnings','exclusions')]==[0,0,0,0],
                'protected-width control requires separately clean actual Native diagnostic')
        row['control_observed']=True

    try:
        for operation in (partial_short, protected_width):
            started, cpu0, count = time.monotonic(), cpu(), len(cases)
            try: operation()
            finally:
                if len(cases) > count:
                    cases[-1].update(wall_seconds=time.monotonic()-started, full_CPU_seconds=cpu()-cpu0)
            stable()
        require(len(cases) == 2 and all(row['control_observed'] is True for row in cases), 'both own controls required')
        report.update(control_passed=True, status='completed')
    except (Exception, KeyboardInterrupt) as exc:
        report.update(control_passed=False, status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=type(exc).__name__ + ': ' + str(exc))
    report['evidence_sha256'] = f.evidence_inventory(out)

    def final_check():
        stable()
        require(f.evidence_inventory(out)==report['evidence_sha256'],'completed invalid evidence changed')
        packets=[];pairs=[]
        for item in positives.values():
            with p.validation_readback_session():
                require(p.check_result(item['paths']['route']).get('current')is True
                    and ex.check_export(item['paths']['export']).get('current')is True,'ordinary positive prerequisite stale')
            packets.extend([(item['paths']['route'].parent,f.read_json(item['paths']['route'])),
                            (item['workspace']/'export/validation',f.read_json(item['paths']['export']))])
            preview=f.read_json(item['workspace']/'review/review.json')['preview']
            plot_root=item['workspace']/'review/plot-work'
            for step in preview['steps']:
                require(step.get('cwd')==str(plot_root),'positive plot worker escaped retained review')
                process=f.process_check(plot_root,preview,step['name'],step['argv'])
                pairs.append((plot_root,f.read_json(plot_root/(step['name']+'-input-binding.json')),process))
        seen=set()
        for job,name,board,target,saved,before,native in stages:
            require(f.check_drc_stage(job.out,{'steps':job.steps},name,board,target,saved,before,
                schematic_parity=not saved,sandboxed=False)==native,'final own Native stage changed')
            if job.out not in seen:
                packets.append((job.out,{'steps':job.steps,'native':native}));seen.add(job.out)
        stable()
        require(f.evidence_inventory(out)==report['evidence_sha256'],'invalid evidence changed during final readback')
        # All source/tool/complete-material and per-stage readers precede the
        # shared cross-root field/PRL metadata replay. No later tool callback.
        local.check_final_events(packets,c.CLI,pairs=pairs)

    def account():
        report.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_CPU_seconds=cpu()-CPU0,
                      publication_allowance_seconds=2, external_exit_required=True)
        if remaining() <= 0: report.update(control_passed=False, status='budget_exceeded')
        if report['status'] != 'completed': report['control_passed'] = False

    f.publish(out, report, stable, account, remaining, owned=lambda: h.owned_destination(owner), final_check=final_check)
    print(json.dumps({key: report.get(key) for key in ('control_passed', 'status', 'error', 'reason',
                                                       'sampled_wall_seconds', 'sampled_full_CPU_seconds')}))
    return 0 if report['control_passed'] and report['status'] == 'completed' else 2


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    args = parser.parse_args()
    def interrupted(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    raise SystemExit(execute(args.protocol, args.protocol_sha256))
