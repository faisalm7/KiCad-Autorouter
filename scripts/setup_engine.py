#!/usr/bin/env python3
"""Download one pinned official binary; no installer, extraction or hooks."""
import hashlib
import os
from pathlib import Path
import sys
import urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter.config import JAR,JAR_SHA256
URL='https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar'
SIZE=64599107

def main():
    if JAR.parent.is_symlink() or JAR.is_symlink():
        raise SystemExit('Engine path must not be a symlink')
    JAR.parent.mkdir(exist_ok=True)
    if JAR.exists():
        if hashlib.sha256(JAR.read_bytes()).hexdigest()!=JAR_SHA256:
            raise SystemExit('Existing engine hash mismatch; refusing overwrite')
        print('Pinned engine already verified')
        return
    tmp=JAR.with_suffix('.download')
    with urllib.request.urlopen(URL,timeout=45) as r, tmp.open('xb') as f:
        total=0
        while True:
            chunk=r.read(1024*1024)
            if not chunk: break
            total+=len(chunk)
            if total>SIZE: raise SystemExit('Download exceeds pinned size')
            f.write(chunk)
    if total!=SIZE or hashlib.sha256(tmp.read_bytes()).hexdigest()!=JAR_SHA256:
        raise SystemExit('Download failed size/hash verification; not installed')
    if JAR.parent.is_symlink(): raise SystemExit('Engine destination changed')
    os.link(tmp,JAR)  # Exclusive publication: preserve a concurrently created destination.
    tmp.unlink()
    print('Verified official Freerouting 2.5.0 JAR:',JAR_SHA256)
if __name__=='__main__': main()
