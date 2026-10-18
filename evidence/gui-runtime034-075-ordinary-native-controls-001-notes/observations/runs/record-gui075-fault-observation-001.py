"""Record lead-observed GUI refusal, not a new validator or race oracle."""
from pathlib import Path
import json,sys,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'.runs/runtime-directory-034/runtime/.runs/gui-session075';label,workspace=sys.argv[1:];assert label in ('source','settings','export')
control=base/'freshness-controls-001'/label;w=base/'jobs'/workspace
pre=json.loads((control/'preopen-001.json').read_bytes());mutation=json.loads((control/'mutation-001.json').read_bytes());assert Path(pre['workspace'])==w and pre['route']['current'] is True and pre['export']['current'] is True
assert hashlib.sha256(Path(mutation['path']).read_bytes()).hexdigest()==mutation['after_sha256']
messages={'source':'Saved source project changed. Start a new session and preview again.','settings':'Captured settings changed. Start a new session.','export':'Checked export refused: current bounded fresh export proof required'}
record=dict(schema=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),kind=label,workspace=str(w),GUI_refusal_observed=True,GUI_message=messages[label],GUI_open_buttons_disabled=True,no_positive_state_adopted=True,retained_files_not_deleted=True,preopen_sha256=hashlib.sha256((control/'preopen-001.json').read_bytes()).hexdigest(),mutation_sha256=hashlib.sha256((control/'mutation-001.json').read_bytes()).hexdigest(),queue_hold_qualified=False,scope='Lead observed actual GUI Open checked export refusal after deliberate mutation BEFORE clicking Open. Not a forced worker-completion/queued-callback race. Existing callback regressions have separate software scope.')
with (control/'refusal-001.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
print(json.dumps(dict(label=label,observed_refusal_recorded=True)))
