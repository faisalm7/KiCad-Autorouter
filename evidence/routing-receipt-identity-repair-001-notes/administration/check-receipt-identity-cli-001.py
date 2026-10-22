"""Actual CLI refusal against preserved invalidated058 receipt; no Native."""
from pathlib import Path
import json
from autorouter import pipeline as p,runner,gui
root=Path(__file__).resolve().parents[1];base=root/'.runs/receipt-identity-CLI-postfix-001';base.mkdir(mode=0o700)
route=root/'.runs/runtime-directory-058/runtime/.runs/native7-natural-expiry-eeprom-001/autorouter-gui-9bfb9e1a759f42718111d22bf25bcfc0/route'
archive=route/'invalidated-result-adbd003ac0424510bb53ca1153d1fc99.json'
pins={str(q):p.sha(q) for q in (archive,route/'result.json',root/'autorouter/pipeline.py',Path(__file__))}
env=gui.child_environment();env['PYTHONPATH']=str(root)
argv=['/usr/bin/sandbox-exec','-p','(version 1)(allow default)(deny network*)',str(root/'.venv/bin/python'),'-B','-m','autorouter','check-result',str(archive)]
process=runner.run(argv,cwd=base,env=env,log=base/'command.log',timeout=30,max_log_bytes=1024**2,max_group_rss_bytes=2*1024**3,max_workdir_bytes=2*1024**2)
p.save_json(base/'process.json',process)
raw=(base/'command.log').read_text();passed=process['exit_code']==2 and process['cleanup_complete'] and not process['log_truncated'] and 'routing receipt requires canonical result.json' in raw
assert all(p.sha(Path(q))==pin for q,pin in pins.items())
p.save_json(base/'result.json',dict(passed=passed,accepted=False,applied=False,Native=False,new_runtime_qualified=False,process_sha256=p.sha(base/'process.json'),pins=pins,scope='Actual modified-main CLI filename refusal before tool/source validation; unchanged058 archived and canonical bytes. Future fresh candidate Native positives still required.'))
print(json.dumps(dict(passed=passed,exit_code=process['exit_code'],cleanup_complete=process['cleanup_complete'])))
raise SystemExit(0 if passed else 2)
