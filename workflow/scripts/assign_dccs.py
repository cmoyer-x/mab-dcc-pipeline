"""
assign_dccs.py — Snakemake script
Assign isolates to DCCs using FastBAPS clusters + SNP distances.
"""
import pandas as pd
import csv
import math
from collections import Counter

abs_dists    = snakemake.input.abs_dists
mas_dists    = snakemake.input.mas_dists
abs_clusters = snakemake.input.abs_clusters
mas_clusters = snakemake.input.mas_clusters
out_abs      = snakemake.output.abs_csv
out_mas      = snakemake.output.mas_csv
out_summary  = snakemake.output.summary
threshold    = int(snakemake.params.dcc_threshold)

RUIS_REFS = {
    'SRR36966619':'DCC1','ERR363247':'DCC2','ERR1045629':'DCC3',
    'ERR1081288':'DCC4','ERR494841':'DCC4',
    'ERR363431':'DCC5','ERR484982':'DCC5',
    'ERR2524314':'DCC6','A47':'DCC6',
    'ERR363320':'DCC7','FLAC047':'DCC7',
}

ALL_REFS = set(RUIS_REFS.keys()) | {'Reference'}

def get_dist(df, ref, iso):
    try:
        if ref in df.index and iso in df.columns:
            v = df.loc[ref, iso]
        elif iso in df.index and ref in df.columns:
            v = df.loc[iso, ref]
        else:
            return None
        return None if (v is None or (isinstance(v,float) and math.isnan(v))) else int(v)
    except:
        return None

def assign(dist_file, cluster_file, subspecies, dcc_list):
    df = pd.read_csv(dist_file, sep='\t', index_col=0)
    gd = [c for c in df.columns if c not in ALL_REFS]

    clusters = {}
    with open(cluster_file) as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                clusters[row[0]] = row[1]

    ref_clusters = {}
    for ref, dcc in RUIS_REFS.items():
        if ref in clusters:
            ref_clusters[ref] = (clusters[ref], dcc)

    level1_dcc = {}
    for ref, (l1, dcc) in ref_clusters.items():
        if dcc in dcc_list:
            if l1 not in level1_dcc:
                level1_dcc[l1] = dcc

    results = []
    for iso in gd:
        l1 = clusters.get(iso, 'unknown')
        dcc_by_cluster = level1_dcc.get(l1)

        dists = {}
        for ref, dcc in RUIS_REFS.items():
            if dcc not in dcc_list:
                continue
            d = get_dist(df, ref, iso)
            if d is not None:
                if dcc not in dists or d < dists[dcc]:
                    dists[dcc] = d

        if dcc_by_cluster:
            dcc_assign = dcc_by_cluster
        elif dists:
            closest = min(dists, key=dists.get)
            dcc_assign = closest if dists[closest] <= threshold else 'Non-DCC'
        else:
            dcc_assign = 'Non-DCC'

        results.append({
            'Isolate': iso,
            'Subspecies': subspecies,
            'DCC': dcc_assign,
            'FastBAPS_Level1': l1,
            'Distance_to_DCC': dists.get(dcc_assign, ''),
        })
    return results

abs_results = assign(abs_dists, abs_clusters, 'M. a. abscessus',
                     ['DCC1','DCC2','DCC4','DCC5'])
mas_results = assign(mas_dists, mas_clusters, 'M. a. massiliense',
                     ['DCC3','DCC6','DCC7'])

with open(out_abs, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=abs_results[0].keys())
    w.writeheader(); w.writerows(abs_results)

with open(out_mas, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=mas_results[0].keys())
    w.writeheader(); w.writerows(mas_results)

all_results = abs_results + mas_results
counts = Counter(r['DCC'] for r in all_results)
with open(out_summary, 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['DCC','Count'])
    for dcc, n in sorted(counts.items()):
        w.writerow([dcc, n])

print(f"DCC assignments: {len(all_results)} isolates")
for dcc, n in sorted(counts.items()):
    print(f"  {dcc}: {n}")
