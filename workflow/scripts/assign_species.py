"""
assign_species.py — Snakemake script
Assign each sample to closest species from MASH distances.
"""
import os, pandas as pd
from collections import defaultdict

distance_files = snakemake.input.distances
threshold      = float(snakemake.params.threshold)

def ref_to_species(ref_path):
    name = os.path.basename(ref_path).replace('.fna','').replace('.fasta','')
    return name.replace('M_','M. ').replace('_',' ')

results, abscessus_samples, non_abscessus_samples = [], [], []

for dist_file in distance_files:
    sample = os.path.basename(dist_file).replace('.tsv','')
    if not os.path.exists(dist_file) or os.path.getsize(dist_file)==0:
        continue
    try:
        df = pd.read_csv(dist_file, sep='\t', header=None,
                         names=['ref','query','dist','p','hashes'])
        df['species'] = df['ref'].apply(ref_to_species)
        best = df.loc[df['dist'].idxmin()]
        species, dist = best['species'], best['dist']
        is_abs = 'abscessus' in species.lower() and dist <= threshold
        results.append({'Sample':sample,'Assigned_species':species,
                        'MASH_distance':round(dist,5),'Is_abscessus':is_abs})
        (abscessus_samples if is_abs else non_abscessus_samples).append(sample)
    except Exception as e:
        print(f"Warning: {dist_file}: {e}")

pd.DataFrame(results).to_csv(snakemake.output.assignments, sep='\t', index=False)
with open(snakemake.output.abscessus_list,'w') as f:
    f.write('\n'.join(abscessus_samples))
with open(snakemake.output.non_abscessus_list,'w') as f:
    f.write('\n'.join(non_abscessus_samples))

with open(snakemake.output.report,'w') as f:
    f.write(f"Species Assignment Report\n{'='*40}\n\n")
    f.write(f"Total: {len(results)}\n")
    f.write(f"M. abscessus: {len(abscessus_samples)}\n")
    f.write(f"Other: {len(non_abscessus_samples)}\n\n")
    if non_abscessus_samples:
        f.write("Non-abscessus excluded:\n")
        for r in results:
            if not r['Is_abscessus']:
                f.write(f"  {r['Sample']}: {r['Assigned_species']} ({r['MASH_distance']})\n")
