"""Pure continuation controls; never start KiCad, Git, JVM or a native worker."""
from pathlib import Path
import copy,importlib.util,sys,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('compat_continuation_draft',HERE/'driver.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)

def fp(uuid,reference,pads=0):
    return ['footprint','"owned-control"',['attr','board_only','exclude_from_bom','exclude_from_pos_files'],['uuid',uuid],['property','"Reference"','"'+reference+'"'],*([['pad','"1"','smd','rect']] * pads)]

class ContinuationTests(unittest.TestCase):
    def test_draft_cannot_execute_or_create_output(self):
        output=HERE/'forbidden-output'
        with patch.object(d.shared,'cpu',side_effect=AssertionError('must reject before runtime')):
            with self.assertRaisesRegex(d.p.Rejected,'promote/checkpoint'):d.experiment(output,run_native=True)
            with self.assertRaisesRegex(d.p.Rejected,'promote/checkpoint'):d.experiment(output,run_native=False)
        self.assertFalse(output.exists())
    def test_actual_prefix_readback_is_only_readback(self):
        protocol=d.f.read_json(HERE/'PROTOCOL.json')
        with patch.object(d.subprocess,'run',side_effect=AssertionError('no subprocess allowed')):
            result=d.prefix_readback(protocol)
        self.assertEqual(result['status'],'failed');self.assertTrue(result['original_export_failure_preserved'])
        self.assertEqual(result['actual_unique_native_processes'],13)
        self.assertEqual([(x['case'],x['steps'],x['native_reexecuted']) for x in result['owned_controls']],[('positive',8,False),('missing_track',2,False),('narrow_track',2,False)])
    def test_prefix_full_tree_and_outer_cost_pins_fail_closed(self):
        protocol=d.f.read_json(HERE/'PROTOCOL.json');altered=copy.deepcopy(protocol)
        altered['prefix']['inventory']['command.log']='0'*64
        with self.assertRaisesRegex(d.p.Rejected,'prior failure evidence'):d.prefix_readback(altered)
        altered=copy.deepcopy(protocol);altered['prefix']['prior_outer_full_cpu_seconds']+=.001
        with self.assertRaisesRegex(d.p.Rejected,'resource charge'):d.prefix_readback(altered)
        altered=copy.deepcopy(protocol);altered['prefix']['prior_outer_wall_seconds']=True
        with self.assertRaisesRegex(d.p.Rejected,'resource charge'):d.prefix_readback(altered)
    def test_duplicate_padless_refs_are_retained_by_uuid(self):
        census=d.footprint_census(['kicad_pcb',fp('a','label'),fp('b','label'),fp('c','U1',1)])
        self.assertEqual(len(census),3);self.assertEqual([x['uuid'] for x in d.duplicate_references(census)['label']],['a','b'])
        self.assertEqual(sum(x['pad_count'] for x in census),1)
        self.assertTrue(all(x['board_only'] and x['exclude_from_bom'] and x['exclude_from_pos_files'] for x in census))
    def test_ambiguous_reference_or_uuid_rejected(self):
        duplicate=fp('a','label');duplicate.append(['fp_text','reference','"another"'])
        with self.assertRaisesRegex(d.p.Rejected,'ambiguous footprint'):d.footprint_census(['kicad_pcb',duplicate])
        with self.assertRaisesRegex(d.p.Rejected,'footprint UUID'):d.footprint_census(['kicad_pcb',fp('a','label'),fp('a','second')])
    def test_original_static_census_is_lead_only(self):
        census=d.footprint_census(d.sx.read(d.prior.SOURCE));groups=d.duplicate_references(census)
        self.assertEqual(len(census),37);self.assertEqual(set(groups),{'kibuzzard-6765D292','kibuzzard-6765D25C'})
        self.assertTrue(all(len(rows)==2 and all(x['pad_count']==0 for x in rows) for rows in groups.values()))
    def test_final_mode_has_no_dsn_and_header_changes_reject(self):
        argv=d.f.context_argv('final',HERE/'source.kicad_pcb',HERE/'context.json')
        self.assertEqual(argv[-3:],['final',str(HERE/'source.kicad_pcb'),str(HERE/'context.json')]);self.assertFalse(any(x.endswith('.dsn') for x in argv))
        original=['kicad_pcb',['version','20240108'],['generator','"owned"']];changed=copy.deepcopy(original);changed[1][1]='20260101'
        with self.assertRaisesRegex(d.p.Rejected,'non-fill geometry'):d.prior.emission_equal(original,changed)
    def test_unsupported_qualification_cannot_be_promoted(self):
        record={k:False for k in d.FALSE_FLAGS};d.qualifications(record)
        for key in d.FALSE_FLAGS:
            changed=dict(record);changed[key]=True
            with self.assertRaisesRegex(d.p.Rejected,'qualification'):d.qualifications(changed)

if __name__=='__main__':unittest.main()
