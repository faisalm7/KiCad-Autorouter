"""Keep the already-qualified owned designs identical during factory changes."""
import hashlib
import unittest

from experiments.placement_native_proposal_v1 import multipad_fixture, ordinary_fixture


class PlacementFixtureIdentity(unittest.TestCase):
    def test_complete_owned_projects_keep_their_native_qualification_inputs(self):
        # Captured before the per-tree UUID-map optimization. A deliberate design
        # change requires new Native evidence, not silently updating these pins.
        expected = {
            'owned-placement-multipad.kicad_pcb': '4f72ef42dd51db8bd5fb265e28159cb02f8d71d51f70c969085f186d711ff7e1',
            'owned-placement-multipad.kicad_sch': 'e6fed6902827b0dce27b655ffd83fcd89e4eaff9b81a4cc6279b4064b384ab61',
            'owned-placement-multipad.kicad_pro': 'c74502eedb3af50bee84422ea4a33b1523443d777c3ec89f3b11cd261c9d2670',
            'owned-placement-multipad.kicad_prl': '7254c14a8e07658cd87adbefcf2e90f50768c8371990dcb5870062dee25a4e10',
            'owned-placement-ordinary.kicad_pcb': '4e981c7b6e8b80ac3caba0dcf6294c6bb0fb46b98a0912e74a0c19b5c5f17be9',
            'owned-placement-ordinary.kicad_sch': '79ed76c28d7969535966d52c89d22ab9786a2be5f97418b9f7aefda6a1e64c9c',
            'owned-placement-ordinary.kicad_pro': 'c0db040c62561fcfd0d53e091966b4021a5387f0edecf9177fdbd4757898f647',
            'owned-placement-ordinary.kicad_prl': 'eb4ba044056b137dc4a066d472dc902f64040a59f2d10a0ceb0586ed8b825a68',
        }
        actual = {name: hashlib.sha256(raw).hexdigest()
                  for factory in (multipad_fixture, ordinary_fixture)
                  for name, raw in factory.files().items()}
        self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
