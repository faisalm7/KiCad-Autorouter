import base64,datetime,hashlib,json,subprocess,sys
from pathlib import Path
def run(args):return subprocess.check_output(args)
head=run(['git','rev-parse','HEAD']).decode().strip();branch=run(['git','branch','--show-current']).decode().strip()
remote=run(['git','ls-remote','origin','refs/heads/'+branch]).decode().split()[0];assert head==remote
name=sys.argv[1];audit=sys.argv[2]
d=json.loads(run(['/opt/homebrew/bin/gh','api','repos/faisalm7/KiCad-Autorouter/contents/'+name+'?ref='+head]))
assert type(d.get('size')) is int and 0<=d['size']<=4*1024**2 and d.get('type')=='file'
if d.get('encoding')=='base64':
    raw=base64.b64decode(d['content'])
else:
    assert d.get('encoding')=='none' and d.get('content')==''
    blob=json.loads(run(['/opt/homebrew/bin/gh','api','repos/faisalm7/KiCad-Autorouter/git/blobs/'+d['sha']]))
    assert blob.get('sha')==d['sha'] and blob.get('encoding')=='base64' and blob.get('size')==d['size']
    raw=base64.b64decode(blob['content'])
assert len(raw)==d['size'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==d['sha']
assert raw==run(['git','show',head+':'+name])
record={'verified':True,'git_head':head,'remote_sha':remote,'branch':branch,'file':name,'file_sha256':hashlib.sha256(raw).hexdigest(),'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'audit':audit}
Path('.runs/checkpoint-'+head[:7]+'.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
