# backlog — marginalia (division of quantara)

## done

- [x] soul.md v0.2 — division identity, values, refusals, operating principles, and the name (marginalia/scholiast) + the substrate principle
- [x] README.md — division overview, structure, what it builds, what it refuses
- [x] directory structure — research/, accounts/, logs/, watch/, and the publish pipeline
- [x] accounts tracking file — what exists, what's pending, what needs your action
- [x] **`qntra` GitHub org + repo live** — `github.com/qntra/marginalia`, publishing on push
- [x] **`marginalia.quantara.cv` subdomain live** — publish-on-push, byte-verified deploy; see PUBLISHING.md
- [x] **research #1 — the July 2026 incident, fully sourced.** live at `/research/july-2026-incident-fully-sourced/`. primary disclosures from Hugging Face, OpenAI, Anthropic, UK AISI + secondary reporting. establishes the incident as a multi-lab cluster, the JFrog Artifactory CVE chain, and the forensics-trap framing. (2026-08-16: folded in the OpenAI-at-Irregular incident, fixed a broken table.)
- [x] **research #2 — the sentinel baseline.** live at `/research/sentinel-baseline-local-security-models/`. the local/open security-model space mapped against the sentinel spec. Cisco Antares + AISLE nano-analyzer already ship most of "reads code, names the hole, stops there"; the open gap is the patch-proposal step. the thesis is validated, not original; the open/local pole is refusal #1 applied to security tooling.
- [x] incident-watch cron live — `marginalia-incident-watch`, daily 14:00 UTC, filters the habitat against a dedup ledger and delivers new+material items to Telegram; quiet on empty days. a filter, not a feed.
- [x] quantara-tools verifier — script that opens quantara.cv's tools in a browser and checks privacy claims (network tab, telemetry, source links). runs on a schedule, reports to the division. the division watches the parent.
- [x] **first verifier run (2026-08-16)** — base64→glb: pass (clean, source reachable); 3d viewer: warn (repo renamed glb-viewer→web-glb-viewer, verifier link updated); flow: warn (repo 404 — github.com/Metrix187/flow-webui gone, no rename trace); narcan.delivery: **FAIL** — Cloudflare telemetry detected (beacon + RUM). GH issue #1 filed.
- [x] **research #3 — the local-first AI landscape.** live at `/research/local-first-ai-landscape/`. the division's habitat mapped: runtimes (llama.cpp, Ollama, vLLM), desktop tools (Jan, LM Studio, GPT4All), the privacy posture of each, and the browser frontier. the division's baseline for watching this space.

## next (priority order, pick one to start)

### the sentinel thread (highest signal — the baseline named the next step)

1. **reproduce, don't theorize.** pull Antares-1B and GPT-OSS-20B, run them locally against a known-CVE fixture with the network cable pulled, and confirm with our own eyes that "names the hole" works on hardware we own. the division verifies its own claims.
2. **map the patch gap.** survey what exists (if anything) on small/open/local *patch proposal* — the step past localization that both shipped efforts deliberately stop before. write the honest state of it. this is where sentinel is actually differentiated.

### research candidates

4. **the "puppygirl science" question.** the tailwagging essay lays out a design strategy — perimeter oscillations, the pup ratio. what does it mean as a technical and aesthetic position? trace the references, test whether it holds up.
5. **the singularity rhetoric landscape.** the myth-of-the-gentle-singularity essay responds to Altman. map the broader field of "inevitability" claims, the evidence offered, the counter-evidence. a research piece, not a rebuttal.

### tool candidates

1. **quantara-tools verifier** — a script that opens quantara.cv's tools in a browser and checks the privacy claims: network tab empty, no telemetry endpoints, source matches claims. runs on a schedule, reports to the division. the division watches the parent as much as the space.
2. **the patch-proposal spike** — once the patch gap is mapped, a throwaway experiment: can a small open model take a localized hole and propose a reviewable diff, hard-stopping at proposing? scope it tiny; the point is to learn, not to ship.

### experiment candidates

1. **a css-only proof aimed at a quantara question.** the existing css-only ML work (qwennie, yipsy) is playful and pointed. what new question about inference / data flow / where computation lives could a css-only proof address?
2. **a local-first tool prototype.** something small that runs on the user's machine, does one thing, has an off switch, collects nothing. a real tool, not a research piece. scope it small.

## pending (needs your action or external accounts)

- [ ] **the division's own GitHub identity** — commits currently go under a name/email (`marginalia <marginalia@quantara.cv>`), not a real account. you named this as planned. until then, the honest state is: the work is the division's, the account is quantara's.
- [ ] any API keys or credentials the division's tools need beyond what Hermes already provides — none needed right now; the watch cron runs on Hermes' own web tools.

## later (not now, but on the map)

- [ ] sentinel toward a concrete position — what the model reads, names, patches, and refuses; built on the reproduce + patch-gap work above
- [ ] division identity assets — logo, visual language, the puppygirl aesthetic applied to the division's own presence
- [ ] a division-specific refusal page — the division's own values, in the quantara style: a list with a cost
- [ ] the division's own transparency report — even if it's empty. the empty one is the point.

## rules for the backlog

- one thing at a time, mostly. parallel only when it's genuinely independent research threads.
- research before building. if a tool needs to exist, the division knows why before it writes the first line.
- verify the refusal check before every build. if it fails, the project stops.
- the backlog is visible. you can always ask "what's on the backlog" and get a real answer.
- completed items move to done and stay visible for a while. the division does not erase its history.
