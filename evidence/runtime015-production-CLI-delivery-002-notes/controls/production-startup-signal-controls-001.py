"""Real owned sleep-child signals at the exact locked CliJob startup seam."""
from pathlib import Path
import importlib.util,os,signal,subprocess,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('bridge',ROOT/'.runs/run-native1007-delivery-004.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class StartupSignals(unittest.TestCase):
    def test_real_SIGINT_and_SIGTERM_before_Popen_assignment_are_forwarded_and_reaped(self):
        for requested in(signal.SIGINT,signal.SIGTERM):
            with self.subTest(signal=requested),tempfile.TemporaryDirectory(dir=ROOT/'.runs')as folder:
                job=module.CliJob();created=[];original=subprocess.Popen
                def startup(*args,**kwargs):
                    process=original(*args,**kwargs);created.append(process)
                    os.kill(os.getpid(),requested)
                    return process
                previous={sig:signal.getsignal(sig)for sig in(signal.SIGINT,signal.SIGTERM)}
                with module.cancellation_bridge(job)as(queued,live),patch.object(subprocess,'Popen',side_effect=startup):
                    row=job.run(['/bin/sleep','30'],Path(folder)/'sleep.log',timeout=5)
                    self.assertTrue(queued[0]);self.assertTrue(row['cancel_requested']);self.assertNotEqual(row['exit_code'],0)
                    with self.assertRaises(module.p.Rejected):live()
                self.assertEqual(len(created),1);self.assertIsNotNone(created[0].poll())
                self.assertEqual(previous,{sig:signal.getsignal(sig)for sig in previous})
if __name__=='__main__':unittest.main()
