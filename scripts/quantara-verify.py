#!/usr/bin/env python3
"""
quantara-tools verifier — the division watches the parent.

opens each quantara.cv tool in a real browser and checks the privacy claims:
  1. page loads without errors
  2. no unexpected network requests after load (telemetry, tracking, beacons)
  3. no third-party analytics scripts
  4. for local-first tools: inference happens client-side (no API calls for prompts)
  5. source is public (github link present and reachable)

this is not a test suite. it is a privacy audit the division runs on a schedule,
because "we respect your privacy" is what surveillance companies say — the
division prefers to watch the network tab.

usage:
  python scripts/quantara-verify.py            # run all checks, print report
  python scripts/quantara-verify.py --json     # machine-readable output
  python scripts/quantara-verify.py --tool flow # check one tool only

requirements: playwright (chromium installed), requests (for github link check)
"""

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    sys.exit("playwright not installed: /opt/data/.venv/bin/pip install playwright")

# ── tools to verify ──────────────────────────────────────────────────────────
# each entry: url, and which checks apply.
# checks: network (no telemetry), client_side (inference local), source (github link)

@dataclass
class Tool:
    name: str
    url: str
    github: Optional[str] = None
    check_network: bool = True      # look for telemetry beacons
    check_client_side: bool = False  # verify no prompt leaves the machine
    check_source: bool = True       # verify github link reachable
    notes: str = ""

TOOLS = [
    Tool(
        name="flow (local inference)",
        url="https://flow.quantara.cyou/",
        github="https://github.com/Metrix187/flow-webui",
        check_network=True,
        check_client_side=True,  # THE key claim: prompts stay on-device
        check_source=True,
        notes="the strongest privacy claim — local inference. prompts must not leave the machine.",
    ),
    Tool(
        name="3d viewer (client-side)",
        url="https://3d.quantara.cyou/",
        github="https://github.com/Metrix187/glb-viewer",
        check_network=True,
        check_client_side=True,  # files should not upload anywhere
        check_source=True,
        notes="3d files viewed in-browser. the glb should never upload to a server.",
    ),
    Tool(
        name="base64→glb converter",
        url="https://base64.quantara.cv/",
        github="https://github.com/Metrix187/base64-to-glb",
        check_network=True,
        check_client_side=True,
        check_source=True,
        notes="format conversion, offline-capable.",
    ),
    Tool(
        name="narcan.delivery",
        url="https://narcan.delivery/",
        github=None,  # not listed with a github link on the site
        check_network=True,
        check_client_side=False,
        check_source=False,
        notes="finds naloxone nearby, then forgets. sensitive query — must not log.",
    ),
]

# known-safe third-party origins (CDNs, fonts) that are NOT telemetry
ALLOWED_ORIGINS = {
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
}

# telemetry / tracking patterns to flag
TELEMETRY_PATTERNS = [
    r"google-analytics\.com",
    r"googletagmanager\.com",
    r"facebook\.com/tr",
    r"analytics",
    r"telemetry",
    r"tracking",
    r"segment\.com",
    r"mixpanel\.com",
    r"hotjar\.com",
    r"plausible\.io",
    r"fathom\.com",
    r"pixel",
    r"beacon",
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    evidence: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class ToolReport:
    tool: str
    url: str
    loads: bool
    load_error: Optional[str] = None
    checks: list = field(default_factory=list)
    network_requests: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    verdict: str = "unknown"  # pass / warn / fail

    def to_dict(self):
        r = asdict(self)
        r["checks"] = [c.to_dict() for c in self.checks]
        return r


def launch_browser():
    """launch chromium with no-sandbox (container) flags."""
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    )
    return p, browser


def check_page_loads(browser, url: str, timeout_ms: int = 15000) -> tuple[bool, list, Optional[str], list]:
    """open the page, collect all network requests, return (ok, requests, error, warnings)."""
    ctx = browser.new_context()
    page = ctx.new_page()
    requests = []
    errors = []

    def on_request(r):
        requests.append({
            "url": r.url,
            "method": r.method,
            "resource_type": r.resource_type,
        })

    def on_console(msg):
        if msg.type == "error":
            errors.append(msg.text)

    page.on("request", on_request)
    page.on("console", on_console)

    try:
        page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        # give telemetry beacons a moment to fire
        page.wait_for_timeout(2000)
    except PWTimeout:
        ctx.close()
        return False, requests, "page load timed out", errors
    except Exception as e:
        ctx.close()
        return False, requests, str(e), errors

    ctx.close()
    return True, requests, None, errors


def flag_telemetry(requests: list) -> list:
    """return requests that look like telemetry."""
    flagged = []
    for r in requests:
        url = r["url"]
        # skip same-origin (the tool's own assets)
        if re.match(r"https?://(www\.)?quantara\.(cYOU|cv)", url):
            continue
        if re.match(r"https?://narcan\.delivery", url):
            continue
        # skip known-safe origins
        if any(o in url for o in ALLOWED_ORIGINS):
            continue
        # check telemetry patterns
        for pat in TELEMETRY_PATTERNS:
            if re.search(pat, url, re.I):
                flagged.append({"url": url, "reason": f"matches '{pat}'"})
                break
        else:
            # not telemetry, but still a third-party request — warn
            if r["resource_type"] in ("xhr", "fetch", "websocket"):
                flagged.append({"url": url, "reason": f"3rd-party {r['resource_type'].upper()} (not obviously telemetry)"})

    return flagged


