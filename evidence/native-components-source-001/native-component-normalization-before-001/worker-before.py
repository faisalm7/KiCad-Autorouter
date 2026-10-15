"""UNEXECUTED DRAFT: pinned KiCad10 pad-component observer; not routing validation."""
import argparse, hashlib, json, platform, signal, sys, time
from pathlib import Path
START, CPU0 = time.monotonic(), time.process_time()
ROOT = next(p for p in Path(__file__).resolve().parents if (p/'autorouter/pipeline.py').is_file())
sys.path.insert(0,str(ROOT)); sys.dont_write_bytecode = True
from autorouter import config as c, pipeline as p, floor_route as f, handoff as h, placement_clearance as pc, board_floor as g, sexpr as sx
from experiments.native_components_v1.normalize import normalize, need, MAX_PADS, MAX_NETS, MAX_ITEMS, MAX_TOTAL_RETURNED, MAX_OUTPUT
SECONDS = 60

def digest(raw): return hashlib.sha256(raw).hexdigest()
def owned_path(value, existing=True):
    path = Path(value)
    need(path.is_absolute() and str(path) == value and '..' not in path.parts and ROOT/'.runs' in path.parents, 'canonical owned .runs path required')
    need(not any(x.is_symlink() for x in (path,*path.parents)), 'symlink path refused')
    need(path.exists() if existing else not path.exists(), 'input missing or destination exists')
    return path

