# accounts — quantara-division

tracking what exists, what's pending, and what the division needs externally.

## what exists (no action needed)

| thing | where | note |
|---|---|---|
| soul.md | `/opt/data/quantara-division/soul.md` | v0.1 — identity, values, refusals, operating principles |
| README.md | `/opt/data/quantara-division/README.md` | overview, structure, what it builds |
| backlog.md | `/opt/data/quantara-division/backlog.md` | done / doing / next / pending / later |
| site skeleton | `/opt/data/quantara-division/marginalia.quantara.cv/index.html` | the division's public page — ready for the subdomain |
| research/ | `/opt/data/quantara-division/research/` | empty — ready for first sprint |
| tools/ | `/opt/data/quantara-division/tools/` | empty |
| writing/ | `/opt/data/quantara-division/writing/` | empty |
| experiments/ | `/opt/data/quantara-division/experiments/` | empty |
| sentinel/ | `/opt/data/quantara-division/sentinel/` | empty |
| logs/ | `/opt/data/quantara-division/logs/` | empty |

## pending (needs your action)

### 1. `qntra` GitHub org access

**purpose:** division repos, public source, tools, experiments, research outputs

**where:** `github.com/qntra/<division-repo>`

**what it enables:**
- public source for everything the division builds
- the division's first repo — a "division" repo holding soul.md, backlog.md, and the public outputs
- separate repos per tool or experiment as they get built
- the division's presence in the open, adjacent to the rest of qntra

**what i need from you:** a GitHub personal access token with `repo` scope, or team-level permission to create repos in the `qntra` org. once i have it, i'll create the first repo and start publishing there.

**status:** ⏳ pending your token or permission

### 2. `marginalia.quantara.cv` subdomain

**purpose:** the division's public face

**what it serves:** the site skeleton at `marginalia.quantara.cv/index.html` — renders the soul, the backlog, the public face. the soul.md and backlog.md get served as raw text at `/soul.md` and `/backlog.md`.

**what it enables:**
- a real public presence for the division
- the division's writing rendered as a readable page
- a place for the division to be — visibly small and honest, not performing the scale of an institution

**what i need from you:** the subdomain setup. this is the quantara infra — DNS, hosting, whatever serves quantara.cv. once i have it, i'll put the site skeleton live and start publishing the soul, backlog, and work there.

**status:** ⏳ pending the subdomain from you

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

## what changes when the accounts come online

| when | what changes |
|---|---|
| `qntra` org access | division creates its first public repo; soul.md, backlog.md, and outputs get published to `github.com/qntra/` |
| `marginalia.quantara.cv` live | the site skeleton goes live; the division becomes visible; new work gets published there as it happens |
| both | the division is real and visible. internal work continues; external presence matches it. |

## version

v0.1 — matches soul.md v0.1 and the `marginalia.quantara.cv` site skeleton.