def check_github_reachable(github_url: str) -> bool:
    """quick HEAD request to confirm the repo is public."""
    import urllib.request
    req = urllib.request.Request(github_url, method="HEAD",
                                headers={"User-Agent": "marginalia-verify"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200
    except Exception:
        return False


def verify_tool(browser, tool: Tool) -> ToolReport:
    """run all applicable checks on one tool."""
    report = ToolReport(tool=tool.name, url=tool.url, loads=False)

    # 1. load the page
    ok, requests, error, console_errors = check_page_loads(browser, tool.url)
    report.loads = ok
    report.load_error = error
    report.network_requests = [r["url"] for r in requests]

    if not ok:
        report.verdict = "fail"
        report.warnings.append(f"page did not load: {error}")
        return report

    # 2. telemetry check
    if tool.check_network:
        flagged = flag_telemetry(requests)
        report.checks.append(CheckResult(
            name="no_telemetry",
            passed=len(flagged) == 0,
            detail=f"{len(flagged)} telemetry-like requests flagged" if flagged else "no telemetry beacons detected",
            evidence=[f["url"] for f in flagged],
        ))

    # 3. client-side inference check (for flow/3d/base64)
    if tool.check_client_side:
        # heuristic: any XHR/fetch to an external origin with a large body could be
        # a prompt upload. flag them.
        outbound_calls = []
        for r in requests:
            if r["resource_type"] in ("xhr", "fetch"):
                # skip same-origin and allowed
                if any(a in r["url"] for a in ALLOWED_ORIGINS):
                    continue
                if "quantara" in r["url"]:
                    continue
                outbound_calls.append(r["url"])
        report.checks.append(CheckResult(
            name="client_side_only",
            passed=len(outbound_calls) == 0,
            detail=f"{len(outbound_calls)} outbound data calls during load" if outbound_calls else "no outbound data calls — client-side only",
            evidence=outbound_calls,
        ))

    # 4. source availability
    if tool.check_source and tool.github:
        reachable = check_github_reachable(tool.github)
        report.checks.append(CheckResult(
            name="source_public",
            passed=reachable,
            detail="github repo is public and reachable" if reachable else f"github repo NOT reachable: {tool.github}",
            evidence=[tool.github],
        ))

    # 5. console errors (informational)
    if console_errors:
        report.warnings.append(f"{len(console_errors)} console error(s)")
        report.checks.append(CheckResult(
            name="no_console_errors",
            passed=False,
            detail=f"{len(console_errors)} console error(s)",
            evidence=console_errors[:5],
        ))

    # verdict
    failures = [c for c in report.checks if not c.passed]
    if any(c.name in ("no_telemetry", "client_side_only") and not c.passed for c in failures):
        report.verdict = "fail"
    elif failures:
        report.verdict = "warn"
    else:
        report.verdict = "pass"

    return report


def main():
    ap = argparse.ArgumentParser(description="quantara tools privacy verifier")
    ap.add_argument("--tool", help="only verify one tool (substring match)")
    ap.add_argument("--json", action="store_true", help="output JSON")
    args = ap.parse_args()

    tools = TOOLS
    if args.tool:
        tools = [t for t in tools if args.tool.lower() in t.name.lower()]
        if not tools:
            sys.exit(f"no tool matches '{args.tool}'. names: {[t.name for t in TOOLS]}")

    playwright_ctx, browser = launch_browser()
    reports = []

    try:
        for tool in tools:
            print(f"  checking {tool.name} ...", file=sys.stderr)
            report = verify_tool(browser, tool)
            reports.append(report)
    finally:
        browser.close()
        playwright_ctx.stop()

    summary = {
        "run_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "tools_checked": len(reports),
        "pass": sum(1 for r in reports if r.verdict == "pass"),
        "warn": sum(1 for r in reports if r.verdict == "warn"),
        "fail": sum(1 for r in reports if r.verdict == "fail"),
        "reports": [r.to_dict() for r in reports],
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"\nmarginalia verifier — {summary['run_at']}")
        print(f"tools: {summary['tools_checked']} | pass: {summary['pass']} | warn: {summary['warn']} | fail: {summary['fail']}\n")
        for r in reports:
            icon = "✓" if r.verdict == "pass" else ("!" if r.verdict == "warn" else "✗")
            print(f"  {icon} {r.tool} ({r.url}) — {r.verdict}")
            for c in r.checks:
                mark = "✓" if c.passed else "✗"
                print(f"    {mark} {c.name}: {c.detail}")
            if r.warnings:
                for w in r.warnings:
                    print(f"    ! {w}")
        print()

    # exit non-zero if any tool failed a core privacy check
    if summary["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
