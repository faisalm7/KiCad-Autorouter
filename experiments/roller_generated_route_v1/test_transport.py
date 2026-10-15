"""Authored transport/fault controls only; no Native or routing proof."""
import copy
import json
import unittest
from autorouter import pipeline as p,sexpr as sx,adapter
from experiments.roller_generated_route_v1 import driver,transport
from experiments.roller_export_alias_v1 import padless_alias as alias


def fixture():
    tree=sx.parse('''(kicad_pcb (version 20241229) (net 0 "") (net 1 "A") (net 2 "B")
      (footprint "art" (uuid "00000000-0000-0000-0000-000000000001")
        (property "Reference" "DUP" (layer "F.Fab")) (attr board_only))
      (footprint "art" (uuid "00000000-0000-0000-0000-000000000002")
        (property "Reference" "DUP" (layer "F.Fab")) (attr board_only))
      (footprint "connector" (uuid "00000000-0000-0000-0000-000000000003")
        (property "Reference" "J1" (layer "F.Fab")) (pad "1" thru_hole circle) (pad "2" thru_hole circle))
      (segment (start 0 0) (end 1 1) (width .25) (layer "F.Cu") (net 1)
        (uuid "00000000-0000-0000-0000-000000000004"))
      (zone (net 1) (net_name "A") (layer "F.Cu")
        (polygon (pts (xy 0 0) (xy 5 0) (xy 5 5)))
        (filled_polygon (layer "F.Cu") (pts (xy 0 0) (xy 4 0) (xy 4 4)))) )''')
    raw=(sx.dump(tree)+'\n').encode();binding=alias.plan(raw)
    names=[x['alias'] for x in binding['aliases']]
    places=' '.join('(place '+json.dumps(n)+' 0 0 front 0)' for n in names)
    dsn=('(pcb "/authored/absolute/native.dsn" (parser (string_quote ")) (resolution um 10) (unit um) '
         '(placement (component "art" '+places+') (component "conn" (place "J1" 1 2 front 0))) '
         '(library (image "art") (image "conn" (pin "1" P 0 0) (pin "2" P 1 0))) '
         '(network (net "A" (pins "J1-1")) (net "B" (pins "J1-2"))))').encode()
    ses=('(session "authored.ses" (base_design "task") '
         '(placement (resolution um 10) (component "conn" (place "J1" 9999 8888 back 90)) '
         '(component "art" '+places+')) (was_is) '
         '(routes (resolution um 10) (library_out) '
         '(network_out (net "A" (wire (path "F.Cu" 1524 0 0 25 30))) '
         '(net "B" (wire (path "B.Cu" 1524 10 10 40 40))))))').encode()
    return tree,raw,binding,dsn,ses


