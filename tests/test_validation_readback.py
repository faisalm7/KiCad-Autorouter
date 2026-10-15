"""Scoped consistency reuse controls; native validation is never simulated as run."""
import copy
import shutil
import unittest
from unittest.mock import patch
import test_placement_policy as fixture
import test_result as native_fixture
from autorouter import pipeline as p, placement_clearance as pc


class ReadbackSession(unittest.TestCase):
    setUp=fixture.Receipt.setUp
    save=fixture.Receipt.save

    def test_full_check_once_copied_value_and_context_exit(self):
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check:
            with p.validation_readback_session():
                first=p.check_result(self.receipt);first['current']=False
                second=p.check_result(self.receipt)
                self.assertTrue(second['current']);self.assertEqual(check.call_count,1)
            p.check_result(self.receipt);self.assertEqual(check.call_count,2)

    def test_original_rules_reports_receipt_and_retained_code_mutations_reject(self):
        for path in (self.source,self.source.with_suffix('.kicad_pro'),self.out/'final-drc.json',
                     self.receipt,self.out/'code/placement_strategy.py'):
            raw=path.read_bytes()
            with self.subTest(path=path),p.validation_readback_session():
                p.check_result(self.receipt)
                # Equal byte count defeats a size-only shortcut.
                path.write_bytes(raw[:-1]+(b'x' if raw[-1:]!=b'x' else b'y'))
                with self.assertRaises((p.Rejected,ValueError,KeyError)):p.check_result(self.receipt)
            path.write_bytes(raw)

    def test_empty_directory_is_bound_and_requires_new_full_check(self):
        before=pc.inventory(self.out);witness=pc.inventory(self.out,with_directories=True)
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            (self.out/'trials/9999').mkdir(parents=True)
            self.assertEqual(pc.inventory(self.out),before)
            self.assertNotEqual(pc.inventory(self.out,with_directories=True),witness)
            p.check_result(self.receipt);self.assertEqual(check.call_count,2)
        # Schema3 allows this directory. Schema5's exact trial-population check
        # is still reached on a miss; cache may not skip it.

    def test_symlink_alias_and_special_file_reject(self):
        import os
        with p.validation_readback_session():
            p.check_result(self.receipt)
            link=self.root/'alias';link.symlink_to(self.out,target_is_directory=True)
            with self.assertRaises(p.Rejected):p.check_result(link/'result.json')
            pipe=self.out/'pipe';os.mkfifo(pipe)
            with self.assertRaises(p.Rejected):p.check_result(self.receipt)

    def test_late_full_checker_mutation_cannot_populate(self):
        real=p._check_result_uncached
        def changed(path):
            result=real(path);(self.out/'empty').mkdir();return result
        with patch.object(p,'_check_result_uncached',changed),p.validation_readback_session():
            with self.assertRaisesRegex(p.Rejected,'during full readback'):p.check_result(self.receipt)
            self.assertFalse(p._readback_session.get()['entries'])

    def test_late_hit_mutation_rejects_and_clears(self):
        real=p._readback_witness
        with p.validation_readback_session():
            # Replacement is installed before populating to keep live identities stable.
            calls=[0]
            def changed(*args):
                calls[0]+=1
                if calls[0]==4:(self.out/'empty').mkdir()
                return real(*args)
            with patch.object(p,'_readback_witness',changed):
                p.check_result(self.receipt)
                with self.assertRaisesRegex(p.Rejected,'during cached readback'):p.check_result(self.receipt)
                self.assertFalse(p._readback_session.get()['entries'])

    def test_callable_replacement_forces_full_check(self):
        real=p._check_result_uncached
        with p.validation_readback_session():
            p.check_result(self.receipt)
            with patch.object(p,'_check_result_uncached',wraps=real) as check:
                p.check_result(self.receipt);self.assertEqual(check.call_count,1)

    def test_legacy_zone_helper_replacement_invalidates_reuse(self):
        from autorouter import legacy_zone
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            with patch.object(legacy_zone,'qualify',wraps=legacy_zone.qualify):
                p.check_result(self.receipt)
                self.assertEqual(check.call_count,2)

    def test_prl_metadata_and_core_helper_changes_invalidate_reuse(self):
        import os,stat,sys
        from autorouter import local_settings
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            with patch.object(local_settings,'check_event',wraps=local_settings.check_event):
                p.check_result(self.receipt);self.assertEqual(check.call_count,2)
        if sys.platform!='darwin' or not hasattr(os,'chflags'):return
        prls=list(self.out.rglob('*.kicad_prl'));self.assertTrue(prls);prl=prls[0];before=prl.stat().st_flags
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            try:
                os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
                p.check_result(self.receipt);self.assertEqual(check.call_count,2)
            finally:os.chflags(prl,before,follow_symlinks=False)

    def test_late_tool_callback_prl_flag_change_rejects_cached_witness(self):
        import os,stat,sys
        if sys.platform!='darwin' or not hasattr(os,'chflags'):self.skipTest('Mac flags required')
        prls=list(self.out.rglob('*.kicad_prl'));self.assertTrue(prls);prl=prls[0];flags=prl.stat().st_flags
        real=p.tool_manifest;calls=[0]
        def mutate_on_final_witness():
            calls[0]+=1
            value=real()
            if calls[0]==4:os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
            return value
        try:
            with patch.object(p,'tool_manifest',side_effect=mutate_on_final_witness),p.validation_readback_session():
                p.check_result(self.receipt)
                with self.assertRaisesRegex(p.Rejected,'during cached readback'):p.check_result(self.receipt)
                self.assertFalse(p._readback_session.get()['entries'])
        finally:os.chflags(prl,flags,follow_symlinks=False)

    def test_in_memory_critical_policy_change_invalidates_hit(self):
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            with patch.object(p,'CRITICAL_FINDINGS',p.CRITICAL_FINDINGS|{'missing_courtyard'}):
                # The original project ignores this check. Making it critical
                # must reach full checking and reject the disabled check.
                with self.assertRaisesRegex(p.Rejected,'disabled policy-critical'):p.check_result(self.receipt)
                self.assertEqual(check.call_count,2)

    def test_nested_handled_failure_and_cancellation_clear(self):
        for error in (ValueError('handled'),KeyboardInterrupt()):
            with p.validation_readback_session():
                p.check_result(self.receipt)
                try:
                    with p.validation_readback_session():raise error
                except BaseException:pass
                self.assertFalse(p._readback_session.get()['entries'])
        self.assertIsNone(p._readback_session.get())

    def test_actual_tool_path_change_fails_closed(self):
        with p.validation_readback_session():
            p.check_result(self.receipt)
            with patch.object(p.c,'CLI',self.source):
                with self.assertRaises(p.Rejected):p.check_result(self.receipt)

    def test_lock_and_live_implementation_identity_force_miss(self):
        real=p.tool_manifest
        with patch.object(p,'tool_manifest',wraps=real) as manifest,p.validation_readback_session():
            p.check_result(self.receipt)
            # A changed actual identity must never reuse the previous result.
            def changed():
                value=real();value['implementation_sha256']['autorouter/pipeline.py']='0'*64;return value
            manifest.side_effect=changed
            with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check:
                p.check_result(self.receipt);self.assertEqual(check.call_count,1)

    def test_eight_entry_bound_and_mixed_unsupported_uncached(self):
        # Synthetic checker seam exercises admission/eviction only. The earlier
        # tests use the complete real consistency checker and retained fixtures.
        with patch.object(p,'_check_result_uncached',return_value={'current':True}) as check,p.validation_readback_session():
            for i in range(10):
                target=self.root/('extra-'+str(i));shutil.copytree(self.out,target)
                p.check_result(target/'result.json')
            self.assertEqual(len(p._readback_session.get()['entries']),8)
            for schema in (1,2):
                self.data['schema']=schema;self.save()
                p.check_result(self.receipt);p.check_result(self.receipt)
            self.assertEqual(check.call_count,14)


