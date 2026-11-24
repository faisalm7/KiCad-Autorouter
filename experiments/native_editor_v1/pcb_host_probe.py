"""Opt-in legacy import probe for a docked, read-only PCB pane in KiCad 10.0.8.

Load this module only in an isolated profile. The source variable names one
existing absolute PCB path. The receipt variable names a fresh JSONL file in
a canonical directory private to the current user. No ActionPlugin is run or
registered. This internal hosting probe makes no PCB or settings edits.
"""

import json
import os
from pathlib import Path
import stat
import time


_PANE = "CopperpathNativeHostProbe"
_ATTACH_SECONDS = 12
_POLL_MS = 300
_RECEIPT_LIMIT = 64


def _open_receipt(path):
    if not path.is_absolute() or path.parent.resolve(strict=True) != path.parent:
        raise ValueError("Receipt must have a canonical absolute parent directory.")
    parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        info = os.fstat(parent)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ValueError("Receipt directory must be private to the current user.")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        fd = os.open(path.name, flags, 0o600, dir_fd=parent)
    finally:
        os.close(parent)
    return os.fdopen(fd, "w", encoding="utf-8", buffering=1)


class _HostProbe:
    def __init__(self, wx, aui, pcbnew, source, receipt):
        self.wx, self.aui, self.pcbnew = wx, aui, pcbnew
        self.source, self.receipt = source, receipt
        self.deadline = time.monotonic() + _ATTACH_SECONDS
        self.panel = self.timer = self.last_selection = None
        self.events = 0

    def record(self, event, **facts):
        if self.receipt.closed or self.events >= _RECEIPT_LIMIT:
            return
        row = {"schema": 1, "event": event, "pid": os.getpid(),
               "time_ns": time.monotonic_ns(), **facts}
        self.receipt.write(json.dumps(row, ensure_ascii=True) + "\n")
        self.events += 1

    def same_board(self):
        board = self.pcbnew.GetBoard()
        return board is not None and Path(board.GetFileName()) == self.source

    def find_frame(self):
        matches = []
        for frame in self.wx.GetTopLevelWindows():
            manager = self.aui.AuiManager.GetManager(frame)
            if manager is None or manager.GetManagedWindow() != frame:
                continue
            canvas = manager.GetPane("DrawFrame")
            layers = manager.GetPane("LayersManager")
            if (canvas.IsOk() and layers.IsOk() and canvas.window.GetParent() == frame
                    and canvas.dock_direction == self.aui.AUI_DOCK_CENTER):
                matches.append((frame, manager, canvas.window))
        if len(matches) > 1:
            raise RuntimeError("More than one native PCB frame matched.")
        return matches[0] if matches else None

    def attach(self):
        try:
            match = self.find_frame() if self.same_board() else None
            if match is None:
                if time.monotonic() < self.deadline:
                    self.wx.CallLater(150, self.attach)
                else:
                    self.refuse("Exact PCB frame was unavailable within the attach window.")
                return
            self.dock(*match)
        except Exception as error:
            self.refuse(f"Native host attach failed ({type(error).__name__}).")

    def dock(self, frame, manager, canvas):
        wx = self.wx
        if manager.GetPane(_PANE).IsOk():
            raise RuntimeError("Probe pane already exists.")
        panel = wx.Panel(frame, name=_PANE)
        try:
            layout = wx.BoxSizer(wx.VERTICAL)
            self.selection_label = wx.StaticText(panel, label="Select a footprint on the board.")
            self.position_label = wx.StaticText(panel, label="")
            layout.Add(wx.StaticText(panel, label="Read-only PCB inspection"), 0, wx.ALL, 10)
            layout.Add(self.selection_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
            layout.Add(self.position_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
            panel.SetSizer(layout)
            info = (self.aui.AuiPaneInfo().Name(_PANE).Caption("Copperpath").Left()
                    .BestSize(frame.FromDIP(wx.Size(260, 130)))
                    .MinSize(frame.FromDIP(wx.Size(210, 100))).Floatable(False)
                    .CloseButton(False))
            if not manager.AddPane(panel, info):
                raise RuntimeError("The native manager declined the pane.")
            manager.Update()
            attached = manager.GetPane(_PANE)
            if not (attached.IsOk() and attached.IsDocked() and attached.window == panel
                    and panel.GetParent() == frame and canvas.GetParent() == frame):
                raise RuntimeError("Native dock-parent verification failed.")
            self.panel = panel
            self.timer = wx.Timer(panel)
            panel.Bind(wx.EVT_TIMER, self.poll, self.timer)
            panel.Bind(wx.EVT_WINDOW_DESTROY, self.destroyed)
            self.record("attached", editor_version="10.0.8", exact_source=True,
                        pane=_PANE, native_canvas="DrawFrame", native_layers="LayersManager",
                        pane_parent_is_managed_frame=True, canvas_parent_is_managed_frame=True,
                        is_docked=True, frame_id=frame.GetId(), pane_id=panel.GetId(),
                        canvas_id=canvas.GetId())
            self.timer.Start(_POLL_MS)
            self.poll(None)
        except Exception:
            if manager.GetPane(panel).IsOk():
                manager.DetachPane(panel)
                manager.Update()
            panel.Destroy()
            raise

    def poll(self, _event):
        try:
            if not self.same_board():
                self.selection_label.SetLabel("The PCB changed. Inspection stopped.")
                self.position_label.SetLabel("")
                self.refuse("Active PCB changed.")
                return
            if not self.panel.IsShownOnScreen():
                return
            selected = self.pcbnew.GetCurrentSelection()
            count = len(selected)
            facts = {"count": count}
            label, position = "Select one footprint on the board.", ""
            if count == 1 and selected[0].Type() == self.pcbnew.PCB_FOOTPRINT_T:
                footprint = self.pcbnew.Cast_to_FOOTPRINT(selected[0])
                point = footprint.GetPosition()
                reference = str(footprint.GetReference())[:64]
                facts.update(reference=reference, position_nm=[point.x, point.y])
                label = f"Footprint {reference}"
                position = f"X {point.x / 1_000_000:.3f} mm   Y {point.y / 1_000_000:.3f} mm"
            if facts != self.last_selection:
                self.record("selection", **facts)
                self.last_selection = facts
                self.selection_label.SetLabel(label)
                self.position_label.SetLabel(position)
                self.panel.Layout()
        except Exception as error:
            if self.panel.IsShownOnScreen():
                self.selection_label.SetLabel("Selection unavailable. Inspection stopped.")
                self.position_label.SetLabel("")
            self.refuse(f"Native selection read failed ({type(error).__name__}).")

    def destroyed(self, event):
        if event.GetEventObject() == self.panel:
            self.stop()
        event.Skip()

    def refuse(self, reason):
        try:
            self.record("stopped", reason=reason)
        finally:
            self.stop()

    def stop(self):
        timer, self.timer = self.timer, None
        if timer is not None:
            timer.Stop()
        self.receipt.close()


def _start():
    source_text = os.environ.get("COPPERPATH_PCB_HOST_PROBE_SOURCE")
    receipt_text = os.environ.get("COPPERPATH_PCB_HOST_PROBE_RECEIPT")
    if not source_text or not receipt_text:
        return
    source = Path(source_text)
    if (not source.is_absolute() or source.suffix != ".kicad_pcb"
            or not source.is_file() or source.resolve() != source):
        return
    receipt = _open_receipt(Path(receipt_text))
    try:
        import pcbnew
        import wx
        import wx.aui

        probe = _HostProbe(wx, wx.aui, pcbnew, source, receipt)
        if str(pcbnew.GetBaseVersion()) != "10.0.8":
            probe.refuse("This probe requires exactly KiCad 10.0.8.")
        elif not wx.IsMainThread() or wx.GetApp() is None:
            probe.refuse("The native wx editor event loop is unavailable.")
        else:
            probe.record("scheduled", editor_version="10.0.8")
            wx.CallAfter(probe.attach)
    except Exception:
        receipt.close()
        raise


_start()
