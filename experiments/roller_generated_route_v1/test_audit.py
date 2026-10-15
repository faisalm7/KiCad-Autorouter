"""Regressions for demonstrated preimage and late-callback proof gaps."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,sexpr as sx
from experiments.roller_generated_route_v1 import driver as d,transport,run as outer
from experiments.roller_generated_route_v1.test_transport import fixture


class AuditControls(unittest.TestCase):
    def test_both_phase_preimages_reject_route_or_fault_replacement(self):
        original,*_=fixture()
        scene={'nets':[{'name':'A','width_nm':152400},{'name':'B','width_nm':152400}],
            'pads':[{'uuid':'00000000-0000-0000-0000-000000000010','net':'A','position_nm':[0,0],'copper_layers':['F.Cu']},
                    {'uuid':'00000000-0000-0000-0000-000000000011','net':'B','position_nm':[4000000,5000000],'copper_layers':['F.Cu']}]}
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.runs',prefix='roller-audit-unit-') as tmp:
            out=Path(tmp);sx.write(out/'imported.kicad_pcb',original)
            positive=p.transplant_routes(transport.task(original),original,protected=[],policy='exact_non_uuid_lock_position_v2')
            (out/'positive').mkdir();(out/'negative').mkdir()
            candidate=out/'positive/candidate.kicad_pcb';sx.write(candidate,positive)
            negative,control=transport.bridge(positive,scene)
            phases={name:{'directory':str(out/name),'candidate':str(candidate)} for name in ('positive','negative')}
            a=out/'positive/pre-refill.kicad_pcb';b=out/'negative/pre-refill.kicad_pcb'
            a.write_bytes(d.encoded(positive));b.write_bytes(d.encoded(negative))
            d.verify_phase_preimages(out,original,scene,phases,control)
            changed=copy.deepcopy(positive);sx.one(p.routes(changed)[0],'end')[1]='99'
            a.write_bytes(d.encoded(changed))
            with self.assertRaisesRegex(p.Rejected,'positive pre-refill'):d.verify_phase_preimages(out,original,scene,phases,control)
            a.write_bytes(d.encoded(positive));b.write_bytes(d.encoded(positive))
            with self.assertRaisesRegex(p.Rejected,'physical bridge'):d.verify_phase_preimages(out,original,scene,phases,control)
            b.write_bytes(d.encoded(negative));wrong={**control,'uuid':'00000000-0000-0000-0000-000000000099'}
            with self.assertRaisesRegex(p.Rejected,'physical bridge'):d.verify_phase_preimages(out,original,scene,phases,wrong)

    def test_final_tool_callback_mutations_are_seen_by_later_material_sweep(self):
        with tempfile.TemporaryDirectory(dir=d.ROOT/'.runs',prefix='roller-audit-unit-') as tmp:
            root=Path(tmp);here=root/'experiments/roller_generated_route_v1';here.mkdir(parents=True)
            source=root/'source';source.mkdir();(source/'creator.txt').write_text('authored source\n')
            (root/'toolchain.lock.json').write_text('{}\n');out=root/'output';out.mkdir()
            candidate=out/'candidate.kicad_pcb';candidate.write_text('authored original\n')
            tools={'implementation_sha256':{}}
            spec={'code_sha256':{},'source_inventory':d.inventory(source),'retained_inventories':{}}
            specraw=(json.dumps(spec)+'\n').encode();(here/'protocol.json').write_bytes(specraw)
            actor={'schema':1,'kind':'roller_generated_route_diagnostic','status':'completed','qualified':True,
                'charged_wall_seconds':1.0,'charged_full_cpu_seconds':1.0,'accepted':False,'production_support_qualified':False,'tools':tools,'protocol_sha256':d.digest(specraw),
                'runtime_source_sha256':{'experiments/roller_generated_route_v1/protocol.json':d.digest(specraw),
                    'toolchain.lock.json':p.sha(root/'toolchain.lock.json')},'completed_material':d.witness(out)}
            raw=(json.dumps(actor)+'\n').encode();(out/'result.json').write_bytes(raw)
            with patch.object(outer,'ROOT',root),patch.object(outer,'HERE',here),patch.object(d,'SOURCE',source):
                self.assertEqual(outer.audit_material(spec,specraw,out,raw,tools,tool_reader=lambda:tools),actor)
                for target in (candidate,out/'result.json',here/'protocol.json',source/'creator.txt',root/'toolchain.lock.json'):
                    with self.subTest(target=target.name):
                        before=target.read_bytes()
                        def callback():target.write_bytes(before+b'changed\n');return tools
                        try:
                            with self.assertRaises((ValueError,p.Rejected)):outer.audit_material(spec,specraw,out,raw,tools,tool_reader=callback)
                        finally:target.write_bytes(before)
                for field,value in (('qualified',1),('accepted',None),('production_support_qualified',0),('status','failed'),('schema',True),('charged_wall_seconds',float('nan')),('charged_full_cpu_seconds',True)):
                    with self.subTest(field=field):
                        wrong={**actor,field:value};bad=(json.dumps(wrong)+'\n').encode();(out/'result.json').write_bytes(bad)
                        with self.assertRaises(p.Rejected):outer.audit_material(spec,specraw,out,bad,tools,tool_reader=lambda:tools)
                (out/'result.json').write_bytes(raw)


if __name__=='__main__':unittest.main()
