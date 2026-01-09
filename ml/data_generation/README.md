# Synthetic Dataset Generation

This module generates large-scale synthetic datasets for medication demand forecasting ML training and evaluation.

## Overview

The generator creates **500 scenarios** across 5 demand archetypes:

- **Archetype A**: High volume, stable demand
- **Archetype B**: Low volume, intermittent (many zero days)
- **Archetype C**: Weekly pattern (weekday high, weekend low)
- **Archetype D**: Trend up/down (linear or step changes)
- **Archetype E**: Burst events (rare spike days)

Each archetype has **100 scenarios** (A001-A100, B001-B100, etc.).

### Hospital Size Tiers

Each scenario is assigned to one of three hospital size tiers:
- **small**: Low baseline demand, smaller inventory
- **medium**: Moderate demand
- **large**: Higher baseline demand, larger inventory

Distribution is roughly balanced (33/33/34) within each archetype.

### Data Period

- **Training period**: 2023-2024 (731 days)
- **Testing period**: 2025 (365 days)
- **Total**: 3 years of daily data per scenario

## Usage

### Generate All Datasets

```bash
# Generate all 500 scenarios (default output: ml/data/synthetic_bank)
python3 -m ml.data_generation.generate_synthetic_bank

# Specify custom output directory
python3 -m ml.data_generation.generate_synthetic_bank --output_dir /path/to/output

# Generate with zip archive
python3 -m ml.data_generation.generate_synthetic_bank --zip

# Custom zip path
python3 -m ml.data_generation.generate_synthetic_bank --zip --zip_path datasets.zip

# Use custom base seed
python3 -m ml.data_generation.generate_synthetic_bank --base_seed 99999

# Quiet mode (no progress bars)
python3 -m ml.data_generation.generate_synthetic_bank --quiet
```

### Output Structure

```
ml/data/synthetic_bank/
├── DATASET_MANIFEST.csv          # Metadata for all scenarios
├── Training_Sets_2023-2024/      # Train CSV files
│   ├── A001_small_train_2023_2024.csv
│   ├── A001_medium_train_2023_2024.csv
│   └── ...
└── Testing_Sets_2025/            # Test CSV files
    ├── A001_small_test_2025.csv
    ├── A001_medium_test_2025.csv
    └── ...
```

### Dataset Columns

Each CSV file contains the following columns:

**Core Inventory Flow:**
- `date`: Date (YYYY-MM-DD)
- `total_onsite_units`: Total units in inventory
- `expired_units`: Units expired on this day
- `used_units`: Units used/consumed on this day
- `newly_added_units`: Units arriving from orders
- `ordered_units`: Units ordered on this day
- `non_expired_inventory`: Non-expired units available

**Time Features:**
- `day_of_week`: Day of week (0=Monday, 6=Sunday)
- `week_of_year`: ISO week number (1-53)
- `month`: Month (1-12)

**Lag Features (past-only):**
- `used_lag_1`: Used units 1 day ago
- `used_lag_2`: Used units 2 days ago
- `used_lag_7`: Used units 7 days ago
- `used_lag_14`: Used units 14 days ago

**Rolling Statistics (past-only):**
- `rolling_used_7d_total`: Sum of used units over past 7 days
- `rolling_used_7d_avg`: Average used units over past 7 days
- `rolling_used_30d_total`: Sum of used units over past 30 days
- `rolling_used_30d_avg`: Average used units over past 30 days
- `usage_7d_to_30d_ratio`: Ratio of 7d to 30d usage

**Derived Features:**
- `days_until_stockout_est`: Estimated days until stockout

**Important**: All features use only past information (no data leakage).

### Manifest File

The `DATASET_MANIFEST.csv` contains metadata for each scenario:

- `scenario_id`: Unique ID (e.g., "A023")
- `archetype`: Demand archetype ("A", "B", "C", "D", "E")
- `hospital_size`: Size tier ("small", "medium", "large")
- `seed`: Random seed used for generation
- `train_file`: Training CSV filename
- `test_file`: Test CSV filename
- `lead_time`: Order lead time in days
- `avg_used_train/test`: Average daily usage
- `pct_zero_train/test`: Percentage of zero-usage days
- `max_used_train/test`: Maximum daily usage
- Archetype-specific generation parameters

## Examples

### Generate and Inspect

```bash
# Generate datasets
python3 -m ml.data_generation.generate_synthetic_bank --output_dir data/synthetic

# View manifest
head -20 data/synthetic/DATASET_MANIFEST.csv

# Check a specific scenario
python3 -c "
import pandas as pd
df = pd.read_csv('data/synthetic/Training_Sets_2023-2024/A001_small_train_2023_2024.csv')
print(df.describe())
"
```

### Use with ML Training Pipeline

After generation, use the datasets with the ML training pipeline:

```bash
# Train on a specific scenario
python3 -m ml.train_lgbm --dataset_id A001 --horizon 14 --objective l2

# Train on all scenarios (requires updating datasets.py to point to new data directory)
python3 -m ml.train_lgbm --dataset_id all --horizon 14 --objective l2
```

## Notes

- **Reproducibility**: Each scenario uses a unique seed derived from the base seed and scenario ID
- **Inventory Simulation**: Includes realistic ordering logic with lead times and reorder points
- **No Data Leakage**: All features are computed using only past information
- **File Naming**: Files follow pattern `{scenario_id}_{hospital_size}_{split}_{period}.csv`

## Time Estimates

- **Generation time**: Approximately 15-30 minutes for all 500 scenarios (depends on hardware)
- **Disk space**: Approximately 200-300 MB for all CSV files (uncompressed)
- **Zipped**: Approximately 50-80 MB
