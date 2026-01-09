"""
CLI script for training LightGBM models on demand forecasting datasets.
"""

import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
from typing import Dict, List, Optional
import json

from ml.config import (
    DEFAULT_DATA_DIR,
    DEFAULT_OUTPUT_DIR,
    SUPPORTED_HORIZONS,
    SUPPORTED_OBJECTIVES,
    DEFAULT_LIGHTGBM_PARAMS,
    DEFAULT_QUANTILE_ALPHA,
    VALIDATION_SPLIT_DAYS,
    RANDOM_SEED,
    FEATURE_COLUMNS,
    EARLY_STOPPING_ROUNDS,
)
from ml.datasets import (
    load_dataset_files,
    get_all_dataset_ids,
    get_dataset_info,
)
from ml.features import (
    prepare_features_and_labels,
    create_time_based_validation_split,
)
from ml.evaluate import (
    compute_metrics,
    save_predictions,
    save_metrics,
    compute_stockout_rate,
)


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    objective: str = "l2",
    quantile_alpha: float = 0.95,
    params: Optional[Dict] = None,
    early_stopping_rounds: int = EARLY_STOPPING_ROUNDS,
) -> lgb.Booster:
    """
    Train a LightGBM model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        objective: Model objective ("l2" or "quantile")
        quantile_alpha: Alpha for quantile regression (if objective="quantile")
        params: LightGBM parameters (defaults used if None)
        early_stopping_rounds: Early stopping patience
    
    Returns:
        Trained LightGBM model
    """
    if params is None:
        params = DEFAULT_LIGHTGBM_PARAMS.copy()
    
    # Set objective
    if objective == "quantile":
        params["objective"] = "quantile"
        params["alpha"] = quantile_alpha
    else:
        params["objective"] = "regression"
        params["metric"] = "rmse"
    
    # Create datasets
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    # Train model
    model = lgb.train(
        params,
        train_data,
        valid_sets=[train_data, val_data],
        valid_names=["train", "val"],
        num_boost_round=1000,
        callbacks=[
            lgb.early_stopping(early_stopping_rounds, verbose=True),
            lgb.log_evaluation(period=100),
        ],
    )
    
    return model


