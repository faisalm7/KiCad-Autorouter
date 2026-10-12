"""Boundary regressions only; real KiCad rendering is a separate native test."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import handoff as h, review_view as view, pipeline as p


class SvgControls(unittest.TestCase):
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
    def test_native_added_prl_is_confined_and_original_changes_reject(self):
        for mutation in ('added_prl', 'changed_board', 'changed_existing_prl', 'late_added_rule'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); source = root / 'source'; source.mkdir()
                candidate = root / 'candidate'; candidate.mkdir(); out = root / 'review'; out.mkdir()
                tree = '(kicad_pcb (layers (0 "F.Cu" signal) (31 "B.Cu" signal)))'
                for directory in (source, candidate):
                    (directory / 'board.kicad_pcb').write_text(tree)
                    (directory / 'board.kicad_pro').write_text('{}')
                    if mutation == 'changed_existing_prl': (directory / 'board.kicad_prl').write_text('{"old":true}')
                before = [h.pc.inventory(source), h.pc.inventory(candidate)]
                tool = root / 'tool'; tool.write_text('fake plotter')
                calls = []
                class Job:
                    def __init__(self, path, *_):
                        self.out = path; path.mkdir(); self.steps = []
                    def step(self, name, argv):
                        calls.append(argv); board = Path(argv[-1])
                        assert board.parent not in (source, candidate)
                        target = Path(argv[argv.index('--output') + 1])
                        target.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
                        if mutation == 'changed_board': board.write_text('altered board')
                        else: board.with_suffix('.kicad_prl').write_text('{"generated":true}')
                        (self.out / (name + '.log')).write_text('controlled fake plot')
                        (self.out / (name + '-process.json')).write_text('{}')
                        if mutation == 'late_added_rule' and len(calls) == 2:
                            (self.out / 'before-F.Cu-input/extra.kicad_dru').write_text('(version 1)')
                pin = {'tools': {'kicad_cli': {'path': str(tool), 'sha256': p.sha(tool)}}}
                with patch.object(view.c, 'CLI', tool), patch.object(view.f, 'read_json', return_value=pin), patch.object(view.f, 'FloorJob', Job):
                    if mutation == 'added_prl':
                        result = view.render(out, source / 'board.kicad_pcb', candidate / 'board.kicad_pcb', {}, lambda: 30, lambda: None)
                        self.assertEqual(len(calls), 4)
                        self.assertTrue(all(p.sha(out / name) == digest for name, digest in result['files'].items()))
                    else:
                        with self.assertRaises(p.Rejected):
                            view.render(out, source / 'board.kicad_pcb', candidate / 'board.kicad_pcb', {}, lambda: 30, lambda: None)
                self.assertEqual([h.pc.inventory(source), h.pc.inventory(candidate)], before)
