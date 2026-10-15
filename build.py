"""Статическая сборка сайта Oh-My-Opencode — простым языком.
Читает *.md из корня, складывает готовые .html в site/.
Запуск: python build.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
SRC = ROOT / "site-src"
SITE_TITLE = "Oh-My-Opencode — простым языком"

PAGES = [
    ("README-ru.md", ("index.html", "Главная")),
    ("00-architecture-ru.md", ("00-architecture.html", "Обзор архитектуры")),
    ("01-plugin-bootstrap-ru.md", ("01-plugin-bootstrap.html", "01 · Как просыпается OMO")),
    ("02-sisyphus-planning-ru.md", ("02-sisyphus-planning.html", "02 · Начальник получает задание")),
    ("03-delegation-ru.md", ("03-delegation.html", "03 · Кто кому что поручает")),
    ("04-specialist-agents-ru.md", ("04-specialist-agents.html", "04 · Команда специалистов")),
    ("05-hook-pipeline-ru.md", ("05-hook-pipeline.html", "05 · Невидимые контролёры")),
    ("06-error-recovery-ru.md", ("06-error-recovery.html", "06 · Когда что-то ломается")),
    ("07-background-agents-ru.md", ("07-background-agents.html", "07 · Работа в несколько рук")),
    ("08-dynamic-prompts-ru.md", ("08-dynamic-prompts.html", "08 · Инструкции на лету")),
    ("09-crafted-tools-ru.md", ("09-crafted-tools.html", "09 · Крутые инструменты")),
    ("10-cc-compatibility-ru.md", ("10-cc-compatibility.html", "10 · Дружба со старыми привычками")),
    ("11-ralph-loop-ru.md", ("11-ralph-loop.html", "11 · Цикл до победного")),
]

MD_LINK = re.compile(r"\[([^\]]+)\]\(\./([^)]+?)-ru\.md\)")


def inline(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = MD_LINK.sub(lambda m: f'<a href="./{m.group(2)}.html">{m.group(1)}</a>', s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def is_table_sep(line: str) -> bool:
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def md_to_html(md: str) -> str:
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    in_code = False
    code_lang = ""
    code_buf: list[str] = []
    in_list = False

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = stripped[3:].strip()
                code_buf = []
            else:
                in_code = False
                if code_lang == "mermaid":
                    raw = "\n".join(code_buf)
                    out.append(
                        '<div class="mermaid-wrap">'
                        f'<pre class="mermaid-source"><code>{html.escape(raw)}</code></pre>'
                        f'<div class="mermaid">{html.escape(raw)}</div></div>'
                    )
                else:
                    cls = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                    out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code_buf))}</code></pre>")
                code_lang = ""
                code_buf = []
            i += 1
            continue
        if in_code:
            code_buf.append(line.rstrip("\n"))
            i += 1
            continue
        if "|" in line and i + 1 < len(lines) and is_table_sep(lines[i + 1]):
            close_list()
            headers = [c.strip() for c in line.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append('<div class="table-wrap"><table><thead><tr>')
            out.extend(f"<th>{inline(h)}</th>" for h in headers)
            out.append("</tr></thead><tbody>")
            for row in rows:
                out.append("<tr>")
                for j, h in enumerate(headers):
                    cell = row[j] if j < len(row) else ""
                    out.append(f"<td>{inline(cell)}</td>")
                out.append("</tr>")
            out.append("</tbody></table></div>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)", stripped)
        if m:
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2).strip())}</h{level}>")
            i += 1
            continue
        if stripped in ("---", "***"):
            close_list()
            out.append("<hr>")
            i += 1
            continue
        if stripped.startswith(">"):
            close_list()
            out.append(f"<blockquote>{inline(re.sub(r'^>\\s?', '', stripped))}</blockquote>")
            i += 1
            continue
        if re.match(r"^([-*]|\d+\.)\s+", stripped):
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^([-*]|\d+\.)\s+", "", stripped)
            out.append(f"<li>{inline(item)}</li>")
            i += 1
            continue
        if not stripped:
            close_list()
            i += 1
            continue
        close_list()
        out.append(f"<p>{inline(stripped)}</p>")
        i += 1
    close_list()
    return "\n".join(out)
def page_title(md: str, fallback: str) -> str:
    for line in md.split("\n"):
        if line.startswith("# "):
            return re.sub(r"[#*>`]", "", line).strip()
    return fallback


def strip_md(md: str) -> str:
    md = re.sub(r"```.*?```", " ", md, flags=re.S)
    md = re.sub(r"[#>*|`\-]", " ", md)
    md = MD_LINK.sub(lambda m: m.group(1), md)
    md = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", md)
    return re.sub(r"\s+", " ", md).strip()


TEMPLATE_HEAD = """<!DOCTYPE html>
<html lang="ru" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {site}</title>
<meta name="description" content="Перевод руководства Oh My OpenCode простым языком.">
<link rel="stylesheet" href="./style.css">
</head>
<body>
<a class="skip" href="#content">Перейти к содержанию</a>
<header class="topbar">
  <a class="brand" href="./index.html">{site}</a>
  <div class="search">
    <input id="search" type="search" placeholder="Поиск по руководству…  ( / )" autocomplete="off" aria-label="Поиск по руководству">
    <div id="results" class="results" hidden></div>
  </div>
  <button id="theme" class="theme-btn" type="button" aria-label="Переключить тему">Тема</button>
