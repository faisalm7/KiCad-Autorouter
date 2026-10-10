"""Generate inspectable fixed owned boards only; no native/framework import."""
import argparse,hashlib,json,shutil
from pathlib import Path
import driver as d
import fixture

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);out=ap.parse_args().output.absolute()
    if out.parent!=d.HERE or out.exists() or out.is_symlink():raise ValueError('fresh direct child of owned draft required')
    hashes,total=d.source_binding();core=d.inventory(d.ROOT/'autorouter');actual=d.inventory(d.ROOT/'.runs/pic-custom-observation-002')
    source=d.sx.read(d.SOURCE);project=d.read(d.SOURCE.with_suffix('.kicad_pro'));out.mkdir();rows=[]
    shutil.copytree(d.SOURCE.parent/'_licenses',out/'_licenses')
    for variant,case in fixture.ORDER:
        raw,scene=fixture.prepare(source,case,variant);directory=out/(variant+'-'+case);directory.mkdir()
        board=directory/d.SOURCE.name;board.write_bytes(raw);d.p.save_json(directory/'recipe.json',scene)
        rows.append({'variant':variant,'case':case,'board_sha256':d.sha_bytes(raw),'bytes':len(raw),'project_sha256':d.PROJECT_SHA,
            'source14otherfiles_preserved_by_runtime':True,'two_route_count':len(d.p.routes(d.sx.parse(raw.decode()))),'four_footprints':len(d.sx.children(d.sx.parse(raw.decode()),'footprint'))})
    if hashes!=d.inventory(d.SOURCE.parent) or core!=d.inventory(d.ROOT/'autorouter') or actual!=d.inventory(d.ROOT/'.runs/pic-custom-observation-002'):raise ValueError('original/native evidence/core changed')
    report={'status':'generated_only','native_executed':False,**d.FALSE_CLAIMS,'source_hashes':hashes,'source_bytes':total,'cases':rows,
        'baseline_native_report_sha256':d.digest(d.ROOT/d.BASELINE_REPORT_REL),'source_explicit_ignored_checks':sorted(k for k,v in project['board']['design_settings']['rule_severities'].items() if v=='ignore'),
        'expected_native_effective_ignored_checks':list(d.OBSERVED_IGNORED),'source_core_native002_unchanged':True,
        'prepared_board_total_bytes':sum(r['bytes'] for r in rows),'protocol':d.protocol()}
    d.p.save_json(out/'preparation.json',report);print(json.dumps({k:report[k] for k in ('status','native_executed','source_core_native002_unchanged','prepared_board_total_bytes')}))
if __name__=='__main__':main()
