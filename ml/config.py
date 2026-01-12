"""
Configuration defaults for LightGBM training pipeline.
"""

import os
from pathlib import Path

# Default data directory - can be overridden
DEFAULT_DATA_DIR = Path(__file__).parent.parent / "lib" / "smartstat_synth_2023-2025"

# Default output directory for models and metrics
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "ml" / "models"

# Supported forecast horizons (in days)
SUPPORTED_HORIZONS = [7, 14, 30]

# Supported objectives
OBJECTIVE_L2 = "l2"
OBJECTIVE_QUANTILE = "quantile"
SUPPORTED_OBJECTIVES = [OBJECTIVE_L2, OBJECTIVE_QUANTILE]

# Default LightGBM hyperparameters
# Updated: Increased num_leaves from 31 to 63 to better capture complex patterns (especially trends)
DEFAULT_LIGHTGBM_PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "boosting_type": "gbdt",
    "num_leaves": 63,  # Increased from 31 to better capture trends and complex patterns
    "learning_rate": 0.05,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "min_data_in_leaf": 20,
    "verbose": -1,
    "seed": 42,
    "deterministic": True,
}

# Quantile regression parameters
DEFAULT_QUANTILE_ALPHA = 0.95

# Training parameters
VALIDATION_SPLIT_DAYS = 90  # Last N days of training data for validation
RANDOM_SEED = 42

# Feature configuration
# List of numeric feature columns to use for training
FEATURE_COLUMNS = [
    "total_onsite_units",
    "expired_units",
    "used_units",  # Can be excluded via flag
    "newly_added_units",
    "ordered_units",
    "non_expired_inventory",
    "used_lag_1",
    "used_lag_2",
    "used_lag_7",
    "used_lag_14",
    "rolling_used_7d_total",
    "rolling_used_7d_avg",
    "rolling_used_30d_total",
    "rolling_used_30d_avg",
    "usage_7d_to_30d_ratio",
    "days_until_stockout_est",
    # Trend detection features (for Category D improvement)
    "trend_slope_7d",
    "trend_slope_14d",
    "trend_slope_30d",
    "momentum_7d",
    "momentum_14d",
    "momentum_30d",
    "trend_up_7d",
    "trend_up_14d",
    "trend_up_30d",
    "trend_strength_7d",
    "trend_strength_14d",
    "trend_strength_30d",
    "day_of_week",
    "week_of_year",
    "month",
]

# Columns to exclude from features
EXCLUDED_COLUMNS = ["date"]

# Early stopping parameters
EARLY_STOPPING_ROUNDS = 50

