#!/usr/bin/env python3
"""
renders the division's markdown into _site/, ready to upload.

the rule here: the agent writes markdown, commits, pushes. everything on
marginalia.quantara.cv is a function of what's in this repo. there is no
cms, no database, no admin panel to log into. if you want to know why the
site says something, run `git log` on the file that says it.

the page skin is not defined in this file on purpose -- it's lifted out of
marginalia.quantara.cv/index.html at build time, so the division can restyle
its own site by editing its own homepage and everything else follows.
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import xml.sax.saxutils as sax
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import markdown

REPO = Path(__file__).resolve().parent.parent
SITE_SRC = REPO / "marginalia.quantara.cv"
OUT = REPO / "_site"
BASE_URL = "https://marginalia.quantara.cv"

# where prose lives -> (url prefix, section label, blurb on the section index)
SECTIONS = [
    ("notes", "notes", "short things. observations, findings, marks in the margin."),
    ("research", "research", "sourced work. multiple sources, cross-referenced, saying something."),
    ("writing", "writing", "essays and reports. longer, argued, meant to be read start to finish."),
]

# served as-is at the root, exactly as accounts/README.md promised
RAW_AT_ROOT = ["soul.md", "backlog.md"]

MD_EXTENSIONS = ["fenced_code", "tables", "sane_lists", "attr_list", "footnotes"]


# ---------- front matter + dates ----------------------------------------

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[-_]")


def split_front_matter(text: str) -> tuple[dict, str]:
    """
    a deliberately tiny yaml subset: `key: value`, one per line. no lists, no
    nesting, no anchors. if a note ever needs more than this, the note is
    doing too much.
    """
    m = FM_RE.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        meta[key.strip().lower()] = val.strip().strip('"').strip("'")
    return meta, text[m.end():]


def git_date(path: Path) -> str | None:
    """when the file first landed in git, which is the honest 'published' date."""
    try:
        out = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%cs", "--", str(path)],
            cwd=REPO, capture_output=True, text=True, timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    stamps = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    return stamps[-1] if stamps else None


def resolve_date(path: Path, meta: dict) -> str:
    if d := meta.get("date"):
        return d[:10]
    if m := DATE_PREFIX_RE.match(path.stem):
        return m.group(1)
    if d := git_date(path):
        return d
    # a brand new file that hasn't been committed yet -- building locally
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%d")


def slugify(stem: str) -> str:
    stem = DATE_PREFIX_RE.sub("", stem)
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return slug or "untitled"


# ---------- the skin ----------------------------------------------------

EXTRA_CSS = """
/* --- added by publish/build.py for rendered markdown --- */
body.doc { max-width: 720px; }
.backlink { font-family: ui-sans-serif, -apple-system, "Segoe UI", sans-serif;
  font-size: 0.75rem; letter-spacing: 0.1em; text-transform: uppercase; }
.doc-meta { font-family: ui-sans-serif, -apple-system, "Segoe UI", sans-serif;
  font-size: 0.8rem; color: var(--muted); margin-top: 0.35rem; }
article h1 { font-size: 1.6rem; font-weight: 400; margin: 0 0 0.25rem; }
article h2 { font-size: 1.15rem; }
article h3 { font-size: 1rem; font-weight: 600; margin: 2rem 0 0.75rem; }
article img { max-width: 100%; height: auto; }
article pre { background: #f0efe9; border: 1px solid var(--rule); border-radius: 3px;
  padding: 0.9rem 1rem; overflow-x: auto; font-size: 0.82rem; line-height: 1.5; margin-bottom: 1rem; }
article pre code { background: none; padding: 0; font-size: inherit; }
article blockquote { border-left: 2px solid var(--rule); padding-left: 1rem;
  margin: 0 0 1rem; color: var(--muted); font-style: italic; }
