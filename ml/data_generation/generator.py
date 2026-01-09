"""
Core generator functions for synthetic medication demand datasets.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import random


class SeededRandom:
    """Seeded random number generator for reproducibility."""
    
    def __init__(self, seed: int):
        self.seed = seed
    
    def random(self) -> float:
        """Generate random float in [0, 1)."""
        self.seed = (self.seed * 1103515245 + 12345) & 0x7fffffff
        return self.seed / 2147483648.0
    
    def randint(self, a: int, b: int) -> int:
        """Generate random integer in [a, b]."""
        return int(self.random() * (b - a + 1)) + a
    
    def choice(self, seq):
        """Choose random element from sequence."""
        return seq[self.randint(0, len(seq) - 1)]
    
    def gauss(self, mu: float, sigma: float) -> float:
        """Generate random number from normal distribution (Box-Muller)."""
        import math
        u1 = self.random()
        u2 = self.random()
        z = math.sqrt(-2 * math.log(u1 + 1e-10)) * math.cos(2 * math.pi * u2)
        return mu + sigma * z


def generate_demand_archetype_a(
    dates: pd.DatetimeIndex,
    rng: SeededRandom,
    hospital_size: str,
    season_amp: float = 0.15,
    phase: float = 0.0
) -> np.ndarray:
    """
    Archetype A: High volume, stable demand.
    - Consistent daily usage with small seasonal variation
    - Low variance relative to mean
    """
    size_multipliers = {"small": 20, "medium": 50, "large": 120}
    base_demand = size_multipliers[hospital_size]
    
    # Add seasonal pattern (yearly cycle)
    day_of_year = dates.dayofyear
    seasonal = 1.0 + season_amp * np.sin(2 * np.pi * (day_of_year / 365.25 + phase))
    
    # Generate daily demand with Poisson noise
    demands = []
    for i, date in enumerate(dates):
        lambda_param = base_demand * seasonal[i] * (1.0 + 0.05 * rng.gauss(0, 1))
        demand = max(0, int(rng.gauss(lambda_param, lambda_param * 0.15)))
        demands.append(demand)
    
    return np.array(demands, dtype=int)


def generate_demand_archetype_b(
    dates: pd.DatetimeIndex,
    rng: SeededRandom,
    hospital_size: str,
    zero_prob: float = 0.4
) -> np.ndarray:
    """
    Archetype B: Low volume, intermittent (many zero days).
    - Many days with zero usage
    - When usage occurs, typically small quantities
    """
    size_multipliers = {"small": 1.5, "medium": 3.0, "large": 6.0}
    base_demand = size_multipliers[hospital_size]
    
    demands = []
    for date in dates:
        if rng.random() < zero_prob:
            demands.append(0)
        else:
            # Poisson-like with small mean
            lambda_param = base_demand * (0.8 + 0.4 * rng.random())
            demand = max(0, int(rng.gauss(lambda_param, lambda_param * 0.5)))
            demands.append(demand)
    
    return np.array(demands, dtype=int)


def generate_demand_archetype_c(
    dates: pd.DatetimeIndex,
    rng: SeededRandom,
    hospital_size: str,
    weekday_multiplier: float = 1.5,
    weekend_multiplier: float = 0.6
) -> np.ndarray:
    """
    Archetype C: Weekly pattern (weekday high, weekend low).
    - Clear day-of-week effect
    - Weekdays higher, weekends lower
    """
    size_multipliers = {"small": 15, "medium": 35, "large": 80}
    base_demand = size_multipliers[hospital_size]
    
    demands = []
    for date in dates:
        day_of_week = date.weekday()  # 0=Monday, 6=Sunday
        is_weekend = day_of_week >= 5
        multiplier = weekend_multiplier if is_weekend else weekday_multiplier
        
        lambda_param = base_demand * multiplier * (0.9 + 0.2 * rng.random())
        demand = max(0, int(rng.gauss(lambda_param, lambda_param * 0.2)))
        demands.append(demand)
    
    return np.array(demands, dtype=int)


def generate_demand_archetype_d(
    dates: pd.DatetimeIndex,
    rng: SeededRandom,
    hospital_size: str,
    trend_type: str = "linear_up",
    trend_rate: float = 0.001,
    step_change_day: Optional[int] = None,
    step_multiplier: float = 1.5
) -> np.ndarray:
    """
    Archetype D: Trend up/down with possible seasonality.
    - Linear trend or step change
    - Can be increasing or decreasing
    """
    size_multipliers = {"small": 25, "medium": 60, "large": 140}
    base_demand = size_multipliers[hospital_size]
    
    # Determine trend direction
    if trend_type == "random":
        trend_type = rng.choice(["linear_up", "linear_down", "step_up", "step_down"])
    
    n_days = len(dates)
    day_numbers = np.arange(n_days)
    
    demands = []
    for i, date in enumerate(dates):
        # Base level
        level = base_demand
        
        # Apply trend
        if "linear" in trend_type:
            if "up" in trend_type:
                level *= (1.0 + trend_rate * day_numbers[i])
            else:  # down
                level *= (1.0 - trend_rate * day_numbers[i])
        
        # Apply step change
        if "step" in trend_type and step_change_day is not None:
            if i >= step_change_day:
                if "up" in trend_type:
                    level *= step_multiplier
                else:  # down
                    level *= (1.0 / step_multiplier)
        
        # Add seasonal variation
        day_of_year = date.dayofyear
        seasonal = 1.0 + 0.1 * np.sin(2 * np.pi * day_of_year / 365.25)
        level *= seasonal
        
        # Add noise
        lambda_param = level * (0.95 + 0.1 * rng.random())
        demand = max(0, int(rng.gauss(lambda_param, lambda_param * 0.18)))
        demands.append(demand)
    
    return np.array(demands, dtype=int)


def generate_demand_archetype_e(
    dates: pd.DatetimeIndex,
    rng: SeededRandom,
    hospital_size: str,
    burst_prob: float = 0.02,
    burst_multiplier: float = 3.0
) -> np.ndarray:
    """
    Archetype E: Burst events (rare spike days).
    - Mostly normal usage with occasional large spikes
    - Spikes can cluster in time windows
    """
    size_multipliers = {"small": 18, "medium": 45, "large": 100}
    base_demand = size_multipliers[hospital_size]
    
    demands = []
    burst_active = False
    burst_remaining = 0
    
    for date in dates:
        # Check for new burst
        if not burst_active and rng.random() < burst_prob:
            burst_active = True
            burst_remaining = rng.randint(1, 3)  # Burst lasts 1-3 days
        
        # Apply burst multiplier if active
        multiplier = burst_multiplier if burst_active else 1.0
        if burst_active:
            burst_remaining -= 1
            if burst_remaining <= 0:
                burst_active = False
        
        # Generate demand
        lambda_param = base_demand * multiplier * (0.9 + 0.2 * rng.random())
        demand = max(0, int(rng.gauss(lambda_param, lambda_param * 0.25)))
        demands.append(demand)
    
    return np.array(demands, dtype=int)


def simulate_inventory(
    dates: pd.DatetimeIndex,
    used_units: np.ndarray,
    rng: SeededRandom,
    hospital_size: str,
    lead_time: int = 3,
    reorder_point_ratio: float = 0.3,
    initial_stock_ratio: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate inventory flow based on usage.
    
    Returns:
        total_onsite_units, expired_units, newly_added_units, 
        ordered_units, non_expired_inventory
    """
    # Size-based parameters
    size_params = {
        "small": {"shelf_life_days": 180, "order_size_multiplier": 1.5},
        "medium": {"shelf_life_days": 210, "order_size_multiplier": 1.3},
        "large": {"shelf_life_days": 240, "order_size_multiplier": 1.2},
    }
    params = size_params[hospital_size]
    
    n_days = len(dates)
    avg_daily_usage = np.mean(used_units)
    
    # Initialize
    total_onsite = np.zeros(n_days, dtype=int)
    expired_units = np.zeros(n_days, dtype=int)
    newly_added = np.zeros(n_days, dtype=int)
    ordered_units = np.zeros(n_days, dtype=int)
    non_expired = np.zeros(n_days, dtype=int)
    
    # Track pending orders (order_date -> quantity)
    pending_orders = {}
    
    # Track inventory batches (arrival_date, quantity, expiry_date)
    batches = []
    
    # Initial stock
    initial_stock = int(avg_daily_usage * initial_stock_ratio * 30)  # ~30 days coverage
    batches.append((0, initial_stock, params["shelf_life_days"]))
    total_onsite[0] = initial_stock
    non_expired[0] = initial_stock
    
    reorder_point = int(avg_daily_usage * reorder_point_ratio * 30)
    order_quantity = int(avg_daily_usage * params["order_size_multiplier"] * 30)
    
    for day in range(n_days):
        # Process arrivals (newly_added from pending orders)
        if day in pending_orders:
            quantity = pending_orders.pop(day)
            newly_added[day] = quantity
            expiry_day = day + params["shelf_life_days"]
            batches.append((day, quantity, expiry_day))
            total_onsite[day] += quantity
            non_expired[day] += quantity
        
        # Update stock at start of day (before usage)
        if day > 0:
            total_onsite[day] = total_onsite[day - 1]
            non_expired[day] = non_expired[day - 1]
        
        # Process expiration (batches that expire today)
        expired_today = 0
        batches_to_remove = []
        for batch in batches:
            batch_arrival, batch_qty, batch_expiry = batch
            if batch_expiry == day:
                expired_today += batch_qty
                batches_to_remove.append(batch)
        
        for batch in batches_to_remove:
            batches.remove(batch)
        
        expired_units[day] = expired_today
        total_onsite[day] -= expired_today
        non_expired[day] -= expired_today
        
        # Apply usage (reduce from non-expired, remove oldest batches first)
        usage_today = used_units[day]
        remaining_usage = usage_today
        
        # Sort batches by arrival (FIFO)
        batches_sorted = sorted(batches, key=lambda x: x[0])
        
        for batch in batches_sorted:
            if remaining_usage <= 0:
                break
            batch_arrival, batch_qty, batch_expiry = batch
            consumed = min(remaining_usage, batch_qty)
            remaining_usage -= consumed
            batch_qty -= consumed
            
            # Update or remove batch
            batches.remove(batch)
            if batch_qty > 0:
                batches.append((batch_arrival, batch_qty, batch_expiry))
        
        total_onsite[day] -= usage_today
        non_expired[day] -= usage_today
        
        # Ensure non-negative
        total_onsite[day] = max(0, total_onsite[day])
        non_expired[day] = max(0, non_expired[day])
        
        # Check reorder point (place order if stock is low)
        if non_expired[day] <= reorder_point:
            order_date = day + lead_time
            if order_date < n_days:
                ordered_units[day] = order_quantity
                if order_date not in pending_orders:
                    pending_orders[order_date] = 0
                pending_orders[order_date] += order_quantity
        
        # Update for next iteration
        if day < n_days - 1:
            total_onsite[day + 1] = total_onsite[day]
            non_expired[day + 1] = non_expired[day]
    
    return total_onsite, expired_units, newly_added, ordered_units, non_expired


