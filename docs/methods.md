# Pipeline Methods

## Overview
This pipeline replicates the population genomics framework of Ruis et al. 2021
(Nature Microbiology, PMC8478660) for assigning M. abscessus clinical isolates
to Dominant Circulating Clones (DCCs 1-7).

## Step 1 — Species Identification (MASH)
All input FASTAs are compared against a 17-species NTM reference panel using
MASH genome distances. Non-M. abscessus isolates are excluded and logged.

## Step 2 — Subspecies Assignment (MASH)
M. abscessus complex isolates are assigned to subspecies (abscessus,
massiliense, bolletii) by MASH distance to three reference genomes:
- M. a. abscessus: ATCC19977 (CU458896.1)
- M. a. massiliense: CIP_108297 (GCF_001792625.1)
- M. a. bolletii: CCUG_50184 (GCF_000701545.1)

## Step 3 — SNP Calling (Snippy)
Each isolate is mapped against its subspecies reference using Snippy v4.6.0.
DCC anchor sequences are also mapped at this step.

## Step 4 — Core SNP Alignment (snippy-core)
A core SNP alignment is built per subspecies including all patient isolates
and DCC reference sequences.

## Step 5 — Population Structure (FastBAPS)
FastBAPS v1.0.8 is run on the core alignment to identify population structure
clusters using the optimise.symmetric prior at 2 levels.

## Step 6 — DCC Anchoring
FastBAPS clusters are assigned to DCCs by identifying which cluster each
DCC reference strain falls into. References used:
- DCC1: SRR36966619 (Ruis et al.)
- DCC2: ERR363247 (Ruis et al.)
- DCC3: ERR1045629 (Ruis et al.)
- DCC4: ERR1081288 + ERR494841/strain 976 (Ruis + Dedrick et al.)
- DCC5: ERR363431 + ERR484982/strain 1100 (Ruis + Dedrick et al.)
- DCC6: ERR2524314 + A47/GCF_002799795.1 (Ruis + Dedrick et al.)
- DCC7: ERR363320 + FLAC047/GCF_002140035.1 (Ruis + Dedrick et al.)

Note: DCC6 and DCC7 are M. a. massiliense lineages confirmed by SNP distance.

## Step 7 — Recombination Removal (Gubbins)
Gubbins v3.3.5 is run independently on each FastBAPS cluster using IQ-TREE
as the tree builder. FastTree is used as fallback for small clusters (<8 seqs)
or when IQ-TREE fails.

## Step 8 — SNP Distances (snp-dists)
Pairwise SNP distances are calculated from Gubbins-filtered alignments
per cluster and from whole-cohort alignments for DCC assignment.

## Step 9 — Transmission Pairs
Transmission pairs are identified at two thresholds:
- <=10 SNPs: likely direct transmission (Ruis et al. 2021)
- <=20 SNPs: probable transmission cluster (Bronson et al. 2021)

## Step 10 — Phylogenetic Trees (RAxML)
Maximum likelihood trees are reconstructed using RAxML v8.2 with the
GTR+GAMMA model and 100 bootstrap replicates, matching Ruis et al.

## References
- Ruis et al. 2021. Nature Microbiology. doi:10.1038/s41564-021-00963-3
- Bronson et al. 2021. PMC8390669
- Dedrick et al. PMC10583746
