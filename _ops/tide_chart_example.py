"""Print the inline SVG tide curve used in how-to-read-a-tide-chart.html.

Data: NOAA CO-OPS predictions, station 9414290 (San Francisco, Golden Gate), 5 November 2026,
MLLW, feet, local time, 15-minute and high/low intervals. Re-run with network access and paste
the output between the <!-- tide-svg --> comments if the example date ever changes.
"""
import json
import urllib.request

API = 'https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions&application=seawindow_site&begin_date=20261105&end_date=20261106&datum=MLLW&station=9414290&time_zone=lst_ldt&units=english&format=json&interval='
curve = json.load(urllib.request.urlopen(API + '15'))['predictions'][:97]
events = json.load(urllib.request.urlopen(API + 'hilo'))['predictions']
events = [e for e in events if e['t'].startswith('2026-11-05')]
W, H, L, R, T, B = 680, 320, 52, 16, 28, 44
LO, HI = -1.0, 7.0
x = lambda minutes: L + (W - L - R) * minutes / 1440
y = lambda ft: T + (H - T - B) * (HI - ft) / (HI - LO)
mins = lambda t: int(t[11:13]) * 60 + int(t[14:16]) + (1440 if t.startswith('2026-11-06') else 0)
pts = ' '.join(f'{x(mins(p["t"])):.1f},{y(float(p["v"])):.1f}' for p in curve)
out = [f'<svg class="tide-svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="tide-svg-title tide-svg-desc">',
       '<title id="tide-svg-title">Predicted tide, San Francisco (Golden Gate), 5 November 2026</title>',
       '<desc id="tide-svg-desc">Curve of NOAA predicted water level in feet above MLLW from midnight to midnight: low 0.9 ft at 1:47 AM, high 5.9 ft at 8:35 AM, low 0.7 ft at 2:48 PM, high 4.7 ft at 9:03 PM. Mean sea level is 3.1 ft above MLLW.</desc>']
for ft in (0, 2, 4, 6):
    out.append(f'<line class="grid" x1="{L}" x2="{W-R}" y1="{y(ft):.1f}" y2="{y(ft):.1f}"/><text class="axis" x="{L-8}" y="{y(ft)+5:.1f}" text-anchor="end">{ft} ft</text>')
for h, label in ((0, '12 AM'), (6, '6 AM'), (12, '12 PM'), (18, '6 PM'), (24, '12 AM')):
    anchor = 'start' if h == 0 else 'end' if h == 24 else 'middle'
    out.append(f'<text class="axis" x="{x(h*60):.1f}" y="{H-16}" text-anchor="{anchor}">{label}</text>')
out.append(f'<line class="msl" x1="{L}" x2="{W-R}" y1="{y(3.12):.1f}" y2="{y(3.12):.1f}"/><text class="note-label" x="{x(888):.1f}" y="{y(3.12)-6:.1f}" text-anchor="middle">Mean sea level</text>')
out.append(f'<text class="note-label" x="{W-R-4}" y="{y(0)-6:.1f}" text-anchor="end">0 = MLLW</text>')
out.append(f'<polyline class="curve" points="{pts}"/>')
for e in events:
    cx, cy, high = x(mins(e['t'])), y(float(e['v'])), e['type'] == 'H'
    hh, mm = int(e['t'][11:13]), e['t'][14:16]
    clock = f'{(hh % 12) or 12}:{mm} {"AM" if hh < 12 else "PM"}'
    label = f'{"High" if high else "Low"} {float(e["v"]):.1f} ft · {clock}'
    ty = cy - 12 if high else y(0) + 20  # lows sit below the 0 line so the grid never strikes through them
    anchor = 'start' if cx < 120 else 'end' if cx > W - 140 else 'middle'
    out.append(f'<circle class="{"hi" if high else "lo"}" cx="{cx:.1f}" cy="{cy:.1f}" r="5"/><text class="event" x="{cx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">{label}</text>')
out.append('</svg>')
print(''.join(out))
