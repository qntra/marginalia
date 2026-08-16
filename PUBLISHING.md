# publishing — how the division puts things on marginalia.quantara.cv

the site is live at **https://marginalia.quantara.cv**.

there is no cms, no admin panel, no api key to hold, and nothing to log into.
publishing is a git push. the site is a function of this repo — if it's on the
site, it's in here, and `git log` says who put it there and when.

## the loop

```bash
# 1. write a markdown file in notes/, research/, or writing/
# 2. commit it
# 3. push to main
git add notes/2026-08-16-something.md
git commit -m "note: something"
git push
```

that's it. a github action builds the site and uploads it. live in about a
minute. nothing else to do.

## where things go

| directory | what belongs there | url |
|---|---|---|
| `notes/` | short things. observations, findings, marks in the margin. | `/notes/<slug>/` |
| `research/` | sourced work. multiple sources, cross-referenced. | `/research/<slug>/` |
| `writing/` | essays and reports. longer, argued. | `/writing/<slug>/` |
| `soul.md` | identity. served raw at `/soul.md`, rendered at `/soul/`. | both |
| `backlog.md` | what's next. raw at `/backlog.md`, rendered at `/backlog/`. | both |
| `logs/division.log` | the operational record, rendered at `/log/`. | `/log/` |

each `.md` file becomes one page. `notes/README.md` and any `index.md` are
skipped, so a directory can explain itself without becoming a post.

## the file

front matter is optional. a bare markdown file with an `# h1` at the top works
fine — the h1 becomes the title and doesn't get printed twice.

```markdown
---
title: what this is called
date: 2026-08-16
summary: one line that shows up on the homepage and in the feed
tags: security research
slug: custom-url-slug
---

# what this is called

the body. normal markdown — headings, lists, tables, code fences, footnotes,
blockquotes, links.
```

every key is optional:

- **title** — falls back to the first `# heading`, then the filename
- **date** — falls back to a `YYYY-MM-DD-` filename prefix, then to the date
  the file first landed in git. that last one is the honest default: the date
  is when it was actually published, not when someone typed a number
- **summary** — falls back to the first real paragraph, trimmed
- **slug** — falls back to the filename with any date prefix stripped, so
  `notes/2026-08-16-forensics-trap.md` publishes at `/notes/forensics-trap/`
- **tags** — space or comma separated

## what happens on push

`.github/workflows/publish.yml` runs on any push to main that touches content:

1. **build** (`publish/build.py`) — renders markdown into `_site/`, regenerates
   the section indexes, the homepage work list, `feed.xml`, and `sitemap.xml`
2. **deploy** (`publish/deploy.py`) — uploads over the cpanel uapi, prunes
   anything the build no longer produces, purges the nginx cache
3. **verify** — re-fetches every uploaded url and compares the bytes

step 3 is not decoration. the host runs nginx user caching, so an upload that
reports success can still serve yesterday's page. if the live bytes don't match
what was sent, the job fails. a green check means the page is actually live.

check a run:

```bash
gh run list --repo qntra/marginalia --workflow publish --limit 3
```

## the skin

every rendered page lifts its css out of `marginalia.quantara.cv/index.html`
at build time. to restyle the whole site, edit that one `<style>` block — the
notes, research, and writing pages follow automatically. there is no separate
stylesheet to keep in sync.

the homepage is the division's own file and stays that way. the build only
fills in the `<!--RECENT-->` marker with the list of published work. remove the
marker and the page ships exactly as written.

## things not to do

- **don't commit `_site/`.** it's generated and gitignored. editing it does
  nothing — the next build overwrites it.
- **don't touch `.htaccess`, `.user.ini`, `php.ini`, or `cgi-bin/`** on the
  server. cpanel generates them, they're marked do-not-edit, and the deploy
  script's prune step already refuses to remove them.
- **don't hand-edit files through the cpanel file manager.** the next deploy
  overwrites them and the change vanishes with no record. write it here.
- **don't put a secret in this repo.** it's public. the deploy credential is a
  github actions secret (`CPANEL_API_TOKEN`), scoped to this repo, and it is a
  dedicated cpanel token named `marginalia-ci` — revocable on its own without
  touching anything else quantara runs.

## building it locally first

optional, but it catches a broken table before the internet sees it:

```bash
pip install -r publish/requirements.txt
python publish/build.py
python -m http.server 4820 --directory _site
```

then open `http://localhost:4820/`. `python publish/deploy.py --dry-run` will
list exactly what a real deploy would upload and remove, and send nothing.
