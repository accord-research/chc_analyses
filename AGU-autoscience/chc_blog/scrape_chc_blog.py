"""scrape_chc_blog.py — pull the N most-recent UCSB Climate Hazards Center blog posts.

The CHC blog (https://blog.chc.ucsb.edu) is WordPress, but its REST API and RSS feed are
intercepted (return the site shell), so this scrapes the rendered HTML with BeautifulSoup:

  1. walk the paged listing (`?paged=1,2,…`) collecting post permalinks (`?p=<id>`), newest first;
  2. fetch each post, extract title / date / author / categories / body;
  3. convert the body to readable Markdown (links preserved for citation; figures noted);
  4. write `posts/<NNN>-<slug>.md` (YAML front-matter + body) and `posts/index.json`.

Polite: a real UA and a short delay between requests. Idempotent: re-running overwrites.

Usage: python scrape_chc_blog.py [N]      # default N=30
"""
from __future__ import annotations
import json, re, sys, time, urllib.request
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

BASE = "https://blog.chc.ucsb.edu"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) research-scraper (ACCORD/AGU-autoscience)"}
HERE = Path(__file__).resolve().parent
POSTS = HERE / "posts"
DELAY = 0.8  # seconds between requests


def get(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "replace")


def _main_post_links(html: str) -> list[str]:
    """Post permalinks from the MAIN content column only (sidebar 'popular posts' widgets removed),
    preserving document order."""
    soup = BeautifulSoup(html, "html.parser")
    for junk in soup.select("aside, #secondary, .sidebar, .widget, .widget-area, footer, nav"):
        junk.decompose()
    main = soup.select_one("#main") or soup.select_one(".site-main") or soup.select_one("#content") or soup
    out, seen = [], set()
    for a in main.find_all("a", href=re.compile(r"https://blog\.chc\.ucsb\.edu/\?p=\d+")):
        u = a["href"]
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def recent_post_urls(n: int) -> list[str]:
    """Collect the n most-recent post permalinks by walking monthly archives (?m=YYYYMM) newest
    first — clean reverse-chronological order, no sidebar contamination."""
    home = get(f"{BASE}/")
    months = sorted(set(re.findall(r"\?m=(\d{6})", home)), reverse=True)
    seen, ordered = set(), []
    for ym in months:
        if len(ordered) >= n:
            break
        for u in _main_post_links(get(f"{BASE}/?m={ym}")):
            if u not in seen:
                seen.add(u); ordered.append(u)
        time.sleep(DELAY)
    return ordered[:n]


def _inline(el) -> str:
    """Render inline content, preserving links as [text](url) and bold/italic."""
    out = []
    for c in el.children:
        if isinstance(c, NavigableString):
            out.append(str(c))
        elif isinstance(c, Tag):
            if c.name == "a" and c.get("href"):
                out.append(f"[{c.get_text(' ', strip=True)}]({c['href']})")
            elif c.name in ("strong", "b"):
                out.append(f"**{c.get_text(' ', strip=True)}**")
            elif c.name in ("em", "i"):
                out.append(f"*{c.get_text(' ', strip=True)}*")
            elif c.name == "br":
                out.append("\n")
            else:
                out.append(_inline(c))
    return re.sub(r"[ \t]+", " ", "".join(out)).strip()


