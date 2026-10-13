"""Pure alias-plan scope counterexample; no native/solver/Git/network."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).absolute().parent;ROOT=HERE.parents[1]
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT))
DRAFT=ROOT/'.runs/roller-export-alias-draft-001'
spec=importlib.util.spec_from_file_location('existing_alias_fixture',DRAFT/'test_alias.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
def forbidden(*args,**kwargs):raise AssertionError('no process permitted in pure review')
cases={}
with patch.object(subprocess,'run',side_effect=forbidden),patch.object(subprocess,'Popen',side_effect=forbidden):
    for value in ('%R','%V','${REFERENCE}'):
        tree=t.sx.parse(t.source().decode());footprint=t.sx.children(tree,'footprint')[0]
        footprint.append(['fp_text','user',json.dumps(value),['at','0','0'],['layer','"F.Cu"'],['effects',['font',['size','1','1'],['thickness','0.15']]],['uuid','"c658f84c-197e-4b3f-8104-e95741513f3f"']])
        raw=(t.sx.dump(tree)+'\n').encode();accepted=False;reason=None
        try:binding=t.m.plan(raw);accepted=True
        except ValueError as exc:reason=str(exc)
        cases[value]={'plan_accepted':accepted,'rejection':reason,'input_sha256':hashlib.sha256(raw).hexdigest(),'layer':'F.Cu','scope':'Synthetic modern-footprint source AST only; no native parse or geometry claim.'}
assert cases['%R']['plan_accepted'] is True and cases['%V']['plan_accepted'] is True
assert cases['${REFERENCE}']['plan_accepted'] is False
result={'schema':1,'draft_module_sha256':t.m.sha((DRAFT/'padless_alias.py').read_bytes()),'native_execution':False,'cases':cases}
(HERE/'macro-result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True))
