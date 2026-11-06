"""Independent pinned Native witness for the bounded ordinary front scope.

Never writes a board or grants placement authority. Source parsing, exact AST
translation and the three actual full-project DRC passes remain separate checks.
"""


def capture(native, pcbnew, raw, contract, fc):
    expected = contract.inspect_board(raw, scope=contract.ORDINARY_SCOPE)
    need = contract.need
    need(native.GetCopperLayerCount() == 2, 'Native two-copper census differs')

    def uid(item): return str(item.m_Uuid.AsString())
    def xy(value):
        row = [value.x, value.y]
        need(all(type(n) is int and abs(n) <= 2_000_000_000 for n in row), 'Exact Native integer coordinate required')
        return row
    def integer(value):
        need(type(value) is int and 0 <= value <= 2_000_000_000, 'Exact Native integer dimension required')
        return value
    def boolean(value):
        need(type(value) is bool, 'Exact Native Boolean required')
        return value
    def angle(value):
        need(type(value) in (int, float) and abs(value) <= 360 and value % 90 == 0,
             'Exact Native cardinal angle required')
        return int(value) % 360
    def layer(value):
        names = {'F.Cu': 'F_Cu', 'B.Cu': 'B_Cu', 'F.CrtYd': 'F_CrtYd',
                 'F.SilkS': 'F_SilkS', 'B.SilkS': 'B_SilkS', 'F.Fab': 'F_Fab', 'B.Fab': 'B_Fab',
                 'Dwgs.User': 'Dwgs_User', 'Cmts.User': 'Cmts_User', 'Eco1.User': 'Eco1_User',
                 'Eco2.User': 'Eco2_User', 'Edge.Cuts': 'Edge_Cuts'}
        names.update({'User.' + str(i): 'User_' + str(i) for i in range(1, 10)})
        need(value in names, 'Unsupported Native layer selector')
        return getattr(pcbnew, names[value])
    def graphics(items, rows):
        by_id = {uid(item): item for item in items}
        need(len(by_id) == len(items) == len(rows), 'Native graphic census differs')
        for row in rows:
            item = by_id.get(row['uuid'])
            need(item is not None and item.GetLayer() == layer(row['layer']), 'Native graphic identity/layer differs')
            if row['kind'] in ('fp_line', 'fp_rect', 'gr_line', 'gr_rect'):
                shape = pcbnew.SHAPE_T_RECT if row['kind'].endswith('rect') else pcbnew.SHAPE_T_SEGMENT
                need(isinstance(item, pcbnew.PCB_SHAPE) and item.GetShape() == shape,
                     'Native straight graphic kind differs')
                need(xy(item.GetStart()) == row['start_nm'] and xy(item.GetEnd()) == row['end_nm']
                     and integer(item.GetWidth()) == row['stroke_nm'] and boolean(item.IsLocked()) == row['locked'],
                     'Native graphic geometry/lock differs')
                need(item.GetFillMode() == (pcbnew.FILL_T_FILLED_SHAPE if row['fill'] == 'solid'
                     else pcbnew.FILL_T_NO_FILL), 'Native graphic fill differs')
            else:
                need(isinstance(item, pcbnew.PCB_TEXT) and row['kind'] in ('gr_text', 'fp_text'),
                     'Native passive text kind differs')
                need(str(item.GetText()) == row['text'] and xy(item.GetPosition()) == row['position_nm']
                     and angle(item.GetTextAngleDegrees()) == row['angle'], 'Native passive text differs')

    graphics(list(native.GetDrawings()), expected['outline']['primitives'] + expected['graphics'])
    native_fps = {uid(fp): fp for fp in native.GetFootprints()}
    need(len(native_fps) == len(list(native.GetFootprints())) == len(expected['footprints']), 'Native footprint census differs')
    pad_ids, netcodes = set(), {}
    for source in expected['footprints']:
        fp = native_fps.get(source['uuid'])
        need(fp is not None and str(fp.GetReference()) == source['reference']
             and xy(fp.GetPosition()) == source['position_nm'] and angle(fp.GetOrientationDegrees()) == source['angle']
             and fp.GetLayer() == pcbnew.F_Cu and boolean(fp.IsFlipped()) is False
             and boolean(fp.IsLocked()) == source['locked'] and not list(fp.Zones()),
             'Native footprint identity/pose/lock/area differs')
        # Native fields are separately managed from graphical items. Exact source
        # property syntax is retained by the AST check; actual fields with source
        # UUIDs must also retain their native value/position/layer.
        properties = [row for row in source['graphics'] if row['kind'] == 'property']
        native_fields = {uid(item): item for item in fp.GetFields()}
        for row in properties:
            if row['uuid'] is None:
                item = fp.GetField(row['name'])
                need(item is not None and str(item.GetText()) == row['text'] and item.GetLayer() == layer(row['layer'])
                         and xy(item.GetPosition()) == row['position_nm']
                         and angle(item.GetTextAngleDegrees()) == row['angle'],
                     'Native source property absent')
            else:
                item = native_fields.get(row['uuid'])
                named = fp.GetField(row['name'])
                need(item is not None and named is not None and uid(named) == row['uuid']
                     and str(item.GetText()) == row['text'] and item.GetLayer() == layer(row['layer'])
                     and xy(item.GetPosition()) == row['position_nm']
                     and angle(item.GetTextAngleDegrees()) == row['angle'], 'Native source property differs')
        graphics(list(fp.GraphicalItems()), source['courtyard']['primitives']
                 + [row for row in source['graphics'] if row['kind'] != 'property'])
        pads = {uid(pad): pad for pad in fp.Pads()}
        need(len(pads) == len(list(fp.Pads())) == len(source['pads']), 'Native footprint pad census differs')
        for row in source['pads']:
            pad = pads.get(row['uuid'])
            need(pad is not None and row['uuid'] not in pad_ids, 'Native pad identity differs'); pad_ids.add(row['uuid'])
            smd = row['kind'] == 'smd'
            required_layers = ({pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_Paste} if smd
                               else set(pcbnew.LSET.AllCuMask().Seq()) | {pcbnew.F_Mask, pcbnew.B_Mask})
            need(pad.GetAttribute() == (pcbnew.PAD_ATTRIB_SMD if smd else pcbnew.PAD_ATTRIB_PTH)
                 and boolean(pad.IsFlipped()) is False and set(pad.GetLayerSet().Seq()) == required_layers,
                 'Native pad type/side/layer set differs')
            shape = {'circle': pcbnew.PAD_SHAPE_CIRCLE, 'rect': pcbnew.PAD_SHAPE_RECT,
                     'roundrect': pcbnew.PAD_SHAPE_ROUNDRECT}[row['shape']]
            for copper in ((pcbnew.F_Cu,) if smd else (pcbnew.F_Cu, pcbnew.B_Cu)):
                need(pad.GetShape(copper) == shape and xy(pad.GetSize(copper)) == row['size_nm']
                     and xy(pad.GetOffset(copper)) == [0, 0], 'Native pad shape/size/offset differs')
                if row['shape'] == 'roundrect':
                    need(pad.GetRoundRectRadiusRatio(copper) == row['roundrect_rratio']
                         and integer(pad.GetRoundRectCornerRadius(copper)) == round(min(row['size_nm']) * row['roundrect_rratio']),
                         'Native rounded corner differs')
            need(xy(pad.GetPosition()) == row['position_nm'] and xy(pad.GetFPRelativePosition()) == row['offset_nm']
                 and angle(pad.GetOrientationDegrees()) == row['angle'] and xy(pad.GetDrillSize()) == row['drill_nm']
                 and str(pad.GetNumber()) == row['number'] and str(pad.GetNetname()) == row['net']
                 and boolean(pad.GetRemoveUnconnected()) == row['remove_unused_layers']
                 and boolean(pad.GetKeepTopBottom()) == row['keep_end_layers'], 'Native pad position/net/drill/flags differ')
            code = integer(pad.GetNetCode()); need(code > 0, 'Named Native pad net required'); netcodes[row['uuid']] = code
    need(len(list(native.GetPads())) == len(pad_ids), 'Native board pad census differs')
    routes, route_netcodes = [], {}
    for item in native.GetTracks():
        need(isinstance(item, pcbnew.PCB_TRACK) and not isinstance(item, (pcbnew.PCB_VIA, pcbnew.PCB_ARC))
             and item.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu), 'Native straight outer copper required')
        identity = uid(item); need(identity not in route_netcodes, 'Duplicate Native route identity')
        code = integer(item.GetNetCode()); need(code > 0, 'Named Native route net required'); route_netcodes[identity] = code
        routes.append(dict(uuid=identity, kind='segment', net=str(item.GetNetname()), start_nm=xy(item.GetStart()),
            end_nm=xy(item.GetEnd()), width_nm=integer(fc.route_width(item, pcbnew)),
            layer='F.Cu' if item.GetLayer() == pcbnew.F_Cu else 'B.Cu', locked=boolean(item.IsLocked())))
    need(sorted(routes, key=lambda row: row['uuid']) == expected['routes'], 'Native preserved copper differs')
    areas = fc.observe_areas(native, pcbnew)
    need(areas['footprint_zone_count'] == areas['footprint_rulearea_count'] == 0, 'Native footprint areas unsupported')
    by_id = {row['uuid']: row for row in areas['zones']}
    need(len(by_id) == len(areas['zones']) == len(expected['zones']), 'Native zone census differs')
    for row in expected['zones']: contract.check_ordinary_zone(row, by_id.get(row['uuid']))
    return expected, dict(native_pad_netcodes=netcodes, native_route_netcodes=route_netcodes, actual_native_areas=areas)
