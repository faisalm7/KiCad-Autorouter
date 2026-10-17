"""Authored worker seams for two demonstrated controller defects; no Native proof."""
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
import importlib.util, json, sys, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, handoff as h, review_export as ex
spec=importlib.util.spec_from_file_location('delivery_child',ROOT/'.runs/native1007-delivery-child-001.py')
child=importlib.util.module_from_spec(spec);spec.loader.exec_module(child)

class ControllerControls(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name).resolve();(self.root/'.runs').mkdir()
        self.packet={'owned.kicad_pcb':'(kicad_pcb)'};self.tools={'authored_mock_workers':True}
        self.plan=dict(native_toolchain={},runtime_tools=self.tools,fixture_files=self.packet,
            fixture_sha256={n:h.digest(v.encode()) for n,v in self.packet.items()},board_name='owned.kicad_pcb',source_head='authored')
        self.protocol=self.root/'protocol.json';p.save_json(self.protocol,self.plan)
        stack=ExitStack();self.addCleanup(stack.close);self.stack=stack
        for target,name,value in ((child,'ROOT',self.root),(p.c,'ROOT',self.root),(sys,'executable',str(self.root/'.venv/bin/python')),
                                  (sys,'prefix',str(self.root/'.venv'))):stack.enter_context(patch.object(target,name,value))
        stack.enter_context(patch.object(p.ExperimentalNativeToolchain,'from_record',return_value=object()))
        stack.enter_context(patch.object(p,'tool_manifest',return_value=self.tools))
        self.route=stack.enter_context(patch.object(p,'route',side_effect=self.route_seam))
        stack.enter_context(patch.object(p,'protected_for_record',return_value=[['locked']]))
        stack.enter_context(patch.object(p,'locked',return_value=True))
        stack.enter_context(patch.object(h,'review_copy',return_value={'preview':{'layers':['F.Cu','B.Cu']}}))
        stack.enter_context(patch.object(h,'review_choice',return_value={'human_pcb_approval_observed':False,'applied':False}))
        stack.enter_context(patch.object(p,'check_result',side_effect=p.Rejected('authored default refusal')))
        stack.enter_context(patch.object(h,'check_delivery_context',side_effect=p.Rejected('authored default refusal')))
        stack.enter_context(patch.object(ex,'bind',side_effect=p.Rejected('authored default refusal')))
        def check(*args,**kw):
            if not kw:raise p.Rejected('authored default refusal')
            return {'current':True}
        stack.enter_context(patch.object(ex,'check_export',side_effect=check))
        stack.enter_context(patch.object(ex,'export',side_effect=self.export_seam))
    def route_seam(self,board,out,**kw):
        out.mkdir();p.save_json(out/'result.json',{'authored_no_Native':True})
        return dict(accepted=True,source=str(board),source_hashes=p.tree_hash(board.parent),source_drc={'opens':1},
                    native=dict(opens=0,blocking=0,warnings=6,exclusions=0),metrics={'version':'10.0.7'})
    def export_seam(self,choice,out,**kw):
        out.mkdir();p.save_json(out/'export.json',{'authored_no_Native':True})
        return dict(native=dict(opens=0,blocking=0,warnings=6,exclusions=0),metrics={'version':'10.0.7'})
    def test_late_shared_publisher_failure_cannot_leave_passed_or_exit_zero(self):
        publish=f.publish
        def injected(*args,**kw):
            def fail():raise p.Rejected('authored late final-check failure')
            return publish(*args,**{**kw,'final_check':fail})
        with patch.object(f,'publish',side_effect=injected):code=child.execute(self.protocol,p.sha(self.protocol))
        data=f.read_json(self.root/'.runs/native1007-delivery-001/result.json')
        self.assertEqual(code,2);self.assertFalse(data['passed']);self.assertEqual(data['status'],'invalidated')
        self.assertTrue(list((self.root/'.runs/native1007-delivery-001').glob('invalidated-result-*')))
    def test_outside_board_name_refuses_before_route(self):
        self.plan['board_name']=str(self.root/'outside.kicad_pcb');self.protocol.write_text(json.dumps(self.plan))
        with self.assertRaisesRegex(p.Rejected,'exact flat owned PCB'):child.execute(self.protocol,p.sha(self.protocol))
        self.route.assert_not_called()

if __name__=='__main__':unittest.main()
