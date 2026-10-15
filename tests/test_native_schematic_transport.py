"""Explicit experimental transport controls; synthetic journals never prove DRC."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from tests import test_native_toolchain as fixture
from autorouter import pipeline as p,floor_route as f,config as c,schematic_field_evidence as fields

class SchematicTransportControls(unittest.TestCase):
    setUp=fixture.NativeToolchainControls.setUp
    report=fixture.NativeToolchainControls.report
    def test_optin_is_strict_and_requires_explicit_toolchain_and_prl_before_creating_output(self):
        for flag,nt,prl in ((True,None,True),('yes',self.toolchain,True),(1,self.toolchain,True),(None,self.toolchain,True),(True,self.toolchain,False)):
            with self.subTest(flag=flag,prl=prl),self.assertRaises(p.Rejected):
                p.Job(self.root/'not-created',30,native_toolchain=nt,protect_local_settings=prl,experimental_schematic_parity=flag)
            self.assertFalse((self.root/'not-created').exists())
        job=f.FloorJob(self.root/'explicit-parity',30,lambda:30,native_toolchain=self.toolchain,protect_local_settings=True,experimental_schematic_parity=True)
        self.assertIs(job.experimental_schematic_parity,True)
        self.assertEqual(p.experimental_parity_policy(self.toolchain,True),p.EXPERIMENTAL_PARITY_POLICY)
    def test_opted_producer_rechecks_protected_mode_before_any_input_copy(self):
        job=p.Job(self.root/'drift-parity',30,native_toolchain=self.toolchain,protect_local_settings=True,experimental_schematic_parity=True)
        job.protect_local_settings=False
        with self.assertRaisesRegex(p.Rejected,'protected local settings'):
            job.drc('blocked',self.root/'absent.kicad_pcb',schematic_parity=True)
        self.assertFalse((job.out/'blocked-input').exists())
    def test_default_experimental_parity_producer_and_reader_refuse_before_input_access(self):
        job=p.Job(self.root/'default-experiment',30,native_toolchain=self.toolchain)
        with self.assertRaisesRegex(p.Rejected,'opt-in'):job.drc('blocked',self.root/'absent.kicad_pcb',schematic_parity=True)
        self.assertFalse((job.out/'blocked-input').exists())
        with patch.object(f,'read_json',side_effect=AssertionError('must not read any stage')),self.assertRaisesRegex(p.Rejected,'opt-in'):
            f.check_drc_stage(job.out,{},'blocked',self.root/'absent',self.root/'absent',False,{},schematic_parity=True,native_toolchain=self.toolchain)
    def test_experimental_reader_refuses_missing_tampered_policy_or_missing_prl(self):
        for marker,prl in ((None,'job-owned-prl-immutable-v1'),('other','job-owned-prl-immutable-v1'),(p.EXPERIMENTAL_PARITY_POLICY,None)):
            binding={'after':{},'experimental_schematic_parity_policy':marker,'local_settings_policy':prl}
            with self.subTest(marker=marker,prl=prl),patch.object(f,'read_json',return_value=binding),self.assertRaisesRegex(p.Rejected,'policy|local settings'):
                f.check_drc_stage(self.root,{},'stage',self.root/'a',self.root/'a',False,{},schematic_parity=True,native_toolchain=self.toolchain,experimental_schematic_parity=True)
    def test_field_arguments_use_literal_experimental_tools_and_worker_record_without_config_mutation(self):
        board=self.root/'board.kicad_pcb';original=(c.CLI,c.PYTHON,c.PCBNEW)
        default=fields.arguments(self.root,'stage',board)
        explicit=fields.arguments(self.root,'stage',board,native_toolchain=self.toolchain)
        self.assertEqual(default[0][0],str(c.CLI));self.assertEqual(default[1][0],str(c.PYTHON))
        self.assertNotIn('--experimental-native',default[1])
        self.assertEqual(explicit[0],[str(self.toolchain.cli),'sch','export','netlist','--format','kicadsexpr','--output',str(self.root/'stage-fields.net'),str(board.with_suffix('.kicad_sch'))])
        self.assertEqual(explicit[1],[str(self.toolchain.python),str(c.ROOT/'autorouter/native.py'),'--experimental-native',json.dumps(self.toolchain.record(),sort_keys=True),'fields',str(board),str(self.root/'stage-fields.json')])
        self.assertEqual((c.CLI,c.PYTHON,c.PCBNEW),original)
        self.paths['python'].write_bytes(b'changed')
        with self.assertRaisesRegex(p.Rejected,'tool changed'):fields.arguments(self.root,'stage',board,native_toolchain=self.toolchain)
    def test_parse_report_passes_explicit_toolchain_to_complete_field_readback(self):
        path=self.report('10.0.7');raw=json.loads(path.read_text())
        raw['schematic_parity']=[{'type':fields.TYPE,'severity':'warning','items':[]}];path.write_text(json.dumps(raw))
        with patch.object(fields,'readback',return_value={'synthetic':'only-control'}) as reader:
            parsed=p.parse_report(path,'fixture.kicad_pcb',native_toolchain=self.toolchain)
        self.assertEqual(reader.call_args.kwargs,{'native_toolchain':self.toolchain})
        self.assertEqual(parsed['field_parity'],{'synthetic':'only-control'})
        self.assertFalse(p.native_accepted(parsed))
    def test_field_derivation_refuses_toolchain_policy_and_prl_tampering_before_input_read(self):
        binding={'experimental_native_toolchain':self.toolchain.record(),'experimental_schematic_parity_policy':p.EXPERIMENTAL_PARITY_POLICY,'local_settings_policy':'job-owned-prl-immutable-v1','field_local_settings_policy':p.FIELD_LOCAL_SETTINGS_POLICY}
        for key in ('experimental_native_toolchain','experimental_schematic_parity_policy','local_settings_policy','field_local_settings_policy'):
            bad=copy.deepcopy(binding);bad.pop(key)
            with self.subTest(key=key),patch.object(f,'read_json',return_value=bad),self.assertRaisesRegex(p.Rejected,'binding differs'):
                fields.derive(self.root,'stage',{},native_toolchain=self.toolchain)
    def test_experimental_field_policy_cannot_disappear_with_guard_receipt(self):
        binding={'experimental_native_toolchain':self.toolchain.record(),
                 'experimental_schematic_parity_policy':p.EXPERIMENTAL_PARITY_POLICY,
                 'local_settings_policy':'job-owned-prl-immutable-v1',
                 'input':str(self.root/'absent.kicad_pcb'),'after':{}}
        with patch.object(f,'read_json',return_value=binding),patch.object(p,'tree_hash',side_effect=AssertionError('unprotected field input was reached')):
            with self.assertRaisesRegex(p.Rejected,'field PRL'):
                fields.derive(self.root,'stage',{},native_toolchain=self.toolchain)

if __name__=='__main__':unittest.main()
