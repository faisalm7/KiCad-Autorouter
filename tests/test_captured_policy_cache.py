"""Pure captured-code memo controls; no file/Native validation is cached."""
import ast
import unittest
from unittest.mock import patch

from autorouter import local_settings as ls, pipeline as p


class CapturedPolicyCacheTests(unittest.TestCase):
    def setUp(self):
        ls._cached_policy_declarations.cache_clear()
        self.addCleanup(ls._cached_policy_declarations.cache_clear)

    def test_float_defaults_stay_uncached_even_when_equal_with_different_sign(self):
        import math
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        def derive(raw,policies,parse,walk,sign=0.0):
            return tuple((name,value if math.copysign(1,sign)>0 else None) for name,value in policies)
        with patch.object(ls,'_derive_policy_declarations',derive):
            self.assertEqual(ls.policy_declarations(raw,expected),expected)
            derive.__defaults__=(-0.0,)
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
        self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,0)

    def test_identical_bytes_and_reordered_expectations_parse_once(self):
        raw=b"FIRST='one'\nSECOND: str='two'\n"
        with patch('ast.parse',wraps=ast.parse) as parsed:
            first=ls.policy_declarations(raw,{'FIRST':'one','SECOND':'two'})
            second=ls.policy_declarations(raw,{'SECOND':'two','FIRST':'one'})
        self.assertEqual(first,{'FIRST':'one','SECOND':'two'})
        self.assertEqual(second,first)
        self.assertEqual(list(second),['SECOND','FIRST'])
        self.assertIsNot(first,second)
        parsed.assert_called_once_with(raw)

    def test_changed_source_or_expected_value_derives_again(self):
        with patch('ast.parse',wraps=ast.parse) as parsed:
            self.assertEqual(ls.policy_declarations(b"ONE='one'\n",{'ONE':'one'}),{'ONE':'one'})
            self.assertEqual(ls.policy_declarations(b'# absent\n',{'ONE':'one'}),{'ONE':None})
            with self.assertRaises(p.Rejected):
                ls.policy_declarations(b"ONE='one'\n",{'ONE':'wrong'})
            self.assertEqual(parsed.call_count,3)

    def test_returned_dictionary_and_caller_dictionary_do_not_mutate_memo(self):
        expected={'ONE':'one'};raw=b"ONE='one'\n"
        first=ls.policy_declarations(raw,expected)
        first['ONE']='corrupt';first['EXTRA']='unexpected'
        second=ls.policy_declarations(raw,expected)
        self.assertEqual(second,{'ONE':'one'})
        expected['ONE']='changed'
        with self.assertRaises(p.Rejected):ls.policy_declarations(raw,expected)
        self.assertEqual(ls.policy_declarations(raw,{'ONE':'one'}),{'ONE':'one'})

    def test_all_type_namespace_and_size_guards_run_after_warm_hit(self):
        class Bytes(bytes):pass
        class Dict(dict):pass
        class Str(str):pass
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        bad_raw=(None,raw.decode(),bytearray(raw),Bytes(raw),b'#'*(1024**2+1))
        bad_policies=(None,{},Dict(expected),{'ONE':Str('one')},{Str('ONE'):'one'},
                      {True:'one'},{'ONE':True},{str(i):'one' for i in range(9)})
        with patch('ast.parse',wraps=ast.parse) as parsed:
            self.assertEqual(ls.policy_declarations(raw,expected),expected)
            self.assertEqual(ls.policy_declarations(raw,expected),expected)
            for value in bad_raw:
                with self.subTest(raw_type=type(value)),self.assertRaises(p.Rejected):
                    ls.policy_declarations(value,expected)
            for value in bad_policies:
                with self.subTest(policies=value),self.assertRaises(p.Rejected):
                    ls.policy_declarations(raw,value)
            parsed.assert_called_once_with(raw)

    def test_maximum_source_and_namespace_remain_valid(self):
        raw=b"ONE='one'\n#";raw+=b'x'*(1024**2-len(raw))
        expected={'ONE':'one',**{'MISSING'+str(i):'expected' for i in range(7)}}
        result=ls.policy_declarations(raw,expected)
        self.assertEqual(result,{'ONE':'one',**{name:None for name in expected if name!='ONE'}})
        self.assertEqual(ls.policy_declarations(raw,expected),result)

    def test_large_names_or_expectations_bypass_cache_without_new_refusal(self):
        cases=((b'# absent\n',{'M'*8193:'expected'},None),
               (b'# absent\n',{'MISSING':'x'*8193},None),
               (b"ONE='"+b'x'*8193+b"'\n",{'ONE':'x'*8193},'x'*8193))
        with patch('ast.parse',wraps=ast.parse) as parsed:
            for raw,expected,value in cases:
                for _ in range(2):
                    self.assertEqual(ls.policy_declarations(raw,expected),{name:value for name in expected})
                    self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,0)
        self.assertEqual(parsed.call_count,2*len(cases))

    def test_syntax_duplicate_nested_and_ambiguous_failures_are_not_cached(self):
        cases=(b'def broken(:\n',b"ONE='one'\nONE='one'\n",
               b"if True:\n ONE='one'\n",b"other=ONE='one'\n",
               b"ONE=choose()\n",b"(ONE := 'one')\n",b"ONE += 'one'\n")
        with patch('ast.parse',wraps=ast.parse) as parsed:
            for raw in cases:
                for _ in range(2):
                    with self.subTest(raw=raw),self.assertRaises(p.Rejected):
                        ls.policy_declarations(raw,{'ONE':'one'})
        self.assertEqual(parsed.call_count,2*len(cases))
        self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,0)

    def test_sixteen_entry_bound_evicts_oldest_derivation(self):
        sources=[b"ONE='one'\n#"+str(i).encode() for i in range(17)]
        with patch('ast.parse',wraps=ast.parse) as parsed:
            for raw in sources:ls.policy_declarations(raw,{'ONE':'one'})
            info=ls._cached_policy_declarations.cache_info()
            self.assertEqual((info.maxsize,info.currsize),(16,16))
            ls.policy_declarations(sources[-1],{'ONE':'one'})
            self.assertEqual(parsed.call_count,17)
            ls.policy_declarations(sources[0],{'ONE':'one'})
            self.assertEqual(parsed.call_count,18)
            self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,16)

    def test_replaced_derivation_function_cannot_reuse_old_result(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        self.assertEqual(ls.policy_declarations(raw,expected),expected)
        def replacement(raw,policies,parse,walk):return tuple((name,None) for name,_ in policies)
        with patch.object(ls,'_derive_policy_declarations',replacement):
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
        self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_changed_code_on_same_derivation_function_cannot_reuse_old_result(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        self.assertEqual(ls.policy_declarations(raw,expected),expected)
        derive=ls._derive_policy_declarations;original=derive.__code__
        def replacement(raw,policies,parse,walk):return tuple((name,None) for name,_ in policies)
        try:
            derive.__code__=replacement.__code__
            self.assertIs(ls._derive_policy_declarations,derive)
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
        finally:derive.__code__=original
        self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_replaced_parser_and_walker_cannot_reuse_old_derivation(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        self.assertEqual(ls.policy_declarations(raw,expected),expected)
        def invalid_parser(raw):raise ValueError('changed parser')
        with patch.object(ast,'parse',invalid_parser):
            with self.assertRaises(p.Rejected):ls.policy_declarations(raw,expected)
        def empty_walk(node):return iter(())
        with patch.object(ast,'walk',empty_walk):
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
        self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_changed_code_on_same_parser_and_walker_cannot_reuse_old_derivation(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        def parser(raw,saved=ast.parse):return saved(raw)
        def invalid_parser(raw,saved=None):raise ValueError('changed parser code')
        def walker(node,saved=ast.walk):return saved(node)
        def empty_walk(node,saved=None):return iter(())
        for name,callable_,replacement in (('parse',parser,invalid_parser),('walk',walker,empty_walk)):
            with self.subTest(callable=name),patch.object(ast,name,callable_):
                self.assertEqual(ls.policy_declarations(raw,expected),expected)
                original=callable_.__code__
                try:
                    callable_.__code__=replacement.__code__
                    if name=='parse':
                        with self.assertRaises(p.Rejected):ls.policy_declarations(raw,expected)
                    else:self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
                finally:callable_.__code__=original
                self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_actual_parser_mode_default_change_refuses_warmed_assignment(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'};parser=ast.parse
        original=parser.__defaults__
        self.assertEqual(original[-1],'exec')
        self.assertEqual(ls.policy_declarations(raw,expected),expected)
        try:
            parser.__defaults__=(*original[:-1],'eval')
            with self.assertRaises(SyntaxError):parser(raw)
            with self.assertRaises(p.Rejected):ls.policy_declarations(raw,expected)
        finally:parser.__defaults__=original
        self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_actual_parser_keyword_default_change_refuses_warmed_source(self):
        raw=b"ONE='one'\npass # type: int\n";expected={'ONE':'one'};parser=ast.parse
        original=parser.__kwdefaults__
        self.assertIs(original['type_comments'],False)
        self.assertEqual(ls.policy_declarations(raw,expected),expected)
        try:
            parser.__kwdefaults__={**original,'type_comments':True}
            with self.assertRaises(SyntaxError):parser(raw)
            with self.assertRaises(p.Rejected):ls.policy_declarations(raw,expected)
        finally:parser.__kwdefaults__=original
        self.assertEqual(ls.policy_declarations(raw,expected),expected)

    def test_derivation_and_walker_defaults_bind_immutable_values(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'}
        original_derive=ls._derive_policy_declarations;original_walk=ast.walk
        def derive(raw,policies,parse,walk,*,present=True):
            return original_derive(raw,policies,parse,walk) if present else tuple((name,None) for name,_ in policies)
        def walk(node,empty=False):return iter(()) if empty else original_walk(node)
        with patch.object(ls,'_derive_policy_declarations',derive):
            self.assertEqual(ls.policy_declarations(raw,expected),expected)
            derive.__kwdefaults__={'present':False}
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})
        with patch.object(ast,'walk',walk):
            self.assertEqual(ls.policy_declarations(raw,expected),expected)
            walk.__defaults__=(True,)
            self.assertEqual(ls.policy_declarations(raw,expected),{'ONE':None})

    def test_mutable_or_large_callable_defaults_bypass_without_new_refusal(self):
        raw=b"ONE='one'\n";expected={'ONE':'one'};original=ast.parse;calls=[]
        def parser(raw,state=None):
            calls.append(raw)
            return original(raw)
        def keyword_parser(raw,*,state=None):
            calls.append(raw)
            return original(raw)
        unsupported=([],{'key':'value'},'x'*8193,tuple(range(65)),2**257)
        with patch.object(ast,'parse',parser):
            for value in unsupported:
                parser.__defaults__=(value,)
                for _ in range(2):self.assertEqual(ls.policy_declarations(raw,expected),expected)
                self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,0)
        with patch.object(ast,'parse',keyword_parser):
            for value in unsupported:
                keyword_parser.__kwdefaults__={'state':value}
                for _ in range(2):self.assertEqual(ls.policy_declarations(raw,expected),expected)
                self.assertEqual(ls._cached_policy_declarations.cache_info().currsize,0)
        self.assertEqual(len(calls),4*len(unsupported))


if __name__=='__main__':unittest.main()