def train_and_evaluate_dataset(
    data_dir: Path,
    dataset_id: str,
    horizon: int,
    objective: str,
    quantile_alpha: float,
    output_dir: Path,
    exclude_contemporaneous_used: bool = False,
) -> Dict:
    """
    Train and evaluate a model for a single dataset.
    
    Args:
        data_dir: Root directory containing datasets
        dataset_id: Dataset ID (e.g., "A1")
        horizon: Forecast horizon in days
        objective: Model objective ("l2" or "quantile")
        quantile_alpha: Alpha for quantile regression
        output_dir: Directory to save models and results
        exclude_contemporaneous_used: Exclude used_units from features
    
    Returns:
        Dictionary with results and metrics
    """
    print(f"\n{'='*60}")
    print(f"Dataset: {dataset_id}, Horizon: {horizon}, Objective: {objective}")
    print(f"{'='*60}")
    
    # Load data
    train_df, test_df = load_dataset_files(data_dir, dataset_id)
    print(f"Train: {len(train_df)} rows ({train_df['date'].min()} to {train_df['date'].max()})")
    print(f"Test: {len(test_df)} rows ({test_df['date'].min()} to {test_df['date'].max()})")
    
    # Prepare features and labels
    X_train, y_train, X_test, y_test = prepare_features_and_labels(
        train_df,
        test_df,
        horizon,
        exclude_contemporaneous_used=exclude_contemporaneous_used,
    )
    print(f"Features: {len(X_train.columns)} ({', '.join(X_train.columns[:5])}...)")
    print(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Create validation split
    X_train_split, y_train_split, X_val, y_val = create_time_based_validation_split(
        X_train, y_train, validation_days=VALIDATION_SPLIT_DAYS
    )
    print(f"Train split: {len(X_train_split)}, Validation: {len(X_val)}")
    
    # Train model
    print("\nTraining model...")
    model = train_model(
        X_train_split,
        y_train_split,
        X_val,
        y_val,
        objective=objective,
        quantile_alpha=quantile_alpha,
    )
    
    # Evaluate on test set
    print("\nEvaluating on test set...")
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    
    # Compute metrics (with normalization)
    metrics = compute_metrics(y_test, pd.Series(y_pred), normalize_by_mean=True)
    
    # Compute stockout rate
    # Get dates and actual daily usage for test set
    # We need actual daily usage, not horizon-sum
    # Use the original test_df 'used_units' column (daily)
    test_dates_for_stockout = test_df["date"].iloc[:len(y_test)]
    daily_actual = test_df["used_units"].iloc[:len(y_test)]
    
    # We forecast horizon-sum (y_pred is sum over H days)
    # For stockout simulation, we need daily forecasts
    # Convert by dividing by horizon to get average daily forecast
    # Note: This assumes uniform distribution over horizon, which is a simplification
    # A more sophisticated approach would back-cast daily from horizon-sum, but this is reasonable
    daily_predicted = pd.Series(y_pred) / horizon
    
    # Get initial stock from test data (first day's non_expired_inventory)
    # If not available, estimate from average usage
    if 'non_expired_inventory' in test_df.columns and len(test_df) > 0:
        initial_stock = float(test_df["non_expired_inventory"].iloc[0])
    else:
        # Estimate: enough for 30 days at average usage
        initial_stock = float(np.mean(daily_actual) * 30)
    
    # Get lead time from dataset info if available
    try:
        from ml.datasets import get_dataset_info
        dataset_info = get_dataset_info(data_dir, dataset_id)
        lead_time = int(dataset_info.get('lead_time', 3))
    except:
        lead_time = 3
    
    stockout_metrics = compute_stockout_rate(
        test_dates_for_stockout,
        daily_actual,
        daily_predicted,
        initial_stock,
        lead_time=lead_time,
    )
    metrics.update(stockout_metrics)
    
    print(f"Normalized MAE: {metrics['normalized_mae']:.4f}, "
          f"Stockout Rate: {metrics['stockout_rate']:.2f}%, "
          f"MAPE: {metrics['mape']:.1f}%" if metrics['mape'] else 
          f"Normalized MAE: {metrics['normalized_mae']:.4f}, "
          f"Stockout Rate: {metrics['stockout_rate']:.2f}%")
    
    # Save model
    model_dir = output_dir / dataset_id
    model_dir.mkdir(parents=True, exist_ok=True)
    
    model_filename = f"model_h{horizon}_{objective}"
    if objective == "quantile":
        model_filename += f"_q{quantile_alpha}"
    model_filename += ".txt"
    model_path = model_dir / model_filename
    model.save_model(str(model_path))
    print(f"Saved model to {model_path}")
    
    # Save feature importance
    feature_importance = pd.DataFrame({
        "feature": X_train.columns,
        "importance": model.feature_importance(importance_type="gain"),
    }).sort_values("importance", ascending=False)
    
    importance_path = model_dir / f"feature_importance_h{horizon}_{objective}.csv"
    feature_importance.to_csv(importance_path, index=False)
    print(f"Saved feature importance to {importance_path}")
    
    # Save predictions
    # Get dates for test set (need to account for dropped rows)
    test_dates = test_df["date"].iloc[:-horizon] if len(test_df) > horizon else test_df["date"]
    if len(test_dates) != len(y_test):
        # Align dates with y_test
        test_dates = test_df["date"].iloc[:len(y_test)]
    
    predictions_path = model_dir / f"predictions_h{horizon}_{objective}.csv"
    save_predictions(
        test_dates,
        y_test,
        pd.Series(y_pred),
        predictions_path,
        dataset_id,
        horizon,
    )
    
    # Save metrics
    metrics_path = model_dir / f"metrics_h{horizon}_{objective}.json"
    save_metrics(
        metrics,
        metrics_path,
        dataset_id,
        horizon,
        objective,
        model.params,
        list(X_train.columns),
        (str(train_df["date"].min()), str(train_df["date"].max())),
        (str(test_df["date"].min()), str(test_df["date"].max())),
        quantile_alpha if objective == "quantile" else None,
    )
    
    return {
        "dataset_id": dataset_id,
        "horizon": horizon,
        "objective": objective,
        "metrics": metrics,
        "model_path": str(model_path),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Train LightGBM models for demand forecasting"
    )
    parser.add_argument(
        "--data_dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Root directory containing datasets (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--dataset_id",
        type=str,
        default="A1",
        help='Dataset ID to train (e.g., "A1") or "all" for all datasets',
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        choices=SUPPORTED_HORIZONS,
        help=f"Forecast horizon in days (choices: {SUPPORTED_HORIZONS})",
    )
    parser.add_argument(
        "--objective",
        type=str,
        default="l2",
        choices=SUPPORTED_OBJECTIVES,
        help=f"Model objective (choices: {SUPPORTED_OBJECTIVES})",
    )
    parser.add_argument(
        "--quantile_alpha",
        type=float,
        default=DEFAULT_QUANTILE_ALPHA,
        help="Alpha for quantile regression (default: 0.95)",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for models and results (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--exclude_contemporaneous_used",
        action="store_true",
        help="Exclude 'used_units' from features (use only lags)",
    )
    
    args = parser.parse_args()
    
    # Get list of datasets to process
    if args.dataset_id.lower() == "all":
        dataset_ids = get_all_dataset_ids(args.data_dir)
        print(f"Training on {len(dataset_ids)} datasets: {dataset_ids}")
    else:
        dataset_ids = [args.dataset_id]
    
    # Train and evaluate each dataset
    results = []
    for dataset_id in dataset_ids:
        try:
            result = train_and_evaluate_dataset(
                args.data_dir,
                dataset_id,
                args.horizon,
                args.objective,
                args.quantile_alpha,
                args.output_dir,
                args.exclude_contemporaneous_used,
            )
            results.append(result)
        except Exception as e:
            print(f"\nError processing {dataset_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary table
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Dataset':<10} {'Horizon':<8} {'Norm MAE':<12} {'Stockout %':<12} {'MAPE':<10}")
    print("-" * 80)
    
    for result in results:
        m = result["metrics"]
        norm_mae = m.get('normalized_mae', np.nan)
        stockout_rate = m.get('stockout_rate', np.nan)
        mape_str = f"{m['mape']:.1f}%" if m.get("mape") else "N/A"
        norm_mae_str = f"{norm_mae:.4f}" if not np.isnan(norm_mae) else "N/A"
        stockout_str = f"{stockout_rate:.2f}%" if not np.isnan(stockout_rate) else "N/A"
        print(
            f"{result['dataset_id']:<10} "
            f"{result['horizon']:<8} "
            f"{norm_mae_str:<12} "
            f"{stockout_str:<12} "
            f"{mape_str:<10}"
        )
    
    print(f"{'='*80}")
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()

