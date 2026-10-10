#!/usr/bin/env python3
"""Small predeclared development ablation, not confirmatory population testing."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from autorouter.config import ROOT
from autorouter.pipeline import route,save_json,tree_hash,tool_manifest

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
    board=ROOT/'.data/boards/kicad-sonde-xilinx/sonde xilinx.kicad_pcb'
    arms=[('stock-a','none'),('graphics','graphics'),('planes','planes'),('combined','both'),('stock-b','none')]
    protocol={'schema':1,'split':'development-exposed','family':'kicad-sonde-xilinx','arms':arms,'task':'remove only unlocked routes; preserve native zones and constraints','wall_budget_per_arm_seconds':120,'concurrency':1,'tools':tool_manifest(),'source_hashes':tree_hash(board.parent),'primary':'zero native opens/blocking errors, invariant/rule preservation','secondary':['length','vias','wall','parent+child+monitor CPU'],'predictions':'graphics fixes copper-graphic collisions; plane suppression fixes unconnected terminals with likely wirelength cost; combined should remove both failure types','claims_limit':'One development family; B0 vs B1 only. No C or superiority beyond adapter; no speedup claim.'}
    save_json(out/'protocol.json',protocol)
    results=[]
    for name,adapter in arms:
        if tree_hash(board.parent)!=protocol['source_hashes']:raise RuntimeError('source changed between arms')
        j=route(board,out/name,120,False,adapter)
        row={'arm':name,'adapter':adapter,'status':j['status'],'accepted':j['accepted'],'reason':j.get('reason'),'opens':j.get('native',{}).get('opens'),'blocking':j.get('native',{}).get('blocking'),'warnings':j.get('native',{}).get('warnings'),'length_mm':j.get('metrics',{}).get('track_length_mm'),'vias':j.get('metrics',{}).get('vias'),'wall_seconds':j['wall_seconds'],'total_cpu_seconds':j['total_cpu_seconds'],'result':str(out/name/'result.json')}
        results.append(row);print(json.dumps(row),flush=True)
    save_json(out/'summary.json',{'protocol':'protocol.json','results':results})
if __name__=='__main__':main()
