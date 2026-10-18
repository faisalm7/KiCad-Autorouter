"""Explicit B1 interchange corrections; these are not a new routing strategy.

Graphics use conservative native bounding rectangles. Plane suppression asks
the engine to wire all terminals; native zones are retained by the caller.
Only a disposable exported DSN may be passed to this module.
"""
from __future__ import annotations

import copy
from decimal import Decimal, InvalidOperation
import hashlib
import math
import os
from pathlib import Path
import re
import stat
import tempfile

from . import sexpr as sx


_QUOTE_SENTINEL = "__KICAD_AUTOROUTER_DSN_QUOTE_SENTINEL__"
_QUOTE_DECLARATION = re.compile(r'\(\s*string_quote\s+"\s*\)')
_KEEP_OUT_PREFIX = "kicad_autorouter_graphic_"
_MAX_OBSTACLES = 10000


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def fixed_placement_session(raw):
    """Keep native footprint poses; import only the unchanged SES routing.

    Freerouting's placement grid can be coarser than the native board. KiCad
    applies that optional section, so omit it for this fixed-placement tool.
    This does not qualify the routes: original-design/native checks still run.
    """
    if type(raw) is not bytes or not raw or len(raw)>sx.MAX_BYTES:
        raise ValueError('bounded SES bytes required')
    tree=sx.parse(raw.decode('utf-8'))
    if (len(tree)!=6 or tree[0]!='session' or type(tree[1]) is not str
            or not sx.unquote(tree[1])
            or any(type(n) is not list or not n or type(n[0]) is not str for n in tree[2:])
            or sorted(n[0] for n in tree[2:])!=['base_design','placement','routes','was_is']):
        raise ValueError('qualified fixed-placement SES root required')
    base=sx.one(tree,'base_design')
    if len(base)!=2 or type(base[1]) is not str or not sx.unquote(base[1]) or sx.one(tree,'was_is')!=['was_is']:
        raise ValueError('SES design renaming is not qualified')
    routes=sx.one(tree,'routes')
    for key in ('resolution','library_out','network_out'):
        if len(sx.children(routes,key))!=1:raise ValueError('unique SES routing '+key+' required')
    resolution=sx.one(routes,'resolution')
    if (len(resolution)!=3 or resolution[1]!='um' or type(resolution[2]) is not str
            or re.fullmatch(r'[1-9][0-9]{0,6}',resolution[2]) is None or int(resolution[2])>1000000):
        raise ValueError('qualified SES routing resolution required')
    filtered=[n for n in tree if not isinstance(n,list) or not n or n[0]!='placement']
    encoded=(sx.dump(filtered)+'\n').encode('utf-8')
    decoded=sx.parse(encoded.decode('utf-8'))
    if decoded!=filtered or sx.one(decoded,'routes')!=routes:
        raise ValueError('SES routing changed during placement removal')
    return encoded,dict(schema=1,policy='fixed-placement-session-v1',input_sha256=_digest(raw),
        output_sha256=_digest(encoded),removed_root_placement_count=1,routing_ast_unchanged=True,
        original_footprint_poses_preserved_by_omission=True,routing_accepted=False)


