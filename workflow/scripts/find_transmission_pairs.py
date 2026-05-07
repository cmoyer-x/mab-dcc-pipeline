"""
find_transmission_pairs.py — Snakemake script
Find transmission pairs at both SNP thresholds.
"""
import pandas as pd
import csv
import math
import os

abs_dists    = snakemake.input.abs_dists
mas_dists    = snakemake.input.mas_dists
abs_csv      = snakemake.input.abs_csv
mas_csv      = snakemake.input.mas_csv
out_combined = snakemake.output.combined
threshold_1  = int(snakemake.params.threshold_1)
threshold_2  = int(snakemake.params.threshold_2)

ALL_REFS = {'SRR36966619','ERR363247','ERR1045629','ERR1081288','ERR363431',
            'ERR2524314','ERR363320','ERR484982','ERR494841','A47','FLAC047','Reference'}

dcc_map = {}
for fpath in [abs_csv, mas_csv]:
    try:
        with open(fpath) as f:
            for row in csv.DictReader(f):
                dcc_map[row['Isolate']] = row['DCC']
    except:
        pass

all_pairs = []

for dist_file in [abs_dists, mas_dists]:
    if not os.path.exists(dist_file) or os.path.getsize(dist_file) == 0:
        continue
    try:
        df = pd.read_csv(dist_file, sep='\t', index_col=0)
        gd = [c for c in df.columns if c not in ALL_REFS]
        for i, iso1 in enumerate(gd):
            for iso2 in gd[i+1:]:
                try:
                    v = df.loc[iso1, iso2]
                    if v is None or (isinstance(v,float) and math.isnan(v)):
                        continue
                    dist = int(v)
                except:
                    continue
                if dist <= threshold_2:
                    label = f'<={threshold_1}' if dist <= threshold_1 \
                            else f'{threshold_1+1}-{threshold_2}'
                    all_pairs.append({
                        'Isolate1': iso1,
                        'Isolate2': iso2,
                        'SNP_distance': dist,
                        'Threshold': label,
                        'DCC': dcc_map.get(iso1, 'Unknown'),
                    })
    except Exception as e:
        print(f"Warning: {dist_file}: {e}")

all_pairs.sort(key=lambda x: x['SNP_distance'])

# Always write output file even if empty
os.makedirs(os.path.dirname(out_combined), exist_ok=True)
fieldnames = ['Isolate1','Isolate2','SNP_distance','Threshold','DCC']
with open(out_combined, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(all_pairs)

t1 = sum(1 for p in all_pairs if p['Threshold'].startswith('<='))
print(f"Pairs <={threshold_1} SNPs: {t1}")
print(f"Pairs <={threshold_2} SNPs: {len(all_pairs)}")
