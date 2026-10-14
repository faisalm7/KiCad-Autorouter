"""Pure retained-producer controls; no Native or old code execution."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from autorouter import pipeline as p, sexpr as sx
from tests.test_legacy_zone import fixture, pad


class RetainedLegacyZoneControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()
        base=p.c.ROOT
        names=('legacy_zone','board_floor','floor_route','placement_clearance','sexpr','pipeline')
        (self.root/'autorouter').mkdir()
        for name in names:shutil.copyfile(base/'autorouter'/(name+'.py'),self.root/'autorouter'/(name+'.py'))
        self.patch=mock.patch.object(p.c,'ROOT',self.root);self.patch.start();self.addCleanup(self.patch.stop)
        self.directory=self.root/'.runs/owned/route';self.directory.mkdir(parents=True)
        self.board,self.project=fixture();self.candidate=self.directory/'owned.kicad_pcb'
        sx.write(self.candidate,self.board);self.candidate.with_suffix('.kicad_pro').write_text(json.dumps(self.project))
        self.current=p.legacy_zone_evidence(self.board,self.candidate)
        self.artifact=self.directory/'legacy-zone-witness.json'
        self.code=self.directory.parent/'code';self.code.mkdir()
        self.record=copy.deepcopy(self.current);self.pins={}
        for name in self.current['implementation_sha256']:
            raw=(self.root/name).read_bytes()+b'\n# Authored retained producer; never executed.\n'
            (self.code/Path(name).name).write_bytes(raw)
            self.pins[name]=hashlib.sha256(raw).hexdigest()
        self.record['implementation_sha256']=dict(self.pins);self.save()

    def save(self):p.save_json(self.artifact,self.record)
    def check(self,**kwargs):
        p.check_legacy_zone_evidence(self.directory,self.board,self.candidate,implementation=self.pins,**kwargs)

    def test_older_captured_producer_rederives_current_semantics(self):
        self.check()
        self.assertEqual(json.loads(self.artifact.read_text()),self.record)
        direct=self.directory/'code';self.code.rename(direct);self.code=direct;self.check()

    def test_default_strict_and_explicit_current_behavior_unchanged(self):
        with self.assertRaisesRegex(p.Rejected,'changed'):
            p.check_legacy_zone_evidence(self.directory,self.board,self.candidate)
        self.record=copy.deepcopy(self.current);self.save();shutil.rmtree(self.code)
        p.check_legacy_zone_evidence(self.directory,self.board,self.candidate)
        p.check_legacy_zone_evidence(self.directory,self.board,self.candidate,
                                     implementation=self.current['implementation_sha256'])

    def test_missing_tampered_or_mixed_captured_files_refuse(self):
        target=self.code/'board_floor.py';raw=target.read_bytes()
        for changed in (None,raw+b'# tamper\n',(self.root/'autorouter/board_floor.py').read_bytes()):
            with self.subTest(changed=changed is None):
                if changed is None:target.unlink()
                else:target.write_bytes(changed)
                with self.assertRaisesRegex(p.Rejected,'producer'):self.check()
                target.write_bytes(raw)

    def test_supplied_pin_key_type_and_mixed_metadata_refuse(self):
        name='autorouter/board_floor.py'
        bad=[{},{**self.pins,name:self.current['implementation_sha256'][name]},
             {**self.pins,name:True}]
        for pins in bad:
            with self.subTest(pins=pins),self.assertRaisesRegex(p.Rejected,'provenance'):
                p.check_legacy_zone_evidence(self.directory,self.board,self.candidate,implementation=pins)
        with self.assertRaisesRegex(p.Rejected,'changed'):
            p.check_legacy_zone_evidence(self.directory,self.board,self.candidate,implementation=None)
        for pins in ({k:v for k,v in self.pins.items() if k!=name},{**self.pins,'outside.py':'0'*64}):
            self.record['implementation_sha256']=pins;self.save()
            with self.assertRaisesRegex(p.Rejected,'provenance'):self.check()

    def test_semantic_metadata_and_false_pad_witness_refuse(self):
        baseline=copy.deepcopy(self.record)
        edits=[lambda r:r.__setitem__('schema',True),lambda r:r.__setitem__('native_enforcement_claimed',0),
               lambda r:r.__setitem__('project_sha256','0'*64),lambda r:r.__setitem__('candidate_sha256','0'*64),
               lambda r:r.__setitem__('policy','other'),
               lambda r:r['witness']['zones'][0]['pad_witness'].__setitem__('pad_uuid','0'*36)]
        for index,edit in enumerate(edits):
            self.record=copy.deepcopy(baseline);edit(self.record);self.save()
            with self.subTest(index=index),self.assertRaisesRegex(p.Rejected,'changed'):self.check()

    def test_changed_pad_project_and_deleted_witness_refuse(self):
        changed=copy.deepcopy(self.board);sx.one(pad(changed),'net')[:]=['net','2','"PADLESS"'];sx.write(self.candidate,changed)
        with self.assertRaises(p.Rejected):self.check()
        sx.write(self.candidate,self.board)
        project=copy.deepcopy(self.project);project['board']['design_settings']['rule_severities']['zone_has_empty_net']='warning'
        self.candidate.with_suffix('.kicad_pro').write_text(json.dumps(project))
        with self.assertRaises(p.Rejected):self.check()
        self.candidate.with_suffix('.kicad_pro').write_text(json.dumps(self.project));self.artifact.unlink()
        with self.assertRaisesRegex(p.Rejected,'missing or changed'):self.check()

    def test_symlink_hardlink_and_ambiguous_capture_refuse(self):
        target=self.code/'sexpr.py';raw=target.read_bytes();other=self.root/'aliased.py';other.write_bytes(raw)
        target.unlink();target.symlink_to(other)
        with self.assertRaises(p.Rejected):self.check()
        target.unlink();os.link(other,target)
        with self.assertRaises(p.Rejected):self.check()
        target.unlink();target.write_bytes(raw)
        (self.directory/'code').mkdir()
        with self.assertRaisesRegex(p.Rejected,'ambiguous'):self.check()

    def test_noncanonical_outside_and_code_directory_alias_refuse(self):
        for directory in (self.directory/'..'/'route',self.root):
            with self.subTest(directory=str(directory)),self.assertRaises(p.Rejected):
                p.check_legacy_zone_evidence(directory,self.board,self.candidate,implementation=self.pins)
        moved=self.root/'moved-code';self.code.rename(moved);self.code.symlink_to(moved,target_is_directory=True)
        with self.assertRaises(p.Rejected):self.check()

    def test_oversized_producer_refuses_even_with_matching_supplied_pin(self):
        raw=b'#'+b' '*1024*1024;name='autorouter/sexpr.py';(self.code/'sexpr.py').write_bytes(raw)
        self.pins[name]=hashlib.sha256(raw).hexdigest();self.record['implementation_sha256']=dict(self.pins);self.save()
        with self.assertRaises(p.Rejected):self.check()


if __name__=='__main__':unittest.main()
