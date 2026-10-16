"""Support rejection after actual native keepout controls went undetected."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from autorouter import pipeline as p, sexpr as sx

FLAGS=('tracks','vias','pads','copperpour','footprints')


def zone():
    return ['zone',['keepout',*[[flag,'allowed'] for flag in FLAGS]],
            ['placement',['enabled','yes'],['sheetname','"/Diagnostic/"']]]


class RuleAreaScope(unittest.TestCase):
    def test_every_prohibition_blocks_board_and_footprint_areas(self):
        for parent in ('board','footprint'):
            for flag in FLAGS:
                with self.subTest(parent=parent,flag=flag):
                    area=zone();sx.one(sx.one(area,'keepout'),flag)[1]='not_allowed'
                    tree=['kicad_pcb',area if parent=='board' else ['footprint','"owned"',area]]
                    with self.assertRaisesRegex(p.Rejected,'rule-area restrictions'):
                        p.check_rule_area_support(tree)

    def test_missing_duplicate_unknown_or_malformed_flags_block(self):
        base=zone();bad=[]
        missing=copy.deepcopy(base);sx.one(missing,'keepout').pop();bad.append(missing)
        duplicate=copy.deepcopy(base);sx.one(duplicate,'keepout')[-1]=['tracks','allowed'];bad.append(duplicate)
        unknown=copy.deepcopy(base);sx.one(unknown,'keepout')[-1]=['future','allowed'];bad.append(unknown)
        malformed=copy.deepcopy(base);sx.one(malformed,'keepout')[-1]=['footprints','allowed','extra'];bad.append(malformed)
        bad.append(['zone',sx.one(base,'placement')])
        bad.append(['zone',['keepout']])
        for area in bad:
            with self.subTest(area=area), self.assertRaisesRegex(p.Rejected,'rule-area restrictions'):
                p.check_rule_area_support(['kicad_pcb',area])

    def test_unrestricted_area_and_ordinary_copper_zone_preserved(self):
        tree=['kicad_pcb',zone(),['zone',['net','1'],['layer','"F.Cu"']],['footprint','"owned"',zone()]]
        before=copy.deepcopy(tree);p.check_rule_area_support(tree)
        self.assertEqual(tree,before)

    def test_preflight_rejects_before_candidate_or_native_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            board=Path(tmp).resolve()/'fixture.kicad_pcb'
            tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],zone()]
            board.with_suffix('.kicad_pro').write_text(json.dumps({}))
            sx.write(board,tree);self.assertEqual(p.preflight(board),tree)
            sx.one(sx.one(tree[-1],'keepout'),'vias')[1]='not_allowed';sx.write(board,tree)
            before=board.read_bytes()
            with self.assertRaisesRegex(p.Rejected,'unsupported: rule-area restrictions'):
                p.preflight(board)
            job=Mock()
            with self.assertRaisesRegex(p.Rejected,'rule-area restrictions'):
                p.validate_candidate(job,tree,board,{},[])
            self.assertFalse(job.mock_calls);self.assertEqual(board.read_bytes(),before)

    def test_legacy_module_alias_cannot_hide_footprint_constraints(self):
        with tempfile.TemporaryDirectory() as tmp:
            board=Path(tmp).resolve()/'fixture.kicad_pcb'
            tree=['kicad_pcb',['version','20260206'],['layers',['0','"F.Cu"','signal'],['2','"B.Cu"','signal']],['module','"owned"',zone()]]
            board.with_suffix('.kicad_pro').write_text('{}')
            for prohibited in (False,True):
                with self.subTest(prohibited=prohibited):
                    sx.one(sx.one(tree[-1][-1],'keepout'),'tracks')[1]='not_allowed' if prohibited else 'allowed'
                    sx.write(board,tree)
                    with self.assertRaisesRegex(p.Rejected,'legacy module'):
                        p.check_rule_area_support(tree)
                    with self.assertRaisesRegex(p.Rejected,'legacy module'):
                        p.preflight(board)


if __name__=='__main__':unittest.main()
