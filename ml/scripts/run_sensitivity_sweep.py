#!/usr/bin/env python3
"""
Run sensitivity sweep across all scenarios and collect expired rates.
"""
import subprocess
import sys
import time
from pathlib import Path
import pandas as pd
import json

SCENARIOS = ['baseline', 'S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12']
BASE_DIR = Path('ml/data')

def run_scenario(scenario_name):
    """Generate datasets for a scenario."""
    output_dir = BASE_DIR / f"scenario_{scenario_name.lower()}"
    
    print(f"\n{'='*70}")
    print(f"Generating scenario: {scenario_name}")
    print(f"Output: {output_dir}")
    print(f"{'='*70}")
    
    cmd = [
        sys.executable,
        'ml/data_generation/generate_synthetic_bank.py',
        '--params', 'ml/config/realistic_params.yaml',
        '--scenario', scenario_name,
        '--output_dir', str(output_dir),
        '--quiet'
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"ERROR generating {scenario_name}:")
        print(result.stderr)
        return None
    
    print(f"✓ Completed in {elapsed:.1f}s")
    return output_dir

def analyze_scenario(data_dir):
    """Analyze expired rate for a scenario."""
    script_path = Path('ml/scripts/analyze_scenario_expired_rate.py')
    result = subprocess.run(
        [sys.executable, str(script_path), str(data_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error analyzing {data_dir}: {result.stderr}")
        return None
    
    # Parse output
    lines = result.stdout.strip().split('\n')
    expired_rate = float(lines[0].split(':')[1].strip().replace('%', ''))
    
    return {
        'expired_rate': expired_rate,
        'raw_output': result.stdout
    }

def main():
    results = []
    
    print(f"Running sensitivity sweep across {len(SCENARIOS)} scenarios...")
    
    for scenario in SCENARIOS:
        # Generate datasets
        data_dir = run_scenario(scenario)
        if data_dir is None:
            continue
        
        # Analyze
        analysis = analyze_scenario(data_dir)
        if analysis:
            results.append({
                'scenario': scenario,
                'expired_rate': analysis['expired_rate'],
                'data_dir': str(data_dir)
            })
            print(f"  Expired rate: {analysis['expired_rate']:.2f}%")
    
    # Save results
    results_df = pd.DataFrame(results)
    results_path = BASE_DIR / 'sensitivity_sweep_results.csv'
    results_df.to_csv(results_path, index=False)
    print(f"\n{'='*70}")
    print(f"Results saved to: {results_path}")
    print(f"{'='*70}")
    print(results_df.to_string(index=False))
    
    return results_df

if __name__ == "__main__":
    main()
