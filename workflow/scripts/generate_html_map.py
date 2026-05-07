"""
generate_html_map.py — Snakemake script
Generate interactive D3 global transmission map.
"""
import csv, json, re, os
from collections import defaultdict

abs_csv   = snakemake.input.abs_csv
mas_csv   = snakemake.input.mas_csv
loc_file  = snakemake.input.locations
out_html  = snakemake.output.html

# Load location data if available
locations = {}
if loc_file and loc_file != "" and os.path.exists(loc_file):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(loc_file)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            if row[0] and row[1]:
                gd = re.match(r'(GD\d+)', str(row[0]))
                if gd:
                    locations[gd.group(1)] = str(row[1]).strip()
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

DCC_COLORS = {
    'DCC1':'#60a5fa','DCC2':'#34d399','DCC3':'#f97316','DCC4':'#a78bfa',
    'DCC5':'#fbbf24','DCC6':'#e11d48','DCC7':'#06b6d4',
    'Non-DCC':'#fb923c','Unknown':'#888888'
}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>M. abscessus DCC Global Transmission Map</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/topojson/3.0.2/topojson.min.js"></script>
<style>
:root{--bg:#0a0e1a;--panel:#111827;--border:#1e2d45;--text:#c8d8f0;--muted:#5a7a9a;--accent:#3b82f6}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:sans-serif;height:100vh;display:flex;flex-direction:column}
header{padding:10px 20px;background:var(--panel);border-bottom:1px solid var(--border)}
h1{font-family:monospace;font-size:13px;font-weight:600;color:var(--accent);letter-spacing:.08em;text-transform:uppercase}
#map{flex:1;overflow:hidden}
svg{width:100%;height:100%}
.country{fill:#1a2744;stroke:#0d1833;stroke-width:.3}
.sphere{fill:#060d1a}
.graticule{fill:none;stroke:#0f1d36;stroke-width:.2}
.tooltip{position:fixed;background:var(--panel);border:1px solid var(--border);border-radius:5px;
  padding:8px 12px;font-family:monospace;font-size:10px;color:var(--text);
  pointer-events:none;display:none;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.6)}
.legend{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.legend-item{display:flex;align-items:center;gap:4px;font-family:monospace;font-size:9px}
.legend-dot{width:8px;height:8px;border-radius:50%}
.zoom-controls{position:absolute;bottom:16px;left:16px;display:flex;flex-direction:column;gap:4px}
.zoom-btn{width:28px;height:28px;background:var(--panel);border:1px solid var(--border);
  color:var(--text);border-radius:4px;cursor:pointer;font-size:14px}
</style>
</head>
<body>
<header>
  <h1>M. abscessus — Global DCC Distribution</h1>
  <div class="legend" id="legend"></div>
</header>
<div id="map" style="position:relative">
  <svg id="world"></svg>
  <div class="zoom-controls">
    <button class="zoom-btn" id="zi">+</button>
    <button class="zoom-btn" id="zo">−</button>
    <button class="zoom-btn" id="zr">⊙</button>
  </div>
  <div class="tooltip" id="tip"></div>
</div>
<script>
const DCC_COLORS=""" + json.dumps(DCC_COLORS) + """;
const svg=d3.select('#world');
const tip=document.getElementById('tip');
let w=document.getElementById('map').clientWidth;
let h=document.getElementById('map').clientHeight;
const proj=d3.geoNaturalEarth1().scale(w/6.5).translate([w/2,h/2]);
let pathGen=d3.geoPath().projection(proj);
const zoom=d3.zoom().scaleExtent([0.8,16]).on('zoom',(e)=>{g.attr('transform',e.transform);});
svg.attr('viewBox',`0 0 ${w} ${h}`).call(zoom);
const g=svg.append('g');
g.append('path').datum({type:'Sphere'}).attr('class','sphere').attr('d',pathGen);
g.append('path').datum(d3.geoGraticule()()).attr('class','graticule').attr('d',pathGen);
const gC=g.append('g'),gM=g.append('g');
fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
  .then(r=>r.json()).then(world=>{
    gC.selectAll('path')
      .data(topojson.feature(world,world.objects.countries).features)
      .join('path').attr('class','country').attr('d',pathGen);
  });
// Legend
const leg=document.getElementById('legend');
Object.entries(DCC_COLORS).forEach(([dcc,color])=>{
  const el=document.createElement('div');el.className='legend-item';
  el.innerHTML=`<div class="legend-dot" style="background:${color}"></div><span>${dcc}</span>`;
  leg.appendChild(el);
});
document.getElementById('zi').addEventListener('click',()=>svg.transition().call(zoom.scaleBy,1.8));
document.getElementById('zo').addEventListener('click',()=>svg.transition().call(zoom.scaleBy,0.56));
document.getElementById('zr').addEventListener('click',()=>svg.transition().call(zoom.transform,d3.zoomIdentity));
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(out_html), exist_ok=True)
with open(out_html, 'w') as f:
    f.write(html)
print(f"HTML map written: {len(dcc_map)} isolates")
