#!/usr/bin/env python3
"""Private on-Mac backup and restoration check; never deletes an earlier backup."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import subprocess
import sys
import tarfile
import uuid
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SCOPES = (".runs", ".data", ".local-reference")
# Actual October14 stat forecast retains260,600files/7,498,045,240B after
# CellScan trials and installation021. It exceeds the old260,000file ceiling
# and leaves only18,147,528B below7GiB before the matched stock trial. Keep
# all evidence: finite8GiB/270,000 ceilings, unchanged scopes/secret/path guards,
# receipt-memory caps/streaming/chains. Actual backup and full restore required.
LIMIT = 8 * 1024 ** 3
MAX_FILES = 270000
MAX_CHAIN = 16
# Actual229,196-file receipt is63,984,764B. The249,270-file forecast needs
# about70MB at that measured ratio;80MiB permits finite headroom. Two such
# receipts fit the192MiB chain bound. No scopes or safety checks change.
MAX_RECEIPT_BYTES = 80 * 1024 ** 2
MAX_CHAIN_RECEIPT_BYTES = 192 * 1024 ** 2
LIMITATION = "On-Mac only; a second folder on this disk provides no disk-failure protection."
SECRET_NAMES = {".env", ".ssh", ".aws", ".gnupg", "credentials", "credentials.json", "secrets", "secrets.json", "id_rsa", "id_ed25519"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keychain", ".keychain-db"}


# This exact public unit-test source contains only a synthetic PEM header used
# to exercise this guard. Fresh-install copies are archived byte-for-byte.
# Any content change or different path still fails. Reviewed at dd2cce9.
NONSECRET_TEST_SOURCE = "6d010b7d95db21e6921d9c2af9647e29a33725bdc835d03136928648e69d63ee"
AUDITED_DRAFT_TEST_SOURCES = {
    # Actual installation021 uses a descriptive suffix, outside the legacy
    # numeric-install regex. Byte-identical to public tests/test_backup.py;
    # only this exact path/hash of the synthetic-header test is exempt.
    ".runs/installation-021-current965/checkout/tests/test_backup.py":
        "39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a",
    # Byte-identical public test source; inspected after the d183c43 guard stop.
    ".runs/board-floor-production-draft-001/tests/test_backup.py":
        "39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a",
    # Byte-identical to public tests/test_backup.py at 8cd8cc4. This one
    # retained policy-test staging copy is evidence, not a credential.
    ".runs/padstack-policy-draft-001/stage/tests/test_backup.py":
        "39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a",
}


def audited_nonsecret_test_source(relative, sha256):
    return ((re.fullmatch(r"[.]runs/installation-[0-9]+/checkout/tests/test_backup[.]py", relative) is not None
            and sha256 in {NONSECRET_TEST_SOURCE, "39fffc805691665b89433577a633ddc6929b5d0aba13f75c1a66db8ca03cd97a"})
            or (relative in AUDITED_DRAFT_TEST_SOURCES
                and AUDITED_DRAFT_TEST_SOURCES[relative] == sha256))


class BackupError(RuntimeError):
    pass


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(root, *args):
    # Ignore user/global Git config during archival and scratch restoration. Do
    # not alter it; this prevents global hooks/filters from running in restores.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    result = subprocess.run(["git", "-c", "core.hooksPath=" + os.devnull,
                             "-c", "core.autocrlf=false", *args], cwd=root,
                            env=env, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise BackupError("Git operation failed: " + " ".join(args[:2]) + ": " + result.stderr[-2000:])
    return result.stdout.strip()


def exclusive_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def read_json(path):
    """Bounded regular-file, duplicate-key-free receipt read."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > MAX_RECEIPT_BYTES:
            raise BackupError("Receipt exceeds regular-file/size bounds")
        raw = stream.read(MAX_RECEIPT_BYTES + 1)
        after = os.fstat(stream.fileno())
    if len(raw) != before.st_size or (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise BackupError("Receipt changed during bounded read")
    def pairs(items):
        value = {}
        for key, entry in items:
            if key in value: raise BackupError("Duplicate receipt key")
            value[key] = entry
        return value
    value = json.loads(raw, object_pairs_hook=pairs,
                       parse_constant=lambda value: (_ for _ in ()).throw(BackupError("Nonfinite receipt value")))
    return value, hashlib.sha256(raw).hexdigest(), len(raw)


def backups_directory(root):
    path = root / ".local-backups"
    if path.is_symlink():
        raise BackupError("Backup directory must not be a symlink")
    path.mkdir(mode=0o700, exist_ok=True)
    if not path.is_dir():
        raise BackupError("Backup destination is not a directory")
    return path


def validate_name(name):
    if not isinstance(name, str):
        raise BackupError("Archive/inventory path must be a string")
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or
            ".." in path.parts or str(path) != name or "\\" in name or
            path.parts[0] not in SCOPES):
        raise BackupError("Archive/inventory path is outside the exact backup scopes")
    for part in path.parts:
        lower = part.lower()
        if lower in SECRET_NAMES or lower.startswith(".env.") or Path(lower).suffix in SECRET_SUFFIXES:
            raise BackupError("Credential-like path in backup scope; review and relocate it privately")
    return path


