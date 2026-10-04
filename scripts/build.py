"""Afro-Eurasia location map (Wikimedia Commons, PD) → black-and-white map without borders, with Himalayas and 7th-century capitals."""
import sys
import shapefile
from shapely.geometry import shape, Polygon, LineString
from shapely.ops import unary_union
from shapely import affinity
from svgelements import SVG, Path

# Module:Location map/data/Afro-Eurasia: equirectangular, image bounds
W, H = 457.266, 307.0
LEFT, RIGHT, TOP, BOTTOM = -25.65, 180.0, 90.0, -48.15
KX, KY = W / (RIGHT - LEFT), H / (TOP - BOTTOM)

def xy(lon, lat):
    return (lon - LEFT) * KX, (TOP - lat) * KY

# Crop: Mediterranean to Japan
LON0, LON1, LAT0, LAT1 = -11.0, 147.0, 4.0, 56.0
X0, Y0 = xy(LON0, LAT1)
X1, Y1 = xy(LON1, LAT0)

CAPITALS = {  # (lat, lon)
    "Constantinople": (41.01, 28.98),
    "Chang'an": (34.27, 108.94),
    "Asuka": (34.47, 135.82),
    "Geumseong": (35.84, 129.21),
    "Rasa": (29.65, 91.13),
    "Medina": (24.47, 39.61),
}

def land_union():
    polys = []
    for el in SVG.parse("data/afro.svg").elements():
        if not isinstance(el, Path) or el.fill is None or el.fill.hex != "#fdfcea":
            continue
        for sub in el.as_subpaths():
            sp = Path(sub)
            n = max(8, int(sp.length(error=1e-2) * 4))
            pts = [(p.x, p.y) for p in (sp.point(i / n) for i in range(n + 1))]
            if len(pts) >= 4:
                pg = Polygon(pts).buffer(0)
                if not pg.is_empty:
                    polys.append(pg)
    # Close hairline gaps between neighbouring country polygons
    eps = 0.08
    land = unary_union([p.buffer(eps, join_style=2) for p in polys]).buffer(-eps, join_style=2)
    # Drop leftover slivers between countries; real inland seas (Caspian, Black Sea) are far larger
    return unary_union([Polygon(p.exterior, [i for i in p.interiors if Polygon(i).area > 1]) for p in land.geoms])

def ring_d(coords):
    return "M" + "L".join(f"{x:.3f},{y:.3f}" for x, y in coords) + "Z"

def geom_d(g):
    parts = getattr(g, "geoms", [g])
    out = []
    for p in parts:
        out.append(ring_d(p.exterior.coords))
        out.extend(ring_d(i.coords) for i in p.interiors)
    return "".join(out)

def himalaya_peaks():
    r = shapefile.Reader("data/regions/ne_50m_geography_regions_polys")
    poly = next(shape(s.__geo_interface__) for s, rec in zip(r.shapes(), r.records()) if rec["NAME"] == "HIMALAYAS")
    lon0, _, lon1, _ = poly.bounds
    peaks = []
    n = 9
    for i in range(n):
        lon = lon0 + (lon1 - lon0) * (i + 0.5) / n
        seg = poly.intersection(LineString([(lon, -90), (lon, 90)]))
        if seg.is_empty:
            continue
        _, la, _, lb = seg.bounds
        peaks.append(xy(lon, (la + lb) / 2))
    return peaks

def mountain(x, y, s=1.9):
    return f'<path d="M{x - s:.3f},{y + s * 0.55:.3f}L{x:.3f},{y - s * 0.75:.3f}L{x + s:.3f},{y + s * 0.55:.3f}Z"/>'

def main():
    land = land_union()
    crop = Polygon([(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)])
    land = land.intersection(crop.buffer(2))
    vw, vh = X1 - X0, Y1 - Y0
    peaks = "".join(mountain(x, y) for x, y in himalaya_peaks())
    dots = "".join(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="1.25"/>' for x, y in (xy(lon, lat) for lat, lon in CAPITALS.values()))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{vw * 10:.0f}" height="{vh * 10:.0f}" viewBox="{X0:.3f} {Y0:.3f} {vw:.3f} {vh:.3f}">
<rect x="{X0:.3f}" y="{Y0:.3f}" width="{vw:.3f}" height="{vh:.3f}" fill="#d4d4d4"/>
<path id="land" fill="#ffffff" stroke="#000000" stroke-width="0.3" stroke-linejoin="round" fill-rule="evenodd" d="{geom_d(land)}"/>
<g id="himalayas" fill="#ffffff" stroke="#000000" stroke-width="0.3" stroke-linejoin="round">{peaks}</g>
<g id="capitals" fill="#000000">{dots}</g>
</svg>
'''
    open(sys.argv[1], "w").write(svg)

if __name__ == "__main__":
    main()
