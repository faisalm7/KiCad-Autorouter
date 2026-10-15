"""Complete Native finding populations cannot lose warnings or multiplicities."""
import copy,unittest
from experiments.native_schematic_toolchain_v1.continuation import same_findings

class FindingPopulationControls(unittest.TestCase):
    def scene(self):
        return dict(findings=[{'type':'footprint_symbol_field_mismatch','severity':'warning','description':'literal first field','items':[{'uuid':'owned1','description':'Footprint J1','pos':{'x':10.0,'y':10.0}}]},
                              {'type':'other_warning','severity':'warning','description':'retained unrelated warning','items':[]}],ignored_checks=[{'key':'retained_original_ignore'}])
    def test_permutation_only_keeps_every_literal_finding_and_duplicate(self):
        first=self.scene();second=copy.deepcopy(first);second['findings'].reverse()
        self.assertTrue(same_findings(first,second))
        first['findings'].append(copy.deepcopy(first['findings'][0]));second['findings'].append(copy.deepcopy(second['findings'][1]))
        self.assertTrue(same_findings(first,second));second['findings'].pop();self.assertFalse(same_findings(first,second))
    def test_changed_missing_added_excluded_and_ignored_findings_never_compare_equal(self):
        first=self.scene()
        for mode in ('missing','added','description','severity','uuid','position','excluded','ignore','unknown_field'):
            second=copy.deepcopy(first)
            if mode=='missing':second['findings'].pop()
            elif mode=='added':second['findings'].append(copy.deepcopy(second['findings'][0]))
            elif mode=='description':second['findings'][0]['description']='different first field'
            elif mode=='severity':second['findings'][0]['severity']='error'
            elif mode=='uuid':second['findings'][0]['items'][0]['uuid']='other'
            elif mode=='position':second['findings'][0]['items'][0]['pos']['x']=10.1
            elif mode=='excluded':second['findings'][0]['excluded']=True
            elif mode=='ignore':second['ignored_checks']=[]
            else:second['findings'][0]['unexpected']='retained must differ'
            with self.subTest(mode=mode):self.assertFalse(same_findings(first,second))

if __name__=='__main__':unittest.main()
