"""Authored temporary-source capture controls; no downloaded boards or workers."""
from contextlib import contextmanager
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments.licensed_acquisition_v2 import native_snapshot as capture
from experiments.licensed_acquisition_v1 import fetch as shared

NAMES=('.gitignore','LICENSE','README.md','board-3d.png','board.png',
       'fabrication-toolkit-options.json','fp-lib-table','paw3395.kicad_pcb',
       'paw3395.kicad_prl','paw3395.kicad_pro','paw3395.kicad_sch',
       'paw3395_pcb.pretty/PAW3395.kicad_mod','photo-1.jpg','photo-3950.jpg')

@contextmanager
def authored():
    # Fixed production census is intentional. One inert media payload supplies
    # the ~2MiB total; every other authored file is tiny. Nothing is parsed as PCB.
    files={name:('authored '+name+'\n').encode() for name in NAMES}
    files['paw3395.kicad_prl']=b'{"fixture":"PRL must survive byte-exact"}\n'
    files['photo-3950.jpg']=b'P'*(2163350-sum(len(raw) for name,raw in files.items() if name!='photo-3950.jpg'))
    rows=[{'source_path':name,'bytes':len(raw),'sha256':shared.sha(raw),
           'git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
          for name,raw in files.items()]
    with tempfile.TemporaryDirectory(prefix='paw-capture-owned-') as scratch:
        root=Path(scratch).resolve();source=root/'.data/expansion005/paw3395'
        for name,raw in files.items():
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        receipt=root/capture.RECEIPT;receipt.parent.mkdir(parents=True)
        data={'status':'acquired_unqualified','protocol_sha256':shared.profile('v2')['protocol_sha256'],
              'original_inputs_unchanged':True,'acquired_files':14,'acquired_bytes':2163350,'files':rows}
        receipt.write_text(json.dumps(data,sort_keys=True)+'\n')
        # Replace only fixed fixture protocol rows and receipt pin. All payload,
        # inventory, bounded reading, path and race checks execute real helpers.
        with mock.patch.object(shared,'load',return_value=({}, {}, rows)), \
             mock.patch.object(capture,'RECEIPT_SHA256',shared.sha(receipt.read_bytes())):
            yield root,source,files,rows,receipt

class PawNativeCaptureControls(unittest.TestCase):
    def test_full_original_packet_keeps_prl_media_and_paths_without_writing(self):
        with authored() as (root,source,files,_,receipt):
            before=shared.inventory(source);receipt_before=receipt.read_bytes()
            result=capture.capture(root)
            self.assertEqual(result,files)
            self.assertEqual((len(result),sum(map(len,result.values()))),(14,2163350))
            self.assertEqual(result['paw3395.kicad_prl'],files['paw3395.kicad_prl'])
            self.assertTrue({'board.png','board-3d.png','photo-1.jpg','photo-3950.jpg','fabrication-toolkit-options.json'}<=result.keys())
            self.assertFalse(any('_licenses/' in name for name in result))
            self.assertEqual(shared.inventory(source),before);self.assertEqual(receipt.read_bytes(),receipt_before)

    def test_missing_extra_symlink_and_same_size_payload_drift_refuse(self):
        for fault in ('missing','extra','symlink','payload'):
            with self.subTest(fault=fault),authored() as (root,source,files,_,_):
                path=source/'README.md'
                if fault=='missing':path.unlink()
                elif fault=='extra':(source/'unowned-extra').write_bytes(b'not approved')
                elif fault=='symlink':path.unlink();path.symlink_to(source/'LICENSE')
                else:path.write_bytes(b'X'*len(files['README.md']))
                with self.assertRaises(ValueError):capture.capture(root)

    def test_receipt_pin_and_prospective_git_blob_are_independent_guards(self):
        for fault in ('receipt','gitblob'):
            with self.subTest(fault=fault),authored() as (root,_,_,rows,receipt):
                if fault=='receipt':receipt.write_bytes(receipt.read_bytes()+b' ')
                else:rows[-1]['git_blob_sha1']='0'*40
                with self.assertRaisesRegex(ValueError,'receipt changed|payload hash'):capture.capture(root)

    def test_late_source_or_receipt_change_after_real_payload_validation_refuses(self):
        for fault in ('source','receipt'):
            with self.subTest(fault=fault),authored() as (root,source,files,rows,receipt):
                real_payload=shared.payload
                def after_validation(row,raw):
                    result=real_payload(row,raw)
                    if row is rows[-1]:
                        if fault=='source':(source/'paw3395.kicad_prl').write_bytes(b'X'*len(files['paw3395.kicad_prl']))
                        else:receipt.write_bytes(receipt.read_bytes()+b' ')
                    return result
                with mock.patch.object(shared,'payload',side_effect=after_validation),self.assertRaisesRegex(ValueError,'inventory changed|receipt changed during capture'):
                    capture.capture(root)

if __name__=='__main__':unittest.main()
