"""One prospective original-HFE schematic export; never routing acceptance.
SPDX-License-Identifier: GPL-3.0-or-later
Caller must freeze this file and use the existing bounded enclosing runner.
"""
import time,resource
START=time.monotonic()
def cpu():return sum(x.ru_utime+x.ru_stime for x in (resource.getrusage(resource.RUSAGE_SELF),resource.getrusage(resource.RUSAGE_CHILDREN)))
CPU0=cpu()
from pathlib import Path
import argparse,collections,fcntl,hashlib,json,os,signal,stat,sys
ROOT=next(x for x in Path(__file__).resolve().parents if (x/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from autorouter import pipeline as p,floor_route as f,handoff as h,placement_clearance as io,sexpr as sx,board_floor as g,local_settings as ls,schematic_fields as fields,schematic_field_evidence as field_evidence
from experiments.hfe_original_native_v1 import driver as original
from experiments.placement_handoff_native_v1.driver import copy_bytes
WHOLE=60;LIMIT=128*1024**2
RECEIPT=ROOT/'.runs/hfe-original-native-execution-001/native/result.json'
REPORT=RECEIPT.parent/'job/original-final.json'
# Exact values below are filled by pure draft preparation, never by a route receipt.
RECEIPT_PIN='a3aaf2ea70bf687fd81a4bdfcdcba2f3db74da83c4d53fa52b7812cbea7b0cdb'
REPORT_PIN='9daa9b6ffa53a801560f148ea64b530debb32e3182eb1f8fc5770cbc2060e9a0'
NATIVE_TOOLCHAIN={'schema': 1, 'mode': 'experimental-native-qualification', 'expected_version': '10.0.7', 'tools': {'cli': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/MacOS/kicad-cli', 'sha256': '0b9d96dbdac9517e7d85833f926fee07a563549ffe2c55670147bff3f562d01f'}, 'python': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9', 'sha256': 'fd8c2fa5393bebb9be6789dab8583acee6c5cff90d42696e8c1dbcabe02ec39f'}, 'pcbnew': {'path': '/Users/faisal/Projects/KiCad-Autorouter-local/.tools/kicad-10.0.7-local-001/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/_pcbnew.so', 'sha256': '610ae51927809192be637d0de03c32d006332638e2272cbf11a553fe65c75f6e'}}}


def members(netlist,board,report):
    """Complete logical/physical census; unsupported semantics stay diagnostic."""
    tree=sx.parse(netlist);observed={'source':str(board)}
    components=fields.components(netlist,observed,native_version='10.0.7')
    single=fields.singleton;reasons=[];library={};declared={};node_members=collections.defaultdict(list)
    for part in sx.one(tree,'libparts')[1:]:
        if not isinstance(part,list) or part[0]!='libpart':raise ValueError('unknown native libparts member')
        key=(single(part,'lib'),single(part,'part'))
        if key in library:raise ValueError('duplicate native libpart identity')
        pins=sx.one(part,'pins')
        if pins is None:raise ValueError('complete native library pin census absent')
        rows=[]
        for pin in pins[1:]:
            if not isinstance(pin,list) or pin[0]!='pin':raise ValueError('unknown native library pin member')
            rows.append({'number':single(pin,'num'),'name':single(pin,'name'),'type':single(pin,'type'),'raw_ast':pin})
        library[key]=rows
    comps=sx.children(sx.one(tree,'components'),'comp')
    if len(comps)!=len(components):raise ValueError('native component census differs')
    for comp in comps:
        ref=single(comp,'ref');libsource=sx.one(comp,'libsource')
        key=(single(libsource,'lib'),single(libsource,'part'))
        if key not in library:raise ValueError('component lacks complete native libpart')
        declared[ref]=library[key]
        numbers=[row['number'] for row in library[key]]
        if not numbers or any(not n for n in numbers) or len(numbers)!=len(set(numbers)):
            reasons.append({'kind':'ambiguous_library_pin_population','reference':ref,'numbers':numbers})
    nets=[];codes=set();names=set()
    section=sx.one(tree,'nets')
    if section is None:raise ValueError('complete native nets absent')
    for net in section[1:]:
        if not isinstance(net,list) or net[0]!='net':raise ValueError('unknown native nets member')
        code=single(net,'code');name=single(net,'name')
        if not code.isdecimal() or code in codes or not name or name in names:raise ValueError('non-bijective native net code/name')
        codes.add(code);names.add(name);rows=[]
        unknown=[child for child in net[1:] if not isinstance(child,list) or not child or child[0] not in {'code','name','class','node'}]
        if unknown:reasons.append({'kind':'unknown_export_net_members','members':unknown})
        if int(code)<=0:reasons.append({'kind':'nonpositive_native_net_code','code':code,'name':name})
        for node in sx.children(net,'node'):
            ref,number=single(node,'ref'),single(node,'pin');key=(ref,number)
            attrs={key:fields.singleton(node,key) for key in ('pinfunction','pintype') if sx.one(node,key) is not None}
            unknown=[child for child in node[1:] if not isinstance(child,list) or not child or child[0] not in {'ref','pin','pinfunction','pintype'}]
            if unknown:reasons.append({'kind':'unknown_export_node_members','reference':ref,'number':number,'members':unknown})
            rows.append({'reference':ref,'number':number,'attributes':attrs,'raw_ast':node})
            node_members[key].append({'code':code,'name':name,'attributes':attrs,'raw_ast':node})
            if ref not in declared or number not in {r['number'] for r in declared[ref]}:
                reasons.append({'kind':'undeclared_export_terminal','reference':ref,'number':number})
        if not rows:reasons.append({'kind':'empty_export_net','code':code,'name':name})
        nets.append({'code':code,'name':name,'name_has_unconnected_prefix':name.startswith('unconnected-'),'nodes':rows})
    schkeys={(ref,row['number']) for ref,rows in declared.items() for row in rows}
    pcb=sx.parse(io.read_bytes(board).decode());_,resolve=g.source_net_identity(pcb)
    footprints=[];padgroups=collections.defaultdict(list);ids=set();refs=set();mechanical=[]
    for fp in sx.children(pcb,'footprint'):
        properties=[r for r in sx.children(fp,'property') if len(r)>=3 and sx.unquote(r[1])=='Reference']
        if len(properties)!=1:raise ValueError('ambiguous source footprint reference')
        ref=fields.atom(properties[0][2]);uid=single(fp,'uuid')
        if not ref or fields.UUID.fullmatch(uid) is None or ref.casefold() in refs or uid in ids:raise ValueError('duplicate footprint reference/UUID')
        refs.add(ref.casefold());ids.add(uid);pads=[]
        for pad in sx.children(fp,'pad'):
            if len(pad)<4 or any(not isinstance(x,str) for x in pad[:4]):raise ValueError('unknown source pad header')
            puid=single(pad,'uuid');number=fields.atom(pad[1]);net=resolve(sx.one(pad,'net'))
            if fields.UUID.fullmatch(puid) is None or puid in ids:raise ValueError('duplicate source pad/footprint UUID')
            ids.add(puid)
            row={'uuid':puid,'footprint_uuid':uid,'reference':ref,'number':number,'attribute':pad[2],'net':net,'layers':sx.one(pad,'layers'),
                 'disposition':'positive_named_net' if net else 'no_net','raw_net_ast':sx.one(pad,'net')}
            pads.append(row)
            if number:padgroups[(ref,number)].append(row)
            else:
                mechanical.append(row)
                if pad[2]!='np_thru_hole' or net:reasons.append({'kind':'unmapped_numberless_electrical_pad','uuid':puid})
        footprints.append({'reference':ref,'uuid':uid,'symbol_path':sx.one(fp,'path'),'pads':pads})
    pcbrefs={row['reference'] for row in footprints}
    if pcbrefs!=set(components):reasons.append({'kind':'component_footprint_census','only_schematic':sorted(set(components)-pcbrefs),'only_pcb':sorted(pcbrefs-set(components))})
    pcbkeys=set(padgroups)
    if pcbkeys!=schkeys:reasons.append({'kind':'terminal_census','only_schematic':sorted(schkeys-pcbkeys),'only_pcb':sorted(pcbkeys-schkeys)})
    terminal=[];mapping=collections.defaultdict(set);reverse=collections.defaultdict(set);mismatch_pads=[]
    pcbparts=collections.defaultdict(set);schparts=collections.defaultdict(set)
    for ref,number in sorted(pcbkeys|schkeys|set(node_members)):
        key=(ref,number);pads=padgroups.get(key,[]);nodes=node_members.get(key,[])
        pn={r['net'] for r in pads};sn={r['name'] for r in nodes}
        dispositions=[]
        if any(r['name'].startswith('unconnected-') for r in nodes):dispositions.append('generated_unconnected_name_pattern_only')
        if any('no_connect' in r['attributes'].get('pintype','').split('+') for r in nodes):dispositions.append('export_pintype_has_no_connect_marker')
        if any(not r['net'] for r in pads):dispositions.append('pcb_no_net_never_unioned')
        if len(pads)>1:dispositions.append('multiple_physical_pads_same_terminal')
        if not nodes:dispositions.append('absent_from_export_nets_unqualified')
        if len(nodes)>1:dispositions.append('duplicate_export_nodes_unqualified')
        if len(pn)!=1 or len(sn)!=1 or len(nodes)!=1 or '' in pn:
            reasons.append({'kind':'unresolved_terminal_membership','reference':ref,'number':number})
        else:
            before=next(iter(pn));after=next(iter(sn));mapping[before].add(after);reverse[after].add(before)
            pcbparts[before].add(key);schparts[after].add(key)
            if before!=after:mismatch_pads.extend({'uuid':r['uuid'],'pcb_net':before,'schematic_net':after} for r in pads)
        terminal.append({'reference':ref,'number':number,'declared_library_pins':[r for r in declared.get(ref,[]) if r['number']==number],
            'pcb_pads':pads,'export_memberships':nodes,'dispositions':dispositions})
    if any(len(v)!=1 for v in (*mapping.values(),*reverse.values())):reasons.append({'kind':'nonbijective_net_renaming'})
    pp=sorted(sorted(v) for v in pcbparts.values());sp=sorted(sorted(v) for v in schparts.values())
    if pp!=sp:reasons.append({'kind':'terminal_partition_mismatch'})
    # Compare the independently derived physical mismatch population against ALL
    # retained raw warnings; never obtain net aliases from warning prose.
    expected={r['uuid']:r for r in mismatch_pads};warned=[]
    for row in report['schematic_parity']:
        items=row.get('items',[])
        if row.get('type')!='net_conflict' or row.get('severity')!='warning' or row.get('excluded',False) or len(items)!=1:
            reasons.append({'kind':'other_original_parity_finding','finding':row});continue
        uid=items[0].get('uuid');warned.append(uid);pair=expected.get(uid)
        if pair is None or row.get('description')!=f"Pad net ({pair['pcb_net']}) doesn't match net given by schematic ({pair['schematic_net']})":
            reasons.append({'kind':'original_warning_terminal_mismatch','uuid':uid})
    if len(warned)!=len(set(warned)) or set(warned)!=set(expected):reasons.append({'kind':'original_warning_population_mismatch'})
    proposed={key:next(iter(value)) for key,value in mapping.items() if len(value)==1 and key!=next(iter(value))}
    return {'components':components,'library_pin_census':[{'library':key[0],'part':key[1],'pins':rows} for key,rows in sorted(library.items())],
        'footprints':footprints,'numberless_pads':mechanical,'export_nets':nets,'terminals':terminal,
        'logical_terminal_count':len(schkeys),'physical_pad_count':sum(len(r['pads']) for r in footprints),
        'pcb_positive_partitions':[{'net':n,'terminals':sorted(v)} for n,v in sorted(pcbparts.items())],
        'schematic_positive_partitions':[{'net':n,'terminals':sorted(v)} for n,v in sorted(schparts.items())],
        'rename_only_hypothesis':not reasons and bool(proposed),'proposed_rename_map':proposed if not reasons else None,'unqualified_reasons':reasons,
        'original_parity_findings':report['schematic_parity'],'original_ignored_checks':report['ignored_checks'],
        'limitation':'Logical membership/label diagnostic only; no circuit repair, Native waiver, connectivity rerun or board support admission.'}


def main(head,controller_pin,output):
    original.clean(head);packet=original.source()
    if p.sha(Path(__file__))!=controller_pin or p.sha(RECEIPT)!=RECEIPT_PIN or p.sha(REPORT)!=REPORT_PIN:raise p.Rejected('frozen controller/original proof changed')
    if p.sha(original.PROOF)!=original.PROOF_PIN:raise p.Rejected('signed bundle proof changed')
    nt=p.ExperimentalNativeToolchain.from_record(NATIVE_TOOLCHAIN);tools=p.tool_manifest(native_toolchain=nt)
    if tools['git_head']!=head:raise p.Rejected('caller checkpoint differs')
    raw_report=f.read_json(REPORT)
    if raw_report['kicad_version']!='10.0.7' or len(raw_report['schematic_parity'])!=18 or len(raw_report['ignored_checks'])!=11:raise p.Rejected('retained original raw population differs')
    if len(original.route_records(sx.parse(packet[original.STEM+'.kicad_pcb'].decode())))!=785:raise p.Rejected('original785route identity census differs')
    output=h.real_path(output,existing=False)
    if ROOT/'.runs' not in output.parents:raise p.Rejected('fresh canonical .runs destination required')
    output.mkdir();owner={};h.capture_destination(owner,output)
    def remaining():return min(WHOLE-2-(time.monotonic()-START),WHOLE-2-(cpu()-CPU0))
    job=original.BoundJob(output/'job',30,remaining,native_toolchain=nt,protect_local_settings=True)
    prl=(json.dumps({'meta':{'filename':original.STEM+'.kicad_prl','version':5},'board':{'active_layer':0,'hidden_nets':[],'hidden_netclasses':[]}},indent=2,sort_keys=True)+'\n').encode()
    # Original six files are byte-exact; only this explicitly owned PRL is added.
    isolated=dict(packet);isolated[original.STEM+'.kicad_prl']=prl
    copy_bytes(isolated,job.out/'input');board=job.out/'input'/(original.STEM+'.kicad_pcb');before=p.tree_hash(board.parent)
    names=set(tools['implementation_sha256'])|{str(Path(__file__).relative_to(ROOT)),'experiments/hfe_original_native_v1/driver.py','experiments/placement_handoff_native_v1/driver.py'}
    code={name:p.sha(ROOT/name) for name in sorted(names)}
    copy_bytes({name:io.read_bytes(ROOT/name,1024**2) for name in code},output/'control-code')
    plan=dict(schema=1,git_head=head,source_commit=original.COMMIT,source_sha256=original.SOURCE_PINS,
        tools=tools,native_toolchain=NATIVE_TOOLCHAIN,controller_sha256=controller_pin,code_sha256=code,
        acquisition_sha256=p.sha(original.ACQUISITION),original_receipt_sha256=RECEIPT_PIN,original_report_sha256=REPORT_PIN,
        owned_prl_sha256=hashlib.sha256(prl).hexdigest(),input_with_owned_prl_sha256=before,
        limits=dict(whole_wall_full_cpu_seconds=WHOLE,worker_wall_seconds=30,scratch_bytes=LIMIT,group_rss_bytes=2*1024**3,log_bytes=256*1024,publication_allowance_seconds=2))
    copy_bytes({'original-result.json':io.read_bytes(RECEIPT),'original-final.json':io.read_bytes(REPORT)},output/'retained-original-proof')
    p.save_json(output/'protocol.json',plan);plan_pin=p.sha(output/'protocol.json')
    argv=field_evidence.arguments(job.out,'parity-probe',board,native_toolchain=nt)[0]
    name=field_evidence.names('parity-probe')[0];netlist=field_evidence.paths(job.out,'parity-probe')[0]
    record=dict(schema=1,accepted=False,passed=False,status='failed',production_support_qualified=False,observation_complete=False,
        tools=tools,protocol_sha256=plan_pin,source_sha256=original.SOURCE_PINS,source_route_count=785,steps=job.steps,netlist_sha256=None,
        scope='One original-HFE native schematic kicadsexpr export only; complete terminal census. No DRC/engine/refill/routing/repair/support or warning waiver.')
    lane=os.open(ROOT/'.runs/quality-experiment.lock',os.O_RDWR|os.O_NOFOLLOW)
    with os.fdopen(lane,'r+') as lock:
        info=os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise p.Rejected('ordinary shared lane required')
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            ls.protected_step(job,name,argv)
            if p.tree_hash(board.parent)!=before:raise p.Rejected('native netlist export changed isolated project')
            record['netlist_sha256']=p.sha(netlist)
            record['terminal_comparison']=members(io.read_bytes(netlist).decode(),board,raw_report)
            record.update(passed=True,status='completed',observation_complete=True)
        except (Exception,KeyboardInterrupt) as exc:
            record.update(passed=False,status='cancelled' if isinstance(exc,KeyboardInterrupt) or any(step.get('status')=='cancelled' for step in job.steps) else 'failed',error=type(exc).__name__+': '+str(exc))
            if netlist.is_file() and not netlist.is_symlink():record['netlist_sha256']=p.sha(netlist)
        witness=original.material(output);record['completed_evidence']=witness
        def stable():
            h.owned_destination(owner);original.clean(head);original.source()
            if (p.tool_manifest(native_toolchain=nt)!=tools or p.sha(RECEIPT)!=RECEIPT_PIN or p.sha(REPORT)!=REPORT_PIN
                    or p.sha(original.PROOF)!=original.PROOF_PIN or p.sha(original.ACQUISITION)!=plan['acquisition_sha256']
                    or p.sha(output/'protocol.json')!=plan_pin or f.canonical(f.read_json(output/'protocol.json'))!=f.canonical(plan)
                    or any(p.sha(ROOT/n)!=pin for n,pin in code.items()) or original.material(output)!=witness
                    or p.tree_hash(board.parent)!=before):raise p.Rejected('probe code/source/tool/project/material changed')
            if record['observation_complete']:
                proc=f.process_check(job.out,record,name,[*f.SANDBOX,*argv])
                if p.sha(netlist)!=record['netlist_sha256']:raise p.Rejected('netlist changed')
                ls.check_preserved(board.with_suffix('.kicad_prl'),before,proc['local_settings_protection'])
            if remaining()<=0:raise p.Rejected('probe whole wall/fullCPU budget exhausted')
        def account():
            record.update(wall_seconds=time.monotonic()-START,full_cpu_seconds=cpu()-CPU0,publication_allowance_seconds=2)
            if remaining()<=0 and record['status']!='cancelled':record.update(passed=False,status='budget_exceeded')
            if record['status']!='completed':record['passed']=False
        f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)
        stored=f.read_json(output/'result.json')
        if f.canonical(stored)!=f.canonical(record):raise p.Rejected('stored diagnostic snapshot differs')
        return stored


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-head',required=True);parser.add_argument('--controller-sha256',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def cancel(*_):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,cancel)
    row=main(args.source_head,args.controller_sha256,args.output)
    print(f.canonical({k:row.get(k) for k in ('passed','status','observation_complete','wall_seconds','full_cpu_seconds')}))
    raise SystemExit(0 if row.get('passed') is True and row.get('status')=='completed' else 2)
