"""
render_showcase.py — SHOWCASE.md -> styled HTML -> print-ready PDF.

markdown-it for parsing (tables + blockquotes), pygments for code highlighting, a hand-written
print stylesheet for typography, and headless Chrome for the PDF. No pandoc/LaTeX needed.
"""
from pathlib import Path
import subprocess, sys

from markdown_it import MarkdownIt
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "SHOWCASE.md"
HTML = ROOT / "SHOWCASE.html"
PDF = ROOT / "SHOWCASE.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _highlight(code, lang, _attrs):
    try:
        lexer = get_lexer_by_name(lang or "text")
    except Exception:
        lexer = get_lexer_by_name("text")
    formatter = HtmlFormatter(nowrap=False, cssclass="hl")
    return highlight(code, lexer, formatter)


CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
:root{
  /* Jataware brand navy, sampled from the logo (#1D365B), with matching tints. */
  --ink:#12171f; --muted:#5b6675; --rule:#dfe4ec;
  --accent:#1D365B; --accent-mid:#5c7196; --accent-soft:#eef1f5;
  --code-bg:#f7f9fc; --good:#0f7b4f; --warn:#9a5b00;
}
*{box-sizing:border-box}
body{
  font-family:"Charter","Iowan Old Style","Palatino",Georgia,serif;
  color:var(--ink); line-height:1.56; font-size:10.3pt; margin:0;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:none}

/* ---- Jataware branded masthead ---- */
.masthead{
  display:flex; align-items:center; justify-content:space-between;
  padding-bottom:.55em; margin-bottom:1.5em;
  border-bottom:2.2px solid var(--accent);
}
.masthead img{height:30px; width:auto; display:block}
.masthead .kicker{
  font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:8.4pt; font-weight:600; letter-spacing:.09em; text-transform:uppercase;
  color:var(--accent-mid);
}

h1{
  font-size:23pt; line-height:1.18; letter-spacing:-.015em; margin:0 0 .25em;
  font-weight:700; color:var(--accent);
}
h1 + h3{
  font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:11.2pt; font-weight:500; color:var(--muted); line-height:1.45;
  margin:0 0 1.1em; letter-spacing:.005em;
}
h2{
  font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:14pt; font-weight:650; letter-spacing:-.01em; color:var(--accent);
  margin:1.5em 0 .6em; padding-bottom:.3em; border-bottom:2px solid var(--accent);
  break-after:avoid;
}
h3{
  font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:11.2pt; font-weight:650; color:var(--accent); margin:1.5em 0 .5em;
  break-after:avoid;
}
p{margin:.62em 0}
strong{font-weight:700}
em{color:var(--muted)}

/* lede blockquote under the title, and pull-quote cautions */
blockquote{
  margin:1.1em 0; padding:.85em 1.1em; background:var(--accent-soft);
  border-left:3px solid var(--accent); border-radius:0 5px 5px 0;
  font-size:10.1pt; color:#243044;
}
blockquote p{margin:.3em 0}
blockquote strong{color:#0d1b2e}

hr{border:0; border-top:1px solid var(--rule); margin:1.5em 0}

/* ---- code ---- */
code{
  font-family:"JetBrains Mono","SF Mono",Menlo,Consolas,monospace;
  font-size:8.9pt; background:#eef1f6; padding:.1em .36em; border-radius:3px;
  color:#243044;
}
pre{
  background:var(--code-bg); border:1px solid var(--rule); border-radius:6px;
  padding:.85em 1em; margin:.85em 0;
  break-inside:avoid; font-size:8.6pt; line-height:1.5;
  /* print has no scrollbars: wrap long lines instead of clipping them */
  white-space:pre-wrap; overflow-wrap:anywhere; word-break:break-word;
}
pre code{background:none;padding:0;font-size:inherit}
.hl{background:none}

/* ---- tables ---- */
table{
  border-collapse:collapse; width:100%; margin:1em 0; font-size:9.3pt;
  font-family:"Inter","Helvetica Neue",Arial,sans-serif; break-inside:avoid;
}
th{
  text-align:left; font-weight:650; font-size:8.5pt; letter-spacing:.04em;
  text-transform:uppercase; color:#fff; background:var(--accent);
  padding:.55em .6em;
}
th:first-child{border-top-left-radius:4px}
th:last-child{border-top-right-radius:4px}
td{padding:.46em .6em; border-bottom:1px solid var(--rule)}
tbody tr:last-child td{border-bottom:1.5px solid var(--accent)}
th[align=right],td[align=right]{text-align:right; font-variant-numeric:tabular-nums}
table strong{color:var(--accent)}

ul,ol{margin:.6em 0 .6em 1.15em; padding:0}
li{margin:.3em 0}

/* ---- figures ---- */
figure{
  margin:1.15em 0 1.25em; padding:0; break-inside:avoid; page-break-inside:avoid;
}
figure img{
  display:block; width:100%; height:auto;
  border:1px solid var(--rule); border-radius:6px; background:#fff;
}
figcaption{
  margin-top:.5em; font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:8.3pt; line-height:1.45; color:var(--muted);
  padding-left:.15em; border-left:2px solid var(--rule); padding-left:.6em;
}
figcaption code{font-size:7.8pt; background:#eef1f6}
figcaption em{color:var(--muted)}

.footer-note{
  margin-top:.9em; padding-top:.55em; border-top:1px solid var(--rule);
  font-size:8.6pt; color:var(--muted); line-height:1.5;
  font-family:"Inter","Helvetica Neue",Arial,sans-serif;
}
.footer-note code{font-size:8pt}

/* ---- formal abstract block ---- */
.abstract{
  background:var(--accent-soft); border:1px solid var(--rule); border-radius:6px;
  padding:1em 1.2em .6em; margin:1em 0; break-inside:avoid;
}
.abstract p{margin:.55em 0; font-size:9.8pt; line-height:1.55}
.abstract p:first-child{margin-top:0}
.abstract code{font-size:8.4pt}
.abstract-meta{
  display:block; margin-top:.4em; font-family:"Inter","Helvetica Neue",Arial,sans-serif;
  font-size:7.8pt; color:var(--muted); letter-spacing:.01em;
}
"""


def main():
    md = MarkdownIt("commonmark", {"highlight": _highlight}).enable("table")
    body = md.render(SRC.read_text())
    pyg = HtmlFormatter(cssclass="hl").get_style_defs(".hl")
    import sys as _sys
    _sys.path.insert(0, str(ROOT.parent / "common"))
    from style import logo_path
    logo = logo_path()               # shared JATAWARE/style-resources (no per-analysis copy)
    masthead = (
        "<div class='masthead'>"
        f"<img src='{logo.as_uri()}' alt='Jataware'>"
        "<span class='kicker'>Rosetta &nbsp;·&nbsp; DeepScale</span>"
        "</div>"
    )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Seasonal forecast design as a search problem</title>"
        f"<style>{CSS}\n{pyg}</style></head><body><div class='wrap'>{masthead}{body}</div></body></html>"
    )
    HTML.write_text(html)
    print(f"wrote {HTML} ({len(html)//1024} KB)")

    if Path(CHROME).exists():
        subprocess.run([
            CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
            f"--print-to-pdf={PDF}", HTML.as_uri(),
        ], check=True, capture_output=True, timeout=180)
        print(f"wrote {PDF} ({PDF.stat().st_size//1024} KB)")
    else:
        print("Chrome not found — HTML only", file=sys.stderr)


if __name__ == "__main__":
    main()
