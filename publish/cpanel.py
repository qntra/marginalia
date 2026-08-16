"""
thin cpanel uapi client. stdlib only, no deps, python 3.11+.

this host has shell access disabled and we can't turn it on ourselves, so
uapi over https is the only way in. auth is a token header:

    Authorization: cpanel <user>:<token>

docs, such as they are: https://api.docs.cpanel.net/cpanel/introduction/
"""

from __future__ import annotations

import json
import mimetypes
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class CPanelError(RuntimeError):
    """uapi said no."""


def load_config(env_path: Path | None = None) -> dict:
    """env vars win, .env fills the gaps. keeps the token out of argv and git."""
    cfg = {
        "host": "jarvis-us3.appliednetwork1.com",
        "port": "2083",
        "user": "quantara",
        "token": "",
        "remote_root": "/home/quantara/public_html",
        "site_url": "https://quantara.cv",
    }

    # CPANEL_API_TOKEN is the name cpanel itself uses, so accept it even though
    # the internal key is just "token"
    aliases = {"api_token": "token"}

    def normalize(raw: str) -> str:
        key = raw.strip().upper().removeprefix("CPANEL_").lower()
        return aliases.get(key, key)

    env_path = env_path or REPO_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            raw_key, _, val = line.partition("=")
            key = normalize(raw_key)
            val = val.strip().strip('"').strip("'")
            if key in cfg and val:
                cfg[key] = val

    for key in cfg:
        for env_name in (f"CPANEL_{key.upper()}", "CPANEL_API_TOKEN" if key == "token" else None):
            if env_name and (override := os.environ.get(env_name)):
                cfg[key] = override
                break

    if not cfg["token"]:
        raise CPanelError(
            "no api token. make one at cpanel > manage api tokens, then drop it in\n"
            f"  {REPO_ROOT / '.env'}\n"
            "as CPANEL_API_TOKEN=... (that file is gitignored)"
        )
    return cfg


