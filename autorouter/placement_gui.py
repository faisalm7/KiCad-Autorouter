"""Selected-placement controls over the shared guarded core.

Optional intent proposals confer no editor mutation or implicit routing approval. Native qualification runs
in the ordinary isolated CLI; the existing routing frame owns later routing,
warning review, acceptance and separate-project delivery.
"""
from __future__ import annotations

import argparse
import copy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import uuid
import xml.etree.ElementTree as ET

from . import config as c, conversation, gui, handoff as h, placement_intent as intent, placement_view
from . import finish_gaps, routing_scope
from .pipeline import Rejected
from . import schematic_context, workspace_chrome as chrome


def copilot_context(inspection, settings, seconds):
    """The same visible choices and affected-net plan as ordinary controls."""
    from . import design_intent
    seconds = routing_seconds(seconds)
    plan = intent.copper_plan(inspection, settings)
    if plan is None:
        raise ValueError('This pilot needs your explicit affected-net rebuild choice. '
            'Choose Rebuild affected unlocked nets and review the protection controls first. '
            'The assistant cannot give that permission.')
    selected = set(settings['selected'])
    fixed = [row['uuid'] for row in inspection['components'] if row['uuid'] not in selected]
    return design_intent.placement_route_context(inspection, settings, fixed_components=fixed,
        rebuild_permission=intent.rebuilds_copper(settings),
        approved_route_nets=plan['incident_names'], route_seconds=seconds)


def routing_seconds(text):
    if (type(text) is not str or not 1 <= len(text) <= 32 or not text.isascii()
            or not text.isdecimal() or not 5 <= int(text) <= 900):
        raise ValueError('Enter a whole-number routing budget from 5 to 900 seconds.')
    return int(text)


LOCAL_REQUEST_EXAMPLE = 'Select J1, J2\nArea 14, 8 to 22, 13 mm\nRouting time 75 s'
CONVERSATION_EMPTY = 'Describe a placement or protected routing request. Review any proposed settings beside the board.'


def local_constraint_request(text):
    """Read only explicit local settings, leaving other wording for clarification."""
    number = r'-?[0-9]+(?:\.[0-9]+)?'
    region = rf'area\s+({number})\s*,\s*({number})\s+to\s+({number})\s*,\s*({number})\s+mm'
    fields = dict(selected_refs=None, region_nm=None, route_seconds=None)
    if type(text) is not str or len(text) > 4096 or not text.strip():
        raise ValueError('Enter a local request using one or more example lines.')
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if match := re.fullmatch(r'select\s+(.+)', line, re.IGNORECASE):
            key = 'selected_refs'
            value = constraint_references(match[1])
        elif match := re.fullmatch(region, line, re.IGNORECASE):
            key = 'region_nm'
            value = [millimetres(token) for token in match.groups()]
        elif match := re.fullmatch(r'routing\s+time\s+([0-9]+)\s+(?:s|seconds?)', line, re.IGNORECASE):
            key = 'route_seconds'
            value = routing_seconds(match[1])
        else:
            raise ValueError('Use the example lines for component references, an area in mm or routing time. '
                             'Use the ordinary controls for copper protection and other policies.')
        if fields[key] is not None:
            raise ValueError('Enter each requested setting on just one line.')
        fields[key] = value
    return fields


def constraint_references(text):
    refs = [ref.strip() for ref in re.split(r',|\s+and\s+', text, flags=re.IGNORECASE)]
    if (not 1 <= len(refs) <= 16 or len(set(refs)) != len(refs)
            or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9_+.-]{0,63}', ref) for ref in refs)):
        raise ValueError('Enter one to sixteen distinct component references, separated by commas.')
    return refs


def constraint_change_text(offer, *, conversational=False, adopted=False):
    before, after = offer['before'], offer['after']
    if offer['kind'] == conversation.ROUTING_KIND:
        target = ', '.join(after['nets']) or 'all open connections'
        return (f'Protected routing suggestion\nTarget  {target}\n'
                f"Routing time  {before['route_seconds']} s → {after['route_seconds']} s\n"
                f"{offer['checked']['protected_route_items']} existing copper items stay protected.")

    def area(bounds):
        if bounds is None:
            return 'unset'
        x1, y1, x2, y2 = map(mm, bounds)
        return f'({x1}, {y1}) to ({x2}, {y2}) mm'

    displays = (
        ('Components', 'selected_refs', lambda refs: ', '.join(refs) or 'none'),
        ('Movement area', 'region_nm', area),
        ('Routing time', 'route_seconds', lambda seconds: f'{seconds} s'),
    )
    title = ('Last adopted placement settings' if adopted else
             'Conversation suggestion' if conversational else 'Local suggestion · saved project')
    lines = [title]
    for label, key, show in displays:
        if adopted or before[key] == after[key]:
            lines.append(f'{label}  {show(after[key])}')
        else:
            lines.append(f'{label}  {show(before[key])} → {show(after[key])}')
    if offer['placement_settings'] is not None:
        lines.append('Other parts stay in place. KiCad locks stay as saved.')
        if intent.region_options(offer['placement_settings']):
            lines.append('Selected parts may start outside the area. Every proposed position must fit inside it.')
    plan = offer['copper_plan']
    if plan:
        lines.append(f"{len(plan['protected_routes'])} existing routes stay protected. "
                     f"{len(plan['removed_routes'])} may be rebuilt after review.")
        lines.append('Affected nets for later review  ' + ', '.join(plan['incident_names']))
        if plan['protected_names']:
            lines.append('Protected nets  ' + ', '.join(plan['protected_names']))
    elif offer['placement_settings'] is not None:
        lines.append('Existing copper stays protected.')
    return '\n'.join(lines)


def constraint_entry_values(offer):
    after = offer['after']
    return (', '.join(after['selected_refs']), ', '.join(map(mm, after['region_nm'] or [])),
            str(after['route_seconds']))


def constraint_scene(inspection, controls, offer=None):
    observation = inspection['observation']
    if offer is None:
        selected = controls['selected']
        region = controls['region_nm']
    else:
        after = offer['after']
        refs = set(after['selected_refs'])
        selected = [row['uuid'] for row in inspection['components'] if row['reference'] in refs]
        region = after['region_nm']
    anchors = {row['uuid']: row['position_nm'] for row in observation['footprints']}
    policy = controls['policy']
    plan = None if offer is None else offer['copper_plan']
    protected_ids = ([row['uuid'] for row in plan['protected_routes']] if plan is not None
                     else policy.get('protected_route_ids', []))
    protection = (policy.get('copper_policy') is None,
                  policy.get('protected_names', []), protected_ids)
    return placement_view.scene(observation, {uid: anchors[uid] for uid in selected}, selected,
        region or observation['outline']['bounds_nm'], title='Saved board and placement constraints',
        annotation_context=inspection.get('annotation_context'), protection=protection)


def placement_policy(window):
    """Read the ordinary control choices shared by proposals and execution."""
    policy = dict(scope=window.inspection['observation']['scope'])
    if window.rebuild_copper():
        policy.update(copper_policy=intent.COPPER_POLICY,
            protected_names=[name for name in window.protected_names.GetValue().splitlines() if name],
            protected_route_ids=[identity for identity in window.protected_route_ids.GetValue().splitlines() if identity])
    if window.rigid_group.GetValue():
        policy['group_policy'] = intent.GROUP_POLICY
    if window.target_region.GetValue():
        preferred = intent.target_area_policy(policy['scope'])
        policy['region_initialization'] = (preferred if policy['scope'] == intent.contract.CONTEXT_SCOPE
                                           else getattr(window, 'target_start_policy', preferred))
    return policy


def update_target_area(window):
    """Reflect the effective start policy after an ordinary explicit area edit."""
    if window.inspection is None or not getattr(window, 'automatic_target_area', False):
        return
    enabled = False
    scope = window.inspection['observation']['scope']
    if (intent.target_area_policy(scope) is not None
            and (scope != intent.contract.CONTEXT_SCOPE or not window.rebuild_copper())):
        selected = [row['uuid'] for i, row in enumerate(window.inspection['components'])
                    if window.parts.IsChecked(i)]
        try:
            area = [millimetres(field.GetValue()) for field in window.region]
        except ValueError:
            pass  # The ordinary controls still refuse an incomplete or invalid rectangle.
        else:
            enabled = intent.target_area_needs_initialization(window.inspection, selected, area,
                                                              grouped=window.rigid_group.GetValue())
    if window.target_region.GetValue() != enabled:
        window.target_region.SetValue(enabled)


class SavedProjectOpen(ValueError):
    """The saved-project inventory contains a KiCad lock."""


PCB_SETUP_GUIDANCE = {
    'footprints_needed': ('The saved PCB has no footprints yet.',
        'Add and connect symbols in KiCad, assign their footprints and review ERC. '
        'Then use Update PCB from Schematic (F8) in PCB Editor.'),
    'outline_needed': ('The saved PCB needs a board outline.',
        'Draw a closed outline on Edge.Cuts in KiCad. Placement and routing still check the saved geometry.'),
}


def require_closed_source(board, *, inspection=None):
    """Early UI hint using the same inventory/lock guard as qualification.

    No missing-lock observation proves editor closure. Explicit acknowledgement
    and the independent worker's complete source/design checks remain required.
    """
    # Match saved-project intake's file-identity boundary before inventory:
    # an empty path resolves to cwd, and a directory would scan its parent.
    if not isinstance(board, (str, Path)) or not str(board) or '\x00' in str(board):
        raise ValueError('Select the exact saved .kicad_pcb file before inspection.')
    source = (gui.saved_project_board(board) if Path(board).suffix == '.kicad_pro' else gui.canonical(board))
    if source.suffix != '.kicad_pcb' or not source.is_file():
        raise ValueError('Select the exact saved .kicad_pcb file before inspection.')
    hashes = gui.source_inventory(source)
    try:
        h.require_closed_review(hashes)
    except h.ReviewProjectOpen:
        raise SavedProjectOpen('Save and close the source PCB and schematic editors, then choose '
            'File > Close Project in KiCad manager. A project lock is still present. '
            'Then click Refresh inspection. Closing the project may update saved files.') from None
    if inspection is not None and (str(source) != inspection['source'] or hashes != inspection['source_hashes']):
        raise ValueError('Saved source files changed since inspection. Click Refresh inspection, '
            'then load your settings and review a new draft. Earlier validation was not renewed.')
    return source


def affected_routing_notice(source):
    """Advise about the selected-net class gate without blocking placement review."""
    if c.NATIVE_VERSION != '10.0.7':
        return ''
    from .pipeline import check_native7_selected_netclasses

    try:
        check_native7_selected_netclasses(source)
    except (OSError, ValueError, Rejected) as exc:
        return 'These net-class settings block routing after copper rebuild. ' + str(exc)
    return ''


def saved_routing_scene(inspection, placement):
    """Build optional saved context using the existing bounded board renderer."""
    try:
        if placement is None or placement['source_hashes'] != inspection['source_hashes']:
            placement = intent.inspect_saved(inspection['source'])
        if (placement['source'] != inspection['source']
                or placement['source_hashes'] != inspection['source_hashes']):
            return None
        return placement_view.saved_scene(placement['observation'])
    except (OSError, ValueError, KeyError, TypeError, IndexError, Rejected):
        return None  # Drawing limits do not change routing eligibility.


def empty_copper_selection(source, inspection, selected, settings):
    """Prefill exact selected-part nets only when no original copper can be rebuilt."""
    if not selected or inspection is None or str(source) != inspection['source']:
        return None
    try:
        observation = inspection['observation']
        chosen = [part for part in observation['footprints'] if part['uuid'] in selected]
        nets = {pad['net'] for part in chosen for pad in part['pads']}
        if not nets or '' in nets or len(chosen) != len(selected):
            return None
        current = gui.source_inventory(source)
        if current != inspection['source_hashes']:
            return None
        raw = intent.pc.read_bytes(source, intent.contract.MAX_BYTES)
        if hashlib.sha256(raw).hexdigest() != observation['source_board_sha256']:
            return None
        tree = intent.contract.read_board(raw)
        known, existing = routing_scope.copper_net_context(tree)
        if not nets <= known:
            return None
        if nets & existing or '' in existing:
            return None
        settings = gui.pref.validate(dict(settings, scope='selected_nets', profile='completion-only',
                                          nets=routing_scope.validate_names(sorted(nets))))

        def origin():
            if gui.source_inventory(source) != current:
                raise ValueError('The saved board changed after selecting its unrouted nets. Inspect it again.')

        def retain_copper(edited, _method, _candidate):
            if edited['scope'] == 'selected_nets' and set(edited['nets']) & existing:
                raise ValueError('A selected net already has tracks, vias or a zone. Use Finish gaps to preserve it.')

        return settings, gui.SourceGuard(source, origin, retain_copper)
    except (KeyError, OSError, TypeError, ValueError, Rejected):
        return None  # Inconclusive selection keeps the original Finish gaps settings.


def copilot_plan_text(inspection, proposal):
    """Present checked facts, not generated explanations or execution authority."""
    refs = {row['uuid']: row['reference'] for row in inspection['components']}
    value = proposal['intent']; area = value['region_nm']
    return ('Proposed plan — waiting for your approval\n\nMove: '
        + ', '.join(refs[key] for key in value['selected'])
        + '\nKeep fixed: ' + (', '.join(refs[key] for key in value['fixed']) or 'all unselected parts')
        + '\nMovement area: (' + mm(area[0]) + ', ' + mm(area[1]) + ') to ('
        + mm(area[2]) + ', ' + mm(area[3]) + ') mm'
        + '\nOrientation and board side: unchanged\n\n' + copper_findings(proposal['copper_plan'])
        + '\n\nRoute only: ' + ', '.join(value['route_nets'])
        + '\nRouting budget: ' + str(value['route_seconds']) + ' seconds'
        + '\nOriginal rules and source copper layers; corrected completion routing.'
        + '\n\nApproval here requests placement alternatives only. Review the resulting moves '
          'before Native validation and routing. Final findings and acceptance remain separate.'
        + '\nNo electrical, manufacturing or human PCB approval is granted.')


