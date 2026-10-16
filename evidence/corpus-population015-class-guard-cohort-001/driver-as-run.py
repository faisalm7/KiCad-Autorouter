"""Unexecuted static25-board recheck after schematic class/hierarchy guards."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p
from experiments.licensed_acquisition_v1 import fetch
prior=json.loads((ROOT/'experiments/licensed_acquisition_v7/existing-data-inventory.json').read_text());receipt=json.loads((ROOT/'.runs/licensed-acquisition-010-run-001/receipt.json').read_text())
added={row['destination']:{k:row[k] for k in ('bytes','sha256')} for row in receipt['files']}
expected=fetch.extend(prior,added,destination_root='expansion010')
baseline_path=ROOT/'evidence/corpus-population014-current-df-cohort-001/population.json'
baseline=json.loads(baseline_path.read_text());baseline_pin=p.sha(baseline_path)
assert expected['file_count']==baseline['files_observed']==394
assert expected['bytes']==baseline['bytes']
# Reuse exact bounded acquisition inventories for each original managed root.
# Later demo/creator packets stay visible outside this historical cohort; do not
# scan or silently incorporate their payloads or claim this is all current data.
roots=sorted({name.split('/')[0] for name in expected['files']})
for top in roots:
 prefix=top+'/'
 files={k[len(prefix):]:v for k,v in expected['files'].items()if k.startswith(prefix)}
 directories=[k[len(prefix):]for k in expected['directories']if k.startswith(prefix)]
 subset={'schema':1,'files':dict(sorted(files.items())),'directories':sorted(directories),'file_count':len(files),'bytes':sum(v['bytes']for v in files.values())}
 fetch.inventory(ROOT/'.data'/top,subset)
actual=expected
additional_data_roots=sorted(path.name for path in (ROOT/'.data').iterdir()if path.name not in roots)

old=json.loads((ROOT/'evidence/corpus-population-009-current-001/population.json').read_text());names=[row['board'] for row in old['boards'] if row['board']!='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb']+['.data/expansion010/push-button-led/PushButtonLed.kicad_pcb'];assert len(names)==25 and len(set(names))==25
baseline_rows={row['board']:row for row in baseline['boards']}
assert len(baseline['boards'])==len(baseline_rows)==baseline['canonical_boards']==25 and set(baseline_rows)==set(names)
all_pcbs={'.data/'+name for name in actual['files'] if name.endswith('.kicad_pcb')};duplicate='.data/corpus-audit-coldfire-001/project/kit-dev-coldfire-xilinx_5213.kicad_pcb';canonical='.data/boards/kicad-coldfire-xilinx/kit-dev-coldfire-xilinx_5213.kicad_pcb';assert all_pcbs==set(names)|{duplicate} and p.sha(ROOT/duplicate)==p.sha(ROOT/canonical)
rows=[]
for name in sorted(names):
 path=ROOT/name;row={'board':name,'sha256':p.sha(path),'bytes':path.stat().st_size,'statically_eligible':False,'unsupported_reason':None,'native_acceptance':None}
 assert row['sha256']==baseline_rows[name]['sha256'] and row['bytes']==baseline_rows[name]['bytes']
 try:p.preflight(path);row['statically_eligible']=True
 except p.Rejected as exc:row['unsupported_reason']=str(exc)
 rows.append(row)
paired=[{'board':row['board'],'sha256':row['sha256'],
         'prior_statically_eligible':baseline_rows[row['board']]['statically_eligible'],
         'current_statically_eligible':row['statically_eligible'],
         'prior_unsupported_reason':baseline_rows[row['board']]['unsupported_reason'],
         'current_unsupported_reason':row['unsupported_reason']} for row in rows]
gained=[row['board'] for row in paired if not row['prior_statically_eligible'] and row['current_statically_eligible']]
lost=[row['board'] for row in paired if row['prior_statically_eligible'] and not row['current_statically_eligible']]
comparison={'prior_population':str(baseline_path.relative_to(ROOT)),'prior_population_sha256':baseline_pin,
            'same25_denominator_and_board_bytes':True,
            'prior_statically_eligible':sum(row['prior_statically_eligible'] for row in paired),
            'current_statically_eligible':sum(row['current_statically_eligible'] for row in paired),
            'eligible_gained':gained,'eligible_lost':lost,
            'reason_changed':[row['board'] for row in paired if row['prior_unsupported_reason']!=row['current_unsupported_reason']],
            'boards':paired}
assert p.sha(baseline_path)==baseline_pin
tools=p.tool_manifest()
out=ROOT/'.runs/corpus-population-015-class-guard-cohort-001';out.mkdir();p.save_json(out/'population.json',{'schema':1,'kind':'current static schematic-class/hierarchy guard recheck of retained25-board legacy managed cohort; not all current data','git_head':tools['git_head'],'implementation_sha256':tools['implementation_sha256'],'complete_legacy_cohort_inventory_verified':True,'additional_data_roots_not_admitted_to_this_cohort':additional_data_roots,'files_observed':actual['file_count'],'bytes':actual['bytes'],'physical_boards':len(all_pcbs),'canonical_boards':len(rows),'exact_audit_duplicate':{'board':duplicate,'canonical':canonical,'sha256':p.sha(ROOT/duplicate)},'boards':rows,'comparison_to_population014':comparison,'statically_eligible':sum(r['statically_eligible'] for r in rows),'statically_unsupported':sum(not r['statically_eligible'] for r in rows),'native_executed':False,'all_development_exposed':True,'independent_pedigrees_proven':0,'claims_limit':'Static scope only; no new native run or accepted output, no holdout or family superiority. Earlier audit_corpus-only original7-board subset retained separately, never used as full denominator.'})
p.save_json(out/'inputs.json',{'prior_population_sha256':p.sha(ROOT/'evidence/corpus-population-009-current-001/population.json'),'comparison_population014_sha256':baseline_pin,'preexisting_inventory_sha256':p.sha(ROOT/'experiments/licensed_acquisition_v7/existing-data-inventory.json'),'acquisition_receipt_sha256':p.sha(ROOT/'.runs/licensed-acquisition-010-run-001/receipt.json'),'producer_sha256':p.sha(Path(__file__))})

print({'output':str(out),'eligible':sum(r['statically_eligible'] for r in rows),'unsupported':sum(not r['statically_eligible'] for r in rows),'eligible_gained':gained,'eligible_lost':lost,'files':actual['file_count'],'bytes':actual['bytes'],'native_executed':False})
