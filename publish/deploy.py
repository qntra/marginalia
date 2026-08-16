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


def remote_dirs(cp: CPanel, rel: str = "") -> list[str]:
    """every directory under the docroot, repo-relative. cp.walk() only does files."""
    out = []
    for entry in cp.list_files(rel):
        name = entry.get("file")
        if not name or name in (".", "..") or entry.get("type") != "dir":
            continue
        child = f"{rel}/{name}".strip("/")
        if protected(child):
            continue
        out.append(child)
        out.extend(remote_dirs(cp, child))
    return out


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
        # this box drops a connection now and then, usually mid-run when we're
        # pushing a lot of small files at it. one flaky socket shouldn't strand
        # the docroot half-updated, so give each file a couple of swings.
        for attempt in range(3):
            try:
                cp.upload(path, parent_of(rel))
                break
            except CPanelError as exc:
                if attempt == 2:
                    print(f"  ! gave up on {rel}: {exc}", file=sys.stderr)
                    return 1
                print(f"  retrying {rel} ({exc})")
                time.sleep(2 * (attempt + 1))
        sent += 1
        print(f"  sent  {rel}")

    if not args.no_prune:
        for rel in stale:
            try:
                cp.trash(rel)
                print(f"  trashed  {rel}")
            except CPanelError as exc:
                print(f"  ! could not trash {rel}: {exc}")

        # an emptied directory is worse than a leftover file: apache has
        # autoindex on, so /notes/deleted-thing/ keeps answering 200 with a
        # bare file listing instead of going away. take the folders too.
        wanted_dirs = set()
        for rel in files:
            parts = Path(rel).parent.parts
            wanted_dirs |= {"/".join(parts[: i + 1]) for i in range(len(parts))}
        wanted_dirs -= {"", "."}
        for d in sorted(remote_dirs(cp), key=len, reverse=True):
            if protected(d) or d in wanted_dirs:
                continue
            try:
                cp.trash(d)
                print(f"  trashed  {d}/")
            except CPanelError as exc:
                print(f"  ! could not trash {d}/: {exc}")

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
