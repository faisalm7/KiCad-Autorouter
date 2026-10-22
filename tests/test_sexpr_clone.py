"""Pure syntax-copy equivalence; these controls do not qualify native routing."""
import copy
import random
import unittest
from unittest.mock import patch

from autorouter import pipeline as p, sexpr as sx


class SyntaxCloneControls(unittest.TestCase):
    def test_generated_syntax_preserves_unknown_atoms_and_independent_lists(self):
        rng = random.Random(7541)
        atoms = ['unknown_field', '"quoted \\" atom"', 'µΩ', '0', '-2.5', '']
        def generate(depth):
            if depth == 0 or rng.randrange(3) == 0:return rng.choice(atoms)
            return [generate(depth - 1) for _ in range(rng.randrange(7))]
        for _ in range(60):
            original = [generate(5), ['vendor_extension', '"untouched"']]
            expected = copy.deepcopy(original)
            result = sx.clone(original)
            self.assertEqual(result, expected)
            self.assertEqual(sx.dump(result), sx.dump(original))
            result[-1].append('modified')
            self.assertEqual(original, expected)

    def test_aliases_and_cycles_match_deepcopy_without_sharing_input(self):
        shared = ['a']; original = [shared, shared]
        result = sx.clone(original)
        self.assertIs(result[0], result[1])
        self.assertIsNot(result[0], shared)
        result[0].append('b')
        self.assertEqual(shared, ['a'])
        cycle = []; cycle.append(cycle)
        copied = sx.clone(cycle)
        self.assertIs(copied[0], copied)
        self.assertIsNot(copied, cycle)

    def test_non_syntax_and_subclasses_refuse_before_codec_or_custom_hooks(self):
        class Hostile:
            def __reduce__(self):raise AssertionError('custom reduction executed')
        class StringSubclass(str):pass
        class ListSubclass(list):
            def __iter__(self):raise AssertionError('custom iteration executed')
        for value in (None, 1, {}, b'encoded bytes', Hostile(),
                      StringSubclass('atom'), ListSubclass(['atom'])):
            with self.subTest(value_type=type(value).__name__), patch.object(sx, '_clone_encode') as encode:
                with self.assertRaises(TypeError):sx.clone(['root', value])
                encode.assert_not_called()

    def test_deep_native_syntax_is_unchanged_without_new_memo_limits(self):
        original = ['atom']
        for _ in range(125):original = ['extension', original]
        with patch.object(sx, 'MEMO_BYTES', 0), patch.object(sx, 'MEMO_NODES', 0):
            self.assertEqual(sx.clone(original), copy.deepcopy(original))
        with sx.parsing_session():
            state = sx._parse_session.get(); before = dict(state)
            self.assertEqual(sx.clone(original), original)
            self.assertEqual(state, before)

    def test_codec_failure_propagates_and_live_policy_binds_both_callables(self):
        original = ['board', ['unknown', 'atom']]
        identity = p._readback_live_identity((sx,))
        for name in ('_clone_encode', '_clone_decode'):
            with patch.object(sx, name, side_effect=ValueError('codec refused')):
                self.assertNotEqual(p._readback_live_identity((sx,)), identity)
                with self.assertRaisesRegex(ValueError, 'codec refused'):sx.clone(original)
            self.assertEqual(original, ['board', ['unknown', 'atom']])

    def test_immutable_projection_still_copies_unknown_and_zone_intent(self):
        original = sx.parse('(kicad_pcb (vendor (nested "µΩ")) '
                            '(zone (uuid z) (net 1) (filled_polygon (pts (xy 1 2)))))')
        before = copy.deepcopy(original)
        immutable = p.immutable(original)
        sx.one(sx.one(immutable, 'vendor'), 'nested').append('changed')
        sx.one(immutable, 'zone').append(['name', 'changed'])
        self.assertEqual(original, before)
        self.assertIsNone(sx.one(sx.one(p.immutable(original), 'zone'), 'filled_polygon'))


if __name__ == '__main__':unittest.main()
