"""
generate_summary_report.py — Snakemake script
Generate HTML pipeline run summary report.
"""
import csv, os
from collections import Counter
from datetime import datetime

species_report = snakemake.input.species_report
subsp_assign   = snakemake.input.subsp_assign
dcc_summary    = snakemake.input.dcc_summary
pairs_csv      = snakemake.input.pairs_all
out_html       = snakemake.output.html

species_text = open(species_report).read() if os.path.exists(species_report) else "Not available"

subsp_counts = Counter()
try:
    with open(subsp_assign) as f:
        for row in csv.DictReader(f, delimiter='\t'):
            subsp_counts[row.get('Subspecies','unknown')] += 1
except:
    pass

dcc_counts = Counter()
try:
    with open(dcc_summary) as f:
        for row in csv.DictReader(f, delimiter='\t'):
            dcc_counts[row.get('DCC','unknown')] = int(row.get('Count',0))
except:
    pass

pairs_10 = pairs_20 = 0
try:
    with open(pairs_csv) as f:
        for row in csv.DictReader(f):
            t = row.get('Threshold','')
            if '<=10' in t: pairs_10 += 1
            else: pairs_20 += 1
except:
    pass

html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>Pipeline Summary</title>
<style>
:root{{--bg:#0a0e1a;--panel:#111827;--border:#1e2d45;--text:#c8d8f0;--muted:#5a7a9a;--accent:#3b82f6}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--text);font-family:sans-serif;padding:32px;max-width:900px;margin:0 auto}}
h1{{font-family:monospace;font-size:14px;font-weight:600;color:var(--accent);letter-spacing:.1em;text-transform:uppercase;margin-bottom:4px}}
h2{{font-family:monospace;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin:24px 0 8px}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:6px;overflow:hidden;margin-bottom:24px}}
.stat{{background:var(--panel);padding:16px;text-align:center}}
.stat-val{{font-family:monospace;font-size:28px;font-weight:600;color:var(--accent)}}
.stat-lbl{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px;font-family:monospace}}
th{{background:#2C3E50;color:#fff;padding:8px 12px;text-align:left}}
td{{padding:6px 12px;border-bottom:1px solid var(--border)}}
pre{{background:var(--panel);padding:12px;border-radius:4px;font-size:10px;color:var(--muted);overflow-x:auto;border:1px solid var(--border)}}
.footer{{margin-top:32px;font-size:10px;color:var(--muted);font-family:monospace}}
</style></head><body>
<h1>M. abscessus DCC Pipeline Summary</h1>
<p style="font-size:10px;color:var(--muted);margin-bottom:24px">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
<div class="grid">
  <div class="stat"><div class="stat-val">{sum(subsp_counts.values())}</div><div class="stat-lbl">Total isolates</div></div>
  <div class="stat"><div class="stat-val">{subsp_counts.get('abscessus',0)}</div><div class="stat-lbl">M. a. abscessus</div></div>
  <div class="stat"><div class="stat-val">{subsp_counts.get('massiliense',0)}</div><div class="stat-lbl">M. a. massiliense</div></div>
  <div class="stat"><div class="stat-val">{subsp_counts.get('bolletii',0)}</div><div class="stat-lbl">M. a. bolletii</div></div>
</div>
<div class="grid">
  <div class="stat"><div class="stat-val">{len([d for d in dcc_counts if 'Non-DCC' not in d])}</div><div class="stat-lbl">DCCs identified</div></div>
  <div class="stat"><div class="stat-val">{dcc_counts.get('Non-DCC',0)}</div><div class="stat-lbl">Non-DCC isolates</div></div>
  <div class="stat"><div class="stat-val">{pairs_10}</div><div class="stat-lbl">Pairs &le;10 SNPs</div></div>
  <div class="stat"><div class="stat-val">{pairs_10+pairs_20}</div><div class="stat-lbl">Pairs &le;20 SNPs</div></div>
</div>
<h2>DCC Distribution</h2>
<table>
<tr><th>DCC</th><th>Isolates</th></tr>
{''.join(f"<tr><td>{dcc}</td><td>{n}</td></tr>" for dcc,n in sorted(dcc_counts.items()))}
</table>
<h2>Species Report</h2>
<pre>{species_text}</pre>
<div class="footer">
  mab-dcc-pipeline | Ruis et al. 2021, Bronson et al. 2021, Dedrick et al.<br>
  github.com/cmoyer-x/mab-dcc-pipeline
</div>
</body></html>"""

os.makedirs(os.path.dirname(out_html), exist_ok=True)
with open(out_html, 'w') as f:
    f.write(html)
print("Summary report written")