def html_to_md(content: Tag) -> str:
    """Convert a WordPress entry-content block to readable Markdown (block-level walk)."""
    lines = []
    for el in content.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "blockquote", "figure", "img", "table"], recursive=True):
        # skip nested elements already emitted by a parent list/figure
        if el.find_parent(["ul", "ol", "figure", "table"]) is not None and el.name not in ("li",):
            continue
        if el.name in ("h1", "h2", "h3", "h4"):
            lvl = int(el.name[1]); txt = _inline(el)
            if txt: lines.append(f"\n{'#' * (lvl + 1)} {txt}\n")
        elif el.name == "p":
            txt = _inline(el)
            if txt: lines.append(txt + "\n")
        elif el.name in ("ul", "ol"):
            for i, li in enumerate(el.find_all("li", recursive=False), 1):
                bullet = "-" if el.name == "ul" else f"{i}."
                t = _inline(li)
                if t: lines.append(f"{bullet} {t}")
            lines.append("")
        elif el.name == "blockquote":
            t = _inline(el)
            if t: lines.append(f"> {t}\n")
        elif el.name in ("figure", "img"):
            img = el if el.name == "img" else el.find("img")
            cap = el.find("figcaption")
            src = img.get("src", "") if img else ""
            alt = (cap.get_text(" ", strip=True) if cap else (img.get("alt", "") if img else ""))
            if src: lines.append(f"![{alt}]({src})\n")
        elif el.name == "table":
            lines.append("*(table omitted — see original post)*\n")
    md = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", md).strip()


def parse_post(url: str) -> dict:
    soup = BeautifulSoup(get(url), "html.parser")
    pid = re.search(r"\?p=(\d+)", url).group(1)
    title_el = soup.find(class_=re.compile("entry-title")) or soup.find("h1")
    title = title_el.get_text(" ", strip=True) if title_el else f"post-{pid}"
    iso = ""
    t = soup.find("time")
    if t and t.get("datetime"):
        iso = t["datetime"][:10]
    date_el = soup.find(class_=re.compile("posted-on|entry-date")) or t
    date_raw = date_el.get_text(" ", strip=True) if date_el else ""
    # take the FIRST clean "Month DD, YYYY" (posted-on often duplicates the date text)
    m_date = re.search(r"[A-Z][a-z]+ \d{1,2}, \d{4}", date_raw)
    date = m_date.group(0) if m_date else re.sub(r"^Posted on\s*", "", date_raw).strip()
    cats = sorted({a.get_text(strip=True) for a in soup.find_all("a", href=re.compile(r"\?cat=|/category/"))})
    content = soup.find(class_=re.compile("entry-content"))
    body = html_to_md(content) if content else ""
    author = ""
    ab = soup.find(class_=re.compile("author|byline"))
    if ab:
        author = re.sub(r"^(Author|By)\s*", "", ab.get_text(" ", strip=True)).strip()[:120]
    m = re.search(r"Authors?:\s*([^\n.]+)", body)
    if m and not author:
        author = m.group(1).strip()[:200]
    return dict(id=pid, url=url, title=title, date=date, iso_date=iso,
                author=author, categories=cats, body=body)


def slugify(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    return re.sub(r"[\s_-]+", "-", s)[:60].strip("-")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    POSTS.mkdir(parents=True, exist_ok=True)
    urls = recent_post_urls(n)
    print(f"collected {len(urls)} recent post URLs")
    index = []
    for i, url in enumerate(urls, 1):
        try:
            p = parse_post(url)
        except Exception as e:
            print(f"  [{i:02d}] FAIL {url}: {type(e).__name__}: {e}")
            continue
        fname = f"{i:02d}-{slugify(p['title'])}.md"
        fm = ["---", f"id: {p['id']}", f"title: \"{p['title'].replace(chr(34), chr(39))}\"",
              f"date: \"{p['date']}\"", f"iso_date: {p['iso_date']}",
              f"author: \"{p['author'].replace(chr(34), chr(39))}\"",
              f"categories: [{', '.join(p['categories'])}]", f"url: {p['url']}", "---", ""]
        (POSTS / fname).write_text("\n".join(fm) + f"# {p['title']}\n\n{p['body']}\n")
        index.append(dict(order=i, file=fname, **{k: p[k] for k in
                     ("id", "title", "date", "iso_date", "author", "categories", "url")},
                     words=len(p["body"].split())))
        print(f"  [{i:02d}] {p['date'][:20]:22s} {p['title'][:60]}  ({len(p['body'].split())} words)")
        time.sleep(DELAY)
    (POSTS / "index.json").write_text(json.dumps(index, indent=2))
    print(f"\nwrote {len(index)} posts + index.json to {POSTS}")


if __name__ == "__main__":
    main()
