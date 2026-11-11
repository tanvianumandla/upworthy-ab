#!/usr/bin/env bash
# Runs the full analysis. Expects data/exploratory.csv and data/confirmatory.csv.
set -euo pipefail
cd "$(dirname "$0")"
python src/load.py
python src/ab_results.py exploratory
python src/feature_model.py exploratory
python src/ab_results.py confirmatory
python src/feature_model.py confirmatory
python src/charts.py
echo "Optional (slow, ~1 min): python tests/check_model.py"
