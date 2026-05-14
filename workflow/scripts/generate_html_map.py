"""
generate_html_map.py — Snakemake script
Generate interactive D3 global transmission map.
"""
import csv, json, re, os

abs_csv  = snakemake.input.abs_csv
mas_csv  = snakemake.input.mas_csv
out_html = snakemake.output.html

# Handle locations input robustly
loc_file = ""
try:
    locs = snakemake.input.locations
    if isinstance(locs, str) and locs:
        loc_file = locs
    elif hasattr(locs, '__iter__'):
        items = list(locs)
        if items:
            loc_file = str(items[0])
except:
    loc_file = ""

print(f"Locations file: '{loc_file}'")

# Load location data
locations = {}
if loc_file and os.path.exists(loc_file):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(loc_file)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            if row[0] and row[1]:
                gd = re.match(r'(GD\d+)', str(row[0]))
                if gd:
                    locations[gd.group(1)] = str(row[1]).strip()
        print(f"Loaded {len(locations)} locations")
    except Exception as e:
        print(f"Warning: could not load locations: {e}")

# Load DCC assignments
dcc_map = {}
for fpath, subsp in [(abs_csv,'abscessus'),(mas_csv,'massiliense')]:
    try:
        with open(fpath) as f:
            for row in csv.DictReader(f):
                dcc_map[row['Isolate']] = {'dcc':row['DCC'],'subsp':subsp}
    except:
        pass

# Institution to coordinates mapping
INST_COORDS = {
    'Australia': [-25.2744, 133.7751],
    'New Zealand': [-40.9006, 174.8860],
    'UK': [51.5074, -0.1278],
    'USA': [37.0902, -95.7129],
    'Canada': [56.1304, -106.3468],
    'France': [46.2276, 2.2137],
    'Netherlands': [52.1326, 5.2913],
    'Germany': [51.1657, 10.4515],
    'Italy': [41.8719, 12.5674],
    'Spain': [40.4637, -3.7492],
    'Israel': [31.0461, 34.8516],
    'Ireland': [53.4129, -8.2439],
    'Finland': [61.9241, 25.7482],
    'Switzerland': [46.8182, 8.2275],
    'Singapore': [1.3521, 103.8198],
    'Taiwan': [23.6978, 120.9605],
    'Turkey': [38.9637, 35.2433],
    'Latvia': [56.8796, 24.6032],
    'Portugal': [39.3999, -8.2245],
    'Slovakia': [48.6690, 19.6990],
}

def get_country(loc):
    loc_lower = loc.lower()
    if any(x in loc_lower for x in ['australia','westmead','sydney','melbourne','monash']):
        return 'Australia'
    if any(x in loc_lower for x in ['new zealand','auckland','nz']):
        return 'New Zealand'
    if any(x in loc_lower for x in ['uk','london','imperial','brompton','papworth','gosh','sheffield','glasgow']):
        return 'UK'
    if any(x in loc_lower for x in ['canada','vancouver','toronto','montreal','winnipeg','alberta','ontario']):
        return 'Canada'
    if any(x in loc_lower for x in ['france','paris','montpellier','bordeaux']):
        return 'France'
    if any(x in loc_lower for x in ['netherlands','haga','radboud']):
        return 'Netherlands'
    if any(x in loc_lower for x in ['germany','borstel','jena']):
        return 'Germany'
    if any(x in loc_lower for x in ['italy','gaslini','genoa']):
        return 'Italy'
    if any(x in loc_lower for x in ['spain','barcelona','madrid']):
        return 'Spain'
    if any(x in loc_lower for x in ['israel','hadassah']):
        return 'Israel'
    if any(x in loc_lower for x in ['ireland','dublin']):
        return 'Ireland'
    if any(x in loc_lower for x in ['finland','helsinki']):
        return 'Finland'
    if any(x in loc_lower for x in ['switzerland','lausanne']):
        return 'Switzerland'
    if any(x in loc_lower for x in ['singapore']):
        return 'Singapore'
    if any(x in loc_lower for x in ['taiwan']):
        return 'Taiwan'
    if any(x in loc_lower for x in ['turkey','hacettepe']):
        return 'Turkey'
    if any(x in loc_lower for x in ['latvia']):
        return 'Latvia'
    if loc:
        return 'USA'
    return 'Unknown'

# Build map data
from collections import defaultdict
country_dcc = defaultdict(lambda: defaultdict(int))

for iso, info in dcc_map.items():
    base = re.sub(r'[A-Z]$','', iso.replace('_WGS','').replace('_hybrid',''))
    loc = locations.get(iso, locations.get(base, ''))
    if loc:
        country = get_country(loc)
        if country != 'Unknown':
            country_dcc[country][info['dcc']] += 1

map_data = []
for country, dccs in country_dcc.items():
    if country in INST_COORDS:
        map_data.append({
            'country': country,
            'lat': INST_COORDS[country][0],
            'lon': INST_COORDS[country][1],
            'dccs': dccs,
            'total': sum(dccs.values())
        })

