"""Real child imports through the shared Native job environment, without -B."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from autorouter import pipeline as p


class NativeBytecodeEnvironment(unittest.TestCase):
    def test_separate_python_worker_does_not_write_into_runtime_modules(self):
        with tempfile.TemporaryDirectory() as temporary:
            base=Path(temporary).resolve()
            with patch.dict(os.environ,{},clear=False):
                os.environ.pop('PYTHONDONTWRITEBYTECODE',None)
                job=p.Job(base/'job',10)
            for name,environment,writes in [('control',dict(job.env),True),('worker',job.env,False)]:
                work=base/name;work.mkdir();(work/'owned_probe.py').write_text('value=1\n')
                if writes:environment.pop('PYTHONDONTWRITEBYTECODE',None)
                process=subprocess.run([sys.executable,'-c','import owned_probe; assert owned_probe.value == 1'],
                    cwd=work,env=environment,capture_output=True,timeout=5)
                self.assertEqual(process.returncode,0,process.stderr)
                self.assertEqual((work/'__pycache__').exists(),writes)


if __name__=='__main__':unittest.main()