def add_time_series_features(
    df: pd.DataFrame,
    used_units: np.ndarray
) -> pd.DataFrame:
    """
    Add time-series features with no data leakage.
    All features use only past information.
    """
    df = df.copy()
    
    # Basic temporal features
    df['day_of_week'] = df['date'].dt.dayofweek
    df['week_of_year'] = df['date'].dt.isocalendar().week
    df['month'] = df['date'].dt.month
    
    # Lag features (past values only)
    df['used_lag_1'] = df['used_units'].shift(1).fillna(0).astype(int)
    df['used_lag_2'] = df['used_units'].shift(2).fillna(0).astype(int)
    df['used_lag_7'] = df['used_units'].shift(7).fillna(0).astype(int)
    df['used_lag_14'] = df['used_units'].shift(14).fillna(0).astype(int)
    
    # Rolling statistics (using past window only)
    df['rolling_used_7d_total'] = df['used_units'].shift(1).rolling(window=7, min_periods=1).sum().fillna(0)
    df['rolling_used_7d_avg'] = df['used_units'].shift(1).rolling(window=7, min_periods=1).mean().fillna(0)
    
    df['rolling_used_30d_total'] = df['used_units'].shift(1).rolling(window=30, min_periods=1).sum().fillna(0)
    df['rolling_used_30d_avg'] = df['used_units'].shift(1).rolling(window=30, min_periods=1).mean().fillna(0)
    
    # Ratio features (avoid division by zero)
    df['usage_7d_to_30d_ratio'] = np.where(
        df['rolling_used_30d_total'] > 0,
        df['rolling_used_7d_total'] / df['rolling_used_30d_total'],
        0.0
    )
    
    # Days until stockout estimate (based on current stock and recent usage rate)
    recent_avg = df['rolling_used_7d_avg'].fillna(0)
    df['days_until_stockout_est'] = np.where(
        recent_avg > 0,
        df['non_expired_inventory'] / (recent_avg + 1e-6),
        np.nan
    )
    df['days_until_stockout_est'] = df['days_until_stockout_est'].fillna(999).astype(int)
    
    return df


