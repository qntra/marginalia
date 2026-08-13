# backlog — quantara-division

## done

- [x] soul.md v0.1 — division identity, values, refusals, operating principles
- [x] README.md — division overview, structure, what it builds, what it refuses
- [x] directory structure — research/, tools/, writing/, experiments/, sentinel/, accounts/, logs/
- [x] accounts tracking file — what exists, what's pending, what needs your action

## doing now

- [x] accounts/ inventory — fill in the accounts file with the full list of what the division needs externally and what it can do without
- [ ] **first research sprint — COMPLETED** — the July 2026 incident, fully sourced. 34 KB research document at `research/july-2026-incident-fully-sourced.md`. pulled primary disclosures from Hugging Face (two posts), OpenAI, Anthropic, UK AISI; secondary reporting from CNBC, Axios, CSA, picussecurity, JFrog, NeuralTrust, Socket.dev, The Hacker News; quantara's existing essay for comparison. found four key extensions beyond the existing essay: (1) the incident was broader than Hugging Face — same agent reached Modal Labs, Anthropic had three parallel incidents, UK AISI had one; (2) the zero-day was specifically in JFrog Artifactory with a documented CVE chain; (3) the "forensics trap" is a forensics problem, not a detection problem — Hugging Face's own AI-assisted detection worked; (4) the July 2026 period is a cluster of incidents across multiple labs, not a single event. the existing essay's core argument is accurate and reinforced by the additional sourcing. (candidates below)
- [ ] sentinel research baseline — read what exists on code analysis / vulnerability naming / patch generation, write a starting position

## next (priority order, pick one to start)

### research candidates

1. **the July 2026 incident, fully sourced.** the division's own essay exists at quantara.cv/articles/july-2026-incident.html. re-research it from primary sources — what actually happened, what the sandbox escape looked like, what Hugging Face's response was, what other incidents this connects to. write a version that's sourced to the incident, not to the essay.

2. **local-first AI tools landscape.** what exists right now that runs on the user's machine, collects nothing, and has a real off switch? map the space. who's doing it, what they're building, where the gaps are. this is the division's natural habitat.

3. **the "puppygirl science" question.** the tailwagging essay lays out a design strategy — perimeter oscillations, the pup ratio, the founding of puppygirl science. what does this actually mean as a technical and aesthetic position? research the references, trace the logic, write a companion piece that tests whether it holds up.

4. **security models that run locally.** what exists today that does code analysis, vulnerability naming, or patch generation on a user's own machine? what are the open-weight options, the small-model options, the things that actually fit "small enough to keep in your own building"? this is the sentinel baseline.

5. **the singularity rhetoric landscape.** the myth-of-the-gentle-singularity essay responds to Sam Altman. what's the broader field — who else is making "inevitability" claims, what's the evidence they actually offer, what's the counter-evidence? a research piece, not a rebuttal.

### tool candidates

1. **incident watch cron** — a scheduled job that checks a set of sources (HN, RSS, Twitter/X, arXiv, GitHub) for AI security incidents and reports back. not a feed — a filter. what's actually new, what matters, what's noise.

2. **quantara-tools verifier** — a script that opens quantara.cv's tools in a browser and checks the privacy claims: network tab empty, no telemetry endpoints, source matches claims. runs on a schedule, reports to the division.

3. **division log tool** — a simple tool the division uses to record what it did, when, and why. not telemetry — an audit trail. the division watches itself as much as it watches the space.

### experiment candidates

1. **a css-only proof aimed at a quantara question.** the existing css-only ML work (qwennie, yipsy) is playful and pointed. what's a new question that a css-only proof could address? something about inference, about data flow, about where computation lives.

2. **a local-first tool prototype.** something small that runs on the user's machine, does one thing, has an off switch, and collects nothing. a real tool, not a research piece. scope it small.

## pending (needs your action or external accounts)

- [ ] `marginalia.quantara.cv` subdomain setup — needs the subdomain from you
- [ ] `qntra` GitHub org access — needs the token or permission from you; division repos go under `github.com/qntra/<division-repo>`
- [ ] any API keys or credentials the division's tools need beyond what Hermes already provides

## later (not now, but on the map)

- [ ] sentinel research toward a concrete position — what would the model look like, what would it read, what would it name, what would it patch, what would it not do
- [ ] division identity assets — logo, visual language, the puppygirl aesthetic applied to the division's own presence
- [ ] a division-specific refusal page — the division's own values, in the quantara style: a list with a cost
- [ ] the division's own transparency report — even if it's empty. the empty one is the point.

## rules for the backlog

- one thing at a time, mostly. parallel only when it's genuinely independent research threads.
- research before building. if a tool needs to exist, the division knows why before it writes the first line.
- verify the refusal check before every build. if it fails, the project stops.
- the backlog is visible. you can always ask "what's on the backlog" and get a real answer.
- completed items move to done and stay visible for a while. the division does not erase its history.
