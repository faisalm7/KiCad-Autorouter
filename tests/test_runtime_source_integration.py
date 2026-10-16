"""Product provenance seam; native routing is qualified separately."""
import unittest
from unittest import mock
from types import SimpleNamespace

from autorouter import pipeline as p, placement_clearance as pc, provenance as pv
from autorouter import __main__ as cli


class RuntimeSourceIntegration(unittest.TestCase):
    def test_tool_manifest_retains_explicit_runtime_build_identity(self):
        identity={'kind':pv.KIND,'git_head':'a'*40,'manifest_sha256':'b'*64,
                  'build_source':{'kind':'git-checkout','git_head':'a'*40}}
        with mock.patch.object(pv,'source_identity',return_value=identity) as check:
            tools=p.tool_manifest()
        check.assert_called_once_with(p.c.ROOT,tools['implementation_sha256'])
        self.assertEqual(tools['git_head'],identity['git_head'])
        self.assertEqual(tools['source_provenance'],identity)

    def test_missing_runtime_provenance_is_rejected(self):
        with mock.patch.object(pv,'source_identity',side_effect=ValueError('manifest missing')):
            with self.assertRaisesRegex(p.Rejected,'runtime source provenance unavailable'):
                p.tool_manifest()

    def test_runtime_placement_refuses_before_git_blob_access(self):
        with mock.patch.object(pc.subprocess,'run') as git:
            with self.assertRaisesRegex(p.Rejected,'placement guidance requires the committed source checkout'):
                pc.capture_freeze({'source_provenance':{'kind':pv.KIND}})
        git.assert_not_called()

    def test_doctor_reports_missing_provenance_as_not_ready(self):
        with mock.patch.object(p,'tool_manifest',side_effect=p.Rejected('manifest missing')), mock.patch.object(cli.platform,'platform',return_value='owned-test-host'):
            with mock.patch.object(cli.subprocess,'run') as execute:
                report=cli.doctor()
        execute.assert_not_called()
        self.assertIs(report['ready'],False)
        self.assertEqual(report['checks']['runtime_provenance'],{'verified':False,'error':'manifest missing'})

    def test_doctor_keeps_recorded_build_source_distinct_from_live_git(self):
        identity={'kind':pv.KIND,'git_head':'a'*40}
        with mock.patch.object(p,'tool_manifest',return_value={'source_provenance':identity}), mock.patch.object(cli.platform,'platform',return_value='owned-test-host'):
            with mock.patch.object(cli.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout='10.0.0',stderr='')):
                report=cli.doctor()
        self.assertEqual(report['checks']['runtime_provenance'],{'verified':True,'identity':identity})


if __name__=='__main__':unittest.main()