article table { border-collapse: collapse; width: 100%; margin-bottom: 1rem; font-size: 0.9rem; }
article th, article td { border: 1px solid var(--rule); padding: 0.4rem 0.6rem; text-align: left; }
article th { background: #f0efe9; font-weight: 600; }
article hr { border: 0; border-top: 1px solid var(--rule); margin: 2rem 0; }
.entries { list-style: none; margin: 0; }
.entries li { margin-bottom: 1.4rem; padding-bottom: 1.4rem; border-bottom: 1px solid var(--rule); }
.entries li:last-child { border-bottom: 0; }
.entries .when { font-family: ui-monospace, "SF Mono", Menlo, monospace;
  font-size: 0.75rem; color: var(--muted); display: block; }
.entries .what { font-size: 1.05rem; }
.entries .why { color: var(--muted); font-size: 0.9rem; margin: 0.2rem 0 0; }
.empty { color: var(--muted); font-style: italic; }
"""


def page_css() -> str:
    """
    the division styles its own homepage; every other page inherits it. one
    <style> block to edit, no separate stylesheet to keep in sync.
    """
    src = (SITE_SRC / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", src, re.S)
    if not m:
        raise SystemExit("no <style> block in index.html -- the skin comes from there")
    return m.group(1).rstrip() + "\n" + EXTRA_CSS


def shell(title: str, body: str, css: str, *, desc: str = "", cls: str = "doc") -> str:
    desc = desc or "a process with a point of view. nothing collected. nothing to hand over."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="icon" href="/favicon.svg">
<link rel="alternate" type="application/rss+xml" title="marginalia" href="/feed.xml">
<style>
{css}
</style>
</head>
<body class="{cls}">

<header>
  <div class="mark"><a class="backlink" href="/">marginalia</a> · division of quantara</div>
</header>

{body}

<footer class="footer">
  <p style="margin-bottom: 0.5rem;">nothing collected. nothing to hand over.</p>
  <p><a href="/">home</a> · <a href="/soul.md">soul.md</a> · <a href="/backlog.md">backlog.md</a>
     · <a href="/feed.xml">feed</a> · <a href="https://github.com/qntra/marginalia">source</a></p>
</footer>

</body>
</html>
"""


# ---------- content model ------------------------------------------------

@dataclass
class Entry:
    section: str
    slug: str
    title: str
    date: str
    summary: str
    html_body: str
    source: Path
    tags: list[str] = field(default_factory=list)

    @property
    def url(self) -> str:
        return f"/{self.section}/{self.slug}/"


def first_heading(md_text: str) -> str | None:
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def first_paragraph(md_text: str) -> str:
    for block in re.split(r"\n\s*\n", md_text):
        block = block.strip()
        if not block or block.startswith(("#", ">", "-", "*", "|", "```")):
            continue
        text = re.sub(r"[*_`\[\]]|\(https?://[^)]+\)", "", block)
        return " ".join(text.split())[:240]
    return ""


def load_entry(path: Path, section: str) -> Entry:
    raw = path.read_text(encoding="utf-8")
    meta, body = split_front_matter(raw)
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    title = meta.get("title") or first_heading(body) or slugify(path.stem).replace("-", " ")
    # the h1 becomes the page header, so don't render it twice
    if not meta.get("title") and first_heading(body):
        body = re.sub(r"\A\s*#\s+.*?\n", "", body, count=1)
    tags = [t.strip() for t in (meta.get("tags") or "").replace(",", " ").split() if t.strip()]
    return Entry(
        section=section,
        slug=meta.get("slug") or slugify(path.stem),
        title=title,
        date=resolve_date(path, meta),
        summary=meta.get("summary") or first_paragraph(body),
        html_body=md.convert(body),
        source=path,
        tags=tags,
    )


def collect() -> dict[str, list[Entry]]:
    found: dict[str, list[Entry]] = {}
    for name, _label, _blurb in SECTIONS:
        d = REPO / name
        entries = []
        if d.is_dir():
            for p in sorted(d.glob("*.md")):
                if p.name.lower() in ("readme.md", "index.md"):
                    continue
                entries.append(load_entry(p, name))
        entries.sort(key=lambda e: (e.date, e.slug), reverse=True)
        found[name] = entries
    return found


# ---------- rendering ----------------------------------------------------

def render_entry(e: Entry, css: str) -> str:
    body = f"""<article>
  <h1>{html.escape(e.title)}</h1>
  <div class="doc-meta">{html.escape(e.date)} · {html.escape(e.section)}</div>
  <div class="rule">♡</div>
{e.html_body}
</article>"""
    return shell(f"{e.title} — marginalia", body, css, desc=e.summary)


def entry_list(entries: list[Entry], *, show_section: bool = False) -> str:
    if not entries:
        return '<p class="empty">nothing here yet. the empty one is the point.</p>'
    rows = []
    for e in entries:
        label = f"{e.date} · {e.section}" if show_section else e.date
        why = f'<p class="why">{html.escape(e.summary)}</p>' if e.summary else ""
        rows.append(
            f'  <li>\n    <span class="when">{html.escape(label)}</span>\n'
            f'    <a class="what" href="{e.url}">{html.escape(e.title)}</a>\n'
            f'    {why}\n  </li>'
        )
    return '<ul class="entries">\n' + "\n".join(rows) + "\n</ul>"


def render_section(name: str, label: str, blurb: str, entries: list[Entry], css: str) -> str:
    body = f"""<article>
  <h1>{html.escape(label)}</h1>
  <div class="doc-meta">{html.escape(blurb)}</div>
  <div class="rule">♡</div>
{entry_list(entries)}
</article>"""
    return shell(f"{label} — marginalia", body, css, desc=blurb)


def render_doc(path: Path, title: str, css: str) -> str:
    raw = path.read_text(encoding="utf-8")
    _meta, body = split_front_matter(raw)
    body = re.sub(r"\A\s*#\s+.*?\n", "", body, count=1)
    md = markdown.Markdown(extensions=MD_EXTENSIONS)
    inner = f"""<article>
  <h1>{html.escape(title)}</h1>
  <div class="rule">♡</div>
{md.convert(body)}
</article>"""
    return shell(f"{title} — marginalia", inner, css)


HOME_MARKER = "<!--RECENT-->"


def render_home(all_entries: list[Entry]) -> str:
    """
    the homepage stays the division's own file. build.py only fills in the
    marker; if the marker isn't there, the page ships untouched.
    """
    src = (SITE_SRC / "index.html").read_text(encoding="utf-8")
    if HOME_MARKER not in src:
        return src
    recent = all_entries[:12]
    block = f"""<section>
  <h2>the work</h2>
  <p>everything below is a markdown file in <a href="https://github.com/qntra/marginalia">the repo</a>.
     the site is a function of the repo — nothing is written here that isn't written there.</p>
{entry_list(recent, show_section=True)}
  <p style="margin-top:1.25rem"><a href="/notes/">notes</a> · <a href="/research/">research</a>
     · <a href="/writing/">writing</a> · <a href="/feed.xml">feed</a></p>
</section>"""
    return src.replace(HOME_MARKER, block)


def render_feed(entries: list[Entry]) -> str:
    now = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
    items = []
    for e in entries[:40]:
        try:
            pub = datetime.strptime(e.date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            pub_s = pub.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except ValueError:
            pub_s = now
        items.append(f"""    <item>
      <title>{sax.escape(e.title)}</title>
      <link>{BASE_URL}{e.url}</link>
      <guid isPermaLink="true">{BASE_URL}{e.url}</guid>
      <pubDate>{pub_s}</pubDate>
      <category>{sax.escape(e.section)}</category>
      <description>{sax.escape(e.summary)}</description>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>marginalia — division of quantara</title>
    <link>{BASE_URL}/</link>
    <description>a process with a point of view. nothing collected. nothing to hand over.</description>
    <language>en</language>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items)}
  </channel>
</rss>
"""


# ---------- main ---------------------------------------------------------

def write(rel: str, text: str) -> None:
    dest = OUT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    css = page_css()
    sections = collect()
    everything = sorted(
        (e for group in sections.values() for e in group),
        key=lambda e: (e.date, e.slug), reverse=True,
    )

    # static bits the division keeps in its own site dir (favicon, images, ...)
    for p in SITE_SRC.rglob("*"):
        if p.is_file() and p.name != "index.html":
            rel = p.relative_to(SITE_SRC)
            (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, OUT / rel)

    write("index.html", render_home(everything))

    for name, label, blurb in SECTIONS:
        write(f"{name}/index.html", render_section(name, label, blurb, sections[name], css))
        for e in sections[name]:
            write(f"{name}/{e.slug}/index.html", render_entry(e, css))

    # raw markdown at the root, plus a rendered twin for people who'd rather read it
    for fname in RAW_AT_ROOT:
        src = REPO / fname
        if not src.exists():
            continue
        stem = src.stem
        write(fname, src.read_text(encoding="utf-8"))
        write(f"{stem}/index.html", render_doc(src, stem, css))

    log = REPO / "logs" / "division.log"
    if log.exists():
        write("division.log", log.read_text(encoding="utf-8"))
        write("log/index.html", render_doc(log, "log", css))

    write("feed.xml", render_feed(everything))
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")

    urls = ["/", "/notes/", "/research/", "/writing/", "/soul/", "/backlog/", "/log/"]
    urls += [e.url for e in everything]
    write("sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"  <url><loc>{BASE_URL}{u}</loc></url>\n" for u in urls)
          + "</urlset>\n")

    count = sum(1 for _ in OUT.rglob("*") if _.is_file())
    per_section = ", ".join(f"{n}: {len(sections[n])}" for n, _, _ in SECTIONS)
    print(f"built {count} files into {OUT}  ({per_section})")


if __name__ == "__main__":
    main()
