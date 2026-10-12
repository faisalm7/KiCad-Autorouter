"""Read-only saved-evidence interpretation. No Java, native, routing, or test execution."""
import hashlib, importlib.util, json, math, re, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
RUN=ROOT/'.runs/custom-pad-area-probe-001'
HELP=ROOT/'experiments/custom_pad_area_probe_v1'
def sha(raw): return hashlib.sha256(raw).hexdigest()
summary_raw=(RUN/'summary.json').read_bytes(); summary=json.loads(summary_raw)
for name in ('driver.py','derive.py','checks.py'):
    rel=str((HELP/name).relative_to(ROOT)); assert sha((HELP/name).read_bytes())==summary['runtime']['sources'][rel]['sha256']
sys.path.insert(0,str(HELP)); sys.path.insert(0,str(ROOT))
import driver as d, derive, checks
before=d.inventory(RUN); sources=summary['runtime']['sources']; runtime=d.decode(d.content(RUN/'runtime.json'))
assert runtime==summary['runtime']
assert all(before.get(k)==v for k,v in summary['frozen_evidence'].items())
assert set(before)==set(summary['frozen_evidence'])|{'summary.json'}
source_raw={}
for rel,pin in sources.items():
    raw=d.content(ROOT/rel,1024**2); source_raw[rel]=raw
    assert {'bytes':len(raw),'sha256':sha(raw)}==pin
    assert d.content(RUN/'code'/rel,1024**2)==raw
# One read-only Git object query verifies recorded source bytes against the recorded commit.
requests=[summary['runtime']['git']['head']+':'+rel for rel in sources]
p=subprocess.run(['git','cat-file','--batch'],input=('\n'.join(requests)+'\n').encode(),cwd=ROOT,capture_output=True,check=True,timeout=10)
cursor=0
for rel in sources:
    end=p.stdout.index(b'\n',cursor); header=p.stdout[cursor:end].split(); size=int(header[2]); assert header[1]==b'blob'
    raw=p.stdout[end+1:end+1+size]; assert raw==source_raw[rel]; cursor=end+size+2
assert cursor==len(p.stdout)
protocol=d.decode(d.content(HELP/'PROTOCOL.json'))
for name,pin in protocol['tools'].items():
    path=Path(pin['path']); path=path if path.is_absolute() else ROOT/path
    assert d.content(path,pin['bytes'],digest=True)==runtime['tools'][name]=={k:pin[k] for k in ('bytes','sha256')}
inputs,expected=derive.prepare(RUN/'code',lambda path:d.content(path,1024**2))
assert expected==d.decode(d.content(RUN/'expectations.json'))==protocol['expected']
assert all(d.content(RUN/'inputs'/name)==raw and sha(raw)==protocol['input_sha256'][name] for name,raw in inputs.items())
observed=d.decode(d.content(RUN/'observations.json',262144))
assert sha(d.content(RUN/'observations.json'))==summary['observations_sha256']
assert checks.validate(observed,expected)==summary['case_comparison']
jar=ROOT/protocol['tools']['jar']['path']; home=str(RUN/'home')
argvs=[[*d.SANDBOX,protocol['tools']['javac']['path'],'-J-Xmx256m','-J-Duser.home='+home,'-proc:none','-classpath',str(jar),'-d',str(RUN/'classes'),str(RUN/'code'/HELP.relative_to(ROOT)/'AreaContactProbe.java')],
       [*d.SANDBOX,protocol['tools']['java']['path'],'-Xmx256m','-Djava.awt.headless=true','-Duser.home='+home,'-Djava.io.tmpdir='+str(RUN/'tmp'),'-cp',str(RUN/'classes')+':'+str(jar),'AreaContactProbe',str(RUN/'inputs'),str(RUN/'observations.json')]]
for step,name,argv in zip(summary['steps'],('compile','import'),argvs):
    assert step['name']==name and step['argv']==argv and step['cwd']==str(RUN)
    assert d.decode(d.content(RUN/(name+'-process.json')))=={k:v for k,v in step.items() if k!='name'}
    assert step['status']=='success' and step['exit_code']==0 and step['cleanup_complete'] is True
    assert step['log']==str(RUN/(name+'.log')) and step['log_bytes']==len(d.content(RUN/(name+'.log')))==0
assert len(summary['steps'])==2
for key in ('wall_seconds','total_cpu_seconds'):
    assert math.isfinite(summary[key]) and 0<summary[key]<60