def native_command_parser(native_toolchain=None, *, data=None, with_task_copper=False):
    """Exact caller-pinned Native prefix; normalize a local copy, never argv.

    A visible Native script/experimental flag with a different prefix is an
    error, including on unrelated Native actions scanned during a census.
    """
    from . import pipeline as p
    from .floor_route import SANDBOX, canonical as encode
    from .task_copper import FLAG
    if type(with_task_copper) is not bool:raise p.Rejected('typed Native parser protection context required')
    prefix=p.native_prefix(native_toolchain)
    if data is not None:
        if type(data) is not dict:raise p.Rejected('Native reader receipt must be an object')
        if 'experimental_native_toolchain' in data:
            if (native_toolchain is None or
                    encode(data['experimental_native_toolchain'])!=encode(native_toolchain.record())):
                raise p.Rejected('Native reader toolchain context differs')
    def command(argv,action):
        if type(argv) is not list:return None
        args=argv[len(SANDBOX):] if argv[:len(SANDBOX)]==SANDBOX else argv
        visible=('--experimental-native' in args or any(
            type(value) is str and Path(value).name=='native.py' for value in args))
        if not visible:return None
        if native_toolchain is None and '--experimental-native' in args:
            raise p.Rejected('default Native reader refuses experimental prefix')
        if (any(type(value) is not str for value in args)
                or args[:len(prefix)]!=prefix):
            raise p.Rejected('unqualified caller-pinned Native command prefix')
        tail=args[len(prefix):]
        if not tail:raise p.Rejected('missing Native command action')
        if tail[0].startswith('-'):raise p.Rejected('unexpected Native command flag')
        fixed=FLAG in tail
        if fixed:
            if tail.count(FLAG)!=1 or tail[-1]!=FLAG or tail[0] not in {'export','import'} or native_toolchain is not None:
                raise p.Rejected('unqualified task copper Native flag')
            tail=tail[:-1]
        if any(value.startswith('--') for value in tail[1:]):raise p.Rejected('unexpected Native operation flag')
        if tail[0]!=action:return None
        arities={'export':(3,4),'import':(4,)}
        if action not in arities or len(tail) not in arities[action]:
            raise p.Rejected('unqualified caller-pinned Native command arity')
        normalized=[*prefix[:2],*tail]
        return (normalized,fixed) if with_task_copper else normalized
    # Validate visible Native prefixes even before genuine legacy-policy exits.
    if data is not None:
        for step in data.get('steps', []):
            if type(step) is dict:command(step.get('argv'), 'export')
    return command


def check_fixed_placement_import(root,data,retained,*,native_toolchain=None):
    """Reuse captured-policy and worker inventories to require every import proof."""
    from . import pipeline as p
    from .floor_route import read_json,canonical as encode,SANDBOX
    from .local_settings import canonical,policy_declaration
    from .placement_clearance import read_bytes
    parse_command=native_command_parser(native_toolchain,data=data)
    root=canonical(Path(root));pins=data.get('tools',{}).get('implementation_sha256',{})
    producer=root/'code/native.py';raw=read_bytes(producer,1024**2)
    if _digest(raw)!=pins.get('autorouter/native.py'):raise p.Rejected('captured Native import producer differs')
    policy=policy_declaration(raw,name='FIXED_PLACEMENT_SESSION_POLICY',expected='fixed-placement-session-v1')
    if policy is None:return  # Genuine older producers did not filter placement.
    if _digest(read_bytes(root/'code/adapter.py',1024**2))!=pins.get('autorouter/adapter.py'):
        raise p.Rejected('captured fixed-placement adapter differs')
    def command(argv):return parse_command(argv,'import')
    census={name[:-len('-process.json')] for name in retained if name.endswith('-process.json')
            and command(read_json(root/name).get('argv')) is not None}
    declared=set();proofs=set();transports=set();checked=[]
    for step in data.get('steps',[]):
        args=command(step.get('argv'))
        if args is None:continue
        cwd=canonical(Path(step['cwd']));name=step['name']
        if (cwd!=root and root not in cwd.parents) or type(name) is not str or re.fullmatch(r'[A-Za-z0-9_-]{1,128}',name) is None:
            raise p.Rejected('fixed-placement import worker escaped evidence')
        identity=str((cwd/name).relative_to(root))
        if identity in declared:raise p.Rejected('duplicate fixed-placement import worker')
        declared.add(identity);process=read_json(cwd/(name+'-process.json'))
        annotations=set(step)-set(process)
        if (any(encode(step.get(key))!=encode(value) for key,value in process.items())
                or (annotations and (annotations!={'phase'} or step['phase']!='incumbent'))
                or process.get('status')!='success'
                or type(process.get('exit_code')) is not int or process['exit_code']!=0
                or process.get('cleanup_complete') is not True):
            raise p.Rejected('fixed-placement import process differs')
        source,output,session=(canonical(Path(n)) for n in args[3:])
        if any(root not in n.parents for n in (source,output,session)) or output.parent!=cwd:
            raise p.Rejected('fixed-placement import files escaped evidence')
        read_bytes(source)
        imported_digest=_digest(read_bytes(output))
        filtered,expected=fixed_placement_session(read_bytes(session))
        derived=output.with_suffix('.routes-only.ses')
        proofs.update(str(n.relative_to(root)) for n in (derived,derived.with_suffix('.json')))
        expected.update(source_session=str(session),import_session=str(derived),imported_board_sha256=imported_digest)
        checked.append({'cwd':str(cwd),'name':name,'source':str(source),'output':str(output),'session':str(session)})
        if output.name=='imported.kicad_pcb' and session==cwd/'routes.ses':
            transports.add(str(output.relative_to(root)))
        if (read_bytes(derived)!=filtered
                or encode(read_json(derived.with_suffix('.json')))!=encode(expected)):
            raise p.Rejected('fixed-placement import proof differs')
    if census!=declared:raise p.Rejected('fixed-placement retained import population differs from steps')
    retained_proofs={name for name in retained if name.endswith(('.routes-only.ses','.routes-only.json'))}
    if retained_proofs!=proofs:raise p.Rejected('orphan or missing fixed-placement import proof')
    # Source boards may themselves be named imported.kicad_pcb. Standard
    # project-copy roles are inputs, whereas the worker's direct imported file
    # must keep its proof even after all other import lineage is removed.
    def project_copy(name):
        return any(part in {'snapshot','candidate','original','refill'} or part.endswith('-input')
                   for part in Path(name).parts[:-1])
    retained_transports={name for name in retained if Path(name).name=='imported.kicad_pcb' and not project_copy(name)}
    if retained_transports!=transports:raise p.Rejected('retained SES/imported board lost its import proof')
    p.experimental_native_version(native_toolchain)
    return checked


