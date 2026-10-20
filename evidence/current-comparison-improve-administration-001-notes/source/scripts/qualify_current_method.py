#!/usr/bin/env python3
"""One frozen single-method member of an installed7/v2 comparison.

Adapted from the preserved qualify-native7-current-method-001.py draft. This
administration source is not shipped runtime. Copy its exact committed payload
to the chosen runtime/.runs and freeze both copies and all prerequisites before
execution. Cdefault uses the real Request/Workflow/CliJob without a graphical
window; Cthermal uses actual CLI processes. Comparison arms use caller Context
and library delivery because the ordinary CLI deliberately refuses that scope.
The external shared-lock/no-network enclosure must allow the exact frozen arm
namespace and charge complete exit within600s wall and full waited CPU. The
child's stored samples cannot establish that external cap. Portfolio is run by
its separate committed controller, never implemented or invoked here.

Plan: schema1/kind/arm/population/outputs/output/runtime/source/source_hashes/
source_inventory_sha256/source_rights{family,license,provenance}/source_rights_sha256,
tools/source_head/runtime_manifest_sha256/controller/controller_sha256,
administration_root/qualifier_sha256/prerequisite_sha256/default_settings/limits,
whole_wall_full_cpu_seconds600/pass_key controls_passed. The population is the
six names below; this driver accepts only the five non-portfolio arms. Every
arm sees the same full native project and original constraints. Freeze all
arms and costs before use; no outcome-driven board/settings/arm selection.
"""
import time
import resource

START = time.monotonic()


def cpu():
    return sum(x.ru_utime + x.ru_stime for x in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))


CPU0 = cpu()
from pathlib import Path
import argparse
import hashlib
import inspect
import json
import signal
import sys

KIND = 'installed-native7-current-method-v1'
POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cthermal')
IMPROVE_KIND = 'installed-native7-current-method-v2'
IMPROVE_POPULATION = ('B0', 'B1', 'B2single_tuned', 'B2_portfolio', 'Cdefault', 'Cimprove')
ARMS = tuple(name for name in POPULATION if name != 'B2_portfolio')
COMPARISON = ('B0', 'B1', 'B2single_tuned')
LIMITS = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
              delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120)


def method_contract(kind):
    if kind == KIND: return POPULATION, 'qualify-current-method-001.py'
    if kind == IMPROVE_KIND: return IMPROVE_POPULATION, 'qualify-current-method-002.py'
    raise ValueError('unknown comparison method contract')


