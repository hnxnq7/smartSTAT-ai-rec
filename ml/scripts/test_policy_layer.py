"""
Test policy layer on general inventory scenarios (S3, S6, S8).
Compare: forecast-driven baseline vs policy-selected vs par-driven-all
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.data_generation.generator import generate_scenario, SeededRandom
from ml.data_generation.config_loader import load_params_config, load_scenario_config, merge_configs, get_category_params
from ml.data_generation.policy_selector import get_policy_metadata


def test_scenario_policy_comparison(
    scenario_name: str,
    n_samples: int = 10,
    archetypes: list = None
):
    """Test a scenario with different policy modes."""
    base_config = load_params_config("ml/config/realistic_params.yaml")
    scenario_config = load_scenario_config("ml/config/sensitivity_scenarios.yaml", scenario_name)
    merged_config = merge_configs(base_config, scenario_config)
    
    results = {
        'forecast_driven': {'expired': [], 'stockout': []},
        'forecast_capped': {'expired': [], 'stockout': []},
        'policy_selected': {'expired': [], 'stockout': []},
        'par_driven_all': {'expired': [], 'stockout': []}
    }
    
    archetypes = archetypes or ['A', 'B', 'C']  # Default for speed
    policy_selection_counts = {'par_driven': 0, 'forecast_driven': 0, 'forecast_capped': 0}
    
    for archetype in archetypes:
        category_params = get_category_params(merged_config, archetype)
        
        for seed_offset in range(n_samples):
            seed = 12345 + seed_offset * 1001
            rng = SeededRandom(seed)
            
            dates = pd.date_range("2023-01-01", "2025-12-31", freq='D')
            
            # Generate demand
            if archetype == 'A':
                from ml.data_generation.generator import generate_demand_archetype_a
                used_units = generate_demand_archetype_a(dates, rng, "medium", 0.15, 0.5)
            elif archetype == 'B':
                from ml.data_generation.generator import generate_demand_archetype_b
                used_units = generate_demand_archetype_b(dates, rng, "medium", 0.5)
            elif archetype == 'C':
                from ml.data_generation.generator import generate_demand_archetype_c
                used_units = generate_demand_archetype_c(dates, rng, "medium", 1.5, 0.7)
            else:
                continue
            
            # Common config
            common_kwargs = dict(
                lead_time=category_params.get('lead_time_days', 5),
                archetype=archetype,
                shelf_life_days=category_params.get('shelf_life_days', 730),
                order_cadence_days=category_params.get('order_cadence_days', 7),
                service_level_target=category_params.get('service_level_target', 0.98),
                moq_units=category_params.get('moq_units', None),
                spq_units=category_params.get('spq_units', None),
                shelf_life_mode=category_params.get('shelf_life_mode', None),
                pull_buffer_days=category_params.get('pull_buffer_days', None),
                lead_time_distribution=category_params.get('lead_time_distribution', None),
                lead_time_median=category_params.get('lead_time_median', None),
                lead_time_p95=category_params.get('lead_time_p95', None),
            )
            
            # Test 1: Forecast-driven (baseline)
            from ml.data_generation.generator import simulate_inventory
            _, expired1, _, _, non_expired1 = simulate_inventory(
                dates, used_units, rng, "medium",
                **common_kwargs,
                ordering_mode="forecast_driven",
            )
            
            # Test 2: Forecast-driven with par caps
            _, expired_cap, _, _, non_expired_cap = simulate_inventory(
                dates, used_units, rng, "medium",
                **common_kwargs,
                ordering_mode="forecast_capped",
                par_cap_enabled=True,
            )
            
            # Test 3: Policy-selected (auto)
            _, expired2, _, _, non_expired2 = simulate_inventory(
                dates, used_units, rng, "medium",
                **common_kwargs,
                ordering_mode="auto",
                policy_auto_select=True,
                par_cap_enabled=True,
            )
            
            # Policy selection mix (auto only)
            avg_daily_usage = float(np.mean(used_units)) if len(used_units) > 0 else 0.0
            policy_meta = get_policy_metadata(
                avg_daily_usage=avg_daily_usage,
                used_units_array=used_units,
                shelf_life_days=category_params.get('shelf_life_days', 730),
                moq_units=category_params.get('moq_units', None),
                criticality="critical" if archetype == "E" else "routine",
                exchange_cadence_days=category_params.get('order_cadence_days', 7),
                par_cap_enabled=True,
            )
            if policy_meta["policy"] not in policy_selection_counts:
                policy_selection_counts[policy_meta["policy"]] = 0
            policy_selection_counts[policy_meta["policy"]] += 1
            
            # Test 4: Par-driven all
            _, expired3, _, _, non_expired3 = simulate_inventory(
                dates, used_units, rng, "medium",
                **common_kwargs,
                ordering_mode="par_driven",
                par_level_days=category_params.get('par_level_days', 30)
            )
            
            # Calculate metrics (use test period: 2025)
            test_mask = dates >= pd.Timestamp('2025-01-01')
            used_test = used_units[test_mask]
            expired_test1 = expired1[test_mask]
            expired_test2 = expired2[test_mask]
            expired_test3 = expired3[test_mask]
            non_expired_test1 = non_expired1[test_mask]
            non_expired_test2 = non_expired2[test_mask]
            non_expired_test3 = non_expired3[test_mask]
            
            for i, (expired_test, non_expired_test) in enumerate([
                (expired_test1, non_expired_test1),
                (expired_cap, non_expired_cap),
                (expired_test2, non_expired_test2),
                (expired_test3, non_expired_test3)
            ]):
                mode = ['forecast_driven', 'forecast_capped', 'policy_selected', 'par_driven_all'][i]
                total_expired = expired_test.sum()
                total_used = used_test.sum()
                expired_rate = (total_expired / (total_expired + total_used) * 100) if (total_expired + total_used) > 0 else 0
                stockout_days = (non_expired_test <= 0).sum()
                stockout_rate = (stockout_days / len(non_expired_test) * 100) if len(non_expired_test) > 0 else 0
                
                results[mode]['expired'].append(expired_rate)
                results[mode]['stockout'].append(stockout_rate)
    
    # Summary
    print(f"\n{scenario_name} Policy Comparison (n={n_samples * len(archetypes)}):")
    print("-" * 70)
    for mode in ['forecast_driven', 'forecast_capped', 'policy_selected', 'par_driven_all']:
        expired_mean = np.mean(results[mode]['expired'])
        expired_std = np.std(results[mode]['expired'])
        stockout_mean = np.mean(results[mode]['stockout'])
        stockout_max = np.max(results[mode]['stockout'])
        print(f"{mode:20s}: expired={expired_mean:.2f}%±{expired_std:.2f}%, "
              f"stockout={stockout_mean:.2f}% (max={stockout_max:.2f}%)")
    
    print("\nPolicy selection mix (auto):")
    total_selected = sum(policy_selection_counts.values())
    if total_selected > 0:
        for policy, count in policy_selection_counts.items():
            pct = count / total_selected * 100
            print(f"  {policy}: {count} ({pct:.1f}%)")
    else:
        print("  No selections recorded")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Test policy layer scenarios.")
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["S3", "S6", "S8"],
        help="Scenario names from sensitivity_scenarios.yaml"
    )
    parser.add_argument(
        "--n_samples",
        type=int,
        default=5,
        help="Samples per archetype"
    )
    parser.add_argument(
        "--archetypes",
        nargs="+",
        default=["A", "B", "C"],
        help="Archetypes to test (default: A B C)"
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("POLICY LAYER TESTING")
    print("=" * 70)
    
    scenarios = args.scenarios
    all_results = {}
    
    for scenario in scenarios:
        print(f"\nTesting {scenario}...")
        results = test_scenario_policy_comparison(
            scenario,
            n_samples=args.n_samples,
            archetypes=args.archetypes
        )
        all_results[scenario] = results
    
    # Summary table
    print("\n" + "=" * 70)
    print("SUMMARY TABLE")
    print("=" * 70)
    print(f"{'Scenario':<10} {'Policy':<20} {'Expired Rate':<15} {'Stockout Rate':<15}")
    print("-" * 70)
    
    for scenario in scenarios:
        for mode in ['forecast_driven', 'forecast_capped', 'policy_selected', 'par_driven_all']:
            expired = np.mean(all_results[scenario][mode]['expired'])
            stockout = np.mean(all_results[scenario][mode]['stockout'])
            print(f"{scenario:<10} {mode:<20} {expired:>6.2f}%         {stockout:>6.2f}%")


if __name__ == "__main__":
    main()
