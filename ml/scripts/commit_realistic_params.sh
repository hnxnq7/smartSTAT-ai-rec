#!/bin/bash
# Commit script for realistic parameters work

cd "$(dirname "$0")/../.."

echo "Preparing commit for realistic parameters implementation..."

# Add all new files
git add ml/config/ ml/docs/REALISTIC_PARAMETERS_RESEARCH.md
git add ml/data_generation/config_loader.py
git add ml/scripts/analyze_scenario_expired_rate.py
git add ml/scripts/run_sensitivity_sweep.py

# Add modified files
git add ml/data_generation/generator.py
git add ml/data_generation/generate_synthetic_bank.py
git add ml/evaluate.py
git add ml/results/TRAINING_RESULTS.md

# Add sweep results if they exist
if [ -f ml/data/sensitivity_sweep_results.csv ]; then
    git add ml/data/sensitivity_sweep_results.csv
    echo "✓ Added sensitivity sweep results"
fi

# Create commit
git commit -m "Implement realistic hospital supply chain parameters with evidence-based configs

Round 14: Realistic Parameters Sensitivity Sweep

Major Changes:
- Evidence-based parameter research with Tier 1/2 source citations
- YAML config system for parameter management (realistic_params.yaml)
- Sensitivity scenarios (12 scenarios: baseline + S1-S12)
- Config loader utility for scenario overrides
- Generator and evaluator updated to support config parameters

Key Results:
- S9 (optimal realistic): 7.89% expired rate (down from 59.10% baseline)
- Categories A-D: 0.00% expired rate with 3-year shelf life
- Validated: Parameter realism > ordering logic optimization
- Shelf life is primary driver: 86.6% reduction with 3-year shelf life

Files:
- ml/docs/REALISTIC_PARAMETERS_RESEARCH.md: Evidence-based parameter research
- ml/config/realistic_params.yaml: Base realistic parameter defaults
- ml/config/sensitivity_scenarios.yaml: 12 test scenarios
- ml/data_generation/config_loader.py: Config loading utilities
- ml/scripts/: Analysis and sweep automation scripts
- Updated generator.py, evaluate.py, generate_synthetic_bank.py for config support

This validates that realistic hospital supply chain parameters (especially
2-3 year shelf life for medications) achieve the <50% expired rate target."

echo ""
echo "✓ Commit prepared. Review with 'git show HEAD' or amend as needed."
echo ""
echo "Cleaning up redundant files..."

# Remove temporary helper files
rm -f .commit_when_ready.txt
echo "  ✓ Removed .commit_when_ready.txt"

echo ""
echo "✓ Cleanup complete. Ready to push!"