def captured_method_settings(plan, defaults, improve_preset):
    if plan['kind'] == KIND: return defaults
    if plan['kind'] != IMPROVE_KIND: raise ValueError('unknown comparison method contract')
    improved = improve_preset(defaults)
    if plan.get('improve_settings') != improved: raise ValueError('frozen shipped single Improve settings differ')
    return improved if plan['arm'] == 'Cimprove' else defaults


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    args = parser.parse_args()
    runtime = args.runtime
    sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
    from autorouter import config as c, pipeline as p, floor_route as f, handoff as h, gui
    from autorouter import comparison as cmp, review_export as ex, review_view as view
    from autorouter import thermal, provenance as pv, placement_clearance as pc, sexpr as sx
    from autorouter import local_settings as local, preferences as pref, strategy as pruning

    def require(condition, message):
        if not condition: raise p.Rejected(message)

    runtime = h.real_path(runtime)
    require(c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
        and Path(sys.executable) == runtime/'.venv/bin/python'
        and Path(sys.prefix).resolve() == runtime/'.venv' and sys.prefix != sys.base_prefix,
        'exact curated selected7 interpreter/product modules required')
    protocol = h.real_path(args.protocol)
    require(pv.file_digest(protocol)[0] == args.protocol_sha256, 'frozen protocol hash differs')
    plan = f.read_json(protocol); arm = plan.get('arm') if type(plan) is dict else None
    population, child_name = method_contract(plan.get('kind') if type(plan) is dict else None)
    require(type(plan) is dict and type(plan.get('schema')) is int and plan['schema'] == 1
        and arm in population and arm != 'B2_portfolio' and plan.get('population') == list(population)
        and plan.get('limits') == LIMITS and plan.get('runtime') == str(runtime)
        and plan.get('whole_wall_full_cpu_seconds') == 600 and plan.get('pass_key') == 'controls_passed',
        'exact five-method member of the frozen six-arm420/450/600/export120 population required')
    self_path = h.real_path(__file__); self_pin = p.sha(self_path)
    require(self_path.parent == runtime/'.runs' and plan['controller'] == str(self_path)
        and self_path.name == child_name and plan['controller_sha256'] == self_pin, 'exact frozen copied child required')
    administration = h.real_path(plan['administration_root'])
    controller_source = administration/'scripts/qualify_current_method.py'
    require(pv.file_digest(controller_source)[0] == self_pin, 'copied child differs from public administration source')
    qualifier = administration/'scripts/qualify_installed_workflow.py'
    require(pv.file_digest(qualifier)[0] == plan['qualifier_sha256'], 'shared qualifier pin differs')
    sys.path.insert(1, str(administration))
    from scripts import qualify_installed_workflow as shared
    require(Path(shared.__file__).resolve() == qualifier, 'shared qualifier imported outside pinned administration')
    preset = shared.FixedComparisonPreset(420, 450, 600, 'balanced', 450, export_validation_seconds=120)
    tools = p.tool_manifest(); manifest = runtime/pv.MANIFEST
    require(cmp.POLICY == 'selected-native7-fixed-comparison-v2' and callable(getattr(local, 'check_final_events', None))
        and inspect.signature(p.check_rejected_routing_attempt).parameters.get('ordinary_profile') is not None
        and tools == plan['tools'] and tools['git_head'] == plan['source_head']
        and tools['source_provenance']['kind'] == pv.KIND
        and tools['source_provenance']['native_version'] == '10.0.7'
        and tools['source_provenance']['manifest_sha256'] == plan['runtime_manifest_sha256'] == p.sha(manifest),
        'reviewed v2 runtime/source/tools/shared final-event guard required')
    settings = pref.validate(dict(pref.DEFAULTS, seconds=420))
    require(plan.get('default_settings') == settings and all(settings.get(key) == value for key,value in
        dict(profile='standard',adapter='both',guidance='native',layers='source_all',
             scope='whole_board_unlocked_routing',seconds=420,scoring_preference=None).items()),
        'frozen actual corrected-standard420 defaults required')
    default_settings = settings
    settings = captured_method_settings(plan, default_settings, gui.improve_preset)
    source = h.real_path(plan['source']); hashes = plan['source_hashes']; rights = plan['source_rights']
    inventory_pin = hashlib.sha256((json.dumps(hashes, sort_keys=True, separators=(',', ':'))+'\n').encode()).hexdigest()
    require(type(hashes) is dict and 1 <= len(hashes) <= 2000 and source.suffix == '.kicad_pcb'
        and all(source.with_suffix(suffix).name in hashes for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch'))
        and inventory_pin == plan['source_inventory_sha256'] and pc.inventory(source.parent) == hashes,
        'exact frozen complete native source inventory required')
    require(type(rights) is dict and all(type(rights.get(key)) is str and 0 < len(rights[key]) <= 8192
        for key in ('family','license','provenance'))
        and hashlib.sha256(f.canonical(rights).encode()).hexdigest() == plan['source_rights_sha256'],
        'explicit frozen source rights/provenance required; no board selection policy is inferred')
    prerequisites = plan['prerequisite_sha256']
    require(type(prerequisites) is dict and 0 < len(prerequisites) <= 32, 'lead-frozen current qualification prerequisites required')
    outputs = plan['outputs']
    require(type(outputs) is dict and set(outputs) == set(population)
        and len(set(outputs.values())) == len(population) and plan['output'] == outputs[arm],
        'all distinct population outputs must be frozen before use')
    canonical_outputs = set()
    for name, value in outputs.items():
        path = h.real_path(value, existing=False)
        canonical_outputs.add(path)
        require(path.parent == runtime/'.runs' and source.parent not in path.parents,
                'population output escaped runtime or overlaps source')
        require(path.name.startswith(cmp.PREFIX) if name in (*COMPARISON,'B2_portfolio') else
            path.name.startswith('native7-method-') and not cmp.marked(path), 'arm namespace differs from its frozen authority')
    require(len(canonical_outputs) == len(population), 'population outputs alias the same canonical path')
    out = h.real_path(outputs[arm], existing=False)
    require(not out.exists(), 'fresh arm output required')
    out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out); p.check_storage(active_root=out)
    route = out/('thermal-route/result.json' if arm == 'Cthermal' else 'route/result.json')
    delivery_root = out; exported_path = out/'export/export.json'
    ctx = {}; authority = None; complete = None; flow = None
    record = dict(schema=1, kind=plan['kind'], arm=arm, population=list(population), accepted=False,
        production_admitted=False, project_complete=False, actual_GUI=False, human_review=False,
        controls_passed=False, attempt_qualified=False, workflow_delivered=False, status='failed', outcome='not_started',
        protocol_sha256=args.protocol_sha256, controller_sha256=self_pin, limits=LIMITS,
        runtime=str(runtime), runtime_manifest_sha256=plan['runtime_manifest_sha256'], source_head=plan['source_head'],
        source=str(source), source_hashes=hashes, source_rights=rights, tools=tools,
        protected_route_items=sum(p.locked(row) for row in p.routes(sx.read(source))),
        default_settings=default_settings, processes=[],
        transport=('caller Context/direct API plus library delivery' if arm in COMPARISON else
            'actual Request/Workflow/CliJob headless workflow' if arm in ('Cdefault','Cimprove') else 'actual recover/delivery CLI'),
        external_complete_exit_required=True, fair_full_matrix=False,
        scope='One frozen single-method result. B2single_tuned is one tuned attempt; portfolio is separate. Cdefault exercises the shipped workflow and aliases corrected-standard B1. Cthermal is experimental recover, not Improve. API comparison delivery is not ordinary product admission. No holdout, superiority, graphical interaction, human or physical claim.',
        stock_caveat='B0 disables project adapter corrections and must retain identical native/task DSN bytes. Common fixed-placement, alias, protected-copper, netclass and original-rule Native validation safeguards remain; this is not proof of an untouched official vanilla workflow.')
    if plan['kind'] == IMPROVE_KIND:
        record.update(method_settings=settings,
            scope='Frozen v2 installed comparison. Cimprove is shipped single Improve with a charged tuned incumbent and25-second finalization reserve inside420. Cdefault/B1 unchanged; no GUI/human/electrical/superiority claim.')

    def left(): return preset.remaining(time.monotonic()-START, cpu()-CPU0)

    def method_left(): return min(450-(time.monotonic()-START),450-(cpu()-CPU0))

    def fresh():
        h.owned_destination(owner)
        require(left() > 0 and pv.file_digest(protocol)[0] == args.protocol_sha256
            and p.sha(self_path) == self_pin and pv.file_digest(controller_source)[0] == self_pin
            and pv.file_digest(qualifier)[0] == plan['qualifier_sha256']
            and p.sha(manifest) == plan['runtime_manifest_sha256'] and p.tool_manifest() == tools
            and pc.inventory(source.parent) == hashes, 'whole cap or frozen source/controller/tools changed')
        for name, pin in prerequisites.items():
            require(p.sha(h.real_path(name)) == pin, 'qualification prerequisite changed')
        if authority is not None: authority.check()
        if flow is not None:
            flow.fresh()
            require(flow.workspace.parent == out and flow.board == source
                and json.loads(flow.settings_bytes) == settings, 'live workflow source/settings/output changed')
        for path_key, pin_key in (('selected_route_receipt','selected_route_sha256'),('export_receipt','export_sha256')):
            if path_key in record: require(p.sha(h.real_path(record[path_key])) == record[pin_key], 'bound receipt changed')
        for item in record['processes']:
            require(pv.file_digest(Path(item['log']))[0] == item['log_sha256'], 'actual CLI log changed')
            if 'process' in item:
                require(f.read_json(Path(item['journal'])) == item['process']
                    and item['process']['argv'] == item['argv']
                    and p.sha(Path(item['journal'])) == item['journal_sha256'], 'actual CLI process changed')
        if complete is not None: require(f.evidence_inventory(out) == complete, 'complete arm evidence changed')

    def cli(stage, argv, *, workflow=None, choice=None, method=False, allow_negative=False, minimum_seconds=1):
        fresh()
        cap = workflow.timeout(stage) if workflow is not None else 165 if stage=='export' else 450 if method else 90
        allowance = min(left(), method_left() if method else left(), cap)
        require(allowance >= minimum_seconds, 'complete CLI stage/final-publication allocation unavailable')
        job = gui.CliJob(); log = out/(stage+'.log'); process = None
        try:
            process = job.run(argv, log, timeout=allowance)
        finally:
            if log.is_file():
                item = dict(stage=stage,argv=list(argv),log=str(log),log_sha256=pv.file_digest(log)[0])
                journal = log.with_suffix('.process.json')
                if journal.is_file():
                    item.update(journal=str(journal),journal_sha256=p.sha(journal),process=f.read_json(journal))
                record['processes'].append(item)
        require(record['processes'][-1].get('process') == process, 'actual CLI journal missing or differs')
        if process['cancel_requested'] or process['exit_code'] in (130,143,-2,-15):raise KeyboardInterrupt
        require(process['log_truncated'] is False and process['exit_code'] in ((0,2) if allow_negative else (0,)),
                'actual installed CLI refused: '+stage)
        if workflow is not None and process['exit_code']==0:
            job.adopt(workflow,stage,process,log,choice=choice)
        fresh()
        return process

    def negative():
        if authority is not None:return p.check_rejected_routing_attempt(route,comparison_context=authority)
        if arm=='Cdefault':return p.check_rejected_routing_attempt(route,ordinary_profile='standard')
        raise p.Rejected('strategy parent has no qualified completed-negative method contract')

    def stock_identity():
        if arm == 'B0':
            data = f.read_json(route)
            native_hash = p.sha(route.parent/'native.dsn')
            require(native_hash == p.sha(route.parent/'task.dsn')
                == data['native_dsn_sha256'] == data['task_dsn_sha256'], 'stock adapter changed native DSN')
            return native_hash

    def ordinary_refusal(reader, path):
        try: reader(path)
        except p.Rejected as exc: require('explicit caller context' in str(exc), 'ordinary consumer refused for unrelated reason')
        else: raise p.Rejected('ordinary consumer admitted comparison evidence')

    def terminal():
        fresh()
        if not record['attempt_qualified']: return
        if arm == 'B0':
            require(stock_identity() == record['stock_native_dsn_sha256'] == record['stock_task_dsn_sha256'],
                    'bound stock DSN observation changed')
        data = f.read_json(route); pairs = []; packets = [(route.parent, data)]
        if arm == 'Cimprove': packets = pruning.native7_packets(route.parent, data)
        if arm=='Cthermal':
            packets.append((route.parent/'incumbent',f.read_json(route.parent/'incumbent/result.json')))
            for index,trial in enumerate((data.get('repair') or {}).get('trials',[]),1):
                packets.append((route.parent/'recovery'/('trial-%02d'%index),
                    {**data,'steps':trial['steps'],'native':trial.get('native',{})}))
        if record['workflow_delivered']:
            require(ex.check_export(exported_path, **ctx)['current'] is True, 'final export stale')
            review = f.read_json(delivery_root/'review/review.json'); preview = review['preview']
            if authority is not None:
                pairs = view.check_experimental_preview(delivery_root/'review', preview, None, False, comparison_context=authority)
            else:
                # The shared export reader already bound this rendered review.
                # Reuse its actual plot journals/bindings for the final PRL pass.
                plot_root = delivery_root/'review/plot-work'
                for step in preview['steps']:
                    require(step.get('cwd') == str(plot_root), 'plot worker escaped owned review')
                    process = f.process_check(plot_root, preview, step['name'], step['argv'])
                    pairs.append((plot_root, f.read_json(plot_root/(step['name']+'-input-binding.json')), process))
            packets.append((delivery_root/'export/validation', f.read_json(exported_path)))
        else:
            negative()
            require(flow is None or flow.ready=={'preview'} and flow.choice is None,
                    'negative route entered ready workflow state')
        fresh()  # Includes final Context/tool/material callbacks.
        require(record['workflow_delivered'] or method_left()>0, 'method cap exceeded during final negative readback')
        if arm == 'Cimprove':
            require(pruning.check_native7_final(route.parent, data,
                additional=packets[-1:] if record['workflow_delivered'] else (), pairs=pairs) is True,
                'Improve parent/incumbent/trial final metadata refused')
        else: local.check_final_events(packets, c.CLI, pairs=pairs)
        require(record['workflow_delivered'] or method_left()>0, 'method cap exceeded during final negative metadata replay')

    try:
        fresh(); require(left() >= 420, 'complete method allocation unavailable')
        if arm in COMPARISON:
            require(method_left() >= 420, 'complete420 route allocation unavailable inside entry-start method cap')
            profile = 'tuned' if arm == 'B2single_tuned' else 'standard'
            adapter = 'none' if arm == 'B0' else 'both'
            authority = cmp.Context(source, route.parent, profile, 420, tools, hashes, adapter=adapter, scoring_variant=None)
            ctx = dict(comparison_context=authority)
            result = p.route(source, route.parent, seconds=420, keep_existing=False,
                             adapter=adapter, engine_profile=profile, **ctx)
        elif arm in ('Cdefault','Cimprove'):
            flow = gui.Request(str(source),str(out),json.dumps(settings),True,'improve' if arm=='Cimprove' else 'route').prepare()
            delivery_root = flow.workspace; route = delivery_root/'route/result.json'
            exported_path = delivery_root/'export/export.json'
            record['workspace'] = str(flow.workspace)
            cli('preview',flow.command('preview'),workflow=flow,method=True)
            require(method_left() >= 420 and left() >= 420, 'complete420 route allocation unavailable after preview')
            cli_process = cli('route',flow.command('route'),workflow=flow,method=True,allow_negative=True,minimum_seconds=420)
            result = f.read_json(route)
            require((cli_process['exit_code']==0) is (result.get('accepted') is True), 'CLI exit differs from durable route result')
            require(flow.ready==({'preview','route'} if result.get('accepted') is True else {'preview'})
                and flow.choice is None, 'negative route was adopted or actual route state is missing')
            effective = result.get('pruning_preferences' if arm=='Cimprove' else 'routing_preferences',{}).get('effective',{})
            require(effective == settings, 'actual CLI default scope/settings changed')
            record['workflow_ready'] = sorted(flow.ready)
        else:
            require(thermal.parent_profile() == 'standard', 'thermal incumbent profile changed')
            require(method_left() >= 420, 'complete420 recover allocation unavailable inside entry-start method cap')
            cli_argv = [str(runtime/'.venv/bin/python'),'-B','-m','autorouter',
                *preset.timed_cli_arguments('recover',source,route.parent)]
            cli_process = cli('thermal_route',cli_argv,method=True,allow_negative=True,minimum_seconds=420)
            result = f.read_json(route)
            require((cli_process['exit_code'] == 0) is (result.get('accepted') is True), 'CLI exit differs from durable route result')
        if arm not in COMPARISON:
            require(result.get('source') == str(source) and result.get('source_hashes') == hashes
                and result.get('tools') == tools and result.get('scope') == 'whole_board_unlocked_routing'
                and result.get('budget_seconds') == result.get('cpu_budget_seconds') == 420
                and result.get('adapter') == 'both' and result.get('engine_profile') == ('tuned' if arm=='Cimprove' else 'standard'), 'installed CLI differs from frozen method')
        if result.get('status') == 'cancelled' or any(row.get('status') == 'cancelled' for row in result.get('steps',[])):
            raise KeyboardInterrupt
        if arm == 'B0':
            digest = stock_identity()
            record.update(stock_native_dsn_sha256=digest, stock_task_dsn_sha256=digest, stock_dsn_identical=True)
        if result.get('accepted') is True:
            current = p.check_result(route, **ctx)
            require(current.get('current') is True and current.get('applied') is False, 'central positive reader refused')
            record['route_readback'] = current
        else:
            try: diagnostic = negative()
            except p.Rejected as exc:
                record.update(outcome='method_not_delivered', negative_reader_refusal=str(exc))
                raise p.Rejected('no qualified central completed-negative evidence; raw attempt retained') from exc
            require(diagnostic.get('validated_rejection') is True and diagnostic.get('current') is False
                and diagnostic.get('routing_accepted') is False and diagnostic.get('applied') is False,
                'completed-negative reader flags differ')
            record['negative_readback'] = diagnostic
        if authority is not None: ordinary_refusal(p.check_result, route)
        record.update(method_wall_seconds=time.monotonic()-START, method_full_cpu_seconds=cpu()-CPU0)
        require(max(record['method_wall_seconds'],record['method_full_cpu_seconds']) <= 450, 'method wall/fullCPU cap exceeded')
        record.update(selected_route_receipt=str(route), selected_route_sha256=p.sha(route),
            route_native=result.get('native'), route_metrics=result.get('metrics'))
        if result.get('accepted') is not True:
            record.update(status='completed', outcome='validated_completed_negative', controls_passed=True, attempt_qualified=True)
        else:
            if authority is not None:
                fresh(); require(left() >= h.SECONDS, 'review allocation unavailable')
                review = h.review_copy(route, delivery_root/'review', render=True, **ctx)
                fresh(); require(left() >= h.SECONDS, 'choice allocation unavailable')
                choice = h.review_choice(delivery_root/'review/review.json', delivery_root/'choice', 'accept', **ctx)
                fresh(); require(left() >= 120, 'complete120s export allocation unavailable')
                exported = ex.export(delivery_root/'choice/choice.json', delivery_root/'export', seconds=120, **ctx)
            elif flow is not None:
                for stage,seconds in (('review',h.SECONDS),('choice',h.SECONDS),('export',120),('verify_export',1)):
                    fresh();require(left() >= seconds, 'complete next product workflow stage allocation unavailable')
                    intent = 'accept' if stage=='choice' else None
                    cli(stage,flow.command(stage,choice=intent),workflow=flow,choice=intent,minimum_seconds=seconds)
                require(flow.ready=={'preview','route','review','choice','export','verify_export'}, 'actual product workflow incomplete')
                record['workflow_ready'] = sorted(flow.ready)
                review,choice,exported = (flow.records[name] for name in ('review','choice','export'))
            else:
                python = [str(runtime/'.venv/bin/python'),'-B','-m','autorouter']
                commands = [('review',h.SECONDS,['review-copy',str(route),'--render','--output',str(delivery_root/'review')]),
                    ('choice',h.SECONDS,['review-choice',str(delivery_root/'review/review.json'),'--choice','accept','--output',str(delivery_root/'choice')]),
                    ('export',120,preset.timed_cli_arguments('review-export',delivery_root/'choice/choice.json',delivery_root/'export')),
                    ('verify_export',1,['review-export-check',str(exported_path)])]
                for stage,seconds,arguments in commands:
                    fresh();require(left() >= seconds, 'complete next thermal CLI delivery allocation unavailable')
                    cli(stage,python+arguments,minimum_seconds=seconds)
                review,choice,exported = (f.read_json(delivery_root/name/(name+'.json')) for name in ('review','choice','export'))
            checked = ex.check_export(exported_path, **ctx)
            require(checked.get('current') is True and checked.get('applied') is False
                and exported.get('export_accepted') is True and exported.get('original_geometry_and_routing_unchanged') is True
                and exported.get('schematic_parity') == 'checked by final native DRC'
                and choice.get('human_pcb_approval_observed') is False and choice.get('applied') is False,
                'fresh original/fullSCH delivery proof refused')
            if authority is not None:
                ordinary_refusal(ex.check_export, exported_path)
                require(all(row.get('production_admitted') is False for row in
                    (result,current,review,review['preview'],choice,exported,checked)), 'comparison became ordinary admission')
            record.update(status='completed', outcome='validated_delivery', controls_passed=True, attempt_qualified=True,
                workflow_delivered=True, export_receipt=str(exported_path), export_sha256=p.sha(exported_path),
                candidate_sha256=exported['candidate_sha256'], native=exported['native'], metrics=exported['metrics'],
                review_layers=review['preview']['layers'])
    except (Exception,KeyboardInterrupt) as exc:
        if 'method_wall_seconds' not in record:
            record.update(method_wall_seconds=time.monotonic()-START, method_full_cpu_seconds=cpu()-CPU0)
        record.update(status='cancelled' if isinstance(exc,KeyboardInterrupt) else 'failed', controls_passed=False,
            attempt_qualified=False, workflow_delivered=False, reason=type(exc).__name__+': '+str(exc))
    if route.is_file(): record['route_attempt'] = shared.read_attempt(route)
    if arm in ('Cthermal','Cimprove') and (route.parent/'incumbent/result.json').is_file():
        record['incumbent_attempt'] = shared.read_attempt(route.parent/'incumbent/result.json')
    complete = f.evidence_inventory(out); record['completed_evidence'] = complete

    def account():
        if not record['workflow_delivered']:
            record.update(method_wall_seconds=time.monotonic()-START, method_full_cpu_seconds=cpu()-CPU0)
        record.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_cpu_seconds=cpu()-CPU0,
            accounting='Method starts at entry and includes imports/intake, actual preview/CLI startup, routing/selection and initial central readback. Negative final guards also enforce450; their literal stored sample precedes the last replay. Delivery starts from the same entry and additionally counts render/choice/export/readbacks and guarded publication. RUSAGE_SELF plus waited children; nested receipt CPU is not added. External complete-exit accounting and separately recorded preparation remain required.')
        if left() <= 0 or (not record['workflow_delivered'] and method_left() <= 0): record['status'] = 'budget_exceeded'
        if record['status'] != 'completed':
            record.update(controls_passed=False, attempt_qualified=False, workflow_delivered=False,
                outcome='cancelled' if record['status'] == 'cancelled' else
                record['outcome'] if record['outcome'] == 'method_not_delivered' else 'unqualified_failure')
    f.publish(out, record, fresh, account, left, owned=lambda: h.owned_destination(owner), final_check=terminal)
    print(json.dumps({key:record.get(key) for key in ('arm','controls_passed','attempt_qualified',
        'workflow_delivered','status','outcome','reason','method_wall_seconds','method_full_cpu_seconds',
        'sampled_wall_seconds','sampled_full_cpu_seconds')}))
    return 0 if record['status'] == 'completed' and record['controls_passed'] and record['attempt_qualified'] else 2


if __name__ == '__main__':
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,interrupted)
    raise SystemExit(main())
