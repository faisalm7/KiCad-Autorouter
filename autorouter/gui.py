"""Offline external graphical workflow; no live-board edits or validation bypass.

Run with KiCad's wx-enabled Python. All expensive actions invoke the existing
CLI in a separate project interpreter/process. UI outcomes are not PCB approval.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import uuid
from typing import Callable

from . import config as c, preferences as pref
from ._improve_context import RESERVE_SECONDS as IMPROVE_RETURN_RESERVE_SECONDS
from .runner import elapsed_time, ELAPSED_CLOCK_POLICY

LOG_LIMIT = 2 * 1024 * 1024
GUI_IMPROVE_MIN_SECONDS = 90
METHODS = ('route', 'improve', 'recover')
THERMAL_HELP = ('Experimental thermal recovery has a validated completion result on one exposed board family; '
    'it is not general routing or electrical certification. Requires KiCad 10.0.7, two copper layers, '
    'whole-board unlocked routing, Native guidance, standard/both, all source layers and default via cost. '
    'The 90–900 s method budget includes the incumbent, repair attempts and final validation; internal '
    'reserves are inside it. Fresh export has a separate budget. Failed/cancelled work and its incumbent '
    'are retained; no automatic application, acceptance intent or fallback.')
IMPROVE_HELP = ('Experimental Improve uses a tuned incumbent, bounded pruning trials and final Native validation. '
    f'The whole Improve-method budget includes its {IMPROVE_RETURN_RESERVE_SECONDS:g}-second internal return reserve; it is not an added '
    'allowance or a completion guarantee. Fresh export has a separate budget. Selected KiCad 10.0.7 '
    'requires canonical two-layer flat sources with single Default or supported original netclasses, '
    'no schematic class flags/hierarchy, and engine-default via cost; '
    'unsupported inputs refuse. No live-board application or electrical approval is implied.')
FAILURE_REASON_LIMIT = 512
SUMMARY_LIMIT = 128 * 1024


def export_validation_seconds(route_seconds):
    """Allocate separate bounded Native validation without changing routing settings."""
    from . import review_export as ex
    seconds = pref.validate(dict(pref.DEFAULTS, seconds=route_seconds))['seconds']
    return ex.validate_seconds(max(ex.MIN_SECONDS, min(seconds, ex.SECONDS)))


def method_for_index(index):
    if type(index) is not int or not 0 <= index < len(METHODS):
        raise ValueError('Choose an explicit routing method.')
    return METHODS[index]


def check_thermal_settings(config):
    """The recovery CLI accepts only its fixed contract, not arbitrary presets."""
    effective = pref.validate(config)
    required = dict(scope='whole_board_unlocked_routing', profile='standard', adapter='both',
                    guidance='native', layers='source_all', scoring_preference=None)
    if (c.NATIVE_VERSION != '10.0.7' or any(effective[key] != value for key, value in required.items())
            or not 90 <= effective['seconds'] <= 900):
        raise ValueError('Experimental thermal recovery requires selected KiCad 10.0.7, whole-board unlocked '
            'routing, Native guidance, standard/both, all source layers/default via cost and a 90–900 second '
            'whole recovery-method budget. Settings were not changed.')
    from .pipeline import require_native_scope
    require_native_scope(purpose='thermal-recovery', scope=effective['scope'], guidance=effective['guidance'],
        layers=effective['layers'], profile=effective['profile'], adapter=effective['adapter'],
        scoring=effective['scoring_preference'])
    return effective


def check_thermal_source(board):
    from . import pipeline as p, sexpr as sx
    original = p.preflight(board)  # Same default class/format/rule contract as recover().
    copper = [sx.unquote(row[1]) for row in sx.one(original, 'layers', [])[1:]
              if isinstance(row, list) and len(row) > 2 and sx.unquote(row[1]).endswith('.Cu')]
    if copper != ['F.Cu', 'B.Cu']:
        raise ValueError('Experimental thermal recovery supports two source copper layers only; no layers were changed.')


def human_summary(stage, record, *, receipt_path=None, findings_receipt_path=None, method=None):
    """Presentation only; existing CLI validation and original receipts remain authoritative."""
    title = {'inspect': 'Saved-project Native findings', 'preview': 'Saved-project preview', 'route': 'Routing result',
             'review': 'Disposable review project', 'choice': 'Review intent',
             'export': 'Fresh separate-project export', 'verify_export': 'Export readback'}.get(stage, stage)
    status = str(record.get('status', 'current' if record.get('current') is True else 'not reported')).replace('_', ' ')
    lines = [title, 'Status: ' + status]
    recovery = method == 'recover' or record.get('strategy') == 'native_validated_thermal_bridge'
    improve = method == 'improve' or record.get('strategy') == 'native_validated_zone_net_pruning'
    if recovery:
        lines += [THERMAL_HELP]
    elif improve:
        lines += [IMPROVE_HELP]
    # Findings and protection belong above long filesystem details. Keep exact
    # paths below, including both receipts when review inherits route findings.
    locations = []
    if receipt_path is not None: locations += ['Full workflow receipt: ' + str(receipt_path)]
    if findings_receipt_path is not None: locations += ['Full findings receipt: ' + str(findings_receipt_path)]
    if record.get('source'):
        lines += ['Board: ' + Path(record['source']).name]
        locations += ['Original saved PCB: ' + str(record['source'])]
    project = record.get('project_file') or record.get('review_project')
    if project: locations += ['Separate project: ' + str(project)]
    if record.get('candidate'): locations += ['Candidate PCB: ' + str(record['candidate'])]
    pruning = record.get('pruning_preferences', {})
    # Review/export have their own budgets. Display the actual parent capture
    # rather than the merged stage budget or mutable current widgets.
    settings = ((pruning.get('effective') if improve and isinstance(pruning, dict) else None)
                or record.get('effective_preferences') or record.get('routing_preferences', {}).get('effective', {}))
    scope = settings.get('scope') or record.get('scope')
    scopes = {'whole_board_unlocked_routing': 'Reroute unlocked copper; preserve locked routing',
              'partial_completion': 'Complete gaps; preserve all existing routing',
              'selected_nets': 'Reroute selected unlocked nets; preserve other routing'}
    if scope: lines += ['Routing/protection: ' + scopes.get(scope, str(scope))]
    if settings:
        layers = settings.get('layers', 'not reported')
        if isinstance(layers, list): layers = ', '.join(layers)
        lines += ['Settings: profile ' + str(settings.get('profile', 'not reported'))
                  + '; corrections ' + str(settings.get('adapter', 'not reported'))
                  + ('; whole recovery-method budget ' if recovery else '; whole Improve-method budget ' if improve else '; routing budget ')
                  + str(settings.get('seconds', 'not reported')) + ' s'
                  + '; layers ' + str(layers)
                  + '; via preference ' + str(settings.get('scoring_preference') or 'engine default')]
        if settings.get('nets'): lines += ['Selected nets: ' + ', '.join(settings['nets'])]
        if 'seconds' in settings:
            lines += ['Additional Native export-validation budget: '
                      + str(export_validation_seconds(settings['seconds']))
                      + (' s after acceptance, separate from recovery; the method budget is unchanged.' if recovery
                         else ' s after acceptance, separate from Improve; the method budget is unchanged.' if improve
                         else ' s after acceptance, separate from routing; the routing budget is unchanged.')]
    elif recovery and 'budget_seconds' in record:
        lines += ['Whole recovery-method budget: ' + str(record['budget_seconds'])
                  + ' s, including incumbent routing, repair and final validation.',
                  'Additional Native export-validation budget: '
                  + str(export_validation_seconds(record['budget_seconds'])) + ' s after acceptance.']
    if stage == 'preview':
        lines += ['Static preflight only; Native routing validation has not run.',
                  'Existing route items: ' + str(record.get('existing_route_items', 'not reported'))
                  + '; protected: ' + str(record.get('protected_route_items', 'not reported'))
                  + '; to reroute: ' + str(record.get('rerouted_route_items', 'not reported'))]
        if record.get('schematic_class_check') is not None:
            lines += ['KiCad must verify schematic/PCB class bindings before routing starts.']
    if stage == 'inspect':
        lines += ['Actual Native refill and complete-schematic checks ran on a separate copy.',
                  'Unrouted connections are routing demand; they do not by themselves make the source invalid.',
                  'This inspection does not approve a route or waive any finding.']
    if record.get('invariants_unchanged') is True:
        lines += ['Original-design checks passed; source geometry and protected routing retained.']
    matches = record.get('protected_route_import', {}).get('matches')
    audit = record.get('selected_net_audit')
    if record.get('scope') == 'selected_nets':
        if (record.get('invariants_unchanged') is True and type(audit) is dict
                and type(audit.get('schema')) is int and audit['schema'] == 1
                and audit.get('policy') == 'selected-nets-v1' and audit.get('scope_passed') is True
                and type(audit.get('protected_count')) is int and audit['protected_count'] >= 0):
            lines += ['Protected route items retained: ' + str(audit['protected_count'])]
    elif isinstance(matches, list): lines += ['Protected route items retained: ' + str(len(matches))]
    elif (improve and record.get('invariants_unchanged') is True
            and type(record.get('protected_routes')) is int and record['protected_routes'] >= 0):
        lines += ['Protected route items retained: ' + str(record['protected_routes'])]
    if record.get('schematic_parity'): lines += ['Schematic: ' + str(record['schematic_parity'])]
    metrics = record.get('metrics') or record.get('saved_metrics')
    if isinstance(metrics, dict):
        length = metrics.get('track_length_mm')
        length_text = format(length, '.6f') if type(length) in (int, float) else 'not reported'
        lines += ['Route: ' + length_text + ' mm track; ' + str(metrics.get('vias', 'not reported')) + ' vias',
                  'Board: ' + str(metrics.get('footprints', 'not reported')) + ' footprints; '
                  + str(metrics.get('pads', 'not reported')) + ' pads; '
                  + str(metrics.get('zones', 'not reported')) + ' zones; '
                  + str(metrics.get('copper_layers', 'not reported')) + ' copper layers']
    native = record.get('native') or record.get('saved_native_findings')
    if isinstance(native, dict):
        lines += ['Native findings: ' + str(native.get('opens', 'not reported')) + ' opens; '
                  + str(native.get('blocking', 'not reported')) + ' blocking; '
                  + str(native.get('warnings', 'not reported')) + ' warnings; '
                  + str(native.get('exclusions', 'not reported')) + ' exclusions']
        qualification = native.get('field_parity', {}).get('qualification', {})
        if qualification.get('qualified') is True:
            lines += ['Effective schematic fields compared: ' + str(qualification.get('component_count', 'not reported'))
                      + ' components / ' + str(qualification.get('compared_field_count', 'not reported'))
                      + ' fields. Listed Native warnings remain visible.']
        if record.get('whole_project_drc_clean') is False:
            lines += ['The whole project is not DRC-clean; inspect every finding below.']
    if stage in ('review', 'choice', 'export', 'verify_export'):
        lines += ['Separate-project workflow only; no live-board application or physical/electrical approval.']
    if stage == 'review': lines += ['Inspect the separate project and every finding. Before Accept intent, close its PCB/schematic editors and use File > Close Project in KiCad project manager. Creating this copy does not run a fresh Native check.']
    if stage == 'choice':
        lines += ['Recorded review intent: ' + str(record.get('choice', 'not reported')) + '. This is not PCB certification.']
        unchanged = record.get('candidate_board_unchanged')
        if type(unchanged) is bool:
            lines += ['Reviewed PCB: ' + ('unchanged from the validated candidate.' if unchanged else 'changed from the validated candidate.')]
        changes = record.get('review_project_changes')
        if record.get('review_project_matches_recorded_candidate') is False and isinstance(changes, dict):
            lines += ['Review project differs from the recorded candidate: '
                      + str(len(changes.get('added', []))) + ' added; '
                      + str(len(changes.get('removed', []))) + ' removed; '
                      + str(len(changes.get('changed', []))) + ' changed files.',
                      'Fresh export reconstructs original source rules and settings; review-only changes are not adopted.']
    if stage == 'export': lines += ['Fresh original-rule Native validation; the original source is not overwritten.']
    if record.get('error'): lines += ['Action error: ' + str(record['error'])]
    lines += ['Physical/electrical and manufacturing validation remains separate.']
    if isinstance(native, dict):
        groups = [('Ignored checks', native.get('ignored_checks', [])), ('Findings', native.get('findings', []))]
        size = sum(len(line) + 1 for line in lines)
        omitted = 0
        for label, rows in groups:
            lines += ['', label + ' (' + str(len(rows)) + ' retained):']
            if not rows: lines += ['None.']
            for index, item in enumerate(rows, 1):
                if label == 'Ignored checks':
                    text = str(index) + '. ' + str(item.get('description', 'No description')) + ' [' + str(item.get('key', 'unknown')) + ']'
                else:
                    text = str(index) + '. ' + str(item.get('severity', 'unknown')).upper() + ': ' + str(item.get('description', 'No description')) + ' [' + str(item.get('type', 'unknown')) + ']'
                    for detail in item.get('items', []):
                        text += '\n   ' + str(detail.get('description', 'Item'))
                        position = detail.get('pos')
                        if isinstance(position, dict): text += ' at ' + str(position.get('x', '?')) + ', ' + str(position.get('y', '?')) + ' mm'
                if size + len(text) + 1 <= SUMMARY_LIMIT:
                    lines.append(text); size += len(text) + 1
                else: omitted += 1
        if omitted:
            lines += ['', str(omitted) + ' further finding/ignored-check entries are not displayed because of the UI text bound.',
                      'ALL entries remain in the full findings receipt. Open it before completing review: ' + str(findings_receipt_path or receipt_path or 'retained workflow receipt')]
    if locations:
        lines += ['', 'Files and full reports', *locations]
    return '\n'.join(lines)

def _completed_summary(flow, stage, record):
    """Render retained completed findings for stage completion and inspection."""
    display = {**flow.records.get('route', {}), **record}
    if stage == 'export': display.update(flow.records['export'])
    if getattr(flow, 'method', 'route') in ('recover', 'improve'):
        display['effective_preferences'] = json.loads(flow.settings_bytes)
    receipt_name = {'inspect': 'inspection/inspection.json', 'preview': 'preview.command.log', 'route': 'route/result.json',
        'review': 'review/review.json', 'choice': 'choice/choice.json', 'export': 'export/export.json'}[stage]
    receipt_path = flow.workspace / receipt_name
    findings_path = flow.workspace / 'route/result.json' if stage == 'review' else receipt_path
    return human_summary(stage, display, receipt_path=receipt_path,
                         findings_receipt_path=findings_path if display.get('native') or display.get('saved_native_findings') else None,
                         method=getattr(flow, 'method', 'route'))


_REGISTERED_ACTIONS = []


def canonical(path, *, exists=True):
    from .handoff import real_path
    return real_path(path, existing=exists)


def source_inventory(board):
    from .placement_clearance import inventory
    return inventory(board.parent, max_bytes=32 * 1024 * 1024,
                     max_files=2000, max_entries=4000)


def read_record(path):
    from .floor_route import read_json
    return read_json(path)


def child_environment():
    env = {key: value for key, value in os.environ.items()
           if key not in ('PYTHONPATH', 'PYTHONHOME', 'KICAD_API_SOCKET', 'KICAD_API_TOKEN')}
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1')
    return env



@dataclass(frozen=True)
class SourceGuard:
    """Internal exact-source binding; never selected by model/preset/CLI JSON.

    The trusted, bounded read-only verifier must raise on stale origin and return
    None. It grants no approval. It also runs at queued UI adoption, so callers
    should use a material/metadata fence there, not launch a Native process.
    """
    board: Path
    verify_origin: Callable[[], None]
    verify_task: Callable[[dict, str, Path | None], None] | None = None
    placement_origin: Path | None = None
    _files_json: str = field(init=False, repr=False)

    def __post_init__(self):
        if not callable(self.verify_origin): raise ValueError('A trusted source verifier is required.')
        if self.verify_task is not None and not callable(self.verify_task):
            raise ValueError('A trusted task verifier is required.')
        if self.placement_origin is not None:
            if self.verify_task is None: raise ValueError('Placement origin requires its composed task verifier.')
            object.__setattr__(self, 'placement_origin', canonical(self.placement_origin))
        board = canonical(self.board)
        if board.suffix != '.kicad_pcb' or not board.is_file(): raise ValueError('Bind the exact saved PCB.')
        object.__setattr__(self, 'board', board)
        object.__setattr__(self, '_files_json', json.dumps(source_inventory(board), sort_keys=True))
        self.check(board)

    def check(self, board):
        if canonical(board) != self.board:
            raise ValueError('Displayed PCB differs from the bound source origin. Open an ordinary session for another board.')
        if source_inventory(self.board) != json.loads(self._files_json):
            raise ValueError('Bound source project changed; obtain a fresh checked source.')
        if self.verify_origin() is not None:
            raise ValueError('Source verifier must return no approval or result authority.')
        if source_inventory(self.board) != json.loads(self._files_json):
            raise ValueError('Bound source project changed during origin verification.')

    def check_task(self, settings, method, candidate=None):
        """Composed-task constraints; no model or preset may supply a callback."""
        self.check_task_candidates(settings, method, () if candidate is None else (candidate,))

    def check_task_candidates(self, settings, method, candidates):
        """Fence one bounded read-only batch, rather than rereading origin per file."""
        if type(candidates) not in (tuple, list) or len(candidates) > 2:
            raise ValueError('At most the routed and exported candidate may be checked together.')
        if self.verify_task is not None:
            from .local_settings import check_current_metadata
            self.check(self.board)
            paths = [canonical(candidate) for candidate in candidates]
            witnesses = [source_inventory(path) for path in paths]
            for path in paths or (None,):
                if self.verify_task(copy.deepcopy(settings), method, path) is not None:
                    raise ValueError('Task verifier must return no approval or result authority.')
            self.check(self.board)
            for path, before in zip(paths, witnesses):
                if source_inventory(path) != before:
                    raise ValueError('Composed candidate changed during the final origin check.')
            for path in paths:
                check_current_metadata(path.with_suffix('.kicad_prl'))


def _check_source_guard(guard, board):
    if guard is not None:
        if type(guard) is not SourceGuard: raise ValueError('Internal trusted SourceGuard required.')
        guard.check(board)


def _window_source_guard(window, flow):
    """A displayed request cannot silently detach or replace its injected guard."""
    guard = getattr(window, 'source_guard', None)
    attached = getattr(flow, 'source_guard', None)
    if guard is not None or attached is not None:
        if attached is not guard or canonical(window.board.GetValue()) != guard.board:
            raise ValueError('Displayed source guard differs from this checked session.')
    return guard


def _window_request(window):
    """Read displayed values, including a native popup's committed selection.

    Cocoa can commit a selection after its change event. Event generations
    alone therefore cannot establish that a queued result matches the UI.
    This captures intent only; the existing Workflow checks remain authoritative.
    """
    return Request(window.board.GetValue(), window.output.GetValue(),
                   json.dumps(window.config()), window.ack.GetValue(),
                   method_for_index(window.method.GetSelection()),
                   source_guard=getattr(window, 'source_guard', None))


@dataclass(frozen=True)
class Request:
    board: str
    output_parent: str
    settings_json: str
    saved_closed: bool
    method: str = 'route'
    source_guard: SourceGuard | None = None

    def prepare(self):
        """Called off the UI thread; capture exact saved project identity."""
        if self.saved_closed is not True:
            raise ValueError('Save and close the source PCB and schematic editors, then acknowledge it.')
        board = canonical(self.board)
        _check_source_guard(self.source_guard, board)
        if board.suffix != '.kicad_pcb' or not board.is_file():
            raise ValueError('Select the exact saved .kicad_pcb file.')
        for suffix in ('.kicad_pro', '.kicad_sch'):
            sibling = canonical(board.with_suffix(suffix))
            if not sibling.is_file():
                raise ValueError('A matching saved project and complete schematic are required.')
        parent = canonical(self.output_parent)
        if not parent.is_dir() or parent == board.parent or board.parent in parent.parents:
            raise ValueError('Select an existing output folder outside the source project.')
        settings = pref.validate(json.loads(self.settings_json))
        if self.method not in METHODS: raise ValueError('Unknown routing method.')
        if self.source_guard is not None:
            self.source_guard.check_task(settings, self.method)
        if self.method == 'improve': check_improve_settings(settings)
        if self.method == 'recover':
            check_thermal_settings(settings)
            files = source_inventory(board)
            check_thermal_source(board)
            if source_inventory(board) != files:
                raise ValueError('Saved source changed during thermal support checks; preview again.')
        else:
            files = source_inventory(board)
        _check_source_guard(self.source_guard, board)
        workspace = parent / ('autorouter-gui-' + uuid.uuid4().hex)
        workspace.mkdir(mode=0o700)
        from .handoff import capture_destination
        owner = {}; capture_destination(owner, workspace)
        settings_bytes = (json.dumps(settings, indent=2, sort_keys=True) + '\n').encode()
        target = workspace / 'settings.json'
        with target.open('xb') as stream:
            stream.write(settings_bytes)
        return Workflow(board, workspace, owner, json.dumps(files, sort_keys=True), settings_bytes, self.method,
                        source_guard=self.source_guard)


class Workflow:
    """UI state only. Existing CLI readers authorize every review/export."""
    def __init__(self, board, workspace, owner, files_json, settings_bytes, method='route', *, source_guard=None):
        from .handoff import runtime_inventory
        self.board, self.workspace, self.owner = board, workspace, owner
        self.files_json, self.settings_bytes = files_json, settings_bytes
        self.method = method
        self._source_guard = source_guard
        self.ready = set()
        self.choice = None
        self.records = {}
        self.runtime_hashes = runtime_inventory()

    @property
    def source_guard(self): return self._source_guard

    def fresh(self):
        from .handoff import owned_destination, runtime_inventory
        from .placement_clearance import read_bytes
        if owned_destination(self.owner) != self.workspace:
            raise ValueError('Output folder identity changed.')
        if source_inventory(self.board) != json.loads(self.files_json):
            raise ValueError('Saved source project changed. Start a new session and preview again.')
        if read_bytes(self.workspace / 'settings.json', pref.MAX_PRESET_BYTES) != self.settings_bytes:
            raise ValueError('Captured settings changed. Start a new session.')
        if runtime_inventory()!=self.runtime_hashes:
            raise ValueError('Routing runtime changed. Start a new session with the intended tool profile.')
        _check_source_guard(self.source_guard, self.board)
        if self.source_guard is not None:
            settings = json.loads(self.settings_bytes)
            candidates = [self.records[stage]['candidate'] for stage in ('route', 'export')
                          if stage in self.records] if self.source_guard.verify_task is not None else []
            self.source_guard.check_task_candidates(settings, self.method, candidates)

    def command(self, stage, *, choice=None):
        self.fresh()
        required = {'route': 'preview', 'review': 'route', 'choice': 'review',
                    'export': 'choice', 'verify_export': 'export'}
        if stage in required and required[stage] not in self.ready:
            raise ValueError('Complete the preceding checked workflow step first.')
        python = c.ROOT / '.venv/bin/python'
        if not python.is_file() or not os.access(python, os.X_OK):
            raise ValueError('The project environment is missing; complete documented setup first.')
        argv = [str(python), '-B', '-m', 'autorouter']
        settings = str(self.workspace / 'settings.json')
        if self.method == 'recover': check_thermal_settings(json.loads(self.settings_bytes))
        if stage == 'inspect':
            argv += ['inspect-project', str(self.board), '--seconds', '60',
                     '--output', str(self.workspace / 'inspection')]
        elif stage in ('preview', 'route'):
            if self.method == 'recover' and stage == 'route':
                argv += ['recover', str(self.board), '--seconds', str(json.loads(self.settings_bytes)['seconds'])]
            else:
                argv += [self.method if stage == 'route' else stage, str(self.board), '--settings', settings]
            if stage == 'preview' and self.method == 'improve': argv += ['--purpose', 'improve']
            if stage == 'route': argv += ['--output', str(self.workspace / 'route')]
            if self.source_guard is not None and self.source_guard.placement_origin is not None:
                argv += ['--placement-origin', str(self.source_guard.placement_origin)]
        elif stage == 'review':
            argv += ['review-copy', str(self.workspace / 'route/result.json'), '--render',
                     '--output', str(self.workspace / 'review')]
        elif stage == 'choice':
            if choice not in ('accept', 'reject'): raise ValueError('Choose accept or reject explicitly.')
            argv += ['review-choice', str(self.workspace / 'review/review.json'), '--choice', choice,
                     '--output', str(self.workspace / 'choice')]
        elif stage == 'export':
            if self.choice != 'accept': raise ValueError('Only explicit acceptance intent can request a fresh export.')
            argv += ['review-export', str(self.workspace / 'choice/choice.json'), '--seconds',
                     str(export_validation_seconds(json.loads(self.settings_bytes)['seconds'])),
                     '--output', str(self.workspace / 'export')]
        elif stage == 'verify_export':
            argv += ['review-export-check', str(self.workspace / 'export/export.json')]
        else:
            raise ValueError('Unknown workflow action.')
        if stage in self.ready and stage != 'verify_export':
            raise ValueError('This action already completed; use its retained output.')
        return argv

    def check_request(self, request):
        if (request.saved_closed is not True or canonical(request.board) != self.board
                or canonical(request.output_parent) != self.workspace.parent
                or pref.validate(json.loads(request.settings_json)) != json.loads(self.settings_bytes)
                or request.method != self.method or request.source_guard is not self.source_guard):
            raise ValueError('Displayed source or settings differ from this session; preview again.')

    def timeout(self, stage):
        if stage == 'export':
            return float(export_validation_seconds(json.loads(self.settings_bytes)['seconds'])) + 45
        return float(json.loads(self.settings_bytes)['seconds']) + 45 if stage == 'route' else 90.0

    def adopt(self, stage, process, log_path, *, choice=None):
        self.fresh()
        if (type(process['exit_code']) is not int
                or process['cancel_requested'] or process['log_truncated']
                or process['exit_code'] in (130, 143)
                or type(process['exit_code']) is int and process['exit_code'] < 0):
            raise ValueError('Action failed or was cancelled. Evidence was retained; no positive state adopted.')
        if process['exit_code'] != 0:
            detail = failed_route_detail(self.workspace / 'route/result.json') if stage == 'route' else None
            if stage == 'preview' and type(process['exit_code']) is int and process['exit_code'] == 2:
                detail = failed_preview_detail(log_path)
            if stage == 'export' and type(process['exit_code']) is int and process['exit_code'] == 2:
                detail = failed_export_detail(log_path)
            if stage == 'verify_export' and process['exit_code'] == 2:
                detail = failed_export_check_detail(log_path)
            raise ValueError(detail or 'Action failed or was cancelled. Evidence was retained; no positive state adopted.')
        if stage == 'inspect':
            from .project_inspection import check
            record = check(self.workspace / 'inspection/inspection.json')
            if record['source'] != str(self.board) or record['source_hashes'] != json.loads(self.files_json):
                raise ValueError('Inspection did not bind this exact saved project.')
        elif stage == 'preview':
            record = json.loads(log_path.read_bytes())
            if (record.get('status') != 'preview' or record.get('static_preflight_passed') is not True
                    or record.get('source') != str(self.board)
                    or record.get('source_sha256') != json.loads(self.files_json)[self.board.name]):
                raise ValueError('Preview did not bind this exact saved source.')
        elif stage == 'route':
            record = read_record(self.workspace / 'route/result.json')
            if (record.get('accepted') is not True or record.get('status') != 'routing_accepted'
                    or record.get('source') != str(self.board)
                    or record.get('source_hashes') != json.loads(self.files_json)):
                raise ValueError('Routing did not produce an accepted result for this source. Inspect retained findings.')
            if self.method == 'recover':
                seconds = json.loads(self.settings_bytes)['seconds']
                if (record.get('strategy') != 'native_validated_thermal_bridge'
                        or record.get('scope') != 'whole_board_unlocked_routing'
                        or record.get('engine_profile') != 'standard' or record.get('adapter') != 'both'
                        or record.get('budget_seconds') != seconds or record.get('cpu_budget_seconds') != seconds
                        or record.get('metrics', {}).get('copper_layers') != 2):
                    raise ValueError('Thermal recovery did not bind the captured whole-method contract.')
        elif stage == 'review':
            from .handoff import check_stage_budget
            record = read_record(self.workspace / 'review/review.json')
            check_stage_budget(record, 'review')
            if record.get('status') != 'ready_for_manual_review':
                raise ValueError('Shared review validation did not complete.')
        elif stage == 'choice':
            from .handoff import check_stage_budget
            record = read_record(self.workspace / 'choice/choice.json')
            check_stage_budget(record, 'choice')
            if record.get('choice_recorded') is not True or record.get('choice') != choice:
                raise ValueError('Shared review-choice checks did not complete.')
            self.choice = choice
        elif stage == 'export':
            record = read_record(self.workspace / 'export/export.json')
            if record.get('export_accepted') is not True:
                raise ValueError('Fresh original-rule Native export refused.')
        elif stage == 'verify_export':
            record = json.loads(log_path.read_bytes())
            exported = self.records['export']
            candidate = self.workspace / 'export/validation/candidate' / self.board.name
            if (record.get('current') is not True or record.get('export_accepted') is not True
                    or record.get('applied') is not False or record.get('candidate') != str(candidate)
                    or exported.get('candidate') != str(candidate)
                    or exported.get('project_file') != str(candidate.with_suffix('.kicad_pro'))
                    or record.get('candidate_sha256') != exported.get('candidate_sha256')):
                raise ValueError('Current exported-project readback refused.')
        else:
            raise ValueError('Unknown outcome.')
        self.fresh()
        if self.source_guard is not None and stage in ('route', 'export', 'verify_export'):
            self.source_guard.check_task(json.loads(self.settings_bytes), self.method, record['candidate'])
        self.records[stage] = record
        self.ready.add(stage)
        return record

    def inspect_path(self, kind, *, job=None):
        self.fresh()
        if 'review' not in self.ready: raise ValueError('Create a checked disposable review first.')
        if kind == 'preview': target = self.workspace / 'review/preview.html'
        elif kind == 'review': target = Path(self.records['review']['project_file'])
        elif kind == 'export':
            if 'verify_export' not in self.ready: raise ValueError('Fresh export readback must pass first.')
            if job is None: raise ValueError('A fresh cancellable export check is required before opening.')
            # The public reader installs signal handlers. Run its existing CLI
            # in a child main thread, never inside this GUI inspection thread.
            argv = self.command('verify_export')
            log = self.workspace / ('inspect-export-' + uuid.uuid4().hex + '.command.log')
            process = job.run(argv, log, timeout=self.timeout('verify_export'))
            job.adopt(self, 'verify_export', process, log)
            target = Path(self.records['export']['project_file'])
        else: raise ValueError('Unknown inspection target.')
        target = canonical(target)
        self.fresh()
        if self.workspace not in target.parents or not target.is_file():
            raise ValueError('Inspection target is outside this separate project.')
        return target

    def check_open_export_material(self):
        """Recheck queued export bytes and current retained PRL metadata.

        This is not another Native check or an atomic editor transaction.
        The worker's current CLI reader remains the acceptance authority.
        """
        from . import review_export as ex
        from . import local_settings as local
        from .floor_route import canonical as canonical_json
        exported = self.records['export']
        root = self.workspace / 'export'
        material = ex.evidence(root)
        if (canonical_json(read_record(root / 'export.json')) != canonical_json(exported)
                or material != exported.get('export_evidence')):
            raise ValueError('Checked export changed while opening. Start a fresh preview; retained files were not reaccepted.')
        for relative in material['files']:
            if Path(relative).suffix == '.kicad_prl' and not local.check_current_metadata(root / relative):
                raise ValueError('Checked export local settings disappeared while opening.')


def check_improve_settings(config):
    """GUI-only operational minimum; the public strategy contract is unchanged."""
    from .strategy import pruning_scope
    effective = pref.validate(config)
    pruning_scope(effective)
    if c.NATIVE_VERSION == '10.0.7' and effective['scoring_preference'] is not None:
        raise ValueError('Selected KiCad 10.0.7 Improve requires engine-default via cost. '
            'The via preference and other settings were not changed.')
    if effective['seconds'] < GUI_IMPROVE_MIN_SECONDS:
        raise ValueError('Graphical Improve needs at least 90 seconds for incumbent and final checks. This is an operational minimum, not a completion guarantee; the budget was not changed.')
    return effective


def completion_search_preset(config):
    """Explicit search preference; preserve the requested problem and budget.

    Source eligibility and Native validity still belong to Preview and the
    ordinary producer/readers. This helper grants no routing admission.
    """
    effective = pref.validate(config)
    if (effective['scope'] not in {'whole_board_unlocked_routing', 'partial_completion'}
            or effective['guidance'] != 'native' or effective['adapter'] != 'both'
            or effective['layers'] != 'source_all'):
        raise ValueError('Completion search requires whole-board or gap completion, both corrections '
                         'and all source layers. Set those options explicitly, then preview support.')
    return pref.validate(dict(effective, profile='tuned', scoring_preference='via_low'))


def review_close_hint(workspace):
    """Operational hint only; CLI choice/export still perform full validation."""
    from . import handoff as h
    project = canonical(Path(workspace) / 'review/project')
    h.require_closed_review(h.pc.inventory(project, max_bytes=h.PROJECT_BYTES,
        max_files=2000, max_entries=4000))


def short_failure_reason(reason):
    """Untrusted diagnostic text, bounded for the findings panel, never proof."""
    if type(reason) is not str or not reason.strip(): return None
    text = ''.join(char if char.isprintable() else ' ' for char in reason[:FAILURE_REASON_LIMIT]).strip()
    if not text: return None
    if len(reason) > FAILURE_REASON_LIMIT: text += ' [detail shortened]'
    return text


def failed_command_detail(path, label, next_action):
    """Read the bounded rejected-command shape as diagnostic text only."""
    try:
        try: record = read_record(path)
        except ValueError:
            # A live review emits one bounded event before its final result.
            # This is diagnostic parsing only, never acceptance authority.
            raw = Path(path).read_bytes()
            if len(raw) > SUMMARY_LIMIT: return None
            first, separator, rest = raw.partition(b'\n')
            if not separator or json.loads(first).get('kind') != 'autorouter.warning-review-required.v1': return None
            record = json.loads(rest)
        if (type(record) is not dict or set(record) != {'status', 'reason'}
                or record.get('status') != 'rejected'):
            return None
        text = short_failure_reason(record.get('reason'))
        if text is None: return None
        return (label + ' refused: ' + text + '\n' + next_action +
                '\nFull failure log: ' + str(path))
    except Exception:
        return None


def failed_preview_detail(path):
    return failed_command_detail(path, 'Saved-project preview',
        'Start a fresh preview using the intended saved project and settings. No preview or candidate was accepted.')


def _warning_review_packet(event, expected_path):
    """Read the exact live proof; transport delay cannot renew its deadline."""
    from . import pipeline as p, review_export as ex
    if (type(event) is not dict or event.get('kind') != 'autorouter.warning-review-required.v1'
            or type(event.get('pending')) is not str
            or type(event.get('nonce')) is not str or len(event['nonce']) != 32
            or any(x not in '0123456789abcdef' for x in event['nonce'])
            or any(type(event.get(key)) is not str or len(event[key]) != 64
                   or any(x not in '0123456789abcdef' for x in event[key])
                   for key in ('pending_sha256', 'delta_sha256', 'candidate_sha256', 'native_report_sha256'))
            or type(event.get('warning_review')) is not dict
            or set(event['warning_review']) != {'policy', 'delta', 'findings_equivalent', 'review_text', 'copper_witness'}
            or not ex.finite(event.get('remaining_seconds')) or not 0 < event['remaining_seconds'] <= ex.SECONDS):
        raise ValueError('Invalid live warning-review challenge.')
    try: ex._warning_clock(event, current=elapsed_time())
    except p.Rejected as exc: raise ValueError(str(exc)) from exc
    path = Path(event['pending'])
    if path != expected_path or path.is_symlink() or not path.is_file() or path.stat().st_size > 2*1024*1024:
        raise ValueError('Updated-warning review path or size is unsupported.')
    if p.sha(path) != event['pending_sha256']: raise ValueError('Updated-warning review changed before display.')
    pending = read_record(path); review = pending.get('warning_review')
    if (type(pending.get('schema')) is not int or pending['schema'] != 1
            or pending.get('kind') != 'live-warning-review-pending-v1' or pending.get('policy') != ex.WARNING_REVIEW_POLICY
            or pending.get('export_accepted') is not False or pending.get('resumable_after_exit') is not False
            or pending.get('nonce') != event['nonce'] or type(review) is not dict
            or any(pending.get(key) != event.get(key) for key in
                   ('clock_policy', 'sent_elapsed_time', 'expires_elapsed_time', 'candidate_sha256', 'native_report_sha256'))
            or ex._warning_digest(review) != event['delta_sha256']
            or {key: review.get(key) for key in event['warning_review']} != event['warning_review']
            or p.sha(path) != event['pending_sha256']):
        raise ValueError('Displayed updated-warning findings do not match the live challenge.')
    try: ex._warning_clock(pending, current=elapsed_time())
    except p.Rejected as exc: raise ValueError(str(exc)) from exc
    return review


def warning_review_text(event, expected_path):
    """Bound displayed findings to this challenge; the CLI still owns acceptance."""
    review = _warning_review_packet(event, expected_path)
    lines = ['Fresh validation reports different warning members on the same PCB.',
        'Review the changed items below. Both complete finding lists follow.',
        'This accepts the updated report for export; it is not electrical approval.',
        'The original export deadline includes this review. Expiry accepts no export.', '', 'Changed finding:']
    def describe(finding):
        rows = ['['+str(finding.get('severity', '?'))+'] '+str(finding.get('type', 'Finding'))+': '+str(finding.get('description', ''))]
        rows += ['  '+str(item.get('description', ''))+'  '+str(item.get('pos', ''))+'  UUID '+str(item.get('uuid', ''))
                 for item in finding.get('items', [])]
        return rows
    for title, key in [('Previously reported', 'previous'), ('Freshly reported', 'fresh')]:
        lines.append(title+':'); lines.extend(describe(review['delta'][key])); lines.append('')
    for title, key in [('Complete previous findings', 'previous_findings'), ('Complete fresh findings', 'fresh_findings')]:
        lines.append(title+':')
        for finding in review[key]: lines.extend(describe(finding)); lines.append('')
    value = '\n'.join(lines)
    if len(value.encode('utf-8')) > SUMMARY_LIMIT:
        raise ValueError('Updated findings exceed this dialog’s supported display size; no export accepted.')
    return value


def failed_export_detail(path):
    return failed_command_detail(path, 'Fresh export',
        'No exported project was accepted. Inspect the retained findings and failure log.')


def failed_export_check_detail(path):
    """Explain a failed CLI check without adopting any of its state."""
    try:
        record = read_record(path)
        if type(record) is not dict or record.get('current') is not False: return None
        text = short_failure_reason(record.get('reason'))
        if text is None: return None
        if record['reason'] == 'export inputs/runtime/evidence changed':
            text = 'The export, its inputs, runtime or saved evidence changed after validation.'
        return ('Checked export refused: ' + text +
                '\nStart a fresh preview using the intended saved project. Retained files were not reaccepted.' +
                '\nFull failure log: ' + str(path))
    except Exception:
        return None


def failed_route_detail(path):
    """Bounded diagnostic text only; never adopts a failed receipt as evidence."""
    try:
        record = read_record(path)
        if (type(record) is not dict or record.get('accepted') is not False
                or type(record.get('status')) is not str or not record['status'].strip()
                or record['status'] in ('routing_accepted', 'cancelled', 'canceled')):
            return None
        reason = record.get('reason') or record.get('error')
        text = short_failure_reason(reason)
        if text is None: return None
        return 'Routing refused: ' + text + '\nNo candidate accepted. Full failure receipt: ' + str(path)
    except Exception:
        return None


def improve_preset(config):
    """Choose compatible algorithm settings without replacing task constraints."""
    effective = pref.validate(config)
    candidate = dict(effective, profile='tuned', adapter='both')
    try:
        return check_improve_settings(candidate)
    except Exception as exc:
        raise ValueError('Improve requires whole-board unlocked routing, all source layers, Native guidance and at least 90 seconds. '
            + str(exc) + ' This is not a completion guarantee. Use Route for other tasks.') from exc


class CliJob:
    """One child CLI. Cancel requests SIGINT; its existing runner owns cleanup.

    Never SIGKILL a new process tree or claim descendant cleanup from UI polling.
    A cancelled invocation cannot authorize a positive UI outcome even at exit0.
    """
    def __init__(self):
        self.process = None
        self.cancel_requested = False
        self._lock = threading.Lock()
        self._warning_pending = None
        self._warning_decision = None
        self._action_started = None
        self._action_deadline = None
        self._action_process = None
        self._warning_expected_path = None
        self._warning_deadline = None
        self._deadline_error = None

    def reply_warning_review(self, event, decision):
        """Reply once to this live child's exact challenge; never adopt a result."""
        if decision not in ('accept_updated_findings', 'reject'):
            raise ValueError('Choose an explicit updated-findings decision.')
        with self._lock:
            self._check_warning_locked(event)
            value = dict(kind='autorouter.warning-review-response.v1', decision=decision,
                nonce=event['nonce'], pending_sha256=event['pending_sha256'], delta_sha256=event['delta_sha256'])
            self.process.stdin.write((json.dumps(value)+'\n').encode('utf-8'))
            self.process.stdin.flush(); self._warning_pending = None; self._warning_decision = decision
            self._warning_deadline = None  # A timely completed reply is no longer a pending challenge.

    def _check_warning_locked(self, event):
        self._check_deadline_locked(require_armed=True)
        if (self.cancel_requested or self.process is None or self.process.poll() is not None
                or self._warning_pending is None or event != self._warning_pending):
            raise ValueError('Warning review expired, changed or was cancelled; no acknowledgement sent.')
        _warning_review_packet(event, self._warning_expected_path)
        self._check_deadline_locked(require_armed=True)

    def _cancel_locked(self):
        if self.cancel_requested: return
        self.cancel_requested = True
        if self.process is not None and self.process.poll() is None:
            try: self.process.send_signal(signal.SIGINT)
            except ProcessLookupError: pass

    def _check_deadline_locked(self, *, require_armed=False):
        # Placement intake checks cancellation before run. An untouched job is
        # allowed there, but an injected process has no action authority.
        if self._action_started is None:
            if not require_armed and self.process is None: return
            self._cancel_locked()
            raise ValueError('No armed CLI action deadline; no positive state adopted.')
        try:
            now = elapsed_time()
            if (type(self._action_started) not in (int, float) or not math.isfinite(self._action_started)
                    or type(self._action_deadline) not in (int, float) or not math.isfinite(self._action_deadline)
                    or type(now) not in (int, float) or not math.isfinite(now) or now < 0
                    or self._action_process is not self.process or self.process is None
                    or not self._action_started <= now < self._action_deadline):
                raise ValueError('Action elapsed deadline expired or changed; no positive state adopted.')
            if self._warning_deadline is not None and (type(self._warning_deadline) not in (int, float)
                    or not math.isfinite(self._warning_deadline) or now >= self._warning_deadline):
                raise ValueError('The original warning-review elapsed deadline expired.')
        except Exception as exc:
            self._deadline_error = str(exc)
            self._cancel_locked()
            raise ValueError('CLI action deadline unavailable or expired; no positive state adopted.') from exc

    def check_warning_review(self, event):
        with self._lock: self._check_warning_locked(event)

    def cancel(self):
        with self._lock:
            self._cancel_locked()

    def check_live(self, *, require_armed=False):
        """A retained process snapshot cannot supersede a later Cancel."""
        with self._lock:
            if self.cancel_requested:
                if self._deadline_error is not None:
                    raise ValueError('Action timed out or its timing could not be verified. No result was adopted.')
                raise ValueError('Action was cancelled. No positive UI state adopted.')
            self._check_deadline_locked(require_armed=require_armed)

    def adopt(self, flow, stage, process, log_path, *, choice=None):
        self.check_live(require_armed=True)
        record = flow.adopt(stage, process, log_path, choice=choice)
        try:
            self.check_live(require_armed=True)
        except ValueError:
            flow.ready.clear(); flow.records.clear(); flow.choice = None
            raise
        return record

    def run(self, argv, log_path, *, timeout=165.0, on_warning_review=None):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 1000:
            raise ValueError('Finite GUI action watchdog required.')
        started = elapsed_time(); size = 0; truncated = False
        if (type(started) not in (int, float) or not math.isfinite(started) or started < 0
                or not math.isfinite(started + timeout) or started + timeout <= started):
            raise ValueError('Usable suspend-inclusive CLI action clock required.')
        live_review = on_warning_review is not None
        if live_review and (not callable(on_warning_review) or '--warning-review-stdio' not in argv):
            raise ValueError('Explicit live warning-review command and handler required.')
        lines = b''; warning_seen = False
        with log_path.open('xb') as log:
            with self._lock:
                if self.cancel_requested: raise ValueError('Cancelled before process startup.')
                if self.process is not None and self.process.poll() is None:
                    raise ValueError('The previous CLI action is still running.')
                self._warning_pending = None
                self._warning_decision = None
                self._action_started = started
                self._action_deadline = started + timeout
                self._action_process = None
                self._warning_expected_path = log_path.parent/'export/warning-review.json'
                self._warning_deadline = None
                self._deadline_error = None
                self.process = subprocess.Popen(argv, cwd=c.ROOT, stdin=subprocess.PIPE if live_review else subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=child_environment())
                self._action_process = self.process
            # An awake-clock Timer(timeout) may have most of its wait left after
            # host sleep. Poll the absolute action clock while stdout is silent;
            # this finite owned watchdog is stopped and joined before run exits.
            watch_stopped = None; deadline = None; deadline_started = False
            try:
                watch_stopped = threading.Event()
                def watch_deadline():
                    while not watch_stopped.wait(0.1):
                        with self._lock:
                            if self.cancel_requested: return
                            try: self._check_deadline_locked(require_armed=True)
                            except ValueError: return
                deadline = threading.Timer(0, watch_deadline)
                deadline.daemon = True; deadline.start(); deadline_started = True
                while True:
                    chunk = self.process.stdout.read1(8192)
                    if not chunk: break
                    retained = chunk[:max(0, LOG_LIMIT-size)]
                    log.write(retained); log.flush(); size += len(retained)
                    if len(retained) != len(chunk):
                        truncated = True; self.cancel()
                    if live_review and not truncated:
                        lines += chunk
                        while b'\n' in lines:
                            line, _, lines = lines.partition(b'\n')
                            if len(line) > 64*1024: raise ValueError('Warning-review message exceeds64KiB.')
                            try: event = json.loads(line)
                            except ValueError: continue
                            if type(event) is not dict or event.get('kind') != 'autorouter.warning-review-required.v1': continue
                            expected = log_path.parent/'export/warning-review.json'
                            from . import review_export as ex
                            if (warning_seen or Path(event.get('pending', '')) != expected
                                    or type(event.get('warning_review')) is not dict
                                    or type(event.get('nonce')) is not str or len(event['nonce']) != 32
                                    or any(x not in '0123456789abcdef' for x in event['nonce'])
                                    or any(type(event.get(k)) is not str or len(event[k]) != 64
                                           or any(x not in '0123456789abcdef' for x in event[k])
                                           for k in ('pending_sha256', 'delta_sha256'))
                                    or not ex.finite(event.get('remaining_seconds'))
                                    or not 0 < event['remaining_seconds'] <= ex.SECONDS):
                                raise ValueError('Invalid or repeated live warning-review challenge.')
                            with self._lock:
                                if self.cancel_requested: raise ValueError('Warning review was cancelled.')
                                self._check_deadline_locked(require_armed=True)
                                _warning_review_packet(event, expected)
                                self._warning_deadline = event['expires_elapsed_time']
                                self._check_deadline_locked(require_armed=True)
                                self._warning_pending = copy.deepcopy(event)
                            warning_seen = True; on_warning_review(copy.deepcopy(event))
                        if len(lines) > 64*1024: raise ValueError('Warning-review message exceeds64KiB.')
                code = self.process.wait()
                with self._lock:
                    try: self._check_deadline_locked(require_armed=True)
                    except ValueError: pass  # Retain a refused/cancelled process receipt below.
                if warning_seen and code == 0 and self._warning_decision != 'accept_updated_findings':
                    raise ValueError('Live export exited without explicit updated-findings acknowledgement.')
            except BaseException:
                self.cancel()
                self.process.stdout.close()
                self.process.wait()
                raise
            finally:
                if watch_stopped is not None: watch_stopped.set()
                if deadline is not None: deadline.cancel()
                if deadline_started: deadline.join()
                self.process.stdout.close()
                if live_review: self.process.stdin.close()
                self._warning_pending = None
        with self._lock:
            try: self._check_deadline_locked(require_armed=True)
            except ValueError: pass
        wall = elapsed_time()-started
        if not math.isfinite(wall) or wall < 0:
            raise ValueError('CLI action elapsed accounting is unavailable; no positive state adopted.')
        result = dict(argv=argv, exit_code=code, cancel_requested=self.cancel_requested,
                      log_truncated=truncated, log_bytes=size,
                      wall_seconds=wall, clock_policy=ELAPSED_CLOCK_POLICY,
                      deadline_elapsed_time=self._action_deadline, deadline_error=self._deadline_error,
                      cleanup_scope='CLI existing workers; UI does not certify descendant cleanup')
        with log_path.with_suffix('.process.json').open('x') as stream:
            json.dump(result, stream, indent=2); stream.write('\n')
        return result


