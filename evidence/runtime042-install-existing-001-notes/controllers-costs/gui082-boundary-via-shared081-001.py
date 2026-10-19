"""Use the unchanged081 snapshot/readback algorithm with frozen082 identities.

Only pin/root/protocol binding substitutions are made. Actual screen observations
stay in the lead journal. No GUI or Native process is executed by this helper.
"""
from pathlib import Path
import sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
phase,workspace=sys.argv[1:]
assert phase in ('pre','post')
assert workspace=='autorouter-gui-611f6245c9c74b73817fb85276ba72c8'
name,pin={'pre':('gui081-preopen-001.py','49e86d07207ed9730070a469a5b49ab210199383f5cbad3311ea73ec1ed42de7'),'post':('gui081-postopen-001.py','98c8c0f4877342bef69c2391911f6970d04c2e3a01431f0276819e3a0133cea1')}[phase]
raw=(ROOT/'.runs'/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin
code=raw.decode()
for before,after in [
 ('7ea7e874fe2781e1c915f024a6a72edc05f7d631887d0cd9e744ea32a23242a3','83db7ce927031ea025b3c1db7cda713c7f63ecfa8b9870d87e28ddc7268268b3'),
 ('1dc25cf5133b7a0e0562704008b62bea328e46b61ec159a2bd326c3bf279aa2e','0fa1f13c4a43385d2d0b513c7c84fb89bb6370eb9962531018f0d1ccbfd6f039'),
 ('.runs/runtime-directory-042/runtime','.runs/runtime042 fresh install 001'),
 ('.runs/gui-session081','.runs/gui-session082'),
 ("protocol = Path(frozen['recovery_protocol'])","protocol = Path(frozen['protocol_required'])"),
 ("base / 'recovery-controls-001/protocol-required-001.json'","base / 'protocol-required-001.json'"),
 ("frozen['recovery_protocol_sha256']","frozen['protocol_required_sha256']")]:
 assert code.count(before)==1,(phase,before)
 code=code.replace(before,after)
sys.argv=[str(Path(__file__)),'positive',workspace]
exec(compile(code,str(Path(__file__))+'::shared-'+phase,'exec'),globals())