def inventory(root):
    files, directories, absent = [], [], []
    total = 0
    for scope in SCOPES:
        base = root / scope
        if base.is_symlink():
            raise BackupError("Symlink in backup scope")
        if not base.exists():
            absent.append(scope)
            continue
        if not base.is_dir():
            raise BackupError("Backup scope must be a directory")
        for current, dirs, names in os.walk(base, followlinks=False):
            current = Path(current)
            directories.append(current.relative_to(root).as_posix())
            if len(directories) > MAX_FILES:
                raise BackupError("Non-Git snapshot exceeds directory-count ceiling")
            for name in sorted(dirs + names):
                path = current / name
                relative = path.relative_to(root).as_posix()
                validate_name(relative)
                st = path.lstat()
                if stat.S_ISDIR(st.st_mode):
                    continue
                if not stat.S_ISREG(st.st_mode):
                    raise BackupError("Symlink or special file in backup scope")
                if st.st_nlink != 1:
                    raise BackupError("Hard-linked input requires explicit review before backup")
                total += st.st_size
                if total > LIMIT or len(files) >= MAX_FILES:
                    raise BackupError("Non-Git snapshot exceeds the configured byte/file-count ceiling")
                # Catch common embedded private-key/token forms, without logging
                # their contents. This is a guard, not exhaustive secret detection.
                h = hashlib.sha256()
                flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                with os.fdopen(os.open(path, flags), "rb") as stream:
                    tail = b""
                    possible_credential = False
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        block = tail + chunk
                        if re.search(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}", block):
                            possible_credential = True
                        h.update(chunk)
                        tail = block[-256:]
                    after = os.fstat(stream.fileno())
                if possible_credential and not audited_nonsecret_test_source(relative, h.hexdigest()):
                    raise BackupError("Possible credential in backup input; contents were not printed")
                if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns):
                    raise BackupError("Input changed during inventory")
                files.append({"path": relative, "size": st.st_size, "sha256": h.hexdigest()})
    return {"scopes": list(SCOPES), "absent_scopes": absent,
            "directories": sorted(directories), "files": sorted(files, key=lambda x: x["path"]),
            "total_file_bytes": total}


class LimitedWriter:
    def __init__(self, stream):
        self.stream, self.size = stream, 0

    def write(self, data):
        if self.size + len(data) > LIMIT:
            raise BackupError("Compressed archive exceeds the configured byte ceiling")
        written = self.stream.write(data)
        self.size += written
        return written

    def tell(self):
        return self.size

    def flush(self):
        return self.stream.flush()


def make_archive(root, archive, manifest):
    with archive.open("xb") as stream:
        os.chmod(archive, 0o600)
        with tarfile.open(fileobj=LimitedWriter(stream), mode="w:gz", format=tarfile.PAX_FORMAT) as out:
            for name in manifest["directories"]:
                item = tarfile.TarInfo(name)
                item.type, item.mode = tarfile.DIRTYPE, 0o700
                out.addfile(item)
            for row in manifest["files"]:
                path = root / row["path"]
                with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)), "rb") as source:
                    st = os.fstat(source.fileno())
                    if not stat.S_ISREG(st.st_mode) or st.st_size != row["size"]:
                        raise BackupError("Input changed during archive creation")
                    item = tarfile.TarInfo(row["path"])
                    item.size, item.mode = row["size"], 0o600
                    out.addfile(item, source)


