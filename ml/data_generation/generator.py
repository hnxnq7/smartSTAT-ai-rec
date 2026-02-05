"""
Core generator functions for synthetic medication demand datasets.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import random
import math

# Policy selection (optional import to avoid circular dependency)
try:
    from ml.data_generation.policy_selector import get_policy_metadata
    HAS_POLICY_SELECTOR = True
except ImportError:
    HAS_POLICY_SELECTOR = False


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
    
    def lognormal(self, median: float, p95: float) -> float:
        """Generate random number from log-normal distribution.
        
        Args:
            median: Median value (50th percentile)
            p95: 95th percentile value
        
        Returns:
            Random value from log-normal distribution
        """
        # For log-normal: if X ~ LN(mu, sigma), then median = exp(mu)
        # p95 = exp(mu + 1.645*sigma)  (1.645 is Z-score for 95th percentile)
        mu = math.log(median)
        # Solve: p95 = exp(mu + 1.645*sigma)
        # ln(p95) = mu + 1.645*sigma
        # sigma = (ln(p95) - mu) / 1.645
        sigma = (math.log(p95) - mu) / 1.645
        # Generate from log-normal: exp(normal(mu, sigma))
        u1 = self.random()
        u2 = self.random()
        z = math.sqrt(-2 * math.log(u1 + 1e-10)) * math.cos(2 * math.pi * u2)
        normal_value = mu + sigma * z
        return max(1.0, math.exp(normal_value))  # Ensure positive, at least 1 day


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
    initial_stock_ratio: float = 2.0,
    archetype: Optional[str] = None,  # PRIORITY 3: Category-specific multipliers
    shelf_life_days: Optional[int] = None,  # Override shelf life from config
    order_cadence_days: Optional[int] = None,  # Override order cadence from config
    service_level_target: Optional[float] = None,  # Override service level from config
    moq_units: Optional[int] = None,  # Override MOQ from config
    spq_units: Optional[int] = None,  # Override SPQ from config
    ordering_mode: Optional[str] = None,  # "par_driven" or "forecast_driven" or "auto" (default)
    par_level_days: Optional[int] = None,  # Par level in days coverage (for par-driven)
    policy_auto_select: bool = False,  # If True and ordering_mode="auto", select policy automatically
    shelf_life_mode: Optional[str] = None,  # "effective" or "labeled" (default)
    pull_buffer_days: Optional[int] = None,  # Pull buffer for effective shelf life
    lead_time_distribution: Optional[str] = None,  # "lognormal" or "fixed" (default)
    lead_time_median: Optional[float] = None,  # Median lead time (for lognormal)
    lead_time_p95: Optional[float] = None  # 95th percentile lead time (for lognormal)
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate inventory flow based on usage.
    
    Args:
        shelf_life_days: Shelf life in days (overrides size-based defaults)
        order_cadence_days: Days between order opportunities (for ordering logic)
        service_level_target: Target service level (0.95-0.999, maps to Z-score)
        moq_units: Minimum order quantity (enforced if provided)
        spq_units: Standard pack quantity / minimum order increment (enforced if provided)
    
    Returns:
        total_onsite_units, expired_units, newly_added_units, 
        ordered_units, non_expired_inventory
    """
    # Size-based parameters (defaults, overridden by config if provided)
    size_params = {
        "small": {"shelf_life_days": 180, "order_size_multiplier": 1.5},
        "medium": {"shelf_life_days": 210, "order_size_multiplier": 1.3},
        "large": {"shelf_life_days": 240, "order_size_multiplier": 1.2},
    }
    params = size_params[hospital_size].copy()
    
    # Override with config values if provided
    if shelf_life_days is not None:
        params["shelf_life_days"] = shelf_life_days
    
    # Calculate effective shelf life if mode is "effective"
    if shelf_life_mode == "effective" and pull_buffer_days is not None:
        # Effective shelf life = labeled - pull buffer
        effective_shelf_life = max(1, params["shelf_life_days"] - pull_buffer_days)
        params["shelf_life_days"] = effective_shelf_life
    
    n_days = len(dates)
    avg_daily_usage = np.mean(used_units)
    
    # Policy selection (if auto mode enabled)
    effective_ordering_mode = ordering_mode
    if ordering_mode == "auto" and policy_auto_select and HAS_POLICY_SELECTOR:
        # Calculate demand characteristics for policy selection
        std_usage = np.std(used_units) if len(used_units) > 1 else 0.0
        cv_demand = (std_usage / avg_daily_usage) if avg_daily_usage > 0 else 0.0
        
        # Determine criticality from archetype (E = critical, others = routine)
        criticality = "critical" if archetype == "E" else "routine"
        
        # Get policy metadata
        policy_meta = get_policy_metadata(
            avg_daily_usage=avg_daily_usage,
            used_units_array=used_units,
            shelf_life_days=params["shelf_life_days"],
            moq_units=moq_units,
            criticality=criticality,
            exchange_cadence_days=order_cadence_days,
        )
        effective_ordering_mode = policy_meta["policy"]
    
    # Determine ordering mode (default to forecast_driven)
    use_par_driven = (effective_ordering_mode == "par_driven")
    if use_par_driven and par_level_days is None:
        par_level_days = 30  # Default par level: 30 days coverage
    
    # Determine lead time distribution
    use_stochastic_lead_time = (lead_time_distribution == "lognormal")
    if use_stochastic_lead_time:
        if lead_time_median is None:
            lead_time_median = float(lead_time)  # Use provided lead_time as median
        if lead_time_p95 is None:
            lead_time_p95 = lead_time_median * 3.0  # Default: 3x median for p95
    
    # For par-driven: Calculate par level ONCE at start (use median lead time for consistency)
    if use_par_driven:
        # Use median lead time for par level calculation (not stochastic per-order)
        par_lead_time = int(lead_time_median) if use_stochastic_lead_time and lead_time_median else lead_time
        # Increased safety buffer: lead time + 7 days base + 7 days demand variability buffer
        # This accounts for demand spikes and lead time variability (reduced from 14 to 7 to avoid over-ordering)
        safety_buffer_days = 7
        demand_variability_buffer_days = 7  # Additional buffer for demand variability (reduced to balance stockout vs expiration)
        total_coverage_days = par_level_days + par_lead_time + safety_buffer_days + demand_variability_buffer_days
        # Use avg_daily_usage for par level (will be adjusted with recent consumption when ordering)
        base_par_level_units = int(avg_daily_usage * total_coverage_days)
        # Store for use in loop
        par_lead_time_for_par = par_lead_time
    else:
        base_par_level_units = None
        par_lead_time_for_par = None
    
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
    # For par-driven: Start with par level to avoid immediate stockouts
    if use_par_driven and par_level_days is not None:
        # Use current_lead_time (will be set below, but use lead_time as fallback)
        effective_lead_time = lead_time
        if use_stochastic_lead_time and lead_time_median is not None:
            effective_lead_time = int(lead_time_median)
        # Start with par level (includes lead time + safety buffer + demand variability buffer)
        safety_buffer_days = 7
        demand_variability_buffer_days = 7  # Additional buffer for demand variability (reduced to balance stockout vs expiration)
        total_coverage_days = par_level_days + effective_lead_time + safety_buffer_days + demand_variability_buffer_days
        initial_stock = int(avg_daily_usage * total_coverage_days)
    else:
        initial_stock = int(avg_daily_usage * initial_stock_ratio * 30)  # ~30 days coverage
    
    batches.append((0, initial_stock, params["shelf_life_days"]))
    total_onsite[0] = initial_stock
    non_expired[0] = initial_stock
    
    # Initial reorder point (will be calculated dynamically)
    base_reorder_point = int(avg_daily_usage * reorder_point_ratio * 30)
    base_order_quantity = int(avg_daily_usage * params["order_size_multiplier"] * 30)
    
    # PRIORITY 2: Dynamic safety stock - track stockout history
    stockout_history = []  # Track stockouts for dynamic adjustment
    lookback_window = 30
    dynamic_reorder_point_ratio = reorder_point_ratio  # Will adjust based on stockouts
    
    for day in range(n_days):
        # Update stock at start of day (before usage)
        if day > 0:
            total_onsite[day] = total_onsite[day - 1]
            non_expired[day] = non_expired[day - 1]
        
        # Process arrivals (newly_added from pending orders)
        if day in pending_orders:
            quantity = pending_orders.pop(day)
            newly_added[day] = quantity
            expiry_day = day + params["shelf_life_days"]
            batches.append((day, quantity, expiry_day))
            total_onsite[day] += quantity
            non_expired[day] += quantity
        
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
        
        # Apply usage (reduce from non-expired) - FEFO (First-Expiry-First-Out)
        # Consume batches closest to expiration first to minimize waste
        usage_today = used_units[day]
        remaining_usage = usage_today
        
        # Sort batches by expiry_date (FEFO) - batches expiring soonest consumed first
        batches_sorted = sorted(batches, key=lambda x: x[2])  # x[2] = expiry_date
        
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
        
        # PRIORITY 2: Track stockout history for dynamic safety stock adjustment
        had_stockout = (non_expired[day] <= 0)
        stockout_history.append(1 if had_stockout else 0)
        # Keep only last lookback_window days
        if len(stockout_history) > lookback_window:
            stockout_history.pop(0)
        
        # PRIORITY 2: Dynamic reorder point ratio adjustment based on recent stockout rate
        if len(stockout_history) >= 7:  # Need at least 7 days of history
            recent_stockout_rate = sum(stockout_history) / len(stockout_history)
            
            # Adjust reorder_point_ratio based on recent performance
            # Lower stockout rate → lower reorder point (less safety stock needed)
            if recent_stockout_rate < 0.005:  # < 0.5% stockout rate
                # Reduce reorder point ratio by ~30% (equivalent to ~95% service level vs 99.5%)
                dynamic_reorder_point_ratio = reorder_point_ratio * 0.7
            elif recent_stockout_rate < 0.01:  # < 1% stockout rate
                # Reduce reorder point ratio by ~10% (equivalent to ~99% service level)
                dynamic_reorder_point_ratio = reorder_point_ratio * 0.9
            else:
                # Keep original ratio if stockouts are higher
                dynamic_reorder_point_ratio = reorder_point_ratio
        else:
            # Use original ratio for first few days
            dynamic_reorder_point_ratio = reorder_point_ratio
        
        # Determine lead time for this order (stochastic if enabled)
        if use_stochastic_lead_time:
            current_lead_time = int(rng.lognormal(lead_time_median, lead_time_p95))
            current_lead_time = max(1, min(current_lead_time, 90))  # Clamp to 1-90 days
        else:
            current_lead_time = lead_time
        
        # PRIORITY 1: Adaptive Order Quantities & Inventory-Aware Ordering
        # Calculate recent consumption for adaptive ordering
        if day >= 14:
            # Use last 14 days of actual consumption for more accurate ordering
            recent_consumption = np.mean(used_units[max(0, day-14):day])
        elif day >= 7:
            # Use last 7 days if 14 days not available
            recent_consumption = np.mean(used_units[max(0, day-7):day])
        else:
            # Fall back to average for early days
            recent_consumption = avg_daily_usage
        
        # PAR-DRIVEN ORDERING MODE (Option C)
        if use_par_driven:
            # Par-driven: Maintain fixed par level regardless of forecast
            # Use base par level calculated at start, but adjust for recent consumption if higher
            usage_for_par = max(recent_consumption, avg_daily_usage * 0.95)  # Use recent or 95% of avg (whichever higher)
            # Scale base par level by usage ratio (but don't go below base)
            usage_ratio = max(1.0, usage_for_par / avg_daily_usage) if avg_daily_usage > 0 else 1.0
            par_level_units = int(base_par_level_units * usage_ratio)
            
            # Check if we should order
            # For par-driven: Order immediately when below par (don't wait for cadence)
            # But respect minimum time between orders (cadence) to avoid too frequent ordering
            should_order = False
            
            # Calculate total available inventory (current + pending)
            total_pending = sum(pending_orders.values()) if pending_orders else 0
            total_available = non_expired[day] + total_pending
            
            # Check if inventory is below par level
            if total_available < par_level_units:
                # Calculate days of coverage
                days_coverage = non_expired[day] / (recent_consumption + 1e-6) if recent_consumption > 0 else 0
                
                # Emergency: If coverage is less than lead time + buffer, order immediately
                # Use par_lead_time_for_par (median) for threshold, not current_lead_time (stochastic)
                # Reduced buffer to trigger emergency ordering earlier
                emergency_threshold = par_lead_time_for_par + 3  # Lead time + 3 day buffer (reduced to trigger earlier)
                is_emergency = (days_coverage < emergency_threshold) or (non_expired[day] <= 0)
                
                if is_emergency:
                    # Emergency: Order immediately regardless of cadence
                    should_order = True
                elif order_cadence_days is None or day % order_cadence_days == 0:
                    # Routine: Only order on cadence days if above emergency threshold
                    should_order = True
            
            if should_order:
                # Calculate order quantity to restore to par level
                order_quantity = par_level_units - total_available
                order_quantity = max(0, order_quantity)  # Ensure non-negative
                
                # If we're at zero or very low, ensure we order at least enough to cover lead time + buffer
                if non_expired[day] <= 0 or days_coverage < par_lead_time_for_par:
                    min_order_for_lead_time = int(recent_consumption * (par_lead_time_for_par + 7))  # Lead time + 7 day buffer
                    order_quantity = max(order_quantity, min_order_for_lead_time)
                
                # Apply MOQ constraint if provided
                if moq_units is not None and order_quantity > 0:
                    order_quantity = ((order_quantity + moq_units - 1) // moq_units) * moq_units
                
                # Apply SPQ constraint if provided
                if spq_units is not None and order_quantity > 0:
                    order_quantity = ((order_quantity + spq_units - 1) // spq_units) * spq_units
                
                # Place order
                if order_quantity > 0:
                    order_date = day + current_lead_time
                    if order_date < n_days:
                        ordered_units[day] = order_quantity
                        if order_date not in pending_orders:
                            pending_orders[order_date] = 0
                        pending_orders[order_date] += order_quantity
        else:
            # FORECAST-DRIVEN ORDERING MODE (default, existing logic)
            
            # Adaptive reorder point based on recent consumption and dynamic ratio
            # Use order_cadence_days from config if provided, otherwise default to 7 days
            if order_cadence_days is not None:
                expected_days_until_reorder = max(current_lead_time + 3, order_cadence_days)
            else:
                expected_days_until_reorder = max(current_lead_time + 3, 7)  # At least 7 days
            # Use dynamic_reorder_point_ratio (Priority 2: dynamic safety stock)
            adaptive_reorder_point = int(recent_consumption * dynamic_reorder_point_ratio * expected_days_until_reorder)
            
            # UNDER_50_PERCENT: Strategy 1 - Shelf-Life Aware Ordering
            # Calculate inventory age risk relative to shelf life
            shelf_life_days = params["shelf_life_days"]
            if recent_consumption > 0:
                current_inventory_days = non_expired[day] / (recent_consumption + 1e-6)
                inventory_age_ratio = current_inventory_days / shelf_life_days if shelf_life_days > 0 else 0
            else:
                inventory_age_ratio = 0
            
            # UNDER_50_PERCENT: Strategy 3 - Category-Specific Buffers (reduced from 10%)
            category_buffers = {
                'A': 1.02,  # 2% buffer - stable demand
                'B': 1.01,  # 1% buffer - low volume, minimize waste
                'C': 1.02,  # 2% buffer - weekly pattern
                'D': 1.05,  # 5% buffer - trending, need some buffer
                'E': 1.08,  # 8% buffer - burst events, need safety
            }
            buffer_multiplier = category_buffers.get(archetype, 1.02) if archetype else 1.02
            
            # UNDER_50_PERCENT: Strategy 2 - Category-Specific Order Caps
            category_order_caps = {
                'A': 12,  # Stable - can order less
                'B': 10,  # Low volume - even smaller orders
                'C': 12,  # Weekly pattern - smaller orders
                'D': 16,  # Trending - need slightly more buffer
                'E': 18,  # Burst events - need buffer but not too much
            }
            max_order_days_supply = category_order_caps.get(archetype, 12) if archetype else 12
            
            # PRIORITY 3: Category-Specific Order Multipliers (keep for compatibility)
            category_multipliers = {
                'A': 1.0,   # Stable demand - order exactly what's needed
                'B': 0.8,   # Low volume - smaller orders, more frequent
                'C': 1.0,   # Weekly pattern - order weekly amounts
                'D': 1.1,   # Trending - slightly more for trends
                'E': 1.2,   # Burst events - need buffer for spikes
            }
            category_multiplier = category_multipliers.get(archetype, 1.0) if archetype else 1.0
            
            # Adaptive order quantity with reduced buffer
            order_quantity_base = recent_consumption * expected_days_until_reorder * buffer_multiplier
            # Apply category-specific multiplier
            adaptive_order_quantity = int(order_quantity_base * category_multiplier)
            
            # Apply shelf-life aware reduction
            if inventory_age_ratio > 0.25:
                # If inventory represents >25% of shelf life, reduce orders by 50%
                adaptive_order_quantity = int(adaptive_order_quantity * 0.5)
            elif inventory_age_ratio > 0.15:
                # If inventory represents >15% of shelf life, reduce orders by 25%
                adaptive_order_quantity = int(adaptive_order_quantity * 0.75)
            
            # Apply category-specific order cap
            max_order = int(recent_consumption * max_order_days_supply)
            adaptive_order_quantity = min(adaptive_order_quantity, max_order)
            
            # Apply MOQ constraint if provided
            if moq_units is not None:
                # Round up to nearest MOQ multiple
                adaptive_order_quantity = ((adaptive_order_quantity + moq_units - 1) // moq_units) * moq_units
            
            # Apply SPQ constraint if provided
            if spq_units is not None:
                # Round up to nearest SPQ multiple
                adaptive_order_quantity = ((adaptive_order_quantity + spq_units - 1) // spq_units) * spq_units
            
            # Ensure minimum order quantity (at least lead_time days)
            min_order = int(recent_consumption * current_lead_time)
            adaptive_order_quantity = max(adaptive_order_quantity, min_order)
            
            # PRIORITY 1: Inventory-Aware Ordering
            # Calculate total available inventory (current + pending orders)
            total_pending = sum(pending_orders.values()) if pending_orders else 0
            total_available = non_expired[day] + total_pending
            
            # Projected demand over next period (lead_time + buffer)
            lookahead_days = current_lead_time + 7
            lookahead_end = min(day + 1 + lookahead_days, n_days)
            if lookahead_end > day + 1:
                projected_demand = int(np.sum(used_units[day+1:lookahead_end]))
            else:
                projected_demand = int(recent_consumption * lookahead_days)
            
            # UNDER_50_PERCENT: Strategy 1 - Shelf-Life Aware Ordering (stop orders if inventory too old)
            # If inventory represents >40% of shelf life, stop ordering entirely
            if inventory_age_ratio > 0.40:
                should_order = False  # Don't order - consume existing inventory first
            else:
                # UNDER_50_PERCENT: Strategy 5 - Inventory Age-Based Reorder Points
                # Adjust reorder point based on inventory age
                if inventory_age_ratio < 0.15:
                    # If inventory is relatively new (<15% of shelf life), raise reorder point
                    # This delays ordering when inventory is fresh
                    adjusted_reorder_point = int(adaptive_reorder_point * 1.3)
                elif inventory_age_ratio > 0.30:
                    # If inventory is aging (>30% of shelf life), lower reorder point
                    # This orders earlier to avoid expiration
                    adjusted_reorder_point = int(adaptive_reorder_point * 0.8)
                else:
                    adjusted_reorder_point = adaptive_reorder_point
                
                # PRIORITY 4: Strategy 2 - Consume Inventory Before Reordering (refined)
                # Calculate days of coverage with current inventory
                if recent_consumption > 0:
                    days_coverage = non_expired[day] / (recent_consumption + 1e-6)
                else:
                    days_coverage = 0
                
                # If inventory can cover 10+ days, delay reorder (reduced from 12 days)
                if days_coverage > 10:
                    # Increase reorder point threshold by 20% (order later)
                    adjusted_reorder_point = max(adjusted_reorder_point, int(adaptive_reorder_point * 1.2))
                
                # Only order if total available inventory < projected demand * safety_factor
                safety_factor = 1.2  # 20% safety buffer
                should_order = (non_expired[day] <= adjusted_reorder_point) and (total_available < projected_demand * safety_factor)
            
                # Check reorder point (with inventory-aware logic)
                if should_order:
                    order_date = day + current_lead_time
                    if order_date < n_days:
                        ordered_units[day] = adaptive_order_quantity
                        if order_date not in pending_orders:
                            pending_orders[order_date] = 0
                        pending_orders[order_date] += adaptive_order_quantity
        
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
    
    # TREND DETECTION FEATURES (for Category D improvement)
    # Linear regression slope over rolling windows (trend direction and strength)
    # Using shifted data to avoid leakage
    shifted_used = df['used_units'].shift(1).fillna(0)
    
    def calculate_trend_slope(series: pd.Series, window: int) -> pd.Series:
        """Calculate linear regression slope over rolling window."""
        slopes = []
        for i in range(len(series)):
            if i < window:
                slopes.append(0.0)
            else:
                y = series.iloc[i-window+1:i+1].values
                x = np.arange(len(y))
                if len(y) > 1 and np.std(y) > 1e-6:
                    # Use polyfit for linear regression slope
                    slope = np.polyfit(x, y, 1)[0]
                    slopes.append(slope)
                else:
                    slopes.append(0.0)
        return pd.Series(slopes, index=series.index)
    
    # Trend slopes over different windows
    df['trend_slope_7d'] = calculate_trend_slope(shifted_used, window=7)
    df['trend_slope_14d'] = calculate_trend_slope(shifted_used, window=14)
    df['trend_slope_30d'] = calculate_trend_slope(shifted_used, window=30)
    
    # Momentum indicators (rate of change)
    df['momentum_7d'] = (df['used_lag_1'] - df['used_units'].shift(8).fillna(0)) / 7.0
    df['momentum_14d'] = (df['used_lag_1'] - df['used_units'].shift(15).fillna(0)) / 14.0
    df['momentum_30d'] = (df['used_lag_1'] - df['used_units'].shift(31).fillna(0)) / 30.0
    
    # Trend direction indicators (positive/negative trend)
    df['trend_up_7d'] = (df['trend_slope_7d'] > 0).astype(int)
    df['trend_up_14d'] = (df['trend_slope_14d'] > 0).astype(int)
    df['trend_up_30d'] = (df['trend_slope_30d'] > 0).astype(int)
    
    # Normalized trend strength (slope relative to average level)
    avg_used = df['rolling_used_30d_avg'].fillna(1.0)  # Avoid division by zero
    df['trend_strength_7d'] = np.where(
        avg_used > 1e-6,
        df['trend_slope_7d'] / (avg_used + 1e-6),
        0.0
    )
    df['trend_strength_14d'] = np.where(
        avg_used > 1e-6,
        df['trend_slope_14d'] / (avg_used + 1e-6),
        0.0
    )
    df['trend_strength_30d'] = np.where(
        avg_used > 1e-6,
        df['trend_slope_30d'] / (avg_used + 1e-6),
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
    end_date: str = "2025-12-31",
    config_params: Optional[Dict[str, Any]] = None  # Optional config parameters
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
    
    # Determine lead time (varies by size, or use config if provided)
    if config_params:
        lead_time = config_params.get('lead_time_days', 5)
        shelf_life_days = config_params.get('shelf_life_days', None)
        order_cadence_days = config_params.get('order_cadence_days', None)
        service_level_target = config_params.get('service_level_target', None)
        moq_units = config_params.get('moq_units', None)
        spq_units = config_params.get('spq_units', None)
        # Code Cart Parameters (Option C)
        ordering_mode = config_params.get('ordering_mode', None)
        policy_auto_select = config_params.get('policy_auto_select', False)
        par_level_days = config_params.get('par_level_days', None)
        shelf_life_mode = config_params.get('shelf_life_mode', None)
        pull_buffer_days = config_params.get('pull_buffer_days', None)
        lead_time_distribution = config_params.get('lead_time_distribution', None)
        lead_time_median = config_params.get('lead_time_median', None)
        lead_time_p95 = config_params.get('lead_time_p95', None)
    else:
        size_lead_times = {"small": (2, 4), "medium": (3, 5), "large": (4, 7)}
        lead_time_range = size_lead_times[hospital_size]
        lead_time = rng.randint(lead_time_range[0], lead_time_range[1])
        shelf_life_days = None
        order_cadence_days = None
        service_level_target = None
        moq_units = None
        spq_units = None
        ordering_mode = None
        policy_auto_select = False
        par_level_days = None
        shelf_life_mode = None
        pull_buffer_days = None
        lead_time_distribution = None
        lead_time_median = None
        lead_time_p95 = None

    policy_meta = None
    if ordering_mode == "auto" and policy_auto_select and HAS_POLICY_SELECTOR:
        default_shelf_life = {"small": 180, "medium": 210, "large": 240}
        shelf_life_for_policy = shelf_life_days if shelf_life_days is not None else default_shelf_life[hospital_size]
        if shelf_life_mode == "effective" and pull_buffer_days is not None:
            shelf_life_for_policy = max(1, shelf_life_for_policy - pull_buffer_days)
        avg_daily_usage = float(np.mean(used_units)) if len(used_units) > 0 else 0.0
        criticality = "critical" if archetype == "E" else "routine"
        policy_meta = get_policy_metadata(
            avg_daily_usage=avg_daily_usage,
            used_units_array=used_units,
            shelf_life_days=int(shelf_life_for_policy),
            moq_units=moq_units,
            criticality=criticality,
            exchange_cadence_days=order_cadence_days,
        )
    
    # Simulate inventory (PRIORITY 3: Pass archetype for category-specific multipliers)
    # Pass config parameters if provided (including code cart parameters)
    total_onsite, expired, newly_added, ordered, non_expired = simulate_inventory(
        dates, used_units, rng, hospital_size, lead_time, 
        archetype=archetype,
        shelf_life_days=shelf_life_days,
        order_cadence_days=order_cadence_days,
        service_level_target=service_level_target,
        moq_units=moq_units,
        spq_units=spq_units,
        ordering_mode=ordering_mode,
        par_level_days=par_level_days,
        policy_auto_select=policy_auto_select,
        shelf_life_mode=shelf_life_mode,
        pull_buffer_days=pull_buffer_days,
        lead_time_distribution=lead_time_distribution,
        lead_time_median=lead_time_median,
        lead_time_p95=lead_time_p95
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
    
    if policy_meta:
        metadata.update({
            'policy_selected': policy_meta.get('policy'),
            'policy_reasoning': "; ".join(policy_meta.get('reasoning', [])),
            'policy_avg_daily_usage': policy_meta.get('metadata', {}).get('avg_daily_usage'),
            'policy_cv_demand': policy_meta.get('metadata', {}).get('cv_demand'),
            'policy_is_low_volume': policy_meta.get('metadata', {}).get('is_low_volume'),
            'policy_is_high_intermittency': policy_meta.get('metadata', {}).get('is_high_intermittency'),
            'policy_is_short_shelf_life': policy_meta.get('metadata', {}).get('is_short_shelf_life'),
            'policy_is_exchange_based': policy_meta.get('metadata', {}).get('is_exchange_based'),
            'policy_criticality': policy_meta.get('metadata', {}).get('criticality'),
        })
    
    return df, metadata
