# Troubleshooting Guide

## FastBAPS

### Error: namespace rlang already loaded
Fix: Update rlang and restart R completely:
```r
install.packages("rlang")
# Restart R session fully before retrying
```

### FastBAPS fails on macOS Apple Silicon
Fails due to C++14/clang-17 incompatibility with RcppArmadillo.
Fix: Install and run on Linux only.

## Gubbins

### Bipartitions error
Fix: Use --first-tree-builder fasttree flag:
```bash
### IQ-TREE crash with small clusters
Fix: Switch to fasttree for small clusters:
```bash
Fix: Switch to fasttree for small clusters:
```bash
run_gubbins.py --tree-builder fasttree cluster_X.fasta
```

### Low coverage isolate causing failure
Isolates with less than 1% genome coverage cause Gubbins to fail.
Fix: Identify and exclude before running:
```bash
grep "Variant" snippy_out/*/snps.txt | sort -k2 -n | head
```

## Snippy

### snippy command not found inside nohup
Fix: Source conda explicitly:
```bash
nohup bash -c '
source ~/miniconda3/etc/profile.d/conda.sh
conda activate snippy
snippy ...
' &
```

## RAxML

### Output files already exist
Fix: Use a new run name:
```bash
raxmlHPC-PTHREADS -n run_v2 ...
```

### Alpha parameter warning
This is expected and normal for SNP-only alignments. Not an error.

## SRA Downloads

### SSL certificate error with prefetch
Fix: Download from ENA via HTTP on local Mac then scp to server:
```bash
# On Mac:
curl -L "http://ftp.sra.ebi.ac.uk/vol1/fastq/ERR363/ERR363247/ERR363247_1.fastq.gz" -o ERR363247_1.fastq.gz
# Transfer to server:
scp ERR363247_1.fastq.gz user@server:~/
```