</header>
<div class="layout">
  <nav class="side" aria-label="Содержание">
    <details class="side-toggle" open>
      <summary>Содержание</summary>
      {nav}
    </details>
  </nav>
  <main id="content" class="content">
"""

TEMPLATE_FOOT = """
    {pager}
  </main>
</div>
<footer class="foot">Упрощённый пересказ learn-OMO на русском · <a href="https://github.com/yangheng/learn-OMO">оригинал</a></footer>
<script src="./app.js" defer></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" defer></script>
</body>
</html>
"""


def build() -> None:
    SITE.mkdir(exist_ok=True)
    entries = []
    for pos, (md_file, (html_file, label)) in enumerate(PAGES):
        md = (ROOT / md_file).read_text(encoding="utf-8")
        body = md_to_html(md)
        title = page_title(md, label)
        nav = "\n".join(
            f'<a href="./{h}" class="{"active" if h == html_file else ""}">{html.escape(lb)}</a>'
            for _, (h, lb) in PAGES
        )
        pager = '<nav class="pager">'
        if pos > 0:
            ph, pl = PAGES[pos - 1][1]
            pager += f'<a href="./{ph}">← {html.escape(pl)}</a>'
        else:
            pager += "<span></span>"
        if pos < len(PAGES) - 1:
            nh, nl = PAGES[pos + 1][1]
            pager += f'<a href="./{nh}">{html.escape(nl)} →</a>'
        pager += "</nav>"
        page = TEMPLATE_HEAD.format(
            title=html.escape(title), site=html.escape(SITE_TITLE), nav=nav
        ) + body + TEMPLATE_FOOT.format(pager=pager)
        (SITE / html_file).write_text(page, encoding="utf-8")
        headings = re.findall(r"^#{2,3}\s+(.*)", md, flags=re.M)
        entries.append({
            "title": title, "url": f"./{html_file}", "label": label,
            "headings": [re.sub(r"[*`]", "", h).strip() for h in headings],
            "text": strip_md(md)[:6000],
        })
    (SITE / "search-index.json").write_text(
        json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    for asset in ("style.css", "app.js"):
        src = SRC / asset
        if src.exists():
            (SITE / asset).write_bytes(src.read_bytes())
    print(f"Готово: {len(entries)} страниц в {SITE}")


if __name__ == "__main__":
    build()

