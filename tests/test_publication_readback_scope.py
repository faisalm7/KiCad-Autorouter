"""Real shared publication/session boundaries on authored bytes, never Native."""
from contextlib import contextmanager
import unittest
from unittest.mock import patch

from autorouter import floor_route as f, pipeline as p
from tests import test_native_diagnostic_publication as fixture


class PublicationReadbackScope(unittest.TestCase):
    setUp = fixture.NativeDiagnosticPublicationControls.setUp
    inputs = fixture.NativeDiagnosticPublicationControls.inputs

    def publication(self, name, on_exit=lambda: None):
        out, source, report, stable, account, remaining, owned, clock = self.inputs(name)
        # This is an authored control-flow positive; the explicit checker below
        # checks only this fixture. It cannot establish routing acceptance.
        report.update(accepted=True)
        events = []; states = []

        @contextmanager
        def scope():
            with p.validation_readback_session():
                state = p._readback_session.get(); states.append(state)
                state['native7_contexts']['authored-sentinel'] = object()
                events.append('enter')
                yield
            events.append('exit'); on_exit()

        def check():
            self.assertIs(p._readback_session.get(), states[0]); stable()
            events.append('stable')

        def read(path):
            self.assertIs(p._readback_session.get(), states[0])
            self.assertTrue(f.read_json(path)['accepted']); events.append('reader')

        def cap():
            self.assertIsNone(p._readback_session.get())
            self.assertEqual(states[0]['native7_contexts'], {})
            events.append('cap'); return remaining()

        actual = f.publish(out, report, check, account, cap, owned=owned,
                           result_checker=read, readback_context=scope)
        return actual, out, events, states

    def test_all_proofs_run_in_one_session_and_exit_precedes_final_cap(self):
        actual, out, events, states = self.publication('positive')
        self.assertTrue(actual['accepted'])
        self.assertEqual(events, ['enter', 'stable', 'stable', 'reader', 'stable', 'exit', 'cap'])
        self.assertTrue(f.read_json(out/'result.json')['accepted'])
        self.assertEqual(states[0]['entries'], {})

    def test_exit_wall_or_CPU_exhaustion_invalidates_provisional_positive(self):
        for component in ('wall', 'CPU'):
            with self.subTest(component=component):
                budget = dict(wall=10, CPU=10)
                original = self.inputs
                def inputs(name):
                    values = list(original(name)); values[5] = lambda: min(budget.values())
                    return values
                with patch.object(self, 'inputs', inputs):
                    actual, out, events, states = self.publication(component,
                        on_exit=lambda: budget.update({component: 0}))
                self.assertFalse(actual['accepted']); self.assertIn('budget', actual['reason'])
                self.assertFalse(f.read_json(out/'result.json')['accepted'])
                self.assertTrue(list(out.glob('invalidated-result-*')))
                self.assertIsNone(p._readback_session.get())

    def test_exit_exception_or_cancellation_invalidates_and_resets_session(self):
        for error in (RuntimeError('cleanup failed'), KeyboardInterrupt('cancel during cleanup')):
            with self.subTest(error=type(error).__name__):
                def fail():raise error
                actual, out, events, states = self.publication(type(error).__name__, on_exit=fail)
                self.assertFalse(actual['accepted'])
                self.assertEqual(actual['status'], 'cancelled' if isinstance(error, KeyboardInterrupt) else 'invalidated')
                self.assertFalse(f.read_json(out/'result.json')['accepted'])
                self.assertTrue(list(out.glob('invalidated-result-*')))
                self.assertIsNone(p._readback_session.get())

    def test_exit_receipt_or_record_mutation_is_invalidated(self):
        for kind in ('receipt', 'record'):
            with self.subTest(kind=kind):
                original = self.inputs; saved = []
                def inputs(name):
                    values = original(name); saved.append(values); return values
                def mutate():
                    out, _, report, *_ = saved[0]
                    if kind == 'record':report['changed'] = True
                    else:
                        value = f.read_json(out/'result.json'); value['changed'] = True
                        p.save_json(out/'result.json', value)
                with patch.object(self, 'inputs', inputs):
                    actual, out, _, _ = self.publication(kind, on_exit=mutate)
                self.assertFalse(actual['accepted']); self.assertIn('cleanup', actual['reason'])
                self.assertFalse(f.read_json(out/'result.json')['accepted'])

    def test_session_token_resets_even_when_cache_cleanup_raises(self):
        for error in (RuntimeError('cache clear failed'), KeyboardInterrupt('cache clear cancelled')):
            with self.subTest(error=type(error).__name__):
                with patch.object(p, '_clear_readback_entries', side_effect=error):
                    with self.assertRaises(type(error)):
                        with p.validation_readback_session():
                            self.assertIsNotNone(p._readback_session.get())
                self.assertIsNone(p._readback_session.get())

    def test_exit_directory_replacement_is_never_overwritten(self):
        original = self.inputs; saved = []
        def inputs(name):
            values = original(name); saved.append(values); return values
        def replace():
            out = saved[0][0]; out.rename(out.with_name(out.name+'-preserved'))
            out.mkdir(); (out/'owner-marker').write_text('replacement must survive')
        with patch.object(self, 'inputs', inputs), self.assertRaises(p.Rejected):
            self.publication('replacement', on_exit=replace)
        out = saved[0][0]
        self.assertEqual((out/'owner-marker').read_text(), 'replacement must survive')
        self.assertEqual({path.name for path in out.iterdir()}, {'owner-marker'})
        self.assertTrue((out.with_name(out.name+'-preserved')/'result.json').is_file())
        self.assertIsNone(p._readback_session.get())


if __name__ == '__main__':unittest.main()
