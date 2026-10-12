"""Boundary regressions only; real KiCad rendering is a separate native test."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import handoff as h, review_view as view, pipeline as p


class SvgControls(unittest.TestCase):
    def test_linked_and_active_content_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / 'plot.svg'
            for inner in ('<script/>', '<foreignObject/>', '<image href="https://example.com/a"/>',
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
