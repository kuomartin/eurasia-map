"""Hand-drawn variant: same geography and markers as build.py, with loosened coastlines and sketched mountains."""
import math
import random
import sys
import shapefile
from shapely.geometry import shape, Polygon, LineString
from build import xy, land_union, CAPITALS, X0, Y0, X1, Y1

rng = random.Random(7)

def wobble_ring(coords, step=0.6, amp=0.28):
    """Resample a ring evenly, push points along the normal by smooth noise, then Chaikin-smooth."""
    ring = LineString(coords)
    n = max(12, int(ring.length / step))
    pts = [ring.interpolate(i / n, normalized=True) for i in range(n)]
    pts = [(p.x, p.y) for p in pts]
    waves = [(rng.uniform(0.15, 0.6), rng.uniform(0, 2 * math.pi), rng.uniform(0.4, 1.0)) for _ in range(3)]
    out = []
    for i, (x, y) in enumerate(pts):
        ax, ay = pts[i - 1]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        d = math.hypot(dx, dy) or 1
        s = i * step
        off = amp * sum(w * math.sin(f * s + ph) for f, ph, w in waves) / 2
        out.append((x - dy / d * off, y + dx / d * off))
    for _ in range(2):
        nxt = []
        for i in range(len(out)):
            (x0, y0), (x1, y1) = out[i], out[(i + 1) % len(out)]
            nxt += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        out = nxt
    return out

def ring_d(coords):
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in coords) + "Z"

def coast_d(land):
    out = []
    for p in land.geoms:
        if p.area < 0.15 or in_taiwan_box(p):  # islets too small to read; Taiwan is drawn by taiwan_d
            continue
        p = p.simplify(0.45, preserve_topology=True)
        out.append(ring_d(wobble_ring(p.exterior.coords)))
        out.extend(ring_d(wobble_ring(i.coords)) for i in p.interiors)
    out.append(taiwan_d())
    return "".join(out)

TAIWAN_BOX = Polygon([(119.9, 21.8), (122.2, 21.8), (122.2, 25.4), (119.9, 25.4)])

def taiwan_d():
    """Taiwan's outline in the base map is a few vertices; use Natural Earth 10m land instead."""
    r = shapefile.Reader("data/land/ne_10m_land")
    parts = []
    for s in r.shapes():
        if s.bbox[0] > 122.2 or s.bbox[2] < 119.9 or s.bbox[1] > 25.4 or s.bbox[3] < 21.8:
            continue
        g = shape(s.__geo_interface__)
        parts += [p for p in getattr(g, "geoms", [g]) if p.intersects(TAIWAN_BOX)]
    island = max(parts, key=lambda p: p.area)
    ring = [xy(lon, lat) for lon, lat in island.exterior.coords]
    ring = LineString(ring).simplify(0.06).coords
    return ring_d(wobble_ring(ring, step=0.22, amp=0.05))

def in_taiwan_box(p):
    x0, y0 = xy(119.9, 25.4)
    x1, y1 = xy(122.2, 21.8)
    c = p.centroid
    return x0 < c.x < x1 and y0 < c.y < y1

def himalaya_spine(n):
    r = shapefile.Reader("data/regions/ne_50m_geography_regions_polys")
    poly = next(shape(s.__geo_interface__) for s, rec in zip(r.shapes(), r.records()) if rec["NAME"] == "HIMALAYAS")
    lon0, _, lon1, _ = poly.bounds
    pts = []
    for i in range(n):
        lon = lon0 + (lon1 - lon0) * (i + 0.5) / n
        seg = poly.intersection(LineString([(lon, -90), (lon, 90)]))
        if not seg.is_empty:
            _, la, _, lb = seg.bounds
            pts.append(xy(lon, (la + lb) / 2))
    return pts

