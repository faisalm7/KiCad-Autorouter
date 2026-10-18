"""Cross-root composition controls; authored workers are never Native evidence."""
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, floor_route as f, local_settings as local, handoff as h


@unittest.skipUnless(hasattr(os, 'chflags') and hasattr(stat, 'UF_IMMUTABLE'),
                     'actual owned Mac PRL metadata control')
class FinalEventGroupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve(); self.packets = []; self.workers = {}; self.paths = []
        for index in range(3):
            root = self.base / str(index); root.mkdir(); inputs = root / 'input'; inputs.mkdir()
            board = inputs / 'owned.kicad_pcb'; board.write_bytes(b'(kicad_pcb)\n')
            prl = board.with_suffix('.kicad_prl'); prl.write_bytes(b'{"owned":"unchanged"}\n')
            self.paths.append(prl); owner = {}; h.capture_destination(owner, root)
            before = p.tree_hash(inputs)
            with local.preserve(prl, root, owner) as event: pass
            argv = [str(p.c.CLI), 'pcb', 'drc', str(board)]
            if index == 1: argv = [*f.SANDBOX, *argv]
            process = dict(name='final-drc', cwd=str(root), argv=argv, cleanup_complete=True,
                local_settings_policy=local.JOB_POLICY, local_settings_protection=event)
            binding = dict(input=str(board), saved=False, before=before, local_settings_policy=local.JOB_POLICY)
            p.save_json(root / 'final-drc-binding.json', binding)
            self.workers[root] = process; self.packets.append((root, dict(steps=[process], native={})))
        self.addCleanup(self.restore)

    def restore(self):
        for path in self.paths:
            if path.exists(): os.chflags(path, 0, follow_symlinks=False)

    def replay(self, fault=False, *, pairs=()):
        collected = []
        def process(root, data, name, argv, *, allowed):
            self.assertEqual(allowed, (0, 5)); self.assertEqual(argv, self.workers[root]['argv'])
            collected.append(root)
            if fault and root == self.packets[1][0]:
                os.chflags(self.paths[0], stat.UF_IMMUTABLE, follow_symlinks=False)
            return self.workers[root]
        with patch.object(f, 'process_check', side_effect=process):
            local.check_final_events(self.packets, p.c.CLI, pairs=pairs)
        return collected

    def test_healthy_shared_guards_collect_all_workers_and_keep_optional_plot_pairs(self):
        root, data = self.packets[0]
        binding = f.read_json(root / 'final-drc-binding.json')
        with patch.object(local, 'check_event', wraps=local.check_event) as replayed:
            self.assertEqual(self.replay(pairs=[(root, binding, data['steps'][0])]),
                             [root for root, _ in self.packets])
        self.assertEqual(replayed.call_count, 4)
        self.assertTrue(all(path.stat().st_flags == 0 for path in self.paths))

    def test_later_root_callback_cannot_escape_earlier_roots_final_metadata_check(self):
        before = [path.read_bytes() for path in self.paths]
        with self.assertRaisesRegex(p.Rejected, 'flags'):
            self.replay(fault=True)
        self.assertEqual(self.paths[0].stat().st_flags, stat.UF_IMMUTABLE)
        self.assertEqual([path.read_bytes() for path in self.paths], before)


if __name__ == '__main__': unittest.main()
