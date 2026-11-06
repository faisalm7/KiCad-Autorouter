"""Source-run placement review over retained Native evidence; never a PCB writer.

A selected or edited pose is a draft. Saving intent does not execute placement,
route a board, acknowledge warnings, or qualify an edited pose. The installed
routing GUI is unchanged. This adapter reuses the narrow captured contract until
its general source-capture/qualification bridge is ready.
"""
import argparse
import copy
from decimal import Decimal, InvalidOperation
import importlib.util
import json
from pathlib import Path
import sys
import threading
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class Review:
    def __init__(self, observation, options, alternatives, qualified_pose, witness):
        from experiments.placement_native_proposal_v1 import contract
        from experiments.constrained_placement_v1 import constraints
        self.contract, self.constraints = contract, constraints
        self.observation = copy.deepcopy(observation)
        self.options = contract.scope_options(**copy.deepcopy(options))
        self.facts = contract.facts_from_observation(self.observation, **self.options)
        if type(alternatives) is not list or not 1 <= len(alternatives) <= 3:
            raise ValueError('One to three bounded alternatives are required.')
        self.alternatives = [contract.quantized_translation(self.facts, pose)[0] for pose in alternatives]
        self.qualified_pose = contract.quantized_translation(self.facts, qualified_pose)[0]
        self.witness = copy.deepcopy(witness)
        self.witness_digest = constraints.digest(self.witness)
        self.revision = 0
        self.intent = None
        self.choose(0)

    def choose(self, index):
        if self.revision >= 256:
            raise ValueError('Review revision limit reached; reopen an explicit review.')
        if type(index) is not int or not 0 <= index < len(self.alternatives):
            raise ValueError('Choose an available alternative.')
        pose, moves = self.contract.quantized_translation(self.facts, self.alternatives[index])
        self.pose, self.moves = pose, moves
        self.revision += 1
        self.intent = None

    def edit(self, component, x, y):
        if self.revision >= 256:
            raise ValueError('Review revision limit reached; reopen an explicit review.')
        if component not in self.options['selected']:
            raise ValueError('Only the explicit selected footprints may be edited.')
        if component in self.constraints.immovable(self.facts):
            raise ValueError('Fixed, locked or routed-net footprints cannot move.')
        def nm(text):
            if type(text) is not str or len(text) > 32:
                raise ValueError('Enter a bounded decimal coordinate in millimetres.')
            try:
                value = Decimal(text)
                if not value.is_finite() or abs(value) > 2000:
                    raise ValueError('Coordinate must be finite and within ±2000 mm.')
                return int((value * 1000000).to_integral_value())
            except InvalidOperation as exc:
                raise ValueError('Enter a decimal coordinate in millimetres.') from exc
        moves = copy.deepcopy(self.moves)
        moves[component] = [nm(x), nm(y)]
        pose = self.contract.validate_moves(self.observation, moves, **self.options)
        # Atomic adoption: refused geometry leaves the earlier draft intact.
        self.pose, self.moves = pose, moves
        self.revision += 1
        self.intent = None

    @property
    def matches_native_pose(self):
        return self.pose == self.qualified_pose

    def decision(self, *, acknowledged, accepted, current_witness):
        if type(acknowledged) is not bool or not acknowledged or type(accepted) is not bool:
            raise ValueError('Explicit current review intent is required.')
        if self.constraints.digest(current_witness) != self.witness_digest:
            self.intent = None
            raise ValueError('Placement source or retained evidence changed; reopen the review.')
        self.contract.validate_moves(self.observation, self.moves, **self.options)
        self.intent = dict(schema=1, kind='selected-placement-draft-intent-v1',
            choice='reviewed_draft' if accepted else 'reject', revision=self.revision,
            witness_sha256=self.witness_digest, facts_sha256=self.constraints.digest(self.facts),
            pose_sha256=self.constraints.digest(self.pose), moves_nm=copy.deepcopy(self.moves),
            options=copy.deepcopy(self.options), matches_retained_native_pose=self.matches_native_pose,
            new_native_validation_performed=False, native_validation_required_for_changed_pose=not self.matches_native_pose,
            execution_authorized=False, routing_accepted=False, warning_acknowledged=False,
            human_PCB_approval=False, note='Review intent only. No PCB is written and no route is started.')
        return copy.deepcopy(self.intent)


