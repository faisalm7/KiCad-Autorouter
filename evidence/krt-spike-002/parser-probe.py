import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from kicad_parser import parse_kicad_pcb
result = {}
for name, path in zip(('single_line', 'pretty'), sys.argv[2:4]):
    pcb = parse_kicad_pcb(path)
    result[name] = {'zones': len(pcb.zones), 'footprints': len(pcb.footprints), 'pads': sum(len(p) for p in pcb.pads_by_net.values()), 'nets': len(pcb.nets)}
Path(sys.argv[4]).write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
