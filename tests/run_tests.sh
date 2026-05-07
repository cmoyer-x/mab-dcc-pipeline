#!/bin/bash
# Run pipeline tests on small test dataset
set -e

echo "Running mab-dcc-pipeline tests..."

# Check snakemake is available
snakemake --version || { echo "ERROR: Snakemake not installed"; exit 1; }

# Check required tools
for tool in mash snippy snp-dists; do
    which $tool > /dev/null 2>&1 && echo "PASS: $tool found" || echo "WARN: $tool not found"
done

# Dry run on test data
cd "$(dirname "$0")/.."
snakemake \
    --cores 4 \
    --use-conda \
    --dry-run \
    --config input_dir=tests/test_data output_dir=tests/test_output \
    && echo "PASS: dry run succeeded" \
    || { echo "FAIL: dry run failed"; exit 1; }

echo "All tests passed!"
