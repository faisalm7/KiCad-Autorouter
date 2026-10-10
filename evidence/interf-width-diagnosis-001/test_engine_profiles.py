"""Budget assignment controls; actual-JAR reflection is a separate script."""
import math
import unittest
from autorouter import pipeline as p


class EngineProfileControls(unittest.TestCase):
    def test_strict_classes_disable_all_three_width_reduction_paths(self):
        for profile in ('standard','tuned','completion-only'):
            strict=p.engine_profile_settings(profile,120,strict_class_targets=True)
            legacy=p.engine_profile_settings(profile,120)
            self.assertTrue(strict['strict_class_targets'])
            self.assertFalse(legacy['strict_class_targets'])
            for arg in ('--router.automatic_neckdown=false','--router.fanout.enabled=false','--router.neck_width_um=0'):
                self.assertIn(arg,strict['argv'])
                self.assertNotIn(arg,legacy['argv'])
            self.assertEqual(strict['assigned_job_timeout_seconds'],legacy['assigned_job_timeout_seconds'])

    def test_invalid_static_target_policy_is_rejected(self):
        with self.assertRaisesRegex(p.Rejected,'static netclass'):
            p.engine_profile_settings('standard',120,strict_class_targets='false')

    def test_standard_caps_keep_full_reserves(self):
        result=p.engine_profile_settings('standard',120)
        self.assertEqual(result['assigned_job_timeout_seconds'],60)
        self.assertEqual(result['assigned_optimizer_timeout_seconds'],30)
        self.assertEqual(result['engine_grace_reserve_seconds'],30)
        self.assertEqual(result['native_finalization_reserve_seconds'],10)

    def test_tuned_outer_budget_caps_deadline(self):
        result=p.engine_profile_settings('tuned',117.9)
        self.assertEqual(result['assigned_job_timeout_seconds'],77)
        self.assertEqual(result['assigned_optimizer_timeout_seconds'],77)
        self.assertIn('--router.job_timeout=00:01:17',result['argv'])
        self.assertIn('--router.optimizer.timeout=00:01:17',result['argv'])

    def test_C_incumbent_budget_is_transparent(self):
        full=p.engine_profile_settings('tuned',120)
        incumbent=p.engine_profile_settings('tuned',105)
        self.assertEqual(full['assigned_job_timeout_seconds'],80)
        self.assertEqual(incumbent['assigned_job_timeout_seconds'],65)
        self.assertEqual(full['assigned_job_timeout_seconds']-incumbent['assigned_job_timeout_seconds'],15)

    def test_large_budget_preserves_profile_caps(self):
        result=p.engine_profile_settings('tuned',900)
        self.assertEqual(result['assigned_job_timeout_seconds'],100)
        self.assertEqual(result['assigned_optimizer_timeout_seconds'],90)
        self.assertIn('--router.job_timeout=00:01:40',result['argv'])

    def test_uniform_reserve_short_boundary(self):
        for profile in ('standard','tuned','completion-only'):
            with self.subTest(profile=profile):
                with self.assertRaisesRegex(p.Rejected,'insufficient remaining'):p.engine_profile_settings(profile,40.99)
                result=p.engine_profile_settings(profile,41)
                self.assertEqual(result['assigned_job_timeout_seconds'],1)

    def test_completion_has_distinct_label_and_no_optimizer(self):
        result=p.engine_profile_settings('completion-only',120)
        self.assertIn('--router.optimizer.enabled=false',result['argv'])
        self.assertIsNone(result['assigned_optimizer_timeout_seconds'])
        self.assertEqual(p.engine_baseline('completion-only','both'),'completion_only_probe')
        self.assertEqual(p.engine_baseline('completion-only','none'),'completion_only_probe')

    def test_existing_baseline_labels_stable(self):
        self.assertEqual(p.engine_baseline('standard','none'),'B0')
        self.assertEqual(p.engine_baseline('standard','both'),'B1')
        self.assertEqual(p.engine_baseline('tuned','both'),'B2_tuned')

    def test_tuned_threshold_guard_and_failure_settings_preserved(self):
        args=p.engine_profile_settings('tuned',120)['argv']
        for expected in ('--router.optimizer.improvement_threshold=0.001','--router.optimizer.enable_preflight_guards=false',
                         '--router.optimizer.max_consecutive_failures=100','--router.optimizer.max_consecutive_failures_pass1=100',
                         '--router.optimizer.max_threads=1','--router.optimizer.max_passes=50'):
            self.assertIn(expected,args)

    def test_invalid_remaining_and_profile_fail_closed(self):
        for remaining in (True,None,'120',math.nan,math.inf,-1):
            with self.subTest(remaining=remaining):
                with self.assertRaises(p.Rejected):p.engine_profile_settings('standard',remaining)
        with self.assertRaises(p.Rejected):p.engine_profile_settings('unknown',120)

    def test_no_ambiguous_suffixed_timeout_is_emitted(self):
        for remaining in (41,50.9,105,120,900):
            for profile in ('standard','tuned','completion-only'):
                result=p.engine_profile_settings(profile,remaining)
                self.assertLessEqual(result['assigned_job_timeout_seconds']+40,remaining)
                for arg in result['argv']:
                    if 'timeout=' in arg:self.assertRegex(arg,r'=\d\d:\d\d:\d\d$')


if __name__=='__main__':unittest.main()
