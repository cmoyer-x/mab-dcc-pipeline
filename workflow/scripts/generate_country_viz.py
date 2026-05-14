"""
generate_country_viz.py — Snakemake script
Generate two-panel country x DCC visualization:
1. Stacked bar chart
2. Country x DCC heatmap
"""
import csv, json, re, os
from collections import defaultdict

abs_csv  = snakemake.input.abs_csv
mas_csv  = snakemake.input.mas_csv
loc_file = snakemake.input.get("locations", [])
out_html = snakemake.output.html

if isinstance(loc_file, str):
    loc_path = loc_file
elif hasattr(loc_file, '__iter__'):
    items = list(loc_file)
    loc_path = str(items[0]) if items else ""
else:
    loc_path = ""

locations = {}
if loc_path and os.path.exists(loc_path):
    try:
        import openpyxl
        wb = openpyxl.load_workbook(loc_path)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            if not row[0]: continue
            loc_val = None
            if len(row) >= 3 and row[2]:
                loc_val = str(row[2]).strip().replace('\xa0','')
            elif len(row) >= 2 and row[1]:
                loc_val = str(row[1]).strip().replace('\xa0','')
            gd = re.match(r'(GD\d+)', str(row[0]))
            if gd and loc_val and loc_val.lower() not in ('location','institution','disease','cf','non-cf'):
                locations[gd.group(1)] = loc_val
        print(f"Loaded {len(locations)} locations")
    except Exception as e:
        print(f"Warning: {e}")

def get_country(loc):
    l = loc.lower()
    if any(x in l for x in ['australia','westmead','sydney','melbourne','monash','john hunter','nsw']): return 'Australia'
    if any(x in l for x in ['new zealand','auckland','nz','christchurch']): return 'New Zealand'
    if any(x in l for x in ['u.k','uk','united kingdom','london','imperial','brompton','papworth','gosh','sheffield','glasgow','edinburgh','belfast']): return 'UK'
    if any(x in l for x in ['canada','vancouver','toronto','montreal','winnipeg','alberta','ontario','hamilton','halifax']): return 'Canada'
    if any(x in l for x in ['france','paris','montpellier','bordeaux','arnaud']): return 'France'
    if any(x in l for x in ['netherlands','haga','radboud']): return 'Netherlands'
    if any(x in l for x in ['germany','borstel','jena']): return 'Germany'
    if any(x in l for x in ['italy','gaslini','genoa','pisa']): return 'Italy'
    if any(x in l for x in ['spain','barcelona','madrid','mallorca']): return 'Spain'
    if any(x in l for x in ['israel','hadassah']): return 'Israel'
    if any(x in l for x in ['ireland','dublin']): return 'Ireland'
    if any(x in l for x in ['finland','helsinki','tampere']): return 'Finland'
    if any(x in l for x in ['switzerland','lausanne','chuv']): return 'Switzerland'
    if any(x in l for x in ['singapore']): return 'Singapore'
    if any(x in l for x in ['taiwan']): return 'Taiwan'
    if loc: return 'USA'
    return 'Unknown'

dcc_map = {}
for fpath in [abs_csv, mas_csv]:
    try:
        with open(fpath) as f:
            for row in csv.DictReader(f):
                dcc_map[row['Isolate']] = row['DCC']
    except: pass

country_dcc = defaultdict(lambda: defaultdict(int))
for iso, dcc in dcc_map.items():
    base = re.sub(r'[A-Z]$','', iso.replace('_WGS','').replace('_hybrid','').replace('_1',''))
    loc = locations.get(iso, locations.get(base, ''))
    if loc:
        country = get_country(loc)
        if country != 'Unknown':
            country_dcc[country][dcc] += 1

raw_data = {k: dict(v) for k,v in country_dcc.items()}
raw_json = json.dumps(raw_data)
print(f"Countries: {len(raw_data)}, Total isolates: {sum(sum(v.values()) for v in raw_data.values())}")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>M. abscessus — DCC Distribution by Country</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
:root{{--bg:#0a0e1a;--panel:#111827;--border:#1e2d45;--text:#c8d8f0;--muted:#5a7a9a;--accent:#3b82f6}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:monospace;padding:24px}}
h1{{font-size:13px;font-weight:600;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;margin-bottom:20px}}
h2{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px}}
.section{{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:20px}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}}
.legend-item{{display:flex;align-items:center;gap:5px;font-size:10px;color:var(--text)}}
.legend-dot{{width:10px;height:10px;border-radius:2px;flex-shrink:0}}
.tooltip{{position:fixed;background:var(--panel);border:1px solid var(--border);border-radius:5px;
  padding:8px 12px;font-size:10px;color:var(--text);pointer-events:none;display:none;z-index:100;
  box-shadow:0 4px 20px rgba(0,0,0,.6);line-height:1.7;min-width:160px}}
</style>
</head>
<body>
<h1>M. abscessus — DCC Distribution Across Countries</h1>
<div class="tooltip" id="tip"></div>

<div class="section">
  <h2>Stacked bar chart — isolates per country by DCC</h2>
  <div class="legend" id="bar-legend"></div>
  <div style="position:relative;height:340px">
    <canvas id="barChart" role="img" aria-label="Stacked bar chart showing DCC distribution across countries">DCC isolate counts by country.</canvas>
  </div>
</div>

