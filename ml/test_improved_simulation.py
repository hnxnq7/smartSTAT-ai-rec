#!/usr/bin/env python3
"""
Test script to compare old vs improved inventory simulation logic.
Re-evaluates a few datasets with the improved simulation and compares stockout rates.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.datasets import load_dataset_files, get_dataset_info
from ml.train_lgbm import prepare_features_and_labels
from ml.evaluate import compute_inventory_metrics_simple, compute_metrics
import lightgbm as lgb


def load_model_and_predict(model_dir: Path, dataset_id: str, horizon: int, objective: str):
    """Load a trained model and get predictions."""
    model_file = model_dir / dataset_id / f"model_h{horizon}_{objective}.txt"
    if not model_file.exists():
        return None, None
    
    model = lgb.Booster(model_file=str(model_file))
    
    # Load metrics to get feature list
    metrics_file = model_dir / dataset_id / f"metrics_h{horizon}_{objective}.json"
    if metrics_file.exists():
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)
        features = metrics_data.get('features', [])
    else:
        return None, None
    
    return model, features


def test_improved_simulation(
    data_dir: Path,
    model_dir: Path,
    dataset_ids: list,
    horizon: int = 14,
    objective: str = "asymmetric",
):
    """Test improved simulation on selected datasets."""
    
    print("="*70)
    print("Testing Improved Inventory Simulation")
    print("="*70)
    print(f"\nTesting {len(dataset_ids)} datasets:")
    print(f"  Horizon: {horizon}")
    print(f"  Objective: {objective}")
    print(f"  Datasets: {', '.join(dataset_ids)}")
    print()
    
    results = []
    
    for dataset_id in dataset_ids:
        print(f"\n{'='*70}")
        print(f"Testing {dataset_id}")
        print(f"{'='*70}")
        
        try:
            # Load dataset
            train_df, test_df = load_dataset_files(data_dir, dataset_id)
            
            # Load model and features
            model, feature_list = load_model_and_predict(model_dir, dataset_id, horizon, objective)
            if model is None:
                print(f"  ⚠️  Model not found, skipping {dataset_id}")
                continue
            
            # Prepare features and labels using the same logic as training
            X_train, y_train, X_test, y_test = prepare_features_and_labels(
                train_df,
                test_df,
                horizon,
                exclude_contemporaneous_used=False,
            )
            
            # Get predictions
            y_pred = model.predict(X_test, num_iteration=model.best_iteration)
            
            # Get daily predictions for simulation
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
            
            # Get dates
            test_dates = test_df["date"].iloc[:len(y_test)]
            
            # Get expired units data if available
            expired_units_data = test_df["expired_units"].iloc[:len(y_test)] if 'expired_units' in test_df.columns else None
            non_expired_data = test_df["non_expired_inventory"].iloc[:len(y_test)] if 'non_expired_inventory' in test_df.columns else None
            
            # Run improved simulation
            inventory_metrics = compute_inventory_metrics_simple(
                test_dates,
                daily_actual,
                daily_predicted,
                initial_stock,
                lead_time=lead_time,
                expired_units_actual=expired_units_data,
                non_expired_inventory_actual=non_expired_data,
            )
            
            # Compute prediction metrics
            pred_metrics = compute_metrics(y_test, pd.Series(y_pred), normalize_by_mean=True)
            
            # Load saved metrics for comparison
            metrics_file = model_dir / dataset_id / f"metrics_h{horizon}_{objective}.json"
            old_stockout_rate = None
            old_normalized_mae = None
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    old_metrics_data = json.load(f)
                    old_metrics = old_metrics_data.get('metrics', {})
                    old_stockout_rate = old_metrics.get('stockout_rate')
                    old_normalized_mae = old_metrics.get('normalized_mae')
            
            result = {
                'dataset_id': dataset_id,
                'old_stockout_rate': old_stockout_rate,
                'new_stockout_rate': inventory_metrics['stockout_rate'],
                'old_normalized_mae': old_normalized_mae,
                'new_normalized_mae': pred_metrics['normalized_mae'],
                'stockout_improvement': (old_stockout_rate - inventory_metrics['stockout_rate']) if old_stockout_rate is not None else None,
                'stockout_days': inventory_metrics['stockout_days'],
                'total_days': inventory_metrics['total_days'],
            }
            results.append(result)
            
            print(f"  Stockout Rate:")
            if old_stockout_rate is not None:
                improvement = old_stockout_rate - inventory_metrics['stockout_rate']
                improvement_pct = (improvement / old_stockout_rate * 100) if old_stockout_rate > 0 else 0
                print(f"    Old: {old_stockout_rate:.2f}%")
                print(f"    New: {inventory_metrics['stockout_rate']:.2f}%")
                print(f"    Change: {improvement:+.2f}% ({improvement_pct:+.1f}%)")
            else:
                print(f"    New: {inventory_metrics['stockout_rate']:.2f}%")
            print(f"  Stockout Days: {inventory_metrics['stockout_days']} / {inventory_metrics['total_days']}")
            print(f"  Normalized MAE: {pred_metrics['normalized_mae']:.4f}")
            
        except Exception as e:
            print(f"  ✗ Error processing {dataset_id}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    results_df = pd.DataFrame(results)
    
    if len(results_df) > 0:
        print(f"\nTested {len(results_df)} datasets")
        
        if 'stockout_improvement' in results_df.columns:
            improvements = results_df['stockout_improvement'].dropna()
            if len(improvements) > 0:
                print(f"\nStockout Rate Changes:")
                print(f"  Average improvement: {improvements.mean():.2f}%")
                print(f"  Median improvement: {improvements.median():.2f}%")
                print(f"  Best improvement: {improvements.max():.2f}%")
                print(f"  Worst change: {improvements.min():.2f}%")
                print(f"  Datasets improved: {(improvements > 0).sum()} / {len(improvements)}")
        
        print(f"\nNew Stockout Rates:")
        print(f"  Average: {results_df['new_stockout_rate'].mean():.2f}%")
        print(f"  Median: {results_df['new_stockout_rate'].median():.2f}%")
        print(f"  Min: {results_df['new_stockout_rate'].min():.2f}%")
        print(f"  Max: {results_df['new_stockout_rate'].max():.2f}%")
    
    return results_df


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test improved inventory simulation")
    parser.add_argument(
        "--data_dir",
        type=Path,
        default=Path("ml/data/synthetic_bank_organized"),
        help="Data directory",
    )
    parser.add_argument(
        "--model_dir",
        type=Path,
        default=Path("ml/models_all_500"),
        help="Model directory",
    )
    parser.add_argument(
        "--dataset_ids",
        type=str,
        nargs="+",
        default=["A001", "A002", "B001", "B002", "C001", "C002", "D001", "D002", "E001", "E002"],
        help="Dataset IDs to test",
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
    
    args = parser.parse_args()
    
    results_df = test_improved_simulation(
        args.data_dir,
        args.model_dir,
        args.dataset_ids,
        args.horizon,
        args.objective,
    )
    
    # Save results
    if results_df is not None and len(results_df) > 0:
        output_file = Path("ml/results/simulation_comparison.csv")
        results_df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
