"""
Evaluation metrics and utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path


def compute_metrics(
    y_true: pd.Series,
    y_pred: pd.Series,
    handle_zero: bool = True,
    normalize_by_mean: bool = True,
) -> Dict[str, float]:
    """
    Compute MAE, RMSE, MAPE, and normalized metrics.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        handle_zero: If True, skip MAPE calculation for near-zero targets (< 1)
        normalize_by_mean: If True, normalize errors by mean of y_true (for hospital size normalization)
    
    Returns:
        Dictionary with metrics: mae, rmse, mape, mape_count, normalized_mae, normalized_rmse
    """
    # Ensure same length
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true={len(y_true)}, y_pred={len(y_pred)}")
    
    # Remove any NaN values
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_true_clean = y_true[mask]
    y_pred_clean = y_pred[mask]
    
    if len(y_true_clean) == 0:
        return {
            "mae": np.nan, "rmse": np.nan, "mape": np.nan, "mape_count": 0,
            "normalized_mae": np.nan, "normalized_rmse": np.nan
        }
    
    # MAE
    mae = np.mean(np.abs(y_true_clean - y_pred_clean))
    
    # RMSE
    rmse = np.sqrt(np.mean((y_true_clean - y_pred_clean) ** 2))
    
    # Normalized errors (by mean of true values - normalizes by hospital size)
    mean_true = np.mean(y_true_clean)
    if mean_true > 0 and normalize_by_mean:
        normalized_mae = mae / mean_true
        normalized_rmse = rmse / mean_true
    else:
        normalized_mae = np.nan
        normalized_rmse = np.nan
    
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
        "normalized_mae": float(normalized_mae) if not np.isnan(normalized_mae) else None,
        "normalized_rmse": float(normalized_rmse) if not np.isnan(normalized_rmse) else None,
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


def compute_stockout_rate(
    dates: pd.Series,
    actual_used: pd.Series,
    predicted_used: pd.Series,
    initial_stock: float,
    lead_time: int = 3,
    reorder_point_ratio: float = 0.3,
    order_quantity_multiplier: float = 1.5,
) -> Dict[str, float]:
    """
    Simulate inventory and calculate stockout rate based on predictions vs actuals.
    
    Args:
        dates: Date series
        actual_used: Actual daily usage (true values)
        predicted_used: Predicted daily usage (forecasts)
        initial_stock: Starting inventory level
        lead_time: Days between ordering and receiving
        reorder_point_ratio: Reorder when stock <= this ratio * avg_daily_usage * days_of_coverage
        order_quantity_multiplier: Order quantity = avg_daily_usage * days_of_coverage * multiplier
    
    Returns:
        Dictionary with stockout_rate, avg_stock, stockout_days
    """
    if len(actual_used) != len(predicted_used):
        raise ValueError("actual_used and predicted_used must have same length")
    
    # Simulate inventory based on predictions
    stock = initial_stock
    stockout_days = 0
    total_stock = 0
    pending_orders = {}  # {arrival_day: quantity}
    
    avg_predicted = np.mean(predicted_used[predicted_used > 0]) if (predicted_used > 0).any() else np.mean(actual_used)
    days_of_coverage = 30  # Order to cover ~30 days
    reorder_point = avg_predicted * days_of_coverage * reorder_point_ratio
    order_quantity = avg_predicted * days_of_coverage * order_quantity_multiplier
    
    for i, (date, actual_usage) in enumerate(zip(dates, actual_used)):
        # Process pending orders that arrive today
        if i in pending_orders:
            stock += pending_orders.pop(i)
        
        # Check if stockout occurs (before applying usage)
        if stock <= 0:
            stockout_days += 1
        
        # Apply actual usage (we simulate with predicted, but evaluate with actual)
        stock = max(0, stock - actual_usage)
        total_stock += stock
        
        # Check reorder point (based on predicted demand pattern)
        if stock <= reorder_point:
            order_arrival = i + lead_time
            if order_arrival < len(actual_used):
                if order_arrival not in pending_orders:
                    pending_orders[order_arrival] = 0
                pending_orders[order_arrival] += order_quantity
    
    stockout_rate = (stockout_days / len(actual_used)) * 100 if len(actual_used) > 0 else 0
    avg_stock = total_stock / len(actual_used) if len(actual_used) > 0 else 0
    
    return {
        "stockout_rate": float(stockout_rate),
        "stockout_days": int(stockout_days),
        "avg_stock": float(avg_stock),
        "total_days": int(len(actual_used)),
    }


def compute_inventory_metrics_simple(
    dates: pd.Series,
    actual_used: pd.Series,
    predicted_used: pd.Series,
    initial_stock: float,
    lead_time: int = 3,
    reorder_point_ratio: float = 1.5,
    order_quantity_ratio: float = 3.0,
    expired_units_actual: Optional[pd.Series] = None,
    non_expired_inventory_actual: Optional[pd.Series] = None,
) -> Dict[str, float]:
    """
    Compute inventory metrics using actual expiration data if available.
    
    Simulates inventory ordering based on predictions, but uses actual expired_units
    and non_expired_inventory data for accurate tracking.
    
    Enhanced version that uses percentile-based reorder points and look-ahead logic.
    
    Args:
        dates: Date series
        actual_used: Actual daily usage
        predicted_used: Predicted daily usage (for ordering decisions)
        initial_stock: Starting inventory level
        lead_time: Days between ordering and receiving
        reorder_point_ratio: Reorder when stock covers this ratio * lead_time days of predicted usage
        order_quantity_ratio: Order enough for this ratio * lead_time days of predicted usage
        expired_units_actual: Actual expired units per day (from data)
        non_expired_inventory_actual: Actual non-expired inventory per day (from data)
    
    Returns:
        Dictionary with metrics including stockout_rate, expired_units_total, etc.
    """
    if len(actual_used) != len(predicted_used):
        raise ValueError("actual_used and predicted_used must have same length")
    
    # Use actual data if available
    use_actual_data = (expired_units_actual is not None and 
                      non_expired_inventory_actual is not None and
                      len(expired_units_actual) == len(actual_used) and
                      len(non_expired_inventory_actual) == len(actual_used))
    
    if use_actual_data:
        # Use actual expiration and inventory data
        total_expired = float(expired_units_actual.sum())
        non_expired_negative_days = int((non_expired_inventory_actual < 0).sum())
        avg_non_expired = float(non_expired_inventory_actual.mean())
    else:
        # Fallback: simple simulation (original compute_stockout_rate logic)
        total_expired = 0.0
        non_expired_negative_days = 0
        avg_non_expired = 0.0
    
    # Stockout simulation (based on predictions for ordering, actual usage for consumption)
    stock = initial_stock
    stockout_days = 0
    pending_orders = {}
    
    # Enhanced ordering parameters: Use percentile-based reorder point to account for variance
    use_percentile_reorder = True
    reorder_percentile = 0.75
    use_lookahead = True
    lookahead_days = 7
    
    if use_percentile_reorder:
        # Use percentile-based reorder point to account for variance and spikes
        percentile_value = np.percentile(predicted_used[predicted_used > 0], reorder_percentile * 100) if (predicted_used > 0).any() else np.percentile(actual_used, reorder_percentile * 100)
        avg_predicted_for_order = percentile_value
        reorder_point = percentile_value * lead_time * reorder_point_ratio
    else:
        # Original logic: use average
        avg_predicted = np.mean(predicted_used[predicted_used > 0]) if (predicted_used > 0).any() else max(np.mean(actual_used), 0.1)
        avg_predicted_for_order = avg_predicted
        reorder_point = avg_predicted * lead_time * reorder_point_ratio
    
    order_quantity = avg_predicted_for_order * lead_time * order_quantity_ratio
    
    # Convert to numpy array for easier indexing
    predicted_array = np.array(predicted_used)
    
    for i, (date, actual_usage) in enumerate(zip(dates, actual_used)):
        # Process pending orders
        if i in pending_orders:
            stock += pending_orders.pop(i)
        
        # Check stockout (before usage)
        if stock <= 0:
            stockout_days += 1
        
        # Apply usage
        stock = max(0, stock - actual_usage)
        
        # Enhanced reorder logic
        should_reorder = False
        
        if use_lookahead:
            # Look ahead logic: Check if predicted demand in next (lead_time + lookahead) days exceeds current stock
            lookahead_end = min(i + lead_time + lookahead_days, len(predicted_array))
            predicted_demand_ahead = np.sum(predicted_array[i:lookahead_end])
            
            # Safety buffer: order if predicted demand ahead > current stock * safety_factor
            safety_factor = 1.2  # 20% safety buffer
            if predicted_demand_ahead > stock * safety_factor:
                should_reorder = True
        else:
            # Original logic: reorder if stock <= reorder_point
            if stock <= reorder_point:
                should_reorder = True
        
        if should_reorder:
            order_arrival = i + lead_time
            if order_arrival < len(actual_used):
                if order_arrival not in pending_orders:
                    pending_orders[order_arrival] = 0
                pending_orders[order_arrival] += order_quantity
    
    total_days = len(actual_used)
    stockout_rate = (stockout_days / total_days) * 100 if total_days > 0 else 0
    total_usage = float(actual_used.sum())
    expired_rate = (total_expired / (total_expired + total_usage)) * 100 if (total_expired + total_usage) > 0 else 0
    
    return {
        "stockout_rate": float(stockout_rate),
        "stockout_days": int(stockout_days),
        "expired_units_total": float(total_expired),
        "expired_rate": float(expired_rate),
        "non_expired_negative_days": int(non_expired_negative_days),
        "avg_non_expired_inventory": float(avg_non_expired),
        "total_days": int(total_days),
    }

