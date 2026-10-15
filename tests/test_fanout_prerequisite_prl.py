"""Real owned PRL late-material regression; synthetic receipts, no Native.
Run after lead adopts check_prl; actual pair stable AST is compiled unchanged.
"""
import ast,hashlib,os,signal,stat,sys,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autorouter import pipeline as p,floor_route as f,local_settings as ls,handoff as h
from experiments.hfe_original_native_v1 import driver as shared
from experiments.fanout_baseline_v1 import continuation as owned
from tests import test_result as receipt_fixture,test_normal_local_settings_policy as prl_fixture
PAIR=ROOT/'experiments/fanout_baseline_v1/pair.py'


def function(path,name,parent=None):
    tree=ast.parse(path.read_bytes())
    if parent is not None:tree=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==parent)
    nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name]
    if len(nodes)!=1:raise AssertionError('one exact production '+name+' required')
    return nodes[0]


def compiled(node,path,env):
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),env)
    return env[node.name]


class PrerequisitePRLControls(unittest.TestCase):
    def fixture(self):
        case=receipt_fixture.ResultFreshnessTests('runTest');case.setUp();self.addCleanup(case.doCleanups)
        prl_fixture.NormalPolicyReceiptControls._put_prl_in_fixture(case)
        case.save_receipt()
        return case

    def test_complete_dispositions_keep_failed_and_unattempted_or_missing_arms_visible(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary).resolve();first=out/'ir-obstacle/stock45';first.mkdir(parents=True)
            p.save_json(first/'result.json',dict(protocol_sha256='owned-software-pin',status='failed',passed=False,error='prior worker cleanup incomplete'))
            env=dict(context=lambda *a:None,ORDER=[('ir-obstacle','stock45'),('ir-obstacle','NONE')],OUT=out,f=f,p=p,check_control_prl=lambda *a:None)
            report=compiled(function(PAIR,'dispositions'),PAIR,env)
            rows=report({},'owned-software-pin')['rows']
            self.assertEqual([(row['angle'],row['status'],row['accepted']) for row in rows],[('stock45','failed',False),('NONE','not_attempted',False)])
            self.assertIsNone(rows[1]['candidate']);self.assertIn('cleanup',rows[0]['reason'])
            (out/'ir-obstacle/NONE').mkdir()
            rows=report({},'owned-software-pin')['rows'];self.assertEqual(rows[1]['status'],'missing_receipt');self.assertFalse(rows[1]['accepted']);self.assertIsNone(rows[1]['candidate'])

    @unittest.skipUnless(sys.platform=='darwin' and hasattr(os,'chflags'),'actual Mac PRL flags required')
    def test_actual_pair_final_stable_rejects_owned_prerequisite_flag_flip_during_last_material(self):
        prerequisite=self.fixture();arm=self.fixture()
        target=prerequisite.run/'final-drc-input'/prerequisite.source.with_suffix('.kicad_prl').name
        raw=target.read_bytes();old_flags=target.stat().st_flags;before=f.evidence_inventory(prerequisite.run);self.assertEqual(old_flags,0)
        # Captured path context maps the helper's two fixed endpoints onto the
        # existing owned fixture. No production module/global is monkeypatched.
        # This control isolates its positive prerequisite; actual negative Native
        # bindings remain a separate run gate, never supplied by this fixture.
        childpath=prerequisite.root/'owned-control-child.json';child={'positive':True}
        p.save_json(childpath,child);protocol=prerequisite.root/'owned-control-protocol.json'
        p.save_json(protocol,{'tools':prerequisite.data['tools']})
        class CapturedChild:
            def __truediv__(self,name):
                if name=='route':return prerequisite.run
                if name=='route/result.json':return prerequisite.receipt
                if name=='result.json':return childpath
                raise AssertionError('unexpected helper endpoint '+str(name))
        helper_path=Path(owned.__file__);helper=function(helper_path,'check_prl')
        helper_env=dict(owned.__dict__);helper_env['CHILD']=CapturedChild();helper_env['POSITIVE']=CapturedChild()
        actual_helper=compiled(helper,helper_path,helper_env)
        captured_owned=SimpleNamespace(CHILD=CapturedChild(),check_prl=actual_helper)
        binding=dict(protocol=str(protocol),protocol_sha256=p.sha(protocol),child_receipt_sha256=p.sha(childpath),child_literal=f.canonical(child))
        plan={'control_binding':binding};guard_env=dict(p=p,f=f,Path=Path,owned=captured_owned)
        guard=compiled(function(PAIR,'check_control_prl'),PAIR,guard_env)
        guard(plan)  # Real existing normal-policy checker, before any fault.
        class CapturedArm:
            def __truediv__(self,name):
                if name=='route':return arm.run
                if name=='route/result.json':return arm.receipt
                raise AssertionError('unexpected arm endpoint '+str(name))
        captured_arm=CapturedArm()
        owner={};h.capture_destination(owner,arm.run);witness=shared.material(arm.run)
        state={'readbacks':0,'late_material_reads':0,'triggered':False}
        def material(path):
            actual=arm.run if path is captured_arm else Path(path)
            value=shared.material(actual)
            if actual==arm.run and state['readbacks']:
                state['late_material_reads']+=1
                if state['late_material_reads']==2:
                    os.chflags(target,stat.UF_IMMUTABLE,follow_symlinks=False);state['triggered']=True
                    self.assertEqual(target.read_bytes(),raw)
                    self.assertTrue(target.stat().st_flags & stat.UF_IMMUTABLE)
                    self.assertEqual(f.evidence_inventory(prerequisite.run),before)
            return value
        env=dict(h=h,owner=owner,context=lambda *a:None,plan=plan,pin='isolated-software-context',
                 shared=SimpleNamespace(material=material),folder=captured_arm,witness=witness,p=p,routed=arm.data,
                 check_control_prl=guard,ls=ls,LIMITS={'output':128*1024**2})
        stable=compiled(function(PAIR,'stable',parent='worker'),PAIR,env)
        def readback(path):
            ls.check_normal_policy(arm.run,f.read_json(path));state['readbacks']+=1
        previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        def cancel(signum,frame):raise KeyboardInterrupt('received signal '+str(signum))
        try:
            for sig in previous:signal.signal(sig,cancel)
            result=f.publish(arm.run,arm.data,stable,lambda:None,lambda:100,result_checker=readback)
            if result.get('status')=='cancelled':raise KeyboardInterrupt('shared publisher cancelled')
            self.assertEqual(state,dict(readbacks=1,late_material_reads=2,triggered=True),result.get('reason'))
            self.assertFalse(result['accepted']);self.assertEqual(result['status'],'invalidated')
            self.assertIn('flags',result['reason']);self.assertFalse(f.read_json(arm.receipt)['accepted'])
            self.assertTrue(list(arm.run.glob('invalidated-result-*')))
            self.assertEqual(target.read_bytes(),raw)
        finally:
            try:os.chflags(target,old_flags,follow_symlinks=False)
            finally:
                for sig,handler in previous.items():signal.signal(sig,handler)
        self.assertEqual(target.stat().st_flags,old_flags)


if __name__=='__main__':unittest.main()