def hosted_consent(wx, parent, prepared, consent):
    """One finite private entry; no credentials in persistence or diagnostics."""
    dialog = wx.Dialog(parent, title='Ask the assistant · review data and cost', size=(650, 550))
    layout = wx.BoxSizer(wx.VERTICAL)
    text = wx.StaticText(dialog, label='One request to OpenAI · Sol / medium · maximum $0.05. '
        'Placement, routing and validation still run locally after your separate approval.')
    text.Wrap(610); layout.Add(text, 0, wx.EXPAND | wx.ALL, 12)
    data = wx.TextCtrl(dialog, value=json.dumps(prepared['consent_summary'], indent=2, ensure_ascii=False),
        style=wx.TE_MULTILINE | wx.TE_READONLY)
    layout.Add(data, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
    allowed = wx.CheckBox(dialog, label='I allow this shown request and compact project summary to be sent once.')
    layout.Add(allowed, 0, wx.ALL, 12)
    layout.Add(wx.StaticText(dialog, label='Dedicated API key · held only for this request'), 0, wx.LEFT, 12)
    field = wx.TextCtrl(dialog, style=wx.TE_PASSWORD)
    layout.Add(field, 0, wx.EXPAND | wx.ALL, 12)
    note = wx.StaticText(dialog, label='Entry expires after 90 seconds. No retries or saved key. Closing sends nothing.')
    note.Wrap(610); layout.Add(note, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
    buttons = wx.BoxSizer(wx.HORIZONTAL)
    start = wx.Button(dialog, label='Send one request'); cancel = wx.Button(dialog, wx.ID_CANCEL, label='Cancel')
    buttons.AddStretchSpacer(); buttons.Add(cancel, 0, wx.RIGHT, 8); buttons.Add(start)
    layout.Add(buttons, 0, wx.EXPAND | wx.ALL, 12); dialog.SetSizer(layout)
    answer = {}; timer = wx.Timer(dialog)
    def stop(_=None):
        field.ChangeValue(''); answer.clear(); dialog.EndModal(wx.ID_CANCEL)
    def send(_):
        if not allowed.GetValue():
            note.SetLabel('Review the shown data and explicitly allow this one request first.'); return
        value = field.GetValue(); field.ChangeValue('')
        if not value or len(value) > 4096 or any(not 33 <= ord(ch) <= 126 for ch in value):
            note.SetLabel('Enter a valid dedicated key. It has not been sent or saved.'); return
        answer['credential'] = value
        dialog.EndModal(wx.ID_OK)
    start.Bind(wx.EVT_BUTTON, send); cancel.Bind(wx.EVT_BUTTON, stop)
    dialog.Bind(wx.EVT_TIMER, stop, timer); timer.StartOnce(90000)
    try:
        if dialog.ShowModal() != wx.ID_OK: return None
        approved = copy.deepcopy(consent); approved['approved'] = True
        return answer.pop('credential'), approved
    finally:
        timer.Stop(); field.ChangeValue(''); answer.clear(); dialog.Destroy()


def millimetres(text):
    if type(text) is not str or not 0 < len(text) <= 32:
        raise ValueError('Enter a bounded decimal coordinate in millimetres.')
    try:
        value = Decimal(text)
        if not value.is_finite() or abs(value) > 2000:
            raise ValueError('Coordinates must be finite and within ±2000 mm.')
        # Use the shared exact decimal-tuple parser, independent of ambient
        # arithmetic precision. Fractional nm must not disappear by rounding.
        return intent.contract.pt.nm(text, 1000000)
    except InvalidOperation as exc:
        raise ValueError('Enter a decimal coordinate in millimetres.') from exc


def mm(value):
    if type(value) is not int or abs(value) > 2_000_000_000:
        raise ValueError('An exact bounded nanometre coordinate is required.')
    whole, fraction = divmod(abs(value), 1000000)
    return ('-' if value < 0 else '') + str(whole) + ('.' + str(fraction).zfill(6).rstrip('0') if fraction else '')


ROUTED_REASON = intent.ROUTED_REASON


def blocking_reasons(row, *, rebuild=False):
    return [reason for reason in row['fixed_reasons'] if not (rebuild and reason == ROUTED_REASON)]


def component_label(row, *, rebuild=False):
    reasons = blocking_reasons(row, rebuild=rebuild)
    short = []
    for reason in reasons:
        label = {'Locked in KiCad': 'locked',
                 'Shares a net with existing copper': 'routed net'}.get(reason, 'constraints')
        if label not in short: short.append(label)
    return row['reference'] + (' · fixed (' + ', '.join(short) + ')' if reasons else
        ' · reroute required' if rebuild and ROUTED_REASON in row['fixed_reasons'] else ' · movable')


def component_findings(inspection, *, rebuild=False):
    return '\n'.join(row['reference'] + ': ' + ('; '.join(row['fixed_reasons'])
        + ('; movable only if the exact affected-copper plan passes protection checks.'
           if rebuild and not blocking_reasons(row, rebuild=True) else '')
        if row['fixed_reasons'] else 'Movable when selected; otherwise fixed.')
        for row in inspection['components'])


def placement_move_findings(observation, moves):
    """Describe the same positions used by the current board drawing."""
    def location(xy):
        return f'({mm(xy[0])}, {mm(xy[1])})'

    parts = observation['footprints']
    rows = []
    for part in parts:
        origin = tuple(part['position_nm'])
        target = tuple(moves.get(part['uuid'], origin))
        if target != origin:
            rows.append(f"{part['reference']} · {location(origin)} → {location(target)} mm")
    count = len(rows)
    heading = f'Displayed placement · {count} move' + ('' if count == 1 else 's')
    unchanged = len(parts) - count
    stays = 'stays' if unchanged == 1 else 'stay'
    return '\n'.join([f'{heading} · {unchanged} {stays} in place', *rows])


def inspected_native_findings(inspection):
    """Reuse the exact receipt which placement inspection already checked."""
    context = inspection.get('native_context')
    if context is None:
        return None
    raw = intent.pc.read_bytes(Path(context['receipt']), 512 * 1024)
    if hashlib.sha256(raw).hexdigest() != context['receipt_sha256']:
        raise ValueError('Saved KiCad findings changed during inspection. Refresh the saved project.')
    return json.loads(raw)['native']


def source_native_findings(inspection, native=None):
    """Present the bound original findings, never a draft-validation claim."""
    if native is None:
        native = inspection.get('native_source_baseline', {}).get('native')
    if native is None:
        return ''
    return gui.human_summary('inspect', dict(status='source_inspected_placement_pending',
        source=inspection['source'], native=native,
        source_delivery=finish_gaps.source_delivery(native, field_mismatches_only=True)),
        receipt_path=inspection['native_context']['receipt'])


def region_search_findings(search, inspection):
    """Explain the existing validation checks without inferring infeasibility."""
    summary = search.get('region_initialization') or {}
    labels = {
        'protected_tracks': 'Clearance from protected tracks (rectangular envelopes)',
        'component_spacing': 'Spacing between component courtyards',
        'allowed_area': 'The full courtyard must fit inside the allowed area',
        'board_edge': 'Clearance from the board edge',
        'keepout': 'Clearance from a keepout',
        'annotations': 'Silkscreen or solder mask clearance',
        'other': 'Other placement checks',
    }
    lines = ['No starting placement found in the allowed area.']
    if summary.get('courtyard_cannot_fit'):
        lines += ['At least one selected courtyard and its required clearance cannot fit in the area.']
    elif (count := summary.get('candidates_checked')):
        lines += [f'Checked {count} starting arrangements. Each is counted under its first failed check.']
        for key, count in summary.get('rejected_by_constraint', {}).items():
            lines.append(f'  {count} · {labels.get(key, labels["other"])}')
    lines += ['', 'Use the Board tab to review the area and protected copper. '
              'A bounded search can miss a legal placement. Your original project is unchanged.']
    native = source_native_findings(inspection)
    if native:
        lines += ['', native]
    return '\n'.join(lines)


def copper_findings(plan):
    if plan is None:
        return 'Original copper and unselected/fixed components are preserved.'
    return ('Affected-copper plan · ' + str(len(plan['removed_routes'])) + ' existing routes to rebuild; '
        + str(len(plan['protected_routes'])) + ' routes retained.\n'
        + 'Rebuild complete nets: ' + ', '.join(plan['incident_names']) + '\n'
        + 'User-protected nets: ' + (', '.join(plan['protected_names']) or 'none specified') + '\n'
        + 'User-protected route UUIDs: ' + (', '.join(plan['protected_route_ids']) or 'none specified') + '\n'
        + 'Unrelated and locked copper stays unchanged. This plan is not approval to execute or accept a board.')


def placement_limits(inspection, *, rebuild=False, grouped=False, region_initialization=False):
    limits = inspection.get('limitations', intent.LIMITS)
    if grouped:
        limits = [row.replace('Groups, flips,', 'Flips,').replace('No grouping, side/', 'No side/')
                  for row in limits]
    if intent.contract.fixed_context_scope(inspection.get('observation', {}).get('scope')):
        result = [*limits, *intent.COPPER_LIMITS[:4]] if rebuild else list(limits)
    else:
        result = [limits[0], *intent.COPPER_LIMITS] if rebuild else list(limits)
    if grouped:
        result.append('Rigid selected group: all selected parts share one exact translation; spacing, angles and sides stay fixed. '
                      'Only the explicit affected-net rebuild workflow is supported; other grouping modes remain unsupported.')
    if region_initialization:
        result.append('Place into the target rectangle: a bounded search may start one or two selected parts outside it. '
                      'The source must remain physically valid; every proposed final pose obeys the rectangle, fixed parts, copper and annotation constraints. '
                      'Initialization and optimization share the same 2-second search budget; a seed is not electrical approval or a quality improvement.')
    return result


def prefill_copper_routing(frame, plan, *, seconds=90):
    """Show the shared routing contract; the source guard still enforces it."""
    settings = gui.pref.validate(dict(gui.pref.DEFAULTS, scope='selected_nets',
        profile='completion-only', guidance='native', adapter='both', layers='source_all',
        scoring_preference=None, seconds=seconds, nets=list(plan['incident_names'])))
    prefill_routing(frame, settings)
    frame.status.SetLabel('Review the affected nets and time limit, then preview routing.')
    frame.refresh()


def prefill_routing(frame, settings):
    indices = {name: next(i for i, (_, value) in enumerate(frame.values[name]) if value == settings[name])
               for name in frame.choices}
    frame.method.SetSelection(0)
    for name, index in indices.items(): frame.choices[name].SetSelection(index)
    frame.seconds.SetValue(str(settings['seconds'])); frame.nets.SetValue('\n'.join(settings.get('nets', [])))
    if intent.constraints.encoded(frame.config()) != intent.constraints.encoded(settings):
        raise ValueError('Visible routing settings differ from the required affected-copper task.')


class ReviewGate:
    """One UI-lifecycle fence, independent of wx and all Native execution."""
    def __init__(self):
        self.generation = 0
        self.review = None
        self.acknowledged = False
        self.dirty = False
        self.closed = False

    def invalidate(self, *, dirty=False):
        self.generation += 1
        self.acknowledged = False
        self.dirty = dirty
        if self.review is not None:
            self.review.intent = None

    def attach(self, review):
        self.invalidate()
        self.review = review

    def ticket(self):
        if self.closed or self.dirty or self.acknowledged is not True or self.review is None:
            raise ValueError('Review the exact current draft and acknowledge its limits first.')
        return (self.generation, self.review.revision,
                intent.constraints.digest(self.review.pose),
                intent.constraints.digest(self.review.settings),
                intent.constraints.digest(self.review.inspection),
                intent.constraints.digest(self.review.copper_plan),
                intent.constraints.digest(self.review.observation))

    def check(self, ticket):
        if ticket != self.ticket():
            raise ValueError('Placement review changed; earlier qualification cannot be used.')

    def close(self):
        self.invalidate()
        self.closed = True


def qualification_command(draft, output):
    """The UI has no separate qualification implementation or shell path."""
    python = c.ROOT / '.venv/bin/python'
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError('The installed project Python is unavailable; run installation doctor.')
    draft = h.real_path(draft)
    output = h.real_path(output, existing=False)
    if output.parent != c.ROOT / '.runs' or output.exists():
        raise ValueError('Qualification requires a fresh runtime job folder.')
    raw = intent.pc.read_bytes(draft, 64 * 1024)
    return [str(python), '-B', '-m', 'autorouter.placement', '--draft', str(draft),
            '--draft-sha256', hashlib.sha256(raw).hexdigest(), '--output', str(output), '--qualify']


def write_new_json(path, value):
    path = h.real_path(path, existing=False)
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    if len(raw) > 64 * 1024:
        raise ValueError('Placement settings/draft exceeds its bounded size.')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
    return path


def bitmap_with_labels(wx, svg, size=(850, 500), *, min_text_pixels=9):
    """wx's SVG rasterizer omits text; paint only our passive renderer's labels."""
    image = wx.svg.SVGimage.CreateFromBytes(svg.encode())
    scale = min(size[0] / image.width, size[1] / image.height)
    bitmap = image.ConvertToBitmap(scale=scale, width=round(image.width * scale), height=round(image.height * scale))
    dc = wx.MemoryDC(bitmap)
    for node in ET.fromstring(svg).findall('{http://www.w3.org/2000/svg}text'):
        font = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_SWISS))
        font.SetPixelSize(wx.Size(0, max(min_text_pixels, round(float(node.get('font-size')) * scale))))
        if node.get('font-weight') == 'bold': font = font.Bold()
        dc.SetFont(font); dc.SetTextForeground(wx.Colour(node.get('fill')))
        text = node.text or ''; _, height, descent, _ = dc.GetFullTextExtent(text)
        dc.DrawText(text, round(float(node.get('x')) * scale), round(float(node.get('y')) * scale - height + descent))
    dc.SelectObject(wx.NullBitmap)
    return bitmap


def board_canvas(wx, parent, on_pick, on_region, on_error, on_ready=None, *, read_only=False,
                 empty_note='Choose a saved project to see its board and components.'):
    """Responsive display/picking only; commits use ordinary settings handlers."""
    class Canvas(wx.Panel):
        def __init__(self):
            super().__init__(parent, style=wx.BORDER_SIMPLE | wx.WANTS_CHARS)
            self.display = None; self.bitmap = None; self.draw_area = False
            self.empty_note = empty_note
            self.drag_start = None; self.drag_end = None; self.render_key = None
            self.SetMinSize(self.FromDIP((210, 150) if read_only else (320, 180)))
            self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
            self.Bind(wx.EVT_PAINT, self.paint)
            self.Bind(wx.EVT_SIZE, self.resized)
            if not read_only:
                self.SetToolTip('Click a component to select it. Draw area edits the movement rectangle; numeric controls remain available.')
                self.Bind(wx.EVT_LEFT_DOWN, self.down)
                self.Bind(wx.EVT_MOTION, self.motion)
                self.Bind(wx.EVT_LEFT_UP, self.up)
                self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.capture_lost)
                self.Bind(wx.EVT_CHAR_HOOK, self.key)

        def SetScene(self, value):
            self.display = None; self.bitmap = None; self.render_key = None
            self.drag_start = self.drag_end = None
            if self.HasCapture(): self.ReleaseMouse()
            self.display = value
            try:
                if value is not None:
                    self.prepare_bitmap()
            except Exception:
                self.display = None; self.bitmap = None; self.render_key = None
                raise
            self.Refresh()

        def Ready(self):
            return self.display is not None and self.bitmap is not None and self.render_key == self.view_size()

        def SetEmptyNote(self, text):
            self.empty_note = text
            if self.display is None:
                self.Refresh()

        def view_size(self):
            width, height = self.GetClientSize()
            return width, height, self.GetContentScaleFactor()

        def prepare_bitmap(self):
            key = self.view_size()
            width, height, factor = key
            if width <= 0 or height <= 0:
                return
            if self.bitmap is None or key != self.render_key:
                bitmap = bitmap_with_labels(wx, self.display['svg'],
                    (max(1, round(width * factor)), max(1, round(height * factor))),
                    min_text_pixels=max(9, round(9 * factor)))
                bitmap.SetScaleFactor(factor)
                self.bitmap = bitmap; self.render_key = key
                if on_ready is not None:
                    wx.CallAfter(on_ready)

        def resized(self, event):
            # Cocoa can send a size event for an unchanged canvas whenever the
            # acknowledgement lays out the buttons. Keep that exact raster.
            if self.render_key != self.view_size(): self.Refresh()
            event.Skip()

        def paint(self, _):
            try:
                self.paint_scene()
            except Exception as exc:
                # Raster creation, device drawing and resize are one display
                # transaction. A later paint failure cannot retain old approval.
                self.display = None; self.bitmap = None; self.render_key = None
                on_error(str(exc))

        def paint_scene(self):
            dc = wx.AutoBufferedPaintDC(self)
            dc.SetBackground(wx.Brush(wx.Colour('#ffffff'))); dc.Clear()
            width, height = self.GetClientSize()
            if self.display is None:
                dc.SetTextForeground(wx.Colour('#526273'))
                dc.DrawText(self.empty_note, 18, 22)
                return
            if width <= 0 or height <= 0: return
            self.prepare_bitmap()
            fit = min(width/self.display['size'][0], height/self.display['size'][1])
            px = round((width-self.display['size'][0]*fit)/2)
            py = round((height-self.display['size'][1]*fit)/2)
            dc.DrawBitmap(self.bitmap, px, py, True)
            if self.drag_start is not None and self.drag_end is not None:
                a,b=self.drag_start,self.drag_end
                dc.SetPen(wx.Pen(wx.Colour('#176cba'),2,wx.PENSTYLE_SHORT_DASH))
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.DrawRectangle(min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0]),abs(a[1]-b[1]))

        def down(self, event):
            if self.display is None or 'transform' not in self.display: return
            self.SetFocus(); point=tuple(event.GetPosition())
            if self.draw_area:
                if placement_view.screen_point(self.display,point,tuple(self.GetClientSize())) is None: return
                self.drag_start=self.drag_end=point; self.CaptureMouse()
            else:
                identity=placement_view.pick_component(self.display,point,tuple(self.GetClientSize()))
                if identity is not None:on_pick(identity)

        def motion(self,event):
            if self.drag_start is not None and event.Dragging():
                self.drag_end=tuple(event.GetPosition()); self.Refresh()
            event.Skip()

        def up(self,event):
            if self.drag_start is None:return
            start=self.drag_start;end=tuple(event.GetPosition());display=self.display
            self.drag_start=self.drag_end=None
            if self.HasCapture():self.ReleaseMouse()
            self.Refresh()
            try:on_region(placement_view.drawn_region(display,start,end,tuple(self.GetClientSize())))
            except ValueError as exc:on_region(None,str(exc))

        def capture_lost(self,_):
            self.drag_start=self.drag_end=None;self.Refresh()

        def key(self,event):
            if event.GetKeyCode()==wx.WXK_ESCAPE:
                self.capture_lost(None)
                if self.HasCapture():self.ReleaseMouse()
                return
            event.Skip()
    return Canvas()


def create_window(board='', *, output_hint=None, on_closed=None, conversation_reply=None, source_note='',
                  toolbar_selection=(), launcher_manifest=None, on_return_live=None):
    if on_closed is not None and not callable(on_closed):
        raise ValueError('The parent close notification must be a callable.')
    if on_return_live is not None and (not callable(on_return_live) or on_closed is None):
        raise ValueError('Returning to the live companion requires return and close callbacks.')
    if output_hint is not None and not isinstance(output_hint, (str, Path)):
        raise ValueError('Use a routing output folder path or no hint.')
    import wx
    import wx.svg
    if wx.GetApp() is None or threading.current_thread() is not threading.main_thread():
        raise ValueError('Open placement controls on the existing application main thread.')
    if not isinstance(board, (str, Path)):
        raise ValueError('Use an exact saved PCB path or an empty hint.')

    options = {'launcher_manifest': launcher_manifest} if launcher_manifest is not None else {}
    if on_return_live is not None:
        options['on_return_live'] = on_return_live
    window = window_type(wx, board=board, output_hint=output_hint, on_closed=on_closed,
                         conversation_reply=conversation_reply, toolbar_selection=toolbar_selection, **options)()
    if source_note: window.message(source_note)
    return window


