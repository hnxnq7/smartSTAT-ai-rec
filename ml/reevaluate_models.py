#!/usr/bin/env python3
"""
Re-evaluate all trained models with improved inventory simulation logic.

This script loads existing trained models and re-runs evaluation with the
updated compute_inventory_metrics_simple function that includes:
- 95th percentile reorder points
- Service level targeting (99.5%)
- Variance-aware safety stock
- Multiple reorder triggers
"""

import argparse
import pandas as pd
import numpy as np
import lightgbm as lgb
from pathlib import Path
from typing import Dict
import json
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.datasets import load_dataset_files, get_dataset_info, get_all_dataset_ids
from ml.train_lgbm import prepare_features_and_labels
from ml.evaluate import compute_metrics, compute_inventory_metrics_simple, save_metrics
from ml.config import DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR


def reevaluate_model(
    data_dir: Path,
    model_dir: Path,
    dataset_id: str,
    horizon: int,
    objective: str,
) -> Dict:
    """
    Re-evaluate a trained model with improved inventory simulation.
    
    Args:
        data_dir: Data directory
        model_dir: Model directory (contains subdirectories per dataset)
        dataset_id: Dataset ID
        horizon: Forecast horizon
        objective: Model objective
    
    Returns:
        Dictionary with updated metrics
    """
    # Load data
    train_df, test_df = load_dataset_files(data_dir, dataset_id)
    
    # Load model
    model_file = model_dir / dataset_id / f"model_h{horizon}_{objective}.txt"
    if not model_file.exists():
        print(f"  ⚠️  Model not found: {model_file}")
        return None
    
    model = lgb.Booster(model_file=str(model_file))
    
    # Load existing metrics to get feature list
    metrics_file = model_dir / dataset_id / f"metrics_h{horizon}_{objective}.json"
    if not metrics_file.exists():
        print(f"  ⚠️  Metrics file not found: {metrics_file}")
        return None
    
    with open(metrics_file, 'r') as f:
        existing_metrics = json.load(f)
    
    feature_list = existing_metrics.get('features', [])
    if not feature_list:
        print(f"  ⚠️  No features found in metrics file")
        return None
    
    # Prepare features and labels
    X_train, y_train, X_test, y_test = prepare_features_and_labels(
        train_df,
        test_df,
        horizon,
        exclude_contemporaneous_used=False,
    )
    
    # Get predictions
    y_pred = model.predict(X_test, num_iteration=model.best_iteration)
    
    # Compute prediction metrics
    metrics = compute_metrics(y_test, pd.Series(y_pred), normalize_by_mean=True)
    
    # Get daily data for inventory simulation
    test_dates_for_stockout = test_df["date"].iloc[:len(y_test)]
    daily_actual = test_df["used_units"].iloc[:len(y_test)]
    daily_predicted = pd.Series(y_pred) / horizon
    
    # Get initial stock
    if 'non_expired_inventory' in test_df.columns and len(test_df) > 0:
        initial_stock = float(test_df["non_expired_inventory"].iloc[0])
    else:
        initial_stock = float(np.mean(daily_actual) * 30)
    
    # Get lead time
    try:
        dataset_info = get_dataset_info(data_dir, dataset_id)
        lead_time = int(dataset_info.get('lead_time', 3))
    except:
        lead_time = 3
    
    # Get expired units data if available
    expired_units_data = test_df["expired_units"].iloc[:len(y_test)] if 'expired_units' in test_df.columns else None
    non_expired_data = test_df["non_expired_inventory"].iloc[:len(y_test)] if 'non_expired_inventory' in test_df.columns else None
    
    # Re-compute inventory metrics with improved simulation
    # PRIORITY 3: Get category from dataset_id for category-specific multipliers
    category = dataset_id[0] if dataset_id and len(dataset_id) > 0 else None
    
    inventory_metrics = compute_inventory_metrics_simple(
        test_dates_for_stockout,
        daily_actual,
        daily_predicted,
        initial_stock,
        lead_time=lead_time,
        expired_units_actual=expired_units_data,
        non_expired_inventory_actual=non_expired_data,
        category=category,  # PRIORITY 3: Pass category for multipliers
    )
    metrics.update(inventory_metrics)
    
    # Save updated metrics
    from ml.evaluate import save_metrics
    
    save_metrics(
        metrics,
        metrics_file,
        dataset_id,
        horizon,
        objective,
        model.params,
        feature_list,
        (str(train_df["date"].min()), str(train_df["date"].max())),
        (str(test_df["date"].min()), str(test_df["date"].max())),
        None,  # quantile_alpha
    )
    
    return {
        "dataset_id": dataset_id,
        "metrics": metrics,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Re-evaluate all trained models with improved inventory simulation"
    )
    parser.add_argument(
        "--data_dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Data directory",
    )
    parser.add_argument(
        "--model_dir",
        type=Path,
        default=Path("ml/models_all_500"),
        help="Model directory",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        help="Forecast horizon",
    )
    parser.add_argument(
        "--objective",
        type=str,
        default="asymmetric",
        help="Model objective",
    )
    parser.add_argument(
        "--dataset_id",
        type=str,
        help="Optional: Re-evaluate specific dataset (default: all)",
    )
    parser.add_argument(
        "--output_csv",
        type=Path,
        default=Path("ml/results/results_improved_simulation.csv"),
        help="Output CSV path",
    )
    
    args = parser.parse_args()
    
    # Get list of datasets to re-evaluate
    if args.dataset_id:
        dataset_ids = [args.dataset_id]
    else:
        # Get all dataset IDs from model directory
        dataset_ids = sorted([
            d.name for d in args.model_dir.iterdir()
            if d.is_dir() and (d / f"model_h{args.horizon}_{args.objective}.txt").exists()
        ])
    
    print(f"=" * 70)
    print(f"Re-evaluating {len(dataset_ids)} models with improved inventory simulation")
    print(f"=" * 70)
    print(f"Data directory: {args.data_dir}")
    print(f"Model directory: {args.model_dir}")
    print(f"Horizon: {args.horizon}")
    print(f"Objective: {args.objective}")
    print()
    
    results = []
    successful = 0
    failed = 0
    
    for i, dataset_id in enumerate(dataset_ids, 1):
        print(f"[{i}/{len(dataset_ids)}] Re-evaluating {dataset_id}...", end=" ")
        
        try:
            result = reevaluate_model(
                args.data_dir,
                args.model_dir,
                dataset_id,
                args.horizon,
                args.objective,
            )
            
            if result is not None:
                m = result["metrics"]
                results.append({
                    "dataset_id": dataset_id,
                    "normalized_mae": m.get("normalized_mae"),
                    "normalized_rmse": m.get("normalized_rmse"),
                    "stockout_rate": m.get("stockout_rate"),
                    "stockout_days": m.get("stockout_days"),
                    "mape": m.get("mape"),
                    "expired_rate": m.get("expired_rate"),
                    "expired_units_total": m.get("expired_units_total"),
                    "non_expired_negative_days": m.get("non_expired_negative_days"),
                    "avg_non_expired_inventory": m.get("avg_non_expired_inventory"),
                })
                stockout = m.get("stockout_rate", 0)
                print(f"✓ Stockout: {stockout:.2f}%")
                successful += 1
            else:
                print("✗ Failed")
                failed += 1
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
            continue
    
    # Save results
    if results:
        results_df = pd.DataFrame(results)
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        results_df.to_csv(args.output_csv, index=False)
        
        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        print(f"Successfully re-evaluated: {successful}")
        print(f"Failed: {failed}")
        print(f"\nResults saved to: {args.output_csv}")
        
        if len(results_df) > 0:
            print(f"\nStockout Rate Statistics:")
            stockout = results_df["stockout_rate"].dropna()
            if len(stockout) > 0:
                print(f"  Mean: {stockout.mean():.2f}%")
                print(f"  Median: {stockout.median():.2f}%")
                print(f"  Min: {stockout.min():.2f}%")
                print(f"  Max: {stockout.max():.2f}%")
                print(f"  75th percentile: {np.percentile(stockout, 75):.2f}%")
                print(f"  90th percentile: {np.percentile(stockout, 90):.2f}%")
    else:
        print("\n✗ No results to save")


if __name__ == "__main__":
    main()