def generate_scenario(
    scenario_id: str,
    archetype: str,
    hospital_size: str,
    seed: int,
    start_date: str = "2023-01-01",
    end_date: str = "2025-12-31"
) -> Tuple[pd.DataFrame, Dict]:
    """
    Generate a complete scenario with all required columns.
    
    Args:
        scenario_id: Unique scenario ID (e.g., "A023")
        archetype: Demand archetype ("A", "B", "C", "D", "E")
        hospital_size: Size tier ("small", "medium", "large")
        seed: Random seed for reproducibility
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Tuple of (DataFrame, metadata_dict)
    """
    rng = SeededRandom(seed)
    
    # Generate date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    n_days = len(dates)
    
    # Generate demand based on archetype
    if archetype == "A":
        season_amp = 0.1 + 0.1 * rng.random()
        phase = rng.random()
        used_units = generate_demand_archetype_a(dates, rng, hospital_size, season_amp, phase)
        gen_params = {"season_amp": season_amp, "phase": phase}
    
    elif archetype == "B":
        zero_prob = 0.3 + 0.3 * rng.random()
        used_units = generate_demand_archetype_b(dates, rng, hospital_size, zero_prob)
        gen_params = {"zero_prob": zero_prob}
    
    elif archetype == "C":
        weekday_mult = 1.3 + 0.4 * rng.random()
        weekend_mult = 0.5 + 0.2 * rng.random()
        used_units = generate_demand_archetype_c(dates, rng, hospital_size, weekday_mult, weekend_mult)
        gen_params = {"weekday_multiplier": weekday_mult, "weekend_multiplier": weekend_mult}
    
    elif archetype == "D":
        trend_types = ["linear_up", "linear_down", "step_up", "step_down"]
        trend_type = rng.choice(trend_types)
        trend_rate = 0.0005 + 0.001 * rng.random()
        step_day = rng.randint(200, n_days - 200) if "step" in trend_type else None
        step_mult = 1.3 + 0.4 * rng.random()
        used_units = generate_demand_archetype_d(
            dates, rng, hospital_size, trend_type, trend_rate, step_day, step_mult
        )
        gen_params = {
            "trend_type": trend_type,
            "trend_rate": trend_rate,
            "step_change_day": step_day,
            "step_multiplier": step_mult
        }
    
    elif archetype == "E":
        burst_prob = 0.01 + 0.03 * rng.random()
        burst_mult = 2.5 + 1.5 * rng.random()
        used_units = generate_demand_archetype_e(dates, rng, hospital_size, burst_prob, burst_mult)
        gen_params = {"burst_prob": burst_prob, "burst_multiplier": burst_mult}
    
    else:
        raise ValueError(f"Unknown archetype: {archetype}")
    
    # Determine lead time (varies by size)
    size_lead_times = {"small": (2, 4), "medium": (3, 5), "large": (4, 7)}
    lead_time_range = size_lead_times[hospital_size]
    lead_time = rng.randint(lead_time_range[0], lead_time_range[1])
    
    # Simulate inventory
    total_onsite, expired, newly_added, ordered, non_expired = simulate_inventory(
        dates, used_units, rng, hospital_size, lead_time
    )
    
    # Create base DataFrame
    df = pd.DataFrame({
        'date': dates,
        'total_onsite_units': total_onsite,
        'expired_units': expired,
        'used_units': used_units,
        'newly_added_units': newly_added,
        'ordered_units': ordered,
        'non_expired_inventory': non_expired,
    })
    
    # Add time-series features
    df = add_time_series_features(df, used_units)
    
    # Calculate metadata
    train_mask = df['date'] < '2025-01-01'
    test_mask = df['date'] >= '2025-01-01'
    
    train_used = df.loc[train_mask, 'used_units']
    test_used = df.loc[test_mask, 'used_units']
    
    metadata = {
        'scenario_id': scenario_id,
        'archetype': archetype,
        'hospital_size': hospital_size,
        'seed': seed,
        'lead_time': lead_time,
        'avg_used_train': float(train_used.mean()),
        'avg_used_test': float(test_used.mean()),
        'pct_zero_train': float((train_used == 0).mean() * 100),
        'pct_zero_test': float((test_used == 0).mean() * 100),
        'max_used_train': int(train_used.max()),
        'max_used_test': int(test_used.max()),
        **gen_params
    }
    
    return df, metadata
