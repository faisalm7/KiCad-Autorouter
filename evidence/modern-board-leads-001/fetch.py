"""Bounded primary REST/raw reads; never execute or promote source payloads."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote
from datetime import datetime, timezone
import hashlib, json, sys, time

OUT = Path(__file__).resolve().parent
LIMIT = 5 * 1024 * 1024
DEADLINE = datetime(2026, 10, 13, 14, 39, 1, tzinfo=timezone.utc).timestamp()
ledger_path = OUT / 'fetch-receipt.json'
ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
    'schema': 1, 'start_utc': '2026-10-13T14:29:01+00:00', 'max_raw_response_bytes': LIMIT,
    'deadline_utc': '2026-10-13T14:39:01+00:00', 'requests': [], 'new_raw_response_bytes': 0,
    'native_jobs': 0, 'engine_jobs': 0, 'git_subprocesses': 0, 'spending': 0,
    'scope': 'Primary creator GitHub REST metadata and pinned source/notice data only; no hooks, scripts or acquisition promotion'}


def fetch(url, label):
    if time.time() >= DEADLINE:
        raise RuntimeError('research wall budget exhausted')
    remaining = LIMIT - ledger['new_raw_response_bytes']
    if remaining <= 0:
        raise RuntimeError('raw response budget exhausted')
    row = {'url': url, 'label': label, 'started_utc': datetime.now(timezone.utc).isoformat()}
    target = OUT / ('response-%03d.bin' % len(ledger['requests']))
    try:
        req = Request(url, headers={'User-Agent': 'KiCad-Autorouter-local-source-research', 'Accept': 'application/vnd.github+json'})
        with urlopen(req, timeout=min(15, max(0.1, DEADLINE-time.time()))) as response:
            length = response.headers.get('Content-Length')
            if length and int(length) > remaining:
                raise RuntimeError('declared response exceeds remaining byte budget')
            content = response.read(remaining)
            row.update(status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'))
            if len(content) >= remaining and (not length or int(length) >= remaining):
                row['response_may_be_truncated'] = True
        target.write_bytes(content)
        row.update(file=target.name, bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        ledger['new_raw_response_bytes'] += len(content)
        return content
    except Exception as exc:
        row.update(error=type(exc).__name__ + ': ' + str(exc))
        raise
    finally:
        row['finished_utc'] = datetime.now(timezone.utc).isoformat()
        ledger['requests'].append(row)
        ledger_path.write_text(json.dumps(ledger, indent=2) + '\n')


def main():
    mode, repo = sys.argv[1:3]
    base = 'https://api.github.com/repos/' + repo
    if mode == 'repo':
        data = json.loads(fetch(base, repo + ' repository'))
        branch = data['default_branch']
        commit = json.loads(fetch(base + '/commits/' + quote(branch, safe=''), repo + ' current head'))
        pin = commit['sha']
        tree = json.loads(fetch(base + '/git/trees/' + pin + '?recursive=1', repo + ' pinned recursive tree'))
        if tree.get('truncated'):
            raise RuntimeError('tree truncated; no complete scope proof')
        record = {'repository': repo, 'fork': data['fork'], 'parent': data.get('parent', {}).get('full_name'),
                  'creator': data['owner']['login'], 'description': data.get('description'), 'homepage': data.get('homepage'),
                  'created_at': data['created_at'], 'pushed_at': data['pushed_at'], 'commit': pin,
                  'author': commit['commit']['author'], 'committer': commit['commit']['committer'],
                  'message': commit['commit']['message'], 'tree': tree['tree']}
        (OUT / (repo.replace('/', '__') + '.json')).write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps({k: record[k] for k in ('repository','fork','commit','created_at','pushed_at','message')}))
        for row in tree['tree']:
            if row['path'].endswith(('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru','.kicad_sym','.kicad_mod','.gitmodules')) or 'license' in row['path'].lower() or row['path'].lower().endswith('readme.md') or row['path'].endswith(('fp-lib-table','sym-lib-table','CODEOWNERS')):
                print(row['path'], row.get('size'), row['sha'], row['mode'])
    elif mode == 'raw':
        record = json.loads((OUT / (repo.replace('/', '__') + '.json')).read_text())
        for path in sys.argv[3:]:
            item = next(row for row in record['tree'] if row['path'] == path)
            if item['type'] != 'blob' or item['mode'] != '100644':
                raise RuntimeError('regular nonexecutable source data only')
            content = fetch('https://raw.githubusercontent.com/' + repo + '/' + record['commit'] + '/' + quote(path, safe='/'), repo + ' ' + path)
            blob = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            if len(content) != item['size'] or blob != item['sha']:
                raise RuntimeError('source Git blob/size mismatch')
            print(path, len(content), hashlib.sha256(content).hexdigest())
    elif mode == 'history':
        record = json.loads((OUT / (repo.replace('/', '__') + '.json')).read_text())
        path = sys.argv[3]
        data = json.loads(fetch(base + '/commits?sha=' + record['commit'] + '&path=' + quote(path,safe='') + '&per_page=100', repo + ' pinned path history ' + path))
        print(json.dumps([{'sha': row['sha'], 'author': row['commit']['author'], 'message': row['commit']['message']} for row in data], indent=2))
    else:
        raise RuntimeError('unknown bounded read mode')


if __name__ == '__main__':
    main()
