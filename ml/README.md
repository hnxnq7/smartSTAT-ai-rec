# ML Training Pipeline

This directory contains the machine learning training pipeline for demand forecasting models.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r ../requirements.txt
   ```

2. **Run the Jupyter notebook:**
   ```bash
   jupyter notebook notebooks/lightgbm_training.ipynb
   ```

3. **Or use the CLI:**
   ```bash
   python -m ml.train_lgbm --dataset_id A1 --horizon 14 --objective l2
   ```

## Files

- `notebooks/lightgbm_training.ipynb` - Interactive training notebook (primary interface)
- `train_lgbm.py` - CLI script for batch training
- `datasets.py` - Dataset discovery and loading utilities
- `features.py` - Feature engineering and label creation
- `evaluate.py` - Evaluation metrics computation
- `config.py` - Configuration defaults

## Expected Outputs

After training, models and results are saved to `ml/models/{dataset_id}/`:

- `model_h{horizon}_{objective}.txt` - Trained LightGBM model
- `feature_importance_h{horizon}_{objective}.csv` - Feature importance rankings
- `predictions_h{horizon}_{objective}.csv` - Test set predictions vs actuals
- `metrics_h{horizon}_{objective}.json` - Evaluation metrics and metadata

## Key Design Decisions

1. **No Data Leakage**: Labels use only future data from the same split
2. **Time-based Validation**: Last 90 days of training data used for validation
3. **Deterministic**: Fixed random seeds ensure reproducibility
4. **Configurable Paths**: DATA_DIR can be easily changed for cloud storage

