"""Shared native-project preservation contract, independent of DRC verdicts."""
import unittest
from autorouter import pipeline as p


class ProjectPreservation(unittest.TestCase):
    def setUp(self):
        self.before={'board.kicad_pcb':'board','board.kicad_pro':'rules','child.kicad_sch':'circuit'}

    def test_originals_and_only_named_new_state_file(self):
        p.check_drc_project(self.before,dict(self.before),'board.kicad_pcb')
        p.check_drc_project(self.before,{**self.before,'board.kicad_prl':'state'},'board.kicad_pcb')
        for name in self.before:
            for change in ('missing','changed'):
                after=dict(self.before)
                if change=='missing':del after[name]
                else:after[name]='tamper'
                with self.subTest(name=name,change=change),self.assertRaises(p.Rejected):
                    p.check_drc_project(self.before,after,'board.kicad_pcb')
        for name in ('other.kicad_prl','board.kicad_dru','new.kicad_pcb'):
            with self.subTest(name=name),self.assertRaises(p.Rejected):
                p.check_drc_project(self.before,{**self.before,name:'new'},'board.kicad_pcb')
        before={**self.before,'board.kicad_prl':'existing'}
        with self.assertRaises(p.Rejected):
            p.check_drc_project(before,{**before,'board.kicad_prl':'changed'},'board.kicad_pcb')

    def test_saving_exempts_only_board_content_and_requires_its_presence(self):
        p.check_drc_project(self.before,{**self.before,'board.kicad_pcb':'refilled'},'board.kicad_pcb',saved=True)
        for after in ({k:v for k,v in self.before.items() if k!='board.kicad_pcb'},
                      {**self.before,'board.kicad_pro':'changed'}):
            with self.assertRaises(p.Rejected):p.check_drc_project(self.before,after,'board.kicad_pcb',saved=True)
        for name in ('../board.kicad_pcb','missing.kicad_pcb','board.kicad_pro'):
            with self.assertRaises(p.Rejected):p.check_drc_project(self.before,self.before,name)


if __name__=='__main__':unittest.main()
