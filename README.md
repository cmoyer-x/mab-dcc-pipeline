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

| Step | Tool | Description |
|------|------|-------------|
| 1 | MASH | Species identification — non-*M. abscessus* excluded and logged |
| 2 | MASH | Subspecies assignment → abscessus / massiliense / bolletii |
| 3 | Snippy | SNP calling against subspecies reference genome |
| 4 | snippy-core | Core SNP alignment per subspecies |
| 5 | FastBAPS | Population structure clustering |
| 6 | Gubbins | Recombination removal per cluster |
| 7 | snp-dists | Pairwise SNP distance matrices |
| 8 | Custom | DCC assignment → DCC1–7 + Non-DCC (500 SNP threshold) |
| 9 | RAxML | Phylogenetic trees — GTR+GAMMA + 100 bootstraps |
| 10 | Custom | Outputs — Excel spreadsheets + interactive HTML map |

## Outputs

All outputs written to `results/final/`:

| File | Description |
|------|-------------|
| `DCC_assignments_FINAL.xlsx` | Per-isolate DCC assignments with transmission partners |
| `transmission_pairs_FINAL.xlsx` | Pairs ≤10 SNPs and ≤20 SNPs |
| `DCC_transmission_map.html` | Interactive global map |
| `pipeline_summary.html` | Run summary report |
| `trees/abscessus/RAxML_bipartitions.*` | Abscessus tree — upload to iTOL |
| `trees/massiliense/RAxML_bipartitions.*` | Massiliense tree — upload to iTOL |

## Requirements

All dependencies managed automatically via `--use-conda`.

| Tool | Version | Purpose |
|------|---------|---------|
| Snakemake | ≥7.0 | Workflow manager |
| Mash | ≥2.0 | Species and subspecies identification |
| Snippy | 4.6.0 | Reference-based SNP calling |
| FastBAPS | 1.0.8 | Population structure clustering |
| Gubbins | ≥3.3 | Recombination removal |
| RAxML | ≥8.2 | Maximum likelihood phylogenetic trees |
| snp-dists | ≥0.8 | Pairwise SNP distances |
| Python | ≥3.8 | Analysis and output scripts |

## Configuration

Edit `config.yaml` to set:
- Input/output directories
- Subspecies reference genomes
- DCC anchor accessions (Ruis et al. 2021 + Dedrick et al.)
- SNP thresholds (default: ≤10 strict, ≤20 broad, 500 DCC membership)
- Computational resources (cores, memory)

## DCC Reference Strains

| DCC | Subspecies | Reference | Source |
|-----|-----------|-----------|--------|
| DCC1 | *M. a. abscessus* | SRR36966619 | Ruis et al. 2021 |
| DCC2 | *M. a. abscessus* | ERR363247 | Ruis et al. 2021 |
| DCC3 | *M. a. massiliense* | ERR1045629 | Ruis et al. 2021 |
| DCC4 | *M. a. abscessus* | ERR1081288 + ERR494841 | Ruis + Dedrick et al. |
| DCC5 | *M. a. abscessus* | ERR363431 + ERR484982 | Ruis + Dedrick et al. |
| DCC6 | *M. a. massiliense* | ERR2524314 + A47 | Ruis + Dedrick et al. |
| DCC7 | *M. a. massiliense* | ERR363320 + FLAC047 | Ruis + Dedrick et al. |

> **Note:** DCC6 and DCC7 are *M. a. massiliense* lineages confirmed by SNP distance analysis.

## References

- **Ruis et al. 2021** — Dissemination of *Mycobacterium abscessus* via global transmission networks. *Nature Microbiology*. [PMC8478660](https://pmc.ncbi.nlm.nih.gov/articles/PMC8478660/)
- **Bronson et al. 2021** — Global phylogenomic analyses of *M. abscessus*. [PMC8390669](https://pmc.ncbi.nlm.nih.gov/articles/PMC8390669/)
- **Dedrick et al.** — Phage therapy of *Mycobacterium* infections. [PMC10583746](https://pmc.ncbi.nlm.nih.gov/articles/PMC10583746/)

## Author

Casey Moyer — University of Pittsburgh, Phage Genomics and Bioinformatics
GitHub: [cmoyer-x](https://github.com/cmoyer-x)
