# Code Cart Medication Integration Options

**Purpose**: Document potential approaches for integrating code cart-specific parameters into the simulation framework.

**Source**: Real-world operational guidelines for code cart medications (see `REALISTIC_PARAMETERS_RESEARCH.md` for details)

---

## Key Code Cart Characteristics

1. **Effective shelf life** = Labeled expiry - 60-120 day buffer
2. **Par-driven ordering** (fixed policy, not forecast-based)
3. **Monthly/quarterly cart exchanges** (not weekly)
4. **Case packs/MOQs**: 10-50 units typical
5. **Stochastic lead times**: 7-21 days typical, 30-90+ days during shortages
6. **Realistic expiry target**: 5-25% (vs <5% for general inventory)

---

## Integration Options

### Option A: New Category (Category F: Code Cart)

**Approach**: Add a new demand archetype specifically for code cart medications

**Pros**:
- Clean separation of code cart vs general inventory
- Can have different demand patterns (low-use, burst events)
- Easy to compare code cart vs general inventory results

**Cons**:
- Requires dataset regeneration for all scenarios
- Need to define demand pattern for code cart meds
- More complex category management

**Implementation**:
```yaml
# In realistic_params.yaml
default:
  shelf_life_days:
    F: 300  # 12 months labeled - 60 day buffer = ~10 months effective
  order_cadence_days:
    F: 30  # Monthly cart exchanges
  lead_time_days:
    F: 10  # Median, with stochastic long tail
  # ... other params
```

**Dataset Generation**:
- Add "F" archetype to `generate_synthetic_bank.py`
- Define demand pattern: Low-use with occasional burst events (code cart usage)

---

### Option B: New Scenario (S13: Code Cart Parameters)

**Approach**: Create a scenario that overrides defaults with code cart-specific values

**Pros**:
- No dataset regeneration needed (can reuse existing categories)
- Quick to test without changing core structure
- Easy to compare code cart params vs baseline

**Cons**:
- Doesn't capture par-driven ordering logic (would need code changes)
- May not reflect true code cart demand patterns
- Parameters applied to wrong demand archetypes

**Implementation**:
```yaml
# In sensitivity_scenarios.yaml
scenarios:
  S13:
    description: "Code cart parameters: effective shelf life, monthly exchanges, stochastic lead times"
    shelf_life_days:
      A: 300  # Effective shelf life (labeled - buffer)
      B: 300
      C: 300
      D: 300
      E: 180  # Specialty items keep short shelf life
    order_cadence_days:
      A: 30  # Monthly cart exchanges
      B: 30
      C: 30
      D: 30
      E: 14  # More frequent for emergency items
    lead_time_days:
      A: 10  # Median, would need stochastic implementation
      B: 10
      C: 10
      D: 14
      E: 7
    # ... other overrides
```

---

### Option C: New Config File (`code_cart_params.yaml`)

**Approach**: Separate config file for code cart use cases, with specialized ordering logic

**Pros**:
- Complete separation of concerns
- Can implement par-driven ordering logic
- Can add code cart-specific features (stochastic lead times, pull buffers)
- Doesn't affect existing scenarios

**Cons**:
- Requires code changes to support par-driven ordering
- More complex to maintain multiple config systems
- Need to decide when to use which config

**Implementation**:
```yaml
# ml/config/code_cart_params.yaml
code_cart:
  effective_shelf_life:
    pull_buffer_days: 90  # 60-120 day range
    labeled_expiry_days: 365  # 12 months typical
    effective_days: 275  # labeled - buffer
  
  ordering:
    mode: "par_driven"  # vs "forecast_driven"
    par_level_days: 30  # Maintain 30 days of stock
    exchange_cadence_days: 30  # Monthly exchanges
    case_pack_units: 25  # Typical case pack size
    
  lead_time:
    distribution: "lognormal"  # vs "fixed"
    median_days: 10
    p95_days: 60  # 95th percentile
    
  moq_enabled: true
  moq_units: 25  # Case pack size
  spq_units: 25
```

**Code Changes Needed**:
- Add par-driven ordering logic to `generator.py`
- Add stochastic lead time sampling
- Add pull buffer calculation for effective shelf life

---

### Option D: Hybrid Approach

**Approach**: Use existing categories but add code cart scenario + specialized ordering mode flag

**Pros**:
- Flexible: can test code cart params on any category
- Incremental: add features as needed
- Maintains compatibility with existing scenarios

**Cons**:
- More complex parameter management
- Need to track which scenarios use which mode

**Implementation**:
```yaml
# In sensitivity_scenarios.yaml
scenarios:
  S13:
    description: "Code cart: par-driven ordering, effective shelf life, monthly exchanges"
    ordering_mode: "par_driven"  # New flag
    shelf_life_mode: "effective"  # vs "labeled"
    pull_buffer_days: 90
    # ... other params
```

---

## Recommended Approach

**For Quick Testing**: **Option B (S13 scenario)** - fastest way to test code cart parameters without code changes

**For Full Implementation**: **Option C (separate config)** - allows proper par-driven ordering and stochastic lead times, but requires code changes

**For Research/Comparison**: **Option A (Category F)** - cleanest separation, but requires defining code cart demand patterns

---

## Next Steps (When Ready)

1. **Decide on approach** based on goals (quick test vs full implementation)
2. **If Option B**: Add S13 to `sensitivity_scenarios.yaml` and test
3. **If Option C**: 
   - Create `code_cart_params.yaml`
   - Implement par-driven ordering in `generator.py`
   - Implement stochastic lead time sampling
   - Implement effective shelf life calculation (labeled - buffer)
4. **If Option A**: 
   - Define code cart demand pattern (low-use, burst events)
   - Add Category F to generation pipeline
   - Update all scenarios to include F

---

**Last Updated**: Based on real-world code cart operational guidelines
