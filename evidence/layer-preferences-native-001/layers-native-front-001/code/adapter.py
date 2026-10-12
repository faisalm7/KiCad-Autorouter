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
    return {"classification": "B1_adapter_only", "mode": mode,
            "input_sha256": _digest(raw), "output_sha256": _digest(encoded),
            "input_bytes": len(raw), "output_bytes": len(encoded),
            "planes_removed": len(removed_planes), "graphics_keepouts_added": len(inserted),
            "net_pin_mapping": before_network, "net_pin_mapping_unchanged": True,
            "native_project_modified": False, "transformations": transformations,
            "limitations": ["Graphics use conservative bounding rectangles, not exact copper contours.",
                            "Plane suppression is an all-terminal over-routing surrogate; native zones must remain unchanged."]}
