"""Synthetic late-material regression; no subprocess or Native proof."""
from pathlib import Path
import ast,json,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h
WRAPPER=ROOT/'experiments/native_schematic_toolchain_v1/enclosure.py'

class HiddenOuterMaterial(unittest.TestCase):
    def test_outer_guard_refuses_late_child_or_reference_mutation(self):
        tree=ast.parse(WRAPPER.read_text());function=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name=='stable')
        for changed in ('child','reference','adopted_child'):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory(dir=ROOT/'.cache') as directory:
                root=Path(directory).resolve();out=root/'out';out.mkdir();child=out/'native';child.mkdir();case=child/'owned-case';case.mkdir();artifact=case/'candidate.txt';artifact.write_text('owned child data')
                reference=root/'reference';reference.mkdir();ref=reference/'original.txt';ref.write_text('owned immutable reference')
                log=out/'command.log';log.write_text('owned log')
                ref_pin=p.tree_hash(reference);owner={};h.capture_destination(owner,out)
                def references():
                    if p.tree_hash(reference)!=ref_pin:raise p.Rejected('controlled reference mutation')
                    return {},{'cases':[]},{}
                expected_code={str(WRAPPER):p.sha(WRAPPER)}
                child_record={'cases':[],'completed_evidence':{str(case):p.tree_hash(case)},'code_sha256':expected_code}
                (child/'result.json').write_text(json.dumps(child_record))
                globals=dict(p=p,h=h,owner=owner,Path=Path,__file__=str(WRAPPER),out=out,tools={'owned':'unit'},record={'controller_sha256':p.sha(WRAPPER),'log_sha256':p.sha(log)},remaining=lambda:10,
                    child_material=p.tree_hash(child),child_record=child_record,expected_code=expected_code,expected_case_paths={str(case)},f=f,historical_record={'cases':[]},reference_records=references,REFERENCE=reference)
                exec(compile(ast.Module(body=[function],type_ignores=[]),str(WRAPPER),'exec'),globals)
                with patch.object(p,'tool_manifest',return_value=globals['tools']):
                    globals['stable']()
                    (ref if changed=='reference' else artifact).write_text('changed late')
                    if changed=='adopted_child':globals['child_material']=p.tree_hash(child)
                    with self.assertRaises(p.Rejected):globals['stable']()

if __name__=='__main__':unittest.main(verbosity=2)
