# M. abscessus DCC Assignment Pipeline

A Snakemake workflow for assigning clinical *Mycobacterium abscessus* isolates to Dominant Circulating Clones (DCCs 1–7) and identifying transmission pairs from whole genome sequencing data.

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/cmoyer-x/mab-dcc-pipeline
cd mab-dcc-pipeline

# 2. Install Snakemake
conda install -n base -c conda-forge -c bioconda snakemake

# 3. Place input FASTAs in input/assemblies/
cp /path/to/your/*.fasta input/assemblies/

# 4. Dry run to preview steps
snakemake --cores 16 --use-conda --dry-run

# 5. Run pipeline
snakemake --cores 16 --use-conda
```

## Pipeline Overview
Input FASTAs
│
▼
[1] MASH species ID     → Non-abscessus excluded, logged
│
▼
[2] MASH subspecies     → abscessus / massiliense / bolletii
│
▼
[3] Snippy SNP calling  → per subspecies reference
│
▼
[4] snippy-core         → core SNP alignment
│
▼
[5] FastBAPS            → population structure clusters
│
▼
[6] Gubbins             → recombination removal per cluster
│
▼
[7] snp-dists           → pairwise SNP distances
│
▼
[8] DCC assignment      → DCC1-7 + Non-DCC
│
▼
[9] RAxML trees         → GTR+GAMMA + 100 bootstraps
│
▼
[10] Outputs            → Excel + HTML map + heatmaps
## Outputs

All outputs written to results/final/:

| File | Description |
|------|-------------|
| DCC_assignments_FINAL.xlsx | Per-isolate DCC assignments |
| transmission_pairs_FINAL.xlsx | Pairs ≤10 and ≤20 SNPs |
| DCC_transmission_map.html | Interactive global map |
| DCC_SNP_heatmaps.html | Per-DCC SNP distance heatmaps |
| pipeline_summary.html | Run summary report |
| trees/abscessus/RAxML_bipartitions.* | Abscessus tree for iTOL |
| trees/massiliense/RAxML_bipartitions.* | Massiliense tree for iTOL |

## Requirements

| Tool | Version | Purpose |
|------|---------|---------|
| Snakemake | ≥7.0 | Workflow manager |
| Mash | ≥2.0 | Species/subspecies ID |
| Snippy | 4.6.0 | SNP calling |
| FastBAPS | 1.0.8 | Population structure |
| Gubbins | ≥3.3 | Recombination removal |
| RAxML | ≥8.2 | Phylogenetic trees |
| snp-dists | ≥0.8 | SNP distances |
| Python | ≥3.8 | Analysis scripts |

## References

- Ruis et al. 2021 — Nature Microbiology. PMC8478660
- Bronson et al. 2021 — PMC8390669
- Dedrick et al. — PMC10583746

## Author

Casey Moyer — University of Pittsburgh  
GitHub: cmoyer-x
