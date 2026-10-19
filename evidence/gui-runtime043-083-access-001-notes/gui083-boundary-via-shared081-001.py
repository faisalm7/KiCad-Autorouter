"""Reuse unchanged pre/postopen snapshot logic with explicit GUI083 identities.

No GUI or Native worker is executed. Production readers run in pre phase only;
screen observations and any post-editor changes remain separately recorded.
"""
from pathlib import Path
import hashlib, sys

ROOT = Path(__file__).resolve().parents[1]
phase, role, workspace = sys.argv[1:]
assert phase in ('pre', 'post') and role in ('partial', 'fractional')
assert workspace == Path(workspace).name and workspace.startswith('autorouter-gui-')
name, pin = {
    'pre': ('gui081-preopen-001.py', '49e86d07207ed9730070a469a5b49ab210199383f5cbad3311ea73ec1ed42de7'),
    'post': ('gui081-postopen-001.py', '98c8c0f4877342bef69c2391911f6970d04c2e3a01431f0276819e3a0133cea1'),
}[phase]
raw = (ROOT / '.runs' / name).read_bytes()
assert hashlib.sha256(raw).hexdigest() == pin
code = raw.decode()
replacements = [
    ('7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3', '496a5f4dafda875512ffa1b15c5b756e5eaa1cb8a8ecda7f3dba5fcfa9f3817f'),
    ('82aaa3b750007ef2ffaafd367ffcb718aa93865e', '6ec7ad2344ed060d5e0971965ef05bd9de68925d'),
    ('1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e', '6fdfe60bcbe6aecc2c950a6917b22d8e591f5ae3078eca5a52ae051a1aac5aa3'),
    ('.runs/runtime-directory-042/runtime', '.runs/runtime-directory-043/runtime'),
    ('.runs/gui-session081', '.runs/gui-session083'),
    ("frozen['prerequisites_sha256']", "frozen['prerequisite_sha256']"),
    ("protocol = Path(frozen['recovery_protocol'])", "protocol = base / 'protocol-required-001.json'"),
    ("base / 'recovery-controls-001/protocol-required-001.json'", "base / 'protocol-required-001.json'"),
    ("frozen['recovery_protocol_sha256']", "frozen['protocol_required_sha256']"),
    ("prepared['alias_required']", "prepared['roles']['fractional-owned']"),
    ("prepared['source_hashes']", "prepared['roles']['partial2Cu']['source_hashes']"),
]
for before, after in replacements:
    assert before in code, (phase, before)
    code = code.replace(before, after)
sys.argv = [str(Path(__file__)), 'positive' if role == 'partial' else 'alias_positive', workspace]
exec(compile(code, str(Path(__file__)) + '::shared-' + phase, 'exec'), globals())
