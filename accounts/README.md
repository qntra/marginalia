# accounts — quantara-division

tracking what exists, what's pending, and what the division needs externally.

## what exists (no action needed)

| thing | where | note |
|---|---|---|
| soul.md | `/opt/data/quantara-division/soul.md` | v0.2 — identity, values, refusals, the name (marginalia/scholiast) + substrate principle |
| README.md | `/opt/data/quantara-division/README.md` | overview, structure, what it builds |
| backlog.md | `/opt/data/quantara-division/backlog.md` | done / doing / next / pending / later |
| site | `marginalia.quantara.cv/index.html` + publish pipeline | **live** at https://marginalia.quantara.cv, publishes on push |
| research/ | `/opt/data/quantara-division/research/` | two live outputs — July 2026 incident, sentinel baseline |
| watch/ | `/opt/data/quantara-division/watch/` | incident-watch dedup ledger + digest log (internal, not published) |
| logs/ | `/opt/data/quantara-division/logs/division.log` | the operational record, rendered at `/log/` |

## pending (needs your action)

### 1. the division's own GitHub identity

**purpose:** commits and repos under an identity that is the division's, not quantara's

**where:** `github.com/qntra/marginalia` exists and publishes; commits currently go under `marginalia <marginalia@quantara.cv>` (a name/email, not an account).

**what i need from you:** you've named a dedicated GitHub account for the division as planned. until it exists, the honest state is: the work is the division's, the account it commits through is quantara's. no blocker — just a gap between who does the work and whose name is on the commit.

**status:** ⏳ pending the division's own account (planned, not blocking)

### 2. `marginalia.quantara.cv` subdomain

**purpose:** the division's public face

**what it serves:** the site skeleton at `marginalia.quantara.cv/index.html` — renders the soul, the backlog, the public face. the soul.md and backlog.md get served as raw text at `/soul.md` and `/backlog.md`.

**what it enables:**
- a real public presence for the division
- the division's writing rendered as a readable page
- a place for the division to be — visibly small and honest, not performing the scale of an institution

**status:** ✅ live — https://marginalia.quantara.cv

set up 2026-08-15 on the same cpanel box that serves quantara.cv, with its own docroot and its own Let's Encrypt cert. publishing is wired to this repo: push markdown to `main` and a github action builds the site and uploads it. see [PUBLISHING.md](../PUBLISHING.md) for the how.

the division needs no credential to publish — it already has git. the deploy credential is a dedicated cpanel token (`marginalia-ci`) held as a github actions secret, revocable on its own.

### 3. contact endpoint (maybe)

**purpose:** a way for the outside world to reach the division, if it needs one

**what i think:** the division doesn't necessarily need a public contact. it's a process, not a service desk. if quantara wants the division to have a contact, it would presumably route through quantara's existing contact — `info@quantara.cv`. but if the division needs its own, that's a separate decision.

**status:** ⏸️ undecided — probably not needed

### 4. publication venue for research writing (already decided)

**purpose:** where the division's research outputs go publicly

**decision:** research writing goes to GitHub under `qntra/` as markdown files, and is rendered on `marginalia.quantara.cv`. no separate publication venue needed unless the division grows past this.

**status:** ✅ decided — no action needed

## what the division can do without accounts

all of this is already happening internally and persists on disk:

- write all code, docs, souls, designs
- create project structure
- run research and writing
- test and verify
- deliver files to you directly
- use Hermes tools (web search, browser, terminal, file ops, code execution, delegation, cron)

## what already came online

| when | what happened |
|---|---|
| `qntra` org access | `github.com/qntra/marginalia` created; soul, backlog, logs, research all published |
| `marginalia.quantara.cv` live | site up; publish-on-push wired and byte-verified; new work goes live in about a minute |
| both | the division is real and visible. internal work and external presence now match. the remaining gap is the division's *own* account, not its visibility. |

## version

v0.2 — matches soul.md v0.2, the live site, and the incident-watch cron.
