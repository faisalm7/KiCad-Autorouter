#!/usr/bin/env python3
"""Bounded, isolated native netclass/DSN capability probe; never runs a solver.

This does not change pipeline eligibility or establish routing acceptance. Source
projects remain immutable. Only explicit invocations launch native KiCad.
"""
from __future__ import annotations

import argparse
import copy
import datetime
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time


PROJECTS = {
    "interf_u": ("kicad-interf-u", "interf_u"),
    "complex_hierarchy": ("kicad-complex-hierarchy", "complex_hierarchy"),
}


def native_worker(board_path, dsn_path, report_path):
    """Read copied originals, use native resolution, export without saving board."""
    import pcbnew

    board_path, dsn_path, report_path = map(Path, (board_path, dsn_path, report_path))
    root = board_path.parent.parent
    if board_path.parent.name != "native-input" or dsn_path.parent != root or report_path.parent != root:
        raise ValueError("Native worker requires its isolated native-input project")
    if dsn_path.exists() or report_path.exists():
        raise ValueError("Native worker refuses existing outputs")
    board = pcbnew.LoadBoard(str(board_path))
    if not board or board.GetCopperLayerCount() != 2:
        raise ValueError("Probe currently qualifies two-layer native inputs only")
    board.SynchronizeNetsAndNetClasses(False)
    pad_counts = {}
    for pad in board.GetPads():
        if pad.GetNetCode() > 0 and (pad.IsOnLayer(pcbnew.F_Cu) or pad.IsOnLayer(pcbnew.B_Cu)):
            name = str(pad.GetNetname())
            pad_counts[name] = pad_counts.get(name, 0) + 1
    nets = []
    for name, net in board.GetNetsByName().items():
        if not str(name) or net.GetNetCode() <= 0:
            continue
        # The installed 10.0.0 SWIG binding exposes GetNetClass's raw pointer as
        # SwigPyObject. Its shared_ptr-returning accessor is a usable NETCLASS.
        cls = net.GetNetClassSlow()
        nets.append({"name": str(name), "netcode": net.GetNetCode(),
                     "class": str(cls.GetName()), "width_nm": cls.GetTrackWidth(),
                     "clearance_nm": cls.GetClearance(), "via_diameter_nm": cls.GetViaDiameter(),
                     "via_drill_nm": cls.GetViaDrill(), "copper_pad_count": pad_counts.get(str(name), 0)})
    if not nets or not pcbnew.ExportSpecctraDSN(board, str(dsn_path)):
        raise ValueError("Native board has no nets or DSN export failed")
    data = {"schema": 1, "native_version": pcbnew.GetBuildVersion(),
            "resolution": "BOARD.SynchronizeNetsAndNetClasses(False); NETINFO_ITEM.GetNetClassSlow()",
            "units": "integer nanometres", "nets": sorted(nets, key=lambda n: n["name"]),
            "board_saved": False, "solver_executed": False}
    with report_path.open("x") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")


