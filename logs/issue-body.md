## summary

First verifier run completed 2026-08-16. Two findings that need the parent's attention.

---

## finding 1: broken GitHub source links (2 of 3 tools)

The verifier checks that each tool's GitHub link is reachable. Two are broken:

### flow-webui — 404 (repo deleted or renamed)

- **site:** https://flow.quantara.cyou/ (live, resolves as "QuantaraChat")
- **verifier link:** https://github.com/Metrix187/flow-webui
- **API result:** 404 Not Found
- **search:** zero results for "flow-webui" under Metrix187
- **repo list:** not present in Metrix187's active or archived repos
- **assessment:** the repo is gone. the tool itself is live but the source link on the site and in the verifier points to a dead repo.

### glb-viewer — renamed to web-glb-viewer

- **site:** https://3d.quantara.cyou/ (live)
- **verifier link:** https://github.com/Metrix187/glb-viewer
- **API result:** 404 Not Found
- **found:** https://github.com/Metrix187/web-glb-viewer exists
  - description: "a web based glb viewer, mobile friendly"
  - created: 2025-08-03 (same day the old name would have been active)
  - same purpose, clearly a rename
- **assessment:** the repo was renamed from `glb-viewer` to `web-glb-viewer`. the site and verifier links need to update.

### base64-to-glb — OK

- **site:** https://base64.quantara.cv/ (live)
- **verifier link:** https://github.com/Metrix187/base64-to-glb
- **API result:** 200 OK
- **assessment:** no action needed.

### what needs to happen

1. update the verifier script (`scripts/quantara-verify.py`) to point `glb-viewer` → `web-glb-viewer`
2. update any site links pointing to `github.com/Metrix187/glb-viewer`
3. for flow-webui: restore the repo under its old name, rename it to something else and update the link, or remove the GitHub link from the site if the source is no longer public

---

## finding 2: narcan.delivery phones home to Cloudflare (FAIL)

### tool description

- **site:** https://narcan.delivery/
- **purpose:** finds naloxone nearby — a sensitive health query tool
- **claim:** "finds naloxone nearby, then forgets. sensitive query — must not log."
- **github:** not listed with a github link on the site

### what the verifier found

- **static.cloudflareinsights.com/beacon.min.js** — Cloudflare analytics beacon loaded
- **cloudflareinsights.com/cdn-cgi/rum** — Cloudflare Real User Monitoring (RUM) active
- **CSP error:** console error — CSP directive blocks inline scripts (partial mitigation, but the beacon script still loads)

### why this is a fail

narcan.delivery is a sensitive-query tool. someone using it is asking "where can I get naloxone" — that's a health-adjacent query with real-world stakes. The tool should not phone home to a third party (Cloudflare) for analytics or RUM. This violates the quantara refusals:

- **no telemetry by default** — Cloudflare RUM + beacon is telemetry
- **no pane of glass** — Cloudflare Insights gives quantara a vantage point on who visits and what they do

### what needs to happen

1. remove the Cloudflare Insights beacon (`static.cloudflareinsights.com/beacon.min.js`)
2. disable Cloudflare RUM (`cloudflareinsights.com/cdn-cgi/rum`)
3. verify with the network tab that no outbound requests go to Cloudflare on page load
4. re-run the verifier to confirm the pass

---

## next run

- **verifier cron:** 10:00 UTC daily → Telegram
- **watcher cron:** 14:00 UTC daily → Telegram
- the division will re-check both on the next tick, but these need the parent's action to resolve.

## division note

the division is idle otherwise. soul v0.2 live, 3 research outputs live, sentinel reproduction harness written but blocked on this machine's hardware (54MB RAM, no GPU).
