#!/usr/bin/env python3
"""Build a patched archive from a supported T3 Code installation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import struct
import subprocess
import sys
import tempfile

import patch_frontend


ASSETS = "apps/server/dist/client/assets/"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_archive(raw):
    _, header_size, _, json_size = struct.unpack_from("<4I", raw)
    header_bytes = raw[16:16 + json_size]
    return json.loads(header_bytes), 8 + header_size, sha(header_bytes)


def packed_files(header, prefix=""):
    for key, value in header["files"].items():
        name = prefix + key
        if "files" in value:
            yield from packed_files(value, name + "/")
        elif "offset" in value and not value.get("unpacked"):
            yield name, value


def blob(raw, base, entry):
    offset = base + int(entry["offset"])
    return memoryview(raw)[offset:offset + entry["size"]]


def patch_archive(raw):
    header, base, _ = read_archive(raw)
    entries = dict(packed_files(header))
    candidates = []
    for name, entry in entries.items():
        if name.startswith(ASSETS) and name.endswith(".js"):
            source = bytes(blob(raw, base, entry)).decode("utf-8")
            if patch_frontend.is_target(source) or patch_frontend.is_patched(source):
                candidates.append((name, source))
    if len(candidates) != 1:
        raise ValueError("Unrecognized citation editor. Use a supported T3 Code build.")
    name, source = candidates[0]
    if patch_frontend.is_patched(source):
        raise ValueError("The input is already patched. Use the original archive.")
    replacement = patch_frontend.patch(source).encode("utf-8")
    entry = entries[name]
    offset, size = int(entry["offset"]), entry["size"]
    delta = len(replacement) - size
    for other in entries.values():
        if int(other["offset"]) > offset:
            other["offset"] = str(int(other["offset"]) + delta)
    entry["size"] = len(replacement)
    integrity = entry["integrity"]
    block_size = integrity["blockSize"]
    integrity["hash"] = sha(replacement)
    integrity["blocks"] = [sha(replacement[i:i + block_size])
                           for i in range(0, len(replacement), block_size)]
    header_bytes = json.dumps(header, separators=(",", ":"), ensure_ascii=False).encode()
    padding = (-len(header_bytes)) % 4
    payload_size = 4 + len(header_bytes) + padding
    result = b"".join((
        struct.pack("<4I", 4, payload_size + 4, payload_size, len(header_bytes)),
        header_bytes, bytes(padding), memoryview(raw)[base:base + offset], replacement,
        memoryview(raw)[base + offset + size:],
    ))

    old_header, _, _ = read_archive(raw)
    new_header, new_base, digest = read_archive(result)
    new_entries = dict(packed_files(new_header))
    for path, original in packed_files(old_header):
        expected = replacement if path == name else blob(raw, base, original)
        if blob(result, new_base, new_entries[path]) != expected:
            raise ValueError(f"Archive verification failed for {path}")
    return result, digest


def stage_archive(source, output):
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    patched, _ = patch_archive(source.read_bytes())
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
        temporary.write(patched)
    staged = Path(temporary.name)
    # Keep the original permissions so other users can still read the archive.
    os.chmod(staged, source.stat().st_mode & 0o777)
    try:
        os.link(staged, output)
    finally:
        staged.unlink()
    print(f"Staged {output} (SHA-256 {sha(patched)})")


def mac_copy(source, output, identity):
    if sys.platform != "darwin":
        raise ValueError("Building a macOS app copy requires macOS.")
    if output.exists() or output.suffix != ".app":
        raise ValueError("Choose a fresh output path ending in .app.")

    archive_path = Path("Contents/Resources/app.asar")
    plist_path = Path("Contents/Info.plist")
    info = plistlib.loads((source / plist_path).read_bytes())
    raw = (source / archive_path).read_bytes()
    integrity = info["ElectronAsarIntegrity"]["Resources/app.asar"]
    if integrity["hash"] != read_archive(raw)[2]:
        raise ValueError("Input app archive failed integrity verification.")
    patched, integrity["hash"] = patch_archive(raw)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        staged = Path(scratch) / output.name
        subprocess.run(["ditto", str(source), str(staged)], check=True)
        (staged / archive_path).write_bytes(patched)
        (staged / plist_path).write_bytes(plistlib.dumps(info, fmt=plistlib.FMT_BINARY))
        # Sign the modified outer bundle. Keep the bundled helper signatures.
        subprocess.run(["codesign", "--force", "--sign", identity, "--timestamp=none",
                        str(staged)], check=True)
        subprocess.run(["codesign", "--verify", "--deep", "--strict", str(staged)], check=True)
        staged.rename(output)
    print(f"Staged {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    archive = actions.add_parser("archive", help="stage a separate archive (Windows server.asar, Linux app.asar)")
    archive.add_argument("source", type=Path)
    archive.add_argument("output", type=Path)
    mac = actions.add_parser("mac", help="stage a separate signed macOS app")
    mac.add_argument("source", type=Path)
    mac.add_argument("output", type=Path)
    mac.add_argument("--identity", default="-", help="local codesign identity (default: ad hoc)")
    args = parser.parse_args()
    try:
        if args.action == "mac":
            mac_copy(args.source, args.output, args.identity)
        else:
            stage_archive(args.source, args.output)
    except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Build failed: {error}\n")


if __name__ == "__main__":
    main()