def audit_mapping(tree, native, project):
    """Compare DSN to native-resolved membership; never evaluate pattern strings."""
    from autorouter import sexpr as sx
    from autorouter.adapter import _check_units

    _check_units(tree)
    if native.get("native_version") != "10.0.0":
        raise ValueError("Unexpected native version")
    network, library, structure = (sx.one(tree, key) for key in ("network", "library", "structure"))
    if any(node is None for node in (network, library, structure)):
        raise ValueError("DSN is missing required network/library/structure")
    records = {row["name"]: row for row in native["nets"]}
    if len(records) != len(native["nets"]):
        raise ValueError("Duplicate native net")
    expected = {name for name, row in records.items() if row["copper_pad_count"] > 0}
    exported = [sx.unquote(node[1]) for node in sx.children(network, "net")]
    if len(set(exported)) != len(exported) or set(exported) != expected:
        raise ValueError("DSN/native copper-terminal net inventory differs")
    for net in sx.children(network, "net"):
        if any(isinstance(x, list) and x[0] != "pins" for x in net[2:]):
            raise ValueError("Unqualified DSN net override")
    configured = {item["name"]: item for item in project["net_settings"]["classes"]}
    floors = project["board"]["design_settings"]["rules"]
    observed_classes = {row["class"] for row in records.values()}
    # These two particular probes must exercise at least one nondefault class;
    # default-only output could otherwise hide failure to load project settings.
    if observed_classes <= {"Default"}:
        raise ValueError("Native resolution did not exercise a nondefault class")
    for row in records.values():
        cls = configured.get(row["class"])
        if cls is None:
            raise ValueError("Composite/implicit native class outside this narrow probe")
        for native_key, json_key, floor_key in (
            ("width_nm", "track_width", "min_track_width"),
            ("clearance_nm", "clearance", "min_clearance"),
            ("via_diameter_nm", "via_diameter", "min_via_diameter"),
            ("via_drill_nm", "via_drill", "min_through_hole_diameter"),
        ):
            value = Decimal(str(row[native_key]))
            if value != Decimal(str(cls[json_key])) * 1000000:
                raise ValueError("Native resolved class differs from original project value: " + native_key)
            if value < Decimal(str(floors.get(floor_key, 0))) * 1000000:
                raise ValueError("Class parameter below original board floor: " + native_key)
    layers = {sx.unquote(x[1]) for x in sx.children(structure, "layer")}
    if len(layers) != 2:
        raise ValueError("Probe only understands two-layer through-via export")
    stacks = {sx.unquote(x[1]): x for x in sx.children(library, "padstack")}
    declared_vias = sx.one(structure, "via")
    if declared_vias is None:
        raise ValueError("DSN via declaration missing")
    declared_vias = {sx.unquote(x) for x in declared_vias[1:]}
    membership, classes = {}, []
    for cls in sx.children(network, "class"):
        name = sx.unquote(cls[1])
        members = [sx.unquote(x) for x in cls[2:] if isinstance(x, str)]
        if len(members) != len(set(members)):
            raise ValueError("Duplicate class member")
        if any(isinstance(x, list) and x[0] not in {"rule", "circuit"} for x in cls[2:]):
            raise ValueError("Unqualified DSN class override")
        rules, circuit = sx.one(cls, "rule"), sx.one(cls, "circuit")
        if rules is None or circuit is None or {x[0] for x in rules[1:]} != {"width", "clearance"}:
            raise ValueError("Missing or unqualified DSN class rules")
        width, clearance = sx.one(rules, "width"), sx.one(rules, "clearance")
        via = sx.one(circuit, "use_via")
        if any(len(x) != 2 for x in (width, clearance)) or via is None or len(via) != 2:
            raise ValueError("Malformed class geometry")
        via_id = sx.unquote(via[1])
        match = re.fullmatch(r"Via\[0-1\]_([0-9.]+):([0-9.]+)_um", via_id)
        if not match or via_id not in declared_vias or via_id not in stacks:
            raise ValueError("Unknown native through-via ID or padstack")
        dimensions = {"width_nm": Decimal(width[1]) * 1000,
                      "clearance_nm": Decimal(clearance[1]) * 1000,
                      "via_diameter_nm": Decimal(match[1]) * 1000,
                      "via_drill_nm": Decimal(match[2]) * 1000}
        if any(not value.is_finite() or value <= 0 for value in dimensions.values()):
            raise ValueError("Invalid exported class dimension")
        shapes = sx.children(stacks[via_id], "shape")
        shape_layers = set()
        for shape in shapes:
            circle = sx.one(shape, "circle")
            if circle is None or len(circle) != 3:
                raise ValueError("Unqualified via shape")
            shape_layers.add(sx.unquote(circle[1]))
            if Decimal(circle[2]) * 1000 != dimensions["via_diameter_nm"]:
                raise ValueError("Via ID and actual copper shape disagree")
        if len(shapes) != 2 or shape_layers != layers:
            raise ValueError("Through-via layer coverage differs")
        for net in members:
            if net not in records or net in membership:
                raise ValueError("Unknown or multiply assigned DSN class member")
            row = records[net]
            expected_name = "kicad_default" if row["class"] == "Default" else row["class"]
            if name != expected_name or any(value != row[key] for key, value in dimensions.items()):
                raise ValueError("DSN class differs from native mapping for " + net)
            membership[net] = name
        classes.append({"dsn_class": name, "member_count": len(members),
                        "via": via_id, "dimensions_nm": {key: str(value) for key, value in dimensions.items()}})
    if set(membership) != set(records):
        raise ValueError("Native net missing from explicit DSN classes")
    return {"passed": True, "native_nets": len(records), "exported_terminal_nets": len(expected),
            "classes": classes, "membership": membership,
            "limitation": "Via drill is encoded by pinned KiCad via ID; no solver/import/DRC tested."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=sorted(PROJECTS), default="interf_u")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    from autorouter import config as c, sexpr as sx
    from autorouter.adapter import _parse_dsn, _dump_dsn
    from autorouter.pipeline import Job, Rejected, check_storage, save_json, sha, tool_manifest, tree_hash

    output_arg = Path(args.output).absolute()
    if output_arg.is_symlink() or output_arg.parent.resolve() != c.ROOT / ".runs":
        raise Rejected("Output must be a new direct child of the real .runs directory")
    if (c.ROOT / ".runs").is_symlink():
        raise Rejected("Symlinked .runs directory")
    check_storage()
    project_id, stem = PROJECTS[args.project]
    source_dir = c.ROOT / ".data/boards" / project_id
    source = source_dir / (stem + ".kicad_pcb")
    before = tree_hash(source_dir)
    manifest_path = c.ROOT / "data/sources.json"
    manifest = json.loads(manifest_path.read_text())
    expected = {str(Path(item["destination"]).relative_to(Path("boards") / project_id)): item["sha256"]
                for item in manifest["files"] if item.get("project_id") == project_id}
    if before != expected:
        raise Rejected("Original source inventory differs from acquisition manifest")
    project = json.loads(source.with_suffix(".kicad_pro").read_text())
    custom_rules = source.with_suffix(".kicad_dru")
    if custom_rules.exists() and custom_rules.read_text().strip():
        raise Rejected("Custom rule interaction outside this capability probe")
    tools = tool_manifest()
    job = Job(output_arg, 60)
    report = {"schema": 1, "experiment": "native netclass DSN mapping capability", "split": "development",
              "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source": str(source), "source_hashes": before, "source_manifest_sha256": sha(manifest_path),
              "tools": tools, "script_sha256": sha(__file__), "budget_seconds": 60,
              "original_rule_hashes": {name: value for name, value in before.items()
                                       if name.endswith((".kicad_pro", ".kicad_dru"))},
              "custom_rule_file_present": custom_rules.exists(), "native_execution_proven": False,
              "solver_executed": False, "native_drc_executed": False, "routing_accepted": False,
              "pipeline_eligibility_changed": False, "passed": False}
    try:
        shutil.copy2(__file__, job.out / "netclass_probe.py")
        code = job.out / "code"
        code.mkdir()
        for path in (c.ROOT / "autorouter").glob("*.py"):
            shutil.copy2(path, code / path.name)
        shutil.copytree(source_dir, job.out / "snapshot")
        shutil.copytree(source_dir, job.out / "native-input")
        if tree_hash(job.out / "snapshot") != before or tree_hash(job.out / "native-input") != before:
            raise Rejected("Copy differs from source")
        env = {key: value for key, value in job.env.items()
               if not key.startswith("KICAD_") and key not in {"PYTHONPATH", "PYTHONHOME"}}
        for key in ("KICAD_CONFIG_HOME", "KICAD_CACHE_HOME", "KICAD_DOCUMENTS_HOME"):
            env[key] = job.env[key]
        (job.out / "tmp").mkdir()
        env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(job.out / "tmp"))
        job.env = env
        dsn, native_file = job.out / "native.dsn", job.out / "native-netclasses.json"
        job.step("native-export-probe", ["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)",
                                        c.PYTHON, job.out / "netclass_probe.py", "--native-worker",
                                        job.out / "native-input" / source.name, dsn, native_file])
        report["native_execution_proven"] = native_file.is_file() and dsn.is_file()
        original_dsn_hash = sha(dsn)
        native = json.loads(native_file.read_text())
        tree = _parse_dsn(dsn.read_text())
        report["positive"] = audit_mapping(tree, native, project)
        report["negative_controls"] = []
        nondefault = [node for node in sx.children(sx.one(tree, "network"), "class")
                      if sx.unquote(node[1]) != "kicad_default" and any(isinstance(x, str) for x in node[2:])]
        if not nondefault:
            raise Rejected("No nondefault DSN class available for counterexamples")
        for key in ("width", "clearance"):
            altered = copy.deepcopy(tree)
            cls = next(node for node in sx.children(sx.one(altered, "network"), "class") if node[1] == nondefault[0][1])
            value = sx.one(sx.one(cls, "rule"), key)
            value[1] = str(Decimal(value[1]) / 2)
            false_dsn = job.out / ("counterexample-narrow-" + key + ".dsn")
            false_dsn.write_text(_dump_dsn(altered))
            rejected, reason = False, None
            try:
                audit_mapping(_parse_dsn(false_dsn.read_text()), native, project)
            except ValueError as exc:
                rejected, reason = True, str(exc)
            report["negative_controls"].append({"field": key, "rejected": rejected, "reason": reason,
                                                "dsn_sha256": sha(false_dsn), "native_routing_claim": False})
        report["native_input_hashes_after"] = tree_hash(job.out / "native-input")
        if report["native_input_hashes_after"] != before:
            raise Rejected("Native export changed copied project/rules/file set")
        report["bindings"] = {"native_dsn_sha256": sha(dsn), "native_report_sha256": sha(native_file)}
        report["original_dsn_unchanged"] = sha(dsn) == original_dsn_hash
        if not report["original_dsn_unchanged"]:
            raise Rejected("Original exported DSN changed during counterexample audit")
        report["passed"] = all(item["rejected"] for item in report["negative_controls"])
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        report["source_hashes_after"] = tree_hash(source_dir)
        report["source_unchanged"] = report["source_hashes_after"] == before
        report["snapshot_unchanged"] = (job.out / "snapshot").is_dir() and tree_hash(job.out / "snapshot") == before
        report["passed"] = report["passed"] and report["source_unchanged"] and report["snapshot_unchanged"]
        report["steps"] = job.steps
        report["wall_seconds"] = time.monotonic() - job.started
        report["parent_cpu_seconds"] = time.process_time() - job.cpu_started
        report["total_cpu_seconds"] = report["parent_cpu_seconds"] + sum(
            (step.get("cpu_seconds") or 0) + (step.get("monitor_cpu_seconds") or 0) for step in job.steps)
        report["within_wall_budget"] = report["wall_seconds"] <= report["budget_seconds"]
        report["passed"] = report["passed"] and report["within_wall_budget"]
        save_json(job.out / "result.json", report)
    print(json.dumps({"passed": report["passed"], "result": str(job.out / "result.json"), "error": report.get("error")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--native-worker":
        native_worker(*sys.argv[2:])
    else:
        sys.exit(main())
