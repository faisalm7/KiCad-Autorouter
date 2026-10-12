"""Pure recipe/predicate falsifiers; these are not native qualification."""
import copy,json,unittest
from fractions import Fraction
import driver as d
import clearance_controls as cc
import fixture,recipes,checks
from test_controls import model,native_report,summary

class ClearanceControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original=d.sx.read(d.SOURCE);cls.project=d.read(d.SOURCE.with_suffix('.kicad_pro'))
    def scene(self,case):return cc.prepare(self.original,case,'front0')[1]
    def test_exact_pair_deltas_and_analytic_capsule(self):
        trees={};scenes={}
        for case,(gap,override,_) in cc.CASES.items():
            raw,s=cc.prepare(self.original,case,'front0');trees[case]=d.sx.parse(raw.decode());scenes[case]=s
            target=next(r for r in s['pads'] if r['id']=='CONCAVE');track=s['tracks'][1]
            self.assertEqual(recipes.segment_gap2(track['start'],track['end'],target['polygon']),Fraction((gap+250000)**2))
            self.assertEqual(d.sx.one(trees[case],'setup'),d.sx.one(self.original,'setup'))
            locals_=[d.sx.children(fp,'clearance') for fp in d.sx.children(trees[case],'footprint')]
            self.assertEqual(sum(map(len,locals_)),0 if override is None else 1)
        a=copy.deepcopy(trees['override_260_positive']);b=trees['class_260_negative']
        for fp in d.sx.children(a,'footprint'):
            for node in d.sx.children(fp,'clearance'):fp.remove(node)
        self.assertEqual(a,b)
        for akey,bkey in [('class_290_positive','class_260_negative'),('override_260_positive','override_240_negative')]:
            a=copy.deepcopy(trees[akey]);b=trees[bkey]
            d.sx.one(d.p.routes(a)[1],'end')[:]=d.sx.one(d.p.routes(b)[1],'end')
            self.assertEqual(a,b)
    def test_committed_protocol_and_scope(self):
        self.assertEqual(d.protocol(),d.read(d.HERE/'PROTOCOL.json'))
        self.assertEqual(d.protocol(cc.SUITE),d.read(d.HERE/'CLEARANCE_PROTOCOL.json'))
        with self.assertRaises(ValueError):cc.prepare(self.original,'class_290_positive','back90')
        with self.assertRaises(ValueError):d.protocol('unknown')
    def test_geometry_observer_checks_power_class_without_invented_width_minimum(self):
        scene=self.scene('override_260_positive');base=copy.deepcopy(scene)
        for row in base['pads']+base['tracks']:
            if row['net']=='VCC':row['net']='CONTACT'
        n,c,raw=model(base,self.project)
        n=json.loads(json.dumps(n).replace('CONTACT','VCC'));c=json.loads(json.dumps(c).replace('CONTACT','VCC'));raw=raw.replace(b'CONTACT',b'VCC')
        power=next(row for row in n['nets'] if row['name']=='VCC');power.update({'class':'POWER','width_nm':800000,'clearance_nm':280000})
        self.assertFalse(cc.observe(n,c,raw,scene,self.project)['default_only_settings_observed'])
        for field,value in [('class','Default'),('width_nm',500000),('clearance_nm',250000)]:
            changed=copy.deepcopy(n);next(row for row in changed['nets'] if row['name']=='VCC')[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):cc.observe(changed,c,raw,scene,self.project)
    def report(self,case):
        scene=self.scene(case)
        raw=native_report('positive' if cc.CASES[case][2] else 'foreign_intrusion',scene,list(d.OBSERVED_IGNORED))
        return scene,raw
    def test_strict_clearance_pair_and_positive(self):
        for case in cc.CASES:
            scene,raw=self.report(case);self.assertTrue(cc.predicate(case,summary(raw),raw,scene,list(d.OBSERVED_IGNORED))[0])
        for mutation in ('wrong_pair','wrong_type','warning','excluded','duplicate','none','open','unknown','ignore'):
            case='class_260_negative';scene,raw=self.report(case);hit=raw['violations'][0]
            if mutation=='wrong_pair':hit['items'][0]['uuid']='other'
            if mutation=='wrong_type':hit['type']='solder_mask_bridge'
            if mutation=='warning':hit['severity']='warning'
            if mutation=='excluded':hit['excluded']=True
            if mutation=='duplicate':raw['violations'].append(copy.deepcopy(hit))
            if mutation=='none':raw['violations']=[]
            if mutation=='open':raw['unconnected_items'].append(copy.deepcopy(hit))
            if mutation=='unknown':raw['violations'].append({'type':'unknown','severity':'warning','items':[]})
            if mutation=='ignore':raw['ignored_checks'].append({'key':'clearance'})
            with self.subTest(mutation=mutation):self.assertFalse(cc.predicate(case,summary(raw),raw,scene,list(d.OBSERVED_IGNORED))[0])

if __name__=='__main__':unittest.main()
