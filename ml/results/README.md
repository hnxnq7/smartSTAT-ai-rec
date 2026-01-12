# Training Results Directory

This directory contains all training results, evaluations, and analysis from ML model training rounds.

## Files

### Result CSVs
- `results_second_round.csv` - Round 1 (Baseline) results
- `results_category_d_improved.csv` - Round 2 (Category D improvement) results
- `results_all_categories_improved.csv` - Round 3 (All categories improved) results

### Analysis Documents
- `TRAINING_RESULTS.md` - Consolidated analysis of all training rounds (latest on top)

### Evaluation Outputs
- `evaluation_output_*.txt` - Text outputs from evaluation scripts (if any)

## Model Directories

Trained models are stored separately:
- Round 1 (Baseline): `ml/models/`
- Round 2 (Category D): `ml/models_category_d_improved/`
- Round 3 (All Categories): `ml/models_all_categories_improved/`

## Usage

See `TRAINING_RESULTS.md` for detailed analysis and comparisons across rounds.

To evaluate results:
```bash
PYTHONPATH=. python3 ml/evaluate_results.py \
  --models_dir ml/models_all_categories_improved \
  --horizon 14 --objective l2 \
  --output_csv ml/results/results_new_round.csv
```
