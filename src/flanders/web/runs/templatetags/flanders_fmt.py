from django import template

register = template.Library()


@register.filter
def sci(value):
    """p/q in scientific notation, two significant figures (3.1e-09)."""
    if value is None or value == "":
        return "—"
    v = float(value)
    if v >= 0.01:
        return f"{v:.2g}"
    return f"{v:.1e}"


@register.filter
def dec2(value):
    return "—" if value is None else f"{float(value):.2f}"


@register.filter
def get(d, key):
    return d.get(key) if hasattr(d, "get") else None


@register.filter
def pct(value):
    return "—" if value is None else f"{100 * float(value):.1f}%"


@register.filter
def ratio(b, n):
    return "—" if not n else f"{b / n:.3f}"
