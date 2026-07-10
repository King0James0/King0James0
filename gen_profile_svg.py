from img2ascii_color import render_color, runs
import html, json, os
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(HERE, "stats.json"), encoding="utf-8") as f:
    STATS = json.load(f)

def uptime_str():
    start = datetime.fromisoformat(STATS["created_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    y, m, d = now.year - start.year, now.month - start.month, now.day - start.day
    if d < 0:
        m -= 1
        d += (now.replace(day=1) - timedelta(days=1)).day
    if m < 0:
        y -= 1
        m += 12
    return f"{y} years, {m} months, {d} days"

def fmt(n):
    return "[auto]" if n is None else f"{n:,}"

LOC = None
if STATS.get("loc_add") is not None and STATS.get("loc_del") is not None:
    LOC = STATS["loc_add"] - STATS["loc_del"]

ART_COLS = 77
INFO_W = 52
FONT_SIZE = 10
LINE_H = 12
CHAR_W = 6.02
PAD = 20

ART = render_color(ART_COLS, char_aspect=0.58, crop=(0.02, 0.0, 0.98, 1.0), contrast=2.2, gamma=0.9)

C = {
    "art": "#56d364",
    "hdr": "#ffa657",
    "lab": "#79c0ff",
    "dot": "#484f58",
    "val": "#e6edf3",
    "add": "#56d364",
    "del": "#f85149",
}

def field(label, value):
    left = f". {label}: "
    dots = "." * max(1, INFO_W - len(left) - len(value) - 1)
    return [(left, "lab"), (dots, "dot"), (" " + value, "val")]

def header(text):
    return [(text + " ", "hdr"), ("-" * max(1, INFO_W - len(text) - 1), "dot")]

def section(text):
    return [("- " + text + " ", "hdr"), ("-" * max(1, INFO_W - len(text) - 3), "dot")]

def field2(l1, v1, l2, v2, lw=32):
    rw = INFO_W - lw - 3
    left = f". {l1}: "
    d1 = "." * max(1, lw - len(left) - len(v1) - 1)
    right = f"{l2}: "
    d2 = "." * max(1, rw - len(right) - len(v2) - 1)
    return [(left, "lab"), (d1, "dot"), (" " + v1, "val"), (" | ", "val"),
            (right, "lab"), (d2, "dot"), (" " + v2, "val")]

def loc_row(net, add, dele):
    left = ". Lines of Code: "
    body = f"{net:,} ({add:,}++, {dele:,}--)"
    dots = "." * max(1, INFO_W - len(left) - len(body) - 1)
    return [(left, "lab"), (dots, "dot"), (f" {net:,} (", "val"),
            (f"{add:,}++", "add"), (", ", "val"), (f"{dele:,}--", "del"), (")", "val")]

info = [
    header("king0james0@github"),
    field("Host", "Self-Hosted AI Lab"),
    field("IDE", "Claude Code, VS Code, Agent Zero"),
    field("Interests.Dev", "coding, agent memory systems"),
    field("Interests.Sec", "cyber security, report systems"),
    field("Interests.Fin", "financial research, Solana"),
    [],
    field("Languages.Programming", "Python, Kotlin, JS, Bash"),
    field("Languages.Computer", "HTML, CSS, JSON, YAML"),
    field("Languages.Real", "English, Spanish"),
    [],
    section("Experience"),
    field("Agents", "multi-agent orchestration"),
    field("Retrieval", "hybrid RAG (FAISS+BM25+RRF)"),
    field("Scraping", "crypto, recruiting, real estate"),
    field("Automation", "agent swarms, web research, email"),
    field("Mobile", "Kotlin + Jetpack Compose"),
    field("Security", "STRIDE, IDS/DAST, red-team"),
    field("Evals", "GDPVal scoring, 9 GDP sectors"),
    [],
    section("Education"),
    field("Degrees", "M.S. Info Systems, B.S. IT"),
    field("Certs", "Security+, CCNA, Splunk"),
    [],
    section("Stack"),
    field("AI", "Claude Code, OpenAI API, Ollama, vLLM"),
    field("Web", "vivy_web, Camoufox, Playwright, SearXNG"),
    field("Infra", "Docker, Ubuntu, Git, SQLite, FAISS"),
    [],
    section("Public Repos"),
    field("a0-obsidian-plugin", "vault + canvas UI"),
    field("a0-github-plugin", "GitHub ops via gh"),
    field("a0-reranker", "memory recall reranking"),
    field("a0-gitnexus-plugin", "code-graph queries"),
    field("a0-worktree-plugin", "chat workdir isolation"),
    [],
    section("Contact"),
    field2("GitHub", "king0james0", "X", "@king0james0", lw=31),
    field2("Discord", "king0james0", "TG", "@king0james0", lw=31),
    [],
    section("GitHub Stats"),
    field2("Repos", f"{STATS['repos']} {{Contributed: {STATS.get('contributed', 0)}}}",
           "Stars", str(STATS["stars"])),
    field2("Commits", fmt(STATS["commits"]), "Followers", str(STATS["followers"])),
    loc_row(LOC or 0, STATS.get("loc_add") or 0, STATS.get("loc_del") or 0),
]

rows = max(len(ART), len(info))
pad_top = max(0, (rows - len(info)) // 2)

total_cols = ART_COLS + 2 + INFO_W
width = int(total_cols * CHAR_W + 2 * PAD)
height = rows * LINE_H + 2 * PAD

def esc(s):
    return html.escape(s, quote=False)

lines_svg = []
for i in range(rows):
    y = PAD + (i + 1) * LINE_H - 3
    spans = []
    consumed = 0
    if i < len(ART):
        for text, (r, g, b) in runs(ART[i]):
            spans.append(f'<tspan fill="rgb({r},{g},{b})">{esc(text)}</tspan>')
            consumed += len(text)
    spans.append(f'<tspan> {" " * (ART_COLS + 1 - consumed)}</tspan>')
    ii = i - pad_top
    if 0 <= ii < len(info):
        for text, cls in info[ii]:
            spans.append(f'<tspan fill="{C[cls]}">{esc(text)}</tspan>')
    lines_svg.append(
        f'<text x="{PAD}" y="{y}" xml:space="preserve" font-family="Consolas, Menlo, \'DejaVu Sans Mono\', monospace" '
        f'font-size="{FONT_SIZE}px">{"".join(spans)}</text>'
    )

svg = (
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
    f'viewBox="0 0 {width} {height}">\n'
    f'<rect width="{width}" height="{height}" rx="8" fill="#0d1117"/>\n'
    + "\n".join(lines_svg)
    + "\n</svg>\n"
)

out_svg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.svg")
with open(out_svg, "w", encoding="utf-8") as f:
    f.write(svg)

readme = '<img src="profile.svg" alt="king0james0 profile card" width="100%">\n'
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

print(f"svg: {width}x{height}, {rows} rows, art {len(ART)} rows")
