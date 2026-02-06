#!/usr/bin/env python3
"""
Analyze waste (expired units) metrics across all datasets.

Provides comprehensive waste analysis including:
- Expired units total and rate
- Waste efficiency (units expired per unit used)
- Trade-off analysis between stockout rate and expired rate
- Category-specific waste patterns
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse


def analyze_waste(results_csv: Path):
    """Analyze waste metrics from results CSV."""
    
    df = pd.read_csv(results_csv)
    df['category'] = df['dataset_id'].str[0]
    
    # Calculate additional waste metrics
    # expired_rate = expired / (expired + used) * 100
    # We can derive: waste_efficiency = expired / used (ratio)
    # If expired_rate = 97%, then expired/(expired+used) = 0.97
    # Solving: expired = 0.97*(expired+used) => expired = 0.97*expired + 0.97*used
    # => 0.03*expired = 0.97*used => expired/used = 0.97/0.03 ≈ 32.3
    
    # For each dataset, we need to estimate used units from expired_rate and expired_units_total
    # expired_rate = expired / (expired + used) => used = expired * (1 - expired_rate/100) / (expired_rate/100)
    
    expired_rate_pct = df['expired_rate'] / 100
    # Avoid division by zero: if expired_rate is 100%, set to 99.99%
    expired_rate_pct = expired_rate_pct.clip(upper=0.9999)
    df['estimated_used_units'] = df['expired_units_total'] * (1 - expired_rate_pct) / expired_rate_pct
    df['waste_efficiency'] = np.where(
        df['estimated_used_units'] > 0,
        df['expired_units_total'] / df['estimated_used_units'],  # expired per unit used
        np.nan
    )
    # Estimate days from stockout_days and stockout_rate if total_days not available
    if 'total_days' in df.columns:
        df['waste_per_day'] = df['expired_units_total'] / df['total_days']
    else:
        # Estimate: stockout_rate = stockout_days / total_days * 100
        # => total_days = stockout_days / (stockout_rate / 100)
        df['estimated_total_days'] = df['stockout_days'] / (df['stockout_rate'] / 100)
        df['waste_per_day'] = df['expired_units_total'] / df['estimated_total_days']
    
    print("=" * 80)
    print("WASTE ANALYSIS - Expired Units & Efficiency")
    print("=" * 80)
    
    print(f"\n{'='*80}")
    print("OVERALL WASTE STATISTICS")
    print(f"{'='*80}")
    
    print(f"\nExpired Units Total:")
    print(f"  Total across all datasets: {df['expired_units_total'].sum():,.0f} units")
    print(f"  Mean per dataset: {df['expired_units_total'].mean():,.0f} units")
    print(f"  Median per dataset: {df['expired_units_total'].median():,.0f} units")
    print(f"  Min: {df['expired_units_total'].min():,.0f} units")
    print(f"  Max: {df['expired_units_total'].max():,.0f} units")
    
    print(f"\nExpired Rate (Expired / (Expired + Used)):")
    print(f"  Mean: {df['expired_rate'].mean():.2f}%")
    print(f"  Median: {df['expired_rate'].median():.2f}%")
    print(f"  Min: {df['expired_rate'].min():.2f}%")
    print(f"  Max: {df['expired_rate'].max():.2f}%")
    print(f"  Std: {df['expired_rate'].std():.2f}%")
    
    print(f"\nWaste Efficiency (Expired Units per Used Unit):")
    print(f"  Mean: {df['waste_efficiency'].mean():.2f}x (for every 1 unit used, {df['waste_efficiency'].mean():.2f} units expire)")
    print(f"  Median: {df['waste_efficiency'].median():.2f}x")
    print(f"  Min: {df['waste_efficiency'].min():.2f}x")
    print(f"  Max: {df['waste_efficiency'].max():.2f}x")
    
    print(f"\nWaste per Day:")
    print(f"  Mean: {df['waste_per_day'].mean():,.0f} units/day")
    print(f"  Median: {df['waste_per_day'].median():,.0f} units/day")
    
    print(f"\n{'='*80}")
    print("WASTE BY CATEGORY")
    print(f"{'='*80}")
    
    category_stats = df.groupby('category').agg({
        'expired_units_total': ['sum', 'mean', 'median'],
        'expired_rate': ['mean', 'median'],
        'waste_efficiency': ['mean', 'median'],
        'waste_per_day': ['mean', 'median'],
        'stockout_rate': ['mean', 'median'],
        'dataset_id': 'count'
    }).round(2)
    
    category_stats.columns = ['_'.join(col).strip() for col in category_stats.columns]
    print(category_stats.to_string())
    
    print(f"\n{'='*80}")
    print("TRADE-OFF: STOCKOUT RATE vs EXPIRED RATE")
    print(f"{'='*80}")
    
    # Analyze correlation between stockout rate and expired rate
    correlation = df['stockout_rate'].corr(df['expired_rate'])
    print(f"Correlation (Stockout Rate vs Expired Rate): {correlation:.3f}")
    print(f"(Negative = lower stockouts → higher waste, Positive = lower stockouts → lower waste)")
    
    # Find datasets with best balance
    # Normalize both metrics to 0-1 scale for comparison
    df['stockout_normalized'] = (df['stockout_rate'] - df['stockout_rate'].min()) / (df['stockout_rate'].max() - df['stockout_rate'].min())
    df['waste_normalized'] = (df['waste_efficiency'] - df['waste_efficiency'].min()) / (df['waste_efficiency'].max() - df['waste_efficiency'].min())
    df['combined_score'] = df['stockout_normalized'] + df['waste_normalized']  # Lower is better
    
    print(f"\nTop 10 Best Balance (Low Stockout + Low Waste):")
    best_balance = df.nsmallest(10, 'combined_score')[
        ['dataset_id', 'stockout_rate', 'expired_rate', 'waste_efficiency', 'expired_units_total']
    ]
    print(best_balance.to_string(index=False))
    
    print(f"\nTop 10 Worst Balance (High Stockout + High Waste):")
    worst_balance = df.nlargest(10, 'combined_score')[
        ['dataset_id', 'stockout_rate', 'expired_rate', 'waste_efficiency', 'expired_units_total']
    ]
    print(worst_balance.to_string(index=False))
    
    print(f"\n{'='*80}")
    print("TARGET ANALYSIS: Low Stockout (< 1%) with Acceptable Waste")
    print(f"{'='*80}")
    
    low_stockout = df[df['stockout_rate'] < 1.0]
    print(f"Datasets with stockout rate < 1.0%: {len(low_stockout)} ({len(low_stockout)/len(df)*100:.1f}%)")
    if len(low_stockout) > 0:
        print(f"  Mean expired rate: {low_stockout['expired_rate'].mean():.2f}%")
        print(f"  Mean waste efficiency: {low_stockout['waste_efficiency'].mean():.2f}x")
        print(f"  Mean expired units: {low_stockout['expired_units_total'].mean():,.0f} units")
    
    very_low_stockout = df[df['stockout_rate'] < 0.5]
    print(f"\nDatasets with stockout rate < 0.5%: {len(very_low_stockout)} ({len(very_low_stockout)/len(df)*100:.1f}%)")
    if len(very_low_stockout) > 0:
        print(f"  Mean expired rate: {very_low_stockout['expired_rate'].mean():.2f}%")
        print(f"  Mean waste efficiency: {very_low_stockout['waste_efficiency'].mean():.2f}x")
    
    print(f"\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}")
    
    print(f"""
Current State:
- Mean stockout rate: {df['stockout_rate'].mean():.2f}%
- Mean expired rate: {df['expired_rate'].mean():.2f}%
- Mean waste efficiency: {df['waste_efficiency'].mean():.2f}x

Key Observations:
1. Expired rate ~97% indicates most units expire rather than being used
   (This may reflect synthetic data characteristics, not necessarily real waste)

2. Low stockout rates (1.17% mean) achieved with current strategy

3. Trade-off exists: Reducing stockouts further will likely increase expired units
   Current strategy balances both objectives

4. Category D has lowest stockout rate (0.85%) but similar expired rate

To Further Reduce Waste:
- Tune safety stock levels (reduce if stockouts are rare)
- Optimize order quantities (reduce over-ordering)
- Implement FIFO (First-In-First-Out) inventory rotation
- Category-specific safety stock parameters
- Dynamic safety stock adjustment based on demand patterns
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze waste metrics from evaluation results")
    parser.add_argument(
        "--results_csv",
        type=Path,
        default=Path("ml/results/results_improved_simulation.csv"),
        help="Path to results CSV file"
    )
    
    args = parser.parse_args()
    analyze_waste(args.results_csv)
