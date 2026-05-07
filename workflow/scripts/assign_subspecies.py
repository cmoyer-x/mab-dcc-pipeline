"""
assign_subspecies.py — Snakemake script
Assign M. abscessus samples to abscessus/massiliense/bolletii.
"""
import os, pandas as pd

distance_files = snakemake.input.distances
threshold = float(snakemake.params.threshold)

with open(snakemake.input.abscessus_list) as f:
    abs_samples = set(f.read().splitlines())

SUBSPECIES_MAP = {
    'ATCC19977':'abscessus','CU458896':'abscessus',
    'CIP_108297':'massiliense','GCF_001792625':'massiliense',
    'CCUG_50184':'bolletii','GCF_000701545':'bolletii',
}

results = []
subsp_lists = {'abscessus':[],'massiliense':[],'bolletii':[]}

for dist_file in distance_files:
    sample = os.path.basename(dist_file).replace('.tsv','')
    if sample not in abs_samples:
        continue
    if not os.path.exists(dist_file) or os.path.getsize(dist_file)==0:
        continue
    try:
        df = pd.read_csv(dist_file, sep='\t', header=None,
                         names=['ref','query','dist','p','hashes'])
        df['subspecies'] = df['ref'].apply(
            lambda x: next((v for k,v in SUBSPECIES_MAP.items() if k in x), 'unknown'))
        best = df.loc[df['dist'].idxmin()]
        subsp, dist = best['subspecies'], best['dist']
        results.append({'Sample':sample,'Subspecies':subsp,
                        'MASH_distance':round(dist,5)})
        if subsp in subsp_lists:
            subsp_lists[subsp].append(sample)
    except Exception as e:
        print(f"Warning: {dist_file}: {e}")

pd.DataFrame(results).to_csv(snakemake.output.assignments, sep='\t', index=False)
with open(snakemake.output.abs_list,'w') as f:
    f.write('\n'.join(subsp_lists['abscessus']))
with open(snakemake.output.mas_list,'w') as f:
    f.write('\n'.join(subsp_lists['massiliense']))
with open(snakemake.output.bol_list,'w') as f:
    f.write('\n'.join(subsp_lists['bolletii']))

print(f"Subspecies: {len(subsp_lists['abscessus'])} abscessus, "
      f"{len(subsp_lists['massiliense'])} massiliense, "
      f"{len(subsp_lists['bolletii'])} bolletii")
