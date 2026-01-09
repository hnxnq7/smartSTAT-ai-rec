"""
Feature engineering and label creation utilities.
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
from ml.config import FEATURE_COLUMNS, EXCLUDED_COLUMNS


def create_labels(
    df: pd.DataFrame,
    horizon: int,
    target_column: str = "used_units",
) -> pd.Series:
    """
    Create labels for multi-horizon forecasting.
    
    For each date t, the label is: sum(used_units from t+1 to t+horizon)
    This ensures no data leakage - labels only use future data.
    
    Args:
        df: DataFrame with date index and target_column
        horizon: Forecast horizon in days
        target_column: Name of the column to sum for labels
    
    Returns:
        Series of labels (y_H values). Last H rows will be NaN.
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame")
    
    # Sort by date to ensure chronological order
    df_sorted = df.sort_values("date").reset_index(drop=True)
    
    # Create rolling sum of future H days
    # Shift by -horizon, then sum backwards
    labels = df_sorted[target_column].rolling(
        window=horizon, min_periods=horizon
    ).sum().shift(-horizon)
    
    return labels


def prepare_features_and_labels(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    horizon: int,
    exclude_contemporaneous_used: bool = False,
    target_column: str = "used_units",
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Prepare features and labels for training and testing.
    
    Args:
        train_df: Training DataFrame with date column
        test_df: Test DataFrame with date column
        horizon: Forecast horizon in days
        exclude_contemporaneous_used: If True, exclude 'used_units' from features
        target_column: Column name to use for label creation
    
    Returns:
        Tuple of (X_train, y_train, X_test, y_test)
        Last H rows of each split are dropped where labels are NaN.
    """
    # Create labels separately for train and test (no leakage between splits)
    y_train = create_labels(train_df.copy(), horizon, target_column)
    y_test = create_labels(test_df.copy(), horizon, target_column)
    
    # Select feature columns
    feature_cols = FEATURE_COLUMNS.copy()
    
    # Exclude date column
    for col in EXCLUDED_COLUMNS:
        if col in feature_cols:
            feature_cols.remove(col)
    
    # Optionally exclude contemporaneous used_units
    if exclude_contemporaneous_used and "used_units" in feature_cols:
        feature_cols.remove("used_units")
    
    # Filter to columns that actually exist in the DataFrame
    available_cols = [col for col in feature_cols if col in train_df.columns]
    missing_cols = [col for col in feature_cols if col not in train_df.columns]
    
    if missing_cols:
        print(f"Warning: Some feature columns not found: {missing_cols}")
    
    # Extract features
    X_train = train_df[available_cols].copy()
    X_test = test_df[available_cols].copy()
    
    # Drop rows where labels are NaN (last H rows)
    train_mask = ~y_train.isna()
    test_mask = ~y_test.isna()
    
    X_train = X_train[train_mask].reset_index(drop=True)
    y_train = y_train[train_mask].reset_index(drop=True)
    X_test = X_test[test_mask].reset_index(drop=True)
    y_test = y_test[test_mask].reset_index(drop=True)
    
    # Handle any remaining NaN values in features (fill with 0 or forward fill)
    X_train = X_train.fillna(0)
    X_test = X_test.fillna(0)
    
    return X_train, y_train, X_test, y_test


def create_time_based_validation_split(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    validation_days: int = 90,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Create a time-based validation split from training data.
    
    Uses the last N days as validation set, earlier rows as training.
    
    Args:
        X_train: Training features
        y_train: Training labels
        validation_days: Number of days to use for validation (from the end)
    
    Returns:
        Tuple of (X_train_split, y_train_split, X_val, y_val)
    """
    if len(X_train) <= validation_days:
        raise ValueError(
            f"Training data ({len(X_train)} rows) is too small for "
            f"validation split of {validation_days} days"
        )
    
    split_idx = len(X_train) - validation_days
    
    X_train_split = X_train.iloc[:split_idx].copy()
    y_train_split = y_train.iloc[:split_idx].copy()
    X_val = X_train.iloc[split_idx:].copy()
    y_val = y_train.iloc[split_idx:].copy()
    
    return X_train_split, y_train_split, X_val, y_val