class NativeReadbackSession(unittest.TestCase):
    """Current normal Native receipt fixtures; no Native tools are executed."""
    save_receipt=native_fixture.ResultFreshnessTests.save_receipt

    def setUp(self):
        native_fixture.ResultFreshnessTests.setUp(self)
        self.out=self.run
        # Explicit setup of existing-PRL software evidence, before any fault.
        from test_normal_local_settings_policy import NormalPolicyReceiptControls
        NormalPolicyReceiptControls._put_prl_in_fixture(self)
        self.save_receipt()

    def test_normal_native_full_first_check_then_copied_reuse(self):
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check:
            with p.validation_readback_session():
                first=p.check_result(self.receipt);first['current']=False
                self.assertTrue(p.check_result(self.receipt)['current'])
                self.assertEqual(check.call_count,1)
            p.check_result(self.receipt);self.assertEqual(check.call_count,2)

    def test_native_source_report_aliasproof_and_missing_proof_force_recheck(self):
        import json
        proof=self.out/'task.alias-export.json'
        for path in (self.source,self.source.with_suffix('.kicad_pro'),self.native,proof):
            raw=path.read_bytes()
            with self.subTest(path=path),patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
                p.check_result(self.receipt)
                try:
                    if path==proof:
                        data=json.loads(raw);data['source_sha256']='0'*64;path.write_text(json.dumps(data))
                    else:path.write_bytes(raw+b' ')
                    with self.assertRaises((p.Rejected,ValueError,KeyError)):p.check_result(self.receipt)
                    self.assertEqual(check.call_count,2);self.assertFalse(p._readback_session.get()['entries'])
                finally:path.write_bytes(raw)
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            try:
                proof.unlink()
                with self.assertRaises((p.Rejected,FileNotFoundError)):p.check_result(self.receipt)
                self.assertEqual(check.call_count,2);self.assertFalse(p._readback_session.get()['entries'])
            finally:proof.write_bytes(raw)

    def test_native_live_scope_edge_alias_and_thermal_helpers_force_recheck(self):
        from autorouter import routing_scope,native_edge,padless_alias_native,thermal
        for module,name in ((routing_scope,'audit'),(native_edge,'correct'),
                            (padless_alias_native,'observe'),(thermal,'_report_binding')):
            with self.subTest(module=module.__name__),patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
                p.check_result(self.receipt)
                with patch.object(module,name,wraps=getattr(module,name)):
                    p.check_result(self.receipt);self.assertEqual(check.call_count,2)

    def test_native_prl_link_metadata_cannot_reuse(self):
        import os
        prl=self.out/'final-drc-input'/self.source.with_suffix('.kicad_prl').name
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt);link=self.root/'prl-hardlink'
            try:
                os.link(prl,link)
                with self.assertRaises(p.Rejected):p.check_result(self.receipt)
                self.assertEqual(check.call_count,2);self.assertFalse(p._readback_session.get()['entries'])
            finally:link.unlink(missing_ok=True)

    def test_native_prl_flags_cannot_reuse(self):
        import os,stat,sys
        if sys.platform!='darwin' or not hasattr(os,'chflags'):self.skipTest('Mac flags required')
        prl=self.out/'final-drc-input'/self.source.with_suffix('.kicad_prl').name;flags=prl.stat().st_flags
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            p.check_result(self.receipt)
            try:
                os.chflags(prl,stat.UF_IMMUTABLE,follow_symlinks=False)
                with self.assertRaises(p.Rejected):p.check_result(self.receipt)
                self.assertEqual(check.call_count,2);self.assertFalse(p._readback_session.get()['entries'])
            finally:os.chflags(prl,flags,follow_symlinks=False)

    def test_native_final_tool_callback_cannot_hide_report_or_aliasproof_bytes(self):
        for path in (self.native,self.out/'task.alias-export.json'):
            raw=path.read_bytes();real=p.tool_manifest;calls=[0]
            def changed():
                calls[0]+=1;value=real()
                if calls[0]==4:path.write_bytes(raw+b' ')
                return value
            try:
                with self.subTest(path=path),patch.object(p,'tool_manifest',side_effect=changed),p.validation_readback_session():
                    p.check_result(self.receipt)
                    with self.assertRaisesRegex(p.Rejected,'during cached readback'):p.check_result(self.receipt)
                    self.assertFalse(p._readback_session.get()['entries'])
            finally:path.write_bytes(raw)

    def test_native_unsupported_or_diagnostic_rows_are_never_cached(self):
        # Admission-only seam: even a permissive stand-in must not cache these
        # markers. Genuine supported rows above use the full central checker.
        original=copy.deepcopy(self.data)
        for change in ({'schema':2},{'schema':6},{'schema':True},{'accepted':False},
                       {'status':'drc_rejected'},{'input_policy':'unknown'},
                       {'strategy':'unqualified-diagnostic'},{'diagnostic_schema':1},
                       {'production_qualified':False}):
            self.data={**original,**change};self.save_receipt()
            with self.subTest(change=change),patch.object(p,'_check_result_uncached',return_value={'current':True}) as check,p.validation_readback_session():
                p.check_result(self.receipt);p.check_result(self.receipt)
                self.assertEqual(check.call_count,2);self.assertFalse(p._readback_session.get()['entries'])
        self.data=original;self.save_receipt()

    def test_native_first_stale_receipt_never_populates(self):
        self.source.write_bytes(self.source.read_bytes()+b' ')
        with patch.object(p,'_check_result_uncached',wraps=p._check_result_uncached) as check,p.validation_readback_session():
            with self.assertRaisesRegex(p.Rejected,'stale source'):p.check_result(self.receipt)
            self.assertEqual(check.call_count,1);self.assertFalse(p._readback_session.get()['entries'])