def main(request_name, output_name):
    request = owned_path(request_name); request_raw = pc.read_bytes(request,256*1024); spec = json.loads(request_raw)
    keys = {'schema','board','project_sha256','refill_receipt','refill_receipt_sha256','worker_sha256','normalizer_sha256','lock_sha256'}
    need(type(spec) is dict and set(spec) == keys and spec['schema'] == 1, 'exact frozen request schema required')
    board_path = owned_path(spec['board']); output = owned_path(output_name,False)
    refill = owned_path(spec['refill_receipt'])
    need(board_path.suffix == '.kicad_pcb' and board_path.with_suffix('.kicad_pro').is_file(), 'PCB plus original PRO required')
    need(board_path.parent not in output.parents and output not in board_path.parents, 'observation output must be separate from input project')
    need(request.parent not in (board_path.parent,output), 'request must be outside input/output directory')
    source_files = pc.inventory(board_path.parent,max_bytes=8*1024**2,max_files=64,max_entries=128)
    need(source_files == spec['project_sha256'], 'complete input project pins differ')
    raw = pc.read_bytes(board_path,8*1024**2); tree = sx.parse(raw.decode())
    need(tree[0] == 'kicad_pcb', 'native PCB AST required')
    layers = [sx.unquote(n[1]) for n in sx.one(tree,'layers')[1:] if isinstance(n,list) and len(n)>2 and sx.unquote(n[1]).endswith('.Cu')]
    need(layers == ['F.Cu','B.Cu'], 'initial observer only qualifies two outer copper layers')
    names, resolve = g.source_net_identity(tree)
    need(1 <= len(names) <= MAX_NETS, 'complete source net population exceeded')
    expected = {}; ast_items = 0; footprint_ids = set(); references = set()
    def scan(node):
        nonlocal ast_items
        if type(node) is list:
            ast_items += 1; need(ast_items <= 50000, 'source AST population exceeded')
            for child in node: scan(child)
    scan(tree)
    for fp in sx.children(tree,'footprint'):
        need(not sx.children(fp,'zone') and not sx.children(fp,'net_tie_pad_groups'), 'footprint zones/net ties unqualified')
        refrows = [r for r in sx.children(fp,'property') if len(r)>=3 and sx.unquote(r[1])=='Reference']
        need(len(refrows)==1, 'exact footprint reference required')
        ref, fp_uuid = sx.unquote(refrows[0][2]), sx.unquote(sx.one(fp,'uuid')[1]).lower()
        need(fp_uuid not in footprint_ids and ref not in references, 'duplicate footprint UUID/reference')
        footprint_ids.add(fp_uuid); references.add(ref)
        for pad in sx.children(fp,'pad'):
            need(len(pad)>3 and pad[2] in ('thru_hole','smd','np_thru_hole') and pad[3] in ('circle','rect','oval','roundrect'), 'ordinary pad scope exceeded')
            uid = sx.unquote(sx.one(pad,'uuid')[1]).lower()
            need(uid not in expected and len(expected)<MAX_PADS, 'duplicate or excess source pad')
            expected[uid] = (fp_uuid,ref,sx.unquote(pad[1]),resolve(sx.one(pad,'net')))
    need(expected and not set(expected).intersection(footprint_ids), 'missing source pads or aliased pad/footprint UUID')
    need(platform.system() == 'Darwin' and Path(sys.executable).resolve() == c.PYTHON.resolve(), 'pinned native Mac interpreter required')
    lock_path = ROOT/'toolchain.lock.json'; lock_raw = pc.read_bytes(lock_path,64*1024); lock = json.loads(lock_raw)
    need(digest(lock_raw)==spec['lock_sha256'] and lock['kicad']=='10.0.0', 'frozen native lock differs')
    # Installed Python framework's trusted symlink layout is resolved by config; job paths never allow symlinks.
    tool_files = {}
    for key, path in [('kicad_python',c.PYTHON),('pcbnew',c.PCBNEW)]:
        need(str(path)==lock['tools'][key]['path'], 'pinned native tool path differs')
        tool_files[str(path)] = digest(path.read_bytes())
        need(tool_files[str(path)]==lock['tools'][key]['sha256'], 'pinned native tool bytes differ')
    own = {Path(__file__):spec['worker_sha256'],Path(__file__).with_name('normalize.py'):spec['normalizer_sha256']}
    need(all(digest(pc.read_bytes(path,256*1024))==pin for path,pin in own.items()), 'observer implementation differs')
    refill_raw = pc.read_bytes(refill,8*1024**2)
    need(digest(refill_raw)==spec['refill_receipt_sha256'], 'caller refill receipt pin differs')
    import pcbnew, _pcbnew
    need(pcbnew.GetBuildVersion()=='10.0.0' and Path(_pcbnew.__file__).resolve()==c.PCBNEW.resolve(), 'loaded native module/version differs')
    native = pcbnew.LoadBoard(str(board_path)); need(native is not None, 'native load failed')
    attributes = {pcbnew.PAD_ATTRIB_PTH:'pth',pcbnew.PAD_ATTRIB_SMD:'smd',pcbnew.PAD_ATTRIB_NPTH:'npth'}
    pads = {}; rows = []
    for pad in native.GetPads():
        uid = str(pad.m_Uuid.AsString()).lower(); fp=pad.GetParentFootprint()
        need(uid in expected and uid not in pads and len(pads)<MAX_PADS and fp is not None, 'native pad missing/added/duplicate')
        fp_uuid,ref,number,net = str(fp.m_Uuid.AsString()).lower(),str(fp.GetReference()),str(pad.GetNumber()),str(pad.GetNetname())
        need((fp_uuid,ref,number,net)==expected[uid], 'native/source pad identity differs')
        attr=attributes.get(pad.GetAttribute()); need(attr is not None, 'unqualified native pad attribute')
        copper=[label for layer,label in [(pcbnew.F_Cu,'F.Cu'),(pcbnew.B_Cu,'B.Cu')] if pad.IsOnLayer(layer)]
        code=int(pad.GetNetCode()); eligible=attr in ('pth','smd') and bool(copper) and code>0
        need(attr!='npth' or code==0, 'netted NPTH pad unqualified')
        rows.append(dict(uuid=uid,footprint_uuid=fp_uuid,reference=ref,number=number,net=net,netcode=code,layers=copper,attribute=attr,eligible=eligible,
            excluded_reason='' if eligible else 'NPTH/no positive native net/no outer copper; excluded from electrical component queries'))
        pads[uid]=pad
    need(set(pads)==set(expected), 'native complete pad census differs')
    output.mkdir(); owner={}; h.capture_destination(owner,output)
    record=dict(schema=1,kind='experimental-native-pad-component-observation-draft-v1',status='incomplete',accepted=False,routing_accepted=False,production_admitted=False,
        board_saved=False,native_refill_performed=False,whole_project_drc_clean=False,source=str(board_path),source_hashes=source_files,request_sha256=digest(request_raw),
        refill_receipt_sha256=digest(refill_raw),refill_semantics_checked_by_worker=False,tools=tool_files,native_version='10.0.0',flags=0,returned_items=0)
    def remaining(): return min(SECONDS-(time.monotonic()-START),SECONDS-(time.process_time()-CPU0))
    def stable():
        h.owned_destination(owner); need(remaining()>0, 'observer wall/CPU budget exhausted')
        need(pc.inventory(board_path.parent,max_bytes=8*1024**2,max_files=64,max_entries=128)==source_files, 'source project mutated')
        need(pc.read_bytes(request,256*1024)==request_raw and pc.read_bytes(refill,8*1024**2)==refill_raw and pc.read_bytes(lock_path,64*1024)==lock_raw, 'request/refill/lock mutated')
        need(all(digest(pc.read_bytes(path,256*1024))==pin for path,pin in own.items()), 'observer code mutated')
    def account():
        record.update(wall_seconds=time.monotonic()-START,worker_cpu_seconds=time.process_time()-CPU0,within_budget=remaining()>0)
        if not record['within_budget']: record['status']='budget_exceeded'
    try:
        stable(); need(native.BuildConnectivity() is True, 'explicit native connectivity rebuild failed')
        connectivity=native.GetConnectivity(); need(connectivity is not None, 'native connectivity unavailable')
        reachable={}; allowed={pcbnew.PCB_PAD_T,pcbnew.PCB_TRACE_T,pcbnew.PCB_VIA_T,pcbnew.PCB_ARC_T,pcbnew.PCB_ZONE_T}
        for row in rows:
            if not row['eligible']: continue
            stable(); members=[]; count=0
            for item in connectivity.GetConnectedItems(pads[row['uuid']],0):
                count+=1; record['returned_items']+=1
                need(count<=MAX_ITEMS and record['returned_items']<=MAX_TOTAL_RETURNED, 'native returned-item ceiling exceeded')
                need(item is not None and item.Type() in allowed and int(item.GetNetCode())==row['netcode'], 'unknown or mixed-net connected item')
                if item.Type()==pcbnew.PCB_PAD_T:
                    uid=str(item.m_Uuid.AsString()).lower()
                    need(uid in pads and uid not in members and str(item.GetNetname())==row['net'], 'unknown/duplicate/mixed-net returned pad')
                    members.append(uid)
            reachable[row['uuid']]=members
        for row in rows:
            pad=pads[row['uuid']]
            need(str(pad.GetNetname())==row['net'] and int(pad.GetNetCode())==row['netcode'], 'native rebuild/query changed pad net identity')
        normalized=normalize(rows,reachable)
        need(len(json.dumps(dict(record,**normalized)).encode())<=MAX_OUTPUT-16384, 'observer output ceiling exceeded')
        record.update(normalized); record['status']='diagnostic_completed'; stable(); account()
    except (Exception,KeyboardInterrupt) as exc:
        record.update(status='failed',reason=(type(exc).__name__+': '+str(exc))[:2000]); account()
    return f.publish(output,record,stable,account,remaining,owned=lambda:h.owned_destination(owner),final_check=stable)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--request',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    def stop(*_): raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM): signal.signal(sig,stop)
    r=main(args.request,args.output); print(json.dumps({k:r[k] for k in ('status','accepted','routing_accepted','production_admitted')})); raise SystemExit(0 if r['status']=='diagnostic_completed' else 2)
