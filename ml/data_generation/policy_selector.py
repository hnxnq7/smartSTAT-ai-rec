"""
Policy selection layer: Choose par-driven vs forecast-driven ordering based on SKU context.
"""
from typing import Dict, Optional, Literal


def select_ordering_policy(
    avg_daily_usage: float,
    cv_demand: float,  # Coefficient of variation (std/mean)
    shelf_life_days: int,
    moq_units: Optional[int] = None,
    criticality: str = "routine",  # "routine" or "critical"
    exchange_cadence_days: Optional[int] = None,
    min_daily_usage_threshold: float = 5.0,  # Below this = low volume
    high_cv_threshold: float = 1.0,  # Above this = high intermittency
    short_shelf_life_threshold: int = 180,  # Below this = short shelf life
) -> Literal["par_driven", "forecast_driven"]:
    """
    Select ordering policy based on SKU characteristics.
    
    Decision Rules:
    - Par-driven: Low volume + high intermittency + (high criticality OR exchange-based)
    - Forecast-driven: High volume OR low intermittency (default)
    
    Args:
        avg_daily_usage: Average daily usage rate
        cv_demand: Coefficient of variation (std/mean) - measures intermittency
        shelf_life_days: Shelf life in days
        moq_units: Minimum order quantity (if None, assume no constraint)
        criticality: "routine" or "critical"
        exchange_cadence_days: Exchange cadence if exchange-based (None if not)
        min_daily_usage_threshold: Below this = low volume
        high_cv_threshold: Above this = high intermittency
        short_shelf_life_threshold: Below this = short shelf life
    
    Returns:
        "par_driven" or "forecast_driven"
    """
    # Calculate demand characteristics
    is_low_volume = avg_daily_usage < min_daily_usage_threshold
    is_high_intermittency = cv_demand > high_cv_threshold
    is_short_shelf_life = shelf_life_days < short_shelf_life_threshold
    is_critical = (criticality == "critical")
    is_exchange_based = (exchange_cadence_days is not None and exchange_cadence_days >= 14)
    
    # Decision logic
    # Regime 1: Par-driven (low-volume, safety-critical, exchange-based)
    use_par_driven = False
    
    if is_exchange_based:
        # Exchange-based replenishment → par-driven
        use_par_driven = True
    elif is_low_volume and is_high_intermittency:
        # Low volume + high intermittency → par-driven
        if is_critical:
            # Critical items: always par-driven for low-volume intermittent
            use_par_driven = True
        elif moq_units and avg_daily_usage * 30 < moq_units:
            # MOQ forces over-ordering for low-volume → par-driven prevents waste
            use_par_driven = True
    elif is_low_volume and is_short_shelf_life:
        # Low volume + short shelf life → par-driven to prevent expiration
        use_par_driven = True
    
    # Regime 2: Forecast-driven (default for high-volume, low-intermittency)
    # If none of the par-driven conditions met, use forecast-driven
    
    return "par_driven" if use_par_driven else "forecast_driven"


def get_policy_metadata(
    avg_daily_usage: float,
    used_units_array,  # Array of daily usage for CV calculation
    shelf_life_days: int,
    moq_units: Optional[int] = None,
    criticality: str = "routine",
    exchange_cadence_days: Optional[int] = None,
    par_cap_enabled: bool = False,
) -> Dict:
    """
    Calculate policy selection metadata and return selected policy.
    
    Returns:
        Dictionary with:
        - policy: "par_driven" or "forecast_driven"
        - reasoning: List of reasons for selection
        - metadata: Demand characteristics (cv, is_low_volume, etc.)
    """
    import numpy as np
    
    # Calculate CV
    std_usage = np.std(used_units_array) if len(used_units_array) > 1 else 0.0
    mean_usage = np.mean(used_units_array) if len(used_units_array) > 0 else avg_daily_usage
    cv_demand = (std_usage / mean_usage) if mean_usage > 0 else 0.0
    
    # Select policy
    policy = select_ordering_policy(
        avg_daily_usage=avg_daily_usage,
        cv_demand=cv_demand,
        shelf_life_days=shelf_life_days,
        moq_units=moq_units,
        criticality=criticality,
        exchange_cadence_days=exchange_cadence_days,
    )
    if policy == "forecast_driven" and par_cap_enabled:
        policy = "forecast_capped"
    
    # Build reasoning
    reasoning = []
    is_low_volume = avg_daily_usage < 5.0
    is_high_intermittency = cv_demand > 1.0
    is_short_shelf_life = shelf_life_days < 180
    is_exchange_based = (exchange_cadence_days is not None and exchange_cadence_days >= 14)
    
    if policy == "par_driven":
        if is_exchange_based:
            reasoning.append("Exchange-based replenishment")
        if is_low_volume and is_high_intermittency:
            reasoning.append("Low volume + high intermittency")
        if is_low_volume and is_short_shelf_life:
            reasoning.append("Low volume + short shelf life")
        if criticality == "critical" and is_low_volume:
            reasoning.append("Critical + low volume")
    else:
        reasoning.append("High volume or low intermittency (default)")
        if policy == "forecast_capped":
            reasoning.append("Forecast-driven capped by par level")
    
    return {
        "policy": policy,
        "reasoning": reasoning,
        "metadata": {
            "avg_daily_usage": float(avg_daily_usage),
            "cv_demand": float(cv_demand),
            "is_low_volume": is_low_volume,
            "is_high_intermittency": is_high_intermittency,
            "is_short_shelf_life": is_short_shelf_life,
            "is_exchange_based": is_exchange_based,
            "criticality": criticality,
        }
    }
