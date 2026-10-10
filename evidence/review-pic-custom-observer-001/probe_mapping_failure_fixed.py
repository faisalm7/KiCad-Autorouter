"""Independent successful-export/mapping-rejection truth control; fake workers only."""
import hashlib,inspect,json,sys,textwrap,unittest
from pathlib import Path
base=Path(__file__).resolve().parent
sys.path.insert(0,str(base/'snapshot-final-001'))
import test_driver_original as t
method=textwrap.dedent(inspect.getsource(t.Tests.test_whole_flow_stage_and_final_material_falsifiers))
method=method.replace("('unchanged','parsed_context','parsed_drc','late_source','late_helper','late_tool','late_custom')", "('unchanged','mapping_failure')")
method=method.replace("(out/'native.dsn').write_bytes(raw);d.p.save_json(out/'observation.json',n)","if variant=='mapping_failure':n['pads'][0]['net']='WRONG_NATIVE_MAPPING';mutated.append(1)\n                    (out/'native.dsn').write_bytes(raw);d.p.save_json(out/'observation.json',n)")
method=method.replace("self.assertIs(result['observations_complete'],variant=='unchanged',result)","(self.out/(variant+'-result.json')).write_text(json.dumps({'returned':result,'canonical':real_read(out/'summary.json'),'dsn_nonempty':bool((out/'native.dsn').read_bytes()),'observed_stage_exit':job_exit(out),'expected_error':'native original terminal identities differ' if variant=='mapping_failure' else None},indent=2)+'\\n')\n            self.assertIs(result['observations_complete'],variant=='unchanged',result)")
# Retain small copied inputs/output; no native processes or source writes.
space=dict(t.__dict__)
space['job_exit']=lambda out:t.d.read(out/'observe-process.json')['exit_code']
exec(method,space)
class Review(t.Tests):
 def setUp(self):
  self.out=base/'mapping-failure-fixed-001';self.out.mkdir(exist_ok=False)
Review.test_rejected_mapping_truth=space['test_whole_flow_stage_and_final_material_falsifiers']
suite=unittest.TestSuite([Review('test_rejected_mapping_truth')])
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