class TransportControls(unittest.TestCase):
    def test_task_removes_routing_and_derived_fill_only(self):
        tree,*_=fixture();before=copy.deepcopy(tree);task=transport.task(tree)
        self.assertEqual(tree,before);self.assertFalse(p.routes(task))
        self.assertEqual(p.immutable(task),p.immutable(tree))
        self.assertFalse(sx.children(sx.one(task,'zone'),'filled_polygon'))
        for lock in ('locked',['locked','yes']):
            bad=copy.deepcopy(tree);p.routes(bad)[0].append(lock)
            with self.assertRaises(p.Rejected):transport.task(bad)

    def test_rounded_or_moved_placement_is_omitted_with_all_route_fields_exact(self):
        _,raw,binding,dsn,ses=fixture();before=sx.parse(ses.decode())
        filtered,receipt=transport.session(ses,dsn,raw,binding,engine_input_name='task.dsn');after=sx.parse(filtered.decode())
        self.assertIsNone(sx.one(after,'placement'))
        self.assertEqual(sx.one(after,'routes'),sx.one(before,'routes'))
        self.assertEqual(filtered,adapter.fixed_placement_session(ses)[0])
        self.assertFalse(receipt['routing_accepted']);self.assertFalse(receipt['alias_outside_placement'])
        self.assertEqual(receipt['alias_count'],2)
        self.assertEqual(receipt['engine_input_name'],'task.dsn');self.assertEqual(receipt['expected_base_design'],'task')
        for invalid in ('wrong.dsn','/tmp/task.dsn','sub/task.dsn',r'sub\task.dsn','.dsn','..dsn',None):
            with self.subTest(engine_input=invalid):
                with self.assertRaises(p.Rejected):transport.session(ses,dsn,raw,binding,engine_input_name=invalid)
        # Alias absence is independent of the coarse native placement grid.
        bad=sx.parse(ses.decode());sx.one(sx.one(bad,'routes'),'library_out').append(['padstack',json.dumps(binding['aliases'][0]['alias'])])
        with self.assertRaises(p.Rejected):transport.session((sx.dump(bad)+'\n').encode(),dsn,raw,binding,engine_input_name='task.dsn')

    def test_wrong_design_alias_namespace_and_renaming_are_not_transport(self):
        _,raw,binding,dsn,ses=fixture()
        for change in ('design','rename','route-alias','source-drift','dsn-pin'):
            with self.subTest(change=change):
                a,b,c,d=raw,binding,dsn,ses
                if change=='design':d=ses.replace(b'base_design "task"',b'base_design "other.dsn"')
                elif change=='rename':d=ses.replace(b'(was_is)',b'(was_is (pins "J1-1" "J1-2"))')
                elif change=='route-alias':d=ses.replace(b'(net "A"',('(net '+json.dumps(binding['aliases'][0]['alias']+'-1')).encode())
                elif change=='source-drift':a=raw.replace(b'version 20241229',b'version 20260206')
                else:c=dsn.replace(b'"J1-1"',json.dumps(binding['aliases'][0]['alias']+'-1').encode())
                with self.assertRaises((ValueError,p.Rejected)):transport.session(d,c,a,b,engine_input_name='task.dsn')

    def test_physical_fault_uses_bound_native_centers_and_preserves_candidate(self):
        tree,*_=fixture();before=copy.deepcopy(tree)
        scene={'nets':[{'name':'A','width_nm':152400},{'name':'B','width_nm':152400}],
            'pads':[{'uuid':'00000000-0000-0000-0000-000000000010','net':'A','position_nm':[-1234567,2000001],'copper_layers':['F.Cu','B.Cu']},
                    {'uuid':'00000000-0000-0000-0000-000000000011','net':'B','position_nm':[4321000,5000000],'copper_layers':['F.Cu']}]}
        bad,proof=transport.bridge(tree,scene)
        self.assertEqual(tree,before);self.assertEqual(p.routes(bad)[:-1],p.routes(tree))
        self.assertEqual(p.immutable(bad),p.immutable(tree));self.assertEqual(sx.one(p.routes(bad)[-1],'start'),['start','-1.234567','2.000001'])
        self.assertEqual(proof['net_names'],['A','B']);self.assertEqual(proof['layer'],'F.Cu');self.assertFalse(proof['routing_accepted'])
        self.assertEqual(transport.bridge(tree,scene),(bad,proof))
        for change in ('same-net','fraction','boolean','duplicate','disjoint-layer','unknown-layer','missing-width'):
            with self.subTest(change=change):
                g=copy.deepcopy(scene)
                if change=='same-net':g['pads'][1]['net']='A'
                elif change=='fraction':g['pads'][0]['position_nm'][0]=1.5
                elif change=='boolean':g['pads'][0]['position_nm'][0]=True
                elif change=='duplicate':g['pads'][1]['uuid']=g['pads'][0]['uuid']
                elif change=='disjoint-layer':g['pads'][0]['copper_layers']=['B.Cu']
                elif change=='unknown-layer':g['pads'][0]['copper_layers']=['In1.Cu']
                else:del g['nets'][0]['width_nm']
                with self.assertRaises(p.Rejected):transport.bridge(tree,g)

    def test_native_opt_in_is_required_before_files_or_workers(self):
        with self.assertRaisesRegex(p.Rejected,'opt-in'):driver.experiment('/never-created',run_native=False)

if __name__=='__main__':unittest.main()
