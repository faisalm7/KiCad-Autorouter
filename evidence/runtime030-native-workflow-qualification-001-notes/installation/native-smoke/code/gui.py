"""Offline external graphical workflow; no live-board edits or validation bypass.

Run with KiCad's wx-enabled Python. All expensive actions invoke the existing
CLI in a separate project interpreter/process. UI outcomes are not PCB approval.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
import uuid

from . import config as c, preferences as pref

LOG_LIMIT = 2 * 1024 * 1024
GUI_IMPROVE_MIN_SECONDS = 90
FAILURE_REASON_LIMIT = 512
SUMMARY_LIMIT = 128 * 1024


def export_validation_seconds(route_seconds):
    """Allocate separate bounded Native validation without changing routing settings."""
    from . import review_export as ex
    seconds = pref.validate(dict(pref.DEFAULTS, seconds=route_seconds))['seconds']
    return ex.validate_seconds(max(ex.MIN_SECONDS, min(seconds, ex.SECONDS)))


def human_summary(stage, record, *, receipt_path=None, findings_receipt_path=None):
    """Presentation only; existing CLI validation and original receipts remain authoritative."""
    title = {'preview': 'Saved-project preview', 'route': 'Routing result',
             'review': 'Disposable review project', 'choice': 'Review intent',
             'export': 'Fresh separate-project export', 'verify_export': 'Export readback'}.get(stage, stage)
    status = str(record.get('status', 'current' if record.get('current') is True else 'not reported')).replace('_', ' ')
    lines = [title, 'Status: ' + status]
    if receipt_path is not None: lines += ['Full workflow receipt: ' + str(receipt_path)]
    if findings_receipt_path is not None: lines += ['Full findings receipt: ' + str(findings_receipt_path)]
    if record.get('source'): lines += ['Original saved PCB: ' + str(record['source'])]
    project = record.get('project_file') or record.get('review_project')
    if project: lines += ['Separate project: ' + str(project)]
    if record.get('candidate'): lines += ['Candidate PCB: ' + str(record['candidate'])]
    settings = record.get('effective_preferences') or record.get('routing_preferences', {}).get('effective', {})
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
                  + '; routing budget ' + str(settings.get('seconds', 'not reported')) + ' s'
                  + '; layers ' + str(layers)
                  + '; via preference ' + str(settings.get('scoring_preference') or 'engine default')]
        if settings.get('nets'): lines += ['Selected nets: ' + ', '.join(settings['nets'])]
        if 'seconds' in settings:
            lines += ['Additional Native export-validation budget: '
                      + str(export_validation_seconds(settings['seconds']))
                      + ' s after acceptance, separate from routing; the routing budget is unchanged.']
    if stage == 'preview':
        lines += ['Static preflight only; Native routing validation has not run.',
                  'Existing route items: ' + str(record.get('existing_route_items', 'not reported'))
                  + '; protected: ' + str(record.get('protected_route_items', 'not reported'))
                  + '; to reroute: ' + str(record.get('rerouted_route_items', 'not reported'))]
        if record.get('schematic_class_check') is not None:
            lines += ['KiCad must verify schematic/PCB class bindings before routing starts.']
    if record.get('invariants_unchanged') is True:
        lines += ['Original-design checks passed; source geometry and protected routing retained.']
    matches = record.get('protected_route_import', {}).get('matches')
    if isinstance(matches, list): lines += ['Protected route items retained: ' + str(len(matches))]
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
    return '\n'.join(lines)

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
class Request:
    board: str
    output_parent: str
    settings_json: str
    saved_closed: bool
    method: str = 'route'

    def prepare(self):
        """Called off the UI thread; capture exact saved project identity."""
        if self.saved_closed is not True:
            raise ValueError('Save and close the source PCB and schematic editors, then acknowledge it.')
        board = canonical(self.board)
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
        if self.method not in ('route', 'improve'): raise ValueError('Unknown routing method.')
        if self.method == 'improve': check_improve_settings(settings)
        files = source_inventory(board)
        workspace = parent / ('autorouter-gui-' + uuid.uuid4().hex)
        workspace.mkdir(mode=0o700)
        from .handoff import capture_destination
        owner = {}; capture_destination(owner, workspace)
        settings_bytes = (json.dumps(settings, indent=2, sort_keys=True) + '\n').encode()
        target = workspace / 'settings.json'
        with target.open('xb') as stream:
            stream.write(settings_bytes)
        return Workflow(board, workspace, owner, json.dumps(files, sort_keys=True), settings_bytes, self.method)


class Workflow:
    """UI state only. Existing CLI readers authorize every review/export."""
    def __init__(self, board, workspace, owner, files_json, settings_bytes, method='route'):
        from .handoff import runtime_inventory
        self.board, self.workspace, self.owner = board, workspace, owner
        self.files_json, self.settings_bytes = files_json, settings_bytes
        self.method = method
        self.ready = set()
        self.choice = None
        self.records = {}
        self.runtime_hashes = runtime_inventory()

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
        if stage in ('preview', 'route'):
            argv += [self.method if stage == 'route' else stage, str(self.board), '--settings', settings]
            if stage == 'preview' and self.method == 'improve': argv += ['--purpose', 'improve']
            if stage == 'route': argv += ['--output', str(self.workspace / 'route')]
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
                or request.method != self.method):
            raise ValueError('Displayed source or settings differ from this session; preview again.')

    def timeout(self, stage):
        if stage == 'export':
            return float(export_validation_seconds(json.loads(self.settings_bytes)['seconds'])) + 45
        return float(json.loads(self.settings_bytes)['seconds']) + 45 if stage == 'route' else 90.0

    def adopt(self, stage, process, log_path, *, choice=None):
        self.fresh()
        if (process['cancel_requested'] or process['log_truncated']
                or process['exit_code'] in (130, 143)
                or type(process['exit_code']) is int and process['exit_code'] < 0):
            raise ValueError('Action failed or was cancelled. Evidence was retained; no positive state adopted.')
        if process['exit_code'] != 0:
            detail = failed_route_detail(self.workspace / 'route/result.json') if stage == 'route' else None
            if stage == 'preview' and type(process['exit_code']) is int and process['exit_code'] == 2:
                detail = failed_preview_detail(log_path)
            if stage == 'verify_export' and process['exit_code'] == 2:
                detail = failed_export_check_detail(log_path)
            raise ValueError(detail or 'Action failed or was cancelled. Evidence was retained; no positive state adopted.')
        if stage == 'preview':
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
        elif stage == 'review':
            record = read_record(self.workspace / 'review/review.json')
            if record.get('status') != 'ready_for_manual_review':
                raise ValueError('Shared review validation did not complete.')
        elif stage == 'choice':
            record = read_record(self.workspace / 'choice/choice.json')
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
        """Seal the queued open gap using the existing bounded byte witness.

        This is not another Native check or an atomic editor transaction.
        The worker's current CLI reader remains the acceptance authority.
        """
        from . import review_export as ex
        from .floor_route import canonical as canonical_json
        exported = self.records['export']
        root = self.workspace / 'export'
        if (canonical_json(read_record(root / 'export.json')) != canonical_json(exported)
                or ex.evidence(root) != exported.get('export_evidence')):
            raise ValueError('Checked export changed while opening. Start a fresh preview; retained files were not reaccepted.')


def check_improve_settings(config):
    """GUI-only operational minimum; the public strategy contract is unchanged."""
    from .strategy import pruning_scope
    effective = pref.validate(config)
    pruning_scope(effective)
    if effective['seconds'] < GUI_IMPROVE_MIN_SECONDS:
        raise ValueError('Graphical Improve needs at least 90 seconds for incumbent and final checks. This is an operational minimum, not a completion guarantee; the budget was not changed.')
    return effective


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


def failed_preview_detail(path):
    """Explain the CLI's rejected preview shape without adopting any state."""
    try:
        record = read_record(path)
        if (type(record) is not dict or set(record) != {'status', 'reason'}
                or record.get('status') != 'rejected'):
            return None
        text = short_failure_reason(record.get('reason'))
        if text is None: return None
        return ('Saved-project preview refused: ' + text +
                '\nStart a fresh preview using the intended saved project and settings. No preview or candidate was accepted.' +
                '\nFull failure log: ' + str(path))
    except Exception:
        return None


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
        raise ValueError('Improve requires whole-board unlocked routing, all source layers, Native guidance and at least 90 seconds. This is not a completion guarantee. Use Route for other tasks.') from exc


