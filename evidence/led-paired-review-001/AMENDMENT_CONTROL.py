"""Pure demonstration of the actual supplemental-003 assertion mismatch."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'.runs/qualify-push-button-led-native-paired-complete-sch-003.py'
spec=json.loads((ROOT/'.runs/push-button-led-native-paired-complete-sch-001-protocol.json').read_text())
amend=json.loads((ROOT/'.runs/push-button-led-native-paired-complete-sch-003-qualification-protocol.json').read_text())
result=json.loads((ROOT/'.runs/push-button-led-native-paired-complete-sch-003-qualification/result.json').read_text())
tree=ast.parse(source.read_text());cap=next(node.value.value for node in ast.walk(tree) if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='CAP' for x in node.targets))
condition=next(node.test for node in ast.walk(tree) if isinstance(node,ast.Assert) and "spec['audit_charge_seconds']" in ast.unparse(node.test))
actual=eval(compile(ast.Expression(condition),str(source),'eval'),{'spec':spec,'CAP':cap,'protocol':{'freeze':{'tools':{'git_head':spec['git_head']}}}})
assert actual is False and cap==amend['new_equal_charge_seconds']==15 and spec['audit_charge_seconds']==5
assert result['status']=='failed' and result['comparison_eligible'] is False and result['results']==[] and result['reason'].startswith('AssertionError')
print(json.dumps({'schema':1,'native_execution':False,'condition':ast.unparse(condition),'actual_result':actual,'original_cap':spec['audit_charge_seconds'],'supplemental_cap':cap,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'actual_failure_result_sha256':hashlib.sha256((ROOT/'.runs/push-button-led-native-paired-complete-sch-003-qualification/result.json').read_bytes()).hexdigest(),'required_correction':'Validate original predeclared5 and separate prospective supplemental15; retain actual003 failure and its costs.'},indent=2))