def check_manifest(manifest):
    if manifest.get("scopes") != list(SCOPES):
        raise BackupError("Unexpected inventory scopes")
    files, dirs = {}, set()
    for name in manifest["directories"]:
        validate_name(name)
        if name in dirs:
            raise BackupError("Duplicate directory in inventory")
        dirs.add(name)
    if len(dirs) > MAX_FILES:
        raise BackupError("Inventory directory-count bound")
    for name in dirs:
        if name not in SCOPES and str(PurePosixPath(name).parent) not in dirs:
            raise BackupError("Inventory omits a parent directory")
    if "absent_scopes" in manifest and manifest["absent_scopes"] != [s for s in SCOPES if s not in dirs]:
        raise BackupError("Absent scopes do not match inventory directories")
    total = 0
    for row in manifest["files"]:
        name = row["path"]
        validate_name(name)
        if name in files or name in dirs or type(row["size"]) is not int or row["size"] < 0:
            raise BackupError("Invalid inventory entry")
        if not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]):
            raise BackupError("Invalid inventory hash")
        if str(PurePosixPath(name).parent) not in dirs:
            raise BackupError("Inventory omits a parent directory")
        total += row["size"]
        files[name] = row
    if total > LIMIT or len(files) > MAX_FILES or total != manifest["total_file_bytes"]:
        raise BackupError("Invalid inventory size")
    return files, dirs


def delta_inventory(previous, current):
    old, old_dirs = check_manifest(previous)
    new, new_dirs = check_manifest(current)
    changed = [row for name, row in sorted(new.items()) if old.get(name) != row]
    # All target directory names keep the existing standalone extraction guard.
    # Directory entries carry no payload; only changed/new files are archived.
    delta = {**current, "files": changed, "total_file_bytes": sum(row["size"] for row in changed)}
    return {"inventory": delta, "deleted_files": sorted(set(old) - set(new)),
            "deleted_directories": sorted(old_dirs - new_dirs)}


def archive_member(item, files, dirs, seen):
    """Check each observed header before any payload or destination is opened."""
    name = item.name.rstrip("/") if item.isdir() else item.name
    validate_name(name)
    if (name in seen or item.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
            or item.sparse is not None):
        raise BackupError("Duplicate, linked, or special archive member")
    if item.isdir():
        if name not in dirs or item.size:
            raise BackupError("Unexpected archive directory")
    elif name not in files or item.size != files[name]["size"]:
        raise BackupError("Unexpected archive file or size")
    seen.add(name)
    return name


def archive_payload(source, item, row, output=None):
    """Read no more than the declared payload plus one overflow sentinel byte."""
    remaining = row["size"]
    hashed = hashlib.sha256()
    with source.extractfile(item) as payload:
        while remaining:
            chunk = payload.read(min(1024 * 1024, remaining))
            if not chunk or len(chunk) > remaining:
                raise BackupError("Archive payload size mismatch")
            remaining -= len(chunk)
            hashed.update(chunk)
            if output is not None:
                output.write(chunk)
        if payload.read(1):
            raise BackupError("Archive payload exceeds inventory size")
    if hashed.hexdigest() != row["sha256"]:
        raise BackupError("Restored non-Git file hash mismatch")


def audit_archive(archive, manifest):
    """Exact safe member and payload validation without restoring any files."""
    files, dirs = check_manifest(manifest)
    if archive.stat().st_size > LIMIT:
        raise BackupError("Archive exceeds compressed-size limit")
    seen = set()
    with tarfile.open(archive, "r|gz") as source:
        for item in source:
            name = archive_member(item, files, dirs, seen)
            if item.isreg():
                archive_payload(source, item, files[name])
    if seen != set(files) | dirs:
        raise BackupError("Archive does not exactly match inventory")
    return files, dirs


