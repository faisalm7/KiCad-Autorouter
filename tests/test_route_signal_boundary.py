"""Real subprocess signals at the public Route/shared-publication boundary.

No Native or engine runs: the inner task is replaced by a finite publication
seam. The real public wrapper and shared invalidation execute in a child.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from autorouter import pipeline as p


class RouteSignalBoundary(unittest.TestCase):
    def test_shared_native_job_propagates_cancellation_after_retaining_worker_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            job=p.Job(Path(directory).resolve()/'job',30,protect_local_settings=True)
            result=dict(status='cancelled',exit_code=-9,cleanup_complete=True)
            with patch.object(p,'run',return_value=result):
                with self.assertRaises(KeyboardInterrupt):job.step('engine',['deliberately-not-run'])
            self.assertEqual(job.steps[0]['status'],'cancelled')
            retained=json.loads((job.out/'engine-process.json').read_bytes())
            self.assertEqual(retained,job.steps[0]);self.assertTrue(retained['cleanup_complete'])

    def test_sigterm_after_positive_write_invalidates_direct_route_and_restores_handlers(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory).resolve()
            script=r'''
import json,signal,sys,time
from pathlib import Path
from autorouter import pipeline as p,floor_route as f
folder=Path(sys.argv[1]);before={s:signal.getsignal(s)for s in(signal.SIGINT,signal.SIGTERM)}
save=p.save_json
def pause(path,value):
    save(path,value)
    if value.get('accepted')is True:
        (folder/'ready').write_text('positive written, awaiting owned test signal')
        time.sleep(8)
def inner(*args,**kwargs):
    record=dict(accepted=True,status='routing_accepted')
    return f.publish(folder,record,lambda:None,lambda:None,lambda:10)
p.save_json=pause;p._route=inner
result=p.route(folder/'not-read.kicad_pcb',folder)
assert all(signal.getsignal(s)==v for s,v in before.items())
(folder/'returned.json').write_text(json.dumps(result))
'''
            child=subprocess.Popen([sys.executable,'-B','-c',script,str(folder)],cwd=p.c.ROOT,
                stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                deadline=time.monotonic()+6
                while not (folder/'ready').exists() and child.poll()is None and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue((folder/'ready').is_file(),'child did not reach controlled publication seam')
                os.kill(child.pid,signal.SIGTERM)
                stdout,stderr=child.communicate(timeout=4)
                self.assertEqual(child.returncode,0,(stdout,stderr))
                result=json.loads((folder/'result.json').read_bytes())
                self.assertFalse(result['accepted']);self.assertEqual(result['status'],'cancelled')
                self.assertEqual(result,json.loads((folder/'returned.json').read_bytes()))
                self.assertEqual(len(list(folder.glob('invalidated-result-*'))),1)
            finally:
                if child.poll()is None:child.kill();child.communicate()

    def test_direct_api_exception_restores_existing_handlers(self):
        before={s:signal.getsignal(s)for s in(signal.SIGINT,signal.SIGTERM)}
        with patch.object(p,'_route',side_effect=ValueError('controlled inner refusal')):
            with self.assertRaisesRegex(ValueError,'controlled inner refusal'):p.route('unread','uncreated')
        self.assertEqual(before,{s:signal.getsignal(s)for s in before})


if __name__=='__main__':unittest.main()
