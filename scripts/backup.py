#!/usr/bin/env python3
"""Private on-Mac backup and restoration check; never deletes an earlier backup."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import uuid
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SCOPES = (".runs", ".data", ".local-reference")
LIMIT = 1024 ** 3
MAX_FILES = 100000
LIMITATION = "On-Mac only; a second folder on this disk provides no disk-failure protection."
SECRET_NAMES = {".env", ".ssh", ".aws", ".gnupg", "credentials", "credentials.json", "secrets", "secrets.json", "id_rsa", "id_ed25519"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".keychain", ".keychain-db"}


# This exact public unit-test source contains only a synthetic PEM header used
# to exercise this guard. Fresh-install copies are archived byte-for-byte.
# Any content change or different path still fails. Reviewed at dd2cce9.
NONSECRET_TEST_SOURCE = "6d010b7d95db21e6921d9c2af9647e29a33725bdc835d03136928648e69d63ee"
AUDITED_DRAFT_TEST_SOURCES = {
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
                    raise BackupError("Non-Git snapshot exceeds the 1 GiB/file-count ceiling")
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
            raise BackupError("Compressed archive exceeds 1 GiB ceiling")
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


def restore_archive(archive, destination, manifest):
    """Whitelist archive members before writing; never use extractall."""
    if destination.exists() or destination.is_symlink():
        raise BackupError("Refusing restore destination collision")
    files, dirs = check_manifest(manifest)
    if archive.stat().st_size > LIMIT:
        raise BackupError("Archive exceeds compressed-size limit")
    seen = set()
    with tarfile.open(archive, "r|gz") as source:
        for item in source:
            name = item.name.rstrip("/") if item.isdir() else item.name
            validate_name(name)
            if name in seen or not (item.isdir() or item.isreg()):
                raise BackupError("Duplicate, linked, or special archive member")
            seen.add(name)
            if item.isdir():
                if name not in dirs or item.size:
                    raise BackupError("Unexpected archive directory")
            elif name not in files or item.size != files[name]["size"]:
                raise BackupError("Unexpected archive file or size")
    if seen != set(files) | dirs:
        raise BackupError("Archive does not exactly match inventory")
    destination.mkdir(mode=0o700)
    for name in sorted(dirs, key=lambda x: (len(PurePosixPath(x).parts), x)):
        (destination / name).mkdir(mode=0o700)
    with tarfile.open(archive, "r|gz") as source:
        for item in source:
            if not item.isreg():
                continue
            target = destination / item.name
            with source.extractfile(item) as payload, target.open("xb") as output:
                os.chmod(target, 0o600)
                while True:
                    chunk = payload.read(1024 * 1024)
                    if not chunk:
                        break
                    output.write(chunk)
            if digest(target) != files[item.name]["sha256"]:
                raise BackupError("Restored non-Git file hash mismatch")


def create(root=ROOT):
    root = Path(root).resolve()
    if Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise BackupError("Run only in the selected Git checkout")
    if git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise BackupError("Commit/audit safe source first; backup refuses uncommitted or untracked nonignored files")
    head = git(root, "rev-parse", "HEAD")
    refs = git(root, "show-ref")
    manifest = inventory(root)
    base = backups_directory(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = base / ("checkpoint-" + stamp + "-" + uuid.uuid4().hex)
    backup.mkdir(mode=0o700)  # Exclusive; earlier artifacts are never overwritten.
    bundle = backup / "repository.bundle"
    git(root, "bundle", "create", str(bundle), "--all")
    os.chmod(bundle, 0o600)
    if bundle.stat().st_size > LIMIT:
        raise BackupError("Git bundle exceeds 1 GiB ceiling; retained for review")
    git(root, "bundle", "verify", str(bundle))
    archive = backup / "non-git.tar.gz"
    make_archive(root, archive, manifest)
    if manifest != inventory(root) or head != git(root, "rev-parse", "HEAD") or refs != git(root, "show-ref") or git(root, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise BackupError("Source changed during snapshot; partial backup retained but not certified")
    receipt = {"schema": 1, "created_utc": stamp, "source_root": str(root), "git_head": head,
               "git_refs": refs.splitlines(), "inventory": manifest, "limitation": LIMITATION,
               "excluded": [".tools", "credentials", "other ignored directories"],
               "bundle": {"name": bundle.name, "sha256": digest(bundle), "size": bundle.stat().st_size},
               "archive": {"name": archive.name, "sha256": digest(archive), "size": archive.stat().st_size}}
    path = backup / "receipt.json"
    exclusive_json(path, receipt)
    return path


def verify(receipt_path, root=ROOT):
    root = Path(root).resolve()
    base = backups_directory(root)
    original = Path(receipt_path).absolute()
    if original.is_symlink() or original.parent.is_symlink() or original.resolve().parent.parent != base.resolve() or original.name != "receipt.json":
        raise BackupError("Receipt must be a regular receipt.json directly inside a local backup")
    receipt = json.loads(original.read_text())
    if receipt.get("schema") != 1 or not re.fullmatch(r"[0-9a-f]{40,64}", receipt.get("git_head", "")):
        raise BackupError("Unsupported or malformed backup receipt")
    artifacts = {}
    for kind, name in (("bundle", "repository.bundle"), ("archive", "non-git.tar.gz")):
        path, entry = original.parent / name, receipt[kind]
        if entry["name"] != name or path.is_symlink() or not path.is_file() or path.stat().st_size != entry["size"] or path.stat().st_size > LIMIT or digest(path) != entry["sha256"]:
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
    restore_archive(artifacts["archive"], restore / "non-git", receipt["inventory"])
    smoke = subprocess.run([sys.executable, "-m", "autorouter", "--help"], cwd=checkout,
                           capture_output=True, text=True, timeout=20,
                           env={k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")})
    if smoke.returncode != 0 or "usage:" not in smoke.stdout.lower():
        raise BackupError("Restored CLI --help smoke failed: " + smoke.stderr[-2000:])
    result = {"schema": 1, "verified": True, "receipt": str(original),
              "receipt_sha256": digest(original), "restored_git_head": receipt["git_head"],
              "restore_directory": str(restore), "git_bundle_verified_in_empty_repository": True,
              "all_refs_restored": True, "non_git_files_verified": len(receipt["inventory"]["files"]),
              "cli_smoke": {"command": [sys.executable, "-m", "autorouter", "--help"], "exit": smoke.returncode,
                            "output": smoke.stdout[:16000]}, "limitation": LIMITATION}
    verification = original.parent / ("verification-" + uuid.uuid4().hex + ".json")
    exclusive_json(verification, result)
    return verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", metavar="RECEIPT", help="Recheck an existing receipt in .local-backups")
    args = parser.parse_args()
    try:
        receipt = Path(args.verify) if args.verify else create()
        verified = verify(receipt)
        print(json.dumps({"receipt": str(receipt), "verification": str(verified), "limitation": LIMITATION}, indent=2))
        return 0
    except (BackupError, OSError, ValueError, KeyError, TypeError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(json.dumps({"verified": False, "error": str(exc), "limitation": LIMITATION}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
