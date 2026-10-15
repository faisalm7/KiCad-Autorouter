"""Real-file resource and race controls for the shared bounded reader; no Native."""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from autorouter import pipeline as p, placement_clearance as pc


class BoundedFileReadTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.path = self.root / 'owned'

    @contextmanager
    def observed_reads(self, *, before=None, after=None):
        original = pc.os.fdopen
        requests = []

        class ObservedFile:
            def __init__(self, handle): self.handle = handle
            def __enter__(self): return self
            def __exit__(self, *args): return self.handle.__exit__(*args)
            def fileno(self): return self.handle.fileno()
            def read(self, size):
                requests.append(size)
                if before is not None: before(size)
                raw = self.handle.read(size)
                if after is not None: after()
                return raw

        def fdopen(*args, **kwargs):
            return ObservedFile(original(*args, **kwargs))

        with patch.object(pc.os, 'fdopen', fdopen):
            yield requests

    def test_request_uses_observed_size_plus_one_for_large_and_exact_limits(self):
        for raw, limit in ((b'', 384 * 1024**2), (b'abc', 384 * 1024**2),
                           (b'abc', 3), (b'', 0)):
            with self.subTest(length=len(raw), limit=limit):
                self.path.write_bytes(raw)
                # Assert before delegating so the old defect does not allocate the ceiling.
                with self.observed_reads(before=lambda size: self.assertEqual(size, len(raw) + 1)) as requests:
                    self.assertEqual(pc.read_bytes(self.path, limit), raw)
                self.assertEqual(requests, [len(raw) + 1])

    def test_inventory_remaining_ceiling_does_not_become_per_file_read_request(self):
        payloads = {'a': b'abc', 'b': b'12345'}
        for name, raw in payloads.items(): (self.root / name).write_bytes(raw)
        with self.observed_reads(before=lambda size: self.assertLessEqual(size, 6)) as requests:
            actual = pc.inventory(self.root, max_bytes=384 * 1024**2)
        self.assertEqual(actual, {name: hashlib.sha256(raw).hexdigest() for name, raw in payloads.items()})
        self.assertCountEqual(requests, [4, 6])

    def test_growth_within_ceiling_during_read_is_rejected(self):
        self.path.write_bytes(b'abc')
        def grow(_):
            with self.path.open('ab') as handle: handle.write(b'd')
        with self.observed_reads(before=grow), self.assertRaisesRegex(p.Rejected, 'changed or exceeded'):
            pc.read_bytes(self.path, 100)
        self.assertEqual(self.path.read_bytes(), b'abcd')

    def test_truncation_during_read_is_rejected(self):
        self.path.write_bytes(b'abc')
        with self.observed_reads(before=lambda _: self.path.write_bytes(b'a')), self.assertRaisesRegex(p.Rejected, 'changed or exceeded'):
            pc.read_bytes(self.path, 100)
        self.assertEqual(self.path.read_bytes(), b'a')

    def test_same_size_late_metadata_change_is_rejected(self):
        self.path.write_bytes(b'abc')
        initial = self.path.stat()
        def change():
            self.path.write_bytes(b'xyz')
            os.utime(self.path, ns=(initial.st_atime_ns, initial.st_mtime_ns + 1_000_000_000))
        with self.observed_reads(after=change), self.assertRaisesRegex(p.Rejected, 'changed or exceeded'):
            pc.read_bytes(self.path, 100)
        self.assertEqual(self.path.read_bytes(), b'xyz')

    def test_oversize_descriptor_is_rejected_before_any_read(self):
        self.path.write_bytes(b'abc')
        with self.observed_reads() as requests, self.assertRaisesRegex(p.Rejected, 'bounded regular'):
            pc.read_bytes(self.path, 2)
        self.assertEqual(requests, [])