def restore_archive(archive, destination, manifest):
    """Whitelist both archive passes; never trust the earlier audit or extractall."""
    if destination.exists() or destination.is_symlink():
        raise BackupError("Refusing restore destination collision")
    files, dirs = audit_archive(archive, manifest)
    if archive.stat().st_size > LIMIT:
        raise BackupError("Archive exceeds compressed-size limit")
    destination.mkdir(mode=0o700)
    for name in sorted(dirs, key=lambda x: (len(PurePosixPath(x).parts), x)):
        (destination / name).mkdir(mode=0o700)
    seen = set()
    with tarfile.open(archive, "r|gz") as source:
        for item in source:
            name = archive_member(item, files, dirs, seen)
            if not item.isreg():
                continue
            target = destination / name
            with target.open("xb") as output:
                os.chmod(target, 0o600)
                archive_payload(source, item, files[name], output)
    if seen != set(files) | dirs:
        raise BackupError("Archive does not exactly match inventory")


def create(root=ROOT, parent=None):
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise BackupError("Run only in the selected Git checkout")
    if git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise BackupError("Commit/audit safe source first; backup refuses uncommitted or untracked nonignored files")
    head = git(root, "rev-parse", "HEAD")
    refs = git(root, "show-ref")
    chain = load_chain(parent, root) if parent is not None else None
    anchor = None
    if chain:
        if chain[-1]["receipt"]["source_root"] != str(root):
            raise BackupError("Incremental parent belongs to a different original source root")
        if len(chain) >= MAX_CHAIN:
            raise BackupError("Incremental chain ceiling reached; create a new full backup")
        anchor = chain[-1]["receipt"].get("base_verification") or find_base_verification(chain[0], root)
    manifest = inventory(root)
    delta = delta_inventory(chain[-1]["receipt"]["inventory"], manifest) if chain else None
    base = backups_directory(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = base / ("checkpoint-" + stamp + "-" + uuid.uuid4().hex)
    backup.mkdir(mode=0o700)  # Exclusive; earlier artifacts are never overwritten.
    bundle = backup / "repository.bundle"
    git(root, "bundle", "create", str(bundle), "--all")
    os.chmod(bundle, 0o600)
    if bundle.stat().st_size > LIMIT:
        raise BackupError("Git bundle exceeds the configured byte ceiling; retained for review")
    git(root, "bundle", "verify", str(bundle))
    archive = backup / "non-git.tar.gz"
    make_archive(root, archive, delta["inventory"] if delta else manifest)
    if manifest != inventory(root) or head != git(root, "rev-parse", "HEAD") or refs != git(root, "show-ref") or git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise BackupError("Source changed during snapshot; partial backup retained but not certified")
    receipt = {"schema": 1, "created_utc": stamp, "source_root": str(root), "git_head": head,
               "git_refs": refs.splitlines(), "inventory": manifest, "limitation": LIMITATION,
               "excluded": [".tools", "credentials", "other ignored directories"],
               "bundle": {"name": bundle.name, "sha256": digest(bundle), "size": bundle.stat().st_size},
               "archive": {"name": archive.name, "sha256": digest(archive), "size": archive.stat().st_size}}
    if chain:
        receipt.update(schema=2, kind="incremental", delta=delta, base_verification=anchor,
                       parent={"name": chain[-1]["path"].relative_to(base).as_posix(), "sha256": chain[-1]["sha256"]})
    path = backup / "receipt.json"
    exclusive_json(path, receipt)
    return path


def receipt_location(receipt_path, base):
    original = Path(receipt_path).absolute()
    if (".." in original.parts or original.is_symlink() or original.parent.is_symlink()
            or original.parent.parent != base or original.name != "receipt.json"):
        raise BackupError("Receipt must be a regular receipt.json directly inside a local backup")
    return original


def local_reference(base, entry, filename):
    name = entry["name"]
    parts = PurePosixPath(name).parts if isinstance(name, str) else ()
    if (len(parts) != 2 or PurePosixPath(name).is_absolute() or parts[-1] != filename or str(PurePosixPath(name)) != name
            or parts[0] in (".", "..") or "\\" in name or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])):
        raise BackupError("Unsafe local backup reference")
    return receipt_location(base / name, base) if filename == "receipt.json" else base / name


