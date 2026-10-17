from pathlib import Path
import json,sys,time,resource
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import gui,pipeline as p,floor_route as f
work=ROOT/'.runs/runtime-directory-018/runtime/.runs/production-delivery-001/jobs/autorouter-gui-4b4489cb692747d7bb17ddbbd79f8fcb'
path=work/'export/export.json';before=p.sha(path);record=f.read_json(path);code=p.sha(ROOT/'autorouter/gui.py')
start=time.monotonic();cpu=time.process_time()
gui.Workflow.check_open_export_material(SimpleNamespace(workspace=work,records={'export':record}))
wall=time.monotonic()-start;used=time.process_time()-cpu
assert p.sha(path)==before and p.sha(ROOT/'autorouter/gui.py')==code
out=ROOT/'.runs/gui-queued-open-material-readback-001';out.mkdir()
(out/'result.json').write_text(json.dumps(dict(schema=1,passed=True,Native_reexecuted=False,GUI_executed=False,
 gui_sha256=code,export_receipt_sha256=before,retained_export=str(path),material_files=len(record['export_evidence']['files']),
 material_directories=len(record['export_evidence']['directories']),guard_wall_seconds=wall,guard_parent_CPU_seconds=used,
 scope='One execution of the new GUI pure bounded material guard on the unchanged actual018 Native export. No Native checker, process/tool probe, GUI or routing rerun. This is not new019 Native acceptance or an end-to-end runtime claim.'),indent=2)+'\n')
print(json.dumps(dict(passed=True,guard_wall_seconds=wall,guard_parent_CPU_seconds=used)))
