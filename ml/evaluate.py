"""
Evaluation metrics and utilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from pathlib import Path

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


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
    use_percentile_reorder: bool = True,
    reorder_percentile: float = 0.95,  # 95th percentile for aggressive stockout prevention
    use_lookahead: bool = True,
    lookahead_days: int = 7,
    service_level_target: float = 0.995,  # Target 99.5% service level (stockout rate < 0.5%)
    use_variance_safety_stock: bool = True,  # Use demand variance for safety stock calculation
    category: Optional[str] = None,  # PRIORITY 3: Category for category-specific multipliers
    shelf_life_days: Optional[int] = None,  # Shelf life for inventory age calculations (default: 210)
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
    
    # Enhanced ordering parameters: Aggressive zero-stockout strategy
    # Use 95th percentile for reorder point to account for variance and spikes
    predicted_series = pd.Series(predicted_used)
    actual_series = pd.Series(actual_used)
    
    # Calculate demand statistics for safety stock
    mean_demand = float(predicted_series[predicted_series > 0].mean()) if (predicted_series > 0).any() else float(np.mean(actual_series))
    std_demand = float(predicted_series[predicted_series > 0].std()) if (predicted_series > 0).any() and len(predicted_series[predicted_series > 0]) > 1 else float(np.std(actual_series))
    
    if mean_demand <= 0:
        mean_demand = max(float(np.mean(actual_series)), 0.1)
    if std_demand <= 0 or np.isnan(std_demand):
        std_demand = mean_demand * 0.3  # Default to 30% coefficient of variation
    
    # Coefficient of variation for demand uncertainty
    cv_demand = std_demand / mean_demand if mean_demand > 0 else 0.3
    
    if use_percentile_reorder:
        # Use percentile-based reorder point (95th percentile by default for aggressive prevention)
        percentile_value = np.percentile(predicted_series[predicted_series > 0], reorder_percentile * 100) if (predicted_series > 0).any() else np.percentile(actual_series, reorder_percentile * 100)
        avg_predicted_for_order = percentile_value
    else:
        # Original logic: use average
        avg_predicted_for_order = mean_demand
    
    # PRIORITY 2: Dynamic Safety Stock
    # Initial safety stock calculation (will be adjusted dynamically)
    # Base Z-score for target service level (99.5% = 2.576 standard deviations)
    if HAS_SCIPY:
        try:
            base_z_score = stats.norm.ppf(service_level_target)
        except:
            base_z_score = 2.576
    else:
        if service_level_target >= 0.995:
            base_z_score = 2.576  # 99.5%
        elif service_level_target >= 0.99:
            base_z_score = 2.326  # 99%
        elif service_level_target >= 0.95:
            base_z_score = 1.645  # 95%
        else:
            base_z_score = 1.282  # 90%
    
    # Track stockout history for dynamic adjustment
    stockout_history = []  # Track last 30 days of stockouts
    lookback_window = 30  # Days to look back for stockout rate calculation
    
    # Initial safety stock calculation (will be recalculated during loop)
    if use_variance_safety_stock:
        initial_safety_stock = base_z_score * std_demand * np.sqrt(lead_time)
    else:
        initial_safety_stock = mean_demand * lead_time * 0.5
    
    # Initial reorder point
    expected_demand_leadtime = avg_predicted_for_order * lead_time
    reorder_point = expected_demand_leadtime + initial_safety_stock
    
    # Order quantity: base quantity + additional buffer based on demand uncertainty
    # Higher uncertainty (CV) leads to larger orders
    # NOTE: This is now calculated dynamically in the loop (Priority 1: Adaptive Order Quantities)
    base_order_quantity = (avg_predicted_for_order * lead_time * order_quantity_ratio)
    
    # Convert to numpy array for easier indexing
    predicted_array = np.array(predicted_used)
    actual_array = np.array(actual_used)
    
    for i, (date, actual_usage) in enumerate(zip(dates, actual_used)):
        # Process pending orders
        if i in pending_orders:
            stock += pending_orders.pop(i)
        
        # Check stockout (before usage)
        had_stockout = (stock <= 0)
        if had_stockout:
            stockout_days += 1
        
        # PRIORITY 2: Track stockout history for dynamic safety stock adjustment
        stockout_history.append(1 if had_stockout else 0)
        # Keep only last lookback_window days
        if len(stockout_history) > lookback_window:
            stockout_history.pop(0)
        
        # PRIORITY 2: Dynamic Z-score adjustment based on recent stockout rate
        if len(stockout_history) >= 7:  # Need at least 7 days of history
            recent_stockout_rate = sum(stockout_history) / len(stockout_history)
            
            # Adjust Z-score based on recent performance
            if recent_stockout_rate < 0.005:  # < 0.5% stockout rate
                dynamic_z_score = 2.0  # 95% service level (down from 99.5%)
            elif recent_stockout_rate < 0.01:  # < 1% stockout rate
                dynamic_z_score = 2.33  # 99% service level
            else:
                dynamic_z_score = base_z_score  # Keep at 99.5% if stockouts are higher
            
            # Recalculate safety stock and reorder point with dynamic Z-score
            if use_variance_safety_stock:
                dynamic_safety_stock = dynamic_z_score * std_demand * np.sqrt(lead_time)
            else:
                dynamic_safety_stock = mean_demand * lead_time * 0.5
            reorder_point = expected_demand_leadtime + dynamic_safety_stock
        else:
            # Use initial values for first few days
            dynamic_z_score = base_z_score
        
        # Apply usage
        stock = max(0, stock - actual_usage)
        
        # PRIORITY 1: Adaptive Order Quantities (Solution 1)
        # Calculate order quantity based on recent consumption instead of fixed multiplier
        if i >= 14:
            # Use last 14 days of actual consumption for more accurate ordering
            recent_consumption = np.mean(actual_array[max(0, i-14):i])
        elif i >= 7:
            # Use last 7 days if 14 days not available
            recent_consumption = np.mean(actual_array[max(0, i-7):i])
        else:
            # Fall back to predicted average
            recent_consumption = avg_predicted_for_order
        
        # Expected days until next reorder (lead time + buffer)
        expected_days_until_reorder = max(lead_time + 3, 7)  # At least 7 days
        
        # UNDER_50_PERCENT: Strategy 3 - Category-Specific Buffers (reduced from 10%)
        category_buffers = {
            'A': 1.02,  # 2% buffer - stable demand
            'B': 1.01,  # 1% buffer - low volume, minimize waste
            'C': 1.02,  # 2% buffer - weekly pattern
            'D': 1.05,  # 5% buffer - trending, need some buffer
            'E': 1.08,  # 8% buffer - burst events, need safety
        }
        buffer_multiplier = category_buffers.get(category, 1.02) if category else 1.02
        
        # UNDER_50_PERCENT: Strategy 2 - Category-Specific Order Caps
        category_order_caps = {
            'A': 12,  # Stable - can order less
            'B': 10,  # Low volume - even smaller orders
            'C': 12,  # Weekly pattern - smaller orders
            'D': 16,  # Trending - need slightly more buffer
            'E': 18,  # Burst events - need buffer but not too much
        }
        max_order_days_supply = category_order_caps.get(category, 12) if category else 12
        
        # PRIORITY 3: Category-Specific Order Multipliers (keep for compatibility)
        category_multipliers = {
            'A': 1.0,   # Stable demand - order exactly what's needed
            'B': 0.8,   # Low volume - smaller orders, more frequent
            'C': 1.0,   # Weekly pattern - order weekly amounts
            'D': 1.1,   # Trending - slightly more for trends
            'E': 1.2,   # Burst events - need buffer for spikes
        }
        category_multiplier = category_multipliers.get(category, 1.0) if category else 1.0
        
        # Adaptive order quantity with reduced buffer
        order_quantity_base = recent_consumption * expected_days_until_reorder * buffer_multiplier
        # Apply category-specific multiplier
        adaptive_order_quantity = order_quantity_base * category_multiplier
        
        # Apply category-specific order cap
        max_order = recent_consumption * max_order_days_supply
        adaptive_order_quantity = min(adaptive_order_quantity, max_order)
        
        # Ensure minimum order quantity (at least lead_time days)
        min_order = recent_consumption * lead_time
        adaptive_order_quantity = max(adaptive_order_quantity, min_order)
        
        # UNDER_50_PERCENT: Strategy 1 - Apply shelf-life aware order quantity reduction
        # Calculate inventory age ratio first to apply reductions
        # Use shelf_life_days parameter if provided, otherwise default to 210 (medium hospital size)
        estimated_shelf_life_days = shelf_life_days if shelf_life_days is not None else 210
        if recent_consumption > 0:
            current_inventory_days = stock / (recent_consumption + 1e-6)
            inventory_age_ratio = current_inventory_days / estimated_shelf_life_days
        else:
            inventory_age_ratio = 0
        
        # Reduce order quantity based on inventory age
        if inventory_age_ratio > 0.25:
            # If inventory represents >25% of shelf life, reduce orders by 50%
            adaptive_order_quantity = adaptive_order_quantity * 0.5
        elif inventory_age_ratio > 0.15:
            # If inventory represents >15% of shelf life, reduce orders by 25%
            adaptive_order_quantity = adaptive_order_quantity * 0.75
        
        # Enhanced reorder logic: Multiple triggers for aggressive stockout prevention
        should_reorder = False
        
        # PRIORITY 1: Inventory-Aware Ordering (Solution 2)
        # Calculate total available inventory (current + pending orders)
        total_pending = sum(pending_orders.values()) if pending_orders else 0
        total_available = stock + total_pending
        
        # Calculate days coverage (for reorder delay logic)
        if recent_consumption > 0:
            days_coverage = stock / (recent_consumption + 1e-6)
        else:
            days_coverage = 0
        
        # Adjust reorder point based on inventory age
        if inventory_age_ratio < 0.15:
            # If inventory is relatively new (<15% of shelf life), raise reorder point
            adjusted_reorder_point = reorder_point * 1.3
        elif inventory_age_ratio > 0.30:
            # If inventory is aging (>30% of shelf life), lower reorder point
            adjusted_reorder_point = reorder_point * 0.8
        else:
            adjusted_reorder_point = reorder_point
        
        # UNDER_50_PERCENT: Strategy 1 - Stop orders if inventory too old (>40% of shelf life)
        # Also consume inventory before reordering (refined threshold: 10 days instead of 12)
        if inventory_age_ratio > 0.40:
            should_reorder = False  # Don't order - consume existing inventory first
        elif days_coverage > 10:
            # If inventory can cover 10+ days, delay reorder (refined from 12 days)
            adjusted_reorder_point = max(adjusted_reorder_point, reorder_point * 1.2)
        
        # UNDER_50_PERCENT: Strategy 1 - Apply shelf-life aware order quantity reduction
        if inventory_age_ratio > 0.25:
            # If inventory represents >25% of shelf life, reduce orders by 50%
            adaptive_order_quantity = adaptive_order_quantity * 0.5
        elif inventory_age_ratio > 0.15:
            # If inventory represents >15% of shelf life, reduce orders by 25%
            adaptive_order_quantity = adaptive_order_quantity * 0.75
        
        if use_lookahead:
            # Strategy 1: Look-ahead logic with aggressive safety buffer
            # Check predicted demand over (lead_time + lookahead) period
            lookahead_start = i + 1
            lookahead_end = min(lookahead_start + lead_time + lookahead_days, len(predicted_array))
            if lookahead_end > lookahead_start:
                predicted_demand_ahead = np.sum(predicted_array[lookahead_start:lookahead_end])
            else:
                predicted_demand_ahead = 0
            
            # Aggressive safety buffer: 50% buffer for near-zero stockouts
            # This ensures we reorder well before stock might run out
            safety_factor = 1.5  # 50% safety buffer (increased from 20%)
            
            # INVENTORY-AWARE: Only reorder if total available inventory < projected demand * safety_factor
            # This prevents over-ordering when current stock + pending orders are sufficient
            if total_available < predicted_demand_ahead * safety_factor:
                # Trigger 1: If total available inventory < predicted demand ahead * safety_factor
                should_reorder = True
            
            # Trigger 2: If stock is below adjusted reorder point (Priority 4: consume inventory first)
            # But still check total_available to avoid redundant orders
            if stock <= adjusted_reorder_point and total_available < predicted_demand_ahead * 1.2:
                should_reorder = True
            
            # Trigger 3: Early warning - if stock is getting low relative to upcoming demand
            # Reorder if current stock can't cover next few days with buffer
            early_warning_days = max(lead_time, 5)  # At least lead_time or 5 days
            early_warning_start = i + 1
            early_warning_end = min(early_warning_start + early_warning_days, len(predicted_array))
            if early_warning_end > early_warning_start:
                short_term_demand = np.sum(predicted_array[early_warning_start:early_warning_end])
            else:
                short_term_demand = 0
            if total_available < short_term_demand * 1.3:  # 30% buffer for early warning
                should_reorder = True
        else:
            # Fallback: Original logic - reorder if stock <= adjusted_reorder_point (Priority 4)
            # But still check total_available
            if stock <= adjusted_reorder_point and total_available < avg_predicted_for_order * lead_time * 1.5:
                should_reorder = True
        
        if should_reorder:
            order_arrival = i + lead_time
            if order_arrival < len(actual_used):
                if order_arrival not in pending_orders:
                    pending_orders[order_arrival] = 0
                # Use adaptive order quantity instead of fixed order_quantity
                pending_orders[order_arrival] += adaptive_order_quantity
    
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

