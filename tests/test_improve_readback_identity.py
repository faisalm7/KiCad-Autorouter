"""Real shared cache identity controls, without Native execution or fixture mocks."""
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, _improve_context as child


class ImproveLiveIdentity(unittest.TestCase):
    def test_private_module_has_bounded_live_identity(self):
        # Imported dataclasses.field previously exposed MISSING defaults and
        # made every ordinary readback session fail closed. Keep the module
        # in the fingerprint population; change the helper import instead.
        first=p._readback_live_identity((child,))
        self.assertTrue(first)
        self.assertEqual(first,p._readback_live_identity((child,)))

    def test_private_policy_and_callable_changes_remain_bound(self):
        first=p._readback_live_identity((child,))
        for name,value in (('RESERVE_SECONDS',24),('POLICY','changed-policy'),('require',lambda *_:None)):
            with self.subTest(name=name),patch.object(child,name,value):
                self.assertNotEqual(first,p._readback_live_identity((child,)))
        self.assertEqual(first,p._readback_live_identity((child,)))

    def test_unknown_mutable_policy_still_refuses(self):
        with patch.object(child,'UNSUPPORTED_POLICY',object(),create=True):
            with self.assertRaisesRegex(p.Rejected,'unsupported mutable readback policy identity'):
                p._readback_live_identity((child,))


if __name__=='__main__':unittest.main()
