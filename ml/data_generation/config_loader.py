"""
Configuration loader for realistic parameter sets.
Supports loading from YAML files and scenario overrides.
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, Any


def load_params_config(config_path: str) -> Dict[str, Any]:
    """Load realistic parameters from YAML config file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def load_scenario_config(scenario_path: str, scenario_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load scenario-specific parameters from YAML config.
    
    Args:
        scenario_path: Path to sensitivity_scenarios.yaml
        scenario_name: Scenario name (e.g., "S1", "baseline"). If None, returns all scenarios.
    
    Returns:
        Dictionary with scenario parameters
    """
    config_file = Path(scenario_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Scenario file not found: {scenario_path}")
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    if scenario_name is None:
        return config.get('scenarios', {})
    
    scenarios = config.get('scenarios', {})
    if scenario_name not in scenarios:
        raise ValueError(f"Scenario '{scenario_name}' not found. Available: {list(scenarios.keys())}")
    
    return scenarios[scenario_name]


def merge_configs(base_config: Dict[str, Any], scenario_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Merge base realistic_params config with scenario overrides.
    
    Scenario config overrides base config values.
    """
    merged = base_config.copy()
    
    if scenario_config is None:
        return merged
    
    # Deep merge for nested dictionaries
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(merged, scenario_config)


def get_category_params(
    config: Dict[str, Any],
    category: str,
    hospital_size: str = "medium"
) -> Dict[str, Any]:
    """
    Extract category-specific parameters from config.
    
    Returns:
        Dictionary with: shelf_life_days, lead_time_days, order_cadence_days,
                         service_level_target, moq_units, spq_units
    """
    params = {}
    
    # Shelf life
    shelf_life = config.get('shelf_life_days', {})
    if isinstance(shelf_life, dict) and category in shelf_life:
        params['shelf_life_days'] = shelf_life[category]
    elif isinstance(shelf_life, dict) and 'by_size' in shelf_life:
        params['shelf_life_days'] = shelf_life['by_size'].get(hospital_size, 730)
    else:
        params['shelf_life_days'] = shelf_life if isinstance(shelf_life, (int, float)) else 730
    
    # Lead time
    lead_time = config.get('lead_time_days', {})
    if isinstance(lead_time, dict) and category in lead_time:
        params['lead_time_days'] = lead_time[category]
    elif isinstance(lead_time, dict) and 'by_size' in lead_time:
        params['lead_time_days'] = lead_time['by_size'].get(hospital_size, 5)
    else:
        params['lead_time_days'] = lead_time if isinstance(lead_time, (int, float)) else 5
    
    # Order cadence
    order_cadence = config.get('order_cadence_days', {})
    if isinstance(order_cadence, dict) and category in order_cadence:
        params['order_cadence_days'] = order_cadence[category]
    else:
        params['order_cadence_days'] = order_cadence if isinstance(order_cadence, (int, float)) else 7
    
    # Service level target
    service_level = config.get('service_level_target', {})
    if isinstance(service_level, dict):
        if 'by_category' in service_level and category in service_level['by_category']:
            params['service_level_target'] = service_level['by_category'][category]
        elif category == 'E':
            params['service_level_target'] = service_level.get('critical', 0.995)
        else:
            params['service_level_target'] = service_level.get('routine', 0.98)
    else:
        params['service_level_target'] = service_level if service_level else 0.98
    
    # MOQ
    moq = config.get('moq_units', {})
    if isinstance(moq, dict) and 'by_category' in moq and category in moq['by_category']:
        params['moq_units'] = moq['by_category'][category]
    elif isinstance(moq, dict):
        params['moq_units'] = moq.get('small_consumables', 200)
    else:
        params['moq_units'] = moq if isinstance(moq, (int, float)) else 200
    
    # SPQ
    spq = config.get('spq_units', {})
    if isinstance(spq, dict) and 'by_category' in spq and category in spq['by_category']:
        params['spq_units'] = spq['by_category'][category]
    elif isinstance(spq, dict):
        params['spq_units'] = spq.get('default', 25)
    else:
        params['spq_units'] = spq if isinstance(spq, (int, float)) else 25
    
    # Code Cart Parameters (Option C)
    # Ordering mode
    params['ordering_mode'] = config.get('ordering_mode', None)
    params['policy_auto_select'] = config.get('policy_auto_select', False)  # Enable auto policy selection
    
    # Par level (for par-driven ordering)
    par_level = config.get('par_level', {})
    if isinstance(par_level, dict):
        params['par_level_days'] = par_level.get('days_coverage', None)
    else:
        params['par_level_days'] = par_level if isinstance(par_level, (int, float)) else None
    
    # Forecast-driven par cap (optional)
    params['par_cap_enabled'] = config.get('par_cap_enabled', False)
    
    # Shelf life mode (effective vs labeled)
    shelf_life_config = config.get('shelf_life', {})
    if isinstance(shelf_life_config, dict):
        params['shelf_life_mode'] = shelf_life_config.get('mode', None)
        params['pull_buffer_days'] = shelf_life_config.get('pull_buffer_days', None)
    else:
        params['shelf_life_mode'] = None
        params['pull_buffer_days'] = None
    
    # Lead time distribution (stochastic)
    lead_time_config = config.get('lead_time', {})
    if isinstance(lead_time_config, dict):
        params['lead_time_distribution'] = lead_time_config.get('distribution', None)
        params['lead_time_median'] = lead_time_config.get('median_days', None)
        params['lead_time_p95'] = lead_time_config.get('p95_days', None)
    else:
        params['lead_time_distribution'] = None
        params['lead_time_median'] = None
        params['lead_time_p95'] = None
    
    return params
