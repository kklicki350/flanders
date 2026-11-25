"""Server-rendered SVG neighborhood map: gene arrows plus annotation tracks."""

from __future__ import annotations

from django.utils.html import escape
from django.utils.safestring import mark_safe

TRACKS = [
    ("antismash", "antiSMASH BGC", "var(--track-antismash)"),
    ("signal_peptide", "Signal peptide", "var(--track-sp)"),
    ("transmembrane", "Transmembrane", "var(--track-tm)"),
    ("pfam", "Pfam domain", "var(--track-pfam)"),
]


def _has(features: list[str], key: str) -> bool:
    return any(f == key or f.startswith(key + ":") for f in features)


def neighborhood(orfs: list[dict], selected_feature: str | None = None, width: int = 1100) -> str:
    if not orfs:
        return ""
    lo = min(o["start"] for o in orfs)
    hi = max(o["end"] for o in orfs)
    span = max(1, hi - lo)
    pad, arrow_y, arrow_h, track_h = 12, 30, 18, 10
    scale = (width - 2 * pad) / span
    tracks_top = arrow_y + arrow_h + 14
    height = tracks_top + len(TRACKS) * (track_h + 6) + 26

    def x(pos: int) -> float:
        return pad + (pos - lo) * scale

    parts = [f'<svg class="hood" viewBox="0 0 {width} {height}" width="100%" role="img" '
             f'aria-label="Gene neighborhood map">']
    # axis
    parts.append(f'<line x1="{pad}" y1="{arrow_y + arrow_h / 2}" x2="{width - pad}" y2="{arrow_y + arrow_h / 2}" class="axis"/>')
    for i, (key, label, color) in enumerate(TRACKS):
        y = tracks_top + i * (track_h + 6)
        parts.append(f'<text x="{pad}" y="{y + track_h - 1}" class="tracklabel">{escape(label)}</text>')
    for o in orfs:
        x1, x2 = x(o["start"]), x(o["end"])
        w = max(2.0, x2 - x1)
        head = min(10.0, w * 0.4)
        top, bot, mid = arrow_y, arrow_y + arrow_h, arrow_y + arrow_h / 2
        if o["strand"] == "+":
            pts = f"{x1},{top} {x1 + w - head},{top} {x1 + w},{mid} {x1 + w - head},{bot} {x1},{bot}"
        else:
            pts = f"{x1 + head},{top} {x1 + w},{top} {x1 + w},{bot} {x1 + head},{bot} {x1},{mid}"
        cls = "gene seed" if o["location"] == "seed" else "gene flank"
        if selected_feature and selected_feature in o["features"]:
            cls += " selected"
        tip = f"{o['orf_id']} · {o.get('product') or 'hypothetical'} · {o['start']}-{o['end']}({o['strand']})"
        if o["features"]:
            tip += " · " + ", ".join(o["features"])
        parts.append(f'<g tabindex="0" aria-label="{escape(tip)}"><title>{escape(tip)}</title>'
                     f'<polygon points="{pts}" class="{cls}"/></g>')
        for i, (key, _label, color) in enumerate(TRACKS):
            if _has(o["features"], key):
                y = tracks_top + i * (track_h + 6)
                parts.append(f'<rect x="{x1}" y="{y}" width="{w}" height="{track_h}" rx="2" '
                             f'style="fill:{color}"><title>{escape(o["orf_id"])}: '
                             f'{escape(", ".join(f for f in o["features"] if f.startswith(key)))}</title></rect>')
    # scale bar: 1 kb
    kb = 1000 * scale
    sy = height - 10
    parts.append(f'<line x1="{width - pad - kb}" y1="{sy}" x2="{width - pad}" y2="{sy}" class="scalebar"/>')
    parts.append(f'<text x="{width - pad - kb}" y="{sy - 4}" class="tracklabel">1 kb</text>')
    parts.append("</svg>")
    return mark_safe("".join(parts))  # noqa: S308 - every interpolated text value is escaped above
