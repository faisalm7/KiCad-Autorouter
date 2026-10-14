"""Run the exact controller tail with real publication and injected failures.

No native tool, route, download, or installation is repeated.
"""
import ast
from pathlib import Path
import tempfile,time,unittest
from unittest.mock import patch
from autorouter import pipeline as p,floor_route as f,handoff as h

SOURCE=Path(__file__).with_name('controller.py')

class WorkflowPublication(unittest.TestCase):
    def control(self,mode):
        tree=ast.parse(SOURCE.read_text())
        start=next(i for i,node in enumerate(tree.body) if isinstance(node,ast.FunctionDef) and node.name=='account')
        suffix=ast.Module(body=tree.body[start:-2],type_ignores=[])
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory).resolve();owner={};h.capture_destination(owner,out)
            record={'status':'completed','accepted':False,'controls_passed':True}
            p.save_json(out/'result.json',record);writer=p.save_json;calls=[]
            def write(path,value):
                calls.append(path)
                if mode=='write':raise OSError('injected write failure')
                if mode=='cancel':raise KeyboardInterrupt()
                writer(path,value)
            seen=[]
            def tracked():
                seen.append(True)
                if mode=='stale' and len(seen)==2:raise p.Rejected('injected late source drift')
            env={'out':out,'record':record,'owner':owner,'p':p,'f':f,'h':h,'time':time,
                 'start':time.monotonic(),'cpu0':time.process_time()+f.child_cpu(),
                 'limit':180.,'remaining':lambda:180.,'tracked':tracked}
            with patch.object(p,'save_json',side_effect=write):
                exec(compile(suffix,str(SOURCE),'exec'),env)
            self.assertFalse(record['controls_passed'])
            self.assertTrue(list(out.glob('invalidated-result-*')))
            if (out/'result.json').exists():
                self.assertFalse(f.read_json(out/'result.json')['controls_passed'])
    def test_write_and_failed_correction(self):self.control('write')
    def test_cancellation(self):self.control('cancel')
    def test_late_source_drift(self):self.control('stale')

if __name__=='__main__':unittest.main()
