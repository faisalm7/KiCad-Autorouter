"""Boundary regressions only; real KiCad rendering is a separate native test."""
import json
import os
import copy
from pathlib import Path
import stat
import sys
import tempfile
import shutil
import unittest
from unittest.mock import patch
from xml.etree import ElementTree
from autorouter import handoff as h, review_view as view, pipeline as p, local_settings as ls


class SvgControls(unittest.TestCase):
    def test_workspace_shows_rectangular_board_context_and_real_part_anchor(self):
        from autorouter import sexpr
        from xml.etree import ElementTree

        board = sexpr.parse('''(kicad_pcb
            (gr_rect (start 4 5) (end 14 17) (layer "Edge.Cuts"))
            (footprint "part" (at 7 8 90) (property "Reference" "J&1"))
            (segment (start 7 8) (end 8 9) (width 0.3) (layer "F.Cu")))''')
        context = view._workspace_context(board)
        self.assertEqual(context, view.BoardDrawing((4, 5, 14, 17), ((7, 8, 'J&1'),)))
        changes = {'protected': p.routes(board)}
        diagrams, note = view.routing_diagrams(changes, ['F.Cu', 'B.Cu'], workspace=True, board_context=context)
        svg = ElementTree.fromstring(diagrams['F.Cu']['svg'])
        ns = {'svg': 'http://www.w3.org/2000/svg'}
        self.assertEqual(note, '')
        self.assertEqual(svg.find('svg:g/svg:rect', ns).get('width'), '10.0')
        self.assertEqual(svg.find('svg:text', ns).text, 'J&1')
        self.assertIn(view.WORKSPACE_COLORS['protected'], diagrams['F.Cu']['svg'])
        self.assertNotIn('<path', diagrams['B.Cu']['svg'])
        board.append(['gr_circle', ['layer', '"Edge.Cuts"']])
        self.assertIsNone(view._workspace_context(board))  # A cutout cannot be omitted.

    def test_four_straight_edges_give_exact_read_only_context_at_any_copper_count(self):
        from autorouter import placement_transform, sexpr

        board = sexpr.parse('''(kicad_pcb
            (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal))
            (gr_line (start 4 17) (end 14 17) (layer "Edge.Cuts"))
            (gr_line (start 14 5) (end 4 5) (layer "Edge.Cuts"))
            (gr_line (start 14 17) (end 14 5) (layer "Edge.Cuts"))
            (gr_line (start 4 5) (end 4 17) (layer "Edge.Cuts")))''')
        self.assertEqual(view._workspace_context(board), view.BoardDrawing((4, 5, 14, 17), ()))
        with self.assertRaisesRegex(ValueError, 'two canonical copper layers'):
            placement_transform.rectangle(board)
        missing_edge = board[:-1]
        substitute = sexpr.parse('(gr_line (start 4 5) (end 4 18) (layer "Edge.Cuts"))')
        self.assertIsNone(view._workspace_context(missing_edge + [substitute]))
        cut = sexpr.parse('(footprint "cutout" (fp_line (layer "Edge.Cuts")))')
        self.assertIsNone(view._workspace_context(board + [cut]))

    def test_curved_saved_outline_renders_the_chain_without_a_filled_area(self):
        from autorouter import sexpr
        from xml.etree import ElementTree

        board = sexpr.parse('''(kicad_pcb
            (gr_line (start 2 3) (end 10 3) (layer "Edge.Cuts"))
            (gr_arc (start 10 3) (mid 13 4) (end 14 7) (layer "Edge.Cuts"))
            (gr_line (start 14 7) (end 14 12) (layer "Edge.Cuts"))
            (gr_line (start 14 12) (end 2 12) (layer "Edge.Cuts"))
            (gr_line (start 2 12) (end 2 3) (layer "Edge.Cuts")))''')
        context = view._workspace_context(board)
        # The arc reaches beyond both endpoints. Keep those extrema in view.
        expected_bounds = (2, 6.5 - 12.5 ** 0.5, 10.5 + 12.5 ** 0.5, 12)
        for observed, expected in zip(context.bounds, expected_bounds):
            self.assertAlmostEqual(observed, expected)
        diagrams, _ = view.routing_diagrams({}, ['F.Cu'], workspace=True, board_context=context)
        svg = ElementTree.fromstring(diagrams['F.Cu']['svg'])
        paths = svg.findall('.//{*}path[@data-role="board-edge"]')
        self.assertEqual(len(paths), 5)
        self.assertEqual(sum(' A ' in item.get('d') for item in paths), 1)
        self.assertIsNone(svg.find('.//{*}rect'))
        self.assertIsNone(view._workspace_context(board[:-1]))
        self.assertIsNone(view._workspace_context(board + [board[-1]]))

    def test_workspace_distinguishes_protected_copper_and_refuses_tampered_copy(self):
        protected = '(segment (start 1 1) (end 2 2) (width .2) (layer "F.Cu") (net 1))'
        new = '(segment (start 2 2) (end 3 3) (width .2) (layer "B.Cu") (net 1))'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            before = root / 'before' / 'board.kicad_pcb'
            after = root / 'project' / before.name
            for path in (before, after): path.parent.mkdir()
            before.write_text(f'(kicad_pcb {protected} (zone (filled_polygon original)))')
            after.write_text(f'(kicad_pcb {protected} {new} (zone (filled_polygon final)))')
            review = dict(board=str(after), source_project_hashes={before.name: p.sha(before)},
                          candidate_sha256=p.sha(after), preview={'layers': ['F.Cu', 'B.Cu']})
            route = {'scope': 'partial_completion'}
            changes = view.workspace_changes(root, before, review, route)
            self.assertEqual(changes['counts'], {'added': 1, 'retained': 0, 'removed': 0, 'protected': 1})
            self.assertIn(view.WORKSPACE_COLORS['protected'], changes['diagrams']['F.Cu']['svg'])
            self.assertNotIn('zone', changes['diagrams']['F.Cu']['svg'])
            after.write_text(f'(kicad_pcb {new})')
            with self.assertRaisesRegex(p.Rejected, 'boards changed'):
                view.workspace_changes(root, before, review, route)
            review['candidate_sha256'] = p.sha(after)
            with self.assertRaisesRegex(p.Rejected, 'every protected'):
                view.workspace_changes(root, before, review, route)

    def test_saved_routing_context_bounds_the_copy_and_grants_no_picking(self):
        with tempfile.TemporaryDirectory() as tmp:
            board = Path(tmp).resolve() / 'board.kicad_pcb'
            board.write_text('''(kicad_pcb (layers (0 "F.Cu" signal) (2 "B.Cu" signal))
                (gr_rect (start 4 5) (end 14 17) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))
                (gr_circle (center 11 12) (end 12 12) (stroke (width 0.05) (type default))
                    (fill none) (layer "Edge.Cuts") (uuid "44ce912b-673a-42d4-913f-06fded0df9df"))
                (footprint "part" (at 7 8) (property "Reference" "J1")))''')
            inspection = dict(source=str(board), source_sha256=p.sha(board))
            scene = view.saved_board_front(inspection)
            self.assertIn('>J1</text>', scene['svg'])
            self.assertIn('cx="11.0" cy="12.0" r="1.0"', scene['svg'])
            self.assertIn('data-role="board-cutout"', scene['svg'])
            self.assertNotIn('transform', scene)  # Picking geometry belongs to validated placement.
            board.write_text('(kicad_pcb)')
            with self.assertRaisesRegex(p.Rejected, 'changed before drawing'):
                view.saved_board_front(inspection)

    def test_route_record_diff_ignores_fill_and_preserves_multiplicity(self):
        from autorouter import sexpr
        via = '(via (at 5 5) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net 1))'
        old = '(segment (start 1 1) (end 2 2) (width .2) (layer "F.Cu") (net 1))'
        new = '(segment (start 2 2) (end 3 3) (width .2) (layer "B.Cu") (net 1))'
        before = sexpr.parse(f'(kicad_pcb {via} {old} {old} (zone (filled_polygon old)))')
        after = sexpr.parse(f'(kicad_pcb {via} {old} {new} (zone (filled_polygon different)))')
        result = view.route_changes(before, after)
        self.assertEqual({key:len(rows) for key, rows in result.items()}, {'retained':2,'added':1,'removed':1})
        layers = ['F.Cu','In1.Cu','In2.Cu','B.Cu']
        diagrams, note = view.routing_diagrams(result, layers)
        self.assertEqual(set(diagrams), set(layers)); self.assertEqual(note, '')
        self.assertTrue(all('<circle' in plot and 'zone' not in plot for plot in diagrams.values()))
        self.assertIn('<g class="added"><path', diagrams['B.Cu'])
        self.assertIn('<g class="removed"><path', diagrams['F.Cu'])

    def test_inheritance_requires_each_exact_source_occurrence(self):
        warning = {'severity':'warning','type':'lib_footprint_issues','description':'Missing library'}
        excluded = dict(warning, excluded=True)
        source = {'findings':[warning]}
        final = {'findings':[warning, warning, dict(warning, description='Different'), excluded,
                             dict(warning, severity='exclusion')]}
        groups = view.finding_groups(final, source)
        self.assertEqual({key:len(rows) for key, rows in groups.items()}, {
            ('Already in the saved input','Footprint library issues'):1,
            ('Source match unconfirmed','Footprint library issues'):2,
            ('Excluded by project settings','Footprint library issues'):2,
        })

    def test_only_observed_kicad_doctype_admitted_and_removed(self):
        header = b'<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" \n "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">'
        drawing = b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 1"/></svg>'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'plot.svg'; path.write_bytes(header + drawing)
            self.assertEqual(view.svg_bytes(path), header + drawing)
            self.assertEqual(view.display_svg(view.svg_bytes(path)), drawing)
            for bad in (header.replace(b'www.w3.org', b'example.com'), header + header,
                        header.replace(b'>', b' [<!ENTITY x "bad">]>'), b'<!DOCTYPE svg SYSTEM "file:///tmp/no">'):
                path.write_bytes(bad + drawing)
                with self.subTest(header=bad), self.assertRaises(p.Rejected): view.svg_bytes(path)

    def test_processing_instructions_rejected_except_initial_xml_declaration(self):
        drawing = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'plot.svg'
            path.write_bytes(b'<?xml version="1.0"?>' + drawing)
            self.assertEqual(view.svg_bytes(path), path.read_bytes())
            for instruction in (b'<?xml-stylesheet href="https://example.com/a.css"?>', b'<?unsafe value?>'):
                path.write_bytes(instruction + drawing)
                with self.subTest(instruction=instruction), self.assertRaises(p.Rejected): view.svg_bytes(path)

    def test_written_display_and_html_must_match_intended_bytes(self):
        original = Path.write_bytes
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('display.svg', 'preview.html'):
                path = Path(tmp).resolve() / name
                def mutate(target, raw):
                    return original(target, b'replaced after write')
                with self.subTest(name=name), patch.object(Path, 'write_bytes', mutate), self.assertRaises(p.Rejected):
                    view.write_bound(path, b'intended content')

    def test_linked_and_active_content_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'plot.svg'
            for inner in ('<script/>', '<foreignObject/>', '<image href="https://example.com/a"/>',
                          '<set attributeName="opacity" to="0"/>', '<animate/>',
                          '<path onload="alert(1)"/>', '<path fill="url(https://example.com/a)"/>'):
                path.write_text('<svg xmlns="http://www.w3.org/2000/svg">' + inner + '</svg>')
                with self.subTest(inner=inner), self.assertRaises(p.Rejected): view.svg_bytes(path)
            path.write_text('<!DOCTYPE svg [<!ENTITY x "test">]><svg xmlns="http://www.w3.org/2000/svg"/>')
            with self.assertRaises(p.Rejected): view.svg_bytes(path)
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 1"/></svg>')
            self.assertEqual(view.svg_bytes(path), path.read_bytes())


