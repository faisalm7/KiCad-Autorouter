"""Experimental .runs-only compatibility wrapper for shared byte protection."""
from pathlib import Path
from autorouter import pipeline as p
from autorouter.local_settings import preserve as _preserve

def preserve(path,owned_root,owner,*,cleanup_complete=lambda:True):
    owned_root=Path(owned_root)
    if owned_root==p.c.ROOT/'.runs' or p.c.ROOT/'.runs' not in owned_root.parents:
        raise p.Rejected('PRL guard requires canonical owned diagnostic copy')
    return _preserve(path,owned_root,owner,cleanup_complete=cleanup_complete)
