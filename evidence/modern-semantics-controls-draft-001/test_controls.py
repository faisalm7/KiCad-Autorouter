"""Pure consistency controls; never substitutes for ROOT's native run."""
import copy,importlib.util,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('modern_semantics_draft',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

class Controls(unittest.TestCase):
    def test_owned_hole_originals_and_floors(self):
        source=d.sx.read(d.FLOOR);project=d.f.read_json(d.FLOOR.with_suffix('.kicad_pro'));before=copy.deepcopy(project)
        for gap in ('1.4','1.1'):
            raw,pro=d.hole_fixture(source,project,gap);tree=d.sx.parse(raw.decode());fps=d.sx.children(tree,'footprint')
            self.assertEqual(len(fps),2);self.assertEqual(pro['board']['design_settings']['rules'],before['board']['design_settings']['rules'])
            self.assertEqual(pro['board']['design_settings']['rule_severities']['hole_to_hole'],'warning')
            for fp in fps:
                pad=d.sx.one(fp,'pad');self.assertEqual(pad[2],'np_thru_hole');self.assertEqual(d.sx.one(pad,'drill'),['drill','1'])
        self.assertEqual(project,before)

    def test_actual_candidate_validator_stops_movement_before_native(self):
        raw,pro=d.hole_fixture(d.sx.read(d.FLOOR),d.f.read_json(d.FLOOR.with_suffix('.kicad_pro')),'1.4')
        with tempfile.TemporaryDirectory(dir=HERE) as temp:
            root=Path(temp);src=root/'source';src.mkdir();(src/'fixture.kicad_pcb').write_bytes(raw);d.p.save_json(src/'fixture.kicad_pro',pro)
            cand=root/'candidate';d.shutil.copytree(src,cand);board=cand/'fixture.kicad_pcb';tree=d.sx.read(board)
            d.sx.one(d.sx.children(tree,'footprint')[1],'at')[1]='23';d.sx.write(board,tree)
            class NeverNative:
                calls=0
                def drc(self,*a,**k):self.calls+=1;raise AssertionError('native forbidden')
            job=NeverNative()
            with self.assertRaisesRegex(d.p.Rejected,'immutable geometry changed'):
                d.p.validate_candidate(job,d.sx.read(src/'fixture.kicad_pcb'),board,d.inventory(src),[])
            self.assertEqual(job.calls,0)

    def test_warning_text_identity_and_other_critical_findings(self):
        raw=d.f.read_json(d.ROOT/'.runs/pic-severity-controls-002/board_edge_text/original-drc.json')
        ignored=sorted(r['key'] for r in raw['ignored_checks']);raw=copy.deepcopy(raw)
        next(r for r in raw['violations'] if r['type']=='text_on_edge_cuts')['severity']='warning'
        self.assertTrue(d.text_predicate(raw,'warning',True,{},ignored))
        self.assertFalse(d.text_predicate(raw,'warning',False,{},ignored))
        raw['violations'].append({'type':'hole_to_hole','severity':'warning','description':'injected critical residual','items':[]})
        self.assertFalse(d.text_predicate(raw,'warning',True,{},ignored))

    def test_shared_critical_warning_rejection_and_hole_pair_identity(self):
        row={'type':'hole_to_hole','severity':'warning','description':'Drilled hole too close to other hole (board setup constraints hole to hole clearance 0.2500 mm; actual 0.1000 mm)','items':[{'uuid':d.uid('pad0')},{'uuid':d.uid('pad1')}]}
        native={'opens':0,'blocking':0,'warnings':1,'exclusions':0,'findings':[row],'ignored_checks':[]}
        self.assertFalse(d.p.native_accepted(native));self.assertTrue(d.hole_predicate(native,True));self.assertFalse(d.hole_predicate(native,False))
        wrong=copy.deepcopy(native);wrong['findings'][0]['items'][1]['uuid']=d.uid('different')
        self.assertFalse(d.hole_predicate(wrong,True))

        for detail in ('Drilled hole too close to other hole (board setup constraints hole to hole clearance 0.2000 mm; actual 0.1000 mm)',
                       'Drilled hole too close to other hole (board setup constraints hole to hole clearance 0.2500 mm; actual 0.1500 mm)', 'missing dimensions'):
            wrong=copy.deepcopy(native);wrong['findings'][0]['description']=detail
            self.assertFalse(d.hole_predicate(wrong,True))

    def test_ignore_diagnostic_keeps_disabled_critical_policy(self):
        raw=d.f.read_json(d.ROOT/'.runs/pic-severity-controls-002/positive/original-drc.json')
        baseline=sorted(r['key'] for r in raw['ignored_checks']);raw=copy.deepcopy(raw)
        raw['ignored_checks'].append({'key':'text_on_edge_cuts','description':'synthetic pure suppression control'})
        self.assertTrue(d.text_predicate(raw,'ignore',False,{},baseline))
        self.assertTrue(d.text_predicate(raw,'ignore',True,{},baseline))
        self.assertFalse(d.p.native_accepted(d.checks.summary(raw)))
        raw['violations'].append({'type':'hole_to_hole','severity':'warning','description':'other critical finding','items':[]})
        self.assertFalse(d.text_predicate(raw,'ignore',True,{},baseline))

    def test_cancellation_handler_spans_publication_and_restores(self):
        before={sig:d.signal.getsignal(sig) for sig in (d.signal.SIGINT,d.signal.SIGTERM)}
        def actual_body(output,*,run_native):
            self.assertTrue(run_native)
            def publisher():
                for sig in before:
                    handler=d.signal.getsignal(sig);self.assertIsNot(handler,before[sig])
                    with self.assertRaises(KeyboardInterrupt):handler(sig,None)
                raise RuntimeError('deliberate publisher exception')
            publisher()
        with patch.object(d,'_experiment',actual_body):
            with self.assertRaisesRegex(RuntimeError,'deliberate publisher exception'):d.experiment('unused',run_native=True)
        self.assertEqual({sig:d.signal.getsignal(sig) for sig in before},before)

if __name__=='__main__':unittest.main()