def check_artifacts(original, receipt):
    if receipt.get("schema") not in (1, 2) or not re.fullmatch(r"[0-9a-f]{40,64}", receipt.get("git_head", "")):
        raise BackupError("Unsupported or malformed backup receipt")
    check_manifest(receipt["inventory"])
    artifacts = {}
    for kind, name in (("bundle", "repository.bundle"), ("archive", "non-git.tar.gz")):
        path, entry = original.parent / name, receipt[kind]
        if entry["name"] != name or path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1 or path.stat().st_size != entry["size"] or path.stat().st_size > LIMIT or digest(path) != entry["sha256"]:
            raise BackupError("Backup artifact size/hash mismatch")
        artifacts[kind] = path
    # A full bundle must not rely on prerequisites in the current repository.
    with artifacts["bundle"].open("rb") as stream:
        header_bytes = 0
        while True:
            line = stream.readline(4097)
            header_bytes += len(line)
            if len(line) > 4096 or header_bytes > 4 * 1024 * 1024 or not line:
                raise BackupError("Malformed bundle header")
            if line == b"\n":
                break
            if line.startswith(b"-"):
                raise BackupError("Incremental bundle cannot independently restore full history")
    return artifacts


def check_base_verification(entry, full, root):
    base = backups_directory(root)
    name = PurePosixPath(entry["name"]).name
    if not re.fullmatch(r"verification-[0-9a-f]{32}\.json", name):
        raise BackupError("Restore verification reference required")
    path = local_reference(base, entry, name)
    if path.parent != full["path"].parent or path.is_symlink() or path.parent.is_symlink():
        raise BackupError("Verification must belong to the full base backup")
    data, hashed, _ = read_json(path)
    if (hashed != entry["sha256"] or data.get("verified") is not True
            or data.get("receipt_sha256") != full["sha256"]
            or data.get("restored_git_head") != full["receipt"]["git_head"]
            or data.get("all_refs_restored") is not True
            or data.get("git_bundle_verified_in_empty_repository") is not True
            or data.get("non_git_files_verified") != len(full["receipt"]["inventory"]["files"])
            or data.get("cli_smoke", {}).get("exit") != 0):
        raise BackupError("Base full backup lacks matching successful restoration evidence")


def find_base_verification(full, root):
    candidates = []
    with os.scandir(full["path"].parent) as entries:
        for count, item in enumerate(entries):
            if count >= 256: raise BackupError("Backup verification directory entry bound")
            if re.fullmatch(r"verification-[0-9a-f]{32}\.json", item.name): candidates.append(Path(item.path))
    for path in sorted(candidates):
        _, hashed, _ = read_json(path)
        entry = {"name": path.relative_to(backups_directory(root)).as_posix(), "sha256": hashed}
        check_base_verification(entry, full, root)
        return entry
    raise BackupError("Incremental requires an existing restore-verified full base")


def load_chain(receipt_path, root=ROOT):
    """Old full receipts remain roots; each new delta is independently recomputed."""
    root = Path(root).resolve(); base = backups_directory(root)
    path = receipt_location(receipt_path, base); reverse = []; seen = set(); expected = None; total = 0
    while True:
        if path in seen or len(reverse) >= MAX_CHAIN:
            raise BackupError("Backup parent cycle or chain-length bound")
        seen.add(path); receipt, hashed, size = read_json(path); total += size
        if total > MAX_CHAIN_RECEIPT_BYTES: raise BackupError("Chain receipt-memory bound")
        if expected is not None and hashed != expected: raise BackupError("Parent receipt hash mismatch")
        artifacts = check_artifacts(path, receipt)
        reverse.append({"path": path, "receipt": receipt, "sha256": hashed, "artifacts": artifacts})
        if receipt["schema"] == 1:
            if any(k in receipt for k in ("parent", "delta", "base_verification")): raise BackupError("Full receipt cannot hide incremental metadata")
            break
        if receipt.get("kind") != "incremental": raise BackupError("Unknown backup kind")
        path = local_reference(base, receipt["parent"], "receipt.json"); expected = receipt["parent"]["sha256"]
    chain = list(reversed(reverse))
    for previous, current in zip(chain, chain[1:]):
        data = current["receipt"]
        if data["source_root"] != previous["receipt"]["source_root"] or data["delta"] != delta_inventory(previous["receipt"]["inventory"], data["inventory"]):
            raise BackupError("Incremental inventory/deletion accounting mismatch")
        check_base_verification(data["base_verification"], chain[0], root)
        audit_archive(current["artifacts"]["archive"], data["delta"]["inventory"])
    return chain


