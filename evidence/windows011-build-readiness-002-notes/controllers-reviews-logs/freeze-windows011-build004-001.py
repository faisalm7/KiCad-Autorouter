"""Freeze one distinct compile/NULL-only regression after failed policy002."""
import datetime,hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
dest=root/'scripts/windows_native_slice/persistent_guard_build_protocol004.json'
assert not dest.exists()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert head=='b89b032427246702284e1dea915a8054fd215cfc'
plan=json.loads((root/'scripts/windows_native_slice/persistent_guard_build_protocol003.json').read_text())
plan['source_files_sha256']={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in plan['source_files_sha256']}
assert plan['source_files_sha256']['scripts/windows_native_slice/persistent_sid_guard.c']=='8de5747968410e085d4b460a56080ee5987a8a83f22f29f776062351caf63714'
plan.update(last_verified_checkpoint=head,
 purpose='One build-null-only regression of the DWORD comparison cast after actual policy attempt002 failed MSVC C4389 under /W4 /WX. No valid owner/SID/profile/policy/socket or Native execution.',
 predeclared_decision='One compile/NULL-only execution: retain every failure or success. This is not a third policy attempt. The two-attempt real-policy011 protocol remains closed regardless of build result; no Windows/Native/owner/mutation admission.',
 prior_actual_failure='evidence/windows011-policy-attempt002-compile-failure-001.json',
 correction='Only cast the existing selected ACE mask to DWORD. Same rights, exact equality, ABI and /W4 /WX. No runner completion or cleanup policy changes.',
 real_policy_protocol_closed=True,
 mode='build-null',
 bounded_executions=1)
plan['bounds']={k:v for k,v in plan['bounds'].items() if not k.startswith(('normal_probe','cancel_probe','cancel_after'))}
plan['unqualified']=['Corrected actual owner and OWNER_RIGHTS policy/security normalization','All actual WFP policy, AppContainer profile, SID custody and network denial operations','Lowbox mutation, lifetime, cancellation, crash and identity reuse','IPv6, UDP, inbound, boot/BFE-off, nonadmin installation','Actual KiCad/JVM routing/cancel/refill/validation/export']
raw=(json.dumps(plan,indent=2)+'\n').encode();dest.write_bytes(raw)
print(json.dumps(dict(path=str(dest.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),source_files=plan['source_files_sha256'],real_policy_protocol_closed=True,Native_admitted=False)))
