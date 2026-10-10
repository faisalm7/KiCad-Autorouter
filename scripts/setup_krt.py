#!/usr/bin/env python3
"""Acquire audited KRT 0.23.0 assets and isolated pinned macOS arm64 wheels.

No KRT installer, build hook, plugin registration or router is executed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import stat
import subprocess
import sys
import urllib.request
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / ".tools"
ASSETS = TOOLS / "krt-0.23.0-assets"
SOURCE = TOOLS / "KiCadRoutingTools-0.23.0"
VENV = TOOLS / "krt-0.23.0-venv"
COMMIT = "9399bfb29e072bfe60b10d9cdae20c274fc2a17a"
RELEASE = "https://github.com/drandyhaas/KiCadRoutingTools/releases/download/v0.23.0/"
PACKAGES = [
    ("KiCadRoutingTools-0.23.0.zip", 14844957,
     "d325f617492bd69943e50dd9f5a9119d328c854e33ab54cac4c96e90d05c52a1", RELEASE + "KiCadRoutingTools-0.23.0.zip"),
    ("grid_router-macos-arm64.so", 1039632,
     "ed667cfbde051e3824c25a21635b322b5adec10d5b1475ad80f1c3e4d066d8d7", RELEASE + "grid_router-macos-arm64.so"),
    ("numpy-1.26.4-cp311-cp311-macosx_11_0_arm64.whl", 13997127,
     "edd8b5fe47dab091176d21bb6de568acdd906d1887a4584a15a9a96a1dca06ef",
     "https://files.pythonhosted.org/packages/1a/2e/151484f49fd03944c4a3ad9c418ed193cfd02724e138ac8a9505d056c582/numpy-1.26.4-cp311-cp311-macosx_11_0_arm64.whl"),
    ("scipy-1.13.1-cp311-cp311-macosx_12_0_arm64.whl", 30317687,
     "54f430b00f0133e2224c3ba42b805bfd0086fe488835effa33fa291561932326",
     "https://files.pythonhosted.org/packages/ba/92/42476de1af309c27710004f5cdebc27bec62c204db42e05b23a302cb0c9a/scipy-1.13.1-cp311-cp311-macosx_12_0_arm64.whl"),
    ("shapely-2.0.6-cp311-cp311-macosx_11_0_arm64.whl", 1296792,
     "9a7a78b0d51257a367ee115f4d41ca4d46edbd0dd280f697a8092dd3989867b2",
     "https://files.pythonhosted.org/packages/37/63/e182e43081fffa0a2d970c480f2ef91647a6ab94098f61748c23c2a485f2/shapely-2.0.6-cp311-cp311-macosx_11_0_arm64.whl"),
]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def checked_asset(entry, check=False):
    name, size, expected, url = entry
    target = ASSETS / name
    if target.is_symlink():
        raise RuntimeError("Asset symlink refused")
    if not target.exists():
        if check:
            raise RuntimeError("Missing pinned asset: " + name)
        temporary = ASSETS / (name + ".download-" + uuid.uuid4().hex)
        with urllib.request.urlopen(url, timeout=45) as source, temporary.open("xb") as output:
            received = 0
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > size:
                    raise RuntimeError("Download exceeded pinned size; partial retained")
                output.write(chunk)
        if temporary.stat().st_size != size or sha(temporary) != expected:
            raise RuntimeError("Download hash mismatch; partial retained")
        # Exclusive destination creation; never overwrite a prior artifact.
        os.link(temporary, target)
        temporary.unlink()
    if target.stat().st_size != size or sha(target) != expected:
        raise RuntimeError("Existing pinned asset mismatch: " + name)
    return target


def checked_members(archive):
    seen, total = set(), 0
    for item in archive.infolist():
        path = PurePosixPath(item.filename.rstrip("/"))
        mode = item.external_attr >> 16
        total += item.file_size
        if (not item.filename or path.is_absolute() or ".." in path.parts or
                "\\" in item.filename or str(path) != item.filename.rstrip("/") or
                item.filename in seen or stat.S_ISLNK(mode) or
                (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)) or
                total > 350 * 1024 * 1024 or len(seen) > 10000):
            raise RuntimeError("Unsafe or oversized archive")
        seen.add(item.filename)
        yield item


def install_source(package, binary, check):
    # Preserve upstream files exactly; skip unrelated platform executables.
    selected = {}
    with zipfile.ZipFile(package) as archive:
        for item in checked_members(archive):
            if item.is_dir() or not item.filename.startswith("plugins/"):
                continue
            relative = item.filename[len("plugins/"):]
            if relative.endswith((".so", ".pyd")):
                continue
            selected[relative] = archive.read(item)
    selected["rust_router/grid_router.so"] = binary.read_bytes()
    if SOURCE.is_symlink():
        raise RuntimeError("Source destination symlink refused")
    if SOURCE.exists():
        for relative, content in selected.items():
            path = SOURCE / relative
            if path.is_symlink() or not path.is_file() or sha(path) != hashlib.sha256(content).hexdigest():
                raise RuntimeError("Existing KRT source differs; refusing overwrite: " + relative)
        return
    if check:
        raise RuntimeError("KRT source is not installed")
    SOURCE.mkdir()
    for relative, content in selected.items():
        path = SOURCE / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(content)


def run(argv):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL")}
    env.update(PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1")
    process = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    if process.returncode:
        raise RuntimeError("Isolated environment command failed: " + process.stderr[-4000:])
    return process.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing installation without network or writes")
    args = parser.parse_args()
    if platform.system() != "Darwin" or platform.machine() != "arm64" or sys.version_info[:2] != (3, 11):
        raise RuntimeError("This pin set requires native macOS arm64 CPython 3.11")
    for directory in (TOOLS, ASSETS, VENV):
        if directory.is_symlink():
            raise RuntimeError("Setup directory symlink refused")
    if not args.check:
        if shutil.disk_usage(ROOT).free < 1024 ** 3:
            raise RuntimeError("Need at least 1 GiB free before the bounded dependency setup")
        ASSETS.mkdir(parents=True, exist_ok=True)
    assets = [checked_asset(entry, args.check) for entry in PACKAGES]
    for path in assets[2:]:
        with zipfile.ZipFile(path) as wheel:
            for item in checked_members(wheel):
                if item.filename.endswith(".pth"):
                    raise RuntimeError("Wheel startup hook requires separate inspection")
    install_source(assets[0], assets[1], args.check)
    marker = VENV / "krt-environment.json"
    expected = {"purpose": "KiCadRoutingTools 0.23.0 experiment", "python": "3.11", "packages": {"numpy": "1.26.4", "scipy": "1.13.1", "shapely": "2.0.6"}}
    if VENV.exists():
        if not marker.is_file() or json.loads(marker.read_text()) != expected:
            raise RuntimeError("Existing venv is unrecognized; refusing modification")
    elif args.check:
        raise RuntimeError("Isolated KRT environment is missing")
    else:
        run([sys.executable, "-m", "venv", str(VENV)])
        with marker.open("x") as stream:
            json.dump(expected, stream, indent=2)
    python = VENV / "bin/python"
    if not args.check:
        # Wheels only, no index/dependency resolution, and network denied during
        # installation; no setup.py or source build can be selected.
        run(["/usr/bin/sandbox-exec", "-p", "(version 1)(allow default)(deny network*)", str(python), "-m", "pip", "install", "--no-index", "--no-deps", "--no-cache-dir", *map(str, assets[2:])])
    versions = json.loads(run([str(python), "-c", "import importlib.metadata as m,json; print(json.dumps({n:m.version(n) for n in ('numpy','scipy','shapely')}))"]))
    if versions != expected["packages"]:
        raise RuntimeError("Installed package metadata differs from pins")
    receipt = {"version": "0.23.0", "source_commit": COMMIT, "source": str(SOURCE), "python": str(python), "assets": [{"name": e[0], "size": e[1], "sha256": e[2], "url": e[3]} for e in PACKAGES], "dependencies": versions, "license": "MIT (upstream LICENSE preserved); wheel notices retained in site-packages", "routing_executed": False, "plugin_installed": False}
    if not args.check:
        with (ASSETS / ("setup-receipt-" + uuid.uuid4().hex + ".json")).open("x") as stream:
            json.dump(receipt, stream, indent=2)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, zipfile.BadZipFile) as exc:
        raise SystemExit(str(exc))
