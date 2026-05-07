# M. abscessus DCC Assignment Pipeline

A Snakemake workflow for assigning clinical *Mycobacterium abscessus* isolates to Dominant Circulating Clones (DCCs 1–7) and identifying transmission pairs from whole genome sequencing data.

## Background

*Mycobacterium abscessus* is a rapidly growing nontuberculous mycobacterium (NTM) and an increasingly important opportunistic pathogen, particularly in patients with cystic fibrosis (CF), bronchiectasis, and other chronic lung diseases. It is notoriously difficult to treat due to intrinsic and acquired antibiotic resistance.

### What are Dominant Circulating Clones (DCCs)?

Genomic epidemiology studies have revealed that *M. abscessus* infections are not solely acquired from the environment. Instead, a significant proportion of infections are caused by a small number of highly transmissible lineages that circulate globally among susceptible patients — these are called **Dominant Circulating Clones (DCCs)**.

DCCs were formally defined by [Ruis et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8478660/) as genomic clusters containing isolates from **at least 20 patients across multiple continents**, identified through whole genome sequencing of over 2,000 clinical isolates. Seven DCCs (DCC1–7) were identified:

| DCC | Subspecies | Geographic spread | Key features |
|-----|-----------|------------------|--------------|
| DCC1 | *M. a. abscessus* | Global — 4 continents | Largest and most widespread |
| DCC2 | *M. a. abscessus* | 3 continents | — |
| DCC3 | *M. a. massiliense* | 3 continents | Massiliense lineage |
| DCC4 | *M. a. abscessus* | 3 continents | — |
| DCC5 | *M. a. abscessus* | 4 continents | Highly dispersed |
| DCC6 | *M. a. massiliense* | Multi-continental | Massiliense lineage |
| DCC7 | *M. a. massiliense* | Multi-continental | Massiliense lineage |

> **Important:** DCC6 and DCC7 are *M. a. massiliense* lineages — not abscessus as sometimes assumed. This was confirmed by SNP distance analysis against subspecies reference genomes in the development of this pipeline.

Understanding which DCC a patient's isolate belongs to has important clinical implications — it can inform infection control decisions, identify likely transmission routes, and distinguish patient-to-patient transmission from independent environmental acquisition.

### Transmission pairs

Within each DCC, isolates that are highly similar (≤10–20 SNPs after recombination removal) are considered **putative transmission pairs** — patients who likely shared the same strain through direct or indirect contact. This pipeline identifies these pairs at two thresholds:
- **≤10 SNPs** — likely direct transmission (Ruis et al. 2021)
- **≤20 SNPs** — probable transmission cluster (Bronson et al. 2021)

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

> **Note:** All reference genomes and DCC anchor sequences are downloaded automatically on first run. This requires internet access and approximately 3–4GB of storage. Subsequent runs skip the download step entirely.

## Pipeline Overview

| Step | Tool | Description |
|------|------|-------------|
| 0a | Python | Input validation — checks FASTA format, file sizes, isolate count |
| 0b | wget | Download subspecies references (ATCC19977, CIP_108297, CCUG_50184) |
| 0c | wget | Download DCC anchor sequences (SRR36966619, ERR363247, etc.) |
| 1 | MASH | Species identification — non-*M. abscessus* excluded and logged |
| 2 | MASH | Subspecies assignment → abscessus / massiliense / bolletii |
| 3 | Snippy | SNP calling against subspecies reference genome |
| 4 | snippy-core | Core SNP alignment per subspecies including DCC references |
| 5 | FastBAPS | Population structure clustering — assigns isolates to lineages |
| 6 | Gubbins | Recombination removal per FastBAPS cluster — **required before SNP distances** |
| 7 | snp-dists | Pairwise SNP distances from Gubbins-filtered alignments |
| 8 | Custom | DCC assignment → DCC1–7 + Non-DCC (500 SNP threshold) |
| 9 | RAxML | Phylogenetic trees — GTR+GAMMA + 100 bootstraps |
| 10 | Custom | Outputs — Excel spreadsheets + interactive HTML map |

### Why Gubbins is critical

*M. abscessus* undergoes frequent recombination — horizontal gene transfer events that introduce large blocks of foreign DNA which appear as clusters of SNPs. Without removing these recombinant regions, SNP distances between isolates are artificially inflated, leading to:

- **False negatives** — genuine transmission pairs that appear too distant
- **False positives** — unrelated isolates that appear close due to shared recombination events

Gubbins identifies and masks recombinant regions per FastBAPS cluster, producing a **recombination-free SNP alignment** that accurately reflects vertical evolutionary history. All transmission pair calls (≤10 and ≤20 SNPs) are made from these filtered alignments, exactly matching the methodology of Ruis et al. 2021.

## Input Validation

The pipeline automatically validates all input files before starting. It will:

