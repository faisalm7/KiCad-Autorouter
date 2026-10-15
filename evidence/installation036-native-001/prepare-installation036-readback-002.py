"""Repair only the installed test-log footer parse; retain six completed semantic groups."""
from pathlib import Path
import ast,sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
old=R/'.runs/current-installation036-review-001';out=R/'.runs/current-installation036-review-002'
first=f.read_json(old/'checks.json');execution=f.read_json(old/'execution.json')
assert execution['passed'] is False and first['passed'] is False and len(first['failures'])==1
assert first['failures'][0]['check']=='installed_targeted_current_changes'
expected={'real_installed_context','actual_commands_and_selected_tests','complete_source_and_installed_inventory','installed_actual_native_smoke_and_current_readback','outer_costs_and_publication','late_complete_material_and_source'}
assert set(first['checks'])==expected and all(x['passed'] is True for x in first['checks'].values())
s=(old/'audit.py').read_text().replace("OUT=ROOT/'.runs/current-installation036-review-001'","OUT=ROOT/'.runs/current-installation036-review-002'")
needle=" population=read(folder/'population.json');match=re.search(r'Ran (\\d+) tests in [0-9.]+s\\n\\nOK\\s*$',text)"
assert s.count(needle)==1
replacement=""" population=read(folder/'population.json');summaries=list(re.finditer(r'(?m)^Ran (\\d+) tests in [0-9.]+s\\n\\nOK$',text))
 assert len(summaries)==1;match=summaries[0]
 tail=text[match.end():].strip().splitlines();assert len(tail)==2
 printed=[json.loads(line) for line in tail]
 assert all(set(item)=={'status','summary'} and item['status']=='completed'
     and type(item['summary']) is str and Path(item['summary']).is_absolute()
     and item['summary'].endswith('/.runs/paired/paired-summary.json') for item in printed)
 assert len({item['summary'] for item in printed})==2
 methods=re.findall(r'^test_\\S+ \\(([^)]+)\\) \\.\\.\\. (ok|ERROR|FAIL)$',text,re.M)
 assert len(methods)==len({name for name,status in methods})==78 and all(status=='ok' for name,status in methods)
"""
s=s.replace(needle,replacement.rstrip('\n'))
# Keep the same definitions/strict current-source proof, but do not repeat six
# successful groups. Their exact successful receipts and original reader are pinned.
tree=ast.parse(s);lines=s.splitlines(keepends=True)
for node in sorted([node for node in tree.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='step'],key=lambda n:n.lineno,reverse=True):
 name=ast.literal_eval(node.value.args[0])
 if name not in {'installed_targeted_current_changes','late_complete_material_and_source'}:
  del lines[node.lineno-1:node.end_lineno]
s=''.join(lines)
needle="checks={};failures=[]"
s=s.replace(needle,"""prior_checks_path=ROOT/'.runs/current-installation036-review-001/checks.json'
prior_checks=json.loads(prior_checks_path.read_text())
assert prior_checks['passed'] is False and len(prior_checks['failures'])==1 and prior_checks['failures'][0]['check']=='installed_targeted_current_changes'
checks=dict(prior_checks['checks']);failures=[]
reused_completed_checks=sorted(checks)
assert set(reused_completed_checks)=={'real_installed_context','actual_commands_and_selected_tests','complete_source_and_installed_inventory','installed_actual_native_smoke_and_current_readback','outer_costs_and_publication','late_complete_material_and_source'}
assert all(value['passed'] is True for value in checks.values())
assert c.ROOT==CLONE and Path(sys.executable)==CLONE/'.venv/bin/python' and Path(sys.prefix).resolve()==CLONE/'.venv'
""")
s=s.replace("'checks':checks,'failures':failures", "'checks':checks,'failures':failures,'reused_completed_checks':reused_completed_checks,'new_semantic_checks':['installed_targeted_current_changes','late_complete_material_and_source'],'failed001_cost':{'wall_seconds':read(ROOT/'.runs/current-installation036-review-001/execution.json')['wall_seconds'],'full_cpu_seconds':read(ROOT/'.runs/current-installation036-review-001/execution.json')['full_cpu_seconds'],'publication_allowance_seconds':2}")
s=s.replace('independent installed036 retained actual readback','missing-only installed036 target-footer readback')
ast.parse(s)
run=(old/'run.py').read_text().replace("out=ROOT/'.runs/current-installation036-review-001'","out=ROOT/'.runs/current-installation036-review-002'")
run=run.replace("adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation035-review-002/audit.py')", "adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation036-review-001/audit.py')")
ast.parse(run);out.mkdir();(out/'audit.py').write_text(s);(out/'run.py').write_text(run)
pins=dict(f.read_json(old/'input-pins.json')['files_sha256'])
for path in [old/'checks.json',old/'execution.json',old/'command.log',old/'input-pins.json',Path(__file__),out/'audit.py',out/'run.py']:pins[str(path.relative_to(R))]=p.sha(path)
p.save_json(out/'input-pins.json',dict(kind='installation036-reader-inputs-v1',git_head=f.read_json(old/'input-pins.json')['git_head'],files_sha256=pins,scope='Missing-only target-footer parse + complete late source/material freshness. Preserve prior001 six successful semantic groups and failed aggregate; no test/Native/installation repeat. Exactly one successful78method unittest summary plus two exact-schema completed CLI records required.'))
print(f.canonical(dict(prepared=True,files=len(pins),reused_completed_groups=6,new_native_execution=False,new_test_execution=False)))
