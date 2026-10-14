"""Pure filesystem continuity regression; no mocked Native success or processes."""
import tempfile,unittest
from pathlib import Path
from autorouter import pipeline as p,preferences as pref
from experiments.native_feedback_engine_continuation_v1 import actor as d

class GroundFailureMaterial(unittest.TestCase):
    def test_incomplete_child_material_and_input_binding_cannot_change(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();source=root/'warm-source'/'owned.kicad_pcb';source.parent.mkdir();source.write_text('authored raw source\n')
            directory=root/'ground';directory.mkdir();(directory/'snapshot').mkdir();(directory/'snapshot'/source.name).write_bytes(source.read_bytes())
            preset={**pref.DEFAULTS,'scope':'selected_nets','nets':['GND'],'seconds':50,'profile':'completion-only','adapter':'both'}
            (directory/'routing-preferences.json').write_bytes(pref.snapshot(overrides={k:v for k,v in preset.items() if k!='schema'}))
            files=[directory/'candidate'/source.name,directory/'final-drc.json',directory/'final-drc-process.json',directory/'metrics.json']
            for file in files:file.parent.mkdir(exist_ok=True);file.write_text('authored raw incomplete evidence\n')
            hashes=p.tree_hash(source.parent);data={'source':str(source),'source_hashes':hashes,'accepted':False,'status':'rejected'};material=d.inventory(directory)
            def check():d._ground_readback(directory,data,source,hashes,preset,material)
            check()
            for file in files:
                original=file.read_bytes()
                for action in ('mutate','delete'):
                    with self.subTest(file=file.name,action=action):
                        if action=='mutate':file.write_bytes(original+b'changed')
                        else:file.unlink()
                        try:
                            with self.assertRaises((p.Rejected,FileNotFoundError)):check()
                        finally:file.write_bytes(original)
            data['source']='different source'
            with self.assertRaises(p.Rejected):check()
