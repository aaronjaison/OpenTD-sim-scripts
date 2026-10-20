"""Dependency-free SVG plot used in saved reports."""
from html import escape


def coordinates(samples, width=760, height=320):
    """Return plot coordinates with room for axes and a flat-series fallback."""
    times = [sample.time_s for sample in samples]
    temps = [sample.temperature_k for sample in samples]
    low, high = min(temps), max(temps)
    span = max(high - low, 1.0)
    duration = max(times[-1] - times[0], 1.0)
    return [(60 + (t-times[0])/duration*(width-90),
             height-45-(temp-low)/span*(height-80)) for t, temp in zip(times, temps)]


def svg(samples, title):
    """Render a sampled polyline; retain full precision in the separate CSV."""
    stride = max(1, len(samples) // 1000)
    selected = samples[::stride]
    if selected[-1] is not samples[-1]:
        selected = [*selected, samples[-1]]
    points = " ".join(f"{x:.2f},{y:.2f}" for x, y in coordinates(selected))
    low = min(row.temperature_k for row in samples)
    high = max(row.temperature_k for row in samples)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="760" height="320" viewBox="0 0 760 320">
<rect width="760" height="320" fill="#101c2e"/>
<g font-family="sans-serif" fill="#e8eff7" font-size="12">
<text x="60" y="23">{escape(title)}</text>
<text x="8" y="48">{high:.2f} K</text><text x="8" y="275">{low:.2f} K</text>
<text x="60" y="303">{samples[0].time_s:g} s</text>
<text x="670" y="303">{samples[-1].time_s:g} s</text></g>
<path d="M60 35 V275 H730" fill="none" stroke="#61748c"/>
<polyline points="{points}" fill="none" stroke="#55d6be" stroke-width="2"/>
</svg>'''