class WorkspaceFindings(unittest.TestCase):
    smd = 'be1bff94-c211-49d1-ab60-a0960bc4af00'
    through = 'deae5183-4901-4fbd-b6ad-e1d01e391527'
    footprint = '35e45d28-a006-4f09-9cdd-4f21605d1497'
    track = '0d32f8a6-05ba-4bc7-abc0-3f3b76869646'
    layers = ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu']

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.before = self.root / 'before' / 'board.kicad_pcb'
        self.after = self.root / 'project' / self.before.name
        for path in (self.before, self.after):
            path.parent.mkdir()

    def render(self, findings=(), *, extra='', removal='', stale=False):
        board = f'''(layers (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal))
            (gr_rect (start 4 5) (end 14 17) (layer "Edge.Cuts"))
            (footprint "part" (layer "F.Cu") (at 7 8 90) (uuid "{self.footprint}")
                (property "Reference" "J&1")
                (fp_rect (start -1 -1) (end 1 1) (stroke (width .05) (type default)) (fill none)
                    (layer "F.CrtYd") (uuid "1b28a367-0662-4112-a2e1-d6e76f8fcd5e"))
                (pad "1" smd roundrect (at 1 2 90) (size 1 .8) (roundrect_rratio .2)
                    (layers "F.Cu" "F.Paste" "F.Mask") (uuid "{self.smd}") (net "A"))
                (pad "2" thru_hole circle (at 0 0) (size 1.7 1.7) (drill 1)
                    (layers "*.Cu" "*.Mask") (uuid "{self.through}") {removal}))
            (segment (start 10 7) (end 10 9) (width .2) (layer "F.Cu") (net "A") (uuid "{self.track}"))
            {extra}'''
        self.before.write_text(f'(kicad_pcb {board})')
        self.after.write_text(f'(kicad_pcb {board} (segment (start 7 8) (end 8 9) (width .2) (layer "B.Cu") (net "B")))')
        candidate = p.sha(self.after)
        review = dict(board=str(self.after), source_project_hashes={self.before.name: p.sha(self.before)},
                      candidate_sha256=candidate, verified_candidate_sha256=candidate, preview={'layers': self.layers})
        route = dict(scope='partial_completion', candidate_sha256='0' * 64 if stale else candidate,
                     native={'findings': list(findings)})
        return view.workspace_changes(self.root, self.before, review, route)

    def test_passive_pad_shapes_use_captured_pose_and_layer(self):
        render = self.render()
        for layer in self.layers:
            with self.subTest(layer=layer):
                scene = render['diagrams'][layer]
                svg = ElementTree.fromstring(scene['svg'])
                outer = svg.find('.//{*}circle[@data-role="pad-shape"]')
                hole = svg.find('.//{*}circle[@data-role="drill"]')
                self.assertEqual((outer.get('cx'), outer.get('cy'), outer.get('r')), ('7.0', '8.0', '0.85'))
                self.assertEqual((hole.get('cx'), hole.get('cy'), hole.get('r')), ('7.0', '8.0', '0.5'))
                rectangular = svg.find('.//{*}rect[@data-role="pad-shape"]')
                if layer == 'F.Cu':
                    self.assertEqual(rectangular.get('transform'), 'rotate(-90 9.0 7.0)')
                    self.assertAlmostEqual(float(rectangular.get('rx')), .16)
                    self.assertIsNotNone(svg.find('.//{*}rect[@data-role="courtyard"]'))
                    item = next(item for item in scene['items'] if item['id'] == self.smd)
                    self.assertEqual((item['kind'], item['label'], item['net']), ('pad', 'J&1 pad 1', 'A'))
                else:
                    self.assertIsNone(rectangular)
                    self.assertIsNone(svg.find('.//{*}rect[@data-role="courtyard"]'))
                self.assertEqual(svg.find('{*}text').text, 'J&1')
                self.assertNotIn('components', scene)
        self.assertEqual(render['counts'], {'retained': 0, 'added': 1, 'removed': 0, 'protected': 1})
        self.assertIn('pad shapes and zone fill', render['context_note'])

    def test_unique_current_finding_uses_board_coordinates_and_preserves_the_base(self):
        render = self.render([{'description': 'Layout check', 'items': [
            {'uuid': self.smd, 'pos': {'x': 999, 'y': float('nan')}}, {'uuid': self.track}]}])
        finding, = render['findings']
        self.assertEqual((finding['index'], finding['label'], finding['layers']), (0, '1. Layout check', ('F.Cu',)))
        scene = view.finding_scene(render, 'F.Cu', 0)
        base = render['diagrams']['F.Cu']
        self.assertEqual(scene['size'], base['size'])
        self.assertEqual(scene['items'], base['items'])
        self.assertNotIn('finding-location', base['svg'])
        svg = ElementTree.fromstring(scene['svg'])
        markers = svg.findall('.//{*}circle[@data-role="finding-location"]')
        scale, tx, ty = base['mm_to_svg']
        self.assertEqual({(float(row.get('cx')), float(row.get('cy'))) for row in markers},
                         {(x * scale + tx, 7 * scale + ty) for x in (9, 10)})
        self.assertEqual(view.finding_scene(render, 'B.Cu', 0), render['diagrams']['B.Cu'])
        self.assertEqual(view.finding_scene(render, 'F.Cu'), base)

    def test_unresolved_duplicate_and_excess_findings_retain_safe_fallback(self):
        unknown = 'c662d038-4a83-4624-951d-97dc8fe2edf2'
        duplicate = f'(gr_text "Another object" (uuid "{self.smd}") (at 6 8) (layer "F.SilkS"))'
        rows = [{'description': 'Ambiguous', 'items': [{'uuid': self.smd}]},
                {'description': 'Unresolved\x00 item', 'items': [{'uuid': unknown}]},
                {'description': 'Over selector bound', 'items': [{'uuid': self.footprint}]}]
        with patch.object(view, 'FINDING_LIMIT', 2):
            render = self.render(rows, extra=duplicate)
        self.assertIn('pad-shape', render['diagrams']['F.Cu']['svg'])
        self.assertEqual(render['findings_omitted'], 1)
        self.assertEqual([row['layers'] for row in render['findings']], [(), ()])
        self.assertEqual(render['findings'][1]['label'], '2. Unresolved item')
        self.assertNotIn('finding-location', view.finding_scene(render, 'F.Cu', 0)['svg'])

    def test_pad_population_or_uncertain_layer_presence_keeps_the_copper_diff(self):
        finding = {'description': 'Through-hole item', 'items': [{'uuid': self.through}]}
        with patch.object(view, 'PAD_MARKER_LIMIT', 1):
            capped = self.render([finding])
        removed = self.render([finding], removal='(remove_unused_layers yes)')
        for render in (capped, removed):
            self.assertIn('Some pad centres are omitted', render['context_note'])
            self.assertNotIn('pad-centre', render['diagrams']['B.Cu']['svg'])
            self.assertIn(view.WORKSPACE_COLORS['added'], render['diagrams']['B.Cu']['svg'])
            self.assertEqual(render['findings'][0]['layers'], ())

    def test_stale_candidate_cannot_supply_finding_anchors(self):
        with self.assertRaisesRegex(p.Rejected, 'candidate differs from the checked routing receipt'):
            self.render([{'items': [{'uuid': self.footprint}]}], stale=True)

    def test_saved_layer_scene_binds_bytes_and_identifies_saved_copper(self):
        self.render()
        inspection = {'source': str(self.before), 'source_sha256': p.sha(self.before)}
        saved = view.saved_workspace(inspection)
        self.assertEqual(set(saved['diagrams']), set(self.layers))
        self.assertIsNone(saved['counts'])
        self.assertEqual(saved['findings'], ())
        front = saved['diagrams']['F.Cu']
        self.assertEqual(view.saved_board_front(inspection), front)
        item = next(item for item in front['items'] if item['id'] == self.track)
        self.assertEqual(item['net'], 'A')
        self.assertIn('Saved copper', item['detail'])
        self.before.write_text('(kicad_pcb)')
        with self.assertRaisesRegex(p.Rejected, 'changed before drawing'):
            view.saved_workspace(inspection)

    def test_pick_pad_at_route_endpoint_and_track_away_from_pad(self):
        track = 'e8a84ef7-7a70-48b4-b3ba-690f9ba981b9'
        extra = (f'(segment (start 8 7) (end 9 7) (width .18) (layer "F.Cu") (net "A") (uuid "{track}"))'
                 '(segment (start 8 7.2) (end 9 7.2) (width .15) (layer "F.Cu") (net "B"))')
        scene = self.render(extra=extra)['diagrams']['F.Cu']
        scale, tx, ty = scene['mm_to_svg']
        self.assertEqual(view.pick_item(scene, (9 * scale + tx, 7 * scale + ty), 4), self.smd)
        self.assertEqual(view.pick_item(scene, (8.25 * scale + tx, 7 * scale + ty), 8), track)
        self.assertIsNone(view.pick_item(scene, (float('nan'), 0), 4))
        self.assertIsNone(view.pick_item(scene, (0, 0), 4))
        marked = view.inspect_item(scene, self.footprint)
        self.assertIn('inspected-item', marked['svg'])
        self.assertEqual(marked['items'], scene['items'])
        self.assertNotIn('inspected-item', scene['svg'])
        self.assertIs(view.inspect_item(scene, 'not-current'), scene)
        net = view.inspect_net(scene, 'A')
        self.assertIn(f'M {8 * scale + tx} {7 * scale + ty} L {9 * scale + tx} {7 * scale + ty}',
                      net['svg'].split('data-role="inspected-net-item"', 1)[1])
        self.assertEqual(net['items'], scene['items'])
        self.assertIs(view.inspect_net(scene, 'a'), scene)

    def test_coincident_pads_are_ambiguous_and_oval_pads_are_marked(self):
        oval = '6eb967ef-066c-4f4f-883c-6869113a5e8e'
        extra = f'''(footprint "overlap" (at 9 7) (layer "F.Cu") (property "Reference" "X1")
                     (pad "1" thru_hole circle (at 0 0) (size .75 .75) (drill .3)
                          (layers "*.Cu" "*.Mask") (uuid "a8e16fad-c6d9-4bed-8bfc-0dc3db112091"))
                     (pad "2" thru_hole oval (at 0 2) (size 1 .75) (drill .3)
                          (layers "*.Cu" "*.Mask") (uuid "{oval}")))'''
        render = self.render(extra=extra)
        front = render['diagrams']['F.Cu']
        centre = next(item['point'] for item in front['items'] if item['id'] == self.smd)
        self.assertIsNone(view.pick_item(front, centre, 4))
        for layer in self.layers:
            scene = render['diagrams'][layer]
            item = next(item for item in scene['items'] if item['id'] == oval)
            self.assertIn('Shape omitted', item['detail'])
            self.assertIn('data-role="pad-centre"', scene['svg'])
        self.assertIn('centre marker', render['context_note'])


