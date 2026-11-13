"""Independent pinned Native witness for the bounded ordinary front scope.

Never writes a board or grants placement authority. Source parsing, exact AST
translation and the three actual full-project DRC passes remain separate checks.
"""
from . import contract as c


def capture(native, pcbnew, raw, contract, fc, *, scope=c.ORDINARY_SCOPE):
    expected = contract.inspect_board(raw, scope=scope)
    need = contract.need
    tht = contract.tht_scope(scope)
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
    def stroke_style(item, row):
        # LINE_STYLE is an opaque, destructor-less SWIG pointer in this pinned
        # build. Use KiCad's in-memory formatter as the independent style
        # witness instead of dereferencing it, guessing an integer or writing
        # any source/candidate file. Coordinates have separate Native getters.
        formatter = pcbnew.PCB_IO_KICAD_SEXPR()
        formatter.Format(item)
        raw_style = formatter.GetStringOutput(True)
        need(type(raw_style) is str and 0 < len(raw_style.encode()) <= contract.MAX_BYTES,
             'Bounded Native graphic style serialization required')
        parsed = contract.sx.parse(raw_style)
        need(contract.uid(parsed) == row['uuid'], 'Native serialized graphic identity differs')
        stroke = contract.sx.one(parsed, 'stroke')
        need(stroke is not None and contract.atom(stroke, 'type') == row['stroke_type'],
             'Native fixed-context stroke style differs')
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
                if 'stroke_type' in row:
                    stroke_style(item, row)
            elif row['kind'] in ('fp_circle', 'fp_arc', 'fp_poly'):
                need(contract.fixed_context_scope(scope) and isinstance(item, pcbnew.PCB_SHAPE),
                     'Native fixed-context shape outside explicit scope')
                shape = {'fp_circle': pcbnew.SHAPE_T_CIRCLE, 'fp_arc': pcbnew.SHAPE_T_ARC,
                         'fp_poly': pcbnew.SHAPE_T_POLY}[row['kind']]
                need(item.GetShape() == shape and integer(item.GetWidth()) == row['stroke_nm']
                     and boolean(item.IsLocked()) == row['locked'], 'Native fixed-context shape/stroke/lock differs')
                stroke_style(item, row)
                need(item.GetFillMode() == (pcbnew.FILL_T_FILLED_SHAPE if row['fill'] == 'solid'
                     else pcbnew.FILL_T_NO_FILL), 'Native fixed-context fill differs')
                if row['kind'] == 'fp_circle':
                    # Native CIRCLE start is its centre (parsePCB_SHAPE), not
                    # a perimeter endpoint or a footprint-local coordinate.
                    need(xy(item.GetStart()) == row['center_nm'] and xy(item.GetEnd()) == row['end_nm']
                         and integer(item.GetRadius()) == row['radius_nm'],
                         'Native fixed-context circle geometry differs')
                elif row['kind'] == 'fp_arc':
                    # EDA_SHAPE may reverse the two ends to normalize winding;
                    # its cached midpoint retains the exact parsed arc witness.
                    swapped = boolean(item.EndsSwapped())
                    ends = [row['end_nm'], row['start_nm']] if swapped else [row['start_nm'], row['end_nm']]
                    need([xy(item.GetStart()), xy(item.GetEnd())] == ends
                         and xy(item.GetArcMid()) == row['mid_nm'], 'Native fixed-context arc geometry differs')
                else:
                    poly = item.GetPolyShape()
                    need(integer(poly.OutlineCount()) == 1 and integer(poly.HoleCount(0)) == 0 and integer(poly.ArcCount()) == 0,
                         'Native fixed-context polygon topology differs')
                    outline = poly.COutline(0)
                    need(integer(outline.PointCount()) == len(row['points_nm'])
                         and [xy(outline.CPoint(i)) for i in range(outline.PointCount())] == row['points_nm']
                         and [xy(point) for point in item.GetPolyPoints()] == row['points_nm'],
                         'Native fixed-context polygon points differ')
            else:
                need(isinstance(item, pcbnew.PCB_TEXT) and row['kind'] in ('gr_text', 'fp_text'),
                     'Native passive text kind differs')
                need(str(item.GetText()) == row['text'] and xy(item.GetPosition()) == row['position_nm']
                     and angle(item.GetTextAngleDegrees()) == row['angle'], 'Native passive text differs')
                if 'mirrored' in row:
                    need(boolean(item.IsMirrored()) == row['mirrored'], 'Native back artwork text mirror differs')

    graphics(list(native.GetDrawings()), expected['outline']['primitives'] + expected['graphics'])
    native_fps = {uid(fp): fp for fp in native.GetFootprints()}
    need(len(native_fps) == len(list(native.GetFootprints())) == len(expected['footprints']), 'Native footprint census differs')
    pad_ids, netcodes, metadata_witnesses = set(), {}, {}
    for source in expected['footprints']:
        fp = native_fps.get(source['uuid'])
        artwork = source.get('artwork_only', False)
        need(fp is not None and str(fp.GetReference()) == source['reference']
             and xy(fp.GetPosition()) == source['position_nm'] and angle(fp.GetOrientationDegrees()) == source['angle']
             and fp.GetLayer() == (pcbnew.B_Cu if artwork else pcbnew.F_Cu)
             and boolean(fp.IsFlipped()) is artwork
             and boolean(fp.IsLocked()) == source['locked'] and not list(fp.Zones()),
             'Native footprint identity/pose/lock/area differs')
        if tht:
            from . import engineering_metadata
            formatter = pcbnew.PCB_IO_KICAD_SEXPR()
            formatter.Format(fp)
            witness = engineering_metadata.compare(source.get('engineering_metadata'),
                formatter.GetStringOutput(True), fp.GetDuplicatePadNumbersAreJumpers())
            # The complete formatted footprint changes on a permitted translation.
            # Retain only invariant metadata details here: the existing worker
            # requires before/after pad/zone/metadata details to remain identical.
            witness.pop('formatted_footprint_sha256')
            try:
                count = len(fp.Points())
            except (AttributeError, TypeError) as exc:
                # PCB_POINT has no Python class in this pinned wrapper. If the
                # container is opaque too, the exact actual footprint formatter
                # above still witnesses every point identity/geometry/owner.
                witness['point_census_method'] = 'exact-footprint-formatter'
                witness['direct_point_count_unavailable'] = type(exc).__name__
            else:
                need(count == len(source['engineering_metadata']['points']),
                     'Native fixed point count differs')
                witness['point_census_method'] = 'Points-length-and-exact-footprint-formatter'
                witness['direct_point_count_unavailable'] = None
            witness['point_count'] = len(source['engineering_metadata']['points'])
            metadata_witnesses[source['uuid']] = witness
        if artwork:
            attributes = {'board_only': pcbnew.FP_BOARD_ONLY,
                          'exclude_from_pos_files': pcbnew.FP_EXCLUDE_FROM_POS_FILES,
                          'exclude_from_bom': pcbnew.FP_EXCLUDE_FROM_BOM}
            expected_attributes = 0
            for name in source['attributes']: expected_attributes |= attributes[name]
            need(contract.fixed_context_scope(scope) and source['side'] == 'back' and source['courtyard'] is None
                 and source['pads'] == [] and type(fp.GetAttributes()) is int
                 and fp.GetAttributes() == expected_attributes and not list(fp.Models()),
                 'Native back artwork physical content differs')
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
            if 'mirrored' in row:
                need(boolean(item.IsMirrored()) == row['mirrored'], 'Native back artwork property mirror differs')
        graphics(list(fp.GraphicalItems()), ([] if artwork else source['courtyard']['primitives'])
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
            if tht and not smd:
                drill_shape = pad.GetDrillShape()
                need(type(drill_shape) is int and drill_shape == pcbnew.PAD_DRILL_SHAPE_CIRCLE,
                     'Native circular PTH drill required')
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
    details = dict(native_pad_netcodes=netcodes, native_route_netcodes=route_netcodes, actual_native_areas=areas)
    if tht:
        details['engineering_metadata'] = metadata_witnesses
    return expected, details
