from pathlib import Path
import ast,sys,re
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f
base=R/'.runs/current-installation036-review-001';fixed=R/'.runs/current-installation036-review-002';out=R/'.runs/current-installation037-review-001'
plan=f.read_json(R/'.runs/installation037-preparation-001/protocol.json');head=plan['git_head'];s=(base/'audit.py').read_text()
replacement=(fixed/'audit.py').read_text();a=replacement.index('def targeted():');b=replacement.index("step('installed_targeted_current_changes',targeted)",a)
x=s.index('def targeted():');y=s.index("step('installed_targeted_current_changes',targeted)",x);s=s[:x]+replacement[a:b]+s[y:]
s=s.replace('installation-036','installation-037').replace('installation036','installation037').replace('installed036','installed037').replace('ba61d69329e74c208223163010bc67cbc2fbe996',head)
s=s.replace("['tests.test_chain_proposals','tests.test_strategy','tests.test_paired']",repr(plan['target_modules']))
s=re.sub(r'\b78\b','112',s)
needle="'source_and_original_constraints_unchanged':True"
s=s.replace(needle,needle+",'known_metadata_issue':'Resource limitations description still says16GiB; actual pipeline source and tested ceiling are18GiB. Retained as an open reporting correction, no guard/Native rule waived.'")
ast.parse(s)
run=(base/'run.py').read_text().replace('installation-036','installation-037').replace('installation036','installation037').replace('current036 source and78','current037 source and112')
run=run.replace("adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation035-review-002/audit.py')","adapted_reader_source_sha256=p.sha(ROOT/'.runs/current-installation036-review-001/audit.py')")
ast.parse(run);out.mkdir();(out/'audit.py').write_text(s);(out/'run.py').write_text(run)
names=['.runs/installation-037/result.json','.runs/installation-037/source-tracked.json','.runs/installation-037-execution/execution.json','.runs/installation-037-execution/command.log','.runs/installation037-targeted-001/execution.json','.runs/installation037-targeted-001/population.json','.runs/installation037-targeted-001/tests.log','.runs/installation037-preparation-001/protocol.json','.runs/current-installation036-review-001/audit.py','.runs/current-installation036-review-002/audit.py','.runs/prepare-installation037-readback-001.py']
pins={n:p.sha(R/n) for n in names};pins.update(plan['controller_sha256']);pins.update(plan['source_sha256']);pins.update({str(x.relative_to(R)):p.sha(x) for x in (out/'audit.py',out/'run.py')})
p.save_json(out/'input-pins.json',dict(kind='installation037-reader-inputs-v1',git_head=head,files_sha256=pins,scope='Existing all7 installed proof groups; corrected strict footer112unique methods plus2actualCLIJSON records, complete inventories/source/tools/PRL/refill/Native/latefreshness. No test/Native repeats. Known cache-description literal16GiB is retained as reporting issue; source guard is18GiB.'))
print(f.canonical(dict(prepared=True,files=len(pins),new_native_execution=False,new_test_execution=False)))