class PreviewTransaction(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.source = self.root / 'source'; self.source.mkdir()
        self.run = self.root / 'run'; self.run.mkdir(); self.candidate = self.run / 'candidate'; self.candidate.mkdir()
        for directory, content in [(self.source, '(kicad_pcb)'), (self.candidate, '(kicad_pcb (candidate))')]:
            (directory / 'board.kicad_pcb').write_text(content); (directory / 'board.kicad_pro').write_text('{}')
        self.receipt = self.run / 'result.json'
        self.receipt.write_text(json.dumps({'schema': 1, 'source': str(self.source / 'board.kicad_pcb'),
            'candidate': str(self.candidate / 'board.kicad_pcb'), 'candidate_sha256': p.sha(self.candidate / 'board.kicad_pcb')}))
        self.check = patch.object(h, 'check_result', return_value={'current': True, 'applied': False,
            'candidate': str(self.candidate / 'board.kicad_pcb'), 'candidate_sha256': p.sha(self.candidate / 'board.kicad_pcb')}).start()
        self.addCleanup(patch.stopall)

    def fake_render(self, out, source, candidate, report, remaining, material):
        self.assertEqual(source.read_bytes(), (self.source / source.name).read_bytes())
        self.assertEqual(candidate.read_bytes(), (self.candidate / candidate.name).read_bytes())
        (out / 'preview.html').write_text('controlled renderer, not native proof')
        material()
        return {'plotter_sha256': p.sha(h.c.CLI), 'files': {'preview.html': p.sha(out / 'preview.html')}}

    def test_render_preserves_both_projects(self):
        out = self.root / 'review'
        with patch.object(view, 'render', side_effect=self.fake_render): result = h.review_copy(self.receipt, out, render=True)
        self.assertEqual(result['status'], 'ready_for_manual_review')
        self.assertTrue((out / 'preview.html').is_file())
        self.assertEqual(result['source_project_hashes'], h.pc.inventory(out / 'before'))

    def test_late_plot_or_original_copy_mutation_invalidates_html(self):
        for name in ('preview.html', 'before/board.kicad_pcb'):
            out = self.root / name.replace('/', '-')
            saved = h.save_json
            def mutate(path, value):
                saved(path, value)
                if path.name == 'review.json' and value['status'] == 'ready_for_manual_review':
                    (out / name).write_text('late change')
            with self.subTest(name=name), patch.object(view, 'render', side_effect=self.fake_render), patch.object(h, 'save_json', side_effect=mutate):
                with self.assertRaises(p.Rejected): h.review_copy(self.receipt, out, render=True)
            self.assertFalse((out / 'preview.html').exists())
            self.assertEqual(json.loads((out / 'review.json').read_text())['status'], 'rejected')

    def test_plot_failure_keeps_no_ready_html(self):
        out = self.root / 'failed'
        def fail(*args):
            self.fake_render(*args); raise p.Rejected('plot failed')
        with patch.object(view, 'render', side_effect=fail), self.assertRaises(p.Rejected): h.review_copy(self.receipt, out, render=True)
        self.assertFalse((out / 'preview.html').exists())
        self.assertEqual(json.loads((out / 'review.json').read_text())['status'], 'rejected')

    def test_late_added_plot_input_rule_invalidates_ready_page(self):
        out = self.root / 'added-rule'; saved = h.save_json
        def render(*args):
            result = self.fake_render(*args)
            directory = out / 'plot-input'; directory.mkdir()
            (directory / 'board.kicad_pcb').write_text('captured input')
            result['input_trees'] = {'plot-input': h.pc.inventory(directory)}
            return result
        def publish(path, value):
            saved(path, value)
            if value['status'] == 'ready_for_manual_review':
                (out / 'plot-input/extra.kicad_dru').write_text('(version 1)')
        with patch.object(view, 'render', side_effect=render), patch.object(h, 'save_json', side_effect=publish):
            with self.assertRaises(p.Rejected): h.review_copy(self.receipt, out, render=True)
        self.assertFalse((out / 'preview.html').exists())
        self.assertEqual(json.loads((out / 'review.json').read_text())['status'], 'rejected')


class PlotCopyControls(unittest.TestCase):
    def projects(self, root, *, old_prl=False):
        source = root / 'source'; source.mkdir()
        candidate = root / 'candidate'; candidate.mkdir()
        out = root / 'review'; out.mkdir()
        tree = '(kicad_pcb (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))'
        for directory in (source, candidate):
            (directory / 'board.kicad_pcb').write_text(tree)
            (directory / 'board.kicad_pro').write_text('{}')
            if old_prl: (directory / 'board.kicad_prl').write_bytes(b'{"old_schema":"retain these bytes"}\n')
        tool = root / 'tool'; tool.write_text('authored plotter placeholder, never executed')
        return source, candidate, out, tool

    def plot_worker(self, source, candidate, operation, calls, *, cleanup=True):
        # Only the process seam is authored: real FloorJob, copy and OS guard run.
        def run(argv, *, cwd, log, timeout, env):
            calls.append(argv); board = Path(argv[-1])
            self.assertNotIn(board.parent, (source, candidate))
            self.assertIn(Path(cwd), board.parents)
            state = operation(board, Path(cwd), len(calls)) or ('success', 0)
            target = Path(argv[argv.index('--output') + 1])
            target.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
            Path(log).write_text('authored process seam; no Native plot executed\n')
            return {'argv': argv, 'cwd': str(cwd), 'log': str(log),
                    'status': state[0], 'exit_code': state[1], 'cleanup_complete': cleanup,
                    'wall_seconds': 0, 'cpu_seconds': 0, 'monitor_cpu_seconds': 0,
                    'log_bytes': Path(log).stat().st_size, 'log_truncated': False}
        return run

    def render(self, out, source, candidate, tool, worker, report=None):
        pin = {'kicad_cli': {'path': str(tool), 'sha256': p.sha(tool), 'bytes':tool.stat().st_size}}
        with patch.object(view.c, 'CLI', tool), patch.object(p,'selected_tool_pins',return_value=pin) as selected,patch.object(p, 'run', side_effect=worker):
            result=view.render(out, source / 'board.kicad_pcb', candidate / 'board.kicad_pcb',
                               {} if report is None else report, lambda: 30, lambda: None)
            selected.assert_called_once_with()
            return result

    def test_browser_review_retains_actionable_findings_as_inert_text(self):
        from html import unescape
        with tempfile.TemporaryDirectory() as tmp:
            source,candidate,out,tool=self.projects(Path(tmp).resolve());calls=[]
            finding={'severity':'warning','type':'footprint_symbol_field_mismatch',
                'description':'Datasheet differs <script>alert(1)</script>',
                'items':[{'description':'Footprint J1','pos':{'x':12.0,'y':10.0},'uuid':'original-item'}]}
            native={'opens':0,'blocking':0,'warnings':1,'exclusions':0,
                    'findings':[finding],'ignored_checks':[{'key':'retained-check','description':'Ignored check'}]}
            self.render(out,source,candidate,tool,
                self.plot_worker(source,candidate,lambda *args:None,calls),{'native':native})
            page=(out/'preview.html').read_text()
            self.assertNotIn('<script>',page)
            details=json.loads(unescape(page.split('<pre>',1)[1].split('</pre>',1)[0]))
            self.assertEqual(details['findings'],[finding])
            self.assertEqual(details['saved_native_findings']['warnings'],1)
            self.assertEqual(details['ignored_checks'],native['ignored_checks'])
            self.assertIn('<dt>Warnings</dt><dd>1</dd>', page)
            self.assertIn('<dt>Ignored checks</dt><dd>1</dd>', page)
            self.assertIn('<dt>Candidate track length</dt><dd>Not recorded</dd>', page)
            self.assertNotIn('<details open', page)
            self.assertLess(page.index('Saved routing-check summary'), page.index('<img '))
            self.assertLess(page.rindex('<img '), page.index('<details id="saved-details">'))
            self.assertIn('not electrical or manufacturing approval', page)
            self.assertIn('plotting does not refill zones or perform DRC', page)
            self.assertIn('Footprint and schematic fields differ', page)
            self.assertIn('Datasheet differs &lt;script&gt;', page)
            self.assertIn('Source match unconfirmed', page)
            self.assertIn('Full KiCad plots with pads and zone fill', page)

    def test_browser_summary_uses_recorded_metrics_and_keeps_missing_counts_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,candidate,out,tool=self.projects(Path(tmp).resolve());calls=[]
            report={'final_drc':{'opens':0,'blocking':0,'warnings':2,'exclusions':1,
                                'findings':[]},
                    'metrics':{'track_length_mm':43.242640687119284,'vias':3}}
            self.render(out,source,candidate,tool,
                self.plot_worker(source,candidate,lambda *args:None,calls),report)
            page=(out/'preview.html').read_text()
            for text in ('<dt>Open connections</dt><dd>0</dd>', '<dt>Warnings</dt><dd>2</dd>',
                         '<dt>Exclusions</dt><dd>1</dd>', '<dt>Ignored checks</dt><dd>Not recorded</dd>',
                         '<dt>Candidate track length</dt><dd>43.242641 mm</dd>',
                         '<dt>Candidate vias</dt><dd>3</dd>'):
                self.assertIn(text,page)
            self.assertIn('See original receipt',page)

    def test_selected7_plot_pin_is_used_and_mixed_path_or_size_refuses(self):
        for mismatch in (None,'old_default_path','bytes'):
            with self.subTest(mismatch=mismatch),tempfile.TemporaryDirectory() as tmp:
                source,candidate,out,tool=self.projects(Path(tmp).resolve());calls=[]
                pin={'path':str(tool),'sha256':p.sha(tool),'bytes':tool.stat().st_size}
                if mismatch=='old_default_path':pin['path']=str(tool.with_name('old-default'))
                if mismatch=='bytes':pin['bytes']+=1
                worker=self.plot_worker(source,candidate,lambda *args:None,calls)
                with patch.object(view.c,'NATIVE_VERSION','10.0.7'),patch.object(view.c,'CLI',tool),patch.object(p,'selected_tool_pins',return_value={'kicad_cli':pin}) as selected,patch.object(p,'run',side_effect=worker):
                    if mismatch:
                        with self.assertRaisesRegex(p.Rejected,'pinned KiCad plotter changed'):
                            view.render(out,source/'board.kicad_pcb',candidate/'board.kicad_pcb',{},lambda:30,lambda:None)
                        self.assertEqual(calls,[])
                    else:
                        view.render(out,source/'board.kicad_pcb',candidate/'board.kicad_pcb',{},lambda:30,lambda:None)
                        self.assertEqual(len(calls),4)
                    selected.assert_called_once_with()

    def test_normal_preview_reuses_exact_plot_proofs_and_rejects_missing_population(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,candidate,out,tool=self.projects(Path(tmp).resolve(),old_prl=True)
            shutil.copytree(source,out/'before');shutil.copytree(candidate,out/'project')
            source,candidate=out/'before',out/'project';calls=[]
            preview=self.render(out,source,candidate,tool,self.plot_worker(source,candidate,lambda *args:None,calls))
            pin={'path':str(tool),'sha256':p.sha(tool),'bytes':tool.stat().st_size}
            with patch.object(view.c,'CLI',tool),patch.object(p,'selected_tool_pins',return_value={'kicad_cli':pin}):
                self.assertEqual(len(view.check_native_preview(out,preview)),4)
                missing=copy.deepcopy(preview);missing['files'].pop('plot-work/after-B.Cu-process.json')
                with self.assertRaises(p.Rejected):view.check_native_preview(out,missing)
                tool.write_text('changed plotter')
                with self.assertRaises(p.Rejected):view.check_native_preview(out,preview)

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac flags required')
    def test_normal_preview_final_tool_read_cannot_hide_earlier_prl_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,candidate,out,tool=self.projects(Path(tmp).resolve(),old_prl=True)
            shutil.copytree(source,out/'before');shutil.copytree(candidate,out/'project')
            source,candidate=out/'before',out/'project';calls=[]
            preview=self.render(out,source,candidate,tool,self.plot_worker(source,candidate,lambda *args:None,calls))
            pin={'path':str(tool),'sha256':p.sha(tool),'bytes':tool.stat().st_size}
            prl=out/'plot-work/before-F.Cu-input/board.kicad_prl';original=p.sha;reads=[]
            def late_hash(path):
                result=original(path)
                if Path(path)==tool:
                    reads.append(path)
                    if len(reads)==2:os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
                return result
            try:
                with patch.object(view.c,'CLI',tool),patch.object(p,'selected_tool_pins',return_value={'kicad_cli':pin}), \
                        patch.object(p,'sha',side_effect=late_hash),self.assertRaises(p.Rejected):
                    view.check_native_preview(out,preview)
                self.assertEqual(len(reads),2)
            finally:
                if prl.exists() and prl.stat().st_flags:os.chflags(prl,0,follow_symlinks=False)

    def test_native_added_prl_is_confined_and_original_changes_reject(self):
        for mutation in ('added_prl', 'changed_board', 'changed_existing_prl', 'late_added_rule'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                source, candidate, out, tool = self.projects(root, old_prl=mutation == 'changed_existing_prl')
                before = [h.pc.inventory(source), h.pc.inventory(candidate)]
                calls = []
                def operation(board, cwd, count):
                    if mutation == 'changed_board': board.write_text('altered board')
                    else:
                        try: board.with_suffix('.kicad_prl').write_text('{"generated":true}')
                        except PermissionError: return ('nonzero_exit', 1)
                    if mutation == 'late_added_rule' and count == 2:
                        (cwd / 'before-F.Cu-input/extra.kicad_dru').write_text('(version 1)')
                worker = self.plot_worker(source, candidate, operation, calls)
                if mutation == 'added_prl':
                    result = self.render(out, source, candidate, tool, worker)
                    self.assertEqual(len(calls), 4)
                    self.assertTrue(all(p.sha(out / name) == digest for name, digest in result['files'].items()))
                else:
                    with self.assertRaises(p.Rejected): self.render(out, source, candidate, tool, worker)
                self.assertEqual([h.pc.inventory(source), h.pc.inventory(candidate)], before)

    @unittest.skipUnless(sys.platform == 'darwin' and hasattr(os, 'chflags'), 'actual Mac flags required')
    def test_plot_workers_protect_existing_prl_and_bind_restored_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, candidate, out, tool = self.projects(Path(tmp).resolve(), old_prl=True)
            before = [h.pc.inventory(source), h.pc.inventory(candidate)]; calls = []
            def operation(board, cwd, count):
                copied = board.with_suffix('.kicad_prl')
                self.assertEqual(copied.stat().st_flags, stat.UF_IMMUTABLE)
                with self.assertRaises(PermissionError): copied.write_bytes(b'forbidden plot rewrite')
                self.assertEqual([d.joinpath(copied.name).stat().st_flags for d in (source, candidate)], [0, 0])
            result = self.render(out, source, candidate, tool, self.plot_worker(source, candidate, operation, calls))
            self.assertEqual(len(calls), 4)
            self.assertFalse(result['native_validation_performed']); self.assertFalse(result['zone_refill_performed'])
            for step in result['steps']:
                process = view.f.read_json(out / 'plot-work' / (step['name'] + '-process.json'))
                binding = view.f.read_json(out / 'plot-work' / (step['name'] + '-input-binding.json'))
                ls.check_event(out / 'plot-work', binding, process)
                event = process['local_settings_protection']; copied = Path(event['path'])
                self.assertTrue(event['present']); self.assertTrue(event['flags_restored']); self.assertTrue(event['bytes_unchanged'])
                self.assertEqual(copied.stat().st_flags, 0)
                self.assertEqual(p.sha(copied), binding['before'][copied.name])
            self.assertEqual([h.pc.inventory(source), h.pc.inventory(candidate)], before)

    @unittest.skipUnless(sys.platform == 'darwin' and hasattr(os, 'chflags'), 'actual Mac flags required')
    def test_plot_unknown_cleanup_refuses_preview_and_keeps_owned_prl_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, candidate, out, tool = self.projects(Path(tmp).resolve(), old_prl=True)
            before = [h.pc.inventory(source), h.pc.inventory(candidate)]; calls = []
            copied = out / 'plot-work/before-F.Cu-input/board.kicad_prl'
            def operation(board, cwd, count):
                self.assertEqual(board.with_suffix('.kicad_prl').stat().st_flags, stat.UF_IMMUTABLE)
                return ('timeout', -15)
            try:
                worker = self.plot_worker(source, candidate, operation, calls, cleanup=False)
                with self.assertRaisesRegex(p.Rejected, 'cleanup not confirmed'):
                    self.render(out, source, candidate, tool, worker)
                process = view.f.read_json(out / 'plot-work/before-F.Cu-process.json')
                event = process['local_settings_protection']
                self.assertFalse(process['cleanup_complete']); self.assertFalse(event['flags_restored'])
                self.assertIn('timeout exit=-15', event['native_error'])
                self.assertIn('cleanup not confirmed', event['guard_error'])
                self.assertEqual(copied.stat().st_flags, stat.UF_IMMUTABLE)
                self.assertEqual(p.sha(copied), before[0][copied.name])
                self.assertFalse((out / 'preview.html').exists()); self.assertEqual(len(calls), 1)
                self.assertEqual([h.pc.inventory(source), h.pc.inventory(candidate)], before)
                self.assertEqual([d.joinpath(copied.name).stat().st_flags for d in (source, candidate)], [0, 0])
            finally:
                # Only this authored owned test copy is released after refusal.
                if copied.exists() and copied.stat().st_flags: os.chflags(copied, 0, follow_symlinks=False)
