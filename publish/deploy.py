#!/usr/bin/env python3
"""
rsyncs _site/ to marginalia.quantara.cv and then checks the live bytes.

the site lives on quantara-nood now (caddy, behind cloudflare). the old cpanel
box died on 2026-10-01 and took the uapi with it. the ci key logs in as
`marginalia-deploy`, and the server pins that key to rrsync inside the
docroot, so all it can do is rsync into /var/www/marginalia.quantara.cv. no
shell, nothing else on the box.

a deploy still isn't finished until the url comes back with what we sent.
cloudflare edge-caches the static extensions, so verification goes through a
cache-busting query string.

usage:
    python publish/deploy.py --dry-run
    python publish/deploy.py

needs `rsync` and an ssh host alias (default `marginalia-origin`, override with
MARGINALIA_SSH_HOST). the workflow sets that alias up from repo secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "_site"
SITE_URL = "https://marginalia.quantara.cv"
SSH_HOST = os.environ.get("MARGINALIA_SSH_HOST", "marginalia-origin")

TEXTY = {".html", ".xml", ".txt", ".md", ".svg", ".css", ".js", ".json", ".log"}


def local_files() -> dict[str, Path]:
    if not OUT.is_dir():
        raise SystemExit("no _site/ -- run `python publish/build.py` first")
    return {
        p.relative_to(OUT).as_posix(): p
        for p in sorted(OUT.rglob("*"))
        if p.is_file()
    }


def fetch(url: str, timeout: int = 30) -> tuple[bytes | None, str]:
    """returns (body, why-it-failed). the reason matters -- see resolves() below."""
    req = urllib.request.Request(url, headers={"User-Agent": "marginalia-deploy", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read(), ""
    except urllib.error.HTTPError as exc:
        return None, f"http {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, str(getattr(exc, "reason", exc))[:80]


def resolves(host: str) -> bool:
    """
    a dns change can be live at cloudflare long before every resolver has
    heard about it. that's a dns problem wearing a deploy problem's coat, so
    check it once up front instead of printing 15 bogus failures.
    """
    try:
        socket.getaddrinfo(host, 443)
        return True
    except socket.gaierror:
        return False


def url_for(rel: str) -> str:
    # /notes/foo/index.html is served at /notes/foo/
    if rel == "index.html":
        return f"{SITE_URL}/"
    if rel.endswith("/index.html"):
        return f"{SITE_URL}/{rel[: -len('index.html')]}"
    return f"{SITE_URL}/{rel}"


def rsync(dry_run: bool, prune: bool) -> int:
    if not shutil.which("rsync"):
        print("no rsync on PATH. this runs in ci; locally, use the workflow", file=sys.stderr)
        return 1
    cmd = [
        "rsync", "-rlc", "--itemize-changes",
        # caddy reads as its own user, so everything has to be world-readable
        "--chmod=D755,F644",
        "-e", "ssh -o BatchMode=yes -o ConnectTimeout=20",
    ]
    if prune:
        # takes emptied folders with it too, so a deleted post 404s instead of lingering
        cmd.append("--delete-after")
    if dry_run:
        cmd.append("--dry-run")
    # rrsync roots the path at the docroot, so "/" here *is* the docroot
    cmd += [f"{OUT.as_posix()}/", f"{SSH_HOST}:/"]
    return subprocess.run(cmd).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="say what would happen, touch nothing")
    ap.add_argument("--no-prune", action="store_true", help="leave remote files the build no longer produces")
    args = ap.parse_args()

    files = local_files()
    print(f"{len(files)} files in _site/")

    # the box drops a connection now and then. one flaky socket shouldn't fail
    # the run, and rsync picks up where it left off, so just swing again
    for attempt in range(3):
        rc = rsync(args.dry_run, prune=not args.no_prune)
        if rc == 0:
            break
        print(f"  rsync exited {rc}, retrying", file=sys.stderr)
        time.sleep(3 * (attempt + 1))
    else:
        print("rsync kept failing -- treat this as a failed deploy.", file=sys.stderr)
        return 1

    if args.dry_run:
        print("dry run -- nothing sent")
        return 0

    host = SITE_URL.split("://", 1)[1]
    if not resolves(host):
        print(
            f"\nsynced, but {host} doesn't resolve from here yet, so there's\n"
            "nothing to verify against. re-run once dns catches up.",
            file=sys.stderr,
        )
        return 2

    # verify. text files get a byte comparison; binaries just have to exist.
    checks = [r for r in files if Path(r).suffix.lower() in TEXTY]
    bad = []
    for rel in checks:
        want = files[rel].read_bytes()
        url = f"{url_for(rel)}?v={hashlib.sha256(want).hexdigest()[:12]}"
        for attempt in range(4):
            got, why = fetch(url)
            if got is not None and got.strip() == want.strip():
                break
            time.sleep(1.5 * (attempt + 1))
        else:
            got_h = hashlib.sha256(got).hexdigest()[:12] if got else (why or "no response")
            bad.append(f"{url}  (want {hashlib.sha256(want).hexdigest()[:12]}, got {got_h})")

    print(f"\nverified {len(checks) - len(bad)}/{len(checks)}")
    if bad:
        print("\nthese urls did not come back with what we sent:", file=sys.stderr)
        for line in bad:
            print(f"  {line}", file=sys.stderr)
        print("\ntreat this as a failed deploy, not a warning.", file=sys.stderr)
        return 1

    print(f"live: {SITE_URL}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
