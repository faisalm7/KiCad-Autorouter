"""Selected-placement controls over the shared guarded core.

No model, editor mutation or implicit routing approval. Native qualification runs
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
import signal
import threading
import uuid
import xml.etree.ElementTree as ET

from . import config as c, gui, handoff as h, placement_intent as intent, placement_view


def millimetres(text):
    if type(text) is not str or not 0 < len(text) <= 32:
        raise ValueError('Enter a bounded decimal coordinate in millimetres.')
    try:
        value = Decimal(text)
        if not value.is_finite() or abs(value) > 2000:
            raise ValueError('Coordinates must be finite and within ±2000 mm.')
        scaled = value * 1000000
        if scaled != scaled.to_integral_value():
            raise ValueError('Use at most nanometre coordinate precision.')
        return int(scaled)
    except InvalidOperation as exc:
        raise ValueError('Enter a decimal coordinate in millimetres.') from exc


def mm(value):
    return format(Decimal(value) / 1000000, 'f')


def component_label(row):
    reasons = row['fixed_reasons']
    short = []
    for reason in reasons:
        label = {'Locked in KiCad': 'locked',
                 'Shares a net with existing copper': 'routed net'}.get(reason, 'constraints')
        if label not in short: short.append(label)
    return row['reference'] + (' · fixed (' + ', '.join(short) + ')' if reasons else ' · movable')


def component_findings(inspection):
    return '\n'.join(row['reference'] + ': ' + ('; '.join(row['fixed_reasons'])
        if row['fixed_reasons'] else 'Movable when selected; otherwise fixed.')
        for row in inspection['components'])


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
                intent.constraints.digest(self.review.inspection))

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


def bitmap_with_labels(wx, svg, size=(850, 500)):
    """wx's SVG rasterizer omits text; paint only our passive renderer's labels."""
    image = wx.svg.SVGimage.CreateFromBytes(svg.encode())
    scale = min(size[0] / image.width, size[1] / image.height)
    bitmap = image.ConvertToBitmap(scale=scale, width=round(image.width * scale), height=round(image.height * scale))
    dc = wx.MemoryDC(bitmap)
    for node in ET.fromstring(svg).findall('{http://www.w3.org/2000/svg}text'):
        font = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_SWISS))
        font.SetPixelSize(wx.Size(0, max(9, round(float(node.get('font-size')) * scale))))
        if node.get('font-weight') == 'bold': font = font.Bold()
        dc.SetFont(font); dc.SetTextForeground(wx.Colour(node.get('fill')))
        text = node.text or ''; _, height, descent, _ = dc.GetFullTextExtent(text)
        dc.DrawText(text, round(float(node.get('x')) * scale), round(float(node.get('y')) * scale - height + descent))
    dc.SelectObject(wx.NullBitmap)
    return bitmap


def create_window(board='', *, on_closed=None):
    if on_closed is not None and not callable(on_closed):
        raise ValueError('The parent close notification must be a callable.')
    import wx
    import wx.svg
    if wx.GetApp() is None or threading.current_thread() is not threading.main_thread():
        raise ValueError('Open placement controls on the existing application main thread.')
    if not isinstance(board, (str, Path)):
        raise ValueError('Use an exact saved PCB path or an empty hint.')

    class Window(wx.Frame):
        def __init__(self):
            super().__init__(None, title='KiCad design assistant — placement', size=(1240, 900))
            self.gate = ReviewGate(); self.inspection = None; self.busy = False
            self.finalized = False
            self.job = None; self.cancel_event = None; self.routing = None
            self.qualified = None; self.validation_revoked = False
            self.updating = False; self.workspace = None; self.owner = {}
            self.pending_coordinates = {}
            self.editing_component = None
            panel = self.panel = wx.ScrolledWindow(self); panel.SetScrollRate(0, 12)
            root = wx.BoxSizer(wx.VERTICAL)
            title = wx.StaticText(panel, label='Place selected components')
            title.SetFont(title.GetFont().Larger().Bold()); root.Add(title, 0, wx.ALL, 14)
            root.Add(wx.StaticText(panel, label='Inspect → choose components and space → review a draft → validate → route a separate project.'), 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
            pathrow = wx.BoxSizer(wx.HORIZONTAL)
            self.board = wx.TextCtrl(panel, value=str(board)); pathrow.Add(self.board, 1, wx.RIGHT, 8)
            self.browse = wx.Button(panel, label='Choose PCB…'); pathrow.Add(self.browse, 0, wx.RIGHT, 8)
            self.inspect = wx.Button(panel, label='Inspect project'); pathrow.Add(self.inspect)
            root.Add(pathrow, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
            columns = wx.BoxSizer(wx.HORIZONTAL); left = wx.BoxSizer(wx.VERTICAL); right = wx.BoxSizer(wx.VERTICAL)
            left.Add(wx.StaticText(panel, label='Components to move'), 0, wx.BOTTOM, 6)
            self.parts = wx.CheckListBox(panel, size=(310, 210)); left.Add(self.parts, 0, wx.EXPAND)
            label = wx.StaticText(panel, label='Unchecked components stay fixed. Locked parts and any part sharing an already-routed net cannot move.')
            label.Wrap(310); left.Add(label, 0, wx.TOP | wx.BOTTOM, 8)
            left.Add(wx.StaticText(panel, label='Allowed movement rectangle · mm'), 0, wx.TOP | wx.BOTTOM, 6)
            grid = wx.FlexGridSizer(cols=2, vgap=6, hgap=8); grid.AddGrowableCol(1)
            self.region = []
            for label in ('Left X', 'Top Y', 'Right X', 'Bottom Y'):
                grid.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL)
                field = wx.TextCtrl(panel, size=(130, -1)); self.region.append(field); grid.Add(field, 1, wx.EXPAND)
            left.Add(grid, 0, wx.EXPAND)
            presetrow = wx.BoxSizer(wx.HORIZONTAL)
            self.load = wx.Button(panel, label='Load settings…'); self.save = wx.Button(panel, label='Save settings…')
            presetrow.Add(self.load, 0, wx.RIGHT, 6); presetrow.Add(self.save)
            left.Add(presetrow, 0, wx.TOP | wx.BOTTOM, 10)
            self.find = wx.Button(panel, label='Find placement alternatives'); left.Add(self.find, 0, wx.EXPAND)
            limits = wx.StaticText(panel, label='Experimental selected translation: 2–16 movable parts. Source orientation and side stay fixed. Inspect the project for supported geometry and fixed-component reasons. Movement space must avoid existing copper and zones. Two alternatives; 2-second cooperative search budget.')
            limits.Wrap(310); left.Add(limits, 0, wx.TOP, 12)
            self.picture = wx.StaticBitmap(panel); self.picture.SetMinSize((850, 500))
            right.Add(self.picture, 0, wx.ALIGN_CENTER_HORIZONTAL)
            self.alternative = wx.Choice(panel); right.Add(self.alternative, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 8)
            editrow = wx.BoxSizer(wx.HORIZONTAL)
            self.part = wx.Choice(panel); editrow.Add(self.part, 1, wx.RIGHT, 8)
            self.x = wx.TextCtrl(panel, size=(95, -1)); self.y = wx.TextCtrl(panel, size=(95, -1))
            for label, field in (('X mm', self.x), ('Y mm', self.y)):
                editrow.Add(wx.StaticText(panel, label=label), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 4)
                editrow.Add(field, 0, wx.RIGHT, 8)
            self.apply = wx.Button(panel, label='Update all edits'); editrow.Add(self.apply)
            right.Add(editrow, 0, wx.EXPAND)
            self.ack = wx.CheckBox(panel, label='I saved and CLOSED this exact source’s PCB and schematic editors.\n'
                'I reviewed this draft and its limits; this is not PCB approval.')
            right.Add(self.ack, 0, wx.TOP | wx.BOTTOM, 10)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            self.reject = wx.Button(panel, label='Reject draft'); self.qualify = wx.Button(panel, label='Validate placement')
            self.route = wx.Button(panel, label='Open routing settings')
            for button in (self.reject, self.qualify, self.route): buttons.Add(button, 0, wx.RIGHT, 8)
            right.Add(buttons, 0, wx.BOTTOM, 8)
            columns.Add(left, 0, wx.RIGHT, 18); columns.Add(right, 1, wx.EXPAND)
            root.Add(columns, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 14)
            self.status = wx.StaticText(panel, label='Choose a saved PCB with matching project and schematic. Save and close its editors before validation.')
            self.status.Wrap(1150); root.Add(self.status, 0, wx.ALL, 14)
            progressrow = wx.BoxSizer(wx.HORIZONTAL)
            self.progress = wx.Gauge(panel); progressrow.Add(self.progress, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            self.cancel = wx.Button(panel, label='Cancel'); progressrow.Add(self.cancel)
            root.Add(progressrow, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
            self.findings = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 150))
            root.Add(self.findings, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)
            panel.SetSizer(root)
            self.input_controls = [self.board, self.browse, self.inspect, self.parts, *self.region, self.load, self.save, self.find]
            self.pose_controls = [self.alternative, self.part, self.x, self.y, self.apply, self.ack, self.reject, self.qualify]
            self.board.Bind(wx.EVT_TEXT, self.source_changed)
            self.browse.Bind(wx.EVT_BUTTON, self.choose_board); self.inspect.Bind(wx.EVT_BUTTON, self.inspect_project)
            self.parts.Bind(wx.EVT_CHECKLISTBOX, self.settings_changed)
            for field in self.region: field.Bind(wx.EVT_TEXT, self.settings_changed)
            self.load.Bind(wx.EVT_BUTTON, self.load_settings); self.save.Bind(wx.EVT_BUTTON, self.save_settings)
            self.find.Bind(wx.EVT_BUTTON, self.find_alternatives); self.alternative.Bind(wx.EVT_CHOICE, self.choose_alternative)
            self.part.Bind(wx.EVT_CHOICE, self.select_part)
            for field in (self.x, self.y): field.Bind(wx.EVT_TEXT, self.pending_edit)
            self.apply.Bind(wx.EVT_BUTTON, self.edit); self.ack.Bind(wx.EVT_CHECKBOX, self.acknowledge)
            self.reject.Bind(wx.EVT_BUTTON, self.reject_draft); self.qualify.Bind(wx.EVT_BUTTON, self.qualify_draft)
            self.route.Bind(wx.EVT_BUTTON, self.open_routing); self.cancel.Bind(wx.EVT_BUTTON, self.cancel_work)
            self.Bind(wx.EVT_CLOSE, self.close)
            self.timer = wx.Timer(self); self.Bind(wx.EVT_TIMER, self.tick, self.timer); self.timer.Start(150)
            self.refresh(); self.layout_panel()

        def layout_panel(self):
            self.Layout()
            self.panel.Layout()
            self.panel.FitInside()

        def message(self, text):
            self.status.SetLabel(text); self.status.Wrap(1150); self.layout_panel()

        def refresh(self):
            for control in self.input_controls: control.Enable(not self.busy)
            self.find.Enable(not self.busy and self.inspection is not None)
            self.save.Enable(not self.busy and self.inspection is not None)
            for control in self.pose_controls: control.Enable(not self.busy and self.gate.review is not None)
            self.qualify.Enable(not self.busy and self.routing is None and self.gate.review is not None and self.gate.acknowledged and not self.gate.dirty)
            self.route.Enable(not self.busy and self.qualified is not None)
            self.cancel.Enable(self.busy)

        def revoke(self, *, dirty=False, discard=False):
            self.validation_revoked = self.qualified is not None or self.validation_revoked
            self.gate.invalidate(dirty=dirty); self.ack.SetValue(False); self.qualified = None
            # Revocation is authoritative even when the passive preview cannot
            # be redrawn. Never leave an earlier success visible during failure.
            self.refresh()
            self.findings.SetValue('No current placement validation. Review the draft and validate it before routing.')
            self.picture.SetBitmap(wx.NullBitmap); self.picture.SetMinSize((850, 500))
            if self.routing is not None: self.routing.Close()
            redraw_error = None
            if discard:
                self.pending_coordinates.clear()
                self.editing_component = None
                self.gate.review = None
                self.alternative.Set([]); self.part.Set([])
                self.x.ChangeValue(''); self.y.ChangeValue('')
                self.findings.SetValue('No current placement draft or validation. Inspect the saved project and choose components to begin again.')
                self.layout_panel()
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
                self.inspection = None; self.parts.Set([]); self.revoke(discard=True)
                self.message('Source changed. Inspect this saved project before requesting placement.')
            event.Skip()

        def settings_changed(self, event):
            if not self.updating:
                self.revoke(discard=True)
                if self.inspection:
                    for index, row in enumerate(self.inspection['components']):
                        if row['fixed_reasons'] and self.parts.IsChecked(index):
                            self.parts.Check(index, False)
                            self.message(row['reference'] + ' stays fixed: ' + '; '.join(row['fixed_reasons']))
            event.Skip()

        def choose_board(self, _):
            with wx.FileDialog(self, 'Choose the saved PCB', wildcard='KiCad PCB (*.kicad_pcb)|*.kicad_pcb', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
                if dialog.ShowModal() == wx.ID_OK: self.board.SetValue(dialog.GetPath())

        def options(self):
            if self.inspection is None: raise ValueError('Inspect the saved project first.')
            selected = [row['uuid'] for i, row in enumerate(self.inspection['components']) if self.parts.IsChecked(i)]
            value = intent.settings(selected, [millimetres(field.GetValue()) for field in self.region],
                scope=self.inspection['observation']['scope'])
            intent.facts(self.inspection, value)
            return value

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
            self.revoke(discard=True); self.inspection = None
            source = self.board.GetValue()
            def adopt(value):
                # The off-thread capture has no authority; bind it again at use.
                self.inspection = value
                self.parts.Set([component_label(row) for row in value['components']])
                self.findings.SetValue('\n'.join(value['limitations']) + '\n\nComponents\n' + component_findings(value))
                self.message('Saved project inspected. Choose at least two movable components and an explicit movement rectangle.')
            self.start('Reading saved project geometry and fixed-component relationships…', lambda job, event: intent.inspect_saved(source), adopt)

        def load_settings(self, _):
            try:
                if self.inspection is None: raise ValueError('Inspect the saved project first.')
                with wx.FileDialog(self, 'Load placement settings', wildcard='JSON (*.json)|*.json', style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
                    if dialog.ShowModal() != wx.ID_OK: return
                    value = intent.load_settings(dialog.GetPath())
                intent.facts(self.inspection, value); self.revoke(discard=True); self.updating = True
                try:
                    for i, row in enumerate(self.inspection['components']): self.parts.Check(i, row['uuid'] in value['selected'])
                    for field, coordinate in zip(self.region, value['region_nm']): field.ChangeValue(mm(coordinate))
                finally: self.updating = False
                self.message('Placement settings loaded. Constraints and fixed components were checked; no operation started.')
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
            try:
                value = self.options(); inspection = copy.deepcopy(self.inspection); self.revoke(discard=True)
                def adopt(proposal):
                    if proposal['search']['status'] != 'proposals_ready':
                        raise ValueError('No draft returned: ' + proposal['search']['status'] + '. This is not an infeasibility proof.')
                    self.gate.attach(intent.Review(proposal)); self.render(0)
                    self.message('Review the alternatives and their constraints. You may edit selected positions before validation.')
                self.start('Searching two alternatives within the 2-second search budget…',
                           lambda job, event: intent.propose(inspection, value, cancel_event=event), adopt)
            except Exception as exc: self.message('Placement search refused: ' + str(exc))

        def render(self, alternative_index=None):
            review = self.gate.review
            self.pending_coordinates.clear()
            references = {r['uuid']: r['reference'] for r in review.inspection['components']}
            self.alternative.Set(['Alternative ' + str(i + 1) for i in range(len(review.alternatives))])
            self.alternative.SetSelection(wx.NOT_FOUND if alternative_index is None else alternative_index)
            self.part.Set([references[key] for key in review.settings['selected']]); self.part.SetSelection(0)
            self.coordinates()
            self.validation_revoked = False
            self.present()

        def present(self):
            """Refresh findings and diagram state without changing the reviewed pose or controls."""
            review = self.gate.review
            if review is None: return
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
            svg = placement_view.render(review.inspection['observation'], review.moves,
                review.settings['selected'], review.settings['region_nm'],
                title='Placement review' if self.qualified is not None else 'Placement draft', state=state)
            bitmap = bitmap_with_labels(wx, svg)
            self.picture.SetBitmap(bitmap); self.picture.SetMinSize(bitmap.GetSize())
            if self.qualified is not None:
                witness = self.qualified['witness']
                findings = state + '\n' + gui.human_summary('inspect', dict(
                    status='placement validated; routing pending', native=witness['findings'],
                    candidate=witness['candidate'], source=review.inspection['source']))
            else:
                index = self.alternative.GetSelection()
                findings = (state + '\nOriginal copper and unselected/fixed components are preserved.\n'
                    + ('Edited draft.\n' if index == wx.NOT_FOUND else 'Alternative ' + str(index + 1) + '.\n')
                    + 'Source: ' + review.inspection['source'] + '\n'
                    + 'No current Native placement validation. A reviewed draft is not route acceptance.')
            self.findings.SetValue(findings + '\nNo electrical or manufacturing approval is granted.\n\n'
                + '\n'.join(review.inspection.get('limitations', intent.LIMITS))
                + '\n\nComponents\n' + component_findings(review.inspection))
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
                index = self.alternative.GetSelection(); self.revoke(dirty=self.gate.dirty or bool(self.pending_coordinates))
                self.gate.review.choose(index); self.gate.dirty = False; self.render(index)
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
                self.pending_coordinates[identity] = [self.x.GetValue(), self.y.GetValue()]
                pending = copy.deepcopy(self.pending_coordinates)
                selection = self.part.GetSelection(); alternative = self.alternative.GetSelection()
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
                    self.part.SetSelection(selection); self.alternative.SetSelection(alternative)
                    self.editing_component = identity
                    self.x.ChangeValue(pending[identity][0]); self.y.ChangeValue(pending[identity][1])
                    self.revoke(dirty=True)
                self.message('Edit refused; previous pose retained: ' + str(exc))

        def acknowledge(self, _):
            checked = self.ack.GetValue(); self.revoke(dirty=self.gate.dirty)
            self.gate.acknowledged = checked and not self.gate.dirty
            self.ack.SetValue(self.gate.acknowledged); self.qualified = None; self.refresh()

        def reject_draft(self, _):
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

        def qualify_draft(self, _):
            try:
                if self.routing is not None:
                    raise ValueError('Wait for the previous routing window and its worker to close before validating another placement.')
                ticket = self.gate.ticket(); review = self.gate.review
                def work(job, event):
                    from . import placement
                    self.gate.check(ticket); draft = review.decision(acknowledged=True, accepted=True)
                    self.gate.check(ticket); workspace = self.owned_workspace()
                    path = write_new_json(workspace / ('draft-' + uuid.uuid4().hex + '.json'), draft)
                    output = c.ROOT / '.runs' / ('placement-qualified-' + uuid.uuid4().hex)
                    process = job.run(qualification_command(path, output), workspace / ('qualification-' + uuid.uuid4().hex + '.log'), timeout=150)
                    job.check_live(); self.gate.check(ticket)
                    if process['exit_code'] != 0 or process['log_truncated'] or process['cancel_requested']:
                        raise ValueError('Native qualification did not complete. Its private job/log is retained: ' + str(output))
                    witness = placement.check(output); job.check_live(); self.gate.check(ticket)
                    guard = placement.source_guard(output, witness, verify_review=lambda: self.gate.check(ticket))
                    return dict(witness=witness, guard=guard, ticket=ticket)
                def adopt(result):
                    self.gate.check(ticket); result['guard'].check(result['witness']['candidate'])
                    self.job.check_live(); self.gate.check(ticket)
                    self.qualified = result
                    self.validation_revoked = False; self.present()
                    self.message('Placement validated on a separate project. Read every finding, then open routing settings. Routing and acceptance remain separate actions.')
                self.start('Validating the reviewed placement on a separate copy · 120-second total qualification budget…', work, adopt)
            except Exception as exc: self.message('Qualification refused: ' + str(exc))

        def open_routing(self, _):
            try:
                if self.qualified is None: raise ValueError('Validate this exact draft first.')
                result = self.qualified; self.gate.check(result['ticket'])
                if self.job is not None: self.job.check_live()
                candidate = result['witness']['candidate']; result['guard'].check(candidate)
                if self.job is not None: self.job.check_live()
                if self.routing is not None:
                    if self.routing.source_guard is not result['guard']:
                        raise ValueError('The previous routing window is closing. Wait before opening the new candidate.')
                    self.routing.Raise(); return
                def finished():
                    if self.routing is frame:
                        self.routing = None
                        if self.gate.closed: self.finish_close()
                        else: self.refresh()
                frame = gui.create_window(candidate, source_guard=result['guard'], on_closed=finished)
                try:
                    result['guard'].check(candidate); self.gate.check(result['ticket'])
                    if self.job is not None: self.job.check_live()
                except Exception:
                    frame.Destroy(); raise
                self.routing = frame
                frame.Show()
                self.message('Routing settings opened. Keep this placement review open; editing, rejecting or closing it revokes the handoff.')
            except Exception as exc:
                self.revoke(dirty=self.gate.dirty); self.message('Routing handoff refused: ' + str(exc))

        def cancel_work(self, _=None):
            # Signal the worker before any fallible rendering or widget update.
            if self.cancel_event is not None: self.cancel_event.set()
            if self.job is not None: self.job.cancel()
            self.revoke(dirty=self.gate.dirty)
            self.message('Cancellation requested. Waiting for the owned worker to finish cleanup; no queued result will be adopted.')

        def tick(self, _):
            if self.busy: self.progress.Pulse()
            else: self.progress.SetValue(0)

        def close(self, event):
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

    return Window()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', default='')
    args = parser.parse_args(argv)
    import wx
    if wx.GetApp() is not None:
        raise ValueError('Use create_window with the existing application; a nested loop is not allowed.')
    app = wx.App(False); window = create_window(args.board); window.Show()
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
