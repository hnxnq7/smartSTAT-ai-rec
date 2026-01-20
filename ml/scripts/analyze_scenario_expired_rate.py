#!/usr/bin/env python3
"""Calculate expired rate from a dataset directory (all train files)."""
import pandas as pd
from pathlib import Path
import sys

def analyze_dataset_expired_rate(data_dir):
    """Calculate expired rate from all datasets in a directory."""
    data_path = Path(data_dir)
    
    total_expired = 0
    total_used = 0
    total_datasets = 0
    by_category = {}
    
    for archetype in ['A', 'B', 'C', 'D', 'E']:
        archetype_dir = data_path / archetype
        if not archetype_dir.exists():
            continue
        
        category_expired = 0
        category_used = 0
        category_count = 0
        
        for csv_file in archetype_dir.glob("*_train.csv"):
            try:
                df = pd.read_csv(csv_file)
                expired = df['expired_units'].sum()
                used = df['used_units'].sum()
                total_expired += expired
                total_used += used
                total_datasets += 1
                category_expired += expired
                category_used += used
                category_count += 1
            except Exception as e:
                print(f"Error reading {csv_file}: {e}", file=sys.stderr)
        
        if category_expired + category_used > 0:
            by_category[archetype] = {
                'expired_rate': (category_expired / (category_expired + category_used)) * 100,
                'expired': category_expired,
                'used': category_used,
                'count': category_count
            }
    
    result = {
        'total_expired_rate': (total_expired / (total_expired + total_used)) * 100 if (total_expired + total_used) > 0 else 0,
        'total_expired': total_expired,
        'total_used': total_used,
        'datasets': total_datasets,
        'by_category': by_category
    }
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_scenario_expired_rate.py <data_dir>")
        sys.exit(1)
    
    result = analyze_dataset_expired_rate(sys.argv[1])
    print(f"Expired Rate: {result['total_expired_rate']:.2f}%")
    print(f"Total Expired: {result['total_expired']:,.0f}")
    print(f"Total Used: {result['total_used']:,.0f}")
    print(f"Datasets: {result['datasets']}")
    print("\nBy Category:")
    for cat in ['A', 'B', 'C', 'D', 'E']:
        if cat in result['by_category']:
            r = result['by_category'][cat]
            print(f"  {cat}: {r['expired_rate']:.2f}% (expired: {r['expired']:,.0f}, used: {r['used']:,.0f}, n={r['count']})")