def load(runtime, evidence, protocol):
    from experiments import placement_native_evidence as reader
    from experiments.placement_native_proposal_v1 import contract
    from autorouter import floor_route as f, placement_clearance as pc, pipeline as p
    witness = reader.check(evidence, runtime, protocol, contract.MULTIPAD_SCOPE)
    work = evidence / 'work'
    def pinned(name):
        import hashlib
        raw = pc.read_bytes(work / name, 2 * 1024**2)
        if hashlib.sha256(raw).hexdigest() != witness['artifact_hashes']['work/' + name]:
            raise ValueError('Retained placement bytes changed during opening.')
        return json.loads(raw)
    observation = pinned('capture-observation.json')['observation']
    result = pinned('result.json')
    proposal = pinned('proposal.json')
    options = dict(scope=witness['placement_scope'], selected=witness['selected_footprints'],
                   region_nm=witness['allowed_region_nm'])
    return Review(observation, options, [item['candidate'] for item in result['search']['alternatives']],
                  proposal['candidate'], witness)


def bitmap_with_labels(wx, svg, size=(870, 520)):
    """NanoSVG omits text; paint our own passive renderer's text with wx fonts."""
    image = wx.svg.SVGimage.CreateFromBytes(svg.encode())
    scale = min(size[0] / image.width, size[1] / image.height)
    bitmap = image.ConvertToBitmap(scale=scale, width=round(image.width * scale), height=round(image.height * scale))
    dc = wx.MemoryDC(bitmap)
    for node in ET.fromstring(svg).findall('{http://www.w3.org/2000/svg}text'):
        font = wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_SWISS))
        font.SetPixelSize(wx.Size(0, max(9, round(float(node.get('font-size')) * scale))))
        if node.get('font-weight') == 'bold': font = font.Bold()
        dc.SetFont(font); dc.SetTextForeground(wx.Colour(node.get('fill')))
        text = node.text or ''
        _, height, descent, _ = dc.GetFullTextExtent(text)
        dc.DrawText(text, round(float(node.get('x')) * scale),
                    round(float(node.get('y')) * scale - height + descent))
    dc.SelectObject(wx.NullBitmap)
    return bitmap


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'evidence', 'protocol', 'output'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args(argv)
    runtime, evidence, protocol, output = (Path(getattr(args, key)).absolute() for key in ('runtime','evidence','protocol','output'))
    # Installed runtime remains authoritative for Native evidence readback.
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(runtime), str(ROOT)]
    from autorouter import handoff as h, pipeline as p, floor_route as f, placement_clearance as pc, gui
    from experiments import placement_native_evidence as reader
    from experiments.placement_native_proposal_v1 import contract
    for path in (runtime, evidence, protocol): h.real_path(path)
    output = h.real_path(output, existing=False)
    if output.exists() or output.parent != ROOT / '.runs':
        raise ValueError('Use a fresh source-project .runs directory; no existing work is overwritten.')
    # No archive scan, model, optimizer or Native process: only shared retained checks.
    review = load(runtime, evidence, protocol)
    output.mkdir(mode=0o700); owner = {}; h.capture_destination(owner, output)
    own_file = Path(__file__); view_file = ROOT / 'autorouter/placement_view.py'
    pins = {str(path): p.sha(path) for path in (own_file, view_file)}
    recorded_tools = f.read_json(evidence / 'work/result.json')['tools']
    from experiments.placement_native_proposal_v1 import driver
    recorded_code = driver.code_pins()
    spec = importlib.util.spec_from_file_location('placement_view_source', view_file)
    view = importlib.util.module_from_spec(spec); spec.loader.exec_module(view)
    def fresh():
        h.owned_destination(owner)
        if any(p.sha(Path(path)) != digest for path, digest in pins.items()):
            raise ValueError('Review code changed; restart this review.')
        return reader.check(evidence, runtime, protocol, contract.MULTIPAD_SCOPE)
    def late_material():
        # The worker already replayed the full Native proof. The UI adoption
        # edge checks unchanged material, not that expensive validation again.
        h.owned_destination(owner)
        witness = review.witness
        if (pc.inventory(evidence, max_bytes=512 * 1024**2) != witness['artifact_hashes']
                or gui.source_inventory(Path(witness['original_source'])) != witness['original_source_hashes']
                or p.sha(protocol) != witness['protocol_sha256']
                or p.sha(Path(reader.__file__)) != witness['reader_sha256']
                or driver.code_pins() != recorded_code
                or any(p.sha(Path(path)) != digest for path, digest in pins.items())):
            raise ValueError('Source, evidence or review code changed before saving intent.')
        p.check_recorded_tool_pins(recorded_tools)
    def write(name, raw):
        h.owned_destination(owner)
        target = output / name
        with target.open('xb') as stream: stream.write(raw)
        target.chmod(0o600)
        return target
    write('opened.json', (json.dumps(dict(schema=1,evidence=str(evidence),protocol=str(protocol),
        witness_sha256=review.witness_digest,source_pins=pins,actual_GUI=False,
        Native_executed=False,model_calls=0,production_placement=False),indent=2)+'\n').encode())
    import wx
    import wx.svg
    class Window(wx.Frame):
        def __init__(self):
            super().__init__(None, title='Placement review — experimental', size=(920, 910))
            self.busy = False; self.closed = False; self.dirty = False
            panel = wx.Panel(self); box = wx.BoxSizer(wx.VERTICAL)
            heading = wx.StaticText(panel,label='Review selected placement')
            heading.SetFont(heading.GetFont().Bold()); box.Add(heading,0,wx.ALL,12)
            note = wx.StaticText(panel,label='Inspect alternatives and adjust selected positions. Original copper stays fixed.\n'
                'This source-run preview saves a draft only; it cannot apply changes or start routing.')
            box.Add(note,0,wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
            self.picture = wx.StaticBitmap(panel);box.Add(self.picture,0,wx.ALIGN_CENTER_HORIZONTAL|wx.LEFT|wx.RIGHT,12)
            row = wx.BoxSizer(wx.HORIZONTAL)
            self.alternative = wx.Choice(panel,choices=['Alternative '+str(i+1) for i in range(len(review.alternatives))])
            self.alternative.SetSelection(0);self.alternative.Bind(wx.EVT_CHOICE,self.select)
            row.Add(self.alternative,0,wx.ALL,6)
            references={fp['uuid']:fp['reference'] for fp in review.observation['footprints']}
            self.selected=list(review.options['selected'])
            self.part=wx.Choice(panel,choices=[references[value] for value in self.selected]);self.part.SetSelection(0)
            self.part.Bind(wx.EVT_CHOICE,lambda event:self.coordinates())
            row.Add(self.part,0,wx.ALL,6)
            row.Add(wx.StaticText(panel,label='X (mm)'),0,wx.ALL|wx.ALIGN_CENTER_VERTICAL,6)
            self.x=wx.TextCtrl(panel,size=(100,-1));row.Add(self.x,0,wx.ALL,6)
            row.Add(wx.StaticText(panel,label='Y (mm)'),0,wx.ALL|wx.ALIGN_CENTER_VERTICAL,6)
            self.y=wx.TextCtrl(panel,size=(100,-1));row.Add(self.y,0,wx.ALL,6)
            for control in (self.x,self.y):control.Bind(wx.EVT_TEXT,self.pending_edit)
            self.edit_button=wx.Button(panel,label='Update draft');self.edit_button.Bind(wx.EVT_BUTTON,self.edit)
            row.Add(self.edit_button,0,wx.ALL,6);box.Add(row)
            self.state=wx.StaticText(panel);box.Add(self.state,0,wx.ALL,12)
            self.ack=wx.CheckBox(panel,label='I reviewed this exact draft and its limits. This is not PCB approval.')
            box.Add(self.ack,0,wx.LEFT|wx.RIGHT|wx.BOTTOM,12)
            buttons=wx.BoxSizer(wx.HORIZONTAL)
            self.save=wx.Button(panel,label='Save reviewed draft');self.save.Bind(wx.EVT_BUTTON,lambda event:self.decide(True))
            self.reject=wx.Button(panel,label='Reject draft');self.reject.Bind(wx.EVT_BUTTON,lambda event:self.decide(False))
            for button in (self.save,self.reject):buttons.Add(button,0,wx.ALL,6)
            box.Add(buttons)
            self.message=wx.TextCtrl(panel,style=wx.TE_MULTILINE|wx.TE_READONLY,size=(-1,75));box.Add(self.message,1,wx.EXPAND|wx.ALL,12)
            self.controls=[self.alternative,self.part,self.x,self.y,self.edit_button,self.ack,self.save,self.reject]
            panel.SetSizer(box);self.Bind(wx.EVT_CLOSE,self.close);self.refresh()
        def coordinates(self):
            xy=review.moves[self.selected[self.part.GetSelection()]]
            self.x.ChangeValue(format(Decimal(xy[0])/1000000,'f'));self.y.ChangeValue(format(Decimal(xy[1])/1000000,'f'))
        def refresh(self):
            self.dirty=False;self.ack.SetValue(False);self.coordinates()
            self.save.Enable();self.reject.Enable()
            label=('Matches retained Native-checked pose; fresh evidence readback required.' if review.matches_native_pose
                   else 'Geometry draft only — fresh Native qualification required before routing.')
            svg=view.render(review.observation,review.moves,review.options['selected'],review.options['region_nm'],state=label)
            self.picture.SetBitmap(bitmap_with_labels(wx,svg))
            self.state.SetLabel(label);self.state.Wrap(860);self.Layout()
            write('preview-%04d.svg'%review.revision,svg.encode())
        def pending_edit(self,event):
            self.dirty=True;self.ack.SetValue(False);review.intent=None
            self.save.Disable();self.reject.Disable()
            self.message.SetValue('Coordinates are not applied yet. Update the draft or choose an alternative to discard them.')
            event.Skip()
        def select(self,event):
            if self.busy:return
            try:
                review.choose(self.alternative.GetSelection());self.refresh();self.message.SetValue('Alternative changed. Earlier review intent was cleared.')
            except Exception as exc:
                self.ack.SetValue(False);review.intent=None;self.message.SetValue('Selection refused: '+str(exc))
        def edit(self,event):
            if self.busy:return
            try:
                review.edit(self.selected[self.part.GetSelection()],self.x.GetValue(),self.y.GetValue())
                self.refresh();self.message.SetValue('Draft updated. All fixed geometry and movement constraints passed; no PCB was written.')
            except Exception as exc:
                self.ack.SetValue(False);review.intent=None;self.message.SetValue('Edit refused: '+str(exc))
        def decide(self,accepted):
            if self.busy:return
            if self.dirty:
                self.message.SetValue('Update or discard the pending coordinates before reviewing intent.');return
            if not self.ack.GetValue():
                self.message.SetValue('Review the current draft and acknowledge its limits first.');return
            self.busy=True
            for control in self.controls:control.Disable()
            self.message.SetValue('Checking source, candidate and retained Native evidence before saving intent…')
            revision=review.revision
            def work():
                result=None;error=None
                try:
                    current=fresh()
                    if self.closed:raise ValueError('Review was closed; no intent saved.')
                    result=review.decision(acknowledged=True,accepted=accepted,current_witness=current)
                    if review.revision!=revision:raise ValueError('Draft changed during checking.')
                    # Return to UI before publication; closing rejects queued intent.
                except Exception as exc:error=str(exc)
                wx.CallAfter(self.finish,result,error)
            threading.Thread(target=work,daemon=False).start()
        def finish(self,result,error):
            self.busy=False
            if self.closed:self.Destroy();return
            for control in self.controls:control.Enable()
            self.ack.SetValue(False)
            if error:self.message.SetValue('Intent refused: '+error);return
            try:
                if self.dirty or review.revision!=result['revision']:raise ValueError('Draft changed before saving.')
                late_material()
                target=write('intent-'+uuid.uuid4().hex+'.json',(json.dumps(result,indent=2)+'\n').encode())
                self.message.SetValue('Saved '+result['choice']+' intent. No PCB changed; no routing started.\n'+str(target))
            except Exception as exc:self.message.SetValue('Intent not saved: '+str(exc))
        def close(self,event):
            self.closed=True;review.intent=None
            if self.busy:
                self.message.SetValue('Closing after read-only evidence check; no intent will be saved.')
                event.Veto()
            else:self.Destroy()
    app=wx.App(False);window=Window();window.Show();app.MainLoop()
    return 0


if __name__=='__main__':raise SystemExit(main())
