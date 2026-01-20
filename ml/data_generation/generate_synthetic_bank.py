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
from typing import Dict, List, Optional, Any
from tqdm import tqdm
import random

from ml.data_generation.generator import generate_scenario
from ml.data_generation.config_loader import (
    load_params_config, load_scenario_config, merge_configs, get_category_params
)


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
    archetypes: List[str] = None,
    verbose: bool = True,
    config_params: Optional[Dict[str, Any]] = None  # Optional config parameters per category
) -> pd.DataFrame:
    """
    Generate all scenarios and save to disk with organized structure.
    
    Organized structure:
    - output_dir/
      - A/
        - A001_train.csv
        - A001_test.csv
        - ...
      - B/
        - B001_train.csv
        - B001_test.csv
        - ...
    
    Args:
        output_dir: Root output directory
        base_seed: Base random seed
        archetypes: List of archetypes to generate (default: all ARCHETYPES)
        verbose: Show progress bars
    
    Returns:
        DataFrame with manifest information
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if archetypes is None:
        archetypes = ARCHETYPES
    
    manifest_rows = []
    scenario_counter = 0
    
    # Progress tracking
    total_scenarios = len(archetypes) * SCENARIOS_PER_ARCHETYPE
    pbar = tqdm(total=total_scenarios, desc="Generating scenarios") if verbose else None
    
    for archetype in archetypes:
        # Create archetype-specific directory
        archetype_dir = output_dir / archetype
        archetype_dir.mkdir(exist_ok=True)
        
        # Assign hospital sizes for this archetype
        sizes = assign_hospital_sizes(SCENARIOS_PER_ARCHETYPE, base_seed + ord(archetype))
        
        for scenario_num in range(1, SCENARIOS_PER_ARCHETYPE + 1):
            scenario_id = f"{archetype}{scenario_num:03d}"
            hospital_size = sizes[scenario_num - 1]
            
            # Create unique seed for this scenario
            scenario_seed = base_seed + scenario_counter * 1001 + hash(scenario_id) % 10000
            
            try:
                # Get category-specific config params if provided
                category_config = None
                if config_params and archetype in config_params:
                    category_config = config_params[archetype]
                
                # Generate full time series (2023-2025)
                df_full, metadata = generate_scenario(
                    scenario_id=scenario_id,
                    archetype=archetype,
                    hospital_size=hospital_size,
                    seed=scenario_seed,
                    start_date="2023-01-01",
                    end_date="2025-12-31",
                    config_params=category_config
                )
                
                # Split into train (2023-2024) and test (2025)
                df_train = df_full[df_full['date'] < '2025-01-01'].copy()
                df_test = df_full[df_full['date'] >= '2025-01-01'].copy()
                
                # Save files with simplified naming
                train_filename = f"{scenario_id}_train.csv"
                test_filename = f"{scenario_id}_test.csv"
                
                train_path = archetype_dir / train_filename
                test_path = archetype_dir / test_filename
                
                df_train.to_csv(train_path, index=False)
                df_test.to_csv(test_path, index=False)
                
                # Prepare manifest row
                manifest_row = {
                    'scenario_id': scenario_id,
                    'archetype': archetype,
                    'hospital_size': hospital_size,
                    'seed': scenario_seed,
                    'train_file': f"{archetype}/{train_filename}",
                    'test_file': f"{archetype}/{test_filename}",
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
    
    # Count files (organized by archetype)
    total_train = 0
    total_test = 0
    for archetype in ARCHETYPES:
        archetype_dir = output_dir / archetype
        if archetype_dir.exists():
            train_count = len(list(archetype_dir.glob("*_train.csv")))
            test_count = len(list(archetype_dir.glob("*_test.csv")))
            total_train += train_count
            total_test += test_count
    
    print(f"\nFiles generated:")
    print(f"  Train files: {total_train}")
    print(f"  Test files: {total_test}")
    print(f"  Manifest: 1")
    print(f"  Total: {total_train + total_test + 1}")


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
    parser.add_argument(
        '--archetypes',
        nargs='+',
        choices=ARCHETYPES,
        help='Specific archetypes to generate (default: all). Example: --archetypes D E'
    )
    parser.add_argument(
        '--params',
        type=str,
        help='Path to realistic_params.yaml config file (default: ml/config/realistic_params.yaml)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        help='Scenario name from sensitivity_scenarios.yaml (e.g., S1, S9). Overrides params.'
    )
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.base_seed)
    np.random.seed(args.base_seed)
    
    # Determine archetypes to generate
    archetypes_to_generate = args.archetypes if args.archetypes else ARCHETYPES
    
    # Load config if provided
    config_params_by_category = None
    if args.params or args.scenario:
        # Load base realistic params
        params_path = args.params or 'ml/config/realistic_params.yaml'
        base_config = load_params_config(params_path)
        
        # Load scenario override if provided
        scenario_config = None
        if args.scenario:
            scenario_path = 'ml/config/sensitivity_scenarios.yaml'
            scenario_config = load_scenario_config(scenario_path, args.scenario)
            print(f"\nUsing scenario: {args.scenario}")
            print(f"  Description: {scenario_config.get('description', 'N/A')}")
            if 'expected_result' in scenario_config:
                exp = scenario_config['expected_result']
                print(f"  Expected expired rate: {exp.get('expired_rate', 'N/A')}")
                print(f"  Expected stockout rate: {exp.get('stockout_rate', 'N/A')}")
        
        # Merge configs
        merged_config = merge_configs(base_config, scenario_config) if scenario_config else base_config
        
        # Extract category-specific parameters
        config_params_by_category = {}
        for archetype in archetypes_to_generate:
            config_params_by_category[archetype] = get_category_params(
                merged_config, archetype, hospital_size="medium"  # Default, will vary by scenario
            )
        
        print(f"\nConfig loaded from: {params_path}")
        if scenario_config:
            print(f"Scenario override: {args.scenario}")
    else:
        print("\nUsing default parameters (no config file specified)")
    
    print("=" * 70)
    print("SYNTHETIC DATASET GENERATION")
    print("=" * 70)
    print(f"Output directory: {args.output_dir}")
    print(f"Archetypes: {', '.join(archetypes_to_generate)}")
    print(f"Scenarios: {len(archetypes_to_generate)} archetypes × {SCENARIOS_PER_ARCHETYPE} scenarios = {len(archetypes_to_generate) * SCENARIOS_PER_ARCHETYPE} total")
    print(f"Period: 2023-2025 (Train: 2023-2024, Test: 2025)")
    print(f"Structure: Organized by archetype (A/, B/, C/, D/, E/)")
    print()
    
    # Generate all scenarios
    manifest_df = generate_all_scenarios(
        output_dir=args.output_dir,
        base_seed=args.base_seed,
        archetypes=archetypes_to_generate,
        verbose=not args.quiet,
        config_params=config_params_by_category
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
