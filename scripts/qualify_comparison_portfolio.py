#!/usr/bin/env python3
"""One frozen installed7/v2 portfolio control, never ordinary admission.

Execute this committed external file with the runtime interpreter, --runtime,
--protocol and --protocol-sha256. The plan pins this controller, portfolio and
quality administration sources, their separate HEAD, and the installed source,
manifest, tools, complete source inventory and fresh reserved output. Required
budget fields are LIMITS below; variants are the existing three fixed scores.
The portfolio output is the control output's '-portfolio' sibling. Its direct
variant parents and the winner's route/review/choice/export siblings remain in
place; no selected Route is copied. A shared no-network enclosing worker must
enforce one heavy lane and count startup through complete exit within600s wall
and full waited CPU. This child's stored samples alone cannot prove that cap.
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
import signal
import sys
import json

KIND = 'installed-native7-comparison-portfolio-functional-v1'
REVIEW60_KIND = 'installed-native7-comparison-portfolio-functional-v2-review60'
VARIANTS = ('via_default', 'via_low', 'via_high')
LIMITS = dict(routing_seconds=420, method_wall_cpu_cap_seconds=450,
    delivery_wall_cpu_cap_seconds=600, export_validation_seconds=120,
    allocation='balanced', trial_readback_reserve_seconds=30,
    root_finalization_reserve_seconds=15)


def require_completed_portfolio(result):
    """A failed method is not a qualified all-negative routing outcome."""
    status = result.get('status')
    if status == 'cancelled': raise KeyboardInterrupt('portfolio cancelled')
    if status not in ('completed', 'no_valid_candidate'):
        raise ValueError('portfolio ' + str(status) + ': wall=' + str(result.get('wall_seconds'))
            + 's CPU=' + str(result.get('total_cpu_seconds')) + 's; caps wall='
            + str(result.get('wall_budget_seconds')) + 's CPU=' + str(result.get('cpu_budget_seconds'))
            + 's; reason=' + str(result.get('reason')))



def delivery_stage_contract(plan, handoff):
    """Freeze review60/choice30 inside the same600s complete portfolio cap."""
    stages=plan.get('delivery_stage_seconds')
    if plan.get('kind') == REVIEW60_KIND:
        if (plan.get('handoff_stage_policy') != 'bounded-review60-choice30-v2'
                or type(stages) is not dict or stages != dict(review=60,choice=30)
                or any(type(value) is not int for value in stages.values())
                or getattr(handoff,'STAGE_POLICY',None) != 'bounded-review60-choice30-v2'
                or type(getattr(handoff,'REVIEW_SECONDS',None)) is not int or handoff.REVIEW_SECONDS != 60
                or type(getattr(handoff,'CHOICE_SECONDS',None)) is not int or handoff.CHOICE_SECONDS != 30):
            raise ValueError('exact prospective portfolio review60/choice30 stage contract required')
        return dict(stages)
    if (plan.get('kind') != KIND or 'handoff_stage_policy' in plan or 'delivery_stage_seconds' in plan
            or getattr(handoff,'STAGE_POLICY',None) is not None or handoff.SECONDS != 30):
        raise ValueError('historical portfolio cannot run a revised delivery stage policy')
    return dict(review=30,choice=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-sha256', required=True)
    args = parser.parse_args()
    runtime = args.runtime
    sys.path.insert(0, str(runtime)); sys.dont_write_bytecode = True
    # Import product modules BEFORE adding the external administration checkout.
    from autorouter import config as c, pipeline as p, floor_route as f, handoff as h
    from autorouter import comparison as cmp, review_export as ex, review_view as view
    from autorouter import provenance as pv, placement_clearance as pc, local_settings as local

    def require(condition, message):
        if not condition: raise p.Rejected(message)

    runtime = h.real_path(runtime)
    require(c.ROOT == runtime and c.NATIVE_VERSION == '10.0.7'
        and Path(sys.executable) == runtime/'.venv/bin/python'
        and Path(sys.prefix).resolve() == runtime/'.venv' and sys.prefix != sys.base_prefix,
        'exact curated selected7 interpreter/product modules required')
    self_path = h.real_path(__file__); administration = self_path.parents[1]
    require(self_path == administration/'scripts/qualify_comparison_portfolio.py',
            'execute the actual tracked external administration controller')
    sys.path.insert(1, str(administration))
    from scripts import experiment_portfolio as portfolio
    require(Path(portfolio.__file__).resolve() == administration/'scripts/experiment_portfolio.py',
            'portfolio imported outside exact administration checkout')
    protocol = h.real_path(args.protocol)
    require(pv.file_digest(protocol)[0] == args.protocol_sha256, 'frozen protocol hash differs')
    plan = f.read_json(protocol)
    require(type(plan) is dict and type(plan.get('schema')) is int and plan['schema'] == 1
        and plan.get('kind') in (KIND,REVIEW60_KIND) and plan.get('runtime') == str(runtime)
        and plan.get('controller') == str(self_path) and plan.get('administration_root') == str(administration)
        and all(plan.get(name) == value for name, value in LIMITS.items())
        and portfolio.VARIANTS == VARIANTS and plan.get('variants') == list(VARIANTS)
        and portfolio.INSTALLED_TRIAL_READBACK_RESERVE == 30 and portfolio.FINAL_RESERVE == 15
        and plan.get('installed_trial_accounting_policy') == portfolio.INSTALLED_TRIAL_RESERVE_POLICY
        and plan.get('comparison_api_policy') == portfolio.COMPARISON_API_POLICY
        and plan.get('whole_wall_full_cpu_seconds') == 600 and plan.get('pass_key') == 'controls_passed',
        'exact frozen v2 three-score420/450/600/export120 control required')
    stage_seconds = delivery_stage_contract(plan,h)
    admin_files = plan['administration_files_sha256']
    require(set(admin_files) == {'scripts/qualify_comparison_portfolio.py',
        'scripts/experiment_portfolio.py', 'scripts/experiment_quality.py'}
        and p.sha(self_path) == plan['controller_sha256'] == admin_files['scripts/qualify_comparison_portfolio.py'],
        'exact committed controller/portfolio/quality pins required')
    require(cmp.POLICY == 'selected-native7-fixed-comparison-v2'
        and p.sha(runtime/pv.MANIFEST) == plan['runtime_manifest_sha256']
        and p.tool_manifest() == plan['tools']
        and plan['tools']['git_head'] == plan['source_head']
        and plan['tools']['source_provenance']['manifest_sha256'] == plan['runtime_manifest_sha256'],
        'frozen installed source/runtime/tools differ')
    final_events = getattr(local, 'check_final_events', None)
    require(callable(final_events), 'reviewed shared cross-root final-event guard required before Native')
    board = h.real_path(plan['source']); out = h.real_path(plan['output'], existing=False)
    portfolio_out = out.with_name(out.name+'-portfolio')
    require(out.parent == runtime/'.runs' and out.name.startswith(cmp.PREFIX)
        and plan.get('portfolio_output') == str(portfolio_out), 'exact reserved direct sibling outputs required')
    context = portfolio.InstalledContext(runtime, board, plan['family'], plan['tools'], plan['source_hashes'],
        administration, plan['administration_head'], admin_files, self_path,
        comparison_policy=portfolio.COMPARISON_API_POLICY, comparison_output=portfolio_out)
    frozen = context.freeze()
    trial_roots = [portfolio._comparison_trial(frozen, name).parent for name in portfolio.VARIANTS]
    require(not any(path.exists() for path in (out, portfolio_out, *trial_roots)), 'fresh owned outputs required')
    out.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, out)
    registry = {}; live = {}; result = None; winner = None; exported = None; material = None
    record = dict(schema=1, kind=plan['kind'], accepted=False, production_admitted=False,
        handoff_stage_policy=getattr(h,'STAGE_POLICY',None),delivery_stage_seconds=stage_seconds,
        project_complete=False, actual_GUI=False, human_review=False, controls_passed=False,
        workflow_delivered=False, status='failed', protocol_sha256=args.protocol_sha256,
        controller_sha256=plan['controller_sha256'], runtime=str(runtime), source=str(board),
        source_hashes=plan['source_hashes'], tools=plan['tools'], portfolio_directory=str(portfolio_out),
        external_complete_exit_required=True,
        scope='One exposed-development fixed three-score API portfolio plus winner delivery, or qualified completed Native negatives. No routing superiority, vanilla B0, default/GUI, human or physical claim.')

    def left():
        return min(585-(time.monotonic()-START), 585-(cpu()-CPU0))

    def fresh():
        h.owned_destination(owner); context.check()
        require(pv.file_digest(protocol)[0] == args.protocol_sha256 and p.sha(self_path) == plan['controller_sha256']
            and p.sha(runtime/pv.MANIFEST) == plan['runtime_manifest_sha256'], 'controller/protocol/runtime changed')

    def roots_material():
        return {str(path): f.evidence_inventory(path) for path in (portfolio_out, *trial_roots) if path.is_dir()}

    def bytes_current():
        # No Context/tool callback: these byte witnesses precede final metadata.
        require(pv.file_digest(protocol)[0] == args.protocol_sha256 and pc.inventory(board.parent) == plan['source_hashes'],
                'final protocol/source changed')
        for name, digest in admin_files.items():
            require(pv.file_digest(administration/name)[0] == digest, 'final administration changed')
        for name, digest in frozen['files_sha256'].items():
            require(pv.file_digest(runtime/name)[0] == digest, 'final runtime source changed')
        for name, digest in plan['tools']['files'].items():
            require(p.sha(Path(name)) == digest, 'final tool bytes changed')
        if material is not None: require(roots_material() == material, 'complete portfolio/delivery material changed')

    def refusal(reader, path):
        try: reader(path)
        except p.Rejected as exc:
            require('explicit caller context' in str(exc), 'default reader refused for an unrelated reason')
        else: raise p.Rejected('ordinary consumer admitted comparison evidence')

    def replay():
        require(result is not None and f.canonical(f.read_json(portfolio_out/'portfolio-summary.json')) == f.canonical(result)
            and p.sha(portfolio_out/'portfolio-summary.json') == record['portfolio_summary_sha256'],
            'portfolio index changed')
        protocol_data = f.read_json(portfolio_out/'protocol.json')
        require(protocol_data['freeze'] == frozen and protocol_data['variants'] == list(portfolio.VARIANTS),
                'portfolio frozen caller contract changed')
        rows = result['trials']
        require([row['id'] for row in rows] == list(portfolio.VARIANTS) and result['all_variants_attempted'] is True,
                'three-score functional qualification did not complete all variants')
        for row in rows:
            authority = live.get(row['id'])
            require(authority is not None and registry.get(row['id']) is authority, 'live caller Context changed')
            if row.get('eligible') is True:
                require(row.get('accepted_in_trial_receipt') is True, 'eligible trial is not accepted')
                portfolio.verify_row(row, board, frozen, comparison_context=authority)
            else:
                require(row.get('validated_rejection') is True, 'loser lacks completed Native rejection')
                portfolio.verify_negative_row(row, board, frozen, comparison_context=authority)
            refusal(p.check_result, Path(row['result']))
        valid = [row for row in rows if row.get('eligible') is True]
        require(result['pareto_frontier'] == portfolio.frontier(rows), 'portfolio frontier changed')
        if valid:
            chosen = min(valid, key=portfolio.rank)
            require(result['status'] == 'completed' and result['comparison_eligible'] is True
                and all(result['selected'][key] == chosen[key] for key in
                    ('id','result','result_sha256','candidate','candidate_sha256','native_report_sha256','vias','length_mm')),
                'portfolio winner differs from shared rank')
        else:
            require(result['status'] == 'no_valid_candidate' and result['comparison_eligible'] is False
                and result['selected'] is None and not any((root/'export').exists() for root in trial_roots),
                'negative-only portfolio claims routing/delivery acceptance')

    def terminal():
        fresh()
        if not record['controls_passed']: return
        replay(); pairs = (); packets = [(authority.output, f.read_json(authority.output/'result.json'))
                                        for authority in live.values()]
        if winner is not None:
            checked = ex.check_export(exported, comparison_context=winner)
            require(checked['current'] is True and checked['export_accepted'] is True, 'winner export stale')
            review_path = winner.output.parent/'review/review.json'
            pairs = view.check_experimental_preview(review_path.parent,
                f.read_json(review_path).get('preview'), None, False, comparison_context=winner)
            packets.append((exported.parent/'validation', f.read_json(exported)))
        fresh(); bytes_current()
        # All later-root census/process reads precede every final PRL event.
        final_events(packets, c.CLI, pairs=pairs)

    def interrupted(*_): raise KeyboardInterrupt
    previous = {sig: signal.signal(sig, interrupted)
                for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        try:
            fresh()
            result = portfolio.experiment(portfolio_out, budget=420, outer_ceiling=450, allocation='balanced',
                installed_context=context, installed_trial_policy=portfolio.INSTALLED_TRIAL_RESERVE_POLICY,
                comparison_contexts=registry)
            live = dict(registry)
            record.update(portfolio_summary_sha256=p.sha(portfolio_out/'portfolio-summary.json'),
                portfolio_status=result['status'], attempted_variants=result.get('attempted_variants'),
                unattempted_variants=result.get('unattempted_variants'), portfolio_reason=result.get('reason'),
                portfolio_wall_seconds=result.get('wall_seconds'), portfolio_full_CPU_seconds=result.get('total_cpu_seconds'),
                portfolio_wall_budget_seconds=result.get('wall_budget_seconds'), portfolio_CPU_budget_seconds=result.get('cpu_budget_seconds'))
            require_completed_portfolio(result)
            replay()
            record.update(method_wall_seconds=time.monotonic()-START, method_full_CPU_seconds=cpu()-CPU0)
            require(max(record['method_wall_seconds'], record['method_full_CPU_seconds']) <= 450, 'whole method cap exceeded')
            if result['selected'] is not None:
                winner = live[result['selected']['id']]; receipt = winner.output/'result.json'
                for seconds, operation in ((stage_seconds['review'], lambda: h.review_copy(receipt, winner.output.parent/'review', render=True, comparison_context=winner)),
                    (stage_seconds['choice'], lambda: h.review_choice(winner.output.parent/'review/review.json', winner.output.parent/'choice', 'accept', comparison_context=winner)),
                    (120, lambda: ex.export(winner.output.parent/'choice/choice.json', winner.output.parent/'export', seconds=120, comparison_context=winner))):
                    fresh(); require(left() >= seconds, 'complete next delivery stage plus reserve does not fit'); operation()
                exported = winner.output.parent/'export/export.json'
                checked = ex.check_export(exported, comparison_context=winner)
                require(checked['current'] is True and checked['export_accepted'] is True, 'fresh winner export refused')
                export_data = f.read_json(exported)
                require(export_data.get('original_geometry_and_routing_unchanged') is True,
                        'fresh original-design export proof refused')
                refusal(ex.check_export, exported)
                record.update(workflow_delivered=True, selected_route_receipt=str(receipt),
                    selected_route_sha256=p.sha(receipt), export_receipt=str(exported), export_sha256=p.sha(exported),
                    native=export_data['native'], metrics=export_data['metrics'],
                    original_geometry_and_routing_unchanged=True)
            record.update(controls_passed=True, status='completed',
                outcome='validated_winner_delivery' if winner is not None else 'validated_no_valid_candidate')
        except (Exception, KeyboardInterrupt) as exc:
            if 'method_wall_seconds' not in record:
                record.update(method_wall_seconds=time.monotonic()-START, method_full_CPU_seconds=cpu()-CPU0)
            record.update(controls_passed=False, workflow_delivered=False,
                status=('cancelled' if isinstance(exc, KeyboardInterrupt) else
                    record['portfolio_status'] if record.get('portfolio_status') in ('budget_exceeded', 'invalidated') else 'failed'),
                reason=type(exc).__name__+': '+str(exc))
        material = roots_material(); record['completed_evidence'] = material
        def account():
            record.update(sampled_wall_seconds=time.monotonic()-START, sampled_full_CPU_seconds=cpu()-CPU0)
            if left() <= 0: record.update(status='budget_exceeded', controls_passed=False)
            if record['status'] != 'completed':
                record.update(controls_passed=False, workflow_delivered=False,
                    outcome='cancelled' if record['status'] == 'cancelled' else 'unqualified_failure')
        f.publish(out, record, fresh, account, left, owned=lambda: h.owned_destination(owner), final_check=terminal)
        print(json.dumps({key: record.get(key) for key in ('controls_passed','workflow_delivered','status','outcome','reason','sampled_wall_seconds','sampled_full_CPU_seconds')}))
        return 0 if record['controls_passed'] and record['status'] == 'completed' else 2
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)


if __name__ == '__main__':
    raise SystemExit(main())