def window_type(wx, *, board='', output_hint=None, on_closed=None, conversation_reply=None,
                toolbar_selection=(), launcher_manifest=None, on_return_live=None):
    """Real window methods exposed for controlled-dependency tests, no fragments."""
    class Window(wx.Frame):
        def __init__(self):
            super().__init__(None, title='Copperpath — Open project', size=(1040, 700))
            self.SetMinSize(self.FromDIP((880, 610)))
            self.gate = ReviewGate(); self.inspection = None; self.busy = False
            self.saved_native = None
            self.saved_route_context = None
            self.finalized = False
            self.job = None; self.cancel_event = None; self.routing = None
            self.qualified = None; self.validation_revoked = False
            self.routing_handoff = None
            self.updating = False; self.workspace = None; self.owner = {}
            self.automatic_target_area = False
            self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
            self.pending_coordinates = {}
            self.alternative_labels = []; self.alternative_targets = []
            self.editing_component = None
            self.copilot_generation = 0; self.pending_copilot = None; self.approved_copilot = None
            self.constraint_review = None; self.constraint_offer = None; self.constraint_edited = False
            self.board_scene = None; self.board_legend = ''
            self.schematic = None; self.schematic_refusal = ''
            self.rebuild_routing_notice = ''
            self.conversation = conversation.Conversation()
            self.conversation_offer = False
            self.routing_source_scene = None
            self.routing_output_hint = str(output_hint) if output_hint is not None else None
            self.toolbar_selection = toolbar_selection
            self.toolbar_source = Path(board).with_suffix('.kicad_pcb') if toolbar_selection else None
            self.editor_context = None
            panel = self.panel = wx.Panel(self)
            background, surface, accent = chrome.colours(wx)
            panel.SetBackgroundColour(wx.Colour(background))
            root = wx.BoxSizer(wx.VERTICAL)
            self.welcome = wx.Panel(panel)
            introduction = wx.BoxSizer(wx.VERTICAL)
            introduction.AddStretchSpacer()
            name = chrome.heading(wx.StaticText(self.welcome, label='Copperpath'), 30)
            name.SetForegroundColour(wx.Colour(accent))
            introduction.Add(name, 0, wx.ALIGN_CENTER | wx.BOTTOM, 12)
            summary = wx.StaticText(self.welcome,
                label='Plan placement and check routing for a KiCad project.')
            introduction.Add(summary, 0, wx.ALIGN_CENTER | wx.BOTTOM, 28)
            self.open_design = wx.Button(self.welcome, label='Continue an existing design…', id=wx.ID_OPEN)
            introduction.Add(self.open_design, 0, wx.ALIGN_CENTER | wx.BOTTOM, 12)
            launch_options = wx.BoxSizer(wx.HORIZONTAL)
            self.new_design = wx.Button(self.welcome, label='Start a new design')
            launch_options.Add(self.new_design, 0, wx.RIGHT, 8)
            from . import live_move
            self.example_project = live_move.example_source() / (live_move.EXAMPLE_NAME + '.kicad_pro')
            self.example = wx.Button(self.welcome, label='Open example')
            self.example.SetToolTip('Try the included board. Any changes go into a separate project.')
            launch_options.Add(self.example)
            introduction.Add(launch_options, 0, wx.ALIGN_CENTER)
            introduction.AddStretchSpacer()
            self.welcome.SetSizer(introduction)
            root.Add(self.welcome, 1, wx.EXPAND)

            self.project_bar = wx.Panel(panel)
            self.project_bar.SetBackgroundColour(wx.Colour(surface))
            heading = wx.BoxSizer(wx.HORIZONTAL)
            identity = wx.BoxSizer(wx.VERTICAL)
            self.project_title = chrome.heading(wx.StaticText(self.project_bar, label='Opening project',
                style=wx.ST_ELLIPSIZE_END | wx.ST_NO_AUTORESIZE), 18)
            identity.Add(self.project_title, 0, wx.EXPAND)
            self.project_mode = wx.StaticText(self.project_bar, label='Saved workspace')
            identity.Add(self.project_mode, 0, wx.TOP, 2)
            heading.Add(identity, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
            self.browse = wx.Button(self.project_bar, label='Choose project…')
            heading.Add(self.browse, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            self.inspect = wx.Button(self.project_bar, label='Refresh inspection')
            self.inspect.SetToolTip('Check the saved project again after edits or after closing it in KiCad.')
            heading.Add(self.inspect, 0, wx.ALIGN_CENTER_VERTICAL)
            self.kicad_setup = wx.Button(self.project_bar, label='Open in KiCad')
            self.kicad_setup.SetToolTip('Open this saved project in KiCad Manager to finish PCB setup.')
            heading.Add(self.kicad_setup, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
            self.route_saved = wx.Button(self.project_bar, label='Route saved board…')
            heading.Add(self.route_saved, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 6)
            header_layout = wx.BoxSizer(wx.VERTICAL)
            header_layout.Add(heading, 0, wx.EXPAND | wx.ALL, 12)
            self.project_bar.SetSizer(header_layout)
            root.Add(self.project_bar, 0, wx.EXPAND | wx.BOTTOM, 10)

            self.path_details = wx.Panel(panel)
            pathrow = wx.BoxSizer(wx.HORIZONTAL)
            project_label = wx.StaticText(self.path_details, label='Project path')
            pathrow.Add(project_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.board = wx.TextCtrl(self.path_details, value=str(board), style=wx.TE_PROCESS_ENTER)
            self.board.SetMinSize(self.FromDIP((160, -1)))
            self.board.SetToolTip('Choose a saved KiCad project or enter its full path and press Return.')
            pathrow.Add(self.board, 1)
            self.path_details.SetSizer(pathrow)
            root.Add(self.path_details, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
            self.path_details.Hide()
            self.workspace_body = wx.Panel(panel)
            columns = wx.BoxSizer(wx.HORIZONTAL)
            self.side_panel = wx.Panel(self.workspace_body)
            self.side_panel.SetBackgroundColour(wx.Colour(surface))
            self.side_panel.SetMinSize(self.FromDIP((352, -1)))
            side_layout = wx.BoxSizer(wx.VERTICAL)
            conversation_title = chrome.heading(wx.StaticText(self.side_panel, label='Design assistant'), 15)
            side_layout.Add(conversation_title, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 8)
            self.copper_controls = wx.Panel(self.side_panel)
            copper_row = wx.BoxSizer(wx.HORIZONTAL)
            copper_row.Add(wx.StaticText(self.copper_controls, label='Copper'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.copper_policy = wx.Choice(self.copper_controls,
                choices=['Preserve all existing copper', 'Rebuild affected unlocked nets'], name='Existing copper policy')
            self.copper_policy.SetSelection(0)
            self.copper_policy.SetToolTip('Locked and unrelated copper always stay protected.')
            copper_row.Add(self.copper_policy, 1)
            self.copper_controls.SetSizer(copper_row)
            side_layout.Add(self.copper_controls, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            self.pages = wx.Notebook(self.side_panel); self.pages.SetMinSize(self.FromDIP((352, 230)))
            side_layout.Add(self.pages, 1, wx.EXPAND)
            self.history = wx.CollapsiblePane(self.side_panel, label='Conversation history', style=wx.CP_NO_TLW_RESIZE)
            history_panel = self.history.GetPane()
            self.assistant_result = wx.TextCtrl(history_panel, style=wx.TE_MULTILINE | wx.TE_READONLY,
                                                size=(-1, 88), name='Conversation history')
            self.assistant_result.ChangeValue(CONVERSATION_EMPTY)
            history_layout = wx.BoxSizer(wx.VERTICAL)
            history_layout.Add(self.assistant_result, 1, wx.EXPAND | wx.TOP, 4)
            history_panel.SetSizer(history_layout)
            self.history.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, lambda _: self.layout_panel())
            side_layout.Add(self.history, 0, wx.EXPAND | wx.ALL, 8)
            self.side_panel.SetSizer(side_layout)
            self.controls = wx.ScrolledWindow(self.pages, style=wx.VSCROLL | wx.TAB_TRAVERSAL)
            self.controls.SetScrollRate(0, 12)
            left = wx.BoxSizer(wx.VERTICAL); side = self.controls
            left.Add(wx.StaticText(side, label='Components'), 0, wx.BOTTOM, 5)
            self.parts = wx.CheckListBox(side, size=self.FromDIP((280, 150))); left.Add(self.parts, 0, wx.EXPAND)
            self.toolbar_pick = wx.Button(side, label='Use KiCad selection' +
                                          (f' ({len(toolbar_selection)})' if toolbar_selection else ''))
            self.toolbar_pick.SetToolTip('Use the component selection captured when this workspace opened. '
                                         'Save, close and inspect the same project first.')
            self.toolbar_pick.Bind(wx.EVT_BUTTON, self.use_toolbar_selection)
            left.Add(self.toolbar_pick, 0, wx.TOP, 6)
            hint = wx.StaticText(side, label='Click a part on the board or check it here. Other parts stay fixed.')
            hint.Wrap(310); left.Add(hint, 0, wx.TOP | wx.BOTTOM, 7)
            self.region_summary = wx.StaticText(side, label='Movement area becomes available after inspection.')
            self.region_summary.Wrap(264); left.Add(self.region_summary, 0, wx.BOTTOM, 7)
            self.precise = wx.CollapsiblePane(side, label='Precise area · mm', style=wx.CP_NO_TLW_RESIZE)
            area_panel = self.precise.GetPane(); grid = wx.FlexGridSizer(cols=2, vgap=5, hgap=6); grid.AddGrowableCol(1)
            self.region = []
            for label in ('Left X', 'Top Y', 'Right X', 'Bottom Y'):
                grid.Add(wx.StaticText(area_panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
                field = wx.TextCtrl(area_panel, size=(120, -1)); self.region.append(field); grid.Add(field, 1, wx.EXPAND)
            area_panel.SetSizer(grid); left.Add(self.precise, 0, wx.EXPAND | wx.BOTTOM, 8)
            self.advanced = wx.CollapsiblePane(side, label='Advanced settings', style=wx.CP_NO_TLW_RESIZE)
            advanced = self.advanced.GetPane(); advanced_layout = wx.BoxSizer(wx.VERTICAL)
            budget_row = wx.BoxSizer(wx.HORIZONTAL)
            budget_row.Add(wx.StaticText(advanced, label='Routing time (s)'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.route_budget = wx.TextCtrl(advanced, value='90', size=(62, -1), name='Routing time in seconds')
            budget_row.Add(self.route_budget, 0); advanced_layout.Add(budget_row, 0, wx.BOTTOM, 8)
            self.three_pad = wx.CheckBox(advanced, label='Move one three-pad SMD part')
            self.three_pad.SetToolTip('Refresh the saved board to check this placement scope. All existing copper stays in place.')
            self.three_pad.Show(c.NATIVE_VERSION == '10.0.7')
            advanced_layout.Add(self.three_pad, 0, wx.BOTTOM, 6)
            self.rigid_group = wx.CheckBox(advanced, label='Keep selected parts together')
            advanced_layout.Add(self.rigid_group, 0, wx.BOTTOM, 6)
            self.target_region = wx.CheckBox(advanced, label='Allow parts to start outside the target area')
            self.target_region.SetToolTip('A drawn or entered area enables this when a supported placement needs it. '
                'Turn it off to require the current positions to fit. Every proposed position must fit inside the area.')
            advanced_layout.Add(self.target_region, 0, wx.BOTTOM, 6)
            self.original_group = wx.Button(advanced, label='Review current group arrangement')
            advanced_layout.Add(self.original_group, 0, wx.EXPAND | wx.BOTTOM, 6)
            self.protection = wx.CollapsiblePane(advanced, label='Additional copper protection', style=wx.CP_NO_TLW_RESIZE)
            protection_panel = self.protection.GetPane(); protection_layout = wx.BoxSizer(wx.VERTICAL)
            hint = wx.StaticText(protection_panel, label='Optional sensitive net names, one per line. No route IDs are needed for ordinary use.')
            hint.Wrap(254); protection_layout.Add(hint, 0, wx.BOTTOM, 4)
            self.protected_names = wx.TextCtrl(protection_panel, style=wx.TE_MULTILINE, size=(250, 45))
            protection_layout.Add(self.protected_names, 0, wx.EXPAND | wx.BOTTOM, 6)
            protection_layout.Add(wx.StaticText(protection_panel, label='Exact route IDs · advanced'), 0, wx.BOTTOM, 4)
            self.protected_route_ids = wx.TextCtrl(protection_panel, style=wx.TE_MULTILINE, size=(250, 45))
            protection_layout.Add(self.protected_route_ids, 0, wx.EXPAND)
            protection_panel.SetSizer(protection_layout)
            advanced_layout.Add(self.protection, 0, wx.EXPAND | wx.BOTTOM, 8)
            presetrow = wx.BoxSizer(wx.HORIZONTAL)
            self.load = wx.Button(advanced, label='Load settings…'); self.save = wx.Button(advanced, label='Save settings…')
            presetrow.Add(self.load, 0, wx.RIGHT, 6); presetrow.Add(self.save)
            advanced_layout.Add(presetrow, 0, wx.BOTTOM, 7); advanced.SetSizer(advanced_layout)
            left.Add(self.advanced, 0, wx.EXPAND)
            settings_layout = wx.BoxSizer(wx.VERTICAL)
            settings_layout.Add(left, 0, wx.EXPAND | wx.ALL, 9); self.controls.SetSizer(settings_layout)
            self.pages.AddPage(self.controls, 'Settings')
            board_page = self.board_page = wx.Panel(self.workspace_body); board_layout = wx.BoxSizer(wx.VERTICAL)
            board_tools = wx.BoxSizer(wx.HORIZONTAL)
            board_tools.Add(chrome.heading(wx.StaticText(board_page, label='Board'), 14), 1, wx.ALIGN_CENTER_VERTICAL)
            self.draw_area = wx.ToggleButton(board_page, label='Draw target area')
            board_tools.Add(self.draw_area, 0, wx.LEFT, 8)
            board_layout.Add(board_tools, 0, wx.EXPAND | wx.BOTTOM, 6)
            self.native_summary = wx.StaticText(board_page)
            board_layout.Add(self.native_summary, 0, wx.EXPAND | wx.BOTTOM, 5)
            self.picture = board_canvas(wx, board_page, self.pick_on_board, self.area_on_board, self.preview_failed, self.preview_ready)
            board_layout.Add(self.picture, 1, wx.EXPAND)
            self.constraint_key = wx.StaticText(board_page)
            board_layout.Add(self.constraint_key, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)
            self.pose_pane = wx.Panel(board_page)
            self.alternative = wx.Choice(self.pose_pane); self.alternative.SetMinSize(self.FromDIP((160, -1)))
            pose_layout = wx.BoxSizer(wx.VERTICAL)
            pose_layout.Add(self.alternative, 0, wx.EXPAND | wx.BOTTOM, 6)
            coordinates = wx.CollapsiblePane(self.pose_pane, label='Edit position numerically', style=wx.CP_NO_TLW_RESIZE)
            edit_panel = coordinates.GetPane()
            editrow = wx.BoxSizer(wx.HORIZONTAL)
            self.part = wx.Choice(edit_panel); self.part.SetMinSize(self.FromDIP((76, -1)))
            editrow.Add(self.part, 1, wx.RIGHT, 6)
            self.x = wx.TextCtrl(edit_panel, size=(62, -1)); self.y = wx.TextCtrl(edit_panel, size=(62, -1))
            for label, field in (('X mm', self.x), ('Y mm', self.y)):
                editrow.Add(wx.StaticText(edit_panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
                editrow.Add(field, 0, wx.RIGHT, 6)
            self.apply = wx.Button(edit_panel, label='Update positions'); editrow.Add(self.apply)
            edit_panel.SetSizer(editrow)
            pose_layout.Add(coordinates, 0, wx.EXPAND)
            self.pose_pane.SetSizer(pose_layout)
            board_layout.Add(self.pose_pane, 0, wx.EXPAND); board_page.SetSizer(board_layout)
            coordinates.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, lambda event: self.layout_panel())
            findings_page = wx.Panel(self.pages); findings_layout = wx.BoxSizer(wx.VERTICAL)
            self.findings = wx.TextCtrl(findings_page, style=wx.TE_MULTILINE | wx.TE_READONLY)
            findings_layout.Add(self.findings, 1, wx.EXPAND); findings_page.SetSizer(findings_layout)
            self.pages.AddPage(findings_page, 'Findings')
            assistant_page = wx.Panel(self.pages)
            assistant_inputs = wx.ScrolledWindow(assistant_page, style=wx.VSCROLL | wx.TAB_TRAVERSAL)
            assistant_inputs.SetScrollRate(0, 12); self.request_controls = assistant_inputs
            assistant_layout = wx.BoxSizer(wx.VERTICAL)
            assistant_layout.AddSpacer(8)
            self.assistant_context = wx.StaticText(assistant_inputs)
            self.assistant_context.Hide()
            assistant_layout.Add(self.assistant_context, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            assistant_layout.Add(wx.StaticText(assistant_inputs, label='Describe where parts should go'),
                                 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            self.assistant_request = wx.TextCtrl(assistant_inputs, style=wx.TE_MULTILINE, size=(-1, 66),
                                               name='Placement request')
            self.assistant_request.SetHint(LOCAL_REQUEST_EXAMPLE)
            assistant_layout.Add(self.assistant_request, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            request_example = wx.StaticText(assistant_inputs,
                label='Local request commands: Select parts, Area in mm, Routing time in seconds.')
            request_example.Wrap(self.FromDIP(300))
            request_example.SetToolTip(LOCAL_REQUEST_EXAMPLE)
            assistant_layout.Add(request_example, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            self.constraint_preview = wx.Button(assistant_inputs, label='Preview placement request')
            self.constraint_preview.SetToolTip('Check component names and area locally. No design changes or model calls.')
            assistant_layout.Add(self.constraint_preview, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            self.model_options = wx.CollapsiblePane(assistant_inputs, label='Model-backed conversation',
                                                    style=wx.CP_NO_TLW_RESIZE)
            model_panel = self.model_options.GetPane()
            model_layout = wx.BoxSizer(wx.VERTICAL)
            options = wx.BoxSizer(wx.HORIZONTAL)
            self.conversation_kind = wx.Choice(model_panel, choices=['Place components', 'Protected routing'],
                                                name='Hosted task')
            self.conversation_kind.SetSelection(0)
            self.conversation_kind.SetToolTip('Choose which settings a hosted reply may suggest.')
            self.conversation_reset = wx.Button(model_panel, label='New conversation')
            options.Add(self.conversation_kind, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
            options.Add(self.conversation_reset, 0, wx.ALIGN_CENTER_VERTICAL)
            model_layout.Add(options, 0, wx.EXPAND | wx.BOTTOM, 6)
            self.assistant_ask = wx.Button(model_panel,
                label='Send controlled reply' if conversation_reply else 'Review data and send…')
            model_layout.Add(self.assistant_ask)
            model_panel.SetSizer(model_layout)
            self.model_options.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, lambda _: self.layout_panel())
            assistant_layout.Add(self.model_options, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            self.constraint_summary = wx.TextCtrl(assistant_inputs, style=wx.TE_MULTILINE | wx.TE_READONLY,
                                                 size=(-1, 74), name='Constraint changes')
            self.constraint_summary.Hide()
            assistant_layout.Add(self.constraint_summary, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            self.constraint_edit = wx.Button(assistant_inputs, label='Edit suggestion')
            self.constraint_editor = wx.Panel(assistant_inputs)
            proposed_fields = self.constraint_editor
            draft_layout = wx.FlexGridSizer(cols=2, vgap=4, hgap=6); draft_layout.AddGrowableCol(1)
            self.constraint_fields = []
            self.constraint_labels = []
            for label in ('Components', 'Area (mm)', 'Routing time (s)'):
                caption = wx.StaticText(proposed_fields, label=label)
                self.constraint_labels.append(caption)
                draft_layout.Add(caption, 0, wx.ALIGN_CENTER_VERTICAL)
                entry = wx.TextCtrl(proposed_fields, name='Proposed ' + label.lower())
                self.constraint_fields.append(entry)
                draft_layout.Add(entry, 1, wx.EXPAND)
                entry.Bind(wx.EVT_TEXT, self.constraint_draft_changed)
            self.constraint_fields[1].SetHint('Left X, top Y, right X, bottom Y')
            self.routing_names_label = wx.StaticText(proposed_fields, label='Nets · one per line')
            self.routing_names = wx.TextCtrl(proposed_fields, style=wx.TE_MULTILINE, size=(-1, 48))
            self.routing_names.Bind(wx.EVT_TEXT, self.constraint_draft_changed)
            draft_layout.Add(self.routing_names_label, 0, wx.ALIGN_CENTER_VERTICAL)
            draft_layout.Add(self.routing_names, 1, wx.EXPAND)
            self.routing_names_label.Hide(); self.routing_names.Hide()
            proposed_fields.SetSizer(draft_layout)
            self.constraint_edit.Bind(wx.EVT_BUTTON, self.toggle_constraint_editor)
            self.constraint_edit.Hide()
            self.constraint_editor.Hide()
            assistant_layout.Add(self.constraint_edit, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
            assistant_layout.Add(proposed_fields, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

            proposal_actions = wx.BoxSizer(wx.HORIZONTAL)
            self.constraint_preview_edits = wx.Button(assistant_page, label='Preview edits')
            self.constraint_use = wx.Button(assistant_page, label='Use settings and find alternatives')
            self.constraint_reject = wx.Button(assistant_page, label='Discard')
            proposal_actions.Add(self.constraint_preview_edits, 0, wx.RIGHT, 6)
            proposal_actions.Add(self.constraint_use, 0, wx.RIGHT, 6)
            proposal_actions.Add(self.constraint_reject)

            conversation_menu = wx.Menu()
            for button, handler, shortcut in (
                (self.constraint_edit, self.toggle_constraint_editor, 'Ctrl+Shift+E'),
                (self.constraint_preview_edits, self.preview_constraints, 'Ctrl+Shift+P'),
                (self.constraint_use, lambda event: self.use_constraints(event, search=True), 'Ctrl+Shift+U'),
            ):
                item = conversation_menu.Append(wx.ID_ANY, f'{button.GetLabel()}\t{shortcut}')
                self.Bind(wx.EVT_MENU, handler, item)
                self.Bind(wx.EVT_UPDATE_UI,
                          lambda event, control=button: event.Enable(control.IsShownOnScreen() and control.IsEnabled()),
                          item)
            menu_bar = wx.MenuBar()
            file_menu = wx.Menu()
            open_item = file_menu.Append(wx.ID_OPEN, 'Choose project…\tCtrl+O')
            path_item = file_menu.Append(wx.ID_ANY, 'Project path\tCtrl+L')
            self.Bind(wx.EVT_MENU, self.choose_board, open_item)
            self.Bind(wx.EVT_MENU, self.toggle_path, path_item)
            for item in (open_item, path_item):
                self.Bind(wx.EVT_UPDATE_UI, lambda event: event.Enable(self.navigation_available()), item)
            menu_bar.Append(file_menu, 'File')
            menu_bar.Append(conversation_menu, 'Conversation')
            routing_menu = wx.Menu()
            for action, label in (
                ('show_board', 'Show board\tCtrl+Shift+B'),
                ('show_findings', 'Show findings\tCtrl+Shift+F'),
                ('preview', 'Preview routing'),
                ('route', 'Start routing\tCtrl+Shift+R'),
                ('cancel', 'Cancel job\tCtrl+Shift+K'),
                ('acknowledge', 'I reviewed the findings and closed any KiCad review project'),
                ('accept', 'Accept and save checked copy'),
                ('reject', 'Reject result'),
                ('open_export', 'Open checked export\tCtrl+Shift+O'),
            ):
                add = routing_menu.AppendCheckItem if action == 'acknowledge' else routing_menu.Append
                item = add(wx.ID_ANY, label)
                self.Bind(wx.EVT_MENU, lambda event, name=action: gui.routing_menu_action(
                    self.routing, name, checked=event.IsChecked() if name == 'acknowledge' else False), item)
                self.Bind(wx.EVT_UPDATE_UI, lambda event, name=action: self.update_routing_menu(event, name), item)
            menu_bar.Append(routing_menu, 'Routing')
            self.SetMenuBar(menu_bar)
            assistant_inputs.SetSizer(assistant_layout)
            assistant_split = wx.BoxSizer(wx.VERTICAL)
            assistant_split.Add(assistant_inputs, 1, wx.EXPAND)
            assistant_split.Add(proposal_actions, 0, wx.ALL, 8)
            assistant_page.SetSizer(assistant_split)
            self.pages.AddPage(assistant_page, 'Request')
            schematic_page = wx.Panel(self.pages); schematic_layout = wx.BoxSizer(wx.VERTICAL)
            self.schematic_text = wx.TextCtrl(schematic_page, style=wx.TE_MULTILINE | wx.TE_READONLY,
                                             name='Saved schematic context')
            schematic_layout.Add(self.schematic_text, 1, wx.EXPAND)
            schematic_page.SetSizer(schematic_layout); self.pages.AddPage(schematic_page, 'Schematic')
            self.schematic_text.ChangeValue('Choose a saved project to see its schematic context.')
            columns.Add(board_page, 1, wx.EXPAND | wx.RIGHT, 10)
            columns.Add(self.side_panel, 0, wx.EXPAND)
            self.workspace_body.SetSizer(columns)
            root.Add(self.workspace_body, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
            self.approval_note = wx.StaticText(panel)
            root.Add(self.approval_note, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 8)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            self.find = wx.Button(panel, label='Find alternatives')
            self.qualify = wx.Button(panel, label='Approve moves and check routing')
            self.route = wx.Button(panel, label='Continue to routing…'); self.reject = wx.Button(panel, label='Reject draft')
            for button in (self.find, self.qualify, self.route): buttons.Add(button, 0, wx.RIGHT, 6)
            buttons.AddStretchSpacer(); buttons.Add(self.reject)
            root.Add(buttons, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 10)
            self.status = wx.StaticText(panel, style=wx.ST_NO_AUTORESIZE)
            self.status.Hide()
            self.status.Wrap(930); root.Add(self.status, 0, wx.EXPAND | wx.ALL, 10)
            progressrow = wx.BoxSizer(wx.HORIZONTAL)
            if on_return_live is not None:
                self.back_live = wx.Button(panel, label='Back to live companion')
                self.back_live.Bind(wx.EVT_BUTTON, self.return_to_live)
                progressrow.Add(self.back_live, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.progress = wx.Gauge(panel); progressrow.Add(self.progress, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.cancel = wx.Button(panel, label='Cancel'); progressrow.Add(self.cancel)
            root.Add(progressrow, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
            panel.SetSizer(root)
            frame_layout = wx.BoxSizer(wx.VERTICAL)
            frame_layout.Add(panel, 1, wx.EXPAND)
            self.SetSizer(frame_layout)
            self.input_controls = [self.board, self.browse, self.open_design, self.new_design, self.example, self.inspect, self.kicad_setup, self.route_saved, self.parts, self.copper_policy, self.rigid_group, self.target_region,
                self.protected_names, self.protected_route_ids, *self.region, self.load, self.save, self.find, self.original_group, self.draw_area,
                self.assistant_request, self.assistant_ask, self.route_budget, self.three_pad]
            self.pose_controls = [self.alternative, self.part, self.x, self.y, self.apply, self.reject, self.qualify]
            self.board.Bind(wx.EVT_TEXT, self.source_changed)
            self.board.Bind(wx.EVT_TEXT_ENTER, self.inspect_project)
            self.new_design.Bind(wx.EVT_BUTTON, self.start_new_design)
            self.kicad_setup.Bind(wx.EVT_BUTTON, self.open_setup_in_kicad)
            self.browse.Bind(wx.EVT_BUTTON, self.choose_board)
            self.open_design.Bind(wx.EVT_BUTTON, self.choose_board)
            self.inspect.Bind(wx.EVT_BUTTON, self.inspect_project)
            self.example.Bind(wx.EVT_BUTTON, self.open_example)
            if board: self.Bind(wx.EVT_SHOW, self.inspect_initial_project)
            self.parts.Bind(wx.EVT_CHECKLISTBOX, self.settings_changed)
            self.copper_policy.Bind(wx.EVT_CHOICE, self.policy_changed)
            self.three_pad.Bind(wx.EVT_CHECKBOX, self.three_pad_changed)
            self.rigid_group.Bind(wx.EVT_CHECKBOX, self.settings_changed)
            self.target_region.Bind(wx.EVT_CHECKBOX, self.settings_changed)
            for pane in (self.protection, self.precise, self.advanced):
                pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, lambda event: self.layout_panel())
            self.pages.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.schematic_page_changed)
            self.Bind(wx.EVT_ACTIVATE, self.activated)
            self.draw_area.Bind(wx.EVT_TOGGLEBUTTON, self.drawing_mode)
            self.Bind(wx.EVT_SIZE, self.resized)
            for field in (self.protected_names, self.protected_route_ids): field.Bind(wx.EVT_TEXT, self.settings_changed)
            for field in self.region: field.Bind(wx.EVT_TEXT, self.settings_changed)
            self.load.Bind(wx.EVT_BUTTON, self.load_settings); self.save.Bind(wx.EVT_BUTTON, self.save_settings)
            self.find.Bind(wx.EVT_BUTTON, self.find_alternatives); self.alternative.Bind(wx.EVT_CHOICE, self.choose_alternative)
            self.original_group.Bind(wx.EVT_BUTTON, self.review_original_group)
            self.part.Bind(wx.EVT_CHOICE, self.select_part)
            for field in (self.x, self.y): field.Bind(wx.EVT_TEXT, self.pending_edit)
            self.apply.Bind(wx.EVT_BUTTON, self.edit)
            self.reject.Bind(wx.EVT_BUTTON, self.reject_draft)
            self.qualify.Bind(wx.EVT_BUTTON, lambda event: self.qualify_draft(event, prepare_routing=True))
            self.route.Bind(wx.EVT_BUTTON, self.open_routing); self.cancel.Bind(wx.EVT_BUTTON, self.cancel_work)
            self.route_saved.Bind(wx.EVT_BUTTON, self.begin_saved_routing)
            self.assistant_request.Bind(wx.EVT_TEXT, self.assistant_changed)
            self.route_budget.Bind(wx.EVT_TEXT, self.settings_changed)
            self.constraint_preview.Bind(wx.EVT_BUTTON, self.preview_constraints)
            self.constraint_preview_edits.Bind(wx.EVT_BUTTON, self.preview_constraints)
            self.constraint_use.Bind(wx.EVT_BUTTON, lambda event: self.use_constraints(event, search=True))
            self.constraint_reject.Bind(wx.EVT_BUTTON, self.discard_constraints)
            self.assistant_ask.Bind(wx.EVT_BUTTON, self.ask_conversation)
            self.conversation_reset.Bind(wx.EVT_BUTTON, self.reset_conversation)
            self.conversation_kind.Bind(wx.EVT_CHOICE, self.reset_conversation)
            self.Bind(wx.EVT_CLOSE, self.close)
            self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.tick, self.timer); self.timer.Start(150)
            self.refresh(); self.layout_panel()
            if not board:
                self.open_design.SetFocus()

        def layout_panel(self):
            self.Layout()
            self.panel.Layout()
            if hasattr(self, 'workspace_body'):
                self.workspace_body.Layout()
                self.side_panel.Layout()
            if hasattr(self, 'controls'):self.controls.FitInside()
            if hasattr(self, 'request_controls'):
                self.request_controls.GetParent().Layout()
                self.request_controls.FitInside()
            if hasattr(self, 'board_page'):self.board_page.Layout()

        def update_routing_menu(self, event, action):
            available = gui.routing_menu_ready(self.routing, action)
            event.Enable(available)
            if action == 'acknowledge':
                event.Check(available and self.routing.inspected.GetValue())

        def message(self, text):
            self.status.SetLabel(text)
            self.status.Show(bool(text))
            self.status.Wrap(max(340, self.GetClientSize().width - 30))
            self.layout_panel()

        def resized(self, event):
            if hasattr(self, 'status'):
                self.status.Wrap(max(340, self.GetClientSize().width - 30))
            event.Skip()

        def preview_failed(self, reason):
            # Paint/resize can fail after a previous successful presentation.
            # Revoke directly, without retrying the same broken presentation.
            self.validation_revoked = self.qualified is not None or self.validation_revoked
            self.gate.invalidate(dirty=self.gate.dirty)
            self.qualified = None
            self.routing_handoff = None
            self.picture.SetScene(None)
            if getattr(self, 'constraint_offer', None) is not None:
                self.constraint_preview_error(reason)
            if self.routing is not None:
                self.routing.Close()
            self.findings.SetValue('Placement preview refused: ' + reason
                + '\nNo current placement validation. The draft is retained; review acknowledgement is cleared.')
            self.refresh(); self.message('The board preview could not be drawn. Approval and routing handoff were revoked. Review the detailed findings before retrying.')

        def preview_ready(self):
            # A resize/hidden notebook page may temporarily discard its bitmap.
            # Refresh the current gates after rendering, never resurrect a ticket.
            if not self.gate.closed:
                self.refresh()
                pending = self.routing_handoff
                if pending is not None and self.picture.Ready():
                    self.routing_handoff = None
                    job, result = pending
                    if (self.job is job and not job.cancel_requested and self.qualified is result
                            and not self.busy and self.routing is None):
                        self.open_routing(None, preview=True)

        def overview(self):
            """Passive source view before a draft exists; never validation."""
            context = getattr(self, 'saved_route_context', None)
            captured = self.inspection if self.inspection is not None else (context or {}).get('static')
            source = Path(captured['source']) if captured is not None else None
            name = source.stem if source is not None else ''
            self.SetTitle('Copperpath — ' + (name or 'Open project'))
            self.project_title.SetLabelText(name or 'Saved project')
            self.project_title.SetToolTip(str(source) if source is not None else '')
            if self.inspection is None:
                setup = (context or {}).get('pcb_setup')
                self.picture.SetEmptyNote('PCB setup continues in KiCad.' if setup else
                    'Choose a saved project to see its board and components.')
                self.set_board_scene(context['scene'] if context is not None else None)
                if context is not None and not setup:
                    self.board_legend = ('Saved snapshot · Read-only view' if context.get('open_in_kicad')
                                         else 'Saved front copper · Read-only view')
                    self.constraint_key.SetLabel(self.board_legend)
                    self.region_summary.SetLabel('Placement unavailable for this project.')
                else:
                    self.region_summary.SetLabel('Movement area becomes available after inspection.')
                return
            observation = self.inspection['observation']
            bounds = observation['outline']['bounds_nm']
            try:
                region = [millimetres(field.GetValue()) for field in self.region]
                placement_view._rect(region)
                area_text = ('Area: (' + ', '.join(mm(n) for n in region[:2])
                    + ') to (' + ', '.join(mm(n) for n in region[2:]) + ') mm')
                if self.target_region.GetValue():
                    area_text += '\nStart outside; place inside this area.'
                self.region_summary.SetLabel(area_text)
            except ValueError:
                region = bounds
                self.region_summary.SetLabel('Enter a valid movement area. The board outline is shown for reference.')
            selected = [row['uuid'] for i, row in enumerate(self.inspection['components'])
                if self.parts.IsChecked(i)]
            anchors = {row['uuid']: row['position_nm'] for row in observation['footprints']}
            display = placement_view.scene(observation,
                {identity: anchors[identity] for identity in selected}, selected, region,
                annotation_context=self.inspection.get('annotation_context'),
                protection=(True, (), ()))
            self.set_board_scene(display)
            self.region_summary.Wrap(264)
            selected_refs = [row['reference'] for row in self.inspection['components'] if row['uuid'] in selected]
            source_readout = (source_native_findings(self.inspection, self.saved_native) if self.saved_native is not None
                              else 'Saved project inspection. KiCad connectivity has yet to be checked.')
            self.findings.SetValue(source_readout + '\n\nPlacement settings\n'
                + 'Selected to move: ' + (', '.join(selected_refs) or 'none')
                + '\nEvery unselected component stays fixed.\n'
                + ('Affected unlocked nets may be rebuilt only after the exact draft and copper plan are reviewed. '
                    'No copper has been changed.\n' if self.rebuild_copper() else copper_findings(None) + '\n')
                + '\n\nComponents\n' + component_findings(self.inspection, rebuild=self.rebuild_copper())
                + '\n\nSupported constraints and limits\n'
                + '\n'.join(placement_limits(self.inspection, rebuild=self.rebuild_copper(),
                    grouped=self.rigid_group.GetValue(), region_initialization=self.target_region.GetValue())))

        def set_board_scene(self, scene, *, rebuild=False):
            self.board_scene = scene
            self.board_legend = ('Blue selected · Slate fixed · Amber retained · Green zones'
                                 if scene is not None else '')
            if rebuild:
                self.board_legend = 'Blue selected · Slate fixed · Amber retained · Green zones. Rebuild plan in Findings.'
            self.picture.SetScene(scene)
            self.constraint_key.SetLabel(self.board_legend)

        def schematic_page_changed(self, event):
            if event.GetSelection() in (2, 3):
                self.update_schematic_view()
            event.Skip()

        def activated(self, event):
            if event.GetActive() and self.pages.GetSelection() in (2, 3):
                self.update_schematic_view()
            event.Skip()

        def update_schematic_view(self):
            note = ''
            if self.schematic is None:
                text = self.schematic_refusal or 'Choose a saved project to see its schematic context.'
                if self.schematic_refusal.startswith('Schematic context needs a fresh inspection.'):
                    note = 'Refresh inspection to update saved schematic context.'
            else:
                text, note = self.current_schematic_readout()
            self.schematic_text.ChangeValue(text)
            if hasattr(self, 'assistant_context'):
                self.assistant_context.SetLabel(note)
                self.assistant_context.Show(bool(note))
                if note:
                    self.assistant_context.Wrap(self.FromDIP(306))
                self.request_controls.Layout(); self.request_controls.FitInside()

        def current_schematic_readout(self):
            try:
                schematic_context.current(self.schematic, self.board.GetValue())
                if (self.constraint_offer is not None and not self.constraint_edited
                        and self.constraint_offer['kind'] != conversation.ROUTING_KIND):
                    names = self.constraint_offer['after']['selected_refs']
                    prefix = 'Proposed selection\n\n'
                elif self.inspection is not None:
                    names = [row['reference'] for index, row in enumerate(self.inspection['components'])
                             if self.parts.IsChecked(index)]
                    prefix = ''
                else:
                    names, prefix = [], ''
                return (prefix + schematic_context.describe(self.schematic, names),
                        schematic_context.selection_summary(self.schematic, names, proposed=bool(prefix)))
            except (OSError, ValueError, Rejected) as exc:
                self.schematic = None
                self.schematic_refusal = 'Schematic context needs a fresh inspection. ' + str(exc)
                return self.schematic_refusal, 'Refresh inspection to update saved schematic context.'

        def pick_on_board(self, identity):
            if self.busy or self.gate.closed or self.inspection is None:
                return
            if self.constraint_offer is not None:
                self.message('Use or discard the proposed settings before changing the selection.')
                return
            review = self.gate.review
            if review is not None:
                if identity in review.settings['selected']:
                    self.part.SetSelection(review.settings['selected'].index(identity))
                    self.coordinates()
                    self.message('Edit this component numerically, then Update positions. All constraints remain enforced.')
                else:
                    self.message('This component stays fixed in the current draft. Change the component list to start a new draft.')
                return
            rows = self.inspection['components']
            matches = [(i, row) for i, row in enumerate(rows) if row['uuid'] == identity]
            if len(matches) != 1:
                return
            index, row = matches[0]
            reasons = blocking_reasons(row, rebuild=self.rebuild_copper())
            if reasons:
                self.message(row['reference'] + ' stays fixed: ' + '; '.join(reasons))
                return
            self.invalidate_copilot()
            self.parts.Check(index, not self.parts.IsChecked(index))
            update_target_area(self)
            self.revoke(discard=True)
            if self.pages.GetSelection() in (2, 3):
                self.update_schematic_view()
            self.message(row['reference'] + (' selected to move.' if self.parts.IsChecked(index)
                else ' will stay fixed.') + ' Choose the allowed area, then Find alternatives.')

        def drawing_mode(self, _):
            enabled = self.draw_area.GetValue() and self.inspection is not None and not self.busy
            self.draw_area.SetValue(enabled); self.picture.draw_area = enabled
            if enabled:
                self.picture.SetFocus()
                self.message('Drag inside the board to propose a movement area. Escape abandons the drag. Numeric controls remain available.')
            else:
                self.message('Component selection enabled. Click a component or use the list.')

        def area_on_board(self, region, error=None):
            if self.busy or self.gate.closed or self.inspection is None:
                return
            if self.constraint_offer is not None:
                self.message('Use or discard the proposed settings before drawing a new movement area.')
                return
            if error is not None:
                self.message('Area unchanged: ' + error); return
            try:
                region = list(placement_view._rect(region))
                bounds = self.inspection['observation']['outline']['bounds_nm']
                if not (bounds[0] <= region[0] < region[2] <= bounds[2]
                        and bounds[1] <= region[1] < region[3] <= bounds[3]):
                    raise ValueError('Draw the area inside the board outline.')
            except (TypeError, ValueError) as exc:
                self.message('Area unchanged: ' + str(exc)); return
            self.invalidate_copilot()
            self.updating = True
            try:
                for field, coordinate in zip(self.region, region):
                    field.ChangeValue(mm(coordinate))
            finally:
                self.updating = False
            self.automatic_target_area = True
            self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
            update_target_area(self)
            self.draw_area.SetValue(False); self.picture.draw_area = False
            self.revoke(discard=True)
            self.message(('Target area set. Search will look for valid positions inside it.'
                          if self.target_region.GetValue() else 'Target area set. Choose Find alternatives when ready.'))

        def refresh(self):
            for control in self.input_controls: control.Enable(not self.busy)
            if hasattr(self, 'back_live'):
                self.back_live.Enable(not self.busy and self.routing is None and not self.gate.closed)
            saved_context = getattr(self, 'saved_route_context', None) or {}
            passive_only = bool(saved_context.get('open_in_kicad') or saved_context.get('pcb_setup'))
            if hasattr(self, 'example'):
                source_entered = bool(self.board.GetValue().strip())
                self.welcome.Show(not source_entered)
                self.project_bar.Show(source_entered)
                self.workspace_body.Show(source_entered)
                self.example.Show(self.example_project.is_file())
                mode = ('Last saved view · Project open in KiCad' if saved_context.get('open_in_kicad') else
                        'Saved project · PCB setup' if saved_context.get('pcb_setup') else 'Saved workspace')
                self.project_mode.SetLabel(mode)
                self.copper_controls.Show(self.inspection is not None)
                if self.inspection is None and not saved_context:
                    self.picture.SetEmptyNote('Checking the saved KiCad project…' if self.busy else
                                              'Choose a saved project to display its board.')
                self.kicad_setup.Show(source_entered and launcher_manifest is not None
                                      and saved_context.get('pcb_setup') in PCB_SETUP_GUIDANCE
                                      and not saved_context.get('open_in_kicad'))
                self.route_saved.Show(source_entered and not passive_only)
            constraint_pending = getattr(self, 'constraint_offer', None) is not None
            scope = self.inspection['observation']['scope'] if self.inspection is not None else None
            baseline_scope = intent.contract.source_baseline_scope(scope)
            three_pad = scope == intent.contract.THREE_PAD_SCOPE
            minimum_parts = 2 if self.rigid_group.GetValue() else 1
            selected_count = len(self.parts.GetCheckedItems()) if self.inspection is not None else 0
            selection_ready = selected_count == 1 if three_pad else selected_count >= minimum_parts
            if hasattr(self, 'three_pad'):
                self.three_pad.Enable(not self.busy and bool(self.board.GetValue().strip()))
                self.copper_policy.Enable(not self.busy and not self.three_pad.GetValue())
            if hasattr(self, 'toolbar_pick'):
                self.toolbar_pick.Show(bool(self.toolbar_selection))
                self.toolbar_pick.Enable(bool(self.toolbar_selection) and self.inspection is not None
                                         and not self.busy and not constraint_pending)
            self.rigid_group.Enable(not self.busy and not baseline_scope)
            region_supported = baseline_scope or (scope == intent.contract.CONTEXT_SCOPE
                                                   and self.copper_policy.GetSelection() == 0)
            self.target_region.Enable(not self.busy and region_supported and not self.rigid_group.GetValue())
            for control in (self.protected_names, self.protected_route_ids):
                control.Enable(not self.busy and self.copper_policy.GetSelection() == 1)
            self.find.Enable(not self.busy and not constraint_pending and selection_ready)
            self.original_group.Enable(not self.busy and self.inspection is not None
                and not baseline_scope and self.rigid_group.GetValue())
            self.save.Enable(not self.busy and self.inspection is not None)
            for control in self.pose_controls: control.Enable(not self.busy and self.gate.review is not None)
            self.qualify.Enable(not self.busy and not constraint_pending and self.routing is None
                and self.gate.review is not None and not self.gate.dirty and self.picture.Ready())
            self.route.Enable(not self.busy and not constraint_pending and self.qualified is not None and self.picture.Ready())
            self.cancel.Enable(self.busy)
            if hasattr(self, 'conversation_kind'):
                routing = self.conversation_kind.GetSelection() == 1
                self.assistant_ask.Enable(not self.busy and not passive_only
                    and not constraint_pending and (bool(self.board.GetValue()) if routing else self.inspection is not None))
                for control in (self.assistant_ask, self.conversation_kind, self.conversation_reset):
                    control.Show(not constraint_pending)
                self.conversation_reset.Enable(not self.busy)
                self.conversation_kind.Enable(not self.busy)
                self.model_options.Show(not constraint_pending)
                self.history.Show(self.conversation.has_display_history or self.conversation.source is not None)
            if hasattr(self, 'assistant_use'):
                self.assistant_ask.Enable(not self.busy and self.inspection is not None)
                self.assistant_ack.Enable(not self.busy and self.pending_copilot is not None)
                self.assistant_use.Enable(not self.busy and self.pending_copilot is not None and self.assistant_ack.GetValue())
            if hasattr(self, 'constraint_preview'):
                edited = constraint_pending and self.constraint_edited
                self.constraint_preview.Show(not constraint_pending)
                self.constraint_preview.Enable(not self.busy and self.inspection is not None and not constraint_pending)
                self.constraint_edit.Enable(not self.busy and constraint_pending)
                self.constraint_preview_edits.Show(edited)
                self.constraint_preview_edits.Enable(not self.busy and edited)
                self.constraint_use.Enable(not self.busy and constraint_pending and not edited)
                self.constraint_reject.Enable(not self.busy and constraint_pending)
                self.constraint_use.Show(constraint_pending and not edited)
                self.constraint_reject.Show(constraint_pending)
                for entry in self.constraint_fields:
                    entry.Enable(not self.busy)
                if hasattr(self, 'routing_names'):
                    self.routing_names.Enable(not self.busy)
            if hasattr(self, 'draw_area'):
                self.draw_area.Show(self.inspection is not None)
                self.draw_area.Enable(not self.busy and not constraint_pending and self.inspection is not None)
                self.picture.Enable(not self.busy)
                native = (self.qualified['witness']['findings'] if self.qualified is not None else
                          self.saved_native)
                if native is not None:
                    scope = 'Validated draft' if self.qualified is not None else 'Saved source'
                    summary = scope + ' · ' + chrome.counts_text(native, 'unrouted')
                    if self.qualified is None and finish_gaps.source_delivery(native, field_mismatches_only=True)['reasons']:
                        summary = 'Saved source · Delivery blocked · See Findings'
                    self.native_summary.SetLabel(summary)
                else:
                    self.native_summary.SetLabel('')
                self.native_summary.Show(native is not None)
            if hasattr(self, 'pose_pane'):
                has_draft = self.gate.review is not None
                reviewable = has_draft and self.qualified is None and not constraint_pending and not self.busy
                needs_selection = self.inspection is not None and not (selection_ready or has_draft or constraint_pending or self.busy)
                self.pose_pane.Show(has_draft and not constraint_pending)
                notes = []
                if self.inspection is not None and not self.busy and self.rebuild_copper() and self.rebuild_routing_notice:
                    notes.append(self.rebuild_routing_notice)
                if reviewable:
                    copper = self.gate.review.copper_plan
                    review = self.gate.review
                    overview = placement_move_findings(review.observation, review.moves).splitlines()[0]
                    instruction = (f"{len(copper['removed_routes'])} routes may be rebuilt · "
                                   f"{len(copper['protected_routes'])} stay protected" if copper is not None
                                   else 'All existing copper stays protected')
                    notes.append(f'{overview} · {instruction}. See Findings for details.\n'
                                 'Close the saved project in KiCad before approval.')
                elif needs_selection:
                    notes.append('Select one eligible three-pad SMD part.' if three_pad else
                                 'Select movable parts to find alternatives. A group needs at least two parts.')
                self.approval_note.SetLabel('\n'.join(notes))
                self.approval_note.Wrap(max(340, self.GetClientSize().width - 30))
                self.approval_note.Show(bool(notes))
                self.find.Show(selection_ready and not has_draft and not constraint_pending and not self.busy)
                self.qualify.Show(reviewable)
                self.route.Show(self.qualified is not None and not constraint_pending and not self.busy)
                self.reject.Show(has_draft and not self.busy)
                self.progress.Show(self.busy); self.cancel.Show(self.busy)
                self.layout_panel()

        def revoke(self, *, dirty=False, discard=False):
            self.routing_handoff = None
            self.validation_revoked = self.qualified is not None or self.validation_revoked
            self.gate.invalidate(dirty=dirty); self.qualified = None
            # Revocation is authoritative even when the passive preview cannot
            # be redrawn. Never leave an earlier success visible during failure.
            self.refresh()
            self.findings.SetValue('No current placement validation. Review the draft and validate it before routing.')
            self.picture.SetScene(None)
            if self.routing is not None: self.routing.Close()
            redraw_error = None
            if discard:
                self.pending_coordinates.clear()
                self.editing_component = None
                self.gate.review = None
                self.alternative_labels = []; self.alternative_targets = []
                self.alternative.Set([]); self.part.Set([])
                self.x.ChangeValue(''); self.y.ChangeValue('')
                self.findings.SetValue('No current placement draft or validation. Inspect the saved project and choose components to begin again.')
                self.overview(); self.layout_panel()
            else:
                try: self.present()
                except Exception as exc:
                    redraw_error = 'Placement preview refused: ' + str(exc)
                    self.findings.SetValue(redraw_error + '\nNo current placement validation. '
                        'The previous pose and any pending coordinate text are retained; review acknowledgement is cleared.')
                    self.layout_panel()
            if redraw_error is not None:
                self.message(redraw_error)
            elif self.validation_revoked:
                self.message('Placement validation revoked. Review and validate the current draft before routing.')
            self.refresh()

        def source_changed(self, event):
            if not self.updating:
                self.toolbar_selection = ()
                self.invalidate_copilot()
                if hasattr(self, 'conversation'):
                    self.conversation.reset()
                    self.assistant_result.ChangeValue(CONVERSATION_EMPTY)
                    self.routing_source_scene = None
                if hasattr(self, 'assistant_request'):
                    self.assistant_request.ChangeValue('')
                self.editor_context = None
                self.automatic_target_area = False
                self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
                self.target_region.SetValue(False)
                if hasattr(self, 'three_pad'): self.three_pad.SetValue(False)
                self.schematic = None; self.schematic_refusal = ''
                self.rebuild_routing_notice = ''
                if hasattr(self, 'schematic_text'):
                    self.update_schematic_view()
                self.saved_route_context = None
                self.inspection = None; self.saved_native = None; self.parts.Set([]); self.revoke(discard=True)
                self.message('Choose a saved project or enter its full path and press Return.')
            if event is not None: event.Skip()

        def source_capture(self):
            return self.inspection or (self.saved_route_context or {}).get('static')

        def show_editor_context(self, captured):
            context = self.editor_context
            source, files = captured['source'], captured['source_hashes']
            if context is not None:
                self.toolbar_selection = (tuple(context['selection'])
                    if conversation.matches_saved_design(source, files, context) else ())
                self.toolbar_source = Path(source) if self.toolbar_selection else None
                label = 'Use KiCad selection'
                if self.toolbar_selection:
                    label += f' ({len(self.toolbar_selection)})'
                self.toolbar_pick.SetLabel(label)
            prior = self.conversation.summary_for(source, files)
            self.assistant_result.ChangeValue(prior or ('The saved project changed. Start a new conversation.'
                if self.conversation.source is not None else CONVERSATION_EMPTY))

        def resume_from_live(self, context, notes):
            self.editor_context = copy.deepcopy(context)
            self.toolbar_selection = ()
            self.toolbar_source = None
            if context is not None:
                self.conversation.remember_editor_notes(context, notes)
            captured = self.source_capture()
            if captured is None:
                return
            try:
                source = gui.saved_project_board(self.board.GetValue())
                if str(source) != captured['source'] or gui.source_inventory(source) != captured['source_hashes']:
                    raise ValueError('The saved project changed.')
            except (OSError, ValueError, Rejected):
                self.inspect_project(None)
                return
            self.show_editor_context(captured)
            self.refresh()

        def history_for_live(self, project):
            captured = self.source_capture()
            if captured is None or not project:
                return ''
            try:
                source = gui.saved_project_board(project)
                if str(source) == captured['source'] and gui.source_inventory(source) == captured['source_hashes']:
                    return self.conversation.summary_for(source, captured['source_hashes'], include_editor=False)
            except (OSError, ValueError, Rejected):
                pass
            return ''

        def return_to_live(self, _):
            if on_return_live is None or self.busy or self.routing is not None or self.gate.closed:
                return
            self.invalidate_copilot(keep_edited_suggestion=True)
            if self.gate.review is not None:
                self.revoke(dirty=self.gate.dirty)
            self.Hide()
            on_return_live()

        def invalidate_copilot(self, *, keep_edited_suggestion=False):
            """Changing intent cannot retain a model plan or its routing handoff."""
            previous = getattr(self, 'approved_copilot', None)
            self.copilot_generation = getattr(self, 'copilot_generation', 0) + 1
            self.pending_copilot = None; self.approved_copilot = None
            if keep_edited_suggestion and getattr(self, 'constraint_edited', False):
                if self.constraint_review is not None:
                    self.constraint_review.cancel()
                    self.constraint_review = None
                self.constraint_summary.ChangeValue('Your edits are still here. Preview them again before using these settings.')
            else:
                self.routing_source_scene = None
                if getattr(self, 'constraint_offer', None) is not None:
                    self.clear_constraint_offer('The request or project controls changed. Preview again.')
            if hasattr(self, 'assistant_ack'):
                self.assistant_ack.SetValue(False)
                self.assistant_result.SetValue('No current assistant plan. Review the controls, then ask when needed.')
            if previous is not None:
                self.revoke(dirty=self.gate.dirty)

        def assistant_changed(self, event):
            self.invalidate_copilot(); self.refresh(); event.Skip()

        def constraint_inputs(self):
            if self.inspection is None:
                raise ValueError('Inspect the saved project first.')
            area = [field.GetValue() for field in self.region]
            return dict(selected=[row['uuid'] for i, row in enumerate(self.inspection['components'])
                                  if self.parts.IsChecked(i)],
                fixed=[], region_nm=[millimetres(value) for value in area] if any(area) else None,
                region_limit_nm=self.inspection['observation']['outline']['bounds_nm'],
                route_seconds=routing_seconds(self.route_budget.GetValue().strip()),
                policy=placement_policy(self))

        def constraint_binding(self):
            return dict(request=self.assistant_request.GetValue(), revision=self.copilot_generation,
                        source=self.board.GetValue())

        def constraint_draft_terms(self):
            refs, area, seconds = (field.GetValue().strip() for field in self.constraint_fields)
            if self.constraint_offer['kind'] == conversation.ROUTING_KIND:
                return dict(nets=self.routing_names.GetValue().splitlines(),
                            route_seconds=routing_seconds(seconds))
            before = self.constraint_offer['before']
            selected_refs = None if not refs or refs == ', '.join(before['selected_refs']) else constraint_references(refs)
            return dict(selected_refs=selected_refs,
                region_nm=[millimetres(value.strip()) for value in area.split(',')] if area else None,
                route_seconds=routing_seconds(seconds) if seconds else None)

        def preview_constraints(self, _):
            if self.busy or self.gate.closed:
                return
            try:
                previous = self.constraint_offer
                if previous is None:
                    self.invalidate_copilot()
                routing = previous is not None and previous['kind'] == conversation.ROUTING_KIND
                inputs = self.conversation_routing_preferences() if routing else self.constraint_inputs()
                binding = self.constraint_binding()
                inspection = self.inspection
                review = self.constraint_review
                captured = self.source_capture() if routing and review is None else None
                arguments = local_constraint_request(binding['request']) if previous is None else self.constraint_draft_terms()

                def prepare(job, event):
                    from . import design_intent as design

                    job.check_live()
                    try:
                        if review is not None:
                            current = review
                            offer = current.revise(previous, arguments, inputs, **binding)
                        elif routing:
                            source = require_closed_source(binding['source'], inspection=captured)
                            saved = design.inspect_project(source)
                            if captured is None or saved['source_hashes'] != captured['source_hashes']:
                                raise design.PendingContextChanged('The saved project changed. Inspect it again.')
                            current = conversation.RoutingReview(saved, inputs,
                                request=binding['request'], revision=binding['revision'])
                            offer = current.receive(conversation.ROUTING_TOOL, arguments, inputs, **binding)
                        else:
                            current = design.PlacementConstraintReview(inspection, inputs,
                                request=binding['request'], revision=binding['revision'])
                            offer = current.receive('propose_placement_constraints_v2', arguments, inputs, **binding)
                    except design.PendingContextChanged as exc:
                        return None, str(exc)
                    except intent.constraints.Refused as exc:
                        if routing or exc.constraint != 'allowed_area':
                            raise
                        identity = str(exc).removeprefix('Component outside allowed region: ')
                        reference = next((part['reference'] for part in inspection['components']
                                          if part['uuid'] == identity), None)
                        if reference is None:
                            raise
                        raise ValueError(f'{reference} starts outside the movement area. '
                                         'Draw an area that includes its whole footprint, then preview again.') from exc
                    return current, offer

                def show(result):
                    current, offer = result
                    if current is None:
                        self.clear_constraint_offer('The suggestion expired. ' + offer)
                        return
                    current_inputs = self.conversation_routing_preferences() if routing else self.constraint_inputs()
                    if binding != self.constraint_binding() or inputs != current_inputs:
                        current.cancel()
                        self.clear_constraint_offer('The request or project controls changed. Preview again.')
                        raise ValueError('The request or project controls changed. Preview again.')
                    self.show_constraint_offer(current, offer)

                self.start('Checking the requested constraints against the saved project…', prepare, show)
            except (OSError, ValueError) as exc:
                self.message('Constraint suggestion refused. ' + str(exc))

        def show_constraint_offer(self, review, offer):
            self.constraint_review, self.constraint_offer = review, offer
            self.constraint_edited = False
            routing = offer['kind'] == conversation.ROUTING_KIND
            self.constraint_use.SetLabel('Use routing settings' if routing else 'Use settings and find alternatives')
            entries = ('', '', str(offer['after']['route_seconds'])) if routing else constraint_entry_values(offer)
            if hasattr(self, 'routing_names'):
                for field in (*self.constraint_labels[:2], *self.constraint_fields[:2]):
                    field.Show(not routing)
                self.routing_names_label.Show(routing)
                self.routing_names.Show(routing)
                self.routing_names.ChangeValue('\n'.join(offer['after']['nets']) if routing else '')
            for field, value in zip(self.constraint_fields, entries):
                field.ChangeValue(value)
            self.constraint_edit.Show()
            self.constraint_summary.Show()
            self.constraint_summary.ChangeValue(constraint_change_text(offer,
                conversational=getattr(self, 'conversation_offer', False)))
            self.update_constraint_map(offer)
            self.layout_panel()
            self.refresh()
            self.message('Review or edit the settings beside the board. You’ll approve any moves separately.')
            if self.constraint_use.IsShownOnScreen() and self.constraint_use.IsEnabled():
                self.constraint_use.SetFocus()

        def toggle_constraint_editor(self, _):
            if self.busy or self.constraint_offer is None:
                return
            expanded = not self.constraint_editor.IsShown()
            self.constraint_editor.Show(expanded)
            self.constraint_edit.SetLabel('Hide editable settings' if expanded else 'Edit suggestion')
            self.layout_panel()
            if expanded:
                first_field = (self.routing_names if self.constraint_offer['kind'] == conversation.ROUTING_KIND
                               else self.constraint_fields[0])
                first_field.SetFocus()

        def constraint_draft_changed(self, event):
            if self.constraint_offer is not None:
                if not self.constraint_edited:
                    self.constraint_edited = True
                    routing = self.constraint_offer['kind'] == conversation.ROUTING_KIND
                    self.update_constraint_map(self.constraint_offer if routing else None)
                self.constraint_summary.ChangeValue('Preview your edits before using these settings.')
                self.refresh()
            event.Skip()

        def clear_constraint_offer(self, message):
            if self.constraint_review is not None:
                self.constraint_review.cancel()
            self.constraint_review = self.constraint_offer = None
            self.constraint_edited = False
            self.conversation_offer = False
            self.constraint_editor.Hide()
            self.constraint_edit.SetLabel('Edit suggestion')
            self.constraint_edit.Hide()
            self.constraint_summary.ChangeValue(message)
            self.constraint_summary.Show(bool(message))
            self.update_constraint_map()
            self.layout_panel()

        def update_constraint_map(self, offer=None):
            try:
                routing = offer is not None and offer['kind'] == conversation.ROUTING_KIND
                if routing:
                    captured = getattr(self, 'routing_source_scene', None)
                    value = captured[2] if captured is not None else None
                else:
                    value = self.board_scene if offer is None else constraint_scene(self.inspection, self.constraint_inputs(), offer)
                self.picture.SetScene(value)
                pending_copper = offer is not None and offer.get('copper_plan') is not None
                legend = ('Proposal · Blue selected · Slate fixed · Amber retained · Rose may be rebuilt'
                          if pending_copper else 'Proposal · Blue selected · Slate fixed · Amber retained')
                if routing:
                    legend = ('Saved board · Review routing changes after the run.' if value is not None else
                              'Saved board drawing unavailable. You can still preview routing.')
                self.constraint_key.SetLabel(self.board_legend if offer is None else legend)
                if hasattr(self, 'schematic_text') and self.pages.GetSelection() in (2, 3):
                    self.update_schematic_view()
            except (KeyError, TypeError, ValueError, OSError) as exc:
                self.picture.SetScene(None)
                self.constraint_preview_error(str(exc))

        def constraint_preview_error(self, reason):
            self.constraint_key.SetLabel('Board preview unavailable')
            if self.constraint_offer is not None and not self.constraint_edited:
                self.constraint_summary.ChangeValue(constraint_change_text(self.constraint_offer)
                    + '\n\nBoard preview unavailable. ' + reason)
            self.message('Constraint board preview unavailable. ' + reason)

        def discard_constraints(self, _):
            self.clear_constraint_offer('Suggestion discarded. Your ordinary settings are unchanged.')
            self.refresh()

        def use_constraints(self, _, *, search=False):
            if (self.busy or self.gate.closed or self.constraint_review is None
                    or self.constraint_offer is None or self.constraint_edited):
                return
            try:
                if self.constraint_offer['kind'] == conversation.ROUTING_KIND:
                    terms = self.constraint_draft_terms()
                    if terms != self.constraint_offer['after']:
                        raise ValueError('Preview the edited suggestion before using it.')
                    values = self.constraint_review.adopt(self.constraint_offer,
                        self.conversation_routing_preferences(), **self.constraint_binding())
                    self.clear_constraint_offer('Routing settings adopted. Preview before entering the router.')
                    self.open_saved_routing(values)
                    return
                if tuple(field.GetValue() for field in self.constraint_fields) != constraint_entry_values(self.constraint_offer):
                    raise ValueError('Preview the edited suggestion before using it.')
                # Recheck even when the files changed outside the application's controls.
                values = self.constraint_review.adopt(self.constraint_offer, self.constraint_inputs(),
                                                      **self.constraint_binding())
            except (OSError, ValueError) as exc:
                self.clear_constraint_offer('Suggestion unavailable. ' + str(exc))
                self.message('Refresh inspection, then preview a fresh suggestion.')
                self.refresh()
                return
            adopted_summary = constraint_change_text(self.constraint_offer, adopted=True)
            local_request = None if self.conversation_offer else self.assistant_request.GetValue()
            self.clear_constraint_offer('')
            self.updating = True
            try:
                selected = set(values['selected'])
                for i, row in enumerate(self.inspection['components']):
                    self.parts.Check(i, row['uuid'] in selected)
                area = values['region_nm']
                for i, field in enumerate(self.region):
                    field.ChangeValue(mm(area[i]) if area is not None else '')
                self.route_budget.ChangeValue(str(values['route_seconds']))
                if values['placement_settings'] is not None:
                    self.automatic_target_area = False
                    start = values['placement_settings'].get('region_initialization')
                    self.target_start_policy = start or intent.prototype.EXACT_TRACK_REGION_POLICY
                    self.target_region.SetValue(start is not None)
            finally:
                self.updating = False
            self.conversation.remember_placement_adoption(adopted_summary, inspection=self.inspection,
                                                         local_request=local_request)
            self.assistant_result.ChangeValue(self.conversation.summary_for(
                self.inspection['source'], self.inspection['source_hashes']))
            self.assistant_result.ShowPosition(0)
            self.revoke(discard=True)
            if self.pages.GetSelection() in (2, 3):
                self.update_schematic_view()
            if search:
                self.find_alternatives(None)
            else:
                self.message('Settings applied. Review the board, then choose Find alternatives.')

        def reset_conversation(self, _):
            if self.busy:
                return
            self.invalidate_copilot()
            self.conversation.reset()
            self.assistant_result.ChangeValue(CONVERSATION_EMPTY)
            self.refresh()

        def conversation_routing_preferences(self):
            return gui.pref.validate(dict(gui.pref.DEFAULTS, scope='partial_completion',
                seconds=routing_seconds(self.route_budget.GetValue().strip())))

        def ask_conversation(self, _):
            if self.busy or self.gate.closed or self.routing is not None:
                return
            saved_context = getattr(self, 'saved_route_context', None) or {}
            if saved_context.get('pcb_setup'):
                self.message('Finish PCB setup in KiCad, then refresh inspection before making a proposal.')
                return
            if saved_context.get('open_in_kicad'):
                self.message('Close the project in KiCad and refresh inspection before making a proposal.')
                return
            from . import design_intent as design, hosted_intent as hosted

            try:
                self.invalidate_copilot()
                binding = self.constraint_binding()
                transcript = self.conversation.history(binding['request'])
                routing = self.conversation_kind.GetSelection() == 1
                controls = self.conversation_routing_preferences() if routing else self.constraint_inputs()
                placement = self.inspection

                def stage(job, cancelled):
                    source = require_closed_source(binding['source'], inspection=placement if not routing else None)
                    inspection = design.inspect_project(source) if routing else placement
                    if inspection.get('pcb_setup'):
                        raise ValueError('Finish PCB setup in KiCad and refresh inspection before making a proposal.')
                    self.conversation.check_source(inspection, routing)
                    review = (conversation.RoutingReview if routing else design.PlacementConstraintReview)(
                        inspection, controls, request=binding['request'], revision=binding['revision'])
                    prepared = hosted.prepare_conversation(review, binding['request'], transcript,
                                                            inspection=inspection, routing=routing)
                    scene = saved_routing_scene(inspection, placement) if routing else None
                    return review, inspection, prepared, scene

                def current():
                    inputs = self.conversation_routing_preferences() if routing else self.constraint_inputs()
                    if binding != self.constraint_binding() or controls != inputs or routing != (self.conversation_kind.GetSelection() == 1):
                        raise ValueError('The request or ordinary settings changed. Send a new request.')

                def show(result, review, inspection, scene):
                    current()
                    require_closed_source(binding['source'], inspection=inspection)
                    proposal, clarification = result['proposal'], result['clarification']
                    identity = self.conversation.check_source(inspection, routing)
                    self.conversation.remember(binding['request'], proposal, clarification, source=identity)
                    self.assistant_result.ChangeValue(self.conversation.summary_for(*identity[:2]))
                    self.assistant_result.SetInsertionPointEnd()
                    if proposal is not None:
                        # Changing the ordinary settings takes a later deliberate action.
                        self.routing_source_scene = ((inspection['source'], inspection['source_hashes'], scene)
                                                     if scene is not None else None)
                        self.conversation_offer = True
                        self.show_constraint_offer(review, proposal)
                    else:
                        question = design.read_design_clarification(clarification)
                        self.constraint_summary.ChangeValue('\n'.join(question['questions']))
                        self.constraint_summary.Show()
                        self.message('This request needs a supported alternative.' if question['status'] == 'unsupported'
                                     else 'Enter your answer and review the next request before sending.')
                        self.assistant_request.SetFocus(); self.assistant_request.SelectAll()

                def ready(value):
                    review, inspection, prepared, scene = value
                    current()
                    if conversation_reply is not None:
                        tool, arguments = conversation_reply(copy.deepcopy(prepared['consent_summary']['data']))
                        answer = review.receive(tool, arguments, controls, **binding)
                        show({'proposal': None if tool == 'clarify_design_request' else answer,
                              'clarification': answer if tool == 'clarify_design_request' else None},
                             review, inspection, scene)
                        return
                    path = self.owned_workspace() / ('assistant-spend-' + uuid.uuid4().hex + '.json')
                    consent = hosted.make_consent(prepared, ledger_path=path)
                    choice = hosted_consent(wx, self, prepared, consent)
                    if choice is None:
                        self.message('Request cancelled. Your conversation and settings are unchanged.')
                        return
                    private = {'credential': choice[0]}; approved = choice[1]

                    def send(job, event):
                        try:
                            job.check_live()
                            if binding['revision'] != self.copilot_generation:
                                raise ValueError('The request changed before sending.')
                            return hosted.propose_conversation(review, controls, binding, transcript, inspection,
                                routing=routing, credential=private['credential'], consent=approved,
                                ledger_path=path, cancel_event=event)
                        finally:
                            private.clear()
                    try:
                        self.start('Waiting for one consented conversation turn…', send,
                                   lambda result: show(result, review, inspection, scene))
                    except BaseException:
                        private.clear()
                        raise
                    finally:
                        choice = None

                self.start('Checking the saved project and request…', stage, ready)
            except (OSError, ValueError, Rejected) as exc:
                self.message('Conversation unavailable: ' + str(exc))
                self.refresh()

        def current_copilot_context(self):
            if self.inspection is None:
                raise ValueError('Inspect the saved project and choose the parts and movement area first.')
            return copilot_context(self.inspection, self.options(), self.route_budget.GetValue().strip())

        def check_copilot_plan(self, *, full=True):
            approved = self.approved_copilot
            if approved is None: raise ValueError('Review and explicitly approve a current assistant plan first.')
            if (approved['generation'] != self.copilot_generation
                    or self.assistant_request.GetValue() != approved['request']
                    or gui.canonical(self.board.GetValue()) != Path(approved['proposal']['source'])
                    or intent.constraints.encoded(self.options(validate_geometry=False)) !=
                        intent.constraints.encoded(approved['proposal']['placement_settings'])
                    or routing_seconds(self.route_budget.GetValue().strip()) != approved['context']['route_seconds']):
                raise ValueError('The request, source or visible constraints changed. Review a new plan before continuing.')
            if full:
                from . import design_intent
                design_intent.validate_pending_placement_route_proposal(self.inspection,
                    self.current_copilot_context(), approved['proposal'], approved['proposal']['intent'])
            return approved

        def ask_copilot(self, _):
            if self.busy or self.gate.closed: return
            try:
                self.invalidate_copilot()
                context = self.current_copilot_context(); inspection = copy.deepcopy(self.inspection)
                text = self.assistant_request.GetValue(); generation = self.copilot_generation
                if not text.strip(): raise ValueError('Describe the placement and routing request first.')
                from . import hosted_intent
                ledger = self.owned_workspace() / ('assistant-spend-' + uuid.uuid4().hex + '.json')
                def prepare(job, event):
                    prepared = hosted_intent.prepare_request(inspection, context, text)
                    consent = hosted_intent.make_consent(prepared, ledger_path=ledger)
                    hosted_intent.probe_tls(cancel_event=event)
                    job.check_live()
                    return prepared, consent
                def ready(value):
                    if generation != self.copilot_generation or self.current_copilot_context() != context:
                        raise ValueError('Inputs changed before consent. Nothing was sent.')
                    choice = hosted_consent(wx, self, value[0], value[1])
                    if choice is None:
                        self.message('Assistant request cancelled before sending. Ordinary controls remain available.'); return
                    private = {'credential': choice[0]}; consent = choice[1]
                    def request(job, event):
                        try:
                            job.check_live()
                            if generation != self.copilot_generation:
                                raise ValueError('The request changed before sending. Nothing was sent.')
                            return hosted_intent.propose_placement_route(inspection, context, text,
                                credential=private['credential'], consent=consent, ledger_path=ledger, cancel_event=event)
                        finally:
                            private.clear()
                    try:
                        self.start('Waiting for one consented plan · no CAD operation or automatic approval…', request,
                            lambda result: self.receive_copilot(result, context, generation, text))
                    except BaseException:
                        private.clear(); raise
                    finally:
                        # The worker alone retains the private holder while active.
                        if self.gate.closed: private.clear()
                        choice = None
                self.start('Checking the exact HTTPS worker before private credential entry · no model request…', prepare, ready)
            except Exception as exc:
                self.invalidate_copilot(); self.message('Assistant unavailable: ' + str(exc)); self.refresh()

        def receive_copilot(self, result, context, generation, text):
            from . import design_intent
            if generation != self.copilot_generation or text != self.assistant_request.GetValue():
                raise ValueError('The request changed while the plan was pending. The response was discarded.')
            initial = design_intent.validate_placement_route_proposal(self.inspection, context,
                design_intent.placement_request(context))
            current = self.current_copilot_context()
            design_intent.validate_pending_placement_route_proposal(self.inspection, current, initial)
            if type(result) is not dict or set(result) != {'proposal', 'clarification', 'metrics'}:
                raise ValueError('Assistant returned an unsupported result. No plan was adopted.')
            proposal = result['proposal']
            checked = design_intent.validate_pending_placement_route_proposal(self.inspection, current,
                initial, None if proposal is None else proposal['intent'])
            if proposal is None:
                question = design_intent.read_design_clarification(result['clarification'])
            elif proposal != checked or result['clarification'] is not None:
                raise ValueError('Assistant result differs from the shared validated intent. No plan was adopted.')
            write_new_json(self.owned_workspace() / ('assistant-response-' + uuid.uuid4().hex + '.json'),
                dict(schema=1, kind='autorouter.assistant-proposal-receipt.v1',
                    request_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                    context_sha256=intent.constraints.digest(current), proposal=None if proposal is None else checked,
                    clarification=question if proposal is None else None, metrics=result['metrics'],
                    execution_authorized=False, approval_granted=False, human_PCB_approval=False))
            self.pending_copilot = None; self.assistant_ack.SetValue(False)
            if proposal is None:
                self.assistant_result.SetValue('Clarification needed — no plan or operation approved.\n\n'
                    + '\n'.join(question['questions']))
                self.message('Answer by clarifying the request or visible controls, then ask again when authorized. No operation started.')
            else:
                self.pending_copilot = dict(proposal=checked, context=copy.deepcopy(current), generation=generation,
                    request=text, metrics=copy.deepcopy(result['metrics']))
                self.assistant_result.SetValue(copilot_plan_text(self.inspection, checked))
                self.message('Read the proposed plan. Approve it only if it matches your request; no component or copper changed.')
            self.refresh()

        def use_copilot_plan(self, _):
            if self.busy: return
            try:
                if self.pending_copilot is None or self.assistant_ack.GetValue() is not True:
                    raise ValueError('Read the current plan and explicitly confirm that it matches your request.')
                self.approved_copilot = copy.deepcopy(self.pending_copilot)
                self.check_copilot_plan()
                write_new_json(self.owned_workspace() / ('assistant-plan-choice-' + uuid.uuid4().hex + '.json'),
                    dict(schema=1, kind='autorouter.assistant-plan-choice.v1', choice='use_plan_for_alternatives',
                        context_sha256=intent.constraints.digest(self.approved_copilot['context']),
                        request_sha256=hashlib.sha256(self.approved_copilot['request'].encode('utf-8')).hexdigest(),
                        proposal=self.approved_copilot['proposal'], geometry_execution_authorized=False,
                        approval_granted=False, human_PCB_approval=False))
                self.pending_copilot = None; self.assistant_ack.SetValue(False)
                self.assistant_result.SetValue(copilot_plan_text(self.inspection, self.approved_copilot['proposal'])
                    .replace('waiting for your approval', 'reviewed for placement alternatives only'))
                self.pages.SetSelection(0)
                self.find_alternatives(None)
            except Exception as exc:
                self.invalidate_copilot(); self.message('Plan refused: ' + str(exc)); self.refresh()

        def settings_changed(self, event):
            if not self.updating:
                self.invalidate_copilot()
                changed = event.GetEventObject()
                if changed is self.target_region:
                    self.automatic_target_area = False
                    self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
                elif any(changed is field for field in getattr(self, 'region', ())):
                    self.automatic_target_area = True
                    self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
                if self.inspection:
                    if (self.inspection['observation']['scope'] == intent.contract.CONTEXT_SCOPE
                            and (self.rebuild_copper() or self.rigid_group.GetValue())):
                        self.target_region.SetValue(False)
                    for index, row in enumerate(self.inspection['components']):
                        if blocking_reasons(row, rebuild=self.rebuild_copper()) and self.parts.IsChecked(index):
                            self.parts.Check(index, False)
                            self.message(row['reference'] + ' stays fixed: ' + '; '.join(row['fixed_reasons']))
                    update_target_area(self)
                self.revoke(discard=True)
            event.Skip()

        def rebuild_copper(self):
            selection = self.copper_policy.GetSelection()
            if type(selection) is not int or selection not in (0, 1):
                raise ValueError('Choose an explicit existing-copper policy.')
            return selection == 1

        def refresh_parts(self):
            if self.inspection is None: return
            checked = {row['uuid'] for index, row in enumerate(self.inspection['components']) if self.parts.IsChecked(index)}
            rebuild = self.rebuild_copper()
            self.parts.Set([component_label(row, rebuild=rebuild) for row in self.inspection['components']])
            for index, row in enumerate(self.inspection['components']):
                self.parts.Check(index, row['uuid'] in checked and not blocking_reasons(row, rebuild=rebuild))
            update_target_area(self)
            self.overview()

        def policy_changed(self, event):
            if not self.updating:
                self.invalidate_copilot()
                self.revoke(discard=True)
                def committed():
                    if self.gate.closed or self.busy: return
                    self.refresh_parts(); self.refresh()
                    self.message('Copper policy changed. Review component eligibility and request new alternatives; no copper was changed.')
                wx.CallAfter(committed)
            event.Skip()

        def three_pad_changed(self, _):
            if self.three_pad.GetValue() and self.rebuild_copper():
                self.three_pad.SetValue(False)
                self.message('Choose Preserve all existing copper before enabling three-pad placement.')
                return
            self.inspect_project(None)

        def navigation_available(self):
            return not self.busy and not self.gate.closed and self.routing is None

        def choose_board(self, _):
            if not self.navigation_available():
                return
            pattern = 'KiCad projects and boards (*.kicad_pro; *.kicad_pcb)|*.kicad_pro;*.kicad_pcb'
            with wx.FileDialog(self, 'Choose a saved KiCad project', wildcard=pattern,
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    return
                selected = dialog.GetPath()
            self.open_saved_source(selected)

        def toggle_path(self, _):
            if not self.navigation_available():
                return
            show = not self.path_details.IsShown()
            self.path_details.Show(show)
            self.layout_panel()
            if show:
                self.board.SetFocus()
                self.board.SelectAll()

        def start_new_design(self, _):
            if self.busy or self.gate.closed or self.board.GetValue().strip():
                return
            guide = ('In KiCad Manager, choose File > New Project > Default. '
                     'Save the new project in its own folder, then choose Continue an existing design in Copperpath.')
            self.open_prepared_manager(guide)

        def open_setup_in_kicad(self, _):
            context = self.saved_route_context or {}
            if (self.busy or self.gate.closed or self.routing is not None or context.get('open_in_kicad')
                    or context.get('pcb_setup') not in PCB_SETUP_GUIDANCE):
                return
            self.open_prepared_manager('Finish setup in KiCad. Save and close the project, then choose Refresh inspection.',
                                       inspection=context['static'])

        def open_prepared_manager(self, guide, *, inspection=None):
            if launcher_manifest is None:
                self.message(guide)
                return
            from scripts import install_gui
            source_hint = self.board.GetValue()
            fallback = guide if inspection is None else (
                'You can open this saved project from your existing KiCad Manager. ' + guide)

            def prepare(_job, _cancelled):
                try:
                    if inspection is not None:
                        source = require_closed_source(source_hint, inspection=inspection)
                    argv, env = install_gui.prepare_new_project_manager(launcher_manifest)
                    if inspection is not None:
                        argv = [argv[0], str(source.with_suffix('.kicad_pro'))]
                    return argv, env
                except (ValueError, OSError, Rejected) as exc:
                    raise ValueError(str(exc) + ' ' + fallback) from exc

            def open_manager(material):
                argv, env = material
                if self.board.GetValue() != source_hint:
                    raise ValueError('The displayed project changed. Choose Refresh inspection first.')
                if inspection is not None:
                    require_closed_source(source_hint, inspection=inspection)
                try:
                    install_gui.require_closed_kicad()
                except ValueError as exc:
                    raise ValueError(str(exc) + ' ' + fallback) from exc
                subprocess.Popen(argv, cwd=c.ROOT, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.message(guide if inspection is None else f'Opening {Path(argv[1]).stem} in KiCad. ' + guide)

            self.start('Checking the prepared KiCad Manager… ' + guide, prepare, open_manager)

        def open_example(self, _):
            if not self.board.GetValue().strip():
                self.open_saved_source(self.example_project)

        def open_saved_source(self, selected):
            if self.busy or self.gate.closed or self.routing is not None:
                return
            try:
                selected_board = str(gui.saved_project_board(selected))
            except (OSError, ValueError, Rejected) as exc:
                self.message(str(exc)); return
            if selected_board != self.board.GetValue():
                self.board.ChangeValue(selected_board)
                self.source_changed(None)
            self.inspect_project(None)

        def inspect_initial_project(self, event):
            event.Skip()
            if event.IsShown():
                self.Unbind(wx.EVT_SHOW, handler=self.inspect_initial_project)
                if self.board.GetValue() == str(board):
                    self.inspect_project(None)

        def use_toolbar_selection(self, _):
            if (self.busy or self.gate.closed or not self.toolbar_selection
                    or self.inspection is None or self.constraint_offer is not None):
                return
            try:
                source = require_closed_source(self.board.GetValue(), inspection=self.inspection)
                if source != self.toolbar_source:
                    raise ValueError('The KiCad selection came from a different project. Select components here.')
                context = getattr(self, 'editor_context', None)
                if context is not None and not conversation.matches_saved_design(
                        source, self.inspection['source_hashes'], context):
                    raise ValueError('The KiCad selection came from an earlier saved design. Select components here.')
                rows = self.inspection['components']
                chosen = set(self.toolbar_selection)
                matches = [row for row in rows if row['uuid'] in chosen]
                if len(matches) != len(chosen) or {row['uuid'] for row in matches} != chosen:
                    raise ValueError('The KiCad selection changed or is missing from the saved board. Select components here.')
                rebuild = self.rebuild_copper()
                for row in matches:
                    reasons = blocking_reasons(row, rebuild=rebuild)
                    if reasons:
                        raise ValueError(row['reference'] + ' stays fixed: ' + ', '.join(reasons)
                                         + '. Select movable components here.')
            except (OSError, ValueError, Rejected) as exc:
                self.message(str(exc)); return
            self.invalidate_copilot()
            for index, row in enumerate(rows):
                self.parts.Check(index, row['uuid'] in chosen)
            self.toolbar_selection = ()
            update_target_area(self)
            self.revoke(discard=True)
            if len(chosen) == 1:
                self.message('One component selected from KiCad. Choose the allowed area and review alternatives.')
            else:
                self.message(f'{len(chosen)} components selected from KiCad. Review them and choose the allowed area.')

        def options(self, *, validate_geometry=True):
            if self.inspection is None: raise ValueError('Inspect the saved project first.')
            selected = [row['uuid'] for i, row in enumerate(self.inspection['components']) if self.parts.IsChecked(i)]
            value = intent.settings(selected, [millimetres(field.GetValue()) for field in self.region],
                                    **placement_policy(self))
            if validate_geometry:
                intent.facts(self.inspection, value)
            return value

        def current_review_settings(self, review):
            # Compare actual controls with already reviewed settings. Required
            # source/geometry validation remains in Review and the origin guard;
            # do not prepare the same source again just to read UI controls.
            if (gui.canonical(self.board.GetValue()) != Path(review.inspection['source'])
                    or intent.constraints.encoded(self.options(validate_geometry=False)) != intent.constraints.encoded(review.settings)):
                raise ValueError('Displayed source or placement settings changed. Request and review new alternatives.')

        def start(self, label, action, adopt):
            if self.busy or self.gate.closed: return
            self.busy = True; self.job = gui.CliJob(); job = self.job
            self.cancel_event = threading.Event(); cancelled = self.cancel_event
            generation = self.gate.generation; self.message(label); self.refresh()
            def work():
                result = None; error = None
                try:
                    job.check_live(); result = action(job, cancelled); job.check_live()
                except Exception as exc: error = str(exc)
                wx.CallAfter(self.finish, job, generation, result, error, adopt)
            threading.Thread(target=work, daemon=False).start()

        def finish(self, job, generation, result, error, adopt):
            if self.job is not job:
                return
            self.busy = False
            if self.gate.closed:
                self.finish_close(); return
            try:
                job.check_live()
                if generation != self.gate.generation: raise ValueError('Inputs changed or action was cancelled; queued result discarded.')
                if error: raise ValueError(error)
                adopt(result)
            except Exception as exc:
                self.revoke(dirty=self.gate.dirty)
                self.message('Action refused: ' + str(exc))
            self.refresh()

        def inspect_project(self, _):
            if self.busy or self.gate.closed: return
            first_inspection = self.inspection is None and self.saved_route_context is None
            three_pad = hasattr(self, 'three_pad') and self.three_pad.GetValue()
            self.invalidate_copilot()
            self.inspection = None; self.saved_native = None; self.saved_route_context = None; self.parts.Set([])
            self.revoke(discard=True)
            self.schematic = None; self.schematic_refusal = ''
            self.rebuild_routing_notice = ''
            self.update_schematic_view()
            source_hint = self.board.GetValue()
            def adopt(result):
                # The off-thread capture has no authority; bind it again at use.
                value, context, refusal, rebuild_notice, native, read_only = result
                findings = value if read_only is None else read_only['static']
                open_snapshot = read_only is not None and read_only.get('open_in_kicad', False)
                if open_snapshot:
                    source = gui.saved_project_board(self.board.GetValue())
                    if str(source) != findings['source'] or gui.source_inventory(source) != findings['source_hashes']:
                        raise ValueError('The last saved board changed before display. Click Refresh inspection.')
                else:
                    source = require_closed_source(self.board.GetValue(), inspection=findings)
                self.board.ChangeValue(str(source))
                if getattr(self, 'editor_context', None) is not None:
                    self.show_editor_context(findings)
                elif self.conversation.has_display_history:
                    prior = self.conversation.summary_for(source, findings['source_hashes'])
                    self.assistant_result.ChangeValue(prior or 'The saved project changed. Start a new conversation.')
                self.inspection = value
                self.saved_native = native
                self.schematic = context
                self.schematic_refusal = ('Schematic context unavailable. ' + refusal) if refusal else ''
                self.rebuild_routing_notice = rebuild_notice
                if read_only is not None:
                    self.saved_route_context = read_only
                    self.overview()
                    setup = read_only.get('pcb_setup')
                    if setup:
                        title, steps = PCB_SETUP_GUIDANCE[setup]
                        assigned = read_only.get('assigned_footprints')
                        if assigned is not None:
                            parts = 'component' if assigned == 1 else 'components'
                            steps = (f'The saved schematic assigns footprints to {assigned} {parts}. '
                                'Review ERC in KiCad, then use Update PCB from Schematic (F8).')
                        details = [title, steps, 'Save and close the KiCad project, then choose Refresh inspection.']
                        status = title + (' Choose Open in KiCad to continue.' if launcher_manifest is not None and not open_snapshot
                                          else ' See Findings for the next step in KiCad.')
                        if open_snapshot:
                            details.append('The snapshot uses the saved files. Unsaved editor changes stay in KiCad.')
                    elif open_snapshot:
                        details = ['Last saved board. Unsaved changes in KiCad are unavailable here.', read_only['reason']]
                        status = 'Showing the last saved board. Close the project in KiCad, then refresh inspection.'
                    else:
                        details = ['Placement is unavailable for this saved project.', read_only['reason'],
                                   'Choose Route saved board and preview your intended routing scope.']
                        tie = findings.get('fixed_net_tie')
                        if tie is not None:
                            details.append(f"Keep fixed tie {tie['reference']} and its bridge. Choose Selected nets and leave "
                                           + ', '.join(tie['nets']) + ' unselected.')
                        status = 'Read-only saved board. See Findings before previewing routing.'
                    self.findings.SetValue('\n\n'.join(details))
                    self.pages.SetSelection(1)
                    self.update_schematic_view()
                    self.message(status)
                    return
                if intent.contract.source_baseline_scope(value['observation']['scope']):
                    self.rigid_group.SetValue(False)
                self.automatic_target_area = False
                self.target_start_policy = intent.prototype.EXACT_TRACK_REGION_POLICY
                self.target_region.SetValue(False)
                rebuild = self.rebuild_copper()
                self.parts.Set([component_label(row, rebuild=rebuild) for row in value['components']])
                self.updating = True
                try:
                    for field,coordinate in zip(self.region,value['observation']['outline']['bounds_nm']):field.ChangeValue(mm(coordinate))
                finally:self.updating=False
                if first_inspection:
                    self.pages.ChangeSelection(2)
                self.overview()
                self.update_schematic_view()
                if native is not None and finish_gaps.source_delivery(native, field_mismatches_only=True)['reasons']:
                    self.pages.SetSelection(1)
                    self.message('The saved source blocks checked delivery. Review Findings before continuing.')
                elif three_pad:
                    self.message('Three-pad placement ready. Select one eligible part. All existing copper stays in place.')
                elif native is not None and native['opens'] == native['blocking'] == 0:
                    self.message(gui.no_missing_connections_message(native['warnings']))
                else:
                    self.message('Saved board ready. Select parts, preview a request, or route the saved board.')
                    if first_inspection and self.pages.GetSelection() == 2:
                        self.refresh()
                        self.assistant_request.SetFocus()
            def read_only_capture(source, reason, *, open_in_kicad=False, static=None):
                from . import design_intent, review_view
                if static is None:
                    static = design_intent.inspect_project(source)
                setup = static.get('pcb_setup')
                scene = review_view.saved_board_front(static)
                if scene is None and not setup:
                    return None
                assigned = None
                if open_in_kicad:
                    # Avoid mixing context from files an editor may be saving.
                    schematic = (None, 'Close the project in KiCad and refresh to inspect the saved schematic.')
                else:
                    require_closed_source(source, inspection=static)
                    if setup == 'footprints_needed':
                        try:
                            assigned = schematic_context.assigned_footprint_count(source, static['source_hashes'])
                        except (OSError, TypeError, ValueError, Rejected):
                            schematic = (None, 'See Findings for the PCB setup steps.')
                        else:
                            schematic = (None, 'Update PCB from Schematic in KiCad to see linked PCB components.')
                    else:
                        schematic = schematic_context.observe(source, static['source_hashes'])
                reason = gui.short_failure_reason(reason) or 'The saved board exceeds the current placement scope.'
                context = dict(static=static, scene=scene, reason=reason, open_in_kicad=open_in_kicad,
                               pcb_setup=setup, assigned_footprints=assigned)
                return (None, *schematic, '', None, context)

            def inspect(job, event):
                source = str(gui.saved_project_board(source_hint))
                try:
                    require_closed_source(source)
                except SavedProjectOpen as lock:
                    try:
                        captured = read_only_capture(source, str(lock), open_in_kicad=True)
                    except (OSError, ValueError, Rejected):
                        raise lock from None
                    if captured is None:
                        raise
                    return captured
                try:
                    value = intent.inspect_saved(source)
                except (ValueError, Rejected, IndexError, TypeError) as exc:
                    from . import design_intent
                    try:
                        static = design_intent.inspect_project(source)
                    except design_intent.IntentError:
                        raise exc from None
                    reason = str(exc)
                    if not static.get('pcb_setup'):
                        if reason == 'Exact two outer copper layers required':
                            reason = 'Placement currently requires a board with front and back copper layers only.'
                        elif (not isinstance(exc, intent.contract.UnsupportedPlacement)
                              and not reason.startswith('Unsupported placement geometry or setting in ')):
                            raise
                    captured = read_only_capture(source, reason, static=static)
                    if captured is None:
                        raise
                    return captured
                scope = value['observation']['scope']
                if three_pad or intent.contract.fixed_context_scope(scope) or c.NATIVE_VERSION == '10.0.7' and scope == intent.contract.ORDINARY_SCOPE:
                    require_closed_source(source, inspection=value)
                    workspace = self.owned_workspace()
                    output = workspace / ('native-inspection-' + uuid.uuid4().hex)
                    argv = [str(c.ROOT/'.venv/bin/python'), '-B', '-m', 'autorouter',
                            'inspect-project', source, '--seconds', '60', '--placement-context', '--output', str(output)]
                    if three_pad: argv.append('--three-pad-placement')
                    process = job.run(argv,
                        workspace / ('native-inspection-' + uuid.uuid4().hex + '.log'), timeout=75)
                    job.check_live()
                    if process['exit_code'] != 0 or process['log_truncated'] or process['cancel_requested']:
                        raise ValueError('Native placement inspection refused; private findings/logs: ' + str(output))
                    value = intent.inspect_saved(source, native_context=output/'inspection.json')
                return (value, *schematic_context.observe(source, value['source_hashes']), affected_routing_notice(source),
                        inspected_native_findings(value), None)
            self.start('Opening the saved project… Checking components, copper and schematic context.', inspect, adopt)

        def load_settings(self, _):
            try:
                if self.inspection is None: raise ValueError('Inspect the saved project first.')
                with wx.FileDialog(self, 'Load placement settings', wildcard='JSON (*.json)|*.json', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
                    if dialog.ShowModal() != wx.ID_OK: return
                    value = intent.load_settings(dialog.GetPath())
                self.invalidate_copilot(); captured = self.inspection
                policy_changed = intent.settings_scope(value) != captured['observation']['scope']
                if policy_changed:
                    if intent.contract.THREE_PAD_SCOPE in (intent.settings_scope(value), captured['observation']['scope']):
                        raise ValueError('Set Move one three-pad SMD part to match the preset, then load it again.')
                    # Preserve an older preset's actual policy instead of
                    # silently upgrading its meaning to zone-aware placement.
                    captured = intent.inspect_saved(self.board.GetValue())
                intent.facts(captured, value)
                if policy_changed:
                    self.saved_native = None
                self.inspection = captured; self.revoke(discard=True); self.updating = True
                try:
                    self.copper_policy.SetSelection(1 if intent.rebuilds_copper(value) else 0)
                    self.rigid_group.SetValue(intent.grouped(value))
                    self.automatic_target_area = False
                    start = value.get('region_initialization')
                    self.target_start_policy = start or intent.prototype.EXACT_TRACK_REGION_POLICY
                    self.target_region.SetValue(start is not None)
                    self.protected_names.ChangeValue('\n'.join(value.get('protected_names', [])))
                    self.protected_route_ids.ChangeValue('\n'.join(value.get('protected_route_ids', [])))
                    self.parts.Set([component_label(row, rebuild=intent.rebuilds_copper(value)) for row in self.inspection['components']])
                    for i, row in enumerate(self.inspection['components']): self.parts.Check(i, row['uuid'] in value['selected'])
                    for field, coordinate in zip(self.region, value['region_nm']): field.ChangeValue(mm(coordinate))
                finally: self.updating = False
                # Rebuild the passive view after committing every control.
                # revoke() rendered the earlier choices before the preset loaded.
                self.overview()
                self.refresh()
                self.message('Placement settings loaded. Constraints and fixed components were checked; no operation started.'
                    + (' This preset’s original placement policy is preserved; review its shown limits.' if policy_changed else ''))
            except Exception as exc: self.message('Settings refused: ' + str(exc))

        def save_settings(self, _):
            try:
                value = self.options()
                with wx.FileDialog(self, 'Save placement settings to a new JSON file', defaultFile='placement-settings.json', wildcard='JSON (*.json)|*.json', style=wx.FD_SAVE) as dialog:
                    if dialog.ShowModal() != wx.ID_OK: return
                    path = write_new_json(dialog.GetPath(), value)
                self.message('Settings saved: ' + str(path))
            except Exception as exc: self.message('Settings not saved: ' + str(exc))

        def find_alternatives(self, _):
            if self.busy or self.gate.closed:
                return
            try:
                if getattr(self, 'constraint_offer', None) is not None:
                    raise ValueError('Use or discard proposed settings before finding alternatives.')
                value = self.options(validate_geometry=False)
                inspection = copy.deepcopy(self.inspection); self.revoke(discard=True)
                def adopt(proposal):
                    search = proposal['search']
                    if search['status'] == 'no_feasible_region_seed':
                        self.findings.SetValue(region_search_findings(search, inspection))
                        self.pages.SetSelection(1)
                        self.message('No placement found. See Findings and constraints.')
                        return
                    if search['status'] != 'proposals_ready':
                        message = {
                            'budget_exhausted': 'The placement search reached its time limit. No draft was kept; your project is unchanged.',
                            'no_changed_alternative': 'No changed placement passed the current constraints. This does not prove that no solution exists. For a rigid group, Review current group arrangement allows explicit manual repositioning; your project is unchanged.',
                            'cancelled': 'Placement search cancelled. No draft was kept; your project is unchanged.',
                        }.get(search['status'], 'Placement search returned an unsupported result; no draft was adopted.')
                        raise ValueError(message)
                    review = intent.Review(proposal); self.current_review_settings(review)
                    self.gate.attach(review); self.render(0)
                    self.message('Compare alternatives on the board. Approve the displayed moves when ready.')
                    if hasattr(self, 'qualify') and self.qualify.IsShownOnScreen() and self.qualify.IsEnabled():
                        self.qualify.SetFocus()
                self.start('Searching two alternatives within the 2-second search budget…',
                           lambda job, event: intent.propose(inspection, value, cancel_event=event), adopt)
            except Exception as exc: self.message('Placement search refused: ' + str(exc))

        def review_original_group(self, _):
            try:
                value = self.options(); inspection = copy.deepcopy(self.inspection); self.revoke(discard=True)
                def adopt(proposal):
                    review = intent.Review(proposal); self.current_review_settings(review)
                    self.gate.attach(review); self.render(0)
                    self.message('Original arrangement, not an optimized result. Edit one member to translate the group, then review and validate.')
                self.start('Checking the current group arrangement; no optimization search…',
                    lambda job, event: intent.original_proposal(inspection, value), adopt)
            except Exception as exc: self.message('Original arrangement refused: ' + str(exc))

        def render(self, alternative_index=None):
            review = self.gate.review
            references = {r['uuid']: r['reference'] for r in review.inspection['components']}
            original = getattr(review, 'proposal', {}).get('search', {}).get('status') == 'original_for_review'
            labels = (['Original arrangement · edit to reposition'] if original else
                      ['Alternative ' + str(i + 1) for i in range(len(review.alternatives))])
            targets = list(range(len(labels)))
            if alternative_index is None:
                labels.append('Edited draft'); targets.append(None)
                selection = len(labels) - 1
            else:
                if type(alternative_index) is not int or not 0 <= alternative_index < len(targets):
                    raise ValueError('Choose an available alternative.')
                selection = alternative_index
            self.pending_coordinates.clear()
            self.alternative_labels = labels; self.alternative_targets = targets
            self.alternative.Set(labels); self.alternative.SetSelection(selection)
            self.part.Set([references[key] for key in review.settings['selected']]); self.part.SetSelection(0)
            self.coordinates()
            self.validation_revoked = False
            self.present()

        def present(self):
            """Refresh findings and diagram state without changing the reviewed pose or controls."""
            review = self.gate.review
            if review is None:
                self.overview(); return
            if self.qualified is not None:
                try: self.gate.check(self.qualified['ticket'])
                except ValueError:
                    self.revoke(dirty=self.gate.dirty); return
            if self.gate.dirty:
                state = 'Pending edits — displayed pose has not been updated'
            elif self.qualified is not None:
                state = 'Placement validated — routing pending'
            elif self.validation_revoked:
                state = 'Validation revoked — review and validate again'
            else:
                state = 'Geometry draft — Native validation required'
            display = placement_view.scene(review.observation, review.moves,
                review.settings['selected'], review.settings['region_nm'],
                title='Placement review' if self.qualified is not None else 'Placement draft', state=state,
                **({'annotation_context': review.inspection['annotation_context']}
                   if 'annotation_context' in review.inspection else {}))
            self.set_board_scene(display, rebuild=review.copper_plan is not None)
            moves = placement_move_findings(review.observation, review.moves)
            findings = f'{state}\n\n{moves}\n\n{copper_findings(review.copper_plan)}\n\n'
            if self.qualified is not None:
                witness = self.qualified['witness']
                findings += gui.human_summary('inspect', dict(
                    status='placement validated; routing pending', native=witness['findings'],
                    candidate=witness['candidate'], source=review.inspection['source']))
            else:
                selection = self.alternative.GetSelection()
                index = (self.alternative_targets[selection] if type(selection) is int
                         and 0 <= selection < len(self.alternative_targets) else None)
                if index is None:
                    label = 'Edited draft.'
                elif getattr(review, 'proposal', {}).get('search', {}).get('status') == 'original_for_review':
                    label = 'Original arrangement — not optimized.'
                else:
                    label = f'Alternative {index + 1}.'
                findings += (f"{label}\nSource: {review.inspection['source']}\n"
                    + 'No current Native placement validation. A reviewed draft is not route acceptance.')
            rebuild = review.copper_plan is not None
            self.findings.SetValue(findings + '\nNo electrical or manufacturing approval is granted.\n\n'
                + '\n'.join(placement_limits(review.inspection, rebuild=rebuild, grouped=intent.grouped(review.settings),
                    region_initialization=bool(intent.region_options(review.settings))))
                + '\n\nComponents\n' + component_findings(review.inspection, rebuild=rebuild))
            self.refresh(); self.layout_panel()

        def coordinates(self):
            review = self.gate.review; index = self.part.GetSelection()
            self.editing_component = None
            if review is not None and 0 <= index < len(review.settings['selected']):
                identity = review.settings['selected'][index]
                xy = self.pending_coordinates.get(identity)
                if xy is None:
                    xy = [mm(value) for value in review.moves[identity]]
                self.x.ChangeValue(xy[0]); self.y.ChangeValue(xy[1])
                self.editing_component = identity

        def edit_component(self):
            review = self.gate.review; index = self.part.GetSelection()
            if (review is None or not 0 <= index < len(review.settings['selected'])
                    or review.settings['selected'][index] != self.editing_component):
                raise ValueError('Component selection changed before its coordinates loaded. Choose the component again.')
            return self.editing_component

        def select_part(self, _):
            # A Cocoa popup may commit its selection after the choice event.
            review, generation = self.gate.review, self.gate.generation
            def loaded():
                if self.gate.closed or self.busy or self.gate.review is not review or self.gate.generation != generation:
                    return
                self.coordinates()
                if self.pending_coordinates:
                    self.message('Edits kept for ' + str(len(self.pending_coordinates))
                        + ' components. Update all edits to check their final positions together.')
            wx.CallAfter(loaded)

        def choose_alternative(self, _):
            try:
                index = self.alternative.GetSelection()
                if (type(index) is int and 0 <= index < len(self.alternative_targets)
                        and self.alternative_targets[index] is None):
                    return  # Current edited pose is a label, not another proposal.
                self.revoke(dirty=self.gate.dirty or bool(self.pending_coordinates))
                if type(index) is not int or not 0 <= index < len(self.alternative_targets):
                    raise ValueError('Choose an available alternative.')
                target = self.alternative_targets[index]
                if type(target) is not int or not 0 <= target < len(self.gate.review.alternatives):
                    raise ValueError('Choose an available alternative.')
                self.gate.review.choose(target); self.gate.dirty = False; self.render(target)
            except Exception as exc: self.message('Alternative refused: ' + str(exc))

        def pending_edit(self, event):
            if not self.updating:
                try:
                    identity = self.edit_component()
                except ValueError as exc:
                    self.revoke(dirty=True); self.message(str(exc)); event.Skip(); return
                self.pending_coordinates[identity] = [self.x.GetValue(), self.y.GetValue()]
                self.revoke(dirty=True)
                self.message('Edits are pending. You can edit another component, then Update all edits. Choosing an alternative discards pending edits.')
            event.Skip()

        def edit(self, _):
            previous = None; rendering = False
            try:
                self.revoke(dirty=True); review = self.gate.review
                identity = self.edit_component()
                visible_coordinates = [self.x.GetValue(), self.y.GetValue()]
                if not intent.grouped(review.settings) or not self.pending_coordinates:
                    self.pending_coordinates[identity] = list(visible_coordinates)
                pending = copy.deepcopy(self.pending_coordinates)
                selection = self.part.GetSelection(); alternative = self.alternative.GetSelection()
                alternative_labels = list(self.alternative_labels)
                alternative_targets = list(self.alternative_targets)
                previous = (review.pose, review.moves, review.revision)
                review.edit_many(copy.deepcopy(self.pending_coordinates))
                rendering = True; self.gate.dirty = False; self.render()
                self.message('Draft updated and geometry checked. Review it again before Native validation.')
            except Exception as exc:
                if previous is not None:
                    review.pose, review.moves, review.revision = previous
                    review.intent = None; self.gate.dirty = True
                if rendering:
                    # Rendering also resets selectors/text. Restore the whole
                    # editing transaction, with approval still revoked.
                    self.pending_coordinates = pending
                    self.alternative_labels = alternative_labels; self.alternative_targets = alternative_targets
                    self.alternative.Set(alternative_labels)
                    self.part.SetSelection(selection); self.alternative.SetSelection(alternative)
                    self.editing_component = identity
                    self.x.ChangeValue(visible_coordinates[0]); self.y.ChangeValue(visible_coordinates[1])
                    self.revoke(dirty=True)
                self.message('Edit refused; previous pose retained: ' + str(exc))

        def reject_draft(self, _):
            self.invalidate_copilot()
            review = self.gate.review
            self.revoke(discard=True)
            self.message('Draft rejected. Earlier placement intent and routing handoff are revoked. Original files are unchanged.')
            if review is not None:
                try:
                    write_new_json(self.owned_workspace() / ('rejected-' + uuid.uuid4().hex + '.json'),
                        dict(schema=1, kind='autorouter.placement-GUI-rejection.v1', choice='reject',
                             source=review.inspection['source'], revision=review.revision,
                             pose_sha256=intent.constraints.digest(review.pose), execution_authorized=False,
                             approval_granted=False, human_PCB_approval=False))
                except Exception as exc:
                    self.message('Draft rejected and earlier handoff revoked. The rejection receipt could not be saved: ' + str(exc))

        def owned_workspace(self):
            if self.workspace is None:
                base = h.real_path(c.ROOT / '.runs')
                self.workspace = base / ('placement-review-' + uuid.uuid4().hex)
                self.workspace.mkdir(mode=0o700); h.capture_destination(self.owner, self.workspace)
            h.owned_destination(self.owner)
            return self.workspace

        def qualify_draft(self, _, *, prepare_routing=False):
            if self.busy or self.gate.closed:
                return
            try:
                if getattr(self, 'constraint_offer', None) is not None:
                    raise ValueError('Use or discard proposed settings before validating placement.')
                if not self.picture.Ready():
                    raise ValueError('Review the current board preview before validating this draft.')
                if self.qualified is not None:
                    return
                if self.routing is not None:
                    raise ValueError('Wait for the previous routing window and its worker to close before validating another placement.')
                review = self.gate.review
                if review is None or self.gate.dirty:
                    raise ValueError('Review the current placement and apply any position edits first.')
                self.current_review_settings(review)
                # This primary action approves the displayed moves and exact copper plan.
                self.gate.acknowledged = True
                ticket = self.gate.ticket()
                def work(job, event):
                    from . import placement
                    require_closed_source(review.inspection['source'], inspection=review.inspection)
                    self.gate.check(ticket); draft = review.decision(acknowledged=True, accepted=True)
                    self.gate.check(ticket); workspace = self.owned_workspace()
                    path = write_new_json(workspace / ('draft-' + uuid.uuid4().hex + '.json'), draft)
                    output = c.ROOT / '.runs' / ('placement-qualified-' + uuid.uuid4().hex)
                    process = job.run(qualification_command(path, output), workspace / ('qualification-' + uuid.uuid4().hex + '.log'), timeout=150)
                    job.check_live(); self.gate.check(ticket)
                    if process['exit_code'] != 0 or process['log_truncated'] or process['cancel_requested']:
                        reason = 'Native qualification did not complete.'
                        try:
                            record = gui.read_record(output / 'result.json')
                            if (type(record) is dict and record.get('placement_qualified') is False
                                    and record.get('status') in ('failed', 'cancelled', 'budget_exhausted', 'invalidated')
                                    and type(record.get('reason')) is str and len(record['reason']) <= 8192):
                                reason = record['reason']
                        except (OSError, ValueError, TypeError, placement.p.Rejected):
                            pass
                        raise ValueError(reason + '\nNo candidate was validated. Private findings and logs: ' + str(output))
                    witness = placement.check(output); job.check_live(); self.gate.check(ticket)
                    guard = placement.source_guard(output, witness, verify_review=lambda: self.gate.check(ticket))
                    return dict(witness=witness, guard=guard, ticket=ticket)
                def adopt(result):
                    self.gate.check(ticket); result['guard'].check(result['witness']['candidate'])
                    self.job.check_live(); self.gate.check(ticket)
                    self.current_review_settings(review)
                    self.job.check_live(); self.gate.check(ticket)
                    self.qualified = result
                    self.validation_revoked = False; self.present()
                    self.message('Placement checked. Review the routing scope before starting routing.')
                    if prepare_routing and self.qualified is result:
                        self.routing_handoff = (self.job, result)
                        self.preview_ready()
                self.start('Validating the reviewed placement on a separate copy · 120-second total qualification budget…', work, adopt)
            except Exception as exc:
                self.revoke(dirty=self.gate.dirty)
                self.message('Qualification refused: ' + str(exc))

        def open_routing(self, _, *, preview=False):
            if self.busy or self.gate.closed:
                return
            try:
                if getattr(self, 'constraint_offer', None) is not None:
                    raise ValueError('Use or discard proposed settings before continuing to routing.')
                if not self.picture.Ready():
                    raise ValueError('The current placement preview is unavailable. Review and validate again.')
                if self.qualified is None: raise ValueError('Validate this exact draft first.')
                self.current_review_settings(self.gate.review)
                result = self.qualified; self.gate.check(result['ticket'])
                # Qualification and initial adoption already used the worker deadline.
                # A reviewed result now depends on the ticket, material and cancellation.
                if self.job is not None: self.job.check_not_cancelled()
                candidate = result['witness']['candidate']; result['guard'].check(candidate)
                if self.job is not None: self.job.check_not_cancelled()
                if self.routing is not None:
                    if self.routing.source_guard is not result['guard']:
                        raise ValueError('The previous routing window is closing. Wait before opening the new candidate.')
                    self.routing.Raise(); return
                def finished():
                    if self.routing is frame:
                        self.routing = None
                        if self.gate.closed: self.finish_close()
                        else:
                            self.panel.Show(); self.Layout(); self.refresh()
                history = (self.conversation.summary_for(self.inspection['source'], self.inspection['source_hashes'])
                           if self.conversation.has_display_history else '')
                note = ('Placement checked. Routing keeps all existing copper.'
                        if self.gate.review.copper_plan is None else
                        'Placement checked. Routing uses a separate project copy.')
                frame = gui.create_window(candidate, source_guard=result['guard'], on_closed=finished,
                    parent=self, placement_scene=self.picture.display, conversation_history=history,
                    on_saved_source=self.open_saved_source, source_note=note,
                    placement_findings=self.findings.GetValue())
                try:
                    if getattr(self, 'routing_output_hint', None) is not None:
                        frame.output.SetValue(self.routing_output_hint)
                    seconds = (routing_seconds(self.route_budget.GetValue().strip())
                        if hasattr(self, 'route_budget') else 90)
                    if self.gate.review.copper_plan is not None:
                        prefill_copper_routing(frame, self.gate.review.copper_plan, seconds=seconds)
                    else:
                        settings = gui.pref.validate(dict(gui.pref.DEFAULTS, scope='partial_completion', seconds=seconds))
                        if self.inspection is not None:
                            selected = self.gate.review.settings['selected']
                            narrow = empty_copper_selection(Path(self.inspection['source']), self.inspection, selected, settings)
                            if narrow is not None:
                                settings, _ = narrow
                        frame.prefill_placement_completion(settings)
                    if getattr(self, 'approved_copilot', None) is not None:
                        approved = self.check_copilot_plan()
                        expected = copy.deepcopy(approved['proposal']['routing_preferences'])
                        frame.seconds.SetValue(str(expected['seconds']))
                        if frame.config() != expected:
                            raise ValueError('Routing controls differ from the explicitly reviewed assistant plan.')
                        def check_settings(settings):
                            self.check_copilot_plan(full=False)
                            if settings != expected:
                                raise ValueError('Routing settings changed from the reviewed plan. Return to placement and review a new plan, or start an ordinary task.')
                        frame._settings_guard = check_settings
                    result['guard'].check(candidate); self.gate.check(result['ticket'])
                    self.current_review_settings(self.gate.review)
                    if self.job is not None: self.job.check_not_cancelled()
                    self.gate.check(result['ticket'])
                except Exception:
                    frame.Destroy(); raise
                self.routing = frame
                self.GetSizer().Add(frame, 1, wx.EXPAND)
                self.panel.Hide(); frame.Show(); self.Layout()
                self.message('Returning to placement keeps this draft. Changes revoke the routing handoff.')
                if preview:
                    frame.preview_qualified_placement()
            except Exception as exc:
                self.revoke(dirty=self.gate.dirty); self.message('Routing handoff refused: ' + str(exc))

        def begin_saved_routing(self, _):
            try:
                self.open_saved_routing(None)
            except Exception as exc:
                self.message('Routing could not open. ' + str(exc))

        def open_saved_routing(self, values):
            """Adopt checked protected settings into the ordinary routing workflow."""
            if self.busy or self.routing is not None:
                raise ValueError('Finish the current task before adopting routing settings.')
            saved_context = getattr(self, 'saved_route_context', None) or {}
            if saved_context.get('pcb_setup'):
                raise ValueError('Finish PCB setup in KiCad and refresh inspection before routing.')
            if saved_context.get('open_in_kicad'):
                raise ValueError('Close the project in KiCad and refresh inspection before routing.')
            captured = self.inspection or saved_context.get('static')
            source = require_closed_source(self.board.GetValue(), inspection=captured)
            if captured is None:
                # Return and file selection normally inspect first. A typed
                # path can reach this action without a cached inspection.
                from . import design_intent
                captured = design_intent.inspect_project(source)
                if captured.get('pcb_setup'):
                    raise ValueError('Finish PCB setup in KiCad and refresh inspection before routing.')
                require_closed_source(source, inspection=captured)
            if values is None and getattr(self, 'constraint_offer', None) is not None:
                raise ValueError('Use or discard proposed settings first.')
            selected_prefill = False
            if values is not None:
                settings, guard = values['effective_preferences'], conversation.routing_source_guard(values)
            else:
                settings, guard = self.conversation_routing_preferences(), None
                if self.inspection is not None:
                    selected = [row['uuid'] for i, row in enumerate(self.inspection['components'])
                                if self.parts.IsChecked(i)]
                    selection = empty_copper_selection(source, self.inspection, selected, settings)
                    if selection is not None:
                        settings, guard = selection
                        selected_prefill = True
            if guard is not None: guard.check(source)

            def finished():
                self.routing = None
                if self.gate.closed:
                    self.finish_close()
                else:
                    self.panel.Show(); self.Layout(); self.refresh()

            view = getattr(self, 'routing_source_scene', None) if values is not None else None
            current = gui.source_inventory(source) if self.conversation.has_display_history or view is not None else None
            history = self.conversation.summary_for(source, current)
            scene = view[2] if view is not None and view[:2] == (str(source), current) else None
            net_context = None
            read_only = getattr(self, 'saved_route_context', None)
            if read_only is not None:
                static = read_only['static']
                require_closed_source(source, inspection=static)
                scene = read_only['scene']
                try:
                    names = routing_scope.validate_names([row['name'] for row in static['nets']])
                except ValueError:
                    pass
                else:
                    net_context = dict(source=str(source), source_hashes=static['source_hashes'], names=names)
            if scene is None and self.inspection is not None and self.inspection['source'] == str(source):
                scene = saved_routing_scene({'source': str(source), 'source_hashes': current or gui.source_inventory(source)}, self.inspection)
                if guard is None:
                    footprints = self.inspection.get('observation', {}).get('footprints', ())
                    names = sorted({pad['net'] for part in footprints
                                    for pad in part.get('pads', ()) if pad['net']})
                    try:
                        names = routing_scope.validate_names(names)
                    except ValueError:
                        pass  # Keep exact manual entry for boards without a usable list.
                    else:
                        net_context = dict(source=str(source), source_hashes=self.inspection['source_hashes'], names=names)
            frame = gui.create_window(source, source_guard=guard, on_closed=finished, parent=self,
                                      conversation_history=history, saved_scene=scene, saved_net_context=net_context,
                                      on_saved_source=self.open_saved_source)
            try:
                if self.routing_output_hint is not None:
                    frame.output.SetValue(self.routing_output_hint)
                prefill_routing(frame, settings)
                if selected_prefill:
                    frame.status.SetLabel('Confirm the project is closed, then preview the selected nets and time limit.')
                else:
                    frame.status.SetLabel('Choose the scope and time limit. Confirm the project is closed to preview.')
            except Exception:
                frame.Destroy()
                raise
            self.routing = frame
            self.GetSizer().Add(frame, 1, wx.EXPAND)
            self.panel.Hide(); frame.Show(); self.Layout()

        def cancel_work(self, _=None):
            # Signal the worker before any fallible rendering or widget update.
            if self.cancel_event is not None: self.cancel_event.set()
            if self.job is not None: self.job.cancel()
            self.invalidate_copilot()
            self.revoke(dirty=self.gate.dirty)
            self.message('Cancellation requested. Waiting for the owned worker to finish cleanup; no queued result will be adopted.')

        def tick(self, _):
            if self.busy: self.progress.Pulse()
            else: self.progress.SetValue(0)

        def close(self, event):
            self.invalidate_copilot()
            self.gate.close(); self.qualified = None
            if self.cancel_event is not None: self.cancel_event.set()
            if self.job is not None: self.job.cancel()
            if self.routing is not None: self.routing.Close()
            if self.busy or self.routing is not None:
                if event.CanVeto(): event.Veto()
                self.Hide()
            else:
                self.finish_close()

        def finish_close(self):
            # Keep the parent assistant hidden until both owned worker scopes
            # have ended. Destroying this frame is the parent's resume signal.
            if self.gate.closed and not self.busy and self.routing is None and not self.finalized:
                self.finalized = True; self.timer.Stop(); self.Destroy()
                if on_closed is not None: wx.CallAfter(on_closed)

    return Window


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='')
    args = parser.parse_args(argv)
    import wx
    if wx.GetApp() is not None:
        raise ValueError('Use create_window with the existing application; a nested loop is not allowed.')
    app = wx.App(False)
    chrome.name_application(app)
    window = create_window(args.board); window.Show()
    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        for sig in previous: signal.signal(sig, lambda *_: wx.CallAfter(window.Close))
        app.MainLoop()
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)
        if window.job is not None: window.job.cancel()
        if window.cancel_event is not None: window.cancel_event.set()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