def apply_delta(node, previous, destination, staging):
    """Only this newly created restoration tree is changed; backups are immutable."""
    data = node["receipt"]; delta = data["delta"]
    restore_archive(node["artifacts"]["archive"], staging, delta["inventory"])
    if inventory(destination) != previous:
        raise BackupError("Scratch restore differs from its parent inventory")
    old, _ = check_manifest(previous)
    replacements = {row["path"] for row in delta["inventory"]["files"]} & set(old)
    for name in sorted(set(delta["deleted_files"]) | replacements):
        (destination / name).unlink()  # Exact known regular files in our fresh private scratch only.
    for name in sorted(delta["deleted_directories"], key=lambda n: (-len(PurePosixPath(n).parts), n)):
        (destination / name).rmdir()  # Nonempty/unknown contents fail; no recursive deletion.
    for name in sorted(data["inventory"]["directories"], key=lambda n: (len(PurePosixPath(n).parts), n)):
        (destination / name).mkdir(mode=0o700, exist_ok=True)
    for row in delta["inventory"]["files"]:
        target = destination / row["path"]
        if target.exists() or target.is_symlink(): raise BackupError("Incremental restore collision")
        source = staging / row["path"]
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            os.chmod(target, 0o600)
            for chunk in iter(lambda: incoming.read(1024 * 1024), b""):
                outgoing.write(chunk)
        if digest(target) != row["sha256"]: raise BackupError("Incremental copied file hash mismatch")
        source.unlink()  # Only the fresh, already verified extraction staging copy.
    if inventory(destination) != data["inventory"]:
        raise BackupError("Complete incremental restoration inventory mismatch")


def check_chain_unchanged(chain):
    for node in chain:
        receipt, hashed, _ = read_json(node["path"])
        if hashed != node["sha256"] or receipt != node["receipt"]:
            raise BackupError("Receipt changed during verification")
        check_artifacts(node["path"], node["receipt"])
        if receipt["schema"] == 2:
            check_base_verification(receipt["base_verification"], chain[0], node["path"].parent.parent.parent)


def publish_check(path, result, stable):
    """Invalidate a detected failed proof; catch SIGTERM only during publication."""
    expected = json.loads(json.dumps(result, allow_nan=False))
    previous_term = signal.getsignal(signal.SIGTERM)

    def cancel(signum, frame):
        raise KeyboardInterrupt("Backup proof publication cancelled by SIGTERM")

    try:
        signal.signal(signal.SIGTERM, cancel)
        stable()
        exclusive_json(path, result)
        stable()
        if read_json(path)[0] != expected or result != expected:
            raise BackupError("Backup proof changed during publication")
    except (Exception, KeyboardInterrupt):
        if path.exists() or path.is_symlink():
            path.rename(path.parent / ("invalidated-" + uuid.uuid4().hex + "-" + path.name))
        raise
    finally:
        signal.signal(signal.SIGTERM, previous_term)


def checkpoint(receipt_path, root=ROOT):
    """Integrity checkpoint only; deliberately does not claim a full restoration."""
    chain = load_chain(receipt_path, root); node = chain[-1]
    if node["receipt"]["schema"] != 2: raise BackupError("Incremental checkpoint requires a delta receipt")
    # Validate the new payload using the same whitelist/hash restoration guard,
    # without copying the unchanged full population. Scratch is retained.
    base = backups_directory(Path(root).resolve()); scratch = base / ("delta-check-" + uuid.uuid4().hex)
    restore_archive(node["artifacts"]["archive"], scratch, node["receipt"]["delta"]["inventory"])
    result = {"schema": 2, "integrity_checked": True, "full_restoration_tested": False,
              "receipt": str(node["path"]), "receipt_sha256": node["sha256"], "chain_length": len(chain),
              "delta_files_verified": len(node["receipt"]["delta"]["inventory"]["files"]),
              "scratch_directory": str(scratch), "limitation": LIMITATION}
    path = node["path"].parent / ("integrity-" + uuid.uuid4().hex + ".json")
    publish_check(path, result, lambda: check_chain_unchanged(chain))
    return path


