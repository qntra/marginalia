#!/usr/bin/env python3
"""
uploads _site/ to marginalia.quantara.cv and then checks the live bytes.

the host is a cpanel box with shell access disabled, so uapi over https is
the only door -- same story as quantara.cv itself. nginx user caching is on,
which means an upload that "worked" can still serve yesterday's page, so a
deploy isn't finished until the url comes back with what we sent.

usage:
    python publish/deploy.py --dry-run
    python publish/deploy.py
"""

from __future__ import annotations

import argparse
import hashlib
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cpanel import CPanel, CPanelError, load_config  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "_site"
DOCROOT = "/home/quantara/public_html/marginalia.quantara.cv"
SITE_URL = "https://marginalia.quantara.cv"

# cpanel owns these. it regenerates them, they are marked do-not-edit, and
# pruning them would break php on the vhost. never in the build, never removed.
PROTECTED = {".htaccess", ".user.ini", "php.ini", "cgi-bin", ".well-known", ".trash"}

TEXTY = {".html", ".xml", ".txt", ".md", ".svg", ".css", ".js", ".json", ".log"}


def local_files() -> dict[str, Path]:
    if not OUT.is_dir():
        raise SystemExit("no _site/ -- run `python publish/build.py` first")
    return {
        p.relative_to(OUT).as_posix(): p
        for p in sorted(OUT.rglob("*"))
        if p.is_file()
    }


def protected(rel: str) -> bool:
    return rel.split("/", 1)[0] in PROTECTED


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
    a freshly created subdomain is live on the host long before every resolver
    has heard about it -- and a machine that already cached the NXDOMAIN can
    stay blind for a while. that's a dns problem wearing a deploy problem's
    coat, so check it once up front instead of printing 15 bogus failures.
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="say what would happen, touch nothing")
    ap.add_argument("--no-prune", action="store_true", help="leave remote files the build no longer produces")
    args = ap.parse_args()

    files = local_files()
    print(f"{len(files)} files in _site/")

    cfg = load_config()
    cfg["remote_root"] = DOCROOT
    cp = CPanel(cfg)

    try:
        remote = [r for r in cp.walk() if not protected(r)]
    except CPanelError as exc:
        print(f"could not list the docroot: {exc}", file=sys.stderr)
        return 1
    stale = sorted(set(remote) - set(files))

    if args.dry_run:
        for rel in sorted(files):
            print(f"  upload  {rel}")
        for rel in stale:
            print(f"  trash   {rel}")
        print("dry run -- nothing sent")
        return 0

    def parent_of(rel: str) -> str:
        p = Path(rel).parent.as_posix()
        return "" if p == "." else p

    # directories first, so an upload never lands in a folder that isn't there
    for d in sorted({parent_of(rel) for rel in files} - {""}):
        cp.mkdir(d)

    sent = 0
    for rel, path in files.items():
        cp.upload(path, parent_of(rel))
        sent += 1
        print(f"  sent  {rel}")

    if stale and not args.no_prune:
        for rel in stale:
            try:
                cp.trash(rel)
                print(f"  trashed  {rel}")
            except CPanelError as exc:
                print(f"  ! could not trash {rel}: {exc}")

    print("purging nginx cache..." if cp.clear_nginx_cache() else "nginx purge unavailable (continuing)")

    host = SITE_URL.split("://", 1)[1]
    if not resolves(host):
        print(
            f"\nuploaded {sent}, but {host} doesn't resolve from here yet, so there's\n"
            "nothing to verify against. the files are on the server -- this is dns\n"
            "catching up (or a stale NXDOMAIN cached locally). re-run once it resolves.",
            file=sys.stderr,
        )
        return 2

    # verify. text files get a byte comparison; binaries just have to exist.
    checks = [r for r in files if Path(r).suffix.lower() in TEXTY]
    bad = []
    for rel in checks:
        want = files[rel].read_bytes()
        url = url_for(rel)
        for attempt in range(4):
            got, why = fetch(url)
            if got is not None and got.strip() == want.strip():
                break
            time.sleep(1.5 * (attempt + 1))
            if attempt == 1:
                cp.clear_nginx_cache()
        else:
            got_h = hashlib.sha256(got).hexdigest()[:12] if got else (why or "no response")
            bad.append(f"{url}  (want {hashlib.sha256(want).hexdigest()[:12]}, got {got_h})")

    print(f"\nuploaded {sent}, verified {len(checks) - len(bad)}/{len(checks)}")
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
