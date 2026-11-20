"""Small wx view for the owned live PCB qualification."""
import json
import sys
import threading

import wx
import wx.svg


class Preview(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent, size=(-1, 128))
        self.move = None
        self.Bind(wx.EVT_PAINT, self.paint)

    def paint(self, _event):
        dc = wx.PaintDC(self)
        width, height = self.GetClientSize()
        dark = wx.SystemSettings.GetAppearance().IsDark()
        ink = wx.Colour('#eef3fa' if dark else '#26343c')
        fill = wx.Colour('#29333a' if dark else '#eaf1f4')
        green = wx.Colour('#81dfb7' if dark else '#146c53')
        muted = wx.Colour('#a0b0ba' if dark else '#4b606d')
        dc.SetBackground(wx.Brush(fill))
        dc.Clear()
        dc.SetTextForeground(ink)
        if self.move is None:
            dc.DrawText('Select a footprint in the KiCad canvas.', 16, (height - 18) // 2)
            return
        left, right = width // 4, width * 3 // 4
        dc.SetPen(wx.Pen(muted, 2, wx.PENSTYLE_SHORT_DASH))
        dc.DrawLine(left, 35, right, 35)
        for x, title, point, color in (
            (left, 'Current', self.move['from_nm'], muted),
            (right, 'Proposed', self.move['to_nm'], green),
        ):
            dc.SetPen(wx.Pen(color, 2))
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            dc.DrawRoundedRectangle(x - 20, 16, 40, 38, 5)
            dc.DrawCircle(x - 8, 35, 3)
            dc.DrawCircle(x + 8, 35, 3)
            coords = '%.2f, %.2f mm' % tuple(p / 1_000_000 for p in point)
            for y, line in ((65, title), (88, coords)):
                dc.DrawText(line, x - dc.GetTextExtent(line).width // 2, y)


class Companion(wx.Frame):
    def __init__(self, *, diagnostics=False, direct_trial=False, workspace=False):
        super().__init__(None, title='Copperpath · Open board', size=(950, 610) if workspace else (486, 455))
        self.SetMinSize((720, 520) if workspace else (450, 434))
        self.workspace = workspace
        self.source_scene = None
        self.move = None
        self.run = None
        self.discard_pending = False
        self.validated = False
        self.readback_pending = False
        self.native_move_open = False
        self.direct_trial = direct_trial
        self.checked_move_finished = False
        self.selected = []
        container = wx.Panel(self)
        box = wx.Panel(container) if workspace else container
        stack = wx.BoxSizer(wx.VERTICAL)
        box.SetSizer(stack)

        heading = wx.StaticText(box, label='Move a selected component')
        font = heading.GetFont()
        font.SetPointSize(17)
        font.MakeBold()
        heading.SetFont(font)
        stack.Add(heading, 0, wx.LEFT | wx.RIGHT | wx.TOP, 18)
        stack.Add(wx.StaticText(box, label='Checked example · KiCad 10.0.8' if workspace else 'Owned test board · live PCB companion'),
                  0, wx.LEFT | wx.RIGHT | wx.TOP, 18)
        self.selection = wx.StaticText(box, label='Reading KiCad selection…')
        stack.Add(self.selection, 0, wx.LEFT | wx.RIGHT | wx.TOP, 18)
        if workspace:
            from autorouter.placement_gui import board_canvas
            layout = wx.BoxSizer(wx.HORIZONTAL)
            self.diagram = board_canvas(wx, container, None, None, self.image_error, self.controls, read_only=True,
                                        empty_note='Reading the checked example from KiCad…')
            layout.Add(self.diagram, 1, wx.EXPAND | wx.ALL, 12)
            layout.Add(box, 0, wx.EXPAND | wx.TOP | wx.RIGHT, 12)
            container.SetSizer(layout)
            box.SetMinSize((316, -1))
        else:
            self.diagram = Preview(box)
            stack.Add(self.diagram, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 18)
        self.status = wx.TextCtrl(box, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE,
                                  size=(-1, 77))
        self.status.SetName('Move status and findings')
        stack.Add(self.status, 1 if workspace else 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 18)

        choices = wx.BoxSizer(wx.HORIZONTAL)
        self.refresh = wx.Button(box, label='Read selection')
        self.discard = wx.Button(box, label='Discard')
        self.next = wx.Button(box, label='Preview move')
        if workspace:
            stack.Add(self.next, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 18)
        for button in (self.refresh, self.discard) if workspace else (self.refresh, self.discard, self.next):
            choices.Add(button, 0, wx.RIGHT, 6)
        stack.Add(choices, 0, wx.ALL, 18)
        if workspace:
            self.saved = wx.Button(box, label='Open saved-project workspace…')
            self.saved.Bind(wx.EVT_BUTTON, self.open_saved)
            stack.Add(self.saved, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 18)
        self.refresh.Bind(wx.EVT_BUTTON, lambda _e: self.request('inspect'))
        self.discard.Bind(wx.EVT_BUTTON, self.on_discard)
        self.next.Bind(wx.EVT_BUTTON, self.advance)
        self.next.SetDefault()

        self.test_buttons = []
        if diagnostics:
            tests = wx.BoxSizer(wx.HORIZONTAL)
            for label, command in (('Cancel staged move', 'drop_test'),
                                   ('Test partial failure', 'partial_test')):
                button = wx.Button(box, label=label)
                tests.Add(button, 0, wx.RIGHT, 5)
                self.test_buttons.append(button)
                button.Bind(wx.EVT_BUTTON, lambda _e, kind=command: self.request(kind, self.move['id']))
            stack.Add(tests, 0, wx.EXPAND | wx.ALL, 18)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Show()
        self.request('inspect')

    def image_error(self, _reason):
        self.move = None
        self.validated = False
        self.status.SetValue('The board preview could not be drawn. Read the selection to try again.')
        self.controls()

    def open_saved(self, _event):
        if self.run is not None:
            return
        from autorouter.placement_gui import create_window
        replacement = create_window()
        replacement.Show()
        self.Destroy()

    def on_close(self, event):
        if self.run is not None and event.CanVeto():
            self.status.SetValue('A check is finishing. Its response cannot approve a move.')
            event.Veto()
        else:
            event.Skip()

    def advance(self, _event):
        if self.readback_pending:
            self.request('undo')
        elif self.native_move_open:
            self.request('check_live_move')
        elif self.move is None:
            self.request('preview')
        else:
            if self.workspace and not self.diagram.Ready():
                self.status.SetValue('Wait for the board preview before checking or applying the move.')
                return
            action = ('apply_direct' if self.direct_trial else 'open_move') if self.validated else 'validate'
            self.request(action, self.move['id'])

    def on_discard(self, _event):
        if self.run == 'validate':
            self.discard_pending = True
            self.status.SetValue('Discarded. Waiting for the isolated check to finish.')
            self.controls()
        else:
            self.request('discard')

    def controls(self):
        self.refresh.Enable(self.run is None and not self.native_move_open)
        self.discard.Enable(self.move is not None and not self.native_move_open
                            and not self.discard_pending and self.run in (None, 'validate'))
        self.next.SetLabel('Verify KiCad Undo' if self.readback_pending else
                           'Check KiCad move' if self.native_move_open else
                           ('Apply checked move' if self.direct_trial else 'Review in KiCad') if self.validated else
                           'Check move' if self.move else 'Preview move')
        self.next.Enable(self.run is None and not self.checked_move_finished and (self.readback_pending or len(self.selected) == 1
                                               and self.selected[0] in ('J1', 'J2')
                                               and (not self.workspace or self.diagram.Ready())))
        for button in self.test_buttons:
            button.Enable(self.run is None and self.move is not None and not self.native_move_open)
        if self.workspace:
            self.saved.Enable(self.run is None)
        else:
            self.diagram.move = self.move
            self.diagram.Refresh()
        self.Layout()

    def request(self, command, *args):
        if self.run is not None:
            return
        if self.workspace and command == 'inspect':
            self.move = None
            self.validated = False
        self.run = command
        if command == 'validate':
            self.status.SetValue('KiCad is checking an isolated copy. You can discard this proposal.')
        self.controls()

        def receive():
            try:
                print(json.dumps(dict(command=command, args=args)), flush=True)
                response = json.loads(sys.stdin.readline())
            except (OSError, ValueError):
                response = dict(ok=False, message='The KiCad connection closed.')
            wx.CallAfter(self.reply, command, response)

        threading.Thread(target=receive, daemon=True).start()

    def reply(self, command, response):
        self.run = None
        if self.discard_pending:
            self.discard_pending = False
            self.request('discard')
            return
        if not response['ok']:
            if command != 'check_live_move' or not response['message'].startswith('Finish or cancel'):
                self.move = None
                self.validated = False
                self.native_move_open = False
            if self.workspace and command == 'apply_direct' and response.get('verify_undo') is True:
                self.readback_pending = True
            self.status.SetValue(response['message'])
        else:
            result = response['value']
            if command == 'inspect':
                self.selected = result['selection']
                self.selection.SetLabel('Selected in KiCad · ' + (', '.join(self.selected) or 'No footprint'))
                self.status.SetValue('The editor contains unsaved board changes.' if result['board_changed']
                                     else 'Select J1 or J2 to preview a 1 mm translation.')
                if self.workspace:
                    self.source_scene = result['scene']
                    self.show_scene(self.source_scene)
            elif command == 'preview':
                self.move = result
                self.status.SetValue(result['ref'] + ' · Preview only. Check against the original project before applying.')
                if self.workspace:
                    self.show_scene(result['scene'])
            elif command == 'validate':
                self.validated = True
                self.status.SetValue(
                    f"KiCad checked the move. {result['opens']} existing opens, "
                    f"{result['warnings']} warning(s), {result['ignored']} original ignored checks.\n"
                    + '\n'.join(result['findings']))
            elif command == 'open_move':
                self.native_move_open = True
                x, y = ((b - a) / 1_000_000 for a, b in zip(self.move['from_nm'], self.move['to_nm']))
                self.status.SetValue(f"In KiCad, select {self.move['ref']} and choose Move Exactly (Shift+M). "
                                     f"Set Move X to {x:g} mm, Move Y to {y:g} mm and Rotate to 0°. "
                                     'Choose OK to apply or Cancel. Then check here.')
            elif command == 'check_live_move':
                self.native_move_open = False
                if result['applied']:
                    self.move = None
                    self.validated = False
                    self.readback_pending = True
                    self.status.SetValue('Move verified in the open board. To test Undo, use the matching '
                                         'Move Exactly entry in KiCad, then verify here.')
                else:
                    self.status.SetValue('The KiCad board is unchanged. Review the preview or discard it.')
            elif command == 'apply_direct':
                self.move = None
                self.validated = False
                self.readback_pending = True
                self.status.SetValue(('The exact in-editor move passed readback.' if result['exact'] else
                                      'The in-editor transaction differs from the checked preview.')
                    + ' Use KiCad Undo on “Copperpath checked component move”, then verify the prior board here.')
            else:
                self.move = None
                self.validated = False
                self.readback_pending = False
                if command == 'undo' and self.direct_trial:
                    self.checked_move_finished = True
                self.status.SetValue({
                    'discard': 'Proposal discarded. The board is unchanged.',
                    'undo': 'KiCad Undo restored the prior board, including unrelated unsaved edits.',
                    'drop_test': 'KiCad discarded the staged move. The board is unchanged.',
                    'partial_test': 'The mixed update was refused and dropped. The board is unchanged.',
                }[command])
                if self.workspace and command in ('discard', 'undo'):
                    self.show_scene(self.source_scene)
        self.controls()

    def show_scene(self, scene):
        try:
            self.diagram.SetScene(scene)
        except Exception as exc:
            self.image_error(str(exc))


if __name__ == '__main__':
    app = wx.App(False)
    Companion(diagnostics='--diagnostics' in sys.argv, direct_trial='--direct-1008-trial' in sys.argv,
              workspace='--workspace' in sys.argv)
    app.MainLoop()
