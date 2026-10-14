"""Scoped consistency reuse controls; native validation is never simulated as run."""
import copy
import shutil
import unittest
from unittest.mock import patch
import test_placement_policy as fixture
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

    def test_eight_entry_bound_and_legacy_uncached(self):
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
