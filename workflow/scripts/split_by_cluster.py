"""
split_by_cluster.py — Snakemake script
Split core alignment by FastBAPS cluster for Gubbins.
"""
import os, csv
from collections import defaultdict
from Bio import SeqIO

aln_file  = snakemake.input.aln
clust_file= snakemake.input.clusters
outdir    = snakemake.params.outdir
min_seqs  = int(snakemake.params.min_seqs)
done_file = snakemake.output.done

os.makedirs(outdir, exist_ok=True)

seqs = {r.id: r for r in SeqIO.parse(aln_file, 'fasta')}

clusters = {}
with open(clust_file) as f:
    for row in csv.reader(f):
        if len(row) >= 2:
            clusters[row[0]] = row[1]

cluster_seqs = defaultdict(list)
for name, seq in seqs.items():
    cluster_seqs[clusters.get(name, 'unknown')].append(seq)

written = 0
for cluster, seqs_list in cluster_seqs.items():
    if len(seqs_list) < min_seqs:
        print(f"  Cluster {cluster}: {len(seqs_list)} seqs — skipped")
        continue
    outfile = os.path.join(outdir, f'cluster_{cluster}.fasta')
    SeqIO.write(seqs_list, outfile, 'fasta')
    print(f"  Cluster {cluster}: {len(seqs_list)} seqs -> {outfile}")
    written += 1

with open(done_file, 'w') as f:
    f.write(f"{written} clusters written\n")