<div class="section">
  <h2>Country &times; DCC heatmap</h2>
  <div id="heatmap-wrap" style="overflow-x:auto"></div>
</div>

<script>
const RAW = {raw_json};
const DCC_COLORS = {{'DCC1':'#60a5fa','DCC2':'#34d399','DCC3':'#f97316','DCC4':'#a78bfa','DCC5':'#fbbf24','DCC6':'#e11d48','DCC7':'#06b6d4','Non-DCC':'#fb923c'}};
const DCCS = ['DCC1','DCC2','DCC3','DCC4','DCC5','DCC6','DCC7','Non-DCC'];
const countries = Object.keys(RAW).sort((a,b)=>
  Object.values(RAW[b]).reduce((s,v)=>s+v,0)-Object.values(RAW[a]).reduce((s,v)=>s+v,0));
const tip = document.getElementById('tip');

const leg = document.getElementById('bar-legend');
DCCS.forEach(dcc=>{{
  const el=document.createElement('div'); el.className='legend-item';
  el.innerHTML=`<span class="legend-dot" style="background:${{DCC_COLORS[dcc]}}"></span>${{dcc}}`;
  leg.appendChild(el);
}});

new Chart(document.getElementById('barChart'),{{
  type:'bar',
  data:{{labels:countries,datasets:DCCS.map(dcc=>({{'label':dcc,'data':countries.map(c=>RAW[c][dcc]||0),'backgroundColor':DCC_COLORS[dcc],'borderWidth':0}}))}},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{title:ctx=>ctx[0].label,label:ctx=>` ${{ctx.dataset.label}}: ${{ctx.raw}}`}}}}}},
    scales:{{
      x:{{stacked:true,ticks:{{color:'#5a7a9a',font:{{family:'monospace',size:11}},maxRotation:30,autoSkip:false}},grid:{{color:'#1e2d45'}}}},
      y:{{stacked:true,ticks:{{color:'#5a7a9a',font:{{family:'monospace',size:11}}}},grid:{{color:'#1e2d45'}}}}
    }}
  }}
}});

const CW=56,RH=32,LW=110,TH=72;
const maxVal=Math.max(...countries.flatMap(c=>DCCS.map(d=>RAW[c][d]||0)));
const hs=d3.select('#heatmap-wrap').append('svg')
  .attr('width',LW+DCCS.length*CW+50).attr('height',TH+countries.length*RH+20);

DCCS.forEach((dcc,j)=>{{
  const x=LW+j*CW+CW/2,y=TH-10;
  hs.append('rect').attr('x',LW+j*CW+4).attr('y',TH-16).attr('width',10).attr('height',10).attr('rx',2).attr('fill',DCC_COLORS[dcc]);
  hs.append('text').attr('x',x+2).attr('y',y).attr('text-anchor','start').attr('font-size',10).attr('fill','#c8d8f0')
    .attr('transform',`rotate(-45,${{x+2}},${{y}})`).text(dcc);
}});

countries.forEach((country,i)=>{{
  const y=TH+i*RH,rowTotal=Object.values(RAW[country]).reduce((s,v)=>s+v,0);
  hs.append('text').attr('x',LW-6).attr('y',y+RH/2+4).attr('text-anchor','end').attr('font-size',11).attr('fill','#c8d8f0').text(country);
  hs.append('text').attr('x',LW+DCCS.length*CW+12).attr('y',y+RH/2+4).attr('text-anchor','start').attr('font-size',10).attr('fill','#5a7a9a').text(rowTotal);
  DCCS.forEach((dcc,j)=>{{
    const val=RAW[country][dcc]||0,alpha=val===0?0.04:0.15+(val/maxVal)*0.82,color=DCC_COLORS[dcc]||'#888';
    const cell=hs.append('g').style('cursor',val>0?'pointer':'default');
    cell.append('rect').attr('x',LW+j*CW+2).attr('y',y+3).attr('width',CW-4).attr('height',RH-6).attr('rx',3).attr('fill',color).attr('opacity',alpha);
    if(val>0) cell.append('text').attr('x',LW+j*CW+CW/2).attr('y',y+RH/2+4).attr('text-anchor','middle')
      .attr('font-size',val>9?11:10).attr('fill',alpha>0.55?'#000':color).text(val);
    cell.on('mouseover',(e)=>{{
      if(!val) return;
      tip.style.display='block'; tip.style.left=(e.clientX+12)+'px'; tip.style.top=(e.clientY-8)+'px';
      tip.innerHTML=`<b style="color:${{color}}">${{dcc}}</b><br>${{country}}: ${{val}} isolates<br><span style="color:var(--muted)">${{Math.round(val/rowTotal*100)}}% of country total</span>`;
    }}).on('mouseleave',()=>tip.style.display='none');
  }});
  hs.append('line').attr('x1',LW).attr('x2',LW+DCCS.length*CW).attr('y1',y).attr('y2',y).attr('stroke','#1e2d45').attr('stroke-width',.5);
}});
hs.append('text').attr('x',LW+DCCS.length*CW+12).attr('y',TH-10).attr('text-anchor','start').attr('font-size',10).attr('fill','#5a7a9a').text('n');
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(out_html), exist_ok=True)
with open(out_html, 'w') as f:
    f.write(html)
print(f"Country visualization written: {len(raw_data)} countries")