class CPanel:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or load_config()
        self.base = f"https://{self.cfg['host']}:{self.cfg['port']}"
        self.remote_root = self.cfg["remote_root"].rstrip("/")
        # cert verification stays ON — the token rides this channel. if the
        # host ever breaks its chain, pin the cert; don't swap this for an
        # unverified context, no matter how tempting the one-liner is.
        self._ssl = ssl.create_default_context()

    # ---- plumbing -------------------------------------------------------

    def _auth_header(self) -> str:
        return f"cpanel {self.cfg['user']}:{self.cfg['token']}"

    def call(self, module: str, func: str, params: dict | None = None) -> dict:
        url = f"{self.base}/execute/{module}/{func}"
        if params:
            url += "?" + urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(url, headers={"Authorization": self._auth_header()})
        return self._send(req, f"{module}::{func}")

    def call_multipart(self, module: str, func: str, fields: dict, files: list[tuple[str, Path]]) -> dict:
        boundary = uuid.uuid4().hex
        body = self._encode_multipart(boundary, fields, files)
        req = urllib.request.Request(
            f"{self.base}/execute/{module}/{func}",
            data=body,
            headers={
                "Authorization": self._auth_header(),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )
        return self._send(req, f"{module}::{func}")

    def call_api2(self, module: str, func: str, params: dict | None = None) -> dict:
        """
        the old json-api. uapi is the front door for everything else, but it
        never got a Fileman::mkdir — asking for one just gets you "could not
        find the function". api2 still has it, so directories come through here.
        """
        query = {
            "cpanel_jsonapi_user": self.cfg["user"],
            "cpanel_jsonapi_module": module,
            "cpanel_jsonapi_func": func,
            "cpanel_jsonapi_apiversion": "2",
            **(params or {}),
        }
        url = f"{self.base}/json-api/cpanel?" + urllib.parse.urlencode(query, doseq=True)
        req = urllib.request.Request(url, headers={"Authorization": self._auth_header()})
        label = f"api2 {module}::{func}"

        result = self._fetch(req, label).get("cpanelresult") or {}
        if result.get("error"):
            raise CPanelError(f"{label} failed: {result['error']}")
        # api2 also likes to report failure quietly inside event
        event = result.get("event") or {}
        if event and not event.get("result"):
            raise CPanelError(f"{label} failed: {event.get('reason') or result}")
        return result

    def _fetch(self, req: urllib.request.Request, label: str) -> dict:
        """http + json, no opinion on the payload shape — uapi and api2 differ."""
        try:
            with urllib.request.urlopen(req, context=self._ssl, timeout=180) as resp:
                raw = resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:400].decode("utf-8", "replace")
            raise CPanelError(f"{label} -> http {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            # dns, refused connections, and ssl failures all land here
            raise CPanelError(f"{label} -> {exc.reason}") from exc
        except TimeoutError as exc:
            raise CPanelError(f"{label} -> timed out") from exc

        # an expired/bad token gets you the login page instead of json, which is
        # a genuinely awful failure mode to debug. call it out explicitly.
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            raise CPanelError(
                f"{label} returned html, not json — the token is probably wrong or revoked"
            ) from None

    def _send(self, req: urllib.request.Request, label: str) -> dict:
        payload = self._fetch(req, label)
        if not payload.get("status"):
            raise CPanelError(f"{label} failed: {payload.get('errors') or payload}")
        return payload

    @staticmethod
    def _encode_multipart(boundary: str, fields: dict, files: list[tuple[str, Path]]) -> bytes:
        out = bytearray()
        for name, value in fields.items():
            out += f"--{boundary}\r\n".encode()
            out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            out += f"{value}\r\n".encode()
        for name, path in files:
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            # a quote or newline in a filename would splice into the headers.
            # shouldn't happen with repo files, but escaping is one line
            fname = path.name.replace("\\", "\\\\").replace('"', '\\"')
            if "\r" in fname or "\n" in fname:
                raise CPanelError(f"filename has a newline in it somehow: {path.name!r}")
            out += f"--{boundary}\r\n".encode()
            out += (
                f'Content-Disposition: form-data; name="{name}"; filename="{fname}"\r\n'
            ).encode()
            out += f"Content-Type: {ctype}\r\n\r\n".encode()
            out += path.read_bytes()
            out += b"\r\n"
        out += f"--{boundary}--\r\n".encode()
        return bytes(out)

    # ---- the handful of calls we actually use ---------------------------

    def remote_path(self, rel: str = "") -> str:
        rel = rel.replace("\\", "/").strip("/")
        # every caller should stay inside public_html; a stray ".." plus
        # --allow-delete is how docroots get emptied
        if ".." in rel.split("/"):
            raise CPanelError(f"path escapes the docroot: {rel!r}")
        return f"{self.remote_root}/{rel}" if rel else self.remote_root

    def list_files(self, rel_dir: str = "") -> list[dict]:
        res = self.call(
            "Fileman",
            "list_files",
            {"dir": self.remote_path(rel_dir), "types": "file|dir|symlink", "show_hidden": 1},
        )
        return res.get("data") or []

    def walk(self, rel_dir: str = "") -> list[str]:
        """every file under rel_dir, as repo-relative posix paths. hidden ones too."""
        found: list[str] = []
        for entry in self.list_files(rel_dir):
            name = entry.get("file")
            if not name or name in (".", ".."):
                continue
            child = f"{rel_dir}/{name}".strip("/")
            if entry.get("type") == "dir":
                found.extend(self.walk(child))
            else:
                found.append(child)
        return found

    def mkdir(self, rel_dir: str) -> None:
        """
        make each level in turn; already-exists is fine, anything else isn't.
        the "exist" sniff is matching english error text — api2 has no error
        codes and cpanel localizes its messages, so this quietly assumes the
        account locale stays english. it always has, but you were warned.
        """
        parts = [p for p in rel_dir.replace("\\", "/").split("/") if p]
        for i, part in enumerate(parts):
            parent = self.remote_path("/".join(parts[:i]))
            try:
                self.call_api2("Fileman", "mkdir", {"path": parent, "name": part})
            except CPanelError as exc:
                if "exist" not in str(exc).lower():
                    raise

    def trash(self, rel_path: str) -> None:
        """
        move a remote path into .trash. uapi has no delete of any spelling —
        Fileman::trash, trash_files and delete_files all come back "could not
        find the function" — so this goes through api2 fileop, same as mkdir.
        """
        self.call_api2(
            "Fileman",
            "fileop",
            {"op": "trash", "sourcefiles": self.remote_path(rel_path), "doubledecode": 0},
        )

    def upload(self, local: Path, rel_dir: str) -> None:
        self.call_multipart(
            "Fileman",
            "upload_files",
            {"dir": self.remote_path(rel_dir), "overwrite": "1"},
            [("file-1", local)],
        )

    def get_file(self, rel_path: str) -> str:
        rel = rel_path.replace("\\", "/")
        parent, _, name = rel.rpartition("/")
        res = self.call("Fileman", "get_file_content", {"dir": self.remote_path(parent), "file": name})
        content = (res.get("data") or {}).get("content")
        if content is None:
            # pull.py writes this straight into backup/ — defaulting to ""
            # here would turn an api hiccup into a silently empty backup file
            raise CPanelError(f"get_file_content came back with no content for {rel}")
        return content

    def clear_nginx_cache(self) -> bool:
        """
        nginx user caching is ON for this account, so a deploy without a purge
        looks like it silently did nothing. best-effort — push.py verifies the
        live bytes anyway, so a failure here is a warning not a death sentence.
        """
        for module, func in (("NginxCaching", "clear_cache"), ("Nginx", "clear_cache")):
            try:
                self.call(module, func)
                return True
            except CPanelError:
                continue
        return False
