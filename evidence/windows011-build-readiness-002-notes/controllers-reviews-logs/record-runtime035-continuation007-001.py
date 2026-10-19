"""Record the exact closed policy protocol and pending compile-only check."""
import datetime,hashlib,json,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];dest=root/'evidence/runtime035-continuation-007.json';assert not dest.exists()
j=json.loads((root/'evidence/runtime035-continuation-006.json').read_text())
j['recorded_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
j['last_independently_verified_checkpoint']='b89b032427246702284e1dea915a8054fd215cfc'
j['current_packets'] += [{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in ('evidence/windows011-policy-attempt002-compile-failure-001.json',)]
j['hierarchy']['next']='Narrow read-only binder contract assessment in progress: versioned full instance/unit/lib alias/pin/Default-class identity and exact unconnected-pad census. Do not repeat completed observation or admit support before implementation/native invalid controls; no automatic two-family gain.'
j['Windows'].update(stage='Both policy011 attempts failed; closed protocol. Separate build-null004 prospective.',actual002_run=39210366235,actual002_source='b89b032427246702284e1dea915a8054fd215cfc',actual002_evidence='evidence/windows011-policy-attempt002-compile-failure-001.json',actual002_failure='C4389/C2220 at C157 before DLL/NULL/profile/policy; mainexit2; remaining owned member waited to original30s cap, all3 reaped.',current_C_source_sha256=hashlib.sha256((root/'scripts/windows_native_slice/persistent_sid_guard.c').read_bytes()).hexdigest(),real_policy_protocol_closed=True,
 build_only_protocol='scripts/windows_native_slice/persistent_guard_build_protocol004.json',build_only_protocol_sha256=hashlib.sha256((root/'scripts/windows_native_slice/persistent_guard_build_protocol004.json').read_bytes()).hexdigest(),
 next='After contract review, auditedpush/readback and fresh public/sequential preflight, dispatch exactly one windows-guard-build with exactnewcommit/build004SHA. No third policy attempt, owner/mutation/Native qualification, installer or broader Windows claim. Return focus to Mac/product binder and actualGUI gate.')
j['owned_processes']='Actual002 CI completed failure; all other modes skipped. No owned Mac Native/JVM/GUI/full-suite/backup worker. Only CUA support runtimes remain; do not kill from saved PIDs.'
j['backup']['free_bytes']=shutil.disk_usage(root).free
j['backup']['scope']='Essential Windows002 compile-failure text/source and prospectivebuild004 prepared for audited Git. No state/profile/policy/DLL created002. Newer Mac raw/preparedGUI remainMac-only outside008/010. Current free space is below prior18.64GB restore lower bound; no restore/delete/capraise.'
j['prospective_working_changes']='One DWORD cast, PS build004 default, workflow removal of real-policy selection/fixedbuild-null plus immutable build004 protocol and current compactdocs. Existing unpublished records/tmpdirs retained.'
j['publication_gate']={'status':'Resolved without override; b89 fastforward pushed and independent file/SHA readback passed.','retained_rejected_commit':'236eb077647fb6de67fe4ee7bb690b9fa50fcb29','local_ref':'refs/local-checkpoints/windows011-owner1307-push-rejected-001','reason':'Generated policyGUIDfilename tokens matched Mailgun syntax. Public aliases usepolicy-guid; raw and rejectedcommit remainlocal. No settingchange/forcepush/unblockoverride.'}
j['additional_costs']['curate_actual002_compile_failure']={'wall_seconds':0.24,'CPU_seconds':0.17}
dest.write_text(json.dumps(j,indent=2)+'\n');print(dest.relative_to(root))
