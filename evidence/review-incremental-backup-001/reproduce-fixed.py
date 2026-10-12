"""Small actual files/owned Python child; no production backup or native process."""
from pathlib import Path
import hashlib,io,json,os,subprocess,sys,tarfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from scripts import backup
OUT=Path(__file__).resolve().parent/'fixed-001';OUT.mkdir()

def fixture(name):
    root=OUT/name;root.mkdir()
    (root/'.data').mkdir();(root/'.data'/'payload').write_bytes(b'original')
    return root

def tar_swap_probe(swap):
    root=fixture('tar-swap' if swap else 'tar-positive');archive=root/'data.tgz';manifest=backup.inventory(root)
    backup.make_archive(root,archive,manifest);original_audit=backup.audit_archive
    def audit(*args,**kwargs):
        answer=original_audit(*args,**kwargs)
        if swap:
            with tarfile.open(archive,'w:gz') as writer:
                item=tarfile.TarInfo('../unexpected-outside-restore');payload=b'review-controlled escape';item.size=len(payload);writer.addfile(item,io.BytesIO(payload))
        return answer
    error=None
    try:
        with patch.object(backup,'audit_archive',side_effect=audit):backup.restore_archive(archive,root/'restore',manifest)
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    return {'mutation':swap,'error':error,'expected_file_preserved':(root/'.data/payload').read_bytes()==b'original','outside_restore_file_created':(root/'unexpected-outside-restore').exists(),'restored_payload':(root/'restore/.data/payload').read_text() if (root/'restore/.data/payload').exists() else None}

def publication_probe(signal_name):
    root=OUT/('publication-'+signal_name);root.mkdir();proof=root/'proof.json'
    script='''from pathlib import Path\nimport os,signal,sys\nsys.path.insert(0,sys.argv[1])\nfrom scripts import backup\nproof=Path(sys.argv[2]);original=backup.exclusive_json\ndef write(path,value):\n original(path,value)\n if sys.argv[3]!='none':os.kill(os.getpid(),getattr(signal,sys.argv[3]))\nbackup.exclusive_json=write\nbackup.publish_check(proof,{'verified':True},lambda:None)\n'''
    completed=subprocess.run([sys.executable,'-B','-c',script,str(ROOT),str(proof),signal_name],capture_output=True,text=True,timeout=10)
    (root/'stdout.log').write_text(completed.stdout);(root/'stderr.log').write_text(completed.stderr)
    return {'signal':signal_name,'exit_code':completed.returncode,'canonical_exists':proof.exists(),'canonical':json.loads(proof.read_text()) if proof.exists() else None,'invalidated_count':len(list(root.glob('invalidated-*')))}

results={'script_sha256':hashlib.sha256((ROOT/'scripts/backup.py').read_bytes()).hexdigest(),'tar':[tar_swap_probe(False),tar_swap_probe(True)],'publication':[publication_probe('none'),publication_probe('SIGINT'),publication_probe('SIGTERM')],'production_artifacts_touched':False}
(OUT/'reproduction-001.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n');print(json.dumps(results,indent=2))
