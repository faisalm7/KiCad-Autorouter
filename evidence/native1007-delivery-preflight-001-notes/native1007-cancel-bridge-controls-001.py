"""Real local signals at CliJob's lock boundary; no child/Native execution."""
from pathlib import Path
import importlib.util, os, signal, sys, threading, unittest
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('enclosure003',ROOT/'.runs/run-native1007-delivery-003.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class SignalBridgeControls(unittest.TestCase):
    def test_signals_while_main_owns_job_lock_queue_without_deadlock(self):
        before={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM)}
        for sig in before:
            with self.subTest(signal=sig):
                job=module.CliJob()
                with module.cancellation_bridge(job) as (queued,live):
                    with job._lock:
                        os.kill(os.getpid(),sig)
                        self.assertTrue(queued[0])
                        with self.assertRaises(module.p.Rejected):live()
                self.assertTrue(job.cancel_requested)
        self.assertEqual(before,{sig:signal.getsignal(sig) for sig in before})
        self.assertFalse(any(t.name=='finite-cancel-forwarder' for t in threading.enumerate()))
    def test_queued_startup_request_reaches_process_assigned_under_lock(self):
        job=module.CliJob();sent=[];delivered=threading.Event()
        def send(sig):sent.append(sig);delivered.set()
        with module.cancellation_bridge(job) as (queued,live):
            with job._lock:
                os.kill(os.getpid(),signal.SIGTERM)
                self.assertTrue(queued[0])
                job.process=SimpleNamespace(poll=lambda:None,send_signal=send)
            self.assertTrue(delivered.wait(1.))
            with self.assertRaises(module.p.Rejected):live()
        self.assertEqual(sent,[signal.SIGINT])
        self.assertTrue(job.cancel_requested)

if __name__=='__main__':unittest.main()
