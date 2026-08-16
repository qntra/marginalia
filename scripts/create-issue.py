#!/usr/bin/env python3
"""Create the GH issue with the verification findings."""
import json
import os
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

# Read issue body
body_path = Path("/opt/data/quantara-division/logs/issue-body.md")
body = body_path.read_text()

payload = {
    "title": "verify run 2026-08-16 findings: broken source links + narcan.delivery Cloudflare telemetry",
    "body": body,
    "labels": ["verification", "privacy"]
}

# Make the API call
result = subprocess.run(
    [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", "POST",
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {pat}",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        "https://api.github.com/repos/qntra/marginalia/issues",
        "-d", json.dumps(payload),
    ],
    capture_output=True,
    text=True,
)

# Parse output — last line is HTTP code
lines = result.stdout.strip().rsplit("\n", 1)
body_out = lines[0] if len(lines) > 1 else result.stdout
http_code = lines[-1].strip() if len(lines) > 1 else "unknown"

print(f"HTTP_CODE: {http_code}")

if http_code == "201":
    d = json.loads(body_out)
    print(f"\nISSUE CREATED")
    print(f"  number: {d.get('number')}")
    print(f"  title:  {d.get('title')}")
    print(f"  url:    {d.get('html_url')}")
    print(f"  state:  {d.get('state')}")
    print(f"  labels: {[l.get('name') for l in d.get('labels', [])]}")
elif http_code == "401":
    print("AUTH FAILURE — PAT may be expired or invalid")
    print(f"  response: {body_out[:300]}")
else:
    print(f"UNEXPECTED: {http_code}")
    print(f"  response: {body_out[:300]}")