def launch_gui(source_hint=''):
    """Tiny KiCad action: spawn only; expensive work stays outside the editor."""
    argv = [str(c.PYTHON), '-B', '-m', 'autorouter.gui']
    if source_hint: argv += ['--board', str(source_hint)]
    return subprocess.Popen(argv, cwd=c.ROOT, env=child_environment(),
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def register_kicad_action():
    """Legacy compatibility only; not the product IPC packaging entry point."""
    import pcbnew
    class SeparateProjectRouter(pcbnew.ActionPlugin):
        def defaults(self):
            self.name = 'Autorouter: separate project'
            self.category = 'External tools'
            self.description = 'Launch offline routing and separate-project review; save and close source editors first.'
            self.show_toolbar_button = False
        def Run(self):
            board = pcbnew.GetBoard()
            launch_gui(str(board.GetFileName()) if board is not None else '')
    plugin = SeparateProjectRouter(); plugin.register()
    _REGISTERED_ACTIONS.append(plugin)
    return plugin


def _finish_window_close(window):
    """Notify a composing parent once, after all owned cleanup scopes end."""
    if (not window.closing or window.busy
            or any(getattr(window, name, None) is not None
                   for name in ('chooser', 'warning_dialog', 'placement_window'))
            or getattr(window, '_close_finalized', False)):
        return False
    window._close_finalized = True
    window.timer.Stop(); window.Destroy()
    callback = getattr(window, '_on_closed', None)
    if callback is not None:
        import wx
        wx.CallAfter(callback)
    return True


def create_window(board='', *, source_guard=None, on_closed=None):
    """Create one unshown routing frame in an existing wx application.

    The caller owns showing the frame and the application loop. This does not
    launch routing, adopt approval, replace signal handlers or nest a wx.App.
    """
    if on_closed is not None and not callable(on_closed):
        raise ValueError('The parent close notification must be a callable.')
    try: import wx
    except ImportError as exc:
        raise SystemExit('wx is unavailable. Launch with the pinned KiCad bundled Python; no packages were installed.') from exc
    if wx.GetApp() is None:
        raise ValueError('Create the wx application before opening routing controls.')
    if threading.current_thread() is not threading.main_thread():
        raise ValueError('Open routing controls on the application main thread.')
    if not isinstance(board, (str, Path)):
        raise ValueError('Use an exact saved PCB path or an empty path hint.')
    board = str(board)
    _check_source_guard(source_guard, board)
    class Window(wx.Frame):
        def __init__(self):
            super().__init__(None, title='KiCad design assistant — routing', size=(820, 780))
            self.flow = None; self.job = None; self.busy = False; self.closing = False
            self._on_closed = on_closed; self._close_finalized = False
            self.source_guard = source_guard
            self.warning_dialog = None
            self.chooser = None; self.input_generation = 0
            self.placement_window = None
            self.edit_controls = []
            panel = wx.ScrolledWindow(self); panel.SetScrollRate(0, 12)
            layout = wx.BoxSizer(wx.VERTICAL)
            heading = wx.StaticText(panel, label='Route a saved project')
            heading.SetFont(heading.GetFont().Bold())
            task_row = wx.BoxSizer(wx.HORIZONTAL)
            task_row.Add(heading, 1, wx.ALIGN_CENTER_VERTICAL)
            self.placement_button = wx.Button(panel, label='Place components…')
            self.placement_button.Bind(wx.EVT_BUTTON, self.open_placement)
            task_row.Add(self.placement_button, 0)
            layout.Add(task_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 12)
            layout.Add(wx.StaticText(panel, label='Inspect your board, choose what to preserve, then review a separate candidate.'),
                       0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 12)
            self.board = self.path_row(panel, layout, 'Saved PCB', board, False)
            self.output = self.path_row(panel, layout, 'Output folder', str(c.ROOT / '.runs'), True)
            self.values = {
                'scope': [('Reroute unlocked; keep locked copper', 'whole_board_unlocked_routing'), ('Finish gaps; keep all existing copper', 'partial_completion'), ('Selected nets; keep other copper', 'selected_nets')],
                'profile': [('Standard', 'standard'), ('More search', 'tuned'), ('Completion only', 'completion-only')],
                'adapter': [('Both corrections', 'both'), ('Stock interchange', 'none'), ('Graphics correction', 'graphics'), ('Plane correction', 'planes')],
                'layers': [('All source copper', 'source_all'), ('Front only', ['F.Cu']), ('Back only', ['B.Cu']), ('Front and back', ['F.Cu', 'B.Cu'])],
                'scoring_preference': [('Engine default', None), ('Default via cost', 'via_default'), ('Lower via cost', 'via_low'), ('Higher via cost', 'via_high')]}
            grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=10); grid.AddGrowableCol(1)
            self.advanced = wx.CollapsiblePane(panel, label='Advanced routing and experiments')
            advanced = self.advanced.GetPane(); advanced_layout = wx.BoxSizer(wx.VERTICAL)
            advanced_grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=10); advanced_grid.AddGrowableCol(1)
            advanced_grid.Add(wx.StaticText(advanced, label='Method'), 0, wx.ALIGN_CENTER_VERTICAL)
            self.method = wx.Choice(advanced, choices=['Route', 'Improve (experimental; tuned whole-board preset)',
                'Thermal recovery (experimental; fixed whole-board method)'])
            self.method.SetSelection(0); self.method.Bind(wx.EVT_CHOICE, self.method_changed)
            self.edit_controls.append(self.method); advanced_grid.Add(self.method, 1, wx.EXPAND)
            self.choices = {}
            for name, label in [('scope', 'Routing and protection'), ('profile', 'Routing profile'), ('adapter', 'Interchange corrections'), ('layers', 'Allowed new copper'), ('scoring_preference', 'Via preference')]:
                host, target_grid = (panel, grid) if name == 'scope' else (advanced, advanced_grid)
                target_grid.Add(wx.StaticText(host, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
                control = wx.Choice(host, choices=[label for label, _ in self.values[name]])
                control.SetSelection(next(i for i, (_, value) in enumerate(self.values[name]) if value == pref.DEFAULTS[name])); control.Bind(wx.EVT_CHOICE, self.changed)
                self.choices[name] = control; self.edit_controls.append(control); target_grid.Add(control, 1, wx.EXPAND)
            self.budget_label = wx.StaticText(panel, label='Routing budget (seconds)')
            grid.Add(self.budget_label, 0, wx.ALIGN_CENTER_VERTICAL)
            # Cocoa SpinCtrl clamps invalid text on focus loss before Preview
            # can validate it. Keep the exact input until explicit validation.
            self.seconds = wx.TextCtrl(panel, value=str(int(pref.DEFAULTS['seconds'])))
            self.seconds.Bind(wx.EVT_TEXT, self.changed)
            self.edit_controls.append(self.seconds); grid.Add(self.seconds)
            grid.Add(wx.StaticText(panel, label='Selected nets (one exact name per line)'), 0, wx.ALIGN_CENTER_VERTICAL)
            self.nets = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 55))
            self.nets.Bind(wx.EVT_TEXT, self.changed); self.edit_controls.append(self.nets); grid.Add(self.nets, 1, wx.EXPAND)
            layout.Add(grid, 0, wx.EXPAND | wx.ALL, 8)
            advanced_layout.Add(advanced_grid, 0, wx.EXPAND | wx.ALL, 8)
            self.method_note = wx.StaticText(advanced, label='')
            self.method_note.Wrap(780)
            advanced_layout.Add(self.method_note, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            export_note = wx.StaticText(advanced, label='Rendered review is bounded to 60 seconds; accept/reject checks to 60 seconds. '
                'These are separate from the routing budget. Fresh export adds Native validation after acceptance: '
                '30–120 seconds, derived from the captured routing or whole-method budget. That budget is unchanged.')
            export_note.Wrap(780)
            advanced_layout.Add(export_note, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            advanced.SetSizer(advanced_layout); layout.Add(self.advanced, 0, wx.EXPAND | wx.ALL, 8)
            presets = wx.BoxSizer(wx.HORIZONTAL)
            for label, callback in [('Load settings…', self.load_preset), ('Save settings as…', self.save_preset),
                                    ('Completion search (may add vias)', self.completion_preset)]:
                button = wx.Button(panel, label=label); button.Bind(wx.EVT_BUTTON, callback)
                presets.Add(button, 0, wx.ALL, 4); self.edit_controls.append(button)
            layout.Add(presets)
            self.assistant = wx.CollapsiblePane(panel, label='Optional local assistant')
            assistant_panel = self.assistant.GetPane(); assistant_layout = wx.BoxSizer(wx.VERTICAL)
            assistant_layout.Add(wx.StaticText(assistant_panel, label='Inspect first. Describe a routing request, then review the proposed settings. No automatic approval.'),
                                 0, wx.ALL, 6)
            self.intent_text = wx.TextCtrl(assistant_panel, style=wx.TE_MULTILINE, size=(-1, 55))
            assistant_layout.Add(self.intent_text, 0, wx.EXPAND | wx.ALL, 6)
            self.model_config = self.path_row(assistant_panel, assistant_layout, 'Local model settings JSON', '', False,
                                              wildcard='JSON settings (*.json)|*.json')
            self.model_config.SetHint('Path to an explicit local model settings .json file')
            assistant_buttons = wx.BoxSizer(wx.HORIZONTAL)
            self.suggest_button = wx.Button(assistant_panel, label='Suggest settings')
            self.suggest_button.Bind(wx.EVT_BUTTON, self.suggest_settings)
            self.apply_proposal_button = wx.Button(assistant_panel, label='Use proposed settings')
            self.apply_proposal_button.Bind(wx.EVT_BUTTON, self.apply_proposal)
            for button in (self.suggest_button, self.apply_proposal_button): assistant_buttons.Add(button, 0, wx.ALL, 4)
            assistant_layout.Add(assistant_buttons)
            assistant_panel.SetSizer(assistant_layout); layout.Add(self.assistant, 0, wx.EXPAND | wx.ALL, 8)
            self.pending_proposal = None; self.inspection_path = None
            self.edit_controls.extend((self.intent_text, self.model_config, self.suggest_button))
            for control in (self.intent_text, self.model_config): control.Bind(wx.EVT_TEXT, self.proposal_inputs_changed)
            for pane in (self.advanced, self.assistant):
                pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, lambda event: (panel.Layout(), panel.FitInside(), event.Skip()))
            self.ack = wx.CheckBox(panel, label='I saved and CLOSED the source PCB and schematic editors. The exact paths above are correct.')
            layout.Add(self.ack, 0, wx.ALL, 6)
            self.inspected = wx.CheckBox(panel, label='I inspected all findings and CLOSED the review editors/project. My choice is intent, not PCB certification.')
            layout.Add(self.inspected, 0, wx.ALL, 6)
            self.buttons = {}
            for names in ((('Inspect project', 'inspect'), ('Preview', 'preview'), ('Route', 'route'), ('Create review', 'review'), ('Cancel', 'cancel')),
                          (('Open preview', 'open_preview'), ('Open review project', 'open_review')),
                          (('Accept intent', 'accept'), ('Reject intent', 'reject'), ('Fresh export', 'export'), ('Open checked export', 'open_export'))):
                row = wx.BoxSizer(wx.HORIZONTAL)
                for label, name in names:
                    button = wx.Button(panel, label=label)
                    button.Bind(wx.EVT_BUTTON, lambda event, action=name: self.act(action))
                    self.buttons[name] = button; row.Add(button, 0, wx.ALL, 4)
                layout.Add(row, 0, wx.ALL, 2)
            self.status = wx.StaticText(panel, label='Select a complete saved project; preview support before routing. Source buffers cannot be inspected.')
            layout.Add(self.status, 0, wx.EXPAND | wx.ALL, 6)
            self.log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 150))
            layout.Add(self.log, 1, wx.EXPAND | wx.ALL, 6)
            panel.SetSizer(layout)
            for control in (self.board, self.output): control.Bind(wx.EVT_TEXT, self.path_changed)
            self.Bind(wx.EVT_CLOSE, self.close)
            self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.tick, self.timer); self.timer.Start(500)
            self.refresh()

        def open_placement(self, _):
            """One task window at a time; routing and placement share this app."""
            if self.busy or self.closing or getattr(self, 'chooser', None) is not None: return
            if self.source_guard is not None:
                self.status.SetLabel('Finish or reject this bound placement candidate before starting another placement task.')
                return
            if self.placement_window is not None:
                self.placement_window.Raise(); return
            try:
                from . import placement_gui
                def finished():
                    self.placement_window = None
                    if self.closing: self.Close()
                    else: self.Show(); self.Raise()
                frame = placement_gui.create_window(self.board.GetValue(), output_hint=self.output.GetValue(), on_closed=finished)
                self.placement_window = frame
                frame.Show(); self.Hide()
            except Exception as exc:
                self.status.SetLabel('Placement controls could not open: ' + str(exc))
                self.Show()

        def path_row(self, panel, layout, label, value, directory, *, wildcard=None):
            row = wx.BoxSizer(wx.HORIZONTAL); row.Add(wx.StaticText(panel, label=label), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            control = wx.TextCtrl(panel, value=value); row.Add(control, 1, wx.ALL, 6)
            button = wx.Button(panel, label='Browse…')
            def browse(_):
                if self.busy or self.chooser is not None: return
                dialog = wx.DirDialog(self, 'Choose output folder') if directory else wx.FileDialog(self,
                    'Choose ' + label if wildcard else 'Choose saved PCB',
                    wildcard=wildcard or 'KiCad PCB (*.kicad_pcb)|*.kicad_pcb', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
                self.choose_path(dialog, control.SetValue)
            button.Bind(wx.EVT_BUTTON, browse); self.edit_controls.append(button)
            row.Add(button, 0, wx.ALL, 6); layout.Add(row, 0, wx.EXPAND)
            return control

        def path_changed(self, event):
            # The acknowledgement names these exact paths. Typing and Browse
            # both emit EVT_TEXT; routing-only settings keep this source intent.
            self.ack.SetValue(False)
            self.changed(event)

        def changed(self, event):
            self.input_generation = getattr(self, 'input_generation', 0) + 1
            self.pending_proposal = None
            if not self.busy:
                previous_workspace = self.flow.workspace if self.flow is not None else None
                self.flow = None; self.inspected.SetValue(False)
                self.status.SetLabel('Inputs changed. Preview the saved project to start a new job.')
                self.log.SetValue('Inputs changed. Preview the saved project to start a new job.\n'
                    'Previous findings are no longer current for these inputs. Retained workspaces were not deleted.'
                    + ('\nPrevious workspace: ' + str(previous_workspace) if previous_workspace is not None else ''))
            self.refresh(); event.Skip()

        def proposal_inputs_changed(self, event):
            self.pending_proposal = None
            self.refresh(); event.Skip()

        def suggest_settings(self, _):
            if self.busy or self.chooser is not None: return
            try:
                if not self.inspection_path:
                    raise ValueError('Use Inspect project first to get actual saved-project findings.')
                if not self.model_config.GetValue().strip():
                    raise ValueError('No application model is configured. Use the ordinary routing controls, or choose explicit local model settings.')
                if method_for_index(self.method.GetSelection()) != 'route':
                    raise ValueError('The assistant proposes Route settings. Select Route first.')
                request_text = self.intent_text.GetValue()
                config_path = self.model_config.GetValue()
                inspection_path = self.inspection_path
                request = Request(self.board.GetValue(), self.output.GetValue(), json.dumps(self.config()), self.ack.GetValue(),
                                  source_guard=getattr(self, 'source_guard', None))
                if request.saved_closed is not True:
                    raise ValueError('Save and close source editors, then acknowledge the exact source.')
                self.pending_proposal = None
                self.busy = True; self.job = CliJob(); job = self.job; self.refresh()
                job.proposal_generation = self.input_generation
                self.status.SetLabel('Preparing one local model request. No route or approval can be performed by the model.')
                def work():
                    flow = None
                    try:
                        from . import project_inspection, model_intent
                        from .placement_clearance import read_bytes
                        inspected = project_inspection.check(inspection_path)
                        if inspected['source'] != str(canonical(request.board)):
                            raise ValueError('Inspection belongs to another project. Inspect the selected source.')
                        config = pref._parse(read_bytes(canonical(config_path), 16384), 16384)
                        model_intent._config(config)
                        flow = request.prepare(); flow.fresh()
                        text_path = flow.workspace / 'request.txt'
                        if not 0 < len(request_text.encode('utf-8')) <= model_intent.MAX_REQUEST_TEXT:
                            raise ValueError('Enter a routing request within 4096 UTF-8 bytes.')
                        with text_path.open('x') as stream: stream.write(request_text)
                        config_copy = flow.workspace / 'model-settings.json'
                        with config_copy.open('x') as stream: json.dump(config, stream)
                        argv = [str(c.ROOT / '.venv/bin/python'), '-B', '-m', 'autorouter',
                            'propose-route', str(flow.board), '--inspection', str(inspection_path),
                            '--request-file', str(text_path), '--model-config', str(config_copy)]
                        log = flow.workspace / 'proposal.command.log'
                        process = job.run(argv, log, timeout=45)
                        job.check_live(); flow.fresh()
                        if process['exit_code'] != 0 or process['cancel_requested'] or process['log_truncated']:
                            raise ValueError('Proposal was refused or cancelled. Read the retained proposal log; ordinary controls remain available.')
                        result = read_record(log)
                        from .design_intent import validate_route_proposal
                        checked = validate_route_proposal(inspected['static'], result['proposal']['intent'])
                        if checked != result['proposal']:
                            raise ValueError('Returned proposal differs from shared validation.')
                        wx.CallAfter(self.proposal_finished, job, flow, inspected['static'], result, None)
                    except Exception as exc:
                        retained = ' Retained workspace: ' + str(flow.workspace) if flow else ''
                        wx.CallAfter(self.proposal_finished, job, flow, None, None, str(exc) + retained)
                threading.Thread(target=work, daemon=False).start()
            except Exception as exc: self.refused(str(exc))

        def proposal_finished(self, job, flow, inspection, result, error):
            if self.job is not job: return
            try:
                job.check_live()
                if error: raise ValueError(error)
                if job.proposal_generation != self.input_generation:
                    raise ValueError('Settings changed while preparing the proposal; request it again.')
                _window_source_guard(self, flow)
                flow.fresh()
                from .design_intent import validate_route_proposal
                proposal = validate_route_proposal(inspection, result['proposal']['intent'])
                if proposal != result['proposal']: raise ValueError('Proposal changed before display.')
                self.pending_proposal = (inspection, proposal, self.input_generation)
                self.log.SetValue('PROPOSED SETTINGS — no route or approval has run.\n\n'
                    + human_summary('preview', proposal['preview'])
                    + '\n\nModel request metrics: ' + json.dumps(result['metrics'], sort_keys=True))
                self.status.SetLabel('Review the proposal. Use proposed settings only if they match your intent; Preview and Route remain separate actions.')
            except Exception as exc:
                self.pending_proposal = None; self.log.SetValue(str(exc))
                self.status.SetLabel('No proposal adopted. Ordinary routing controls remain available.')
            self.busy = False; self.job = None; self.refresh()
            if self.closing: _finish_window_close(self)

        def apply_proposal(self, _):
            if self.busy or self.chooser is not None or self.pending_proposal is None: return
            try:
                _check_source_guard(getattr(self, 'source_guard', None), self.board.GetValue())
                from .design_intent import validate_route_proposal
                inspection, proposal, generation = self.pending_proposal
                if generation != self.input_generation or method_for_index(self.method.GetSelection()) != 'route':
                    raise ValueError('Settings or method changed; request a new proposal.')
                if canonical(self.board.GetValue()) != Path(proposal['source']):
                    raise ValueError('Selected source changed; inspect and request a new proposal.')
                checked = validate_route_proposal(inspection, proposal['intent'])
                if checked != proposal: raise ValueError('Proposal changed before applying settings.')
                settings = checked['effective_preferences']
                indices = {name: next(i for i, (_, value) in enumerate(self.values[name]) if value == settings[name])
                           for name in self.choices}
                self.method.SetSelection(0)
                for name, index in indices.items(): self.choices[name].SetSelection(index)
                self.seconds.SetValue(str(settings['seconds']))
                self.nets.SetValue('\n'.join(settings.get('nets', [])))
                self.input_generation += 1; self.flow = None; self.inspected.SetValue(False)
                self.pending_proposal = None
                self.status.SetLabel('Proposed settings applied. Review the visible choices, then Preview and Route. No run or candidate was approved.')
                self.log.SetValue(human_summary('preview', checked['preview']))
                self.refresh()
            except Exception as exc: self.refused(str(exc))

        def choose_path(self, dialog, on_path):
            """Retain an asynchronous native sheet until its completion event.

            A nested Cocoa ShowModal loop can still dispatch input while starving
            our deferred worker completion. Never start a worker behind a picker.
            """
            if self.busy or self.chooser is not None:
                dialog.Destroy(); return
            lease = (dialog, self.input_generation)
            self.chooser = lease; self.refresh()

            def dispose():
                dialog.Unbind(wx.EVT_WINDOW_MODAL_DIALOG_CLOSED, handler=completed)
                dialog.Destroy()
                if self.closing: _finish_window_close(self)
                else: self.refresh()

            def completed(event):
                if self.chooser is not lease or event.GetDialog() is not dialog: return
                self.chooser = None
                try:
                    if not self.closing and event.GetReturnCode() == wx.ID_OK:
                        if self.input_generation != lease[1]: raise ValueError('Inputs changed while choosing a path; choose again.')
                        on_path(dialog.GetPath())
                except Exception as exc: self.refused(str(exc))
                finally: dispose()

            def show():
                if self.chooser is not lease: return
                if self.closing:
                    self.chooser = None; dispose(); return
                try: dialog.ShowWindowModal()
                except Exception as exc:
                    self.chooser = None; self.refused(str(exc)); dispose()

            dialog.Bind(wx.EVT_WINDOW_MODAL_DIALOG_CLOSED, completed)
            wx.CallAfter(show)

        def refused(self, error):
            self.pending_proposal = None
            if self.flow is not None:
                self.flow.ready.clear(); self.flow.records.clear(); self.flow.choice = None
            self.flow = None; self.inspected.SetValue(False)
            self.status.SetLabel('Action refused or cancelled. Read the findings below; start a fresh preview.')
            self.log.SetValue(str(error) + '\nNo positive state adopted. Retained files were not deleted.')
            self.refresh()

        def method_changed(self, event):
            self.input_generation = getattr(self, 'input_generation', 0) + 1
            self.pending_proposal = None
            if getattr(self, 'chooser', None) is not None: event.Skip(); return
            if self.busy: event.Skip(); return
            self.flow = None; self.inspected.SetValue(False)
            try:
                method = method_for_index(self.method.GetSelection())
                if method == 'improve':
                    settings = improve_preset(self.config())
                    for name in ('profile', 'adapter'):
                        self.choices[name].SetSelection(next(i for i, (_, value) in enumerate(self.values[name]) if value == settings[name]))
                    self.status.SetLabel('Improve selected: tuned profile and both corrections. Routing protection, layers, budget and via preference are unchanged.')
                elif method == 'recover':
                    self.status.SetLabel('Thermal recovery selected explicitly. Set the required whole-board settings; Preview refuses incompatible inputs without changing them.')
                if hasattr(self, 'budget_label'):
                    self.budget_label.SetLabel('Whole recovery-method budget (seconds)' if method == 'recover'
                        else 'Whole Improve-method budget (seconds)' if method == 'improve' else 'Routing budget (seconds)')
                    self.method_note.SetLabel(THERMAL_HELP if method == 'recover' else IMPROVE_HELP if method == 'improve' else '')
                    self.method_note.Wrap(780)
                    self.method_note.GetParent().Layout()
                if hasattr(self, 'buttons'):
                    self.buttons['route'].SetLabel('Recover (experimental)' if method == 'recover' else 'Route')
            except Exception as exc:
                self.refused(str(exc))
                # Cocoa commits the popup selection after this callback.
                # Reset afterwards, without nesting a modal inside its menu loop.
                wx.CallAfter(self.method.SetSelection, 0)
            self.refresh(); event.Skip()

        def completion_preset(self, _):
            if self.busy or getattr(self, 'chooser', None) is not None: return
            self.pending_proposal = None
            try:
                if method_for_index(self.method.GetSelection()) != 'route':
                    raise ValueError('Completion search is a Route preset. Select Route first.')
                config = completion_search_preset(self.config())
                for name in ('profile', 'scoring_preference'):
                    self.choices[name].SetSelection(next(i for i, (_, value) in enumerate(self.values[name])
                                                        if value == config[name]))
                self.input_generation += 1
                self.flow = None; self.inspected.SetValue(False)
                self.status.SetLabel('Completion search selected: more search that may use more vias. '
                    'Scope, copper protection, layers and budget are preserved. Preview the saved project.')
                self.log.SetValue('Settings changed. Earlier findings are no longer current. '
                    'Preview the saved project before routing; retained workspaces were not deleted.')
                self.method_note.SetLabel('Completion search initially supports canonical two-layer boards '
                    'with one Default netclass and a complete flat schematic. It is a routing preference, '
                    'not a completion guarantee or electrical approval. Save settings to reuse it.')
                self.method_note.Wrap(780); self.method_note.GetParent().Layout()
                self.refresh()
            except Exception as exc:
                self.refused(str(exc))

        def load_preset(self, _):
            if self.busy or getattr(self, 'chooser', None) is not None: return
            self.pending_proposal = None
            def loaded(path):
                config = pref.resolve(pref.load(path))
                if config['guidance'] != 'native': raise ValueError('This graphical workflow supports Native guidance; retain other presets for their documented CLI.')
                if config['seconds'] != int(config['seconds']): raise ValueError('This graphical control uses whole seconds; use the CLI for fractional budgets.')
                method = method_for_index(self.method.GetSelection())
                if method == 'improve': check_improve_settings(config)
                if method == 'recover': check_thermal_settings(config)
                indices = {name: next(i for i, (_, value) in enumerate(self.values[name]) if value == config[name]) for name in self.choices}
                for name, control in self.choices.items(): control.SetSelection(indices[name])
                self.seconds.SetValue(str(int(config['seconds']))); self.nets.SetValue('\n'.join(config.get('nets', [])))
                self.flow = None; self.inspected.SetValue(False)
                self.status.SetLabel('Settings loaded. Preview the saved project to start a new job.')
                self.log.SetValue('Settings loaded. Preview the saved project to start a new job.')
                self.refresh()
            self.choose_path(wx.FileDialog(self, 'Load explicit settings', wildcard='JSON (*.json)|*.json', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST), loaded)

        def config(self):
            result = dict(pref.DEFAULTS)
            for name, control in self.choices.items(): result[name] = self.values[name][control.GetSelection()][1]
            raw_seconds = self.seconds.GetValue().strip()
            if not raw_seconds.isascii() or not raw_seconds.isdecimal():
                raise ValueError('Enter a whole-number routing budget from 5 to 900 seconds.')
            result['seconds'] = int(raw_seconds)
            if result['scope'] == 'selected_nets': result['nets'] = [name for name in self.nets.GetValue().splitlines() if name]
            return pref.validate(result)

        def save_preset(self, _):
            if self.busy or getattr(self, 'chooser', None) is not None: return
            try:
                config = self.config()
                source_text = self.board.GetValue()
                def saved(path):
                    if self.config() != config or self.board.GetValue() != source_text: raise ValueError('Settings/source changed while choosing; save again.')
                    target = canonical(path, exists=False)
                    if target.suffix != '.json': raise ValueError('Use a new .json settings filename.')
                    if self.board.GetValue():
                        source = canonical(self.board.GetValue())
                        if target.parent == source.parent or source.parent in target.parents: raise ValueError('Save settings outside the original project.')
                    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as stream:
                        json.dump(config, stream, indent=2); stream.write('\n')
                    self.status.SetLabel('Settings saved: ' + str(target) + '. Preview uses the current displayed settings.')
                self.choose_path(wx.FileDialog(self, 'Save NEW settings JSON', defaultFile='routing-settings.json', wildcard='JSON (*.json)|*.json', style=wx.FD_SAVE), saved)
            except Exception as exc: self.refused(str(exc))

        def refresh(self):
            choosing = getattr(self, 'chooser', None) is not None
            if hasattr(self, 'placement_button'):
                self.placement_button.Enable(not self.busy and not choosing and self.source_guard is None)
            ready = self.flow.ready if self.flow else set()
            allowed = {'inspect': True, 'preview': True, 'route': 'preview' in ready and 'route' not in ready,
                'review': 'route' in ready and 'review' not in ready,
                'open_preview': 'review' in ready, 'open_review': 'review' in ready,
                'accept': 'review' in ready and 'choice' not in ready,
                'reject': 'review' in ready and 'choice' not in ready,
                'export': 'choice' in ready and 'export' not in ready and self.flow.choice == 'accept' if self.flow else False,
                'open_export': 'verify_export' in ready}
            for name, button in self.buttons.items(): button.Enable(not choosing and (self.busy if name == 'cancel' else not self.busy and allowed.get(name, False)))
            for control in (self.board, self.output, self.ack, self.inspected, *self.edit_controls): control.Enable(not self.busy and not choosing)
            if hasattr(self, 'apply_proposal_button'):
                self.apply_proposal_button.Enable(not self.busy and not choosing and self.pending_proposal is not None)

        def act(self, action):
            try:
                if getattr(self, 'chooser', None) is not None: return
                if action == 'cancel': self.job.cancel(); self.status.SetLabel('Cancellation requested; waiting for the CLI worker to finish cleanup.'); return
                if self.busy: return
                if action.startswith('open_'):
                    kind = action.removeprefix('open_'); flow = self.flow
                    self.busy = True; self.job = CliJob(); self.refresh()
                    label = {'preview': 'preview', 'review': 'review project', 'export': 'export'}[kind]
                    self.status.SetLabel('Checking retained ' + label + ' before opening. Cancel remains available.')
                    job = self.job
                    def inspect():
                        try:
                            target = flow.inspect_path(kind, job=job)
                            job.check_live()
                            wx.CallAfter(self.opened, kind, target, None)
                        except Exception as exc: wx.CallAfter(self.opened, kind, None, str(exc))
                    threading.Thread(target=inspect, daemon=False).start()
                    return
                if action == 'accept' and not self.inspected.GetValue():
                    self.status.SetLabel('Inspect and close the review project, then acknowledge review intent.')
                    self.log.SetValue('Inspect the disposable project and findings, close its editors and use File > Close Project, then check the review acknowledgement.\nThe existing route/review is retained; no acceptance or export was adopted.')
                    self.refresh(); return
                if action == 'accept':
                    from .handoff import ReviewProjectOpen
                    try: review_close_hint(self.flow.workspace)
                    except ReviewProjectOpen as exc:
                        # A recoverable close-project precondition must not discard
                        # the valid route/review and force another routing attempt.
                        self.inspected.SetValue(False)
                        self.status.SetLabel('Close the review project, then acknowledge and retry Accept intent.')
                        self.log.SetValue(str(exc) + '\nThe existing route/review is retained; no acceptance or export was adopted.')
                        self.refresh(); return
                choice = action if action in ('accept', 'reject') else None
                stage = 'choice' if choice else action
                if stage in ('preview', 'review'): self.inspected.SetValue(False)
                request = _window_request(self)
                if self.ack.GetValue() is not True: raise ValueError('Save and close source editors, then acknowledge the exact paths.')
                self.busy = True; self.job = CliJob(); job = self.job; self.refresh()
                self.status.SetLabel('Preparing ' + stage + ' outside KiCad; all outputs stay separate.')
                def work():
                    flow = None
                    try:
                        flow = request.prepare() if stage in ('preview', 'inspect') else self.flow
                        flow.check_request(request)
                        argv = flow.command(stage, choice=choice)
                        log_path = flow.workspace / (stage + '.command.log')
                        options = {}
                        if stage == 'export':
                            argv += ['--warning-review-stdio']
                            options['on_warning_review'] = lambda event: wx.CallAfter(self.review_updated_warnings, job, flow, event)
                        process = job.run(argv, log_path, timeout=flow.timeout(stage), **options)
                        record = job.adopt(flow, stage, process, log_path, choice=choice)
                        if stage == 'export':
                            stage2 = 'verify_export'; argv = flow.command(stage2)
                            log2 = flow.workspace / (stage2 + '.command.log')
                            process = job.run(argv, log2, timeout=flow.timeout(stage2)); record = job.adopt(flow, stage2, process, log2)
                        job.check_live()
                        wx.CallAfter(self.finished, job, flow, stage, record, None)
                    except Exception as exc:
                        retained = ' Retained workspace: ' + str(flow.workspace) if flow else ''
                        wx.CallAfter(self.finished, job, None, stage, None, str(exc) + retained)
                threading.Thread(target=work, daemon=False).start()
            except Exception as exc: self.refused(str(exc))

        def review_updated_warnings(self, job, flow, event):
            if self.job is not job or self.closing: return
            dialog = None
            try:
                job.check_warning_review(event); flow.fresh()
                text = warning_review_text(event, flow.workspace/'export/warning-review.json')
                dialog = wx.Dialog(self, title='Review updated warnings', size=(740, 540), style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
                box = wx.BoxSizer(wx.VERTICAL)
                box.Add(wx.TextCtrl(dialog, value=text, style=wx.TE_MULTILINE|wx.TE_READONLY), 1, wx.EXPAND|wx.ALL, 12)
                buttons = wx.BoxSizer(wx.HORIZONTAL)
                reject = wx.Button(dialog, wx.ID_CANCEL, 'Reject export')
                accept = wx.Button(dialog, wx.ID_OK, 'Accept updated findings')
                buttons.Add(reject, 0, wx.RIGHT, 8); buttons.Add(accept)
                box.Add(buttons, 0, wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.BOTTOM, 12)
                dialog.SetSizer(box); reject.SetDefault(); reject.SetFocus(); dialog.CentreOnParent()
                self.queue_warning_dialog(dialog, job, flow, event); dialog = None
            except Exception as exc:
                job.cancel(); self.log.SetValue(str(exc)+'\nNo updated-warning acknowledgement or export was adopted.')
            finally:
                if dialog: dialog.Destroy()

        def queue_warning_dialog(self, dialog, job, flow, challenge):
            """Use the existing deferred Cocoa sheet pattern; no nested modal loop."""
            if self.warning_dialog is not None:
                dialog.Destroy(); job.cancel(); return
            lease = (dialog, job, flow, challenge, self.input_generation)
            self.warning_dialog = lease
            self.status.SetLabel('Fresh validation needs an explicit warning review. Original export deadline remains active.')

            def dispose():
                dialog.Unbind(wx.EVT_WINDOW_MODAL_DIALOG_CLOSED, handler=completed)
                dialog.Destroy()
                if self.closing: _finish_window_close(self)

            def completed(event):
                if self.warning_dialog is not lease or event.GetDialog() is not dialog: return
                self.warning_dialog = None
                try:
                    if self.job is job and not self.closing:
                        job.check_warning_review(challenge); flow.fresh()
                        if self.input_generation != lease[4]: raise ValueError('Inputs changed while reviewing warnings.')
                        warning_review_text(challenge, flow.workspace/'export/warning-review.json')
                        _window_source_guard(self, flow)
                        flow.check_request(_window_request(self))
                        job.reply_warning_review(challenge, 'accept_updated_findings' if event.GetReturnCode() == wx.ID_OK else 'reject')
                except Exception as exc:
                    job.cancel(); self.log.SetValue(str(exc)+'\nNo updated-warning acknowledgement or export was adopted.')
                finally: dispose()

            def show():
                if self.warning_dialog is not lease: return
                try:
                    if self.job is not job or self.closing: raise ValueError('Warning review closed before display.')
                    job.check_warning_review(challenge); flow.fresh()
                    if self.input_generation != lease[4]: raise ValueError('Inputs changed before reviewing warnings.')
                    _window_source_guard(self, flow)
                    flow.check_request(_window_request(self))
                    job.check_warning_review(challenge)
                    if self.closing: raise ValueError('Warning review closed before display.')
                    dialog.ShowWindowModal()
                except Exception as exc:
                    self.warning_dialog = None; job.cancel()
                    self.log.SetValue(str(exc)+'\nNo updated-warning acknowledgement or export was adopted.'); dispose()

            dialog.Bind(wx.EVT_WINDOW_MODAL_DIALOG_CLOSED, completed)
            wx.CallAfter(show)

        def opened(self, kind, target, error):
            job = self.job
            cancelled = job.cancel_requested
            self.busy = False; self.job = None
            if not error and not cancelled and not self.closing:
                try:
                    # The inspection worker can finish before this queued UI
                    # callback runs. Recheck saved inputs at the open boundary.
                    guard = _window_source_guard(self, self.flow)
                    self.flow.fresh()
                    if kind == 'export': self.flow.check_open_export_material()
                    if guard is not None:
                        guard.check(self.flow.board)
                    # Last material/origin reads may precede a delayed native
                    # control commit. Never open evidence for another UI request.
                    self.flow.check_request(_window_request(self))
                    job.check_live()
                    if self.closing: raise ValueError('Window closed; no project was opened.')
                    if kind == 'preview':
                        import webbrowser
                        webbrowser.open(target.as_uri())
                    else: subprocess.Popen(['/usr/bin/open', '-a', str(c.CLI.parents[2]), str(target)])
                    # Inspection shares the busy/progress timer. Restore the
                    # completed findings if its last tick showed an old log.
                    stage = 'export' if kind == 'export' else 'review'
                    self.log.SetValue(_completed_summary(self.flow, stage, self.flow.records[stage]))
                    label = {'preview': 'Preview', 'review': 'Review project', 'export': 'Checked export'}[kind]
                    self.status.SetLabel(label + ' open requested. Separate workspace: ' + str(self.flow.workspace))
                except Exception as exc: self.refused('Could not open retained project: ' + str(exc))
            else: self.refused(error or 'Inspection was cancelled. No project was opened.')
            self.refresh()
            if self.closing: _finish_window_close(self)

        def finished(self, job, flow, stage, record, error):
            if self.job is not job: return
            if getattr(self, 'warning_dialog', None) is not None:
                self.warning_dialog[0].EndModal(wx.ID_CANCEL)
            try:
                job.check_live()
                if self.closing: raise ValueError('Window closed; no positive state adopted.')
                if not error:
                    _window_source_guard(self, flow)
                    flow.fresh()
                    flow.check_request(_window_request(self))
                job.check_live()
                if self.closing: raise ValueError('Window closed; no positive state adopted.')
            except Exception as exc: error = str(exc)
            self.busy = False; self.job = None
            if error:
                if flow is not None:
                    flow.ready.clear(); flow.records.clear(); flow.choice = None
                self.refused(error)
            else:
                self.flow = flow
                if stage == 'inspect': self.inspection_path = flow.workspace / 'inspection/inspection.json'
                self.log.SetValue(_completed_summary(flow, stage, record))
                self.status.SetLabel(stage + ' completed. Separate workspace: ' + str(flow.workspace))
            self.refresh()
            if self.closing: _finish_window_close(self)

        def tick(self, _):
            if not self.busy or not self.flow: return
            if getattr(self, 'warning_dialog', None) is not None: return
            root = self.flow.workspace / 'route'
            names = ('final-drc', 'refill-drc', 'engine', 'export', 'source-drc', 'thermal-geometry')
            paths = [root / (name + '.log') for name in names]
            method = getattr(self.flow, 'method', 'route')
            if method in ('recover', 'improve'):
                roots = [root / 'incumbent']
                if method == 'recover':
                    roots += [root / 'recovery']
                    roots += [root / 'recovery' / ('trial-%02d' % index) for index in range(1, 5)]
                else:
                    # Match the pruning producer's fixed MAX_TRIALS=32 namespace;
                    # never walk arbitrary job or historical directories.
                    roots += [root / 'trials' / ('trial-%04d' % index) for index in range(32)]
                paths += [directory / (name + '.log') for directory in roots for name in names]
                dated = []
                for path in paths:
                    try:
                        if path.is_file() and not path.is_symlink():
                            dated.append((path.stat().st_mtime_ns, path))
                    except OSError:
                        continue
                paths = [path for _, path in sorted(dated, key=lambda row: row[0], reverse=True)]
            for path in paths:
                if path.is_file() and not path.is_symlink():
                    try:
                        with path.open('rb') as stream:
                            stream.seek(max(0, path.stat().st_size - 2048)); tail = stream.read(2048)
                        self.log.SetValue(str(path.relative_to(root)) + '\n' + tail.decode('utf8', errors='replace'))
                    except OSError: pass
                    break

        def close(self, event):
            self.closing = True
            if getattr(self, 'placement_window', None) is not None:
                self.placement_window.Close()
                if event.CanVeto(): event.Veto()
                return
            if getattr(self, 'chooser', None) is not None:
                self.status.SetLabel('Close the file chooser with Cancel; then this window will close. No routing job was started.')
                if event.CanVeto(): event.Veto()
                return
            if self.busy:
                self.job.cancel()
                self.status.SetLabel('Closing after cancellation and CLI cleanup; retained outputs will remain.')
                if event.CanVeto(): event.Veto()
            elif not _finish_window_close(self) and event.CanVeto(): event.Veto()
    return Window()


def main(argv=None, *, source_guard=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='', help='Exact saved board hint; never an editor snapshot')
    args = parser.parse_args(argv)
    _check_source_guard(source_guard, args.board)
    try: import wx
    except ImportError as exc:
        raise SystemExit('wx is unavailable. Launch with the pinned KiCad bundled Python; no packages were installed.') from exc
    if wx.GetApp() is not None:
        raise ValueError('A wx application already exists; use create_window instead of a second application loop.')
    app = wx.App(False); window = create_window(args.board, source_guard=source_guard); window.Show()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    def close_signal(*_): wx.CallAfter(window.Close)
    try:
        for sig in previous: signal.signal(sig, close_signal)
        app.MainLoop()
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)
        if window.job is not None: window.job.cancel()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
