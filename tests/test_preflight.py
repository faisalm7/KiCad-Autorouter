import json
from pathlib import Path
import tempfile
import unittest
from autorouter import sexpr as sx
from autorouter.pipeline import preflight,Rejected

class PreflightTests(unittest.TestCase):
    def test_copper_identity_is_not_layer_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'board.kicad_pcb'
            # Copper layers may be power; user drawing layers can be signal.
            p.write_text('(kicad_pcb (version 20260206) (layers (0 "F.Cu" power) (2 "B.Cu" signal) (50 "User.1" signal)))')
            p.with_suffix('.kicad_pro').write_text('{}')
            self.assertTrue(preflight(p))
            t=sx.read(p);sx.one(t,'layers').append(['4','"In1.Cu"','signal']);sx.write(p,t)
            with self.assertRaisesRegex(Rejected,'2 or 4'):preflight(p)
