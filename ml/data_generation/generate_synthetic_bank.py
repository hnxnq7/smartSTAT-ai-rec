"""
Main script to generate the expanded synthetic dataset bank.

Generates 500 scenarios (100 per archetype A-E) with hospital size tiers
and creates train/test splits for ML evaluation.
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import zipfile
import json
from typing import Dict, List
from tqdm import tqdm
import random

from ml.data_generation.generator import generate_scenario


# Archetype definitions
ARCHETYPES = ["A", "B", "C", "D", "E"]
HOSPITAL_SIZES = ["small", "medium", "large"]
SCENARIOS_PER_ARCHETYPE = 100


def assign_hospital_sizes(n_scenarios: int, rng_seed: int = 42) -> List[str]:
    """
    Assign hospital sizes with roughly balanced distribution.
    Returns list of sizes in order (33/33/34 split).
    """
    sizes = []
    per_size = n_scenarios // 3
    remainder = n_scenarios % 3
    
    for size in HOSPITAL_SIZES:
        count = per_size
        if remainder > 0:
            count += 1
            remainder -= 1
        sizes.extend([size] * count)
    
    # Shuffle for randomness
    rng = random.Random(rng_seed)
    rng.shuffle(sizes)
    
    return sizes


def generate_all_scenarios(
    output_dir: Path,
    base_seed: int = 12345,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Generate all scenarios and save to disk.
    
    Returns:
        DataFrame with manifest information
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    train_dir = output_dir / "Training_Sets_2023-2024"
    test_dir = output_dir / "Testing_Sets_2025"
    train_dir.mkdir(exist_ok=True)
    test_dir.mkdir(exist_ok=True)
    
    manifest_rows = []
    scenario_counter = 0
    
    # Progress tracking
    total_scenarios = len(ARCHETYPES) * SCENARIOS_PER_ARCHETYPE
    pbar = tqdm(total=total_scenarios, desc="Generating scenarios") if verbose else None
    
    for archetype in ARCHETYPES:
        # Assign hospital sizes for this archetype
        sizes = assign_hospital_sizes(SCENARIOS_PER_ARCHETYPE, base_seed + ord(archetype))
        
        for scenario_num in range(1, SCENARIOS_PER_ARCHETYPE + 1):
            scenario_id = f"{archetype}{scenario_num:03d}"
            hospital_size = sizes[scenario_num - 1]
            
            # Create unique seed for this scenario
            scenario_seed = base_seed + scenario_counter * 1001 + hash(scenario_id) % 10000
            
            try:
                # Generate full time series (2023-2025)
                df_full, metadata = generate_scenario(
                    scenario_id=scenario_id,
                    archetype=archetype,
                    hospital_size=hospital_size,
                    seed=scenario_seed,
                    start_date="2023-01-01",
                    end_date="2025-12-31"
                )
                
                # Split into train (2023-2024) and test (2025)
                df_train = df_full[df_full['date'] < '2025-01-01'].copy()
                df_test = df_full[df_full['date'] >= '2025-01-01'].copy()
                
                # Save files
                train_filename = f"{scenario_id}_{hospital_size}_train_2023_2024.csv"
                test_filename = f"{scenario_id}_{hospital_size}_test_2025.csv"
                
                train_path = train_dir / train_filename
                test_path = test_dir / test_filename
                
                df_train.to_csv(train_path, index=False)
                df_test.to_csv(test_path, index=False)
                
                # Prepare manifest row
                manifest_row = {
                    'scenario_id': scenario_id,
                    'archetype': archetype,
                    'hospital_size': hospital_size,
                    'seed': scenario_seed,
                    'train_file': train_filename,
                    'test_file': test_filename,
                    'lead_time': metadata['lead_time'],
                    'avg_used_train': round(metadata['avg_used_train'], 4),
                    'avg_used_test': round(metadata['avg_used_test'], 4),
                    'pct_zero_train': round(metadata['pct_zero_train'], 2),
                    'pct_zero_test': round(metadata['pct_zero_test'], 2),
                    'max_used_train': metadata['max_used_train'],
                    'max_used_test': metadata['max_used_test'],
                }
                
                # Add archetype-specific generation parameters
                for key in metadata:
                    if key not in manifest_row and key not in [
                        'scenario_id', 'archetype', 'hospital_size', 'seed',
                        'lead_time', 'avg_used_train', 'avg_used_test',
                        'pct_zero_train', 'pct_zero_test', 'max_used_train', 'max_used_test'
                    ]:
                        manifest_row[key] = round(metadata[key], 4) if isinstance(metadata[key], float) else metadata[key]
                
                manifest_rows.append(manifest_row)
                scenario_counter += 1
                
                if pbar:
                    pbar.update(1)
            
            except Exception as e:
                print(f"\nError generating {scenario_id}: {e}")
                if pbar:
                    pbar.update(1)
                continue
    
    if pbar:
        pbar.close()
    
    # Create manifest DataFrame
    manifest_df = pd.DataFrame(manifest_rows)
    manifest_path = output_dir / "DATASET_MANIFEST.csv"
    manifest_df.to_csv(manifest_path, index=False)
    
    return manifest_df


def create_zip_archive(output_dir: Path, zip_path: Path) -> None:
    """Create a zip archive of the entire dataset directory."""
    print(f"\nCreating zip archive: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in output_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(output_dir.parent)
                zipf.write(file_path, arcname)
    
    print(f"✓ Archive created: {zip_path} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")


def print_summary(manifest_df: pd.DataFrame, output_dir: Path) -> None:
    """Print generation summary."""
    print("\n" + "=" * 70)
    print("GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total scenarios: {len(manifest_df)}")
    print(f"Output directory: {output_dir}")
    
    print("\nBy Archetype:")
    print(manifest_df['archetype'].value_counts().sort_index())
    
    print("\nBy Hospital Size:")
    print(manifest_df['hospital_size'].value_counts())
    
    print("\nBy Archetype and Size:")
    print(manifest_df.groupby(['archetype', 'hospital_size']).size().unstack(fill_value=0))
    
    # Count files
    train_dir = output_dir / "Training_Sets_2023-2024"
    test_dir = output_dir / "Testing_Sets_2025"
    train_files = len(list(train_dir.glob("*.csv"))) if train_dir.exists() else 0
    test_files = len(list(test_dir.glob("*.csv"))) if test_dir.exists() else 0
    
    print(f"\nFiles generated:")
    print(f"  Train files: {train_files}")
    print(f"  Test files: {test_files}")
    print(f"  Manifest: 1")
    print(f"  Total: {train_files + test_files + 1}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate expanded synthetic dataset bank for medication demand forecasting"
    )
    parser.add_argument(
        '--output_dir',
        type=Path,
        default=Path('ml/data/synthetic_bank'),
        help='Output directory for generated datasets (default: ml/data/synthetic_bank)'
    )
    parser.add_argument(
        '--base_seed',
        type=int,
        default=12345,
        help='Base random seed for reproducibility (default: 12345)'
    )
    parser.add_argument(
        '--zip',
        action='store_true',
        help='Create a zip archive of the generated datasets'
    )
    parser.add_argument(
        '--zip_path',
        type=Path,
        help='Path for zip archive (default: output_dir.parent/synthetic_bank.zip)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress bars'
    )
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.base_seed)
    np.random.seed(args.base_seed)
    
    print("=" * 70)
    print("SYNTHETIC DATASET GENERATION")
    print("=" * 70)
    print(f"Output directory: {args.output_dir}")
    print(f"Scenarios: {len(ARCHETYPES)} archetypes × {SCENARIOS_PER_ARCHETYPE} scenarios = {len(ARCHETYPES) * SCENARIOS_PER_ARCHETYPE} total")
    print(f"Period: 2023-2025 (Train: 2023-2024, Test: 2025)")
    print()
    
    # Generate all scenarios
    manifest_df = generate_all_scenarios(
        output_dir=args.output_dir,
        base_seed=args.base_seed,
        verbose=not args.quiet
    )
    
    # Print summary
    print_summary(manifest_df, args.output_dir)
    
    # Create zip if requested
    if args.zip:
        if args.zip_path:
            zip_path = args.zip_path
        else:
            zip_path = args.output_dir.parent / "synthetic_bank.zip"
        create_zip_archive(args.output_dir, zip_path)
    
    print("\n✓ Generation complete!")
    print(f"\nNext steps:")
    print(f"  1. Review manifest: {args.output_dir / 'DATASET_MANIFEST.csv'}")
    print(f"  2. Verify data quality and statistics")
    print(f"  3. Use datasets for ML training and evaluation")


if __name__ == "__main__":
    main()
