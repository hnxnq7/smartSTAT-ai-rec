"""
Dataset discovery and loading utilities.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


def find_dataset_files(data_dir: Path, dataset_id: str) -> Tuple[Path, Path]:
    """
    Find train and test CSV files for a given dataset ID.
    
    Args:
        data_dir: Root directory containing Training_Sets and Testing_Sets folders
        dataset_id: Dataset ID (e.g., "A1", "E10")
    
    Returns:
        Tuple of (train_file_path, test_file_path)
    
    Raises:
        FileNotFoundError: If files cannot be found
    """
    train_dir = data_dir / "Training_Sets_2023-2024"
    test_dir = data_dir / "Testing_Sets_2025"
    
    # Find train file
    train_pattern = f"{dataset_id}_*_train_2023_2024.csv"
    train_files = list(train_dir.glob(train_pattern))
    if not train_files:
        raise FileNotFoundError(f"Train file not found for dataset {dataset_id} in {train_dir}")
    if len(train_files) > 1:
        raise ValueError(f"Multiple train files found for dataset {dataset_id}: {train_files}")
    train_file = train_files[0]
    
    # Find test file
    test_pattern = f"{dataset_id}_*_test_2025.csv"
    test_files = list(test_dir.glob(test_pattern))
    if not test_files:
        raise FileNotFoundError(f"Test file not found for dataset {dataset_id} in {test_dir}")
    if len(test_files) > 1:
        raise ValueError(f"Multiple test files found for dataset {dataset_id}: {test_files}")
    test_file = test_files[0]
    
    return train_file, test_file


def load_dataset_manifest(data_dir: Path) -> pd.DataFrame:
    """
    Load the DATASET_MANIFEST.csv file.
    
    Args:
        data_dir: Root directory containing DATASET_MANIFEST.csv
    
    Returns:
        DataFrame with manifest information
    """
    manifest_path = data_dir / "DATASET_MANIFEST.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    return pd.read_csv(manifest_path)


def get_all_dataset_ids(data_dir: Path) -> List[str]:
    """
    Get all dataset IDs from the manifest.
    
    Args:
        data_dir: Root directory containing DATASET_MANIFEST.csv
    
    Returns:
        List of dataset IDs (e.g., ["A1", "A2", ..., "E10"] or ["A001", "A002", ...])
    """
    manifest = load_dataset_manifest(data_dir)
    # Support both "dataset_id" (old) and "scenario_id" (new) column names
    id_column = "scenario_id" if "scenario_id" in manifest.columns else "dataset_id"
    return sorted(manifest[id_column].unique().tolist())


def load_dataset_files(data_dir: Path, dataset_id: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load train and test CSV files for a dataset.
    
    Args:
        data_dir: Root directory containing Training_Sets and Testing_Sets folders
        dataset_id: Dataset ID (e.g., "A1", "E10")
    
    Returns:
        Tuple of (train_df, test_df)
    """
    train_file, test_file = find_dataset_files(data_dir, dataset_id)
    
    # Load CSVs with date parsing
    train_df = pd.read_csv(train_file, parse_dates=["date"])
    test_df = pd.read_csv(test_file, parse_dates=["date"])
    
    # Sort by date to ensure chronological order
    train_df = train_df.sort_values("date").reset_index(drop=True)
    test_df = test_df.sort_values("date").reset_index(drop=True)
    
    return train_df, test_df


def get_dataset_info(data_dir: Path, dataset_id: str) -> Dict:
    """
    Get metadata about a dataset from the manifest.
    
    Args:
        data_dir: Root directory containing DATASET_MANIFEST.csv
        dataset_id: Dataset ID (or scenario_id in new format)
    
    Returns:
        Dictionary with dataset metadata
    """
    manifest = load_dataset_manifest(data_dir)
    # Support both "dataset_id" (old) and "scenario_id" (new) column names
    id_column = "scenario_id" if "scenario_id" in manifest.columns else "dataset_id"
    info = manifest[manifest[id_column] == dataset_id].iloc[0].to_dict()
    return info

