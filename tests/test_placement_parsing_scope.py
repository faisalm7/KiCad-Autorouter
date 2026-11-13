"""Pure parsing-lifetime/fresh-file fences, never Native qualification proof."""
import ast
from contextlib import contextmanager
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from autorouter import placement, sexpr as sx
from tests import test_placement_qualification as qualification


class BoundaryStop(Exception):
    pass


class PlacementParsingScopeTests(unittest.TestCase):
    def harness(self):
        value=qualification.MaterialFences(methodName='runTest');value.setUp();self.addCleanup(value.doCleanups)
        return value

    def counter(self):
        original=sx._parse_uncached;calls=[]
        def counted(text):calls.append(text);return original(text)
        return counted,calls

    def test_only_nonpublishing_material_proof_and_check_receive_the_shared_decorator(self):
        tree=ast.parse(Path(placement.__file__).read_text());found=[]
        for node in tree.body:
            if isinstance(node,ast.FunctionDef) and any(ast.unparse(item)=='contract.sx.parsing_session()' for item in node.decorator_list):
                found.append(node.name)
        self.assertEqual(found,['material','proof','check'])
        self.assertIs(placement.contract.sx,sx)
        for name in found:
            function=getattr(placement,name)
            self.assertEqual(function.__name__,name);self.assertEqual(function.__wrapped__.__name__,name)

    def test_every_entrypoint_enters_and_retires_on_exception_and_cancellation_before_work(self):
        for name in ('material','proof','check'):
            for error in (BoundaryStop('stop before work'),KeyboardInterrupt()):
                with self.subTest(entrypoint=name,error=type(error).__name__):
                    states=[]
                    def boundary(*args,**kwargs):
                        state=sx._parse_session.get();self.assertIsNotNone(state);states.append(state)
                        sx.parse('(owned boundary)');self.assertTrue(state['entries'])
                        raise error
                    function=getattr(placement,name)
                    target=(placement,'need') if name in ('material','proof') else (placement.h,'real_path')
                    arguments=({'material':({},),'proof':('unused',{},{}),'check':('unused',)})[name]
                    with patch.object(*target,side_effect=boundary):
                        with self.assertRaises(type(error)):function(*arguments)
                    self.assertEqual(len(states),1);self.assertEqual(states[0]['entries'],{})
                    self.assertEqual(states[0]['bytes'],0);self.assertEqual(states[0]['nodes'],0)
                    self.assertIsNone(sx._parse_session.get())

    def test_material_both_current_fences_run_with_detached_syntax_and_retire_on_success(self):
        harness=self.harness();counted,calls=self.counter();text='(pcb (net 1 "owned"))';states=[];trees=[]
        def current(_):
            state=sx._parse_session.get();self.assertIsNotNone(state);states.append(state)
            tree=sx.parse(text);self.assertEqual(tree,['pcb',['net','1','"owned"']]);trees.append(tree)
            tree[1][1]='changed local tree'
        with patch.object(sx,'_parse_uncached',counted):harness.material(source_read=current)
        self.assertEqual(len(states),2);self.assertIs(states[0],states[1]);self.assertIsNot(trees[0],trees[1])
        self.assertEqual(calls,[text]);self.assertEqual(states[0]['entries'],{});self.assertIsNone(sx._parse_session.get())

    def test_same_size_changed_file_is_freshly_read_and_refused_at_final_material_fence(self):
        harness=self.harness();source=harness.root/'source.kicad_pcb';source.write_text('(pcb (net 1))')
        expected=harness.sha(source);observed=[];counted,calls=self.counter();states=[]
        def current(_):
            states.append(sx._parse_session.get());observed.append(sx.read(source))
            if harness.sha(source)!=expected:raise ValueError('actual source bytes changed')
        def change():source.write_text('(pcb (net 2))');return harness.tools
        with patch.object(sx,'_parse_uncached',counted),self.assertRaisesRegex(ValueError,'actual source bytes changed'):
            harness.material(source_read=current,tool_read=change)
        self.assertEqual(observed,[['pcb',['net','1']],['pcb',['net','2']]])
        self.assertEqual(calls,['(pcb (net 1))','(pcb (net 2))'])
        self.assertIsNone(sx._parse_session.get());self.assertFalse(states[0]['entries'])

    def test_nested_material_reuses_outer_syntax_but_exception_clears_shared_memo(self):
        harness=self.harness();text='(pcb (net 1))';counted,calls=self.counter()
        with patch.object(sx,'_parse_uncached',counted):
            with sx.parsing_session():
                outer=sx._parse_session.get();sx.parse(text)
                def current(_):
                    self.assertIs(sx._parse_session.get(),outer);sx.parse(text)
                harness.material(source_read=current);self.assertEqual(calls,[text]);self.assertTrue(outer['entries'])
                def stopped(_):sx.parse(text);raise BoundaryStop('owned nested failure')
                with self.assertRaises(BoundaryStop):harness.material(source_read=stopped)
                self.assertFalse(outer['entries']);sx.parse(text);self.assertEqual(calls,[text,text])
            self.assertIsNone(sx._parse_session.get());self.assertFalse(outer['entries'])

    def test_independent_material_operations_never_inherit_syntax_or_mutable_trees(self):
        harness=self.harness();text='(pcb (net 1))';counted,calls=self.counter();states=[]
        def current(_):
            state=sx._parse_session.get()
            if not states or states[-1] is not state:states.append(state)
            tree=sx.parse(text);self.assertEqual(tree,['pcb',['net','1']]);tree.clear()
        with patch.object(sx,'_parse_uncached',counted):
            harness.material(source_read=current);self.assertIsNone(sx._parse_session.get())
            harness.material(source_read=current);self.assertIsNone(sx._parse_session.get())
        self.assertEqual(calls,[text,text]);self.assertEqual(len(states),2);self.assertIsNot(states[0],states[1])
        self.assertTrue(all(state['entries']=={} and state['bytes']==state['nodes']==0 for state in states))

    def test_retirement_error_or_cancel_in_material_or_proof_invalidates_authored_pending_publication(self):
        """Exercise the real publisher; the proof body stops at its first guard."""
        for name in ('material','proof'):
            for error in (RuntimeError('retirement failed'),KeyboardInterrupt('retirement cancelled')):
                with self.subTest(entrypoint=name,error=type(error).__name__),tempfile.TemporaryDirectory() as temporary:
                    output=Path(temporary).resolve();states=[]
                    function=getattr(placement,name)
                    # ContextDecorator retains its context factory. Replace only
                    # that test seam, nesting the actual syntax session and then
                    # failing on retirement. No Native proof is manufactured.
                    closed=dict(zip(function.__code__.co_freevars,(cell.cell_contents for cell in function.__closure__)))
                    factory=closed['self']
                    @contextmanager
                    def retirement():
                        with sx.parsing_session():
                            state=sx._parse_session.get();states.append(state)
                            try:yield
                            except BoundaryStop:pass  # Explicit first-guard proof probe only.
                        self.assertIsNone(sx._parse_session.get());self.assertFalse(state['entries'])
                        raise error
                    if name=='material':
                        harness=self.harness()
                        final=lambda:harness.material(source_read=lambda _:sx.parse('(owned material proof)'))
                        guard=patch.object(placement,'need',wraps=placement.need)
                    else:
                        def stop(*args):sx.parse('(owned first proof guard)');raise BoundaryStop()
                        final=lambda:placement.proof('unused',{},{});guard=patch.object(placement,'need',side_effect=stop)
                    record=dict(status='pending_candidate',placement_qualified=True,accepted=False)
                    account=qualification.PublicationControls(methodName='runTest').account(record,lambda:90.)
                    with patch.object(factory,'_recreate_cm',side_effect=retirement),guard:
                        actual=placement.f.publish(output,record,lambda:None,account,lambda:90.,final_check=final)
                    self.assertFalse(actual['placement_qualified'])
                    self.assertEqual(actual['status'],'cancelled' if isinstance(error,KeyboardInterrupt) else 'invalidated')
                    self.assertFalse(json.loads((output/'result.json').read_text())['placement_qualified'])
                    self.assertEqual(len(list(output.glob('invalidated-result-*.json'))),1)
                    self.assertEqual(len(states),1);self.assertIsNone(sx._parse_session.get())

    def test_material_scope_retirement_finishes_before_the_publish_final_cap(self):
        harness=self.harness();events=[]
        def current(_):events.append('current');sx.parse('(owned material)')
        def final():
            harness.material(source_read=current)
            self.assertIsNone(sx._parse_session.get());events.append('retired')
        def remaining():
            self.assertIsNone(sx._parse_session.get());events.append('cap');return 90.
        with tempfile.TemporaryDirectory() as temporary:
            record=dict(status='pending_candidate',placement_qualified=True,accepted=False)
            account=qualification.PublicationControls(methodName='runTest').account(record,lambda:90.)
            result=placement.f.publish(Path(temporary).resolve(),record,lambda:None,account,remaining,final_check=final)
        self.assertTrue(result['placement_qualified']);self.assertEqual(events,['current','current','retired','cap'])


if __name__=='__main__':unittest.main()
