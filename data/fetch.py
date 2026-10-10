#!/usr/bin/env python3
"""Fetch only reviewed, pinned native development projects; never execute data."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("sources.json")
MAX_BYTES = 10 * 1024 * 1024
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
REVIEWED_PROJECTS = {
    "sonde xilinx": "kicad-sonde-xilinx",
    "pic_programmer": "kicad-pic-programmer",
    "complex_hierarchy": "kicad-complex-hierarchy",
    "interf_u": "kicad-interf-u",
    "multichannel": "kicad-multichannel",
    "kit-dev-coldfire-xilinx_5213": "kicad-coldfire-xilinx",
}
DATA_SUFFIXES = {".kicad_pcb", ".kicad_pro", ".kicad_sch", ".kicad_sym",
                 ".kicad_mod", ".kicad_wks", ".wrl", ".bmp", ".wings"}
NOTICE_NAMES = ("LICENSE.README", "LICENSE.CC-BY-SA-4.0")


def relative_path(value: str) -> Path:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")) or "\\" in value:
        raise ValueError(f"Unsafe manifest path: {value!r}")
    return Path(*path.parts)


def safe_destination(relative: str) -> Path:
    path = ROOT / ".data" / relative_path(relative)
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError(f"Symlink destination refused: {cursor}")
    return path


def verify_bytes(data: bytes, item: dict) -> None:
    if len(data) != item["bytes"]:
        raise ValueError(f"Size mismatch: {item['source_path']}")
    if hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(f"SHA256 mismatch: {item['source_path']}")
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if git_blob != item["git_blob_sha1"]:
        raise ValueError(f"Git blob mismatch: {item['source_path']}")


def load_manifest() -> dict:
    manifest = json.loads(MANIFEST.read_text())
    if manifest["schema_version"] != 1 or manifest["split"] != "development":
        raise ValueError("Unsupported manifest schema or split")
    if manifest["repository"] != "KiCad/kicad-source-mirror" or not re.fullmatch(r"[0-9a-f]{40}", manifest["commit"]):
        raise ValueError("Unreviewed repository or revision")
    files = manifest["files"]
    if not files or any(type(item.get("bytes")) is not int or item["bytes"] < 0 for item in files):
        raise ValueError("Invalid source byte count")
    if sum(item["bytes"] for item in files) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds the bounded 32 MiB population limit")
    destinations = set()
    for item in files:
        relative_path(item["source_path"])
        destination = safe_destination(item["destination"])
        if destination in destinations or not 0 <= item["bytes"] <= MAX_BYTES:
            raise ValueError("Duplicate destination or invalid size")
        destinations.add(destination)
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) or not re.fullmatch(r"[0-9a-f]{40}", item["git_blob_sha1"]):
            raise ValueError("Invalid pinned digest")
        if item.get("project_id") not in REVIEWED_PROJECTS.values():
            raise ValueError("Unknown source project binding")
        if not item["destination"].startswith("boards/" + item["project_id"] + "/"):
            raise ValueError("Source project binding differs from destination")
        source = item["source_path"]
        if source in NOTICE_NAMES:
            if item["destination"] not in {f"boards/{name}/_licenses/{source}" for name in REVIEWED_PROJECTS.values()}:
                raise ValueError("Unreviewed license destination")
        else:
            parts = PurePosixPath(source).parts
            if len(parts) < 3 or parts[0] != "demos" or parts[1] not in REVIEWED_PROJECTS:
                raise ValueError(f"Unreviewed source path: {source}")
            if PurePosixPath(source).suffix not in DATA_SUFFIXES and parts[-1] not in ("fp-lib-table", "sym-lib-table"):
                raise ValueError(f"Unreviewed file type: {source}")
            expected = "boards/" + REVIEWED_PROJECTS[parts[1]] + "/" + "/".join(parts[2:])
            if item["destination"] != expected:
                raise ValueError("Source-to-destination mapping changed")
        if item["mode"] != "100644":
            raise ValueError("Executable files and symlinks are not permitted")
    if not isinstance(manifest.get("projects"), list):
        raise ValueError("Complete project population is required")
    if "projects" in manifest:
        projects = manifest["projects"]
        if len(projects) != len(REVIEWED_PROJECTS) or {p["project_id"] for p in projects} != set(REVIEWED_PROJECTS.values()):
            raise ValueError("Considered project population is incomplete")
        for project in projects:
            source_name = next(name for name, identifier in REVIEWED_PROJECTS.items() if identifier == project["project_id"])
            if project["source_directory"] != "demos/" + source_name or project["destination"] != "boards/" + project["project_id"]:
                raise ValueError("Project source mapping changed")
            owned_files = [item for item in files if item["project_id"] == project["project_id"]]
            if sum(item["bytes"] for item in owned_files) > MAX_BYTES:
                raise ValueError("Project exceeds the 10 MiB project limit including notices")
            prefix = project["source_directory"] + "/"
            project_files = [item for item in files if item["source_path"].startswith(prefix)]
            if len(project_files) != project["source_files"] or sum(item["bytes"] for item in project_files) != project["source_bytes"]:
                raise ValueError("Project inventory count or size mismatch")
            if {item["destination"] for item in project_files if item["source_path"].endswith(".kicad_pcb")} != {board["board"] for board in project["boards"]}:
                raise ValueError("Native board inventory is incomplete")
            for board in project["boards"]:
                for key in ("board", "project_file"):
                    if safe_destination(board[key]) not in destinations:
                        raise ValueError("Native board/project missing from manifest")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Verify all local files without any network access")
    parser.add_argument("--project", action="append", choices=sorted(REVIEWED_PROJECTS.values()),
                        help="Select a reviewed project; repeat to form a download batch of at most 10 MiB")
    args = parser.parse_args()
    manifest = load_manifest()
    selected = set(args.project or REVIEWED_PROJECTS.values())
    files = [item for item in manifest["files"] if item["project_id"] in selected]
    # Validate the complete selected local population before any download. A
    # corrupt existing file or an oversized missing-file batch stops untouched.
    missing_bytes = 0
    for item in files:
        destination = safe_destination(item["destination"])
        if destination.exists():
            if not destination.is_file() or destination.stat().st_size != item["bytes"]:
                raise ValueError(f"Existing file differs; preserve and investigate it: {destination}")
            verify_bytes(destination.read_bytes(), item)
        else:
            if args.verify:
                raise ValueError(f"Missing source file: {destination}")
            missing_bytes += item["bytes"]
    if missing_bytes > MAX_BYTES:
        raise ValueError("Missing-source batch exceeds 10 MiB; select one or more --project values for bounded acquisition")
    total = 0
    fetched = 0
    for item in files:
        destination = safe_destination(item["destination"])
        if destination.exists():
            if not destination.is_file() or destination.stat().st_size != item["bytes"]:
                raise ValueError(f"Existing file differs; preserve and investigate it: {destination}")
            verify_bytes(destination.read_bytes(), item)
        elif args.verify:
            raise ValueError(f"Missing source file: {destination}")
        else:
            url = "https://raw.githubusercontent.com/" + manifest["repository"] + "/" + manifest["commit"] + "/" + urllib.parse.quote(item["source_path"], safe="/")
            request = urllib.request.Request(url, headers={"User-Agent": "KiCad-Autorouter-development-fetch/1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                if urllib.parse.urlparse(response.url).hostname != "raw.githubusercontent.com":
                    raise ValueError("Unexpected download redirect")
                data = response.read(item["bytes"] + 1)
            verify_bytes(data, item)
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Recheck after mkdir. Never overwrite an existing or concurrently created source.
            safe_destination(item["destination"])
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".fetch-", delete=False) as handle:
                    temporary = Path(handle.name)
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.link(temporary, destination)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            fetched += 1
        total += item["bytes"]
    selected_boards = [board["board"] for project in manifest["projects"]
                       if project["project_id"] in selected for board in project["boards"]]
    print(json.dumps({"status": "verified", "split": "development", "files": len(files), "bytes": total, "downloaded": fetched, "commit": manifest["commit"], "board": str(ROOT / ".data" / selected_boards[0]), "projects": len(selected), "selected_projects": sorted(selected), "planned_download_bytes": missing_bytes, "native_board_files": len(selected_boards)}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