DCC_COLORS = {
    'DCC1':'#60a5fa','DCC2':'#34d399','DCC3':'#f97316','DCC4':'#a78bfa',
    'DCC5':'#fbbf24','DCC6':'#e11d48','DCC7':'#06b6d4',
    'Non-DCC':'#fb923c','Unknown':'#888888'
}

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>M. abscessus DCC Global Transmission Map</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
<style>
:root{{--bg:#0a0e1a;--panel:#111827;--border:#1e2d45;--text:#c8d8f0;--muted:#5a7a9a;--accent:#3b82f6}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:sans-serif;height:100vh;display:flex;flex-direction:column}}
header{{padding:10px 20px;background:var(--panel);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:16px}}
h1{{font-family:monospace;font-size:13px;font-weight:600;color:var(--accent);letter-spacing:.08em;text-transform:uppercase}}
#map{{flex:1;position:relative;overflow:hidden}}
svg{{width:100%;height:100%}}
.country{{fill:#1a2744;stroke:#0d1833;stroke-width:.3}}
.sphere{{fill:#060d1a}}
.graticule{{fill:none;stroke:#0f1d36;stroke-width:.2}}
.tooltip{{position:fixed;background:var(--panel);border:1px solid var(--border);border-radius:5px;
  padding:8px 12px;font-family:monospace;font-size:10px;color:var(--text);
  pointer-events:none;display:none;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.6);min-width:140px}}
.legend{{display:flex;gap:8px;flex-wrap:wrap}}
.legend-item{{display:flex;align-items:center;gap:4px;font-family:monospace;font-size:9px}}
.legend-dot{{width:8px;height:8px;border-radius:50%}}
.zoom-controls{{position:absolute;bottom:16px;left:16px;display:flex;flex-direction:column;gap:4px}}
.zoom-btn{{width:28px;height:28px;background:var(--panel);border:1px solid var(--border);
  color:var(--text);border-radius:4px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center}}
</style>
</head>
<body>
<header>
  <h1>M. abscessus — Global DCC Distribution</h1>
  <div class="legend" id="legend"></div>
</header>
<div id="map">
  <svg id="world"></svg>
  <div class="zoom-controls">
    <button class="zoom-btn" id="zi">+</button>
    <button class="zoom-btn" id="zo">−</button>
    <button class="zoom-btn" id="zr">⊙</button>
  </div>
  <div class="tooltip" id="tip"></div>
</div>
<script>
const DCC_COLORS = {json.dumps(DCC_COLORS)};
const MAP_DATA = {json.dumps(map_data)};

const svg = d3.select('#world');
const tip = document.getElementById('tip');
let w = document.getElementById('map').clientWidth;
let h = document.getElementById('map').clientHeight;
const proj = d3.geoNaturalEarth1().scale(w/6.5).translate([w/2, h/2]);
const pathGen = d3.geoPath().projection(proj);
const zoom = d3.zoom().scaleExtent([0.5,16]).on('zoom', e => g.attr('transform', e.transform));
svg.attr('viewBox', `0 0 ${{w}} ${{h}}`).call(zoom);
const g = svg.append('g');
g.append('path').datum({{type:'Sphere'}}).attr('class','sphere').attr('d',pathGen);
g.append('path').datum(d3.geoGraticule()()).attr('class','graticule').attr('d',pathGen);
const gC = g.append('g'), gM = g.append('g');

fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
  .then(r => r.json()).then(world => {{
    gC.selectAll('path')
      .data(topojson.feature(world, world.objects.countries).features)
      .join('path').attr('class','country').attr('d',pathGen);

    // Draw pie charts for each country
    MAP_DATA.forEach(d => {{
      const [x, y] = proj([d.lon, d.lat]);
      if (!x || !y) return;
      const r = Math.max(8, Math.min(25, Math.sqrt(d.total) * 4));
      const entries = Object.entries(d.dccs);
      const total = d.total;
      let angle = -Math.PI/2;
      const grp = gM.append('g').attr('transform', `translate(${{x}},${{y}})`);
      entries.forEach(([dcc, count]) => {{
        const sweep = (count/total) * 2 * Math.PI;
        const arc = d3.arc().innerRadius(0).outerRadius(r)
          .startAngle(angle).endAngle(angle + sweep);
        grp.append('path').attr('d', arc())
          .attr('fill', DCC_COLORS[dcc] || '#888')
          .attr('stroke', '#0a0e1a').attr('stroke-width', 0.5)
          .attr('opacity', 0.9);
        angle += sweep;
      }});
      grp.append('circle').attr('r', r).attr('fill','none')
        .attr('stroke','#ffffff').attr('stroke-width',0.8).attr('opacity',0.4);

      // Tooltip
      grp.on('mouseover', (e) => {{
        tip.style.display = 'block';
        tip.style.left = (e.clientX+12)+'px';
        tip.style.top = (e.clientY-8)+'px';
        let html = `<b style="color:var(--accent)">${{d.country}}</b><br><span style="color:var(--muted)">${{d.total}} isolates</span><br>`;
        Object.entries(d.dccs).sort((a,b)=>b[1]-a[1]).forEach(([dcc,n])=>{{
          html += `<span style="color:${{DCC_COLORS[dcc]||'#888'}}">&#11044;</span> ${{dcc}}: ${{n}}<br>`;
        }});
        tip.innerHTML = html;
      }}).on('mouseleave', () => tip.style.display='none');
    }});
  }});

// Legend
const leg = document.getElementById('legend');
Object.entries(DCC_COLORS).forEach(([dcc, color]) => {{
  if (dcc === 'Unknown') return;
  const el = document.createElement('div'); el.className='legend-item';
  el.innerHTML=`<div class="legend-dot" style="background:${{color}}"></div><span>${{dcc}}</span>`;
  leg.appendChild(el);
}});

document.getElementById('zi').addEventListener('click',()=>svg.transition().call(zoom.scaleBy,1.8));
document.getElementById('zo').addEventListener('click',()=>svg.transition().call(zoom.scaleBy,0.56));
document.getElementById('zr').addEventListener('click',()=>svg.transition().call(zoom.transform,d3.zoomIdentity));
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(out_html), exist_ok=True)
with open(out_html, 'w') as f:
    f.write(html)
print(f"HTML map written: {len(dcc_map)} isolates, {len(map_data)} countries")
