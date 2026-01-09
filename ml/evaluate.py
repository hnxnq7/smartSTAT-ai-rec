"""
Evaluation metrics and utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from pathlib import Path


def compute_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    handle_zero: bool = True,
) -> Dict[str, float]:
    """
    Compute MAE, RMSE, and MAPE metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        handle_zero: If True, skip MAPE calculation for near-zero targets (< 1)
    
    Returns:
        Dictionary with metrics: mae, rmse, mape, mape_count
    """
    # Ensure same length
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    # Remove any NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {"mae": np.nan, "rmse": np.nan, "mape": np.nan, "mape_count": 0}
    
    # MAE
    mae = np.mean(np.abs(y_true_clean - y_pred_clean))
    
    # RMSE
    rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
    
    # MAPE (handle near-zero targets)
    if handle_zero:
        # Only calculate MAPE for targets >= 1
        mape_mask = y_true_clean >= 1
        if mape_mask.sum() > 0:
            mape = np.mean(np.abs((y_true_clean[mape_mask] - y_pred_clean[mape_mask]) / y_true_clean[mape_mask])) * 100
            mape_count = mape_mask.sum()
        else:
            mape = np.nan
            mape_count = 0
    else:
        # Calculate MAPE for all (may have division by zero issues)
        non_zero_mask = y_true_clean != 0
        if non_zero_mask.sum() > 0:
            mape = np.mean(np.abs((y_true_clean[non_zero_mask] - y_pred_clean[non_zero_mask]) / y_true_clean[non_zero_mask])) * 100
            mape_count = non_zero_mask.sum()
        else:
            mape = np.nan
            mape_count = 0
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mape": float(mape) if not np.isnan(mape) else None,
        "mape_count": int(mape_count),
        "total_samples": int(len(y_true_clean)),
    }


def save_predictions(
    dates: pd.Series,
    y_true: pd.Series,
    y_pred: pd.Series,
    output_path: Path,
    dataset_id: str,
    horizon: int,
) -> None:
    """
    Save predictions vs actuals to CSV.
    
    Args:
        dates: Date column
        y_true: True values
        y_pred: Predicted values
        output_path: Path to save CSV
        dataset_id: Dataset ID for metadata
        horizon: Forecast horizon
    """
    results_df = pd.DataFrame({
        "date": dates,
        "actual": y_true,
        "predicted": y_pred,
        "error": y_true - y_pred,
        "abs_error": np.abs(y_true - y_pred),
        "pct_error": (y_true - y_pred) / y_true * 100 if (y_true != 0).any() else np.nan,
    })
    
    results_df["dataset_id"] = dataset_id
    results_df["horizon"] = horizon
    
    # Reorder columns
    results_df = results_df[[
        "dataset_id", "date", "horizon", "actual", "predicted",
        "error", "abs_error", "pct_error"
    ]]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)
    print(f"Saved predictions to {output_path}")


def save_metrics(
    metrics: Dict[str, float],
    output_path: Path,
    dataset_id: str,
    horizon: int,
    objective: str,
    model_params: Dict,
    feature_list: list,
    train_range: Tuple[str, str],
    test_range: Tuple[str, str],
    quantile_alpha: Optional[float] = None,
) -> None:
    """
    Save evaluation metrics and metadata to JSON.
    
    Args:
        metrics: Dictionary of computed metrics
        output_path: Path to save JSON
        dataset_id: Dataset ID
        horizon: Forecast horizon
        objective: Model objective (l2, quantile)
        model_params: Model hyperparameters
        feature_list: List of feature names used
        train_range: Tuple of (start_date, end_date) for training
        test_range: Tuple of (start_date, end_date) for testing
        quantile_alpha: Quantile alpha (if using quantile regression)
    """
    import json
    
    metadata = {
        "dataset_id": dataset_id,
        "horizon": horizon,
        "objective": objective,
        "quantile_alpha": quantile_alpha,
        "model_params": model_params,
        "features": feature_list,
        "train_range": {
            "start": train_range[0],
            "end": train_range[1],
        },
        "test_range": {
            "start": test_range[0],
            "end": test_range[1],
        },
        "metrics": metrics,
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved metrics to {output_path}")

