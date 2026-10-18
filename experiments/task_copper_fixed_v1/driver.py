"""One bounded diagnostic using the shared routing/Native validation pipeline.

SPDX-License-Identifier: GPL-3.0-or-later
An alternate worker is deliberately NOT admitted by production proof readers.
No acceptance checker is replaced; publication must retain that refusal.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from autorouter import pipeline as p


class ProbeJob(p.Job):
    def native(self, name, action, board, output, *args):
        if action not in ('export', 'import'):
            return super().native(name, action, board, output, *args)
        return self.step(name, [self.native_python, Path(__file__).with_name('native_probe.py'),
                                action, board, output, *args])


if __name__ == '__main__':
    p.Job = ProbeJob
    result = p.route(sys.argv[1], sys.argv[2], seconds=90, keep_existing=True, adapter='both')
    summary = {k: result.get(k) for k in ('accepted', 'status', 'reason', 'native', 'metrics', 'candidate_sha256')}
    summary.update(diagnostic_only=True, production_admitted=False)
    print(json.dumps(summary, indent=2))
    # Return success for completed diagnostic execution, never product admission.