- **Fail with an error** if fewer than 5 isolates are provided
- **Warn** if fewer than 20 isolates are provided — FastBAPS and RAxML require sufficient diversity to produce meaningful results
- **Warn** if fewer than 50 isolates are provided — recommended minimum for reliable DCC assignment
- **Warn** if any FASTA file is smaller than 500KB — may indicate an incomplete assembly
- **Fail with an error** if any FASTA file is empty or malformed

Example warning for small datasets:
```
[mab-dcc-pipeline] WARNING: Only 15 isolates found. FastBAPS clustering and
RAxML trees require at least 20-50 isolates for meaningful results.
```

## Automatic Reference Downloads

On first run the pipeline automatically downloads all required references:

**Subspecies references** (downloaded to `references/subspecies/`):

| File | Strain | Accession | Purpose |
|------|--------|-----------|---------|
| ATCC19977.fasta | *M. a. abscessus* | GCF_000069185.1 | SNP calling reference |
| CIP_108297.fasta | *M. a. massiliense* | GCF_001792625.1 | SNP calling reference |
| CCUG_50184.fasta | *M. a. bolletii* | GCF_000701545.1 | SNP calling reference |

**DCC anchor sequences** (downloaded to `results/dcc_refs/`):

| Accession | DCC | Source |
|-----------|-----|--------|
| SRR36966619 | DCC1 | Ruis et al. 2021 |
| ERR363247 | DCC2 | Ruis et al. 2021 |
| ERR1045629 | DCC3 | Ruis et al. 2021 |
| ERR1081288 + ERR494841 | DCC4 | Ruis + Dedrick et al. |
| ERR363431 + ERR484982 | DCC5 | Ruis + Dedrick et al. |
| ERR2524314 + A47 | DCC6 | Ruis + Dedrick et al. |
| ERR363320 + FLAC047 | DCC7 | Ruis + Dedrick et al. |

> If your server has no internet access, download these files on a local machine and transfer them manually to the paths above.

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

## Cohort-level vs Global Analysis

### Unbiased cohort analysis (default)

By default this pipeline is designed for **unbiased clinical cohort analysis** — you provide all isolates from your patient population and the pipeline assigns them to DCCs without any pre-selection. This approach:
- Captures the true diversity of *M. abscessus* circulating in your patient population
- Identifies Non-DCC lineages that may represent novel or emerging clones
- Avoids the sampling bias introduced by deliberately including only known DCC representatives
- Produces a higher proportion of Non-DCC isolates than published global datasets — this is expected and biologically meaningful, not a methodological flaw

### Adding global reference genomes (biased toward known DCCs)

To anchor your analysis to the global DCC framework more tightly, you can supplement your cohort with publicly available isolates from published studies. This approach is useful when:
- You want to formally validate Non-DCC clusters against the full global dataset
- You are proposing a new DCC and need multi-continental evidence
- You want to compare your cohort directly against Ruis et al. 2021 figures

To add global genomes, download SRA accessions from published studies and place them in `input/assemblies/` alongside your cohort isolates. Key public datasets:

| Study | Accessions | N isolates | Notes |
|-------|-----------|-----------|-------|
| Ruis et al. 2021 | ERP017141 | 2,045 | Primary DCC definition dataset |
| Bronson et al. 2021 | PRJNA648717 | ~200 | North American cohort |
| Dedrick et al. | PRJNA738526 | 90 | Lab paper reference strains |

> **Warning:** Adding global genomes significantly increases runtime. Consider downloading only the DCC representative strains rather than the full dataset.

### Interpreting Non-DCC isolates

Non-DCC isolates are not sequencing failures. They represent:
1. **Genuinely distinct lineages** — phylogenetically intermediate between defined DCCs
2. **Locally circulating clones** — lineages with active transmission within your cohort not yet sampled globally at sufficient scale to meet formal DCC criteria
3. **Independent environmental acquisitions** — isolates acquired directly from environmental sources

A cluster of Non-DCC isolates meeting ≥10 isolates from ≥2 countries at the 500 SNP threshold should be considered a **candidate novel DCC**.

## Notes on Test Datasets

When running on small test datasets (<20 isolates) RAxML tree building is automatically skipped. A minimum of ~50 isolates is recommended for meaningful phylogenetic trees.

DCC reference sequences (~3–4GB) are downloaded automatically on first run. If your server has no internet access download the references on a local machine and transfer them to `results/dcc_refs/`.

## References

- **Ruis et al. 2021** — Dissemination of *Mycobacterium abscessus* via global transmission networks. *Nature Microbiology*. [PMC8478660](https://pmc.ncbi.nlm.nih.gov/articles/PMC8478660/)
- **Bronson et al. 2021** — Global phylogenomic analyses of *M. abscessus*. [PMC8390669](https://pmc.ncbi.nlm.nih.gov/articles/PMC8390669/)
- **Dedrick et al.** — Phage therapy of *Mycobacterium* infections. [PMC10583746](https://pmc.ncbi.nlm.nih.gov/articles/PMC10583746/)

## Author

Casey Moyer — University of Pittsburgh, Phage Genomics and Bioinformatics
GitHub: [cmoyer-x](https://github.com/cmoyer-x)