def _parse_dsn(text):
    """Normalize only KiCad's bare quote declaration, outside strings/comments."""
    if _QUOTE_SENTINEL in text:
        raise ValueError("DSN contains reserved quote sentinel")
    if len(text.encode("utf-8")) > sx.MAX_BYTES:
        raise ValueError("DSN exceeds size limit")
    pieces, cursor, count = [], 0, 0
    while cursor < len(text):
        char = text[cursor]
        if char == ";":
            end = text.find("\n", cursor)
            end = len(text) if end == -1 else end
            pieces.append(text[cursor:end])
            cursor = end
        elif char == '"':
            end = cursor + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                elif text[end] == '"':
                    end += 1
                    break
                else:
                    end += 1
            else:
                raise ValueError("Unterminated DSN string")
            pieces.append(text[cursor:end])
            cursor = end
        else:
            match = _QUOTE_DECLARATION.match(text, cursor) if char == "(" else None
            if match:
                pieces.append("(string_quote " + _QUOTE_SENTINEL + ")")
                cursor = match.end()
                count += 1
            else:
                pieces.append(char)
                cursor += 1
    if count != 1:
        raise ValueError("Expected exactly one KiCad string_quote declaration")
    tree = sx.parse("".join(pieces))
    if len(tree) < 3 or tree[0] != "pcb" or not isinstance(tree[1], str):
        raise ValueError("Expected pcb DSN root")
    parser = sx.one(tree, "parser")
    if parser is None or sx.one(parser, "string_quote") != ["string_quote", _QUOTE_SENTINEL]:
        raise ValueError("KiCad string_quote declaration must be in parser")
    return tree


def _dump_dsn(tree):
    text = sx.dump(tree)
    declaration = "(string_quote " + _QUOTE_SENTINEL + ")"
    if text.count(declaration) != 1 or text.count(_QUOTE_SENTINEL) != 1:
        raise ValueError("Invalid normalized DSN quote declaration")
    return text.replace(declaration, '(string_quote ")') + "\n"


def _number(value):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or (isinstance(value, float) and not math.isfinite(value))):
        raise ValueError("Obstacle coordinates must be finite JSON numbers")
    return Decimal(str(value))


