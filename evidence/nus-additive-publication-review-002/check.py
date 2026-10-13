"""Run retained exact-source suffix regressions; no actual readback/native."""
import hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[2]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('existing_publication_tests',ROOT/'tests/test_additive_publication.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
counter=0
class RetainedDirectory:
    def __init__(self):
        global counter
        counter+=1;self.path=HERE/('case-'+str(counter));self.path.mkdir()
    def __enter__(self):return str(self.path)
    def __exit__(self,*args):return False
producer=ROOT/'.runs/close-nus-additive-comparison-002.py'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
before=sha(producer)
assert producer.read_bytes()==m.PRODUCER.read_bytes()
names=['test_final_execution_write_failure','test_final_execution_cancel','test_failed_corrective_write']
with patch.object(tempfile,'TemporaryDirectory',side_effect=RetainedDirectory):
    outcome=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(m.AdditivePublicationTests(name) for name in names))
assert outcome.wasSuccessful() and sha(producer)==before
cases={}
for index,name in enumerate(names,1):
    folder=HERE/('case-'+str(index));current=folder/'result.json'
    cases[name]={'current_index_exists':current.exists(),'current_eligible':json.loads(current.read_text())['comparison_eligible'] if current.exists() else None,'archives':len(list(folder.glob('invalidated-result-*'))),'execution_receipt_exists':(folder/'execution.json').exists()}
result={'schema':1,'controls_passed':3,'producer_sha256':before,'public_copy_byte_equal':True,'native_execution':False,'actual_controller_readback_execution':False,'retained_existing_tests_sha256':sha(ROOT/'tests/test_additive_publication.py'),'cases':cases}
(HERE/'RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
