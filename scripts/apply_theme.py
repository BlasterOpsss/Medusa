"""Theme step: restyle index.html with the Medusa JF-4 look (pale aqua-white ground, deep teal ink,
one coral accent, JetBrains Mono labels, Inter for display text, square translucent cards).

Run AFTER scripts/build_frontend.py (the build patches anchor on the original dark palette):

    python3 scripts/build_frontend.py && python3 scripts/apply_theme.py

It decodes the template inside index.html, rewrites colours / fonts / radii, injects the theme CSS
and background layers, and encodes it back the same way. A marker keeps it from running twice.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "index.html")
MARK = "/*medusa-theme*/"

INK, MID, FAINT, LINE = "#0e3a3d", "#5d8284", "#9dbcbc", "#d3e8e7"
CORAL, TEAL, AQUA, BG, BG2 = "#ff5a3c", "#0f9d8a", "#46c9bf", "#f1fbfa", "#e3f4f3"
RED, AMBER = "#d93a2b", "#d98a00"

# literal strings first (most specific), then hex, then rgba
SPECIAL = [
    # primary buttons: green fill + dark text -> coral fill + white text
    ("background:#00c805;color:#04140a", f"background:{CORAL};color:#fffffe"),
    ("background:#19dd1f", "background:#ff7258"),
    # brand mark in the header: coral block with white line-drawn icon
    ('style="display:flex;align-items:center;gap:10px;color:#e8ecef;font-family:\'JetBrains Mono\',monospace;font-size:15px;font-weight:600;letter-spacing:-0.01em"',
     f'style="display:flex;align-items:center;gap:12px;color:#fffffe;background:{CORAL};height:64px;padding:0 22px;font-family:\'JetBrains Mono\',monospace;font-size:14px;font-weight:600;letter-spacing:-0.01em"'),
    ('<g stroke="#9fd9ff" stroke-opacity="0.75"', '<g stroke="#fffffe" stroke-opacity="0.85"'),
    ('<g fill="#00c805"><circle cx="3"', '<g fill="#fffffe"><circle cx="3"'),
    ('rx="3" fill="#0f1a14" stroke="#00c805"', 'rx="3" fill="#ff5a3c" stroke="#fffffe"'),
    ('r="1.9" fill="#00c805" style="filter:drop-shadow(0 0 3px #00c805)"', 'r="1.9" fill="#fffffe"'),
    ("'Geist',Helvetica,Arial,sans-serif", "'Inter',Helvetica,Arial,sans-serif"),
]
HEX = {
    # grounds and surfaces
    "#07090b": BG, "#090c0f": "#fbfffe", "#0b1013": "#f7fdfc", "#0c1114": "#f4fbfa", "#0a0d10": "#f7fdfc",
    "#0b0f12": "#fbfffe", "#0d1317": "#f4fbfa", "#0a0e11": "#f7fdfc", "#0a120d": "#eefaf8", "#0f1a14": "#eefaf8",
    # hairlines
    "#141b20": LINE, "#12181c": LINE, "#11171b": LINE, "#10161a": LINE, "#121a1f": "#e6f3f2", "#131b20": LINE,
    "#151d22": LINE, "#151c21": LINE, "#1a2227": LINE, "#1c252b": "#c3dedc", "#1f2a30": "#c3dedc",
    "#262f35": "#b5d3d1", "#2c353b": "#b5d3d1", "#3a454c": FAINT,
    # text, brightest -> dimmest becomes ink -> faint
    "#eef1f3": INK, "#e8ecef": INK, "#dfe5e8": INK, "#ffffff": INK, "#fff": INK,
    "#c9d1d6": "#2f5a5d", "#aab4ba": "#3f6b6e", "#9aa5ab": "#3f6b6e",
    "#8a959c": MID, "#5f6b72": "#7a9c9d", "#4a555c": FAINT,
    # accents
    "#00c805": TEAL, "#19dd1f": "#12b09c", "#04140a": "#ffffff", "#d9ffd4": TEAL, "#dfffe0": "#ffffff",
    "#9fd9ff": CORAL,
    "#ff4d4d": RED, "#ff6b6b": RED, "#1a0707": "#ffffff",
    "#ffb020": AMBER, "#f5a623": AMBER, "#ff8a3d": "#ee7a22", "#f472b6": "#d4568f",
}
RGB = {
    "0,200,5": "15,157,138", "159,217,255": "255,90,60", "206,232,255": "255,90,60", "255,77,77": "217,58,43",
    "255,176,32": "217,138,0", "245,166,35": "217,138,0", "244,114,182": "212,86,143", "255,138,61": "238,122,34",
    "7,9,11": "241,251,250",
}

THEME_CSS = MARK + """
html,body{background:#f1fbfa;color:#0e3a3d;font-family:'JetBrains Mono',ui-monospace,monospace;-webkit-font-smoothing:antialiased}
a{color:#5d8284}a:hover{color:#ff5a3c}
input::placeholder{color:#9dbcbc}
::selection{background:rgba(255,90,60,.25);color:#0e3a3d}
h1,h2,h3{font-family:'Inter',Helvetica,Arial,sans-serif}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:#c3dedc}::-webkit-scrollbar-track{background:transparent}
"""

BACKDROP = (
    '<div style="position:fixed;inset:0;pointer-events:none;z-index:0;'
    'background:radial-gradient(90% 80% at 50% 42%,#fafefd 0%,#f1fbfa 55%,#e3f4f3 100%)"></div>\n'
    '  <svg aria-hidden="true" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMin slice" '
    'style="position:fixed;left:50%;top:6vh;width:150vmin;height:150vmin;transform:translateX(-50%);pointer-events:none;z-index:0;fill:none;stroke:#bcdcda;stroke-width:1">'
    '<circle cx="500" cy="500" r="190"/><circle cx="500" cy="500" r="270" stroke-dasharray="3 7"/>'
    '<circle cx="500" cy="500" r="350"/><circle cx="500" cy="500" r="430" stroke-dasharray="2 9"/>'
    '<circle cx="500" cy="500" r="490"/>'
    '<g fill="#ff5a3c" stroke="none"><circle cx="690" cy="500" r="3"/><circle cx="500" cy="150" r="3"/><circle cx="231" cy="635" r="3"/></g></svg>\n'
)


def encode(text):
    return "\n" + json.dumps(text, ensure_ascii=False).replace("</", "<\\u002F") + "\n  "


def theme_replay():
    """replay.html is a plain page with CSS variables: same palette, same map."""
    path = os.path.join(ROOT, "replay.html")
    r = open(path, encoding="utf-8").read()
    if MARK in r:
        return
    r = r.replace("family=Geist:wght@400;500;600", "family=Inter:wght@500;600;700")
    r = r.replace("--sans:'Geist'", "--sans:'Inter'")
    r = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", lambda mo: HEX.get(mo.group(0).lower(), mo.group(0)), r)
    r = re.sub(r"rgba\(([0-9 ]+,[0-9 ]+,[0-9 ]+),",
               lambda mo: f"rgba({RGB[mo.group(1).replace(' ', '')]}," if mo.group(1).replace(" ", "") in RGB else mo.group(0), r)
    r = r.replace("rgba(255,255,255,0.03)", "rgba(15,157,138,0.05)")
    r = re.sub(r"border-radius:(?:2|3|4|6|7|8|10|12|14)px", "border-radius:0", r)
    r = r.replace("</style>", MARK + "\nbody{background:radial-gradient(90% 80% at 50% 42%,#fafefd 0%,#f1fbfa 55%,#e3f4f3 100%) fixed}"
                  "\n::selection{background:rgba(255,90,60,.25)}\n</style>", 1)
    open(path, "w", encoding="utf-8").write(r)
    print("replay.html themed")


def main():
    src = open(PATH, encoding="utf-8").read()
    m = re.search(r'<script type="__bundler/template">', src)
    a = m.end(); b = src.find("</script>", a)
    raw = src[a:b]
    t = json.loads(raw)
    if encode(t) != raw:
        sys.exit("index.html: template format changed, encoder does not match - theme stopped")
    if MARK in t:
        sys.exit("theme already applied")

    # replace the three dark decorative layers (dot grid, green glow, blue glow) with the Medusa backdrop
    layers = re.findall(r'  <div style="position:fixed;[^\n]*?pointer-events:none;z-index:0;[^\n]*?</div>\n', t)
    if len(layers) != 3:
        sys.exit(f"expected 3 background layers, found {len(layers)}")
    t = t.replace(layers[0], "  " + BACKDROP, 1)
    for l in layers[1:]:
        t = t.replace(l, "", 1)

    for old, new in SPECIAL:
        if old not in t:
            sys.exit(f"anchor not found: {old[:60]!r}")
        t = t.replace(old, new)

    def hexsub(mo):
        return HEX.get(mo.group(0).lower(), mo.group(0))
    t = re.sub(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", hexsub, t)

    def rgbsub(mo):
        c = mo.group(1).replace(" ", "")
        return f"rgba({RGB[c]}," if c in RGB else mo.group(0)
    t = re.sub(r"rgba\(([0-9 ]+,[0-9 ]+,[0-9 ]+),", rgbsub, t)
    # whites/blacks used as overlays and shadows on the dark theme
    t = t.replace("rgba(255,255,255,0.03)", "rgba(15,157,138,0.05)").replace("rgba(255,255,255,0.06)", "rgba(15,157,138,0.09)")
    t = t.replace("rgba(0,0,0,0.45)", "rgba(40,110,110,0.16)").replace("rgba(0,0,0,0.5)", "rgba(40,110,110,0.18)")

    # square corners (pills 999px and circles 50% stay round)
    t = re.sub(r"border-radius:(?:2|3|4|6|7|8|10|12|14)px", "border-radius:0", t)

    # fonts: Inter next to the already embedded JetBrains Mono, theme CSS last so it wins
    fonts = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700'
             '&family=JetBrains+Mono:wght@400;500;600&display=swap">\n')
    t = t.replace("</helmet>", fonts + "<style>" + THEME_CSS + "</style>\n</helmet>", 1)

    t = t.replace("#fffffe", "#ffffff")
    out = src[:a] + encode(t) + src[b:]
    open(PATH, "w", encoding="utf-8").write(out)
    print("theme applied:", len(t), "chars")
    theme_replay()


if __name__ == "__main__":
    main()
