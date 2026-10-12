"""Fixed disposable write-denial canary, executed only by ROOT under sandbox."""
from pathlib import Path
import errno,json,os,sys
NAMES=('overwrite','append','truncate','create','mkdir','unlink','rename','replace','chmod','rename_root')
SENTINEL=b'owned input must stay exact\n'

def attempts(root,outside):
    def write(path,flags):
        fd=os.open(str(path),flags,0o600)
        try:os.write(fd,b'forbidden')
        finally:os.close(fd)
    return (
        lambda:write(root/'overwrite',os.O_WRONLY),
        lambda:write(root/'append',os.O_WRONLY|os.O_APPEND),
        lambda:os.truncate(str(root/'truncate'),0),
        lambda:write(root/'created',os.O_WRONLY|os.O_CREAT|os.O_EXCL),
        lambda:(root/'newdir').mkdir(),
        lambda:(root/'unlink').unlink(),
        lambda:(root/'rename').rename(root/'renamed'),
        lambda:os.replace(str(outside),str(root/'replace')),
        lambda:os.chmod(str(root/'chmod'),0o600),
        lambda:root.rename(root.with_name(root.name+'-renamed')))

def probe(root,output):
    root=Path(root);output=Path(output);outside=output.with_suffix('.replace-source')
    # Successful outside writes distinguish the intended restriction from global
    # inability to write. Every protected target exists before launching.
    outside.write_bytes(b'owned outside replacement\n')
    rows=[]
    for name,operation in zip(NAMES,attempts(root,outside)):
        try:operation()
        except OSError as exc:rows.append({'name':name,'denied':exc.errno in (errno.EPERM,errno.EACCES),'errno':exc.errno})
        else:rows.append({'name':name,'denied':False,'errno':None})
    result={'schema':1,'protected_input':str(root),'attempts':rows,'outside_write_succeeded':True,
        'passed':all(x['denied'] for x in rows)}
    output.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('canary INPUT OUTPUT')
    raise SystemExit(0 if probe(sys.argv[1],sys.argv[2])['passed'] else 7)