def mountain(x, y, h):
    """A sketched peak: white body, two slightly bowed flanks, and a zigzag snowline."""
    w = h * rng.uniform(0.85, 1.05)
    px, py = x + rng.uniform(-0.12, 0.12) * w, y - h
    lx, rx = x - w, x + w
    body = (f'M{lx:.2f},{y:.2f}Q{(lx + px) / 2 + 0.08 * h:.2f},{(y + py) / 2 - 0.05 * h:.2f} {px:.2f},{py:.2f}'
            f'Q{(rx + px) / 2 - 0.08 * h:.2f},{(y + py) / 2 - 0.05 * h:.2f} {rx:.2f},{y:.2f}')
    t = rng.uniform(0.32, 0.4)
    (ax, ay), (bx, by) = (px + (lx - px) * t, py + h * t), (px + (rx - px) * t, py + h * t)
    snow = (f'M{ax:.2f},{ay:.2f}L{ax + (bx - ax) * 0.3:.2f},{ay + 0.22 * h:.2f}'
            f'L{ax + (bx - ax) * 0.55:.2f},{ay + 0.06 * h:.2f}L{ax + (bx - ax) * 0.78:.2f},{ay + 0.2 * h:.2f}L{bx:.2f},{by:.2f}')
    return f'<path class="m" d="{body}Z"/><path d="{body}{snow}"/>'

def mountains():
    avoid = [xy(lon, lat) for lat, lon in CAPITALS.values()]
    spine = himalaya_spine(7)
    front = [(x + rng.uniform(-0.4, 0.4), y + 0.6, rng.uniform(2.2, 2.8)) for x, y in spine]
    # Back row sits in the gaps between front peaks
    back = [((ax + bx) / 2 + rng.uniform(-0.3, 0.3), (ay + by) / 2 - 1.2, rng.uniform(1.7, 2.2)) for (ax, ay), (bx, by) in zip(spine, spine[1:])]
    items = [(x, y, h) for x, y, h in back + front if all(math.hypot(x - ax, y - h / 2 - ay) > h + 1.9 for ax, ay in avoid)]
    items.sort(key=lambda t: t[1])  # draw back to front
    return "".join(mountain(*t) for t in items)

def capital(x, y, R=1.3):
    """Hand-drawn capital mark: a ring drawn in one stroke that overshoots its start, around an uneven dot."""
    ph = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    def r_at(a, base, amp):
        return base * (1 + amp * (math.sin(2 * a + ph[0]) + 0.6 * math.sin(3 * a + ph[1])))
    a0 = rng.uniform(0, 2 * math.pi)
    n = 40
    turn = 2 * math.pi * 1.12
    ring = []
    for i in range(n + 1):
        a = a0 + turn * i / n
        rr = r_at(a, R, 0.05) * (1 + 0.07 * i / n)
        ring.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    disc = [(x + r_at(a, R * 0.5, 0.08) * math.cos(a), y + r_at(a, R * 0.5, 0.08) * math.sin(a))
            for a in (2 * math.pi * i / 24 + ph[2] for i in range(24))]
    back = ring_d([(x + R * 1.08 * math.cos(2 * math.pi * i / 24), y + R * 1.08 * math.sin(2 * math.pi * i / 24)) for i in range(24)])
    line = "M" + "L".join(f"{px:.2f},{py:.2f}" for px, py in ring)
    return f'<path class="m" d="{back}"/><path fill="none" d="{line}"/><path fill="#000000" stroke="none" d="{ring_d(disc)}"/>'

def main():
    land = land_union()
    crop = Polygon([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)])
    land = land.intersection(crop.buffer(3))
    land = land if hasattr(land, "geoms") else type("M", (), {"geoms": [land]})
    vw, vh = X1 - X0, Y1 - Y0
    dots = "".join(capital(*xy(lon, lat)) for lat, lon in CAPITALS.values())
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{vw * 10:.0f}" height="{vh * 10:.0f}" viewBox="{X0:.3f} {Y0:.3f} {vw:.3f} {vh:.3f}">
<style>.m{{fill:#ffffff;stroke:none}}</style>
<rect x="{X0:.3f}" y="{Y0:.3f}" width="{vw:.3f}" height="{vh:.3f}" fill="#d4d4d4"/>
<path id="land" fill="#ffffff" stroke="#000000" stroke-width="0.4" stroke-linejoin="round" stroke-linecap="round" fill-rule="evenodd" d="{coast_d(land)}"/>
<g id="himalayas" fill="none" stroke="#000000" stroke-width="0.28" stroke-linejoin="round" stroke-linecap="round">{mountains()}</g>
<g id="capitals" stroke="#000000" stroke-width="0.3" stroke-linecap="round" stroke-linejoin="round">{dots}</g>
</svg>
'''
    open(sys.argv[1], "w").write(svg)

if __name__ == "__main__":
    main()