def _atom_number(value):
    if value == 0:
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _check_units(tree):
    if sx.one(tree, "unit") != ["unit", "um"]:
        raise ValueError("Only explicitly declared DSN unit um is supported")
    resolution = sx.one(tree, "resolution")
    if resolution is None or len(resolution) != 3 or resolution[1] != "um":
        raise ValueError("Only DSN resolution um is supported")
    try:
        precision = Decimal(resolution[2])
    except (InvalidOperation, TypeError):
        raise ValueError("Invalid DSN resolution") from None
    if not precision.is_finite() or precision <= 0:
        raise ValueError("Invalid DSN resolution")
    # Fail closed if a nested unit override could change structure coordinates.
    def visit(node):
        if isinstance(node, list):
            if node and node[0] == "unit" and node != ["unit", "um"]:
                raise ValueError("Unknown or conflicting nested DSN units")
            if node and node[0] == "resolution" and node != resolution:
                raise ValueError("Conflicting nested DSN resolution")
            for child in node:
                visit(child)
    visit(tree)


def _network_summary(tree):
    network = sx.one(tree, "network")
    if network is None:
        raise ValueError("DSN network is required")
    nets = sx.children(network, "net")
    pins = []
    for net in nets:
        if len(net) < 2 or not isinstance(net[1], str):
            raise ValueError("Malformed DSN net")
        net_pins = sx.one(net, "pins")
        if net_pins is not None:
            if any(not isinstance(pin, str) for pin in net_pins[1:]):
                raise ValueError("Malformed DSN pin list")
            pins.extend((net[1], pin) for pin in net_pins[1:])
    return {"nets": len(nets), "pins": len(pins),
            "semantic_sha256": _digest(sx.dump(network).encode("utf-8"))}


