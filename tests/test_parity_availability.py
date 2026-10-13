"""Real skip branch is retained separately; bounded-log execution regressions."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from autorouter import pipeline as p,schematic_field_evidence as e

class ParityAvailability(unittest.TestCase):
    def scene(self,directory,text='Found 0 schematic parity issues\n'):
        directory=Path(directory).resolve();log=directory/'final-drc.log';log.write_text(text)
        return directory,{'argv':['drc','--schematic-parity'],'log':str(log),'log_bytes':len(log.read_bytes()),'log_truncated':False},{'schematic_parity':[]}
    def test_zero_parity_positive_and_exact_findings(self):
        with tempfile.TemporaryDirectory() as name:
            d,s,r=self.scene(name);e.check_availability(d,'final-drc',s,r)
            d,s,r=self.scene(name,'Found 2 schematic parity issues\n');r['schematic_parity']=[{},{}];e.check_availability(d,'final-drc',s,r)
    def test_skip_missing_duplicate_wrong_count_and_localized_unknown_reject(self):
        for text in ('Failed to fetch schematic netlist for parity tests.\n','Schematic parity tests require a fully annotated schematic.\nFound 0 schematic parity issues\n','Found 0 violations\n','Found 0 schematic parity issues\nFound 0 schematic parity issues\n','Found 1 schematic parity issues\n','Unknown localized completion\n'):
            with self.subTest(text=text),tempfile.TemporaryDirectory() as name:
                d,s,r=self.scene(name,text)
                with self.assertRaises(p.Rejected):e.check_availability(d,'final-drc',s,r)
    def test_missing_wrong_bound_truncated_and_changed_log_reject(self):
        for kind in ('absent','path','truncated','size','symlink'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as name:
                d,s,r=self.scene(name)
                if kind=='absent':(d/'final-drc.log').unlink()
                elif kind=='path':s['log']='other'
                elif kind=='truncated':s['log_truncated']=True
                elif kind=='size':(d/'final-drc.log').write_text('Found 0 schematic parity issues\nextra\n')
                else:(d/'other.log').write_bytes((d/'final-drc.log').read_bytes());(d/'final-drc.log').unlink();(d/'final-drc.log').symlink_to(d/'other.log')
                with self.assertRaises((p.Rejected,FileNotFoundError)):e.check_availability(d,'final-drc',s,r)
    def test_no_field_findings_still_check_requested_parity(self):
        with tempfile.TemporaryDirectory() as name:
            d,s,r=self.scene(name,'Failed to fetch schematic netlist for parity tests.\n');s.update(name='final-drc',cwd=str(d));r.update(violations=[],unconnected_items=[])
            with patch('autorouter.floor_route.read_json',return_value=r),self.assertRaisesRegex(p.Rejected,'skipped or unavailable'):e.check_processes(d,{'steps':[s]},'final-drc',d/'board',sandboxed=False)

if __name__=='__main__':unittest.main()