assert summary['total_cpu_seconds']>=sum(s['cpu_seconds'] for s in summary['steps'])
assert summary['wall_seconds']>=sum(s['wall_seconds'] for s in summary['steps'])
rows=[]
for case,want in zip(observed['cases'],expected):
    states=[]
    for s in case['states']:
        items=s['pins']+s['areas']+s['traces']; graph={x['id']:set(x['contacts']) for x in items}; pins={p['reference']:p for p in s['pins']}; pin_ids={p['id'] for p in s['pins']}
        areas={a['reference']:next(x for x in s['areas'] if derive.canonical_ring(x['ring_um'])==derive.canonical_ring(a['ring_um'])) for a in want['areas']}
        rings=[]
        for target in want['areas']:
            a=areas[target['reference']]; ring=a['ring_board_integer']; twice=abs(sum(x[0]*y[1]-x[1]*y[0] for x,y in zip(ring,ring[1:]+ring[:1])))
            area=checks.number(twice)/(2*checks.number(s['board_units_per_um'])**2)
            assert checks.integer_coordinate_witness(a,s,area=True) and area==target['area_um2']
            assert a['holes']==0 and a['net']=='CONTACT' and a['layer']==want['layer'] and a['fixed']=='USER_FIXED'
            rings.append({'reference':target['reference'],'exact_ring_match':True,'shoelace_area_um2':float(area),'api_area_um2':a['area_um2']})
        name_rows=[]
        for target in want['pins']:
            actual=pins[target['reference']]; normalized=re.sub(r'\.\d+','',target['padstack_name'])
            assert all(actual[k]==target[k] for k in ('number','net','position_um')) and actual['layers']==[want['layer']]
            assert actual['padstack_name']==normalized
            name_rows.append({'reference':target['reference'],'source_name':target['padstack_name'],'imported_name':actual['padstack_name']})
        # Repeated FOREIGN_A/B names are intentional; different source names must not collide.
        assert len({p['source_name'] for p in name_rows})==len({p['imported_name'] for p in name_rows})
        terminal_rows=[]
        for ref,pin in pins.items():
            reached={pin['id']}; pending=[pin['id']]
            while pending:
                for target in graph[pending.pop()]-reached: reached.add(target);pending.append(target)
            intended={p['id'] for p in s['pins'] if p['net']==pin['net']}
            if pin['net']=='CONTACT' and want['kind']=='false_hull': intended={pin['id']}
            engine=pin_ids&(set(pin['connected'])|{pin['id']}); graph_peers=pin_ids&reached
            terminal_rows.append({'reference':ref,'expected_pin_ids':sorted(intended),'engine_pin_ids':sorted(engine),'graph_pin_ids':sorted(graph_peers),'matches':engine==graph_peers==intended})
        foreign=next(t for t in s['traces'] if t['net']=='FOREIGN')
        states.append({'mode':s['mode'],'rings':rings,'names':name_rows,'reciprocal_graph':all(a in graph[b] for a,peers in graph.items() for b in peers),
            'terminal_rows':terminal_rows,'foreign_tree_clear':foreign['tree_trace_check_clear'],'foreign_tree_overlap_ids':foreign['tree_overlap_ids'],
            'foreign_area_clearances_um':foreign['area_clearances_um'],'plane_nets':[n['contains_plane'] for n in s['nets']]})
    rows.append({'case':case['case'],'parser_warnings':case['parser_warnings'],'recorded_hypothesis_matches':False,'posthoc_states':states})
assert d.inventory(RUN)==before
assert all(d.content(ROOT/rel,1024**2)==raw for rel,raw in source_raw.items())
result={'schema':1,'scope':'AI read-only saved evidence consistency and posthoc interpretation; no rerun, authentication, or new qualification',
    'run':str(RUN.relative_to(ROOT)),'recorded_head':runtime['git']['head'],'summary_sha256':sha(summary_raw),'observations_sha256':summary['observations_sha256'],
    'frozen_files_verified':len(summary['frozen_evidence']),'complete_run_files':len(before),'complete_run_bytes':sum(x['bytes'] for x in before.values()),
    'runtime_source_files_verified':len(sources),'tool_pins_verified':list(runtime['tools']),'source_commit_blobs_verified':True,
    'six_derived_dsns_reproduced_exactly':True,'original_checker_comparison_reproduced':True,'two_processes_argv_status_logs_bound':True,
    'recorded_status':summary['status'],'recorded_expected_observations_match':summary['expected_observations_match'],
    'recorded_observations_complete':summary['observations_complete'],'stored_wall_seconds':summary['wall_seconds'],'stored_cpu_seconds':summary['total_cpu_seconds'],
    'accounting_point':summary['accounting_point'],'run_and_current_recorded_sources_unchanged':True,
    'cases':rows,'routing_accepted':False,'custom_pad_support_qualified':False}
(OUT/'audit.json').write_bytes(d.canonical(result))
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2))
