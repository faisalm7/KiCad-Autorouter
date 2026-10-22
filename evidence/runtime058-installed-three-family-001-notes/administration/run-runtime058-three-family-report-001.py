"""One finite reporting invocation using the existing shared process runner."""
from pathlib import Path
import hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import runner,pipeline as p,handoff as h,provenance as pv
from autorouter.gui import child_environment
self_pin=p.sha(Path(__file__))
BASE=ROOT/'.runs/runtime058-installed-three-family-001'
ENCLOSURE=ROOT/'.runs/runtime058-installed-three-family-report-enclosure-001'
FACTS=ROOT/'.runs/runtime058-installed-three-family-report-001'
POP='7aa591a491b9358868c351b4cf357dcbe38351185bdfc5a7e91832a5330a71f8'
CHILDREN='c0e04f9d0751cf1272abe00ed68ec3af9ccdea53759d32695c3d950fe0895b8f'
assert pv.git_head(ROOT)=='f832b0435ea231332de1ac3831d166bc71c10b12'
assert not os.path.lexists(ENCLOSURE) and not os.path.lexists(FACTS)
assert p.sha(BASE/'population.json')==POP and p.sha(BASE/'frozen-children.json')==CHILDREN
assert p.sha(ROOT/'scripts/report_current_comparison.py')=='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
frozen=json.loads((BASE/'frozen-children.json').read_bytes())
assert all((Path(row['path']).parent/'enclosure/result.json').is_file() for rows in frozen['protocols'].values() for row in rows.values())
ENCLOSURE.mkdir(mode=0o700);owner={};h.capture_destination(owner,ENCLOSURE)
argv=[str(ROOT/'.venv/bin/python'),'-B',str(ROOT/'scripts/report_current_comparison.py'),
 '--population',str(BASE/'population.json'),'--population-sha256',POP,
 '--children',str(BASE/'frozen-children.json'),'--children-sha256',CHILDREN,
 '--output',str(FACTS),'--public-sanitize']
process=runner.run(argv,cwd=ENCLOSURE,env=child_environment(),log=ENCLOSURE/'command.log',timeout=60,
 max_log_bytes=1024**2,max_group_rss_bytes=1024**3,max_workdir_bytes=2*1024**2)
h.owned_destination(owner);assert p.sha(Path(__file__))==self_pin
assert p.sha(ROOT/'scripts/report_current_comparison.py')=='0ba011298586ee7e89ffaa65c9184a6a25ef231f819c34474d2e3b75b557982e'
p.save_json(ENCLOSURE/'process.json',process)
passed=process['status']=='success' and process['exit_code']==0 and process['cleanup_complete'] and not process['log_truncated']
print(json.dumps(dict(passed=passed,process_sha256=p.sha(ENCLOSURE/'process.json'),
 report_sha256=p.sha(FACTS/'report.json') if passed else None,index_sha256=p.sha(FACTS/'files.json') if passed else None,
 Native=False,engine=False,controller_sha256=self_pin)))
raise SystemExit(0 if passed else 2)
