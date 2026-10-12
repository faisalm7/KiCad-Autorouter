"""Two finite original-source diagnostics; these never grant production support."""
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass(frozen=True)
class SourceSpec:
    name: str
    source: Path
    receipt: Path
    receipt_sha256: str
    board_sha256: str
    project_sha256: str
    files: int
    bytes: int
    board_format: str
    pad_id: str
    reference_kind: str
    pads: int
    nets: int
    routes: int
    zones: int
    footprints: int
    gate_rejection: str
    acquisition_project: str | None = None
    acquisition_protocol: str | None = None

    def record(self):
        return {key:str(value) if isinstance(value,Path) else value for key,value in asdict(self).items()}

NAMES=('lipo','paw3395')

def select(name,root):
    if type(name) is not str or name not in NAMES:
        raise ValueError('unknown source profile')
    root=Path(root)
    if name=='lipo':
        return SourceSpec(name,root/'.data/expansion003/lipo-disconnector/lipo_disconnector.kicad_pcb',
            root/'.runs/licensed-acquisition-003/lipo-disconnector-001/receipt.json',
            'b57bc2ce29d7c5e45939fbf917896d02536b357e8b5a08c04828dd8305107c27',
            '3ef2141230ce971115381107486892bdf06a724c5d31d9ef2103622e113cf4e0',
            '8bc2dc577fb98404f317730b10ba2945f213a14e212b7a0b3e7fba7943a8d95e',
            26,4194990,'20220621','tstamp','fp_text',10,3,8,3,13,
            'unsupported: unqualified board format version',acquisition_project='lipo-disconnector')
    return SourceSpec(name,root/'.data/expansion005/paw3395/paw3395.kicad_pcb',
        root/'.runs/licensed-acquisition-005-run-001/receipt.json',
        '370f1c09157a7090fb725018bd7fa3ebb3d184d9163c1ee807110c674f2ac629',
        'c2e8cebd0da804eb3912c6559ad6b3e725c1b29f744d616e1ebb22f1229f7740',
        '4a0b352b482dd49a22aeea5599c44444e2d1dfad2ac77880c63152002445cdad',
        14,2163350,'20240108','uuid','property',56,16,220,1,18,
        'unsupported: unknown rule severity semantics: zone_has_empty_net; unqualified board format version',
        acquisition_protocol='94c5d74bfa34da80278db89bc2fc48ba165ed4bb293cb2f3d8382f3150241a66')
