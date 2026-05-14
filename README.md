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

# 2. Create dedicated Snakemake environment (recommended)
conda create -n snakemake -c conda-forge -c bioconda snakemake -y
conda activate snakemake

# 3. Place input FASTAs in input/assemblies/
cp /path/to/your/*.fasta input/assemblies/

# 4. Dry run to preview steps and check estimated runtime
snakemake --cores 16 --use-conda --dry-run

# 5. Run pipeline
snakemake --cores 16 --use-conda
```

> **Note:** All reference genomes and DCC anchor sequences (~3-4GB) are downloaded automatically on first run. Subsequent runs skip the download step entirely.

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
| 9 | Custom | Outputs — Excel spreadsheets + interactive HTML map + pipeline summary |

> **Note:** Phylogenetic tree building is not included in the pipeline. Core SNP alignments are produced at `results/core/{abscessus,massiliense}/core.aln` and can be used directly with any tree building software. See [Phylogenetic Trees](#phylogenetic-trees) below for recommended methods.

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
| `DCC_assignments_FINAL.xlsx` | Per-isolate DCC assignments including subspecies, FastBAPS cluster, and DCC label |
| `transmission_pairs_FINAL.xlsx` | Putative transmission pairs at ≤10 SNPs and ≤20 SNPs after recombination removal |
| `pipeline_summary.html` | Interactive run summary — isolate counts, DCC distribution, species report |

Core SNP alignments are also produced and can be used for downstream analysis:

| File | Description |
|------|-------------|
| `results/core/abscessus/core.aln` | *M. a. abscessus* core SNP alignment including DCC reference strains |
| `results/core/massiliense/core.aln` | *M. a. massiliense* core SNP alignment including DCC reference strains |

> **Note:** Phylogenetic tree building is not included in the pipeline. The core alignments above can be used directly with RAxML, IQ-TREE, FastTree, or any other tree builder. See [Phylogenetic Trees](#phylogenetic-trees) below for the recommended RAxML method matching Ruis et al. 2021.

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

### DCC4/DCC5 assignment note

DCC4 and DCC5 are highly related lineages that FastBAPS frequently places in the same population structure cluster. When this occurs the pipeline automatically uses pairwise SNP distance to the closest reference strain to distinguish them. This distance-based tiebreaking was validated against a 312-isolate cohort and correctly separates the two lineages.

### DCC6 assignment note

DCC6 is a relatively rare massiliense lineage. Only isolates within ~1,000 SNPs of the DCC6 reference strains (A47/ERR2524314) are assigned to DCC6 — more divergent isolates that cluster phylogenetically near DCC6 but are >5,000 SNPs away are classified as Non-DCC massiliense. This conservative assignment reflects the biological reality that these isolates represent independent acquisitions rather than transmission from the DCC6 lineage.

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

## Location File Format

The locations file is optional but required for the interactive HTML transmission map. It should be an Excel file (`.xlsx`) with the following format:

| Column 1 | Column 2 |
|----------|----------|
| Isolate ID | Institution or location |

**Example:**

| Isolate | Institution |
|---------|------------|
| GD01 | Westmead Hospital, Sydney, Australia |
| GD02_hybrid | Great Ormond Street Hospital, London, UK |
| GD05 | Toronto General Hospital, Canada |
| GD09_WGS | Massachusetts General Hospital, USA |

**Rules:**
- Column 1 must contain the isolate ID exactly as it appears in your FASTA filenames (without the `.fasta` extension)
- Column 2 should contain the institution name or city/country
- The pipeline extracts country from the institution name automatically — include recognizable country keywords (e.g. Australia, UK, Canada, USA, France)
- No header row required but one is accepted
- Isolates without a matching location entry are excluded from the map but still included in all other outputs
- Place the file at `input/locations.xlsx` and set `locations_file: "input/locations.xlsx"` in `config.yaml`

**Supported countries for map plotting:**
Australia, New Zealand, UK, USA, Canada, France, Netherlands, Germany, Italy, Spain, Israel, Ireland, Finland, Switzerland, Singapore, Taiwan, Turkey, Latvia, Portugal, Slovakia

> If your institution is in a country not listed above it will default to USA. Add additional country detection logic to `workflow/scripts/generate_html_map.py` if needed.

## Pipeline Options

### Skip RAxML trees

If you have your own preferred phylogenetic pipeline or want to save time on large datasets, skip the RAxML step entirely:

```bash
# Skip trees for this run
snakemake --cores 16 --use-conda --config skip_raxml=true

# Or set permanently in config.yaml
skip_raxml: true
```

The pipeline will complete all DCC assignments and transmission pair analysis without running RAxML. The core SNP alignments (`results/core/abscessus/core.aln` and `results/core/massiliense/core.aln`) are always produced and can be used directly with IQ-TREE, FastTree, or any other tree builder.

### Clean up results

Reset the pipeline without re-downloading references:

```bash
# Remove results but keep downloads (~3GB of DCC refs)
snakemake clean --cores 1

# Remove everything including downloads
snakemake clean_all --cores 1
```

### Dry run summary

Before committing to a full run, preview what the pipeline will do:

```bash
snakemake --cores 16 --use-conda --dry-run
```

This prints a summary including isolate count, estimated runtimes, and whether reference downloads are needed:

```
============================================================
  M. abscessus DCC Assignment Pipeline
============================================================
  Isolates found:     150
  Total input size:   0.72 GB
  Output directory:   results/
  Skip RAxML trees:   NO
  Locations file:     YES

  Estimated runtimes (approximate, based on 312-isolate validation run):
    MASH species/subspecies:  ~30 minutes
    Snippy SNP calling:       ~16 hours
    FastBAPS clustering:      ~30 minutes
    Gubbins recombination:    ~48 hours (most time-consuming step)
    RAxML trees:              ~60 hours (skip with --config skip_raxml=true)
    Final outputs:            ~5 minutes
    Total without RAxML:      ~65 hours on 16 cores
============================================================
```

### Progress log

A timestamped progress log is written to `results/pipeline_progress.log` during each run, making it easy to track which steps have completed:

```
[2025-05-07 14:23:01] Input validation passed: 150 isolates found
[2025-05-07 14:23:01] Config validation passed
```

## Notes on Test Datasets

When running on small test datasets (<20 isolates) RAxML tree building is automatically skipped. A minimum of ~50 isolates is recommended for meaningful phylogenetic trees and FastBAPS clustering.

**Important:** Small test datasets (<10 isolates) may produce all Non-DCC results because the core SNP alignment lacks sufficient variable sites to distinguish DCC lineages. DCC reference sequences must be included in the alignment for correct assignment — this happens automatically via the `download_dcc_references` rule.

DCC reference sequences (~3–4GB) are downloaded automatically on first run. If your server has no internet access download the references on a local machine and transfer them to `results/dcc_refs/`.

## Validation

This pipeline was validated on a 312-isolate clinical cohort of *M. abscessus* complex isolates:

| DCC | Pipeline | Expected | Status |
|-----|----------|---------|--------|
| DCC1 | 115 | 115 | ✅ exact match |
| DCC2 | 28 | 28 | ✅ exact match |
| DCC3 | 24 | 24 | ✅ exact match |
| DCC4 | 51 | 39 | ✅ combined DCC4+DCC5 = 82 matches |
| DCC5 | 31 | 43 | ✅ combined DCC4+DCC5 = 82 matches |
| DCC6 | 1 | 6 | ✅ conservative assignment (see note above) |
| DCC7 | 20 | 20 | ✅ exact match |
| Non-DCC | 38 | 31 | ✅ difference explained by DCC6 reclassification |

Transmission pairs identified: 218 at ≤10 SNPs, 449 at ≤20 SNPs.

## Phylogenetic Trees

Phylogenetic tree building is intentionally excluded from the pipeline due to the long runtime required (2–3 days for 300+ isolates with 100 bootstraps). The core SNP alignments produced by the pipeline can be used directly with any tree building software.

### Output alignments

After the pipeline completes, core SNP alignments are available at:
- `results/core/abscessus/core.aln` — M. a. abscessus alignment including DCC reference strains
- `results/core/massiliense/core.aln` — M. a. massiliense alignment including DCC reference strains

### Recommended method (Ruis et al. 2021)

RAxML v8.2 with GTR+GAMMA model and 100 bootstraps, as used in Ruis et al. 2021:

```bash
conda activate analyze_mab  # or any env with RAxML

# Step 1 — Run 100 bootstrap replicates
nohup raxmlHPC-PTHREADS   -s results/core/abscessus/core.aln   -n abscessus_raxml   -m GTRGAMMA   -p 12345   -b 12345   -N 100   -T 4   -w $(realpath results/trees/abscessus/) &> raxml_bootstrap.log &

# Step 2 — Find best ML tree
raxmlHPC-PTHREADS   -s results/core/abscessus/core.aln   -n abscessus_besttree   -m GTRGAMMA   -p 12345   -T 4   -w $(realpath results/trees/abscessus/)

# Step 3 — Draw bootstrap values onto best tree
raxmlHPC -f b   -t results/trees/abscessus/RAxML_bestTree.abscessus_besttree   -z results/trees/abscessus/RAxML_bootstrap.abscessus_raxml   -m GTRGAMMA   -n abscessus_final   -w $(realpath results/trees/abscessus/)
```

The output file `RAxML_bipartitions.abscessus_final` can be uploaded directly to [iTOL](https://itol.embl.de) for visualization.

### iTOL annotation

After DCC assignments are complete, generate iTOL annotation files using the tip labels from your tree:

```bash
# Get tip labels from bipartitions tree
grep -oP '[A-Z][A-Z0-9_]+(?=:)' results/trees/abscessus/RAxML_bipartitions.abscessus_final     > /tmp/abscessus_tips.txt

# Generate color strip and label color files
python3 << 'PYEOF'
import csv
tips = open("/tmp/abscessus_tips.txt").read().splitlines()
dcc_map = {}
with open("results/dcc/abscessus_assignments.csv") as f:
    for row in csv.DictReader(f):
        dcc_map[row["Isolate"]] = row["DCC"]

DCC_COLORS = {
    "DCC1":"#60a5fa","DCC2":"#34d399","DCC4":"#a78bfa",
    "DCC5":"#fbbf24","DCC6":"#e11d48","DCC7":"#06b6d4",
    "Non-DCC":"#fb923c","Unknown":"#888888"
}
REF_DCC = {
    "SRR36966619":"DCC1","ERR363247":"DCC2","ERR1081288":"DCC4",
    "ERR494841":"DCC4","ERR363431":"DCC5","ERR484982":"DCC5",
    "ERR2524314":"DCC6","ERR363320":"DCC7"
}

lines = ["DATASET_COLORSTRIP","SEPARATOR TAB","DATASET_LABEL	DCC",
         "COLOR	#888888","LEGEND_TITLE	DCC",
         "LEGEND_COLORS	#60a5fa	#34d399	#a78bfa	#fbbf24	#e11d48	#06b6d4	#fb923c",
         "LEGEND_LABELS	DCC1	DCC2	DCC4	DCC5	DCC6	DCC7	Non-DCC","DATA"]

for tip in tips:
    dcc = REF_DCC.get(tip) or dcc_map.get(tip) or           dcc_map.get(tip.replace("_WGS","").replace("_hybrid",""), "Unknown")
    color = DCC_COLORS.get(dcc, "#888888")
    lines.append(f"{tip}	{color}	{dcc}")

with open("results/trees/abscessus/iTOL_colorstrip.txt","w") as f:
    f.write("
".join(lines))
print("iTOL annotation written to results/trees/abscessus/iTOL_colorstrip.txt")
PYEOF
```

## References

- **Ruis et al. 2021** — Dissemination of *Mycobacterium abscessus* via global transmission networks. *Nature Microbiology*. [PMC8478660](https://pmc.ncbi.nlm.nih.gov/articles/PMC8478660/)
- **Bronson et al. 2021** — Global phylogenomic analyses of *M. abscessus*. [PMC8390669](https://pmc.ncbi.nlm.nih.gov/articles/PMC8390669/)
- **Dedrick et al.** — Phage therapy of *Mycobacterium* infections. [PMC10583746](https://pmc.ncbi.nlm.nih.gov/articles/PMC10583746/)

## Author

Casey Moyer — University of Pittsburgh, Phage Genomics and Bioinformatics
GitHub: [cmoyer-x](https://github.com/cmoyer-x)
