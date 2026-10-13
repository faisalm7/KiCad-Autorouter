"""CLI dispatch/incompatibility checks; native routing is measured separately."""
import contextlib,io,unittest
from unittest.mock import patch
from autorouter import __main__ as cli,placement_strategy as placement,strategy

class ImproveCLI(unittest.TestCase):
    def invoke(self,*extra):
        with patch('sys.argv',['autorouter','improve','board.kicad_pcb','--output','new',*extra]),contextlib.redirect_stdout(io.StringIO()) as out:
            code=cli.main()
        return code,out.getvalue()
    def test_legacy_native_dispatch_remains_explicit(self):
        with patch.object(strategy,'prune',return_value={'accepted':False}) as native,patch.object(placement,'prune') as guided:
            self.assertEqual(self.invoke()[0],2)
            native.assert_called_once_with('board.kicad_pcb','new',120,proposal_policy='single');guided.assert_not_called()
    def test_placement_dispatch_uses_measured_variant_and_preserves_failure(self):
        with patch.object(placement,'prune',return_value={'accepted':False,'status':'drc_rejected'}) as guided,patch.object(strategy,'prune') as native:
            code,text=self.invoke('--guidance','placement-search-v1','--seconds','90')
            self.assertEqual(code,2);self.assertIn('drc_rejected',text)
            guided.assert_called_once_with('board.kicad_pcb','new',90,allocation=placement.STANDARD_ALLOCATION);native.assert_not_called()
    def test_explicit_old_allocation_is_available_for_reproduction(self):
        with patch.object(placement,'prune',return_value={'accepted':True}) as guided:
            self.assertEqual(self.invoke('--guidance','placement-search-v1','--allocation','legacy-tuned')[0],0)
            self.assertEqual(guided.call_args.kwargs['allocation'],placement.LEGACY_ALLOCATION)
    def test_incompatible_controls_cannot_silently_change_policy(self):
        for args in [('--allocation','standard-85-v1'),('--guidance','placement-search-v1','--proposal-policy','single')]:
            with self.subTest(args=args),patch.object(placement,'prune') as guided,patch.object(strategy,'prune') as native:
                self.assertEqual(self.invoke(*args)[0],2);guided.assert_not_called();native.assert_not_called()

if __name__=='__main__':unittest.main()
