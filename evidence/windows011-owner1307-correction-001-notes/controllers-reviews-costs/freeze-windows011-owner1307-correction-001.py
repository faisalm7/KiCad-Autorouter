"""Freeze the one permitted causal correction; never modify old protocols."""
import ast,datetime,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p, floor_route as f, placement_clearance as io
notes=ROOT/'evidence/windows011-owner1307-correction-001-notes';packet=ROOT/'evidence/windows011-owner1307-correction-001.json'
assert not notes.exists() and not packet.exists()
review=ROOT/'.runs/windows011-owner1307-C-fix-review-001.json';rd=f.read_json(review);assert not rd['blocking_findings']
assert p.sha(ROOT/rd['source']['path'])==rd['source']['sha256']=='082ba80972f0484547897608bfffcd7f16d050b9e4aabe7e409bf6455e73d702'
helper=ROOT/'.runs/curate-runtime030-native-workflow-qualification-001.py';assert p.sha(helper)=='b20865bb1b48b9e49301781d99176464ca56120922d19c918b403f9e13f5f7e1'
refs={};files=[];material=[];total=0
defs=[n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='retain'];exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
base=ROOT/'scripts/windows_native_slice';protocols=[]
for prior,name in (('persistent_guard_build_protocol002.json','persistent_guard_build_protocol003.json'),('persistent_guard_lifetime_protocol.json','persistent_guard_lifetime_protocol002.json')):
 plan=f.read_json(base/prior);target=base/name;assert not target.exists()
 plan['source_files_sha256']={name:p.sha(ROOT/name) for name in plan['source_files_sha256']}
 plan['last_verified_checkpoint']='acdffee4276074cea454d940cbc2e018f6130944'
 plan['prior_actual_failure']='evidence/windows011-lifetime-actual001.json'
 plan['correction']='Win1307: request only actual process TokenOwner if SYSTEM/BA. First explicit OWNER_RIGHTS deny WRITE_DAC|WRITE_OWNER, unchangedPG_ACCESS System/BA allows, protected exactly3ACE/owner/group readback. No privilege enabling, extraallowprincipal or fallback.'
 plan['predeclared_decision']='Second and final corrective finite attempt for demonstrated owner1307 only. Preserve all outcomes; any new unresolved policy/denial/cleanup gate defers this bounded protocol. No installer/Native admission or mutation-resistance claim.'
 p.save_json(target,plan);protocols.append(dict(path=str(target.relative_to(ROOT)),sha256=p.sha(target)))
sources=[review,Path(__file__),ROOT/'.runs/curate-windows011-lifetime-actual001-command.log',ROOT/'.runs/curate-windows011-lifetime-actual001-time.log',ROOT/'.runs/curate-windows011-finite-state-mode-002-command.log',ROOT/'.runs/curate-windows011-finite-state-mode-002-time.log']
assert sum(len(io.read_bytes(q,4*1024**2)) for q in sources)<16*1024**2
for q in sources:retain(q,Path('controllers-reviews-costs')/q.name)
p.save_json(notes/'files.json',dict(schema=1,files=files,material=material))
record=dict(schema=1,kind='Windows011-owner1307-causal-correction-prospective',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 project_complete=False,actual_current_C_compiled=False,actual_policy_operations=False,CI_dispatched=False,Native_executed=False,Native_admitted=False,Windows_support=False,
 source_C=rd['source'],protocols=protocols,source_review_sha256=p.sha(review),
 causal_failure='evidence/windows011-lifetime-actual001.json',
 change=plan['correction'],precision='Deny ACE must be first; identical-mask SYSTEM/BA allows may exchange order without changing rights. Non-impersonating current controller only; unknown/defaultTokenOwner outsideSYSTEM/BA refuses.',
 constraints_unchanged='ABI1/INFO196, fixedSID/layers/BLOCK predicates, PG_ACCESS, all budgets, sticky poison/live retained custody/exactremoval and originalprofile/ACL safety remain. No security privilege/globalsetting changes.',
 claim_limits='Not demonstrated LowBox DACL/owner/delete resistance; actual mutationcontrols and fresh unchangedpolicy readback remain mandatory before that claim or anyNative/productadmission. NULL ABI alone does not prove validowner.',
 decision='One reviewed second finite IPv4TCP normal/cancel attempt after auditedpush/readback and fresh zero-cost/public/no-activeCI check. Any next unresolved gate closes this boundedownerprotocol without a thirdretry.',
 accounting='Actualfailed001 costs remainseparate. Curation/sourceauthoring/research/AIreview costsadditional; no routing gain, speed or completion claim.',
 files_index=dict(path=str((notes/'files.json').relative_to(ROOT)),sha256=p.sha(notes/'files.json')))
for row in material:assert p.sha(ROOT/row['original'])==p.sha(ROOT/row['retained'])==row['sha256']
p.save_json(packet,record);print(json.dumps(dict(protocols=protocols,files=len(files),bytes=total,CI_dispatched=False)))
