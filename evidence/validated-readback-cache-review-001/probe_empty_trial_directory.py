"""Actual bounded inventory plus the exact checker directory-population predicate.
No cache implementation, accepted receipt or native qualification is claimed.
"""
from pathlib import Path
import ast,hashlib,json,sys,tempfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import placement_clearance as pc
source=ROOT/'autorouter/placement_strategy.py';text=source.read_text();function=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name=='check_pruning_result')
condition=next(n.test for n in ast.walk(function) if isinstance(n,ast.If) and 'iterdir' in ast.unparse(n.test) and 'trials' in ast.unparse(n.test))
compiled=compile(ast.Expression(condition),str(source),'eval')
with tempfile.TemporaryDirectory(dir=HERE) as tmp:
 directory=Path(tmp);(directory/'trials').mkdir();(directory/'receipt.json').write_text('owned synthetic receipt\n');rows=[]
 before=pc.inventory(directory);reject_before=eval(compiled,{'directory':directory,'rows':rows})
 (directory/'trials/9999').mkdir()
 after=pc.inventory(directory);reject_after=eval(compiled,{'directory':directory,'rows':rows})
 result={'scope':__doc__,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),'exact_checker_condition':ast.unparse(condition),'file_hash_inventory_unchanged':before==after,'checker_rejects_before':reject_before,'checker_rejects_after_empty_directory':reject_after,'before_file_inventory':before,'after_file_inventory':after,'conclusion':'A cache keyed only by pc.inventory file hashes would hit, although full checker rejects the changed trial population.'}
 assert result['file_hash_inventory_unchanged'] is True and reject_before is False and reject_after is True
(HERE/'empty-trial-directory-001.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
