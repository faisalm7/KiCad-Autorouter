"""Retained local baseline + explicitly synthetic selective observations; no JVM."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'autorouter/runner.py').is_file())
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('selective_comparison',HERE/'selective.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        basis=ROOT/'evidence/pic-local-clearance-transport-001'
        cls.baseline=json.loads((basis/'observations.json').read_text())
        cls.expected=json.loads((basis/'expectations.json').read_text())
        c.transport.validate_local(cls.baseline,cls.expected)
        writer=json.loads((ROOT/'evidence/pic-custom-ses-roundtrip-001/observations.json').read_text())
        cls.geometry=writer['cases'][0]['route_geometry']
        c.ses_checks.geometry_check(cls.geometry,cls.baseline['cases'][0]['state'])

    def observation(self):
        row=copy.deepcopy(self.baseline['cases'][0]);state=row['state']
        targets={x['area_id'] for x in row['local_override']['targets']}
        # Actual retained imported route geometry; selective predicates below remain synthetic.
        geometry=copy.deepcopy(self.geometry);traces=geometry['traces'];vias=geometry['vias']
        for field in ('route_geometry_before_local','route_geometry','route_geometry_after_selective'):row[field]=copy.deepcopy(geometry)
        after=copy.deepcopy(state);after['ignore_conduction']=False
        for area in after['areas']:
            if area['id'] in targets:
                area['obstacle']=True
                for p in area['foreign_pin_predicates']:p['trace_obstacle']=True
        row['state_after_selective']=after
        row['settings_after_selective']=copy.deepcopy(row['settings_after'])
        row['selective_override']={'changed_area_ids':sorted(targets),'global_ignore_before':True,
            'global_ignore_after':False,'tree_refresh_completed':True}
        for phase,st in (('predicates_before',state),('predicates_after',after)):
            area_records=[];queries=[]
            for area in st['areas']:
                rs=[]
                for kind,routes in (('trace',traces),('via',vias)):
                    for r in routes:
                        same=bool(set(area['nets'])&set(r['nets']));ob=area['obstacle'] and not same
                        rs.append({'id':r['id'],'kind':kind,'net':r['nets'][0],'same_net':same,
                            'shares_layer':area['first_layer']<=r['last_layer'] and r['first_layer']<=area['last_layer'],
                            'item_obstacle':ob,'trace_obstacle':ob,'drillable':not ob})
                area_records.append({'id':area['id'],'filled':True,'obstacle':area['obstacle'],'routes':rs})
            for trace in traces:
                raw=sorted(a['id'] for a in st['areas'])
                filtered=sorted(a['id'] for a in st['areas'] if a['obstacle'] and not set(a['nets'])&set(trace['nets']))
                queries.append({'id':trace['id'],'shape_count':1,'tree_trace_check_clear':not bool(filtered),
                    'raw_overlap_ids':raw,'flag_filtered_overlap_ids':filtered})
            row[phase]={'area_count':3,'route_count':len(traces)+len(vias),'item_count':len(state['items']),
                'areas':area_records,'trace_queries':queries,'tree_entries':[{'id':x['id'],'valid':True} for x in state['items']],
                'all_tree_entries_valid':True,'trace_shape_count':len(traces)}
        return {'schema':1,'mode':'selective_local250','routing_executed':False,'ses_executed':False,'case':row}

    def check(self,o=None,b=None):return c.compare(o or self.observation(),self.expected,b or self.baseline)
    def test_positive_is_only_representation(self):
        result=self.check();self.assertTrue(result['selective_transition_verified'])
        self.assertFalse(result['routing_accepted']);self.assertFalse(result['native_route_survival_qualified'])
    def test_original_plane_and_unrelated_material_rejected(self):
        changes=[lambda r:next(a for a in r['state_after_selective']['areas'] if a['nets']==['GND']).update(obstacle=True),
          lambda r:r['state_after_selective']['matrix'][0].update(raw_um=1),
          lambda r:r['state_after_selective']['nets'][0].update(contains_plane=not r['state_after_selective']['nets'][0]['contains_plane']),
          lambda r:r['state_after_selective']['items'][0].update(fixed='SYSTEM_FIXED'),
          lambda r:r['route_geometry_after_selective']['traces'][0]['corners_board_integer'][0].__setitem__(0,100)]
        for change in changes:
            with self.subTest(change=change):
                o=self.observation();prior=c.canonical(o);change(o['case']);self.assertNotEqual(prior,c.canonical(o),'negative recipe must mutate bytes')
                with self.assertRaises(ValueError):self.check(o)
    def test_target_scope_refresh_and_full_entries_rejected(self):
        changes=[lambda r:r['selective_override'].update(changed_area_ids=[2,1221]),
          lambda r:next(a for a in r['state_after_selective']['areas'] if a['id']==r['selective_override']['changed_area_ids'][0]).update(obstacle=False),
          lambda r:r['selective_override'].update(tree_refresh_completed=False),
          lambda r:r['predicates_after']['tree_entries'].pop(),
          lambda r:r['predicates_after']['tree_entries'][0].update(valid=False),
          lambda r:r['predicates_after']['areas'][0].update(filled=False)]
        for change in changes:
            with self.subTest(change=change):
                o=self.observation();prior=c.canonical(o);change(o['case']);self.assertNotEqual(prior,c.canonical(o),'negative recipe must mutate bytes')
                with self.assertRaises(ValueError):self.check(o)
    def test_predicate_and_overlap_falsifiers(self):
        changes=[lambda r:next(a for a in r['predicates_after']['areas'] if a['id']==2)['routes'][0].update(item_obstacle=True),
          lambda r:r['predicates_after']['areas'][-1]['routes'].pop(),
          lambda r:r['predicates_after']['trace_queries'][0]['flag_filtered_overlap_ids'].insert(0,2),
          lambda r:r['predicates_after']['trace_queries'][0].update(raw_overlap_ids=[]),
          lambda r:r['predicates_after']['trace_queries'][0].update(tree_trace_check_clear=1)]
        for change in changes:
            with self.subTest(change=change):
                o=self.observation();prior=c.canonical(o);change(o['case']);self.assertNotEqual(prior,c.canonical(o),'negative recipe must mutate bytes')
                with self.assertRaises(ValueError):self.check(o)
    def test_lifecycle_and_exact_baseline_are_mandatory(self):
        changes=[lambda o:o.update(schema=True),lambda o:o.update(ses_executed=True),
          lambda o:o['case'].update(post_load_awaited=False),
          lambda o:o['case']['settings_after_selective'].update(plane_as_obstacle=True),
          lambda o:o['case']['state_before_local']['pins'][0]['position_um'].__setitem__(0,0),
          lambda o:o['case'].update(status='failed')]
        for change in changes:
            with self.subTest(change=change):
                o=self.observation();prior=c.canonical(o);change(o);self.assertNotEqual(prior,c.canonical(o),'negative recipe must mutate bytes')
                with self.assertRaises(ValueError):self.check(o)
        b=copy.deepcopy(self.baseline);b['cases'][1]['state']['nets'][0]['width_um']=[1,1]
        with self.assertRaises(ValueError):self.check(b=b)
    def test_shared_geometry_validator_not_only_equality(self):
        for change in (lambda g:g['traces'][0].update(width_um=1),
                       lambda g:g['traces'][0]['corners_board_integer'][0].__setitem__(0,1),
                       lambda g:g['vias'][0].update(layers=['bottom_layer']),
                       lambda g:g['traces'][0].update(layer='not_a_layer')):
            with self.subTest(change=change):
                o=self.observation()
                for field in ('route_geometry_before_local','route_geometry','route_geometry_after_selective'):
                    change(o['case'][field])
                with self.assertRaises(ValueError):self.check(o)
    def test_duplicate_and_missing_routes_rejected(self):
        for field in ('traces','vias'):
            o=self.observation();o['case']['route_geometry_after_selective'][field].pop()
            with self.assertRaises(ValueError):self.check(o)
        o=self.observation();o['case']['predicates_after']['tree_entries'].append(o['case']['predicates_after']['tree_entries'][0])
        with self.assertRaises(ValueError):self.check(o)

if __name__=='__main__':unittest.main()
