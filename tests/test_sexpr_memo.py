"""Pure syntax memo controls; no Native validation or file evidence is cached."""
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p, sexpr as sx


class SyntaxMemoTests(unittest.TestCase):
    def counter(self):
        real = sx._parse_uncached
        calls = []
        def counted(text):
            calls.append(text)
            return real(text)
        return counted, calls

    def test_lists_are_independent_and_operation_exit_discards_syntax(self):
        counted, calls = self.counter()
        text = '(pcb (net 1 "signal") (unknown (field value)))'
        with patch.object(sx, '_parse_uncached', counted):
            with p.validation_readback_session():
                first = sx.parse(text)
                first[1][2] = 'changed'; first[2][1].append('extra')
                second = sx.parse(text)
                self.assertEqual(second, ['pcb', ['net', '1', '"signal"'], ['unknown', ['field', 'value']]])
                second.clear()
                self.assertEqual(sx.parse(text)[0], 'pcb')
                self.assertEqual(len(calls), 1)
            self.assertIsNone(sx._parse_session.get())
            sx.parse(text); sx.parse(text)
            self.assertEqual(len(calls), 3)

    def test_nested_session_reuses_but_handled_error_and_cancel_clear(self):
        counted, calls = self.counter()
        with patch.object(sx, '_parse_uncached', counted):
            with sx.parsing_session():
                sx.parse('(a)')
                with sx.parsing_session():sx.parse('(a)')
                self.assertEqual(len(calls), 1)
                for exc in (ValueError('handled'), KeyboardInterrupt()):
                    try:
                        with sx.parsing_session():raise exc
                    except BaseException:pass
                    self.assertFalse(sx._parse_session.get()['entries'])
                    sx.parse('(a)')
                self.assertEqual(len(calls), 3)

    def test_malformed_input_clears_success_and_never_populates(self):
        for text in ('(a', '(a))', 'outside', '("bad)', '(a) (b)', '(' * 132 + ')' * 132):
            with self.subTest(text=text), sx.parsing_session():
                sx.parse('(valid)')
                with self.assertRaises(ValueError):sx.parse(text)
                self.assertFalse(sx._parse_session.get()['entries'])

    def test_tokenizer_parser_code_and_size_policy_changes_cannot_hit(self):
        with sx.parsing_session():
            sx.parse('(a)')
            with patch.object(sx, 'TOKEN', re.compile(r'NEVER_MATCH')):
                with self.assertRaises(ValueError):sx.parse('(a)')
            sx.parse('(a)')
            with patch.object(sx, 'MAX_BYTES', 2):
                with self.assertRaisesRegex(ValueError, 'limit'):sx.parse('(a)')
            sx.parse('(a)')
            original = sx._parse_uncached.__code__
            def changed(text):raise ValueError('replacement body')
            try:
                sx._parse_uncached.__code__ = changed.__code__
                with self.assertRaisesRegex(ValueError, 'replacement body'):sx.parse('(a)')
            finally:sx._parse_uncached.__code__ = original

    def test_bounded_eviction_and_valid_large_inputs_remain_supported(self):
        with patch.object(sx, 'MEMO_ENTRIES', 2), patch.object(sx, 'MEMO_BYTES', 12), \
                patch.object(sx, 'MEMO_NODES', 5), sx.parsing_session():
            for text in ('(a)', '(b)', '(c)', '(longlonglong)', '(a b c d e f)'):
                self.assertEqual(sx.parse(text), sx._parse_uncached(text))
                state = sx._parse_session.get()
                self.assertLessEqual(len(state['entries']), 2)
                self.assertLessEqual(state['bytes'], 12)
                self.assertLessEqual(state['nodes'], 5)
                if len(text.encode()) > 12 or text == '(a b c d e f)':
                    self.assertNotIn(text, state['entries'])
            self.assertEqual(list(state['entries']), ['(b)', '(c)'])

    def test_read_always_reads_current_file_even_at_same_size(self):
        with tempfile.TemporaryDirectory(dir=p.c.ROOT / '.cache') as root:
            path = Path(root) / 'board.kicad_pcb'
            with sx.parsing_session():
                path.write_text('(pcb (net 1))')
                self.assertEqual(sx.read(path)[1], ['net', '1'])
                path.write_text('(pcb (net 2))')
                self.assertEqual(sx.read(path)[1], ['net', '2'])
                path.write_text('(pcb (net 2)')
                with self.assertRaises(ValueError):sx.read(path)
                self.assertFalse(sx._parse_session.get()['entries'])

    def test_repeated_parsing_preserves_comments_unicode_quotes_and_dump(self):
        text = '; retained atoms\n(pcb (name "é\\\";trace") (unknown \"Ω\") ())'
        expected = sx.parse(text)
        with sx.parsing_session():
            for _ in range(3):
                self.assertEqual(sx.parse(text), expected)
                self.assertEqual(sx.parse(sx.dump(sx.parse(text))), expected)