def adapt_bytes(raw, mode, obstacles):
    """The existing exact adapter transform, without filesystem mutation."""
    if not isinstance(raw,bytes) or len(raw)>sx.MAX_BYTES:raise ValueError("bounded DSN bytes required")
    if mode not in ("graphics","planes","both"):raise ValueError("unknown adapter mode")
    original = _parse_dsn(raw.decode("utf-8"))
    _check_units(original)
    for required in ("placement", "library"):
        if sx.one(original, required) is None:
            raise ValueError("DSN " + required + " is required")
    before_network = _network_summary(original)
    tree = copy.deepcopy(original)
    structure = sx.one(tree, "structure")
    if structure is None:
        raise ValueError("DSN structure is required")
    layers = {}
    for layer in sx.children(structure, "layer"):
        if len(layer) < 2 or not isinstance(layer[1], str):
            raise ValueError("Malformed DSN layer")
        name = sx.unquote(layer[1])
        if name in layers:
            raise ValueError("Duplicate DSN layer")
        layers[name] = layer[1]
    if not layers:
        raise ValueError("DSN declares no layers")
    if not isinstance(obstacles, list) or len(obstacles) > _MAX_OBSTACLES:
        raise ValueError("Expected bounded native obstacle list")
    graphics = []
    # Validate supplied records even in planes-only mode; bad mapping is never
    # silently accepted as if obstacle support had been qualified.
    for index, obstacle in enumerate(obstacles):
        if not isinstance(obstacle, dict) or not isinstance(obstacle.get("layer"), str):
            raise ValueError("Malformed native obstacle")
        native_layer = obstacle["layer"]
        target = obstacle.get("dsn_layer", native_layer)
        if not isinstance(target, str):
            raise ValueError("Malformed DSN layer mapping")
        if target not in layers and "dsn_layer" not in obstacle:
            target = {"F.Cu": "top_copper", "B.Cu": "bottom_copper"}.get(target, target)
        if target not in layers:
            raise ValueError("Obstacle layer is not declared in DSN: " + target)
        bbox = obstacle.get("bbox_mm")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            raise ValueError("Obstacle bbox_mm must have four coordinates")
        xmin, ymin, xmax, ymax = [_number(value) for value in bbox]
        if xmin >= xmax or ymin >= ymax:
            raise ValueError("Obstacle bounding rectangle must have positive area")
        coords = [_atom_number(value * 1000) for value in (xmin, -ymax, xmax, -ymin)]
        graphics.append({"kind": "native_graphic_bbox_keepout", "obstacle_index": index,
                         "native_layer": native_layer, "dsn_layer": target,
                         "bbox_mm": list(bbox), "rect_um": coords})

    transformations = []
    removed_planes = []
    if mode in ("planes", "both"):
        for plane in sx.children(structure, "plane"):
            if (len(plane) < 3 or not isinstance(plane[1], str)
                    or not isinstance(plane[2], list) or not plane[2]):
                raise ValueError("Malformed structure plane declaration")
            removed_planes.append(plane)
            transformations.append({"kind": "suppress_dsn_plane", "net": sx.unquote(plane[1]),
                                    "semantic_sha256": _digest(sx.dump(plane).encode("utf-8"))})
        structure[:] = [node for node in structure if node not in removed_planes]
    inserted = []
    if mode in ("graphics", "both"):
        for keepout in sx.children(structure, "keepout"):
            if len(keepout) > 1 and isinstance(keepout[1], str) and sx.unquote(keepout[1]).startswith(_KEEP_OUT_PREFIX):
                raise ValueError("DSN already contains adapter graphics keepouts")
        for index, graphic in enumerate(graphics):
            name = _KEEP_OUT_PREFIX + _digest(raw)[:12] + "_" + str(index)
            rect = ["rect", layers[graphic["dsn_layer"]], *graphic["rect_um"]]
            node = ["keepout", name, rect]
            structure.append(node)
            inserted.append(node)
            transformations.append(dict(graphic, keepout=name))

    # Reconstruct the exact expected semantic edit. Everything else, including
    # all net/pin mapping, original keepouts, unknown fields and wiring, survives.
    expected = copy.deepcopy(original)
    expected_structure = sx.one(expected, "structure")
    if mode in ("planes", "both"):
        expected_structure[:] = [node for node in expected_structure
                                 if not (isinstance(node, list) and node and node[0] == "plane")]
    expected_structure.extend(copy.deepcopy(inserted))
    if tree != expected or _network_summary(tree) != before_network:
        raise ValueError("DSN adapter changed protected semantics")
    encoded = _dump_dsn(tree).encode("utf-8")
    if _parse_dsn(encoded.decode("utf-8")) != tree:
        raise ValueError("DSN semantic roundtrip failed")
    if len(encoded) > sx.MAX_BYTES:
        raise ValueError("Adapted DSN exceeds size limit")
    return encoded, {"classification": "B1_adapter_only", "mode": mode,
            "input_sha256": _digest(raw), "output_sha256": _digest(encoded),
            "input_bytes": len(raw), "output_bytes": len(encoded),
            "planes_removed": len(removed_planes), "graphics_keepouts_added": len(inserted),
            "net_pin_mapping": before_network, "net_pin_mapping_unchanged": True,
            "native_project_modified": False, "transformations": transformations,
            "limitations": ["Graphics use conservative bounding rectangles, not exact copper contours.",
                            "Plane suppression is an all-terminal over-routing surrogate; native zones must remain unchanged."]}


def adapt_dsn(path, mode, obstacles):
    """Atomically correct an exported DSN and return auditable transformations.

    ``obstacles`` is a list of native ``layer`` / ``bbox_mm`` records. An optional
    ``dsn_layer`` explicitly supplies the exporter's layer mapping. Without it,
    exact DSN layer names and KiCad F.Cu/B.Cu outer-layer aliases are accepted.
    Bounding boxes include the native object's stroke/font extents; this module
    adds no guessed clearance. The routing engine still applies DSN clearance.
    """
    if mode not in ("graphics", "planes", "both"):
        raise ValueError("Adapter mode must be graphics, planes, or both")
    path = Path(path)
    if path.is_symlink() or path.suffix.lower() != ".dsn" or not path.is_file():
        raise ValueError("Adapter requires a regular exported .dsn file")
    original_stat = path.stat()
    if original_stat.st_size > sx.MAX_BYTES:
        raise ValueError("DSN exceeds size limit")
    raw = path.read_bytes()
    encoded, record = adapt_bytes(raw, mode, obstacles)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".adapter-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.chmod(stat.S_IMODE(original_stat.st_mode))
        if path.is_symlink() or path.read_bytes() != raw:
            raise ValueError("DSN changed during adaptation")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return record
