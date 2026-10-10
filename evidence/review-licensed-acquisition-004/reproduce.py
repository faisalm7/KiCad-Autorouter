"""Tiny real-file lifecycle falsifiers. Git/HTTP mocked; no network or acquisition."""
import argparse,hashlib,importlib.util,json,shutil,time
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=ROOT/'.runs/licensed-acquisition-004/fetch.py');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    out=args.output.absolute()
    if out.parent!=HERE or out.exists():raise ValueError('fresh reviewer-owned output required')
    out.mkdir();source=out/'source.py';shutil.copyfile(args.source,source)
    spec=importlib.util.spec_from_file_location('review_acquisition',source);f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
    plan,unused,unused_rows=f.load(args.source.parent);results=[]
    for variant in ('unchanged','late_helper','late_head','late_response'):
        base=out/variant;base.mkdir();(base/'.data/original').mkdir(parents=True);(base/'.data/original/board.kicad_pcb').write_bytes(b'original')
        (base/'.runs').mkdir();(base/'.git').mkdir();head=base/'.git/HEAD';head.write_text('1'*40)
        helper=base/'experiments/licensed_acquisition_v1';helper.mkdir(parents=True)
        blobs={name:('frozen:'+name).encode() for name in f.MATERIAL}
        for name,raw in blobs.items():(helper/name).write_bytes(raw)
        batch=base/'.runs/output';baseline=f.inventory(base/'.data');mutated=[]
        def positive():
            path=batch/'receipt.json'
            return path.exists() and json.loads(path.read_text()).get('status')=='acquired_unqualified'
        def git(root,args):
            if args==['rev-parse','HEAD']:return head.read_bytes()
            if args[0]!='show':raise AssertionError('unexpected fake git grammar '+repr(args))
            name=args[1].rsplit('/',1)[-1]
            if name==f.MATERIAL[-1] and positive() and not mutated:
                if variant=='late_helper':(helper/'fetch.py').write_bytes(b'changed helper');mutated.append(variant)
                if variant=='late_head':head.write_text('2'*40);mutated.append(variant)
            return blobs[name]
        def transport(row,rec,path,allowance,remaining):
            rec.update(status='response_received',received_bytes=4,response_sha256=f.sha(b'data'),url='mock:no-network');path.write_bytes(b'data');return b'data'
        real_inventory=f.inventory
        def inventory(path,*args,**kwargs):
            if variant=='late_response' and path==batch and positive() and not mutated:
                (batch/'response-000.bin').write_bytes(b'evil');mutated.append(variant)
            return real_inventory(path,*args,**kwargs)
        row={'destination':'one/project.kicad_pcb','bytes':4,'git_blob_sha1':hashlib.sha1(b'blob 4\0data').hexdigest(),'sha256':None}
        with mock.patch.object(f,'git',side_effect=git),mock.patch.object(f,'inventory',side_effect=inventory):
            runtime=f.committed(base,helper);error=None
            try:returned=f.acquire(base,helper,batch,plan,baseline,[row],runtime,time.monotonic(),transport)
            except BaseException as exc:error=type(exc).__name__+': '+str(exc);returned=None
        canonical=f.decode((batch/'receipt.json').read_bytes()) if (batch/'receipt.json').exists() else None
        results.append({'variant':variant,'injected':bool(mutated),'returned_status':returned.get('status') if returned else None,'canonical_status':canonical.get('status') if canonical else None,'error':error,
            'helper_bound':sha(helper/'fetch.py')==runtime['files']['fetch.py'],'head_bound':head.read_text()==runtime['head'],
            'response_bound':sha(batch/'response-000.bin')==f.sha(b'data'),'original_unchanged':(base/'.data/original/board.kicad_pcb').read_bytes()==b'original'})
    report={'scope':'Tiny actual filesystem, real acquire/committed/publish logic, fake Git/transport only; no network/native/engine/project-data mutation','source_sha256':sha(source),'results':results}
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
