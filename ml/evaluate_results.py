"""
Evaluation script for aggregated model results.

This script helps analyze and visualize results from trained LightGBM models
across all datasets.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import argparse


def load_all_metrics(models_dir: Path, horizon: int, objective: str) -> pd.DataFrame:
    """
    Load metrics from all trained models.
    
    Args:
        models_dir: Directory containing model outputs (one subdirectory per dataset)
        horizon: Forecast horizon (14, 30, etc.)
        objective: Model objective ('l2', 'quantile')
    
    Returns:
        DataFrame with metrics for all datasets
    """
    results = []
    
    for dataset_dir in sorted(models_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        
        dataset_id = dataset_dir.name
        metrics_file = dataset_dir / f"metrics_h{horizon}_{objective}.json"
        
        if not metrics_file.exists():
            print(f"Warning: Missing metrics for {dataset_id}")
            continue
        
        try:
            with open(metrics_file) as f:
                data = json.load(f)
            
            results.append({
                "dataset_id": dataset_id,
                "normalized_mae": data["metrics"].get("normalized_mae"),
                "normalized_rmse": data["metrics"].get("normalized_rmse"),
                "stockout_rate": data["metrics"].get("stockout_rate"),
                "stockout_days": data["metrics"].get("stockout_days", 0),
                "mape": data["metrics"].get("mape"),
                "mape_count": data["metrics"].get("mape_count", 0),
                "total_samples": data["metrics"].get("total_samples", 0),
                "horizon": data["horizon"],
                "objective": data["objective"],
                # Keep raw metrics for reference
                "mae": data["metrics"].get("mae"),
                "rmse": data["metrics"].get("rmse"),
            })
        except Exception as e:
            print(f"Error loading {metrics_file}: {e}")
    
    if not results:
        raise ValueError("No metrics found!")
    
    return pd.DataFrame(results)


def load_predictions(models_dir: Path, dataset_id: str, horizon: int, objective: str) -> pd.DataFrame:
    """
    Load predictions for a specific dataset.
    
    Args:
        models_dir: Directory containing model outputs
        dataset_id: Dataset ID (e.g., 'A1')
        horizon: Forecast horizon
        objective: Model objective
    
    Returns:
        DataFrame with predictions vs actuals
    """
    pred_file = models_dir / dataset_id / f"predictions_h{horizon}_{objective}.csv"
    
    if not pred_file.exists():
        raise FileNotFoundError(f"Predictions file not found: {pred_file}")
    
    return pd.read_csv(pred_file)


def print_summary_statistics(df: pd.DataFrame) -> None:
    """Print summary statistics for all models."""
    print("\n" + "=" * 70)
    print("AGGREGATE MODEL PERFORMANCE SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal Datasets: {len(df)}")
    print(f"\nMetric Summary (Normalized by Hospital Size):")
    
    if 'normalized_mae' in df.columns:
        norm_mae = df['normalized_mae'].dropna()
        if len(norm_mae) > 0:
            print(f"  Normalized MAE - Mean: {norm_mae.mean():.4f}, Std: {norm_mae.std():.4f}, "
                  f"Min: {norm_mae.min():.4f}, Max: {norm_mae.max():.4f}")
    
    if 'stockout_rate' in df.columns:
        stockout = df['stockout_rate'].dropna()
        if len(stockout) > 0:
            print(f"  Stockout Rate - Mean: {stockout.mean():.2f}%, Std: {stockout.std():.2f}%, "
                  f"Min: {stockout.min():.2f}%, Max: {stockout.max():.2f}%")
            print(f"  Total Stockout Days: {df['stockout_days'].sum() if 'stockout_days' in df.columns else 'N/A'}")
    
    if 'mape' in df.columns:
        mape = df['mape'].dropna()
        if len(mape) > 0:
            print(f"  MAPE - Mean: {mape.mean():.2f}%, Std: {mape.std():.2f}%, "
                  f"Min: {mape.min():.2f}%, Max: {mape.max():.2f}%")
    
    # Percentiles
    if 'normalized_mae' in df.columns:
        norm_mae = df['normalized_mae'].dropna()
        if len(norm_mae) > 0:
            print(f"\nPercentiles (Normalized MAE):")
            for p in [25, 50, 75, 90, 95]:
                val = np.percentile(norm_mae, p)
                print(f"  {p}th percentile: {val:.4f}")
    
    if 'stockout_rate' in df.columns:
        stockout = df['stockout_rate'].dropna()
        if len(stockout) > 0:
            print(f"\nPercentiles (Stockout Rate):")
            for p in [25, 50, 75, 90, 95]:
                val = np.percentile(stockout, p)
                print(f"  {p}th percentile: {val:.2f}%")


def print_top_performers(df: pd.DataFrame, metric: str = 'stockout_rate', n: int = 5) -> None:
    """Print top N best and worst performing datasets."""
    # Use stockout_rate by default, fall back to normalized_mae
    if metric not in df.columns:
        metric = 'normalized_mae' if 'normalized_mae' in df.columns else 'stockout_rate'
    
    print(f"\n{'=' * 70}")
    print(f"TOP {n} BEST PERFORMING (by {metric.upper()})")
    print("=" * 70)
    
    metric_df = df.dropna(subset=[metric])
    if len(metric_df) == 0:
        print("No data available")
        return
    
    if metric == 'stockout_rate':
        # Lower is better for stockout rate
        top = metric_df.nsmallest(n, metric)[['dataset_id', 'normalized_mae', 'stockout_rate', 'mape']]
    else:
        # Lower is better for normalized_mae
        top = metric_df.nsmallest(n, metric)[['dataset_id', 'normalized_mae', 'stockout_rate', 'mape']]
    print(top.to_string(index=False))
    
    print(f"\n{'=' * 70}")
    print(f"TOP {n} WORST PERFORMING (by {metric.upper()})")
    print("=" * 70)
    
    if metric == 'stockout_rate':
        # Higher is worse for stockout rate
        worst = metric_df.nlargest(n, metric)[['dataset_id', 'normalized_mae', 'stockout_rate', 'mape']]
    else:
        # Higher is worse for normalized_mae
        worst = metric_df.nlargest(n, metric)[['dataset_id', 'normalized_mae', 'stockout_rate', 'mape']]
    print(worst.to_string(index=False))


def analyze_by_category(df: pd.DataFrame) -> None:
    """Analyze performance by dataset category (A, B, C, D, E)."""
    df['category'] = df['dataset_id'].str[0]
    
    print(f"\n{'=' * 70}")
    print("PERFORMANCE BY CATEGORY")
    print("=" * 70)
    
    agg_dict = {'category': 'count'}
    if 'normalized_mae' in df.columns:
        agg_dict['normalized_mae'] = ['mean', 'std']
    if 'stockout_rate' in df.columns:
        agg_dict['stockout_rate'] = ['mean', 'std']
    if 'mape' in df.columns:
        agg_dict['mape'] = ['mean', 'std']
    
    category_stats = df.groupby('category').agg(agg_dict).round(4)
    
    print(category_stats)


def export_summary_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Export summary to CSV."""
    df_sorted = df.sort_values('mae')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_sorted.to_csv(output_path, index=False)
    print(f"\n✓ Exported summary to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate and aggregate results from trained LightGBM models"
    )
    parser.add_argument(
        '--models_dir',
        type=Path,
        default=Path('ml/models'),
        help='Directory containing model outputs'
    )
    parser.add_argument(
        '--horizon',
        type=int,
        default=14,
        help='Forecast horizon (default: 14)'
    )
    parser.add_argument(
        '--objective',
        type=str,
        default='l2',
        choices=['l2', 'quantile', 'asymmetric'],
        help='Model objective (default: l2)'
    )
    parser.add_argument(
        '--output_csv',
        type=Path,
        help='Optional: Export summary to CSV'
    )
    parser.add_argument(
        '--dataset_id',
        type=str,
        help='Optional: Analyze a specific dataset in detail'
    )
    
    args = parser.parse_args()
    
    # Load all metrics
    print(f"Loading metrics from {args.models_dir}...")
    df = load_all_metrics(args.models_dir, args.horizon, args.objective)
    
    # Print summary
    print_summary_statistics(df)
    print_top_performers(df, metric='stockout_rate', n=5)
    analyze_by_category(df)
    
    # Export if requested
    if args.output_csv:
        export_summary_csv(df, args.output_csv)
    
    # Detailed analysis for specific dataset
    if args.dataset_id:
        print(f"\n{'=' * 70}")
        print(f"DETAILED ANALYSIS: {args.dataset_id}")
        print("=" * 70)
        
        try:
            pred_df = load_predictions(args.models_dir, args.dataset_id, args.horizon, args.objective)
            
            print(f"\nPredictions Summary:")
            print(f"  Total predictions: {len(pred_df)}")
            print(f"  Date range: {pred_df['date'].min()} to {pred_df['date'].max()}")
            
            # Calculate additional metrics
            mae = pred_df['abs_error'].mean()
            rmse = np.sqrt((pred_df['error'] ** 2).mean())
            
            print(f"\nRecalculated Metrics:")
            print(f"  MAE: {mae:.2f}")
            print(f"  RMSE: {rmse:.2f}")
            
            # Show sample predictions
            print(f"\nSample Predictions (first 10 rows):")
            print(pred_df[['date', 'actual', 'predicted', 'error', 'pct_error']].head(10).to_string(index=False))
            
        except Exception as e:
            print(f"Error loading predictions for {args.dataset_id}: {e}")


if __name__ == "__main__":
    main()
