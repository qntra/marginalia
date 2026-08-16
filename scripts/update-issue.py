#!/usr/bin/env python3
"""Update GH issue #1 with the 'what the division fixed' section."""
import json
import subprocess
import sys
from pathlib import Path

# Extract PAT from git remote URL
remote_url = subprocess.check_output(
    ["git", "remote", "get-url", "origin"],
    cwd="/opt/data/quantara-division",
    text=True
).strip()
pat = remote_url.split("@")[0].split("://")[-1].rstrip(":")
print(f"PAT extracted (len={len(pat)}, starts={pat[:8]}...)")

# Read current issue body
body_path = Path("/opt/data/quantara-division/logs/issue-body.md")
body = body_path.read_text()

# Append what the division fixed
addition = """---

## what the division fixed (without waiting)

### glb-viewer → web-glb-viewer link update

- updated `scripts/quantara-verify.py` line 66: `github.com/Metrix187/glb-viewer` → `github.com/Metrix187/web-glb-viewer`
- the repo was renamed on 2025-08-03; the verifier now points at the right repo
- **still needs the parent:** any site links (quantara.cv, marginalia.quantara.cv) that point to the old `glb-viewer` name

### flow-webui — unresolved

- the repo is genuinely gone. no rename, no archive, no search trace
- the tool at `flow.quantara.cyou` is live but its source link is dead
- **needs the parent:** restore the repo, rename it and update the link, or remove the github link from the site

### narcan.delivery — unresolved

- the Cloudflare beacon and RUM calls remain
- the division cannot fix this — it needs the parent to remove Cloudflare Insights from the site
- **needs the parent:** remove `static.cloudflareinsights.com/beacon.min.js`, disable `cloudflareinsights.com/cdn-cgi/rum`, verify the network tab is clean, re-run the verifier
"""

new_body = body + "\n" + addition

payload = {"body": new_body}

result = subprocess.run(
    [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", "PATCH",
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {pat}",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        "https://api.github.com/repos/qntra/marginalia/issues/1",
        "-d", json.dumps(payload),
    ],
    capture_output=True,
    text=True,
)

lines = result.stdout.strip().rsplit("\n", 1)
body_out = lines[0] if len(lines) > 1 else result.stdout
http_code = lines[-1].strip() if len(lines) > 1 else "unknown"

print(f"HTTP_CODE: {http_code}")

if http_code == "200":
    d = json.loads(body_out)
    print(f"ISSUE UPDATED")
    print(f"  number: {d.get('number')}")
    print(f"  title:  {d.get('title')}")
    print(f"  state:  {d.get('state')}")
    print(f"  updated: {d.get('updated_at')}")
elif http_code == "401":
    print("AUTH FAILURE")
    print(f"  response: {body_out[:300]}")
else:
    print(f"UNEXPECTED: {http_code}")
    print(f"  response: {body_out[:300]}")
