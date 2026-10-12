"""Run draft modules plus explicitly labelled prospective pipeline hook; no native."""
import importlib.util,json,sys,unittest,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
import autorouter

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

autorouter.netclass=load('autorouter.netclass',HERE/'autorouter/netclass.py')
autorouter.pipeline=load('autorouter.pipeline',HERE/'pipeline-hook-preview.py')
tests=load('default_tuning_controls',HERE/'tests/test_default_tuning_intent.py')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
rows=[]
for directory in sorted((HERE/'old-cases').iterdir()):
    board=directory/'fixture.kicad_pcb'
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in directory.iterdir()}
    try:autorouter.pipeline.preflight(board);status='admitted'
    except Exception as e:status=type(e).__name__+': '+str(e)
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in directory.iterdir()}
    rows.append({'case':directory.name,'preflight':status,'hashes':before})
(HERE/'new-draft-readback.json').write_text(json.dumps({'scope':'Draft netclass plus prospective pipeline hook overlay; tracked production code unchanged. Not native evidence.','test_methods':result.testsRun,'successful':result.wasSuccessful(),'cases':rows},indent=2)+'\n')
raise SystemExit(0 if result.wasSuccessful()else 1)
