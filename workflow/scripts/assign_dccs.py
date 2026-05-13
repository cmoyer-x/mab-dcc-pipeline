"""
assign_dccs.py — Snakemake script
Assign isolates to DCCs using FastBAPS clusters + SNP distances.
Uses distance-based tiebreaking when multiple DCCs share a cluster.
"""
import pandas as pd
import csv
import math
import os
from collections import Counter, defaultdict

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
    if not os.path.exists(dist_file) or os.path.getsize(dist_file) == 0:
        return []
    try:
        df = pd.read_csv(dist_file, sep='\t', index_col=0)
    except Exception as e:
        print(f"Could not parse {dist_file}: {e}")
        return []

    gd = [c for c in df.columns if c not in ALL_REFS]
    if not gd:
        return []

    # Load clusters
    clusters_l1 = {}
    clusters_l2 = {}
    if os.path.exists(cluster_file) and os.path.getsize(cluster_file) > 0:
        with open(cluster_file) as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) >= 3:
                    clusters_l1[row[0]] = row[1]
                    clusters_l2[row[0]] = row[2]
                elif len(row) >= 2:
                    clusters_l1[row[0]] = row[1]

    # Build cluster -> DCC map
    # Track which clusters have MULTIPLE DCCs (ambiguous)
    l1_dccs = defaultdict(set)
    for ref, dcc in RUIS_REFS.items():
        if dcc not in dcc_list: continue
        if ref in clusters_l1:
            l1_dccs[clusters_l1[ref]].add(dcc)

    # Single DCC per cluster = unambiguous
    l1_dcc_unique = {l1: list(dccs)[0] for l1, dccs in l1_dccs.items() if len(dccs)==1}
    # Multiple DCCs per cluster = ambiguous, use distance
    l1_dcc_ambig = {l1: dccs for l1, dccs in l1_dccs.items() if len(dccs)>1}

    print(f"\n{subspecies}:")
    print(f"  Unambiguous clusters: {l1_dcc_unique}")
    print(f"  Ambiguous clusters (will use distance): {dict(l1_dcc_ambig)}")

    results = []
    for iso in gd:
        l1 = clusters_l1.get(iso, 'unknown')
        l2 = clusters_l2.get(iso, 'unknown')

        if l1 in l1_dcc_unique:
            # Unambiguous cluster assignment
            dcc_assign = l1_dcc_unique[l1]
        elif l1 in l1_dcc_ambig:
            # Ambiguous cluster — use distance to closest ref
            candidate_dccs = l1_dcc_ambig[l1]
            dists = {}
            for ref, dcc in RUIS_REFS.items():
                if dcc not in candidate_dccs: continue
                d = get_dist(df, ref, iso)
                if d is not None:
                    if dcc not in dists or d < dists[dcc]:
                        dists[dcc] = d
            if dists:
                dcc_assign = min(dists, key=dists.get)
            else:
                dcc_assign = 'Non-DCC'
        else:
            # Not in any DCC cluster — distance fallback
            dists = {}
            for ref, dcc in RUIS_REFS.items():
                if dcc not in dcc_list: continue
                d = get_dist(df, ref, iso)
                if d is not None:
                    if dcc not in dists or d < dists[dcc]:
                        dists[dcc] = d
            if dists:
                closest = min(dists, key=dists.get)
                dcc_assign = closest if dists[closest] <= threshold else 'Non-DCC'
            else:
                dcc_assign = 'Non-DCC'

        results.append({
            'Isolate': iso,
            'Subspecies': subspecies,
            'DCC': dcc_assign,
            'FastBAPS_Level1': l1,
            'FastBAPS_Level2': l2,
        })
    return results

os.makedirs(os.path.dirname(out_abs), exist_ok=True)

abs_results = assign(abs_dists, abs_clusters, 'M. a. abscessus',
                     ['DCC1','DCC2','DCC4','DCC5'])
mas_results = assign(mas_dists, mas_clusters, 'M. a. massiliense',
                     ['DCC3','DCC6','DCC7'])

fieldnames = ['Isolate','Subspecies','DCC','FastBAPS_Level1','FastBAPS_Level2']
with open(out_abs, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(abs_results)

with open(out_mas, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader(); w.writerows(mas_results)

all_results = abs_results + mas_results
counts = Counter(r['DCC'] for r in all_results)
with open(out_summary, 'w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['DCC','Count'])
    for dcc, n in sorted(counts.items()):
        w.writerow([dcc, n])

print(f"\nDCC assignments: {len(all_results)} isolates")
for dcc, n in sorted(counts.items()):
    print(f"  {dcc}: {n}")
