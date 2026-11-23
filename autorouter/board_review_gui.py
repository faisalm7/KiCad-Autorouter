"""Passive board navigation and inspection for saved and checked workspace views."""
from . import review_view, workspace_chrome as chrome


def board_review(wx, parent, on_error, *, empty_note):
    from .placement_gui import board_canvas

    class BoardReview(wx.Panel):
        def __init__(self):
            super().__init__(parent, style=wx.TAB_TRAVERSAL)
            self.render = None
            self.items = {}
            self.identity = None
            self.finding = None
            self.layer = wx.Choice(self, name='Copper layer')
            self.layer.Bind(wx.EVT_CHOICE, self.change_layer)
            tool_row = wx.BoxSizer(wx.HORIZONTAL)
            tool_row.Add(self.layer, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
            tool_row.AddStretchSpacer()
            self.zoom_label = wx.StaticText(self, label='100%')
            self.zoom_label.SetMinSize(self.FromDIP((40, -1)))
            tool_row.Add(self.zoom_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
            self.tools = []
            for label, title, action in (
                ('−', 'Zoom out', lambda _: self.canvas.magnify(1 / 1.5)),
                ('+', 'Zoom in', lambda _: self.canvas.magnify(1.5)),
                ('Fit', 'Fit board', lambda _: self.canvas.change_view(1.)),
            ):
                button = wx.Button(self, label=label, name=title, style=wx.BU_EXACTFIT)
                button.SetToolTip(title)
                button.Bind(wx.EVT_BUTTON, action)
                self.tools.append(button)
                tool_row.Add(button, 0, wx.RIGHT, 4)
            self.locations = wx.Choice(self, name='Locate a finding')
            self.locations.SetMinSize(self.FromDIP((180, -1)))
            self.locations.Bind(wx.EVT_CHOICE, self.finding_changed)
            self.locations.SetToolTip('Locate a KiCad finding using its verified board item identity.')
            controls = wx.BoxSizer(wx.HORIZONTAL)
            self.objects = wx.ComboBox(self, style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER,
                name='Find a component, pad or net')
            self.objects.SetHint('Find a part, pad or net')
            self.objects.SetMinSize(self.FromDIP((160, -1)))
            self.objects.Bind(wx.EVT_COMBOBOX, self.object_chosen)
            self.objects.Bind(wx.EVT_TEXT_ENTER, self.object_search)
            self.objects.SetToolTip('Type a reference, pad or exact net and press Return, or choose from the list.')
            controls.Add(self.objects, 1, wx.EXPAND | wx.RIGHT, 7)
            controls.Add(self.locations, 1, wx.EXPAND)
            self.canvas = board_canvas(wx, self, None, None, self.render_failed, read_only=True,
                on_inspect=self.select, on_view=self.change_zoom_label, empty_note=empty_note)
            _background, surface, accent = chrome.colours(wx)
            self.card = wx.Panel(self)
            self.card.SetBackgroundColour(wx.Colour(surface))
            self.item_title = chrome.heading(wx.StaticText(self.card, style=wx.ST_ELLIPSIZE_END | wx.ST_NO_AUTORESIZE), 11)
            self.item_title.SetForegroundColour(wx.Colour(accent))
            self.item_detail = wx.StaticText(self.card, style=wx.ST_ELLIPSIZE_END | wx.ST_NO_AUTORESIZE)
            card = wx.BoxSizer(wx.VERTICAL)
            card.Add(self.item_title, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 6)
            card.Add(self.item_detail, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)
            self.card.SetSizer(card)
            layout = wx.BoxSizer(wx.VERTICAL)
            layout.Add(tool_row, 0, wx.EXPAND | wx.BOTTOM, 4)
            layout.Add(controls, 0, wx.EXPAND | wx.BOTTOM, 5)
            layout.Add(self.canvas, 1, wx.EXPAND)
            layout.Add(self.card, 0, wx.EXPAND | wx.TOP, 4)
            self.SetSizer(layout)
            self.set_view(None)

        def change_zoom_label(self, zoom):
            self.zoom_label.SetLabel(f'{zoom:.0%}')

        def set_view(self, render=None, *, scene=None):
            self.render = render if render is not None else {'diagrams': {'F.Cu': scene} if scene else {}}
            self.finding = None
            layers = list(self.render['diagrams'])
            self.layer.Set(layers)
            if layers:
                self.layer.SetStringSelection('F.Cu' if 'F.Cu' in layers else layers[0])
            self.layer.Show(len(layers) > 1)
            self.zoom_label.Show(bool(layers))
            for button in self.tools:
                button.Show(bool(layers))
            self.findings = [row for row in self.render.get('findings', ()) if row['layers']]
            self.locations.Set(['Locate a finding…', *(row['label'] for row in self.findings)])
            self.locations.SetSelection(0)
            self.locations.Show(bool(self.findings))
            self.populate_layer(reset=True)

        def populate_layer(self, *, reset=False):
            self.identity = None
            self.active_layer = self.layer.GetStringSelection()
            self.scene = self.render['diagrams'].get(self.active_layer)
            self.items = {item['id']: item for item in self.scene.get('items', ())} if self.scene else {}
            self.set_item_choices(list(self.items))
            self.objects.Show(bool(self.items))
            self.card.Show(bool(self.scene))
            self.redraw(keep_view=not reset)
            self.Layout()

        def set_item_choices(self, identities, query=''):
            self.ids = identities
            self.objects.Set([self.items[identity]['label'] for identity in identities])
            self.objects.ChangeValue(query)

        def describe(self, title, detail):
            self.item_title.SetLabelText(title)
            self.item_title.SetToolTip(title)
            self.item_detail.SetLabelText(detail)
            self.item_detail.SetToolTip(detail)

        def render_failed(self, reason):
            self.identity = self.finding = None
            self.describe('Board drawing unavailable', 'Use the detailed findings to review the result.')
            on_error(reason)

        def redraw(self, *, keep_view=True):
            try:
                self.draw_selection(keep_view)
            except Exception as exc:
                self.canvas.SetScene(None)
                self.render_failed(str(exc))
                return False
            return True

        def draw_selection(self, keep_view):
            caption = self.render.get('caption', 'Placement preview')
            context = self.render.get('context_note', 'Placement geometry preview. Approval requires the separate checks.')
            detail = context
            scene = self.scene
            item = self.selected_item()
            if self.finding is not None:
                caption = self.finding['label']
                detail = 'Checked item highlight · full text in Findings'
                scene = review_view.finding_scene(self.render, self.active_layer, self.finding['index'])
            elif item is not None:
                caption = item['label']
                detail = item['detail']
                scene = review_view.inspect_item(scene, self.identity)
            self.describe(caption, detail)
            self.canvas.SetScene(scene, keep_view=keep_view)

        def selected_item(self):
            return self.items.get(self.identity)

        def change_layer(self, _):
            if self.finding is not None and self.layer.GetStringSelection() not in self.finding['layers']:
                self.finding = None
                self.locations.SetSelection(0)
            self.populate_layer()

        def finding_changed(self, _):
            index = self.locations.GetSelection() - 1
            self.finding = self.findings[index] if index >= 0 else None
            if self.finding is not None and self.active_layer not in self.finding['layers']:
                self.layer.SetStringSelection(self.finding['layers'][0])
            self.populate_layer()
            if self.finding is not None:
                point = next(point for point in self.finding['points'] if self.active_layer in point.layers)
                scale, tx, ty = self.scene['mm_to_svg']
                self.canvas.focus_item((point.xy[0] * scale + tx, point.xy[1] * scale + ty))

        def object_chosen(self, event):
            if 0 <= event.GetSelection() < len(self.ids):
                self.select(self.ids[event.GetSelection()], focus=True)

        def object_search(self, _):
            text = self.objects.GetValue().strip()
            query = text.casefold()
            if not query:
                self.identity = self.finding = None
                self.locations.SetSelection(0)
                self.set_item_choices(list(self.items))
                self.redraw()
                return
            exact = [identity for identity, item in self.items.items()
                     if item['label'].casefold() == query]
            if len(exact) == 1:
                self.select(exact[0], focus=True)
                return
            net_items = [identity for identity, item in self.items.items() if query == item['net'].casefold()]
            matches = net_items or [identity for identity, item in self.items.items() if query in item['label'].casefold()]
            if len(matches) == 1:
                self.select(matches[0], focus=True)
            else:
                self.identity = self.finding = None
                self.locations.SetSelection(0)
                self.set_item_choices(matches or list(self.items), text)
                if self.redraw():
                    detail = ('Open the item list to pick one.' if matches else 'Try another layer or a part reference.')
                    title = (f'{self.items[net_items[0]]["net"]} · {len(net_items)} items' if net_items else
                             f'{len(matches)} matching items' if matches else 'No matching item on this layer')
                    self.describe(title, detail)

        def select(self, identity, *, focus=False):
            item = self.items.get(identity)
            if item is None:
                return
            self.finding = None
            self.locations.SetSelection(0)
            self.identity = identity
            self.objects.ChangeValue(item['label'])
            drawn = self.redraw()
            if focus and drawn:
                self.canvas.focus_item(item['point'])

    return BoardReview()
