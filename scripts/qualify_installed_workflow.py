#!/usr/bin/env python3
"""One frozen exposed-development arm through actual installed product APIs.

Run with the curated runtime's Python. The external protocol and administration
source are pinned before execution. Use an enclosing bounded runner for complete
exit accounting; sampled results here cannot establish a complete budget alone.
"""
from pathlib import Path
import argparse
from dataclasses import dataclass
import json
import resource
import signal
import sys
import time

START = time.monotonic()
def cpu():
    return sum(row.ru_utime + row.ru_stime for row in
               (resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0 = cpu()
ORIGINAL_ARMS = ('B0', 'B1', 'B2_portfolio', 'B2_stronger', 'C_single')
THERMAL_ARMS = ('B0', 'B1', 'B2_tuned', 'B2_completion', 'B2_portfolio', 'C_single', 'C_thermal')
RESERVED_KIND = 'installed-workflow-thermal-reserved-comparison-v3'
RESERVED_POLICY = 'installed-route-readback-reserve-v1'


@dataclass(frozen=True)
class FixedComparisonPreset:
    routing_seconds: int
    method_wall_cpu_cap_seconds: int
    delivery_wall_cpu_cap_seconds: int
    allocation: str
    cli_timeout_seconds: int
    installed_trial_accounting_policy: str | None = None

    def remaining(self, elapsed_wall, elapsed_cpu):
        # Preserve the existing15s final-publication/enclosing-exit reserve.
        cap = self.delivery_wall_cpu_cap_seconds - 15
        return min(cap - elapsed_wall, cap - elapsed_cpu)

    def portfolio_options(self):
        options = dict(budget=self.routing_seconds,
            outer_ceiling=self.method_wall_cpu_cap_seconds, allocation=self.allocation)
        if self.installed_trial_accounting_policy is not None:
            options['installed_trial_policy'] = self.installed_trial_accounting_policy
        return options

    def timed_cli_arguments(self, command, source, output):
        if command not in ('recover', 'review-export'):
            raise ValueError('Only existing budgeted recovery/export commands are supported.')
        return [command, str(source), '--seconds', str(self.routing_seconds), '--output', str(output)]


def protocol_arms(plan):
    """Exact exposed-development protocols; never accept a partial matrix."""
    from autorouter import pipeline as p
    kinds = {'installed-workflow-exposed-comparison-v1': ORIGINAL_ARMS,
             'installed-workflow-thermal-comparison-v2': THERMAL_ARMS,
             RESERVED_KIND: THERMAL_ARMS}
    if type(plan) is not dict or type(plan.get('kind')) is not str:
        raise p.Rejected('Frozen installed comparison protocol required.')
    expected = kinds.get(plan['kind'])
    if expected is None or plan.get('arms') != list(expected):
        raise p.Rejected('Frozen installed comparison arm population differs.')
    return expected


def protocol_preset(plan):
    """Choose one complete fixed preset; no custom or mixed budget intake."""
    from autorouter import pipeline as p
    protocol_arms(plan)
    preset = (FixedComparisonPreset(420, 450, 600, 'balanced', 450, RESERVED_POLICY)
              if plan['kind'] == RESERVED_KIND else
              FixedComparisonPreset(105, 120, 240, 'remaining', 165))
    if (type(plan.get('schema')) is not int or plan['schema'] != 1
            or any(plan.get(name) != getattr(preset, name) for name in
                   ('routing_seconds', 'method_wall_cpu_cap_seconds',
                    'delivery_wall_cpu_cap_seconds', 'allocation'))
            or plan.get('installed_trial_accounting_policy') != preset.installed_trial_accounting_policy):
        raise p.Rejected('Unsupported frozen comparison protocol or budgets.')
    return preset


def routing_settings(arm, preset):
    """Keep the existing arm profiles while sharing the validated allowance."""
    from autorouter import gui, preferences as pref
    settings = dict(pref.DEFAULTS, seconds=preset.routing_seconds)
    if arm == 'B0': settings.update(adapter='none', profile='standard')
    elif arm == 'B1': settings.update(adapter='both', profile='standard')
    elif arm in ('B2_portfolio', 'B2_stronger', 'B2_tuned'): settings.update(adapter='both', profile='tuned')
    elif arm in ('B2_completion', 'C_thermal'): settings.update(adapter='both', profile='completion-only')
    elif arm == 'C_single': settings = gui.improve_preset(settings)
    else: raise ValueError('Unknown fixed comparison arm.')
    return settings


def read_attempt(path):
    """Retain bounded corrupt producer diagnostics without bypassing publication."""
    import hashlib
    from autorouter import floor_route as f, placement_clearance as pc
    result = dict(receipt=str(path))
    try:
        raw = pc.read_bytes(path, 32 * 1024**2)
        result['sha256'] = hashlib.sha256(raw).hexdigest()
        data = f.read_json(path)
        if type(data) is not dict or pc.read_bytes(path, 32 * 1024**2) != raw:
            raise ValueError('Partial route receipt malformed or changed.')
        result.update(status=data.get('status'), accepted=data.get('accepted'), reason=data.get('reason'),
            source_drc=data.get('source_drc'), native=data.get('native'),
            native_rejection_reasons=data.get('native_rejection_reasons'), metrics=data.get('metrics'),
            incumbent=data.get('incumbent'), repair=data.get('repair'), recovery_needed=data.get('recovery_needed'))
    except Exception as exc:
        result['read_error'] = type(exc).__name__ + ': ' + str(exc)
    return result


def verify_delivery(report, board, context):
    """Use the existing complete portfolio and positive delivery readers."""
    from autorouter import pipeline as p, review_export as ex
    from scripts import experiment_paired as paired
    route, exported = Path(report['selected_route_receipt']), Path(report['export_receipt'])
    def pins():
        if (p.sha(route) != report['selected_route_sha256'] or p.sha(exported) != report['export_sha256']):
            raise p.Rejected('Final selected route/export receipt hash changed.')
        if report['arm'] == 'B2_portfolio':
            directory = Path(report['portfolio_directory'])
            if p.sha(directory/'portfolio-summary.json') != report['portfolio_summary_sha256']:
                raise p.Rejected('Final portfolio summary hash changed.')
            paired.verify_portfolio(directory, report['portfolio'], board, context.freeze())
    pins()
    route_current = p.check_result(route)
    export_current = ex.check_export(exported)
    pins()
    if route_current['current'] is not True or export_current['current'] is not True:
        raise p.Rejected('Final shared delivery readers refused.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'protocol', 'protocol-sha256', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--arm', choices=tuple(dict.fromkeys((*ORIGINAL_ARMS, *THERMAL_ARMS))), required=True)
    args = parser.parse_args()
    runtime = Path(args.runtime)
    sys.path.insert(0, str(runtime))
    sys.dont_write_bytecode = True
    from autorouter import config as c, pipeline as p, gui, handoff as h, review_export as ex
    from autorouter import floor_route as f, provenance as pv
    administration = Path(__file__).resolve().parents[1]
    sys.path.insert(1, str(administration))
    from scripts import experiment_portfolio as portfolio
    if (c.ROOT != runtime or Path(sys.executable) != runtime / '.venv/bin/python'
            or Path(sys.prefix).resolve() != runtime / '.venv'):
        raise p.Rejected('Use the exact curated runtime interpreter and product modules.')
    protocol_path = Path(args.protocol)
    if p.sha(protocol_path) != args.protocol_sha256:
        raise p.Rejected('Frozen protocol hash differs.')
    plan = f.read_json(protocol_path)
    arms = protocol_arms(plan)
    preset = protocol_preset(plan)
    if args.arm not in arms or plan.get('runtime') != str(runtime):
        raise p.Rejected('Unsupported frozen comparison protocol or budgets.')
    if set(plan.get('administration_files_sha256', {})) != {
            'scripts/qualify_installed_workflow.py', 'scripts/experiment_portfolio.py',
            'scripts/experiment_quality.py', 'scripts/experiment_paired.py'}:
        raise p.Rejected('Complete external controller/portfolio/quality/paired source pins required.')
    board = Path(plan['source'])
    context = portfolio.InstalledContext(runtime, board, plan['family'], plan['tools'], plan['source_hashes'],
        administration, plan['administration_head'], plan['administration_files_sha256'], Path(__file__).resolve())
    context.check()
    out = h.real_path(Path(args.output), existing=False)
    if runtime / '.runs' not in out.parents:
        raise p.Rejected('Use a new output directory inside the installed runtime .runs.')
    out.mkdir(mode=0o700)
    owner = {}; h.capture_destination(owner, out)
    selfpin = p.sha(Path(__file__))
    report = dict(schema=1, accepted=False, status='failed', workflow_delivered=False, actual_GUI=False, human_review=False,
        arm=args.arm, runtime=str(runtime), protocol=str(protocol_path), protocol_sha256=args.protocol_sha256,
        controller_sha256=selfpin, source=str(board), source_hashes=plan['source_hashes'],
        tools=plan['tools'], processes=[], routing_seconds=preset.routing_seconds,
        method_wall_cpu_cap_seconds=preset.method_wall_cpu_cap_seconds,
        delivery_wall_cpu_cap_seconds=preset.delivery_wall_cpu_cap_seconds, external_complete_exit_required=True,
        scope='Actual installed product. Exposed development; software test intent only. B2_portfolio uses the external fixed portfolio; B2_stronger is experimental free-angle/global-width; C_thermal is the existing experimental recovery CLI, not the default or graphical optimizer. All use production review/export CLI, '
            f'equal{preset.routing_seconds} routing allocations/{preset.method_wall_cpu_cap_seconds}method caps/{preset.delivery_wall_cpu_cap_seconds}whole-delivery caps; no pooled best-of, human, physical or superiority claim.')
    if preset.installed_trial_accounting_policy is not None:
        report.update(allocation=preset.allocation,
            installed_trial_accounting_policy=preset.installed_trial_accounting_policy)

    def fresh():
        if (p.sha(protocol_path) != args.protocol_sha256 or p.sha(Path(__file__)) != selfpin
                or h.owned_destination(owner) != out):
            raise p.Rejected('Protocol/controller/destination changed.')
        context.check()

    def left():
        return preset.remaining(time.monotonic() - START, cpu() - CPU0)

    def cli(stage, argv, *, flow=None, choice=None):
        fresh()
        allowance = left()
        if allowance <= 1:
            raise p.Rejected('Delivery/final-publication reserve exhausted.')
        job = gui.CliJob(); log = out / (stage + '.log')
        process = job.run(argv, log, timeout=min(preset.cli_timeout_seconds, allowance))
        report['processes'].append(dict(stage=stage, process=process, log_sha256=p.sha(log)))
        if process.get('cancel_requested') is True or process.get('exit_code') in (130, 143):
            raise KeyboardInterrupt('Installed CLI cancellation is terminal.')
        if flow is not None:
            job.adopt(flow, stage, process, log, choice=choice)
        elif (process.get('exit_code') != 0 or process.get('cancel_requested') is not False
                or process.get('log_truncated') is not False):
            raise p.Rejected('Installed delivery CLI refused or was cancelled: ' + stage)
        fresh()
        return process

    settings = routing_settings(args.arm, preset)
    report['settings'] = settings
    flow = gui.Request(str(board), str(out), json.dumps(settings), True,
        'improve' if args.arm == 'C_single' else 'route').prepare()
    report['workspace'] = str(flow.workspace)
    method_start = method_cpu = None
    try:
        cli('preview', flow.command('preview'), flow=flow)
        method_start, method_cpu = time.monotonic(), cpu()
        if args.arm == 'B2_portfolio':
            result = portfolio.experiment(out / 'portfolio', installed_context=context,
                **preset.portfolio_options())
            report.update(portfolio=result, portfolio_directory=str(out / 'portfolio'),
                portfolio_summary_sha256=p.sha(out / 'portfolio/portfolio-summary.json'))
            if result.get('comparison_eligible') is not True or result.get('selected') is None:
                raise p.Rejected('Fixed installed portfolio returned no eligible candidate: ' + str(result.get('status')))
            receipt = Path(result['selected']['result'])
            p.check_result(receipt)
        elif args.arm == 'C_thermal':
            receipt = out / 'thermal-route/result.json'
            cli('thermal_route', [str(runtime / '.venv/bin/python'), '-B', '-m', 'autorouter',
                *preset.timed_cli_arguments('recover', board, receipt.parent)])
            p.check_result(receipt)
        elif args.arm == 'B2_stronger':
            # Predeclared stronger comparator, using the installed experimental
            # API. This is not an ordinary GUI/CLI option or pooled best-of run.
            report['experimental_baseline_settings'] = dict(profile='tuned-free-angle',
                fanout=False, optimizer=False, clearance_margin_nm=20000,
                global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY, scoring_variant='via_default')
            result = p.route(board, out / 'stronger-route', preset.routing_seconds, False, 'both', 'tuned-free-angle',
                scoring_variant='via_default', _fanout_enabled=False, _optimizer_enabled=False,
                _engine_clearance_margin_nm=20000, _engine_global_width_policy=p.ENGINE_GLOBAL_WIDTH_POLICY)
            if result.get('accepted') is not True:
                raise p.Rejected('Stronger experimental baseline refused: ' + str(result.get('status')))
            receipt = out / 'stronger-route/result.json'
            p.check_result(receipt)
        else:
            cli('route', flow.command('route'), flow=flow)
            receipt = flow.workspace / 'route/result.json'
        report.update(method_wall_seconds=time.monotonic() - method_start, method_full_cpu_seconds=cpu() - method_cpu,
                      selected_route_receipt=str(receipt), selected_route_sha256=p.sha(receipt))
        if max(report['method_wall_seconds'], report['method_full_cpu_seconds']) > preset.method_wall_cpu_cap_seconds:
            raise p.Rejected('Complete routing/selection/readback exceeded method cap.')
        if args.arm in ('B2_portfolio', 'B2_stronger', 'C_thermal'):
            python = [str(runtime / '.venv/bin/python'), '-B', '-m', 'autorouter']
            commands = [('review', ['review-copy', str(receipt), '--render', '--output', str(out / 'review')]),
                ('choice', ['review-choice', str(out / 'review/review.json'), '--choice', 'accept', '--output', str(out / 'choice')]),
                ('export', preset.timed_cli_arguments('review-export', out / 'choice/choice.json', out / 'export')),
                ('verify_export', ['review-export-check', str(out / 'export/export.json')])]
            for stage, arguments in commands: cli(stage, python + arguments)
            exported = out / 'export/export.json'
        else:
            for stage in ('review', 'choice', 'export', 'verify_export'):
                choice = 'accept' if stage == 'choice' else None
                cli(stage, flow.command(stage, choice=choice), flow=flow, choice=choice)
            exported = flow.workspace / 'export/export.json'
        with p.validation_readback_session():
            report['route_readback'] = p.check_result(receipt)
            report['export_readback'] = ex.check_export(exported)
        route = f.read_json(receipt); export = f.read_json(exported)
        if export.get('export_accepted') is not True or export.get('original_geometry_and_routing_unchanged') is not True:
            raise p.Rejected('Fresh original-design delivery proof refused.')
        report.update(accepted=True, workflow_delivered=True, status='completed', export_receipt=str(exported),
            export_sha256=p.sha(exported), candidate_sha256=export['candidate_sha256'], native=export['native'],
            metrics=export['metrics'], route_native=route['native'], route_metrics=route['metrics'])
    except (Exception, KeyboardInterrupt) as exc:
        report.update(accepted=False, workflow_delivered=False, status='cancelled' if isinstance(exc, KeyboardInterrupt) else 'failed',
            reason=type(exc).__name__ + ': ' + str(exc))
    if method_start is not None and 'method_wall_seconds' not in report:
        report.update(method_wall_seconds=time.monotonic() - method_start, method_full_cpu_seconds=cpu() - method_cpu)
    # Never omit partial/failed producer evidence when a UI adoption refused it.
    route_file = (out / 'stronger-route/result.json' if args.arm == 'B2_stronger'
        else out / 'thermal-route/result.json' if args.arm == 'C_thermal'
        else flow.workspace / 'route/result.json')
    if route_file.is_file():
        report['route_attempt'] = read_attempt(route_file)
        if 'read_error' in report['route_attempt']:
            report.update(accepted=False, workflow_delivered=False, status='invalidated',
                reason='Partial route receipt could not be read; raw evidence retained.')
    try: fresh()
    except (Exception, KeyboardInterrupt) as exc:
        report.update(accepted=False, workflow_delivered=False, status='invalidated', reason=type(exc).__name__ + ': ' + str(exc))
    def account():
        report.update(sampled_wall_seconds=time.monotonic() - START, sampled_full_cpu_seconds=cpu() - CPU0,
            accounting_point='Before shared guarded publication; final caps include readback tail. Complete enclosing exit accounting required.')
        if report['accepted'] and max(report['sampled_wall_seconds'], report['sampled_full_cpu_seconds']) > preset.delivery_wall_cpu_cap_seconds - 15:
            report.update(accepted=False, status='budget_exceeded')
        report['workflow_delivered'] = report['accepted'] is True and report['status'] == 'completed'

    def delivered(_):
        verify_delivery(report, board, context)

    # Reuse the product's guarded publisher, including correction/retention after
    # cancellation, source drift, readback refusal or cap exhaustion.
    with p.validation_readback_session():
        f.publish(out, report, fresh, account, left,
            owned=lambda: h.owned_destination(owner), result_checker=delivered)
    return 0 if report['accepted'] and report['workflow_delivered'] and report['status'] == 'completed' else 130 if report['status'] == 'cancelled' else 2



if __name__ == '__main__':
    def interrupted(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, interrupted)
    raise SystemExit(main())