class CliJob:
    """One child CLI. Cancel requests SIGINT; its existing runner owns cleanup.

    Never SIGKILL a new process tree or claim descendant cleanup from UI polling.
    A cancelled invocation cannot authorize a positive UI outcome even at exit0.
    """
    def __init__(self):
        self.process = None
        self.cancel_requested = False
        self._lock = threading.Lock()

    def cancel(self):
        with self._lock:
            if self.cancel_requested: return
            self.cancel_requested = True
            if self.process is not None and self.process.poll() is None:
                try: self.process.send_signal(signal.SIGINT)
                except ProcessLookupError: pass

    def check_live(self):
        """A retained process snapshot cannot supersede a later Cancel."""
        with self._lock:
            if self.cancel_requested:
                raise ValueError('Action was cancelled. No positive UI state adopted.')

    def adopt(self, flow, stage, process, log_path, *, choice=None):
        self.check_live()
        record = flow.adopt(stage, process, log_path, choice=choice)
        try:
            self.check_live()
        except ValueError:
            flow.ready.clear(); flow.records.clear(); flow.choice = None
            raise
        return record

    def run(self, argv, log_path, *, timeout=165.0):
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 1000:
            raise ValueError('Finite GUI action watchdog required.')
        started = time.monotonic(); size = 0; truncated = False
        with log_path.open('xb') as log:
            with self._lock:
                if self.cancel_requested: raise ValueError('Cancelled before process startup.')
                self.process = subprocess.Popen(argv, cwd=c.ROOT, stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=child_environment())
            deadline = threading.Timer(timeout, self.cancel)
            deadline.daemon = True; deadline.start()
            try:
                while True:
                    chunk = self.process.stdout.read1(8192)
                    if not chunk: break
                    retained = chunk[:max(0, LOG_LIMIT-size)]
                    log.write(retained); log.flush(); size += len(retained)
                    if len(retained) != len(chunk):
                        truncated = True; self.cancel()
                code = self.process.wait()
            except BaseException:
                self.cancel()
                self.process.stdout.close()
                self.process.wait()
                raise
            finally:
                deadline.cancel(); deadline.join()
                self.process.stdout.close()
        result = dict(argv=argv, exit_code=code, cancel_requested=self.cancel_requested,
                      log_truncated=truncated, log_bytes=size,
                      wall_seconds=time.monotonic()-started,
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='', help='Exact saved board hint; never an editor snapshot')
    args = parser.parse_args(argv)
    try: import wx
    except ImportError as exc:
        raise SystemExit('wx is unavailable. Launch with the pinned KiCad bundled Python; no packages were installed.') from exc
    class Window(wx.Frame):
        def __init__(self):
            super().__init__(None, title='KiCad Autorouter — separate project', size=(820, 780))
            self.flow = None; self.job = None; self.busy = False; self.closing = False
            self.chooser = None; self.input_generation = 0
            self.edit_controls = []
            panel = wx.Panel(self); layout = wx.BoxSizer(wx.VERTICAL)
            self.board = self.path_row(panel, layout, 'Saved PCB', args.board, False)
            self.output = self.path_row(panel, layout, 'Output folder', str(c.ROOT / '.runs'), True)
            self.values = {
                'scope': [('Reroute unlocked; keep locked copper', 'whole_board_unlocked_routing'), ('Finish gaps; keep all existing copper', 'partial_completion'), ('Selected nets; keep other copper', 'selected_nets')],
                'profile': [('Standard', 'standard'), ('Tuned', 'tuned'), ('Completion only', 'completion-only')],
                'adapter': [('Both corrections', 'both'), ('Stock interchange', 'none'), ('Graphics correction', 'graphics'), ('Plane correction', 'planes')],
                'layers': [('All source copper', 'source_all'), ('Front only', ['F.Cu']), ('Back only', ['B.Cu']), ('Front and back', ['F.Cu', 'B.Cu'])],
                'scoring_preference': [('Engine default', None), ('Default via cost', 'via_default'), ('Lower via cost', 'via_low'), ('Higher via cost', 'via_high')]}
            grid = wx.FlexGridSizer(cols=2, vgap=4, hgap=8); grid.AddGrowableCol(1)
            grid.Add(wx.StaticText(panel, label='Method'), 0, wx.ALIGN_CENTER_VERTICAL)
            self.method = wx.Choice(panel, choices=['Route', 'Improve (experimental; tuned whole-board preset)'])
            self.method.SetSelection(0); self.method.Bind(wx.EVT_CHOICE, self.method_changed)
            self.edit_controls.append(self.method); grid.Add(self.method, 1, wx.EXPAND)
            self.choices = {}
            for name, label in [('scope', 'Routing and protection'), ('profile', 'Routing profile'), ('adapter', 'Interchange corrections'), ('layers', 'Allowed new copper'), ('scoring_preference', 'Via preference')]:
                grid.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
                control = wx.Choice(panel, choices=[label for label, _ in self.values[name]])
                control.SetSelection(next(i for i, (_, value) in enumerate(self.values[name]) if value == pref.DEFAULTS[name])); control.Bind(wx.EVT_CHOICE, self.changed)
                self.choices[name] = control; self.edit_controls.append(control); grid.Add(control, 1, wx.EXPAND)
            grid.Add(wx.StaticText(panel, label='Routing budget (seconds)'), 0, wx.ALIGN_CENTER_VERTICAL)
            # Cocoa SpinCtrl clamps invalid text on focus loss before Preview
            # can validate it. Keep the exact input until explicit validation.
            self.seconds = wx.TextCtrl(panel, value=str(int(pref.DEFAULTS['seconds'])))
            self.seconds.Bind(wx.EVT_TEXT, self.changed)
            self.edit_controls.append(self.seconds); grid.Add(self.seconds)
            grid.Add(wx.StaticText(panel, label='Selected nets (one exact name per line)'), 0, wx.ALIGN_CENTER_VERTICAL)
            self.nets = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(-1, 55))
            self.nets.Bind(wx.EVT_TEXT, self.changed); self.edit_controls.append(self.nets); grid.Add(self.nets, 1, wx.EXPAND)
            layout.Add(grid, 0, wx.EXPAND | wx.ALL, 8)
            export_note = wx.StaticText(panel, label='Fresh export adds separate Native validation after acceptance: '
                '30–120 seconds, derived from the routing budget. The routing budget is unchanged.')
            export_note.Wrap(780)
            layout.Add(export_note, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            presets = wx.BoxSizer(wx.HORIZONTAL)
            for label, callback in [('Load settings…', self.load_preset), ('Save settings as…', self.save_preset)]:
                button = wx.Button(panel, label=label); button.Bind(wx.EVT_BUTTON, callback)
                presets.Add(button, 0, wx.ALL, 4); self.edit_controls.append(button)
            layout.Add(presets)
            self.ack = wx.CheckBox(panel, label='I saved and CLOSED the source PCB and schematic editors. The exact paths above are correct.')
            layout.Add(self.ack, 0, wx.ALL, 6)
            self.inspected = wx.CheckBox(panel, label='I inspected all findings and CLOSED the review editors/project. My choice is intent, not PCB certification.')
            layout.Add(self.inspected, 0, wx.ALL, 6)
            self.buttons = {}
            for names in ((('Preview', 'preview'), ('Route', 'route'), ('Create review', 'review'), ('Cancel', 'cancel')),
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
            for control in (self.board, self.output): control.Bind(wx.EVT_TEXT, self.changed)
            self.Bind(wx.EVT_CLOSE, self.close)
            self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.tick, self.timer); self.timer.Start(500)
            self.refresh()

        def path_row(self, panel, layout, label, value, directory):
            row = wx.BoxSizer(wx.HORIZONTAL); row.Add(wx.StaticText(panel, label=label), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 6)
            control = wx.TextCtrl(panel, value=value); row.Add(control, 1, wx.ALL, 6)
            button = wx.Button(panel, label='Browse…')
            def browse(_):
                if self.busy or self.chooser is not None: return
                dialog = wx.DirDialog(self, 'Choose output folder') if directory else wx.FileDialog(self, 'Choose saved PCB', wildcard='KiCad PCB (*.kicad_pcb)|*.kicad_pcb', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
                self.choose_path(dialog, control.SetValue)
            button.Bind(wx.EVT_BUTTON, browse); self.edit_controls.append(button)
            row.Add(button, 0, wx.ALL, 6); layout.Add(row, 0, wx.EXPAND)
            return control

        def changed(self, event):
            self.input_generation = getattr(self, 'input_generation', 0) + 1
            if not self.busy: self.flow = None; self.inspected.SetValue(False)
            self.refresh(); event.Skip()

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
                if self.closing: self.timer.Stop(); self.Destroy()
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
            if self.flow is not None:
                self.flow.ready.clear(); self.flow.records.clear(); self.flow.choice = None
            self.flow = None; self.inspected.SetValue(False)
            self.status.SetLabel('Action refused or cancelled. Read the findings below; start a fresh preview.')
            self.log.SetValue(str(error) + '\nNo positive state adopted. Retained files were not deleted.')
            self.refresh()

        def method_changed(self, event):
            self.input_generation = getattr(self, 'input_generation', 0) + 1
            if getattr(self, 'chooser', None) is not None: event.Skip(); return
            if self.busy: event.Skip(); return
            self.flow = None; self.inspected.SetValue(False)
            try:
                if self.method.GetSelection():
                    settings = improve_preset(self.config())
                    for name in ('profile', 'adapter'):
                        self.choices[name].SetSelection(next(i for i, (_, value) in enumerate(self.values[name]) if value == settings[name]))
                    self.status.SetLabel('Improve selected: tuned profile and both corrections. Routing protection, layers, budget and via preference are unchanged.')
            except Exception as exc:
                self.refused(str(exc))
                # Cocoa commits the popup selection after this callback.
                # Reset afterwards, without nesting a modal inside its menu loop.
                wx.CallAfter(self.method.SetSelection, 0)
            self.refresh(); event.Skip()

        def load_preset(self, _):
            if self.busy or getattr(self, 'chooser', None) is not None: return
            def loaded(path):
                config = pref.resolve(pref.load(path))
                if config['guidance'] != 'native': raise ValueError('This graphical workflow supports Native guidance; retain other presets for their documented CLI.')
                if config['seconds'] != int(config['seconds']): raise ValueError('This graphical control uses whole seconds; use the CLI for fractional budgets.')
                if self.method.GetSelection(): check_improve_settings(config)
                indices = {name: next(i for i, (_, value) in enumerate(self.values[name]) if value == config[name]) for name in self.choices}
                for name, control in self.choices.items(): control.SetSelection(indices[name])
                self.seconds.SetValue(str(int(config['seconds']))); self.nets.SetValue('\n'.join(config.get('nets', [])))
                self.flow = None; self.inspected.SetValue(False); self.refresh()
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
                self.choose_path(wx.FileDialog(self, 'Save NEW settings JSON', defaultFile='routing-settings.json', wildcard='JSON (*.json)|*.json', style=wx.FD_SAVE), saved)
            except Exception as exc: self.refused(str(exc))

        def refresh(self):
            choosing = getattr(self, 'chooser', None) is not None
            ready = self.flow.ready if self.flow else set()
            allowed = {'preview': True, 'route': 'preview' in ready and 'route' not in ready,
                'review': 'route' in ready and 'review' not in ready,
                'open_preview': 'review' in ready, 'open_review': 'review' in ready,
                'accept': 'review' in ready and 'choice' not in ready,
                'reject': 'review' in ready and 'choice' not in ready,
                'export': 'choice' in ready and 'export' not in ready and self.flow.choice == 'accept' if self.flow else False,
                'open_export': 'verify_export' in ready}
            for name, button in self.buttons.items(): button.Enable(not choosing and (self.busy if name == 'cancel' else not self.busy and allowed.get(name, False)))
            for control in (self.board, self.output, self.ack, self.inspected, *self.edit_controls): control.Enable(not self.busy and not choosing)

        def act(self, action):
            try:
                if getattr(self, 'chooser', None) is not None: return
                if action == 'cancel': self.job.cancel(); self.status.SetLabel('Cancellation requested; waiting for the CLI worker to finish cleanup.'); return
                if self.busy: return
                if action.startswith('open_'):
                    kind = action.removeprefix('open_'); flow = self.flow
                    self.busy = True; self.job = CliJob(); self.refresh()
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
                request = Request(self.board.GetValue(), self.output.GetValue(), json.dumps(self.config()), self.ack.GetValue(), 'improve' if self.method.GetSelection() else 'route')
                if self.ack.GetValue() is not True: raise ValueError('Save and close source editors, then acknowledge the exact paths.')
                self.busy = True; self.job = CliJob(); job = self.job; self.refresh()
                self.status.SetLabel('Preparing ' + stage + ' outside KiCad; all outputs stay separate.')
                def work():
                    flow = None
                    try:
                        flow = request.prepare() if stage == 'preview' else self.flow
                        flow.check_request(request)
                        argv = flow.command(stage, choice=choice)
                        log_path = flow.workspace / (stage + '.command.log')
                        process = job.run(argv, log_path, timeout=flow.timeout(stage))
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

        def opened(self, kind, target, error):
            cancelled = self.job.cancel_requested
            self.busy = False; self.job = None
            if not error and not cancelled and not self.closing:
                try:
                    # The inspection worker can finish before this queued UI
                    # callback runs. Recheck saved inputs at the open boundary.
                    self.flow.fresh()
                    if kind == 'export': self.flow.check_open_export_material()
                    if kind == 'preview':
                        import webbrowser
                        webbrowser.open(target.as_uri())
                    else: subprocess.Popen(['/usr/bin/open', '-a', str(c.CLI.parents[2]), str(target)])
                except Exception as exc: self.refused('Could not open retained project: ' + str(exc))
            else: self.refused(error or 'Inspection was cancelled. No project was opened.')
            self.refresh()
            if self.closing: self.timer.Stop(); self.Destroy()

        def finished(self, job, flow, stage, record, error):
            if self.job is not job: return
            try: job.check_live()
            except ValueError as exc: error = str(exc)
            self.busy = False; self.job = None
            if error:
                if flow is not None:
                    flow.ready.clear(); flow.records.clear(); flow.choice = None
                self.refused(error)
            else:
                self.flow = flow
                display = {**flow.records.get('route', {}), **record}
                if stage == 'export': display.update(flow.records['export'])
                receipt_name = {'preview': 'preview.command.log', 'route': 'route/result.json',
                    'review': 'review/review.json', 'choice': 'choice/choice.json', 'export': 'export/export.json'}[stage]
                receipt_path = flow.workspace / receipt_name
                findings_path = flow.workspace / 'route/result.json' if stage == 'review' else receipt_path
                self.log.SetValue(human_summary(stage, display, receipt_path=receipt_path,
                                               findings_receipt_path=findings_path if display.get('native') or display.get('saved_native_findings') else None))
                self.status.SetLabel(stage + ' completed. Separate workspace: ' + str(flow.workspace))
            self.refresh()
            if self.closing: self.timer.Stop(); self.Destroy()

        def tick(self, _):
            if not self.busy or not self.flow: return
            for name in ('final-drc', 'refill-drc', 'engine', 'export', 'source-drc'):
                path = self.flow.workspace / 'route' / (name + '.log')
                if path.is_file() and not path.is_symlink():
                    try:
                        with path.open('rb') as stream:
                            stream.seek(max(0, path.stat().st_size - 2048)); tail = stream.read(2048)
                        self.log.SetValue(name + '\n' + tail.decode('utf8', errors='replace'))
                    except OSError: pass
                    break

        def close(self, event):
            if getattr(self, 'chooser', None) is not None:
                self.closing = True
                self.status.SetLabel('Close the file chooser with Cancel; then this window will close. No routing job was started.')
                event.Veto(); return
            if self.busy:
                self.closing = True; self.job.cancel()
                self.status.SetLabel('Closing after cancellation and CLI cleanup; retained outputs will remain.')
                event.Veto()
            else: self.timer.Stop(); self.Destroy()
    app = wx.App(False); window = Window(); window.Show()
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
