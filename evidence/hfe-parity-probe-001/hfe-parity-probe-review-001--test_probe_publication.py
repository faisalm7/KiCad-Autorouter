"""Pure exact-AST publication/cancellation controls. No Native/subprocess.

Lead may select original/corrected scripts through HFE_PROBE and HFE_ENCLOSURE.
Real owned PRL flags are always restored; process/event values are synthetic.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
ROOT=next(parent for parent in Path(__file__).resolve().parents if (parent/'MASTER_PROMPT.md').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as production,floor_route as f,local_settings as ls,schematic_field_evidence as field_evidence
HERE=Path(__file__).resolve().parent
PROBE=Path(os.environ.get('HFE_PROBE',str(HERE/'probe.py')))
ENCLOSURE=Path(os.environ.get('HFE_ENCLOSURE',str(HERE/'run-hfe-parity-probe-enclosure-001.py')))


class HfeProbePublication(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(dir=HERE)
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name).resolve();self.out=self.root/'outer';self.child=self.out/'probe'
        self.job=self.child/'job';inputs=self.job/'input';inputs.mkdir(parents=True)
        self.stem='owned';self.board=inputs/(self.stem+'.kicad_pcb');self.board.write_bytes(b'owned PCB')
        self.prl=self.board.with_suffix('.kicad_prl');self.prl.write_bytes(b'owned PRL')
        self.addCleanup(self.clear_flags)
        self.before=production.tree_hash(inputs)
        self.name=field_evidence.names('parity-probe')[0]
        self.argv=field_evidence.arguments(self.job,'parity-probe',self.board)[0]
        self.netlist=field_evidence.paths(self.job,'parity-probe')[0];self.netlist.write_bytes(b'owned netlist')
        self.event=dict(policy=ls.POLICY,present=True,path=str(self.prl),sha256=self.before[self.prl.name],
            flags_before=0,flags_during=getattr(stat,'UF_IMMUTABLE',2),flags_restored=True,bytes_unchanged=True)
        self.process=dict(name=self.name,argv=[*f.SANDBOX,*self.argv],cwd=str(self.job),status='success',exit_code=0,
            cleanup_complete=True,local_settings_protection=self.event,local_settings_policy=ls.JOB_POLICY)
        (self.job/(self.name+'-process.json')).write_text(json.dumps(self.process))
        self.record=dict(passed=True,status='completed',observation_complete=True,steps=[self.process],
            netlist_sha256=production.sha(self.netlist),completed_evidence={})
        self.plan=dict(acquisition_sha256='set below',input_with_owned_prl_sha256=self.before)
        self.proof=self.root/'proof.json';self.proof.write_bytes(b'owned proof')
        self.plan['acquisition_sha256']=production.sha(self.proof)
        (self.child/'protocol.json').write_text(json.dumps(self.plan))
        self.receipt=self.root/'original-result.json';self.receipt.write_bytes(b'owned receipt')
        self.report=self.root/'original-report.json';self.report.write_bytes(b'owned report')
        self.controller=self.root/'controller.py';self.controller.write_bytes(b'owned controller')
        self.enclosure=self.root/'enclosure.py';self.enclosure.write_bytes(b'owned enclosure')
        (self.out/'command.log').write_bytes(b'owned log')
        self.childpath=self.child/'result.json';self.childpath.write_text(json.dumps(self.record))
        self.tools={'owned':'synthetic'};self.witness={}
        self.original=SimpleNamespace(clean=lambda _:None,source=lambda:None,material=lambda _:self.witness,
            PROOF=self.proof,PROOF_PIN=production.sha(self.proof),ACQUISITION=self.proof,STEM=self.stem)
        self.p=SimpleNamespace(Rejected=production.Rejected,sha=production.sha,tree_hash=production.tree_hash,
            tool_manifest=lambda **_:self.tools)

    def clear_flags(self):
        if hasattr(os,'chflags') and self.prl.exists():os.chflags(self.prl,0,follow_symlinks=False)

    def require_flags(self):
        if not hasattr(os,'chflags') or not hasattr(stat,'UF_IMMUTABLE'):self.skipTest('actual owned PRL flags require macOS')

    def function(self,path,name):
        tree=ast.parse(path.read_text())
        main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        return next(node for node in ast.walk(main) if isinstance(node,ast.FunctionDef) and node.name==name)

    def namespace(self):
        return dict(p=self.p,f=f,ls=ls,field_evidence=field_evidence,h=SimpleNamespace(owned_destination=lambda _:None),
            original=self.original,owner={},head='owned',tools=self.tools,nt=None,remaining=lambda:10,
            Path=Path,__file__=str(self.enclosure),CONTROLLER=self.controller,outer_pin=production.sha(self.enclosure),
            controller_pin=production.sha(self.controller),OUT=self.out,CHILD=self.child,output=self.child,
            RECEIPT=self.receipt,RECEIPT_PIN=production.sha(self.receipt),REPORT=self.report,REPORT_PIN=production.sha(self.report),
            plan=self.plan,plan_pin=production.sha(self.child/'protocol.json'),code={},witness=self.witness,
            board=self.board,before=self.before,job=SimpleNamespace(out=self.job,steps=self.record['steps']),
            name=self.name,argv=self.argv,netlist=self.netlist,record=self.record,child=self.record,bound=True,
            path=self.childpath,child_pin=production.sha(self.childpath),literal=f.canonical(self.record),
            log_pin=production.sha(self.out/'command.log'))

    def test_child_final_guard_rejects_flag_flip_during_last_netlist_hash(self):
        self.require_flags();namespace=self.namespace();real=self.p.sha
        def late_flip(path):
            digest=real(path)
            if Path(path)==self.netlist:os.chflags(self.prl,stat.UF_IMMUTABLE,follow_symlinks=False)
            return digest
        self.p.sha=late_flip
        node=self.function(PROBE,'stable')
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(PROBE),'exec'),namespace)
        try:
            with self.assertRaisesRegex(production.Rejected,'flags'):
                namespace['stable']()
        finally:self.clear_flags()

    def test_outer_final_guard_rejects_flag_only_change_after_child_publication(self):
        self.require_flags();namespace=self.namespace();node=self.function(ENCLOSURE,'fresh')
        exec(compile(ast.Module(body=[node],type_ignores=[]),str(ENCLOSURE),'exec'),namespace)
        try:
            os.chflags(self.prl,stat.UF_IMMUTABLE,follow_symlinks=False)
            with self.assertRaisesRegex(production.Rejected,'flags'):
                namespace['fresh']()
        finally:self.clear_flags()

    def classify(self,status):
        tree=ast.parse(PROBE.read_text());main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        block=next(node for node in ast.walk(main) if isinstance(node,ast.Try)
            and any(isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute)
                and isinstance(call.func.value,ast.Name) and call.func.value.id=='ls' and call.func.attr=='protected_step'
                for statement in node.body for call in ast.walk(statement)))
        handler=block.handlers[0];namespace=self.namespace()
        namespace['exc']=production.Rejected('owned rejected worker')
        namespace['job'].steps=[dict(status=status)]
        exec(compile(ast.Module(body=handler.body,type_ignores=[]),str(PROBE),'exec'),namespace)
        return namespace['record']

    def test_actual_cancelled_worker_is_classified_cancelled(self):
        row=self.classify('cancelled');self.assertIs(row['passed'],False);self.assertEqual(row['status'],'cancelled')

    def test_ordinary_negative_worker_is_not_classified_cancelled(self):
        row=self.classify('nonzero_exit');self.assertIs(row['passed'],False);self.assertEqual(row['status'],'failed')


if __name__=='__main__':unittest.main(verbosity=2)