def verify(receipt_path, root=ROOT):
    root = Path(root).resolve(); base = backups_directory(root)
    chain = load_chain(receipt_path, root); node = chain[-1]
    original, receipt, artifacts = node["path"], node["receipt"], node["artifacts"]
    restore = base / ("restore-" + uuid.uuid4().hex)
    restore.mkdir(mode=0o700)
    checkout = restore / "checkout"
    checkout.mkdir(mode=0o700)
    git(checkout, "init", "--quiet")
    git(checkout, "symbolic-ref", "HEAD", "refs/heads/__backup_restore_unborn__")
    git(checkout, "bundle", "verify", str(artifacts["bundle"]))
    git(checkout, "fetch", "--quiet", "--no-write-fetch-head", str(artifacts["bundle"]), "refs/*:refs/*")
    # --all bundles also carry HEAD; a detached HEAD may not be reachable from
    # any named ref, so explicitly transfer its objects without adding a ref.
    git(checkout, "fetch", "--quiet", "--no-write-fetch-head", str(artifacts["bundle"]), "HEAD")
    if git(checkout, "show-ref").splitlines() != receipt["git_refs"]:
        raise BackupError("Restored Git refs mismatch")
    git(checkout, "checkout", "--quiet", "--detach", receipt["git_head"])
    if git(checkout, "rev-parse", "HEAD") != receipt["git_head"]:
        raise BackupError("Restored Git HEAD mismatch")
    restore_archive(chain[0]["artifacts"]["archive"], restore / "non-git", chain[0]["receipt"]["inventory"])
    for index in range(1, len(chain)):
        apply_delta(chain[index], chain[index-1]["receipt"]["inventory"], restore / "non-git", restore / ("delta-" + str(index)))
    smoke = subprocess.run([sys.executable, "-B", "-m", "autorouter", "--help"], cwd=checkout,
                           capture_output=True, text=True, timeout=20,
                           env={k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")})
    if smoke.returncode != 0 or "usage:" not in smoke.stdout.lower():
        raise BackupError("Restored CLI --help smoke failed: " + smoke.stderr[-2000:])
    def restored_stable():
        if (git(checkout, "rev-parse", "HEAD") != receipt["git_head"]
                or git(checkout, "show-ref").splitlines() != receipt["git_refs"]
                or git(checkout, "status", "--porcelain=v1", "--untracked-files=normal")):
            raise BackupError("Final restored Git state changed")
        if inventory(restore / "non-git") != receipt["inventory"]:
            raise BackupError("Final complete restored inventory mismatch")
        check_chain_unchanged(chain)
    result = {"schema": 1, "verified": True, "receipt": str(original),
              "receipt_sha256": digest(original), "restored_git_head": receipt["git_head"],
              "restore_directory": str(restore), "git_bundle_verified_in_empty_repository": True,
              "all_refs_restored": True, "non_git_files_verified": len(receipt["inventory"]["files"]),
              "chain_length": len(chain), "full_restoration_tested": True,
              "cli_smoke": {"command": [sys.executable, "-B", "-m", "autorouter", "--help"], "exit": smoke.returncode,
                            "output": smoke.stdout[:16000]}, "limitation": LIMITATION}
    verification = original.parent / ("verification-" + uuid.uuid4().hex + ".json")
    publish_check(verification, result, restored_stable)
    return verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", metavar="RECEIPT", help="Restore a complete existing full/incremental chain")
    mode.add_argument("--incremental", metavar="PARENT_RECEIPT", help="Changed/new artifact checkpoint from a verified full-base chain; no full restoration")
    args = parser.parse_args()
    try:
        receipt = Path(args.verify) if args.verify else create(parent=args.incremental)
        verified = checkpoint(receipt) if args.incremental else verify(receipt)
        print(json.dumps({"receipt": str(receipt), "integrity_check" if args.incremental else "verification": str(verified),
                          "full_restoration_tested": not bool(args.incremental), "limitation": LIMITATION}, indent=2))
        return 0
    except (BackupError, OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(json.dumps({"verified": False, "error": str(exc), "limitation": LIMITATION}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
