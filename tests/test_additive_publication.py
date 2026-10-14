"""Exact final-publication seam: injected failures cannot retain eligible index."""
import ast,signal,subprocess,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f
ROOT=Path(__file__).resolve().parents[1]
PRODUCER=ROOT/'evidence/nus-additive-publication-fix-002/producer.py'

class AdditivePublicationTests(unittest.TestCase):
    def publication_suffix(self):
        tree=ast.parse(PRODUCER.read_text())
        start=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='wall' for t in node.targets))
        return ast.Module(body=tree.body[start:-2],type_ignores=[])
    def check_failure(self,error,correction_fails=False):
        suffix=self.publication_suffix()
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory).resolve();report={'schema':1,'status':'completed','accepted':False,'comparison_eligible':True,'comparisons':[{'synthetic':True}]}
            p.save_json(out/'result.json',report);saved=p.save_json
            def writer(path,value):
                if path.name=='execution.json':raise error
                if correction_fails and path.name=='result.json':raise OSError('corrective write failed')
                saved(path,value)
            def account():
                if report['status']!='completed':report.update(comparison_eligible=False,comparisons=[])
            env={'out':out,'output':out,'report':report,'p':p,'f':f,'h':SimpleNamespace(owned_destination=lambda owner:None),'owner':{},'START':time.monotonic(),'CPU0':time.process_time()+f.child_cpu(),'CAP':25.,'cap':15.,'time':time,'signal':signal,'remaining':lambda:25.,'stable':lambda:None,'account':account,'previous':{signal.SIGTERM:'restored-handler'}}
            with patch.object(p,'save_json',side_effect=writer),patch.object(signal,'signal') as restore,patch.object(subprocess,'run',side_effect=AssertionError('no process')),patch.object(subprocess,'Popen',side_effect=AssertionError('no process')):
                exec(compile(suffix,str(PRODUCER),'exec'),env)
            restore.assert_called_once_with(signal.SIGTERM,'restored-handler')
            self.assertFalse(report['comparison_eligible'])
            self.assertEqual(len(list(out.glob('invalidated-result-*'))),1)
            if (out/'result.json').exists():self.assertFalse(f.read_json(out/'result.json')['comparison_eligible'])
            self.assertFalse((out/'execution.json').exists())
    def test_final_execution_write_failure(self):self.check_failure(OSError('execution receipt failed'))
    def test_final_execution_cancel(self):self.check_failure(KeyboardInterrupt())
    def test_failed_corrective_write(self):self.check_failure(OSError('execution receipt failed'),True)

class NativeContinuationPublicationTests(AdditivePublicationTests):
    """Execute the actual shared producer's final seam, without routing mocks."""
    def publication_suffix(self):
        source=ROOT/'experiments/native_paired_v1/readback.py'
        tree=ast.parse(source.read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='qualify_continuation')
        # Include every statement after positive publication. A receipt write
        # accidentally moved out of the try will therefore fail this control.
        start=next(i for i,node in enumerate(function.body) if isinstance(node,ast.Expr)
            and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
            and node.value.func.attr=='publish')
        return ast.Module(body=function.body[start+1:-1],type_ignores=[])

if __name__=='__main__':unittest.main()
