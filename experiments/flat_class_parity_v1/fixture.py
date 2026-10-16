"""One owned matching directive, derived from the retained routed counterexample.

SPDX-License-Identifier: GPL-3.0-or-later
No routing or source repair occurs. This is an exposed diagnostic control.
"""
import json
from pathlib import Path
from autorouter import pipeline as p,sexpr as sx,placement_clearance as io
from experiments.schematic_class_intent_v1 import fixture as old
ROOT=Path(__file__).resolve().parents[2]
RECORD=ROOT/'evidence/schematic-class-false-accept-runtime006-001.json'

def retained():
    record=json.loads(io.read_bytes(RECORD))
    refs=[row for row in record['refs'] if row['path'].endswith('/route/result.json')]
    if len(refs)!=1:raise ValueError('one retained route reference required')
    receipt=Path(__file__).with_name('retained006')/'route-result.json'
    if p.sha(receipt)!=refs[0]['sha256']:raise ValueError('retained counterexample receipt changed')
    route=json.loads(io.read_bytes(receipt));candidate=receipt.parent/'candidate'/(old.STEM+'.kicad_pcb')
    manifest=json.loads(io.read_bytes(receipt.parent/'manifest.json'))
    for row in manifest['files']:
        path=receipt.parent/row['path']
        if path.stat().st_size!=row['bytes'] or p.sha(path)!=row['sha256']:raise ValueError('retained public packet changed')
    if p.sha(candidate)!=route['candidate_sha256']:raise ValueError('retained routed PCB changed')
    expected=old.files();packet={}
    for name,raw in expected.items():
        actual=io.read_bytes(candidate.parent/name)
        if name.endswith('.kicad_pcb'):
            if p.immutable(sx.parse(actual.decode()))!=p.immutable(sx.parse(raw.decode())):raise ValueError('retained owned layout differs')
        elif actual!=raw:raise ValueError('retained original companion differs: '+name)
        packet[name]=actual
    if set(p.tree_hash(candidate.parent))!=set(expected):raise ValueError('exact four-file retained packet required')
    return receipt,route,packet

def files():
    _,_,packet=retained();name=old.STEM+'.kicad_sch';tree=sx.parse(packet[name].decode())
    flags=sx.children(tree,'netclass_flag')
    if len(flags)!=1:raise ValueError('one flat owned directive required')
    props=[row for row in sx.children(flags[0],'property') if sx.unquote(row[1])=='Netclass']
    if len(props)!=1 or sx.unquote(props[0][2])!='CRITICAL':raise ValueError('exact retained CRITICAL directive required')
    props[0][2]='"POWER"';packet[name]=(sx.dump(tree)+'\n').encode()
    return packet
