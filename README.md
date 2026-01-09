# smartSTAT - AI Recommendations Demo

A medication management dashboard with AI-powered ordering recommendations.

## Features

- **Intelligent Recommendations**: Calculates optimal order quantities and timing based on:
  - Historical usage patterns (daily usage rate)
  - Expiration dates and batch-level inventory
  - User preferences (surplus days, minimum shelf life, lead time)
  - Service level targets

- **Risk Management**: 
  - Identifies medications at risk of stockout
  - Flags medications approaching expiration
  - Projects potential waste from expiring inventory

- **Interactive Dashboard**:
  - Filter by cart, department, planning horizon, and risk type
  - Summary cards showing key metrics
  - Detailed table with all recommendations
  - Side panel with detailed explanations and preference editing

- **Real-time Updates**: Adjust preferences and see recommendations update instantly

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
smartSTAT/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Main page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/               # Reusable UI components
│   ├── AIRecommendations.tsx
│   ├── FilterBar.tsx
│   ├── SummaryCards.tsx
│   ├── RecommendationsTable.tsx
│   ├── RecommendationDetails.tsx
│   └── PreferencesEditor.tsx
├── lib/                  # Business logic
│   ├── data.ts          # Synthetic data generation
│   └── recommendations.ts # Recommendation calculation engine
├── types/               # TypeScript type definitions
│   └── inventory.ts
└── package.json
```

## How It Works

### Recommendation Algorithm

1. **Usage Analysis**: Calculates daily usage rate (λ) from historical usage events over the last 45 days
2. **Demand Forecasting**: Projects demand over the planning horizon (7/14/30 days)
3. **Safety Stock**: Calculates safety stock based on service level and lead time variability
4. **Usable Inventory**: Filters batches by expiration date, considering minimum remaining shelf life
5. **Order Calculation**: 
   - Target Stock = Forecast Demand + Safety Stock + Preferred Surplus
   - Recommended Order = Target Stock - Usable Stock

### Key Metrics

- **Daily Usage Rate (λ)**: Average units consumed per day
- **Forecast Demand**: Expected consumption over planning horizon
- **Safety Stock**: Buffer stock to handle variability (based on service level)
- **Usable Stock**: Current inventory that won't expire before use
- **Recommended Order Quantity**: Amount to order to reach target stock level

## Customization

### Adjusting Preferences

Click "Details" on any recommendation to:
- Change surplus days (0-14)
- Adjust minimum remaining shelf life (0-90 days)
- Modify lead time
- Update service level (90%, 95%, 99%)

Changes update recommendations in real-time.

### Synthetic Data

The demo uses synthetic data generated in `lib/data.ts`. To customize:
- Modify medication names in `MEDICATION_NAMES`
- Adjust departments in `DEPARTMENTS`
- Change usage patterns, batch quantities, or expiration dates

## Tech Stack

- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **date-fns**: Date manipulation
- **lucide-react**: Icons

## ML Training

This project includes a machine learning pipeline for training LightGBM demand forecasting models on synthetic medication usage datasets.

### Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Data Location:**
   - Training/test datasets are located in `lib/smartstat_synth_2023-2025/`
   - Training sets: `Training_Sets_2023-2024/`
   - Test sets: `Testing_Sets_2025/`
   - Dataset manifest: `DATASET_MANIFEST.csv`

### Training Models

#### Interactive Training (Jupyter Notebook)

The primary way to train models is through the Jupyter notebook:

```bash
# Launch Jupyter
jupyter notebook

# Open: ml/notebooks/lightgbm_training.ipynb
```

The notebook allows you to:
- Configure dataset ID, forecast horizon, and model objective
- Visualize data and model performance
- Train models interactively
- Save trained models, metrics, and predictions

**Key Configuration Variables** (at top of notebook):
- `DATA_DIR`: Path to data directory (default: `../lib/smartstat_synth_2023-2025`)
- `DATASET_ID`: Dataset to train (e.g., "A1", "E10", or "all")
- `HORIZON`: Forecast horizon in days (7, 14, or 30)
- `OBJECTIVE`: Model objective ("l2" for regression, "quantile" for quantile regression)
- `OUTPUT_DIR`: Where to save models and results (default: `../models`)

#### Command Line Training

For batch training across multiple datasets:

```bash
# Train single dataset
python -m ml.train_lgbm --data_dir ./lib/smartstat_synth_2023-2025 --dataset_id A1 --horizon 14 --objective l2

# Train all datasets
python -m ml.train_lgbm --data_dir ./lib/smartstat_synth_2023-2025 --dataset_id all --horizon 14 --objective l2

# Quantile regression
python -m ml.train_lgbm --dataset_id A1 --horizon 14 --objective quantile --quantile_alpha 0.95

# Exclude contemporaneous used_units from features
python -m ml.train_lgbm --dataset_id A1 --horizon 14 --exclude_contemporaneous_used
```

### Project Structure

```
ml/
├── notebooks/
│   └── lightgbm_training.ipynb  # Main training notebook
├── __init__.py
├── config.py                     # Configuration defaults
├── datasets.py                   # Dataset loading utilities
├── features.py                   # Feature engineering and label creation
├── evaluate.py                   # Evaluation metrics
└── train_lgbm.py                # CLI training script

models/                          # Output directory (created after training)
├── {dataset_id}/
│   ├── model_h{horizon}_{objective}.txt
│   ├── feature_importance_h{horizon}_{objective}.csv
│   ├── predictions_h{horizon}_{objective}.csv
│   └── metrics_h{horizon}_{objective}.json
```

### Key Features

- **No Data Leakage**: Labels are created using only future data within each split
- **Time-based Validation**: Uses last 90 days of training data for validation
- **Multi-horizon Forecasting**: Supports 7, 14, and 30-day forecast horizons
- **Multiple Objectives**: L2 regression and quantile regression
- **Reproducible**: Fixed random seeds and deterministic training
- **Comprehensive Evaluation**: MAE, RMSE, and MAPE metrics
- **Visualizations**: Interactive plots in notebook

### Outputs

After training, each model produces:

1. **Model artifact** (`.txt`): Saved LightGBM model file
2. **Metrics** (`.json`): Evaluation metrics and metadata
3. **Predictions** (`.csv`): Predictions vs actuals on test set
4. **Feature importance** (`.csv`): Feature importance rankings

### Example Usage

```python
# In notebook or Python script
from ml.datasets import load_dataset_files
from ml.features import prepare_features_and_labels
import lightgbm as lgb

# Load data
train_df, test_df = load_dataset_files(data_dir, "A1")

# Prepare features
X_train, y_train, X_test, y_test = prepare_features_and_labels(
    train_df, test_df, horizon=14
)

# Train model (see notebook for full example)
# ...

# Load saved model
model = lgb.Booster(model_file='models/A1/model_h14_l2.txt')
predictions = model.predict(X_test)
```

## License

This is a demo project for demonstration purposes.








