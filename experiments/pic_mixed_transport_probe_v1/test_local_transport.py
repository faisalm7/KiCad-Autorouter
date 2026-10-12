"""Saved-byte and synthetic mutation checks; no KiCad/JVM work."""
import copy,json,unittest,tempfile,hashlib
from unittest.mock import patch
from contextlib import ExitStack
from pathlib import Path
import test_draft as base
import transport

class LocalTransport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base.Pure.setUpClass()
        cls.path=base.ROOT/'evidence/pic-mixed-transport-probe-005'
        read=lambda name:json.loads((cls.path/name).read_text())
        cls.original=read('observations.json');cls.clearance=read('clearance-observation.json')
        _,cls.expected=transport.derive((cls.path/'native.dsn').read_bytes(),read('context.json'),read('custom.json'),base.Pure.notes)
        cls.project=json.loads((base.ROOT/'.data/boards/kicad-pic-programmer/pic_programmer.kicad_pro').read_text())
    def synthetic(self):
        result=copy.deepcopy(self.original);before=transport.validate(result,self.expected)
        for row,comparison in zip(result['cases'],before):
            state=row['state'];row['state_before_local']=copy.deepcopy(state)
            ids={v for body in comparison['bodies'] for v in (body['pin_id'],body['area_id'])}
            state['clearance_class_names'].append('native_local_250');state['census']['clearance_classes']=6
            for key in ('items','pins','areas'):
                for item in state[key]:
                    if item['id'] in ids:item['clearance_class_index']=5
            old={(c['a'],c['b'],c['layer']):c for c in state['matrix']};matrix=[]
            scale=state['board_units_per_um'];margin=state['clearance_safety_margin_board_units']
            for a in range(6):
                for b in range(6):
                    for layer in (0,1):
                        if (a,b,layer) in old:matrix.append(old[(a,b,layer)]);continue
                        raw=0 if 0 in (a,b) else 250*scale
                        matrix.append({'a':a,'b':b,'layer':layer,'raw_board_units':raw,'raw_um':raw/scale,
                            'compensated_board_units':raw+margin,'compensated_um':(raw+margin)/scale})
            state['matrix']=matrix
            row['local_override']={'class_name':'native_local_250','class_index':5,'changed_item_ids':sorted(ids),
                'tree_refresh_completed':True,'tree_entries_valid':True,
                'tree_entry_checks':[{'id':i,'valid':True} for i in sorted(ids)],
                'raw_row':[{'other_class':c,'layer':l,'raw_board_units':0 if c==0 else 250*scale,'raw_um':0 if c==0 else 250}
                           for c in range(6) for l in (0,1)],
                'targets':[{'reference':w['reference'],'number':w['number'],'net':w['net'],
                    'pin_id':b['pin_id'],'area_id':b['area_id'],'original_pin_class':b['pin_class'],'original_area_class':b['area_class'],
                    'preserved_board_edge_raw_board_units':[old[b['pin_class'],4,l]['raw_board_units'] for l in (0,1)]}
                    for w,b in zip(self.expected['areas'],comparison['bodies'])]}
        return result
    def test_exact_finite_synthetic_change_not_rule_equivalence(self):
        result=transport.validate_local(self.synthetic(),self.expected)
        self.assertTrue(all(row['observed'] for row in result))
        self.assertTrue(all(row['pairwise_rule_equivalence_qualified'] is False for row in result))
    def test_unchanged_old_geometry_or_matrix_cannot_masquerade_as_local(self):
        for mutation in ('one_pin','one_body','extra_item','old_matrix','asymmetric','null','margin','width','plane','geometry','tree','ids','both_contact_loss','census','failed_tree_entry','wrong_target_audit','wrong_row_audit'):
            data=self.synthetic();row=data['cases'][0];state=row['state'];ids=set(row['local_override']['changed_item_ids'])
            if mutation=='one_pin':next(p for p in state['pins'] if p['id'] in ids)['clearance_class_index']=3
            if mutation=='one_body':next(p for p in state['areas'] if p['id'] in ids)['clearance_class_index']=3
            if mutation=='extra_item':next(p for p in state['items'] if p['id'] not in ids)['clearance_class_index']=5
            if mutation in ('old_matrix','asymmetric','null','margin'):
                a,b={'old_matrix':(1,1),'asymmetric':(5,3),'null':(5,0),'margin':(5,1)}[mutation]
                cell=next(c for c in state['matrix'] if c['a']==a and c['b']==b and c['layer']==0)
                if mutation=='margin':cell['compensated_board_units']+=10;cell['compensated_um']+=1
                else:cell['raw_board_units']+=10;cell['raw_um']+=1
            if mutation=='width':state['nets'][0]['width_um']=[10,10]
            if mutation=='plane':next(p for p in state['areas'] if p['id'] not in ids)['obstacle']=not row['requested_obstacle']
            if mutation=='geometry':next(p for p in state['pins'] if p['id'] in ids)['bounds_um'][0]+=1
            if mutation=='tree':row['local_override']['tree_entries_valid']=False
            if mutation=='ids':row['local_override']['changed_item_ids'].pop()
            if mutation=='census':state['census']['clearance_classes']=5
            if mutation=='failed_tree_entry':row['local_override']['tree_entry_checks'][0]['valid']=False
            if mutation=='wrong_target_audit':row['local_override']['targets'][0]['pin_id']=-1
            if mutation=='wrong_row_audit':row['local_override']['raw_row'][3]['raw_um']=280
            if mutation=='both_contact_loss':
                for state_ in (state,row['state_before_local']):
                    for group in ('items','pins','areas'):
                        for item in state_[group]:
                            if item['id'] in ids:item['contacts']=[]
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,KeyError,TypeError)):transport.validate_local(data,self.expected)
    def test_original_local_basis_is_narrow_and_exact(self):
        self.assertEqual(len(transport.local_override_basis(self.clearance,self.project)['targets']),2)
        for key,value in [('pad_local',250000),('footprint_local',280000),('pad_override',None)]:
            changed=copy.deepcopy(self.clearance)
            for phase in changed:
                row=next(r for r in changed[phase]['rows'] if r['reference']=='JP1' and r['number']=='1')
                row[key]['value_nm']=value
            with self.subTest(key=key),self.assertRaises(ValueError):transport.local_override_basis(changed,self.project)
        changed=copy.deepcopy(self.project);changed['board']['design_settings']['rules']['min_clearance']=0.3
        with self.assertRaises(ValueError):transport.local_override_basis(self.clearance,changed)
    def test_changes_during_cached_scan_invalidate_current_material_witness(self):
        d=base.driver
        with tempfile.TemporaryDirectory(dir=base.ROOT/".runs",prefix="local-witness-test-") as tmp:
            root=Path(tmp);helper=root/'helper';tool=root/'tool';original=root/'original'
            cached=root/'.runs/pic-mixed-transport-probe-005';cached.mkdir(parents=True);(cached/'observed').write_text('fixed')
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            protocol={'tools':{'python':{'path':str(tool),'bytes':1}},'basis':{},'mode':'local250','reuse_native':'.runs/pic-mixed-transport-probe-005'}
            inventory=d.inventory
            for target in (helper,tool,original):
                for path in (helper,tool,original):path.write_bytes(b'A')
                with ExitStack() as stack:
                    stack.enter_context(patch.object(d,'ROOT',root));stack.enter_context(patch.object(d,'source_paths',lambda:[helper]))
                    stack.enter_context(patch.object(d.base,'head_witness',lambda:{'head':'0'*40}))
                    stack.enter_context(patch.object(d.original,'source_binding',lambda:({'original':sha(original)},1)))
                    baseline=d.runtime(protocol)
                    def changed_inventory(path):
                        result=inventory(path)
                        if path==cached:target.write_bytes(b'B')
                        return result
                    stack.enter_context(patch.object(d,'inventory',changed_inventory))
                    self.assertNotEqual(baseline,d.runtime(protocol))

if __name__=='__main__':unittest.main()
