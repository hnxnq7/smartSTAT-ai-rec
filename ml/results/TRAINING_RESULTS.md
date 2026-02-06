# ML Training Results - Consolidated Analysis

**Last Updated**: Realistic Parameters Sensitivity Sweep (Round 14)

---

## 🎯 Current Status & Key Findings

### Recent Updates
- **Policy-layer test (capped/hybrid)**: Ran `test_policy_layer.py` for S3/S6/S8/S14_POLICY with `forecast_capped` mode.
  - Stockout means (%), order: forecast / forecast_capped / policy_selected / par_driven

| Scenario | Stockout means (%) |
| --- | --- |
| S3 | 7.38 / 9.03 / 6.26 / 0.00 |
| S6 | 17.26 / 19.76 / 13.72 / 0.00 |
| S8 | 7.38 / 9.03 / 6.26 / 0.00 |
| S14_POLICY | 20.40 / 22.80 / 14.63 / 0.31 |

- **Stockout bug fix**: Inventory arrivals were overwritten each day in `simulate_inventory`, causing false 100% stockouts. Fix applied.
- **S14 (par-driven) revalidation**: Mean stockout **0.19%** (target <2%), max **9.93%** (Category B tail risk).
- **S14_POLICY (auto policy) revalidation**: Mean stockout **18.10%**, max **39.61%**.
- **Policy instrumentation**: Policy selection recorded per SKU in metadata; S14_POLICY mix = **82% forecast-driven / 18% par-driven**.
- **Policy test (S14_POLICY, A–E, n=25)**: forecast-driven stockout **20.40%**, policy-selected **12.93%**, par-driven **0.00%**.

### Major Breakthrough: Realistic Parameters Validation

**Round 14 Results (Realistic Parameters Sensitivity Sweep)**:
- **Best Result**: **S14 (Code Cart with Par-Driven Ordering) achieved 4.46%** expired rate (down from 60.86% baseline, **92.7% reduction**) 🎯
- **Second Best**: S6 achieved 25.42% expired rate (730-day shelf life, 14-day lead time)
- **Key Finding**: Par-driven ordering (maintain fixed par levels) is optimal for code cart medications, achieving <5% expired rate
- **Code Cart Comparison**: S13 (forecast-driven) 40.58% → S14 (par-driven) 4.46% (-36.12 pp improvement)
- **Shelf Life Impact**: Scenarios with 730+ day shelf life achieve ~45-46% expired rate vs 60.86% baseline

**Key Validation**: Using realistic hospital supply chain parameters achieves the <50% expired rate target. For code carts specifically, **par-driven ordering > forecast-driven ordering**, validating that maintaining fixed par levels regardless of forecast prevents over-ordering for low-volume items.

**Primary Driver**: Shelf life is the dominant factor - increasing from 240 days to 730+ days reduces expired rate by 25-35 percentage points. In our current simulator, longer lead times correlate with lower expiry, likely due to indirect effects on ordering behavior; treat this as a second-order effect and validate carefully.

### 📊 Latest Results Summary

| Configuration | Expired Rate | Improvement | Key Parameters |
|--------------|--------------|-------------|----------------|
| **Baseline** (Round 9) | 60.86% | - | 240-day shelf life, 4-day cadence, 99.5% service level |
| **S14** (Code cart, par-driven) | **4.46%** | **-56.40 pp** 🎯 | 300-day effective shelf life, par-driven (30d par), monthly exchanges |
| **S6** (Long lead time) | 25.42% | -35.44 pp | 730-day shelf life, 14-day lead time, weekly cadence |
| **S3** (Full realistic) | 45.82% | -15.04 pp | 730-day shelf life, weekly cadence, 98% service level |
| **S13** (Code cart, forecast) | 40.58% | -20.28 pp | 300-day effective shelf life, forecast-driven, monthly exchanges |

### ✅ System Strengths

1. **Strong Demand Prediction**: Normalized MAE ~0.04-0.05 (excellent accuracy)
2. **Low Stockout Rates**: ~1.09-1.17% (target: <2%)
3. **Robust Inventory Logic**: Multiple reorder triggers, category-aware ordering, adaptive quantities

### 🎯 Key Insight

**Prediction accuracy ≠ Inventory management quality**

The regression model excels at predicting demand (low MSE), but expired rates come from the **inventory simulation parameters**, not prediction errors. Realistic hospital supply chain parameters (especially 2-3 year shelf life for medications) are essential for achieving low expired rates.

---

## Round 14: Realistic Parameters Sensitivity Sweep 🎯

**Status**: ✅ Complete (14 scenarios tested: baseline + S1-S14)  
**Purpose**: Validate that realistic hospital supply chain parameters can achieve expired rates <50% target
**Latest**: S14 (Option C - Par-driven ordering) achieved 4.46% expired rate, validating par-driven approach for code carts

### Research Foundation

**Evidence-Based Parameter Research**: Created comprehensive parameter documentation (`ml/docs/REALISTIC_PARAMETERS_RESEARCH.md`) with:
- **Tier 1 Sources**: FDA, USP, ASHP, NIH/PMC peer-reviewed articles
- **Tier 2 Sources**: Industry reports, major GPO/distributor documentation
- **Assumptions**: Clearly marked where public data unavailable, with conservative priors

**Key Parameter Changes**:
- **Shelf Life**: Increased from 240 days → 730-1095 days (2-3 years, realistic for most medications)
- **Order Cadence**: Changed from 4 days → 7 days (weekly, aligns with hospital practices)
- **Service Level**: Reduced from 99.5% → 98% for routine items (realistic target)
- **Lead Times**: Standardized to 5 days for routine, 14 days for specialty

### Complete Sensitivity Sweep Results

| Scenario | Description | Shelf Life (A-D/E) | Order Cadence | Service Level | Expired Rate | vs Baseline | Key Finding |
|----------|-------------|-------------------|---------------|---------------|--------------|-------------|-------------|
| **baseline** | Round 9 config | 240/180 days | 4 days | 99.5% | **60.86%** | - | Original best |
| **S1** | +1yr shelf life | 365/180 days | 4 days | 99.5% | **57.99%** | -2.87 pp | Shelf life impact |
| **S2** | S1 + weekly cadence | 365/180 days | 7 days | 99.5% | **57.07%** | -3.79 pp | Weekly ordering |
| **S3** | Full realistic (2yr) | 730/180 days | 7 days | 98% | **45.82%** | -15.04 pp | Best realistic |
| **S4** | 3yr shelf life | 1095/180 days | 7 days | 98% | **46.11%** | -14.75 pp | Long shelf life |
| **S5** | Short shelf life | 180/180 days | 3 days | 98% | **68.03%** | +7.17 pp ⚠️ | Worst case |
| **S6** | Long lead time | 730/180 days | 7 days (14d lead) | 98% | **25.42%** | **-35.44 pp** 🎯 | **Best result** |
| **S7** | +MOQ constraints | 730/180 days | 7 days | 98% | **45.64%** | -15.22 pp | MOQ impact |
| **S8** | Lower service (95%) | 730/180 days | 7 days | 95% | **45.30%** | -15.56 pp | Service level |
| **S9** | Optimal realistic | 1095/180 days | 7 days | 98% | **46.16%** | -14.70 pp | Combined optimal |
| **S10** | Category-specific | 730/180 days | 7 days | 98% | **45.43%** | -15.43 pp | Heterogeneous |
| **S11** | Very frequent (3d) | 730/180 days | 3 days | 98% | **45.77%** | -15.09 pp | Frequency test |
| **S12** | Monthly ordering | 1095/180 days | 30 days | 98% | **56.13%** | -4.73 pp | Infrequent |
| **S13** | Code cart params | 300/180 days | 30 days | 99.5% | **40.58%** | -20.28 pp | Code cart (forecast-driven) |
| **S14** | Code cart + par-driven | 300/180 days | 30 days | 99.5% | **4.46%** | **-56.40 pp** 🎯 | **Code cart (par-driven)** |

**Best Performing**: **S14 (4.46% expired rate)** - Code cart with par-driven ordering achieves lowest expired rate 🎯
**Second Best**: **S6 (25.42% expired rate)** - 730-day shelf life with 14-day lead time

**Key Insights**:
- **Shelf life matters most**: Scenarios with 730+ day shelf life (S3, S4, S6-S11) achieve ~45-46% expired rate
- **Lead time impact**: In the current simulator, longer lead times correlate with lower expiry; treat this as a second-order effect and validate carefully.
- **S5 (short shelf life) performs worst**: 68.03% confirms short shelf life is the primary driver of expiration
- **Long shelf life (1095 days) doesn't beat medium (730 days)**: S4 and S9 show similar results to S3, suggesting 2-year shelf life is sufficient for the test period
- **S13 (Code Cart, forecast-driven)**: 40.58% expired rate with 300-day effective shelf life and monthly exchanges. Category B (low-volume) worst at 69.25%, highlighting challenge of case packs + infrequent exchanges for slow movers
- **S14 (Code Cart, par-driven)**: **4.46% expired rate** - Par-driven ordering dramatically improves results! Category B reduced from 69.25% to 29.47%, Categories A/C/D near 0%, Category E at 15.72%

*Full results available in `ml/data/sensitivity_sweep_results.csv`*

### Key Findings

1. **Shelf Life is Primary Driver** ✅
   - **S1** (365 days): -13.81 pp reduction from baseline
   - **S9** (1095 days): -51.21 pp reduction from baseline
   - **Conclusion**: Increasing shelf life from 240 to 1095 days reduces expired rate by **86.6%**

2. **Category-Specific Impact**:
   - **Categories A-D** (1095-day shelf life): **0.00% expired rate** in S9
   - **Category E** (180-day shelf life): **78.24% expired rate** in S9
   - **Insight**: Short shelf-life specialty items remain challenging even with optimized parameters

3. **Validated Hypothesis**:
   - ✅ **Realistic parameters enable <50% expired rate** (S9 achieved 7.89%)
   - ✅ **Parameter realism > ordering logic optimization**
   - ✅ **Shelf life mismatch was root cause**

### S9 Scenario (Optimal Realistic Parameters)

**Configuration**:
- Shelf life: 1095 days (3 years) for categories A-D, 180 days for E
- Order cadence: 7 days (weekly) for A/C/D, 14 days for B, 3 days for E
- Lead time: 5 days (routine), 2 days (emergency E)
- Service level: 98% (routine), 99.5% (critical E)

**Results**:
- **Overall Expired Rate**: 7.89% (down from 59.10% baseline, **86.6% reduction**)
- **Categories A-D**: 0.00% expired rate (no expiration with 3-year shelf life)
- **Category E**: 78.24% expired rate (short 180-day shelf life for specialty items)
- **Total Expired Units**: 1.24M (down from 20.81M baseline, **94.0% reduction**)

### Files & Configuration

- **Research Documentation**: `ml/docs/REALISTIC_PARAMETERS_RESEARCH.md`
- **Base Config**: `ml/config/realistic_params.yaml`
- **Scenarios**: `ml/config/sensitivity_scenarios.yaml`
- **Analysis Script**: `ml/scripts/analyze_scenario_expired_rate.py`
- **Generation**: Use `--params ml/config/realistic_params.yaml --scenario S9`

---

### Best Performing Scenarios

**S14 (Code Cart with Par-Driven Ordering) - Best Result: 4.46% expired rate** 🎯
- **Configuration**: 300-day effective shelf life, par-driven ordering (30-day par level), monthly exchanges, stochastic lead times
- **Key Insight**: Par-driven ordering maintains fixed par levels regardless of forecast, preventing over-ordering for low-volume items
- **Improvement**: -56.40 pp from baseline (92.7% reduction), -36.12 pp from S13 (forecast-driven code cart)
- **Category Breakdown**: A/C/D near 0%, B at 29.47% (down from 69.25% in S13), E at 15.72% (down from 58.70% in S13)

**S6 (Long Lead Time) - 25.42% expired rate**
- **Configuration**: 730-day shelf life, 14-day lead time (routine), weekly cadence, 98% service level
- **Key Insight**: In the current simulator, longer lead times correlate with lower expiry, likely due to indirect effects on ordering behavior; treat as a second-order effect and validate carefully.
- **Improvement**: -35.44 pp from baseline (58.2% reduction)

**S3 (Full Realistic) - 45.82% expired rate**
- **Configuration**: 730-day shelf life, 5-day lead time, weekly cadence, 98% service level
- **Key Insight**: Balanced realistic parameters achieve <50% target
- **Improvement**: -15.04 pp from baseline (24.7% reduction)

**Interpretation**:
- **Par-driven ordering is highly effective**: S14's 4.46% validates that maintaining fixed par levels (vs forecast-driven) is optimal for code carts
- **Shelf life impact**: 730-day shelf life enables ~45-46% expired rate across multiple scenarios
- **Lead time surprise**: Longer lead times (S6) perform better than expected in the current simulator; likely an indirect ordering effect that needs validation.
- **Short shelf life worst**: S5 (180 days) at 68.03% confirms shelf life is the primary driver
- **Realistic parameters work**: Multiple scenarios achieve <50% target, validating the parameter realism approach

### S14 Deploy Readiness Checklist

**Horizon Validation** ✅
- Dataset period: 2023-2025 (3 years), Test: 2025 (1 year)
- Effective shelf life: 300 days (12mo labeled - 90d buffer)
- **Analysis**: Test period (365 days) > Effective shelf life (300 days) = items CAN expire
- **Conclusion**: 4.46% expired rate is meaningful, not guaranteed low by horizon
- Monthly exchanges (12/year) allow multiple order cycles
- Par-driven ordering prevents over-ordering vs forecast-driven (S13: 40.58% → S14: 4.46%)

**Stockout Rate Validation** ⚠️ **TAIL RISK REMAINS**
- **Fix Applied**: Inventory arrivals were being overwritten; corrected in `simulate_inventory`.
- **S14 Results (post-fix)**: Mean **0.19%**, median **0.00%**, max **9.93%** (Category B tail).
- **Interpretation**: Average performance meets target, but worst-case tail needs mitigation (low-volume SKUs).

**Robustness Tests** ✅ (Updated)
- Lead time +20%/+50%: Stockout ~0% (A/B) in quick tests.
- Cadence ±1 week: Stockout remains low (A/B), with small spikes in B.

**Deployment Status**: ⚠️ **CONDITIONALLY OK** - Mean stockout meets target, tail risk remains.

---

### Policy Layer Implementation (Phase 2: General Inventory)

**Status**: ✅ Implemented, ⚠️ Stockout still high in S14_POLICY (mean 18.10%)

**Implementation**:
- Created `policy_selector.py`: Decision rules for par-driven vs forecast-driven
- Added `ordering_mode="auto"` option to generator with `policy_auto_select=True`
- Policy selection based on: demand rate, CV (intermittency), shelf life, MOQ, criticality, exchange cadence

**Decision Rules**:
- **Par-driven**: Low volume + high intermittency + (critical OR exchange-based)
- **Forecast-driven**: High volume OR low intermittency (default)

**Test Results**:
- **S14_POLICY (A–E, n=25)**: forecast-driven stockout **20.40%**, policy-selected **12.93%**, par-driven **0.00%**.
- **Selection Mix (S14_POLICY generation)**: 82% forecast-driven / 18% par-driven (B mostly par-driven).

**Note**: Policy auto-selection improves stockout vs forecast-only but still worse than par-driven for code carts.

### Next Steps

1. **Reduce tail stockout (B/E)**: Increase par coverage or tighten cadence; relax MOQ/SPQ where needed.
2. **Complete sensitivity sweep**: Generate and analyze remaining scenarios (S2-S8, S10-S12).
3. **Category E optimization**: Strategies for short-shelf-life specialty items.
4. **Full training**: Train models on S14 configuration once tail stockout risk is acceptable.

### Files & Configuration

- **Research Documentation**: `ml/docs/REALISTIC_PARAMETERS_RESEARCH.md`
- **Base Config**: `ml/config/realistic_params.yaml`
- **Scenarios**: `ml/config/sensitivity_scenarios.yaml`
- **Analysis Script**: `ml/scripts/analyze_scenario_expired_rate.py`
- **Generation**: Use `--params ml/config/realistic_params.yaml --scenario S9`

---

## Round 9: Priority 3 - Category-Specific Order Multipliers (Optimal) ⭐

**Status**: ✅ Complete (All 550 datasets regenerated, trained, and evaluated)  
**Data Directory**: `ml/data/synthetic_bank/`  
**Model Directory**: `ml/models_priority3_all/`  
**Results CSV**: `ml/results/results_priority3_all.csv`

### Key Improvements

**Priority 3: Category-Specific Order Multipliers**

Order quantities are now adjusted by category based on demand pattern characteristics:
- **Category A (Stable demand)**: 1.0x multiplier - order exactly what's needed
- **Category B (Low volume)**: 0.8x multiplier - smaller orders, more frequent (reduces waste)
- **Category C (Weekly pattern)**: 1.0x multiplier - order weekly amounts
- **Category D (Trending)**: 1.1x multiplier - slightly more for trends
- **Category E (Burst events)**: 1.2x multiplier - need buffer for spikes

**Rationale**: Different demand patterns require different ordering strategies. Category B (low volume) benefits from smaller, more frequent orders to reduce waste, while Category E (burst events) needs larger buffers.

### Performance Summary

| Metric | Round 8 (Priority 1+2) | Round 9 (Priority 3) | Change |
|--------|------------------------|----------------------|--------|
| **Stockout Rate (Mean)** | 1.18% | **1.09%** | **-0.09 pp** ✅ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change ✅ |
| **Expired Rate (Mean)** | 76.56% | **70.22%** | **-6.34 pp** 🎉 |
| **Expired Rate (Median)** | 74.94% | **74.32%** | **-0.62 pp** ✅ |
| **Expired Units (Total)** | 26.5M | 27.6M | +1.1M (+4.2%) |
| **Normalized MAE (Median)** | 0.138 | 0.105 | **-23.9%** ✅ |

### Performance by Category

#### Expired Rate by Category

| Category | Round 8 | Round 9 | Change | Multiplier |
|----------|---------|---------|--------|------------|
| **A** | 76.41% | **68.52%** | **-7.89 pp** ✅ | 1.0x |
| **B** | 75.49% | **69.42%** | **-6.07 pp** ✅ | **0.8x** (reduced orders) |
| **C** | 75.87% | **68.98%** | **-6.89 pp** ✅ | 1.0x |
| **D** | 78.37% | **72.38%** | **-5.99 pp** ✅ | 1.1x |
| **E** | 76.68% | **71.81%** | **-4.87 pp** ✅ | 1.2x |

#### Stockout Rate by Category

| Category | Round 8 | Round 9 | Change |
|----------|---------|---------|--------|
| **A** | 1.14% | **1.08%** | **-0.06 pp** ✅ |
| **B** | 1.20% | **1.10%** | **-0.10 pp** ✅ |
| **C** | 1.19% | **1.08%** | **-0.11 pp** ✅ |
| **D** | 1.18% | **1.10%** | **-0.08 pp** ✅ |
| **E** | 1.17% | **1.08%** | **-0.09 pp** ✅ |

### Key Findings

**Priority 3 Impact Analysis**:
- **Expired Rate**: **6.34 pp reduction** - category-specific multipliers successfully reduced waste across all categories
- **Stockout Rate**: **0.09 pp improvement** - better ordering strategy also improved stockout prevention
- **Category B Benefit**: 0.8x multiplier (smaller orders) led to **6.07 pp expired rate reduction** - validating the strategy
- **All Categories Improved**: Every category saw expired rate reduction, demonstrating effectiveness

**Why It Works**:
1. **Category B (Low Volume)**: 0.8x multiplier prevents over-ordering for sporadic demand
2. **Category E (Burst Events)**: 1.2x multiplier ensures adequate buffer without excessive waste
3. **Category-Specific Optimization**: Tailored ordering strategies match demand characteristics

**Overall Progress from Round 5 → Round 9**:
- **Expired Rate: 97.58% → 70.22% (27.4 pp reduction, 28.0% improvement)** 🎉
- **Expired Units: 321.5M → 27.6M (91.4% reduction!)** 🎉
- **Stockout Rate: 1.17% → 1.09% (6.8% improvement)** ✅

---

## Round 10: Priority 4 - Reduced Order Cap + Consume Inventory First ⚠️

**Status**: ✅ Complete (All 500 datasets regenerated, trained, and evaluated)  
**Data Directory**: `ml/data/synthetic_bank/`  
**Model Directory**: `ml/models_priority4_all/`  
**Results CSV**: `ml/results/results_priority4_all.csv`

### Key Changes

**Priority 4 Phase 1: Two Strategies Implemented**

1. **Strategy 1: Reduce Maximum Order Days Supply**
   - Reduced from 21 days to 14 days supply cap
   - More aggressive cap to prevent over-ordering

2. **Strategy 2: Consume Inventory Before Reordering**
   - Delay orders if current inventory can cover 12+ days of demand
   - Increase reorder point threshold by 20% when inventory is sufficient

### Performance Summary

| Metric | Round 9 (Priority 3) | Round 10 (Priority 4) | Change |
|--------|----------------------|----------------------|--------|
| **Stockout Rate (Mean)** | 1.09% | 1.18% | +0.09 pp ⚠️ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change ✅ |
| **Expired Rate (Mean)** | **70.22%** | 76.74% | **+6.52 pp** ⚠️ |
| **Expired Rate (Median)** | 74.32% | 74.97% | +0.65 pp ⚠️ |
| **Expired Units (Total)** | 27.6M | 27.5M | -0.1M (-0.4%) ✅ |
| **Normalized MAE (Median)** | 0.105 | 0.112 | +6.7% ⚠️ |

### Performance by Category

#### Expired Rate by Category

| Category | Round 9 | Round 10 | Change |
|----------|---------|----------|--------|
| **A** | 68.52% | 76.13% | +7.61 pp ⚠️ |
| **B** | 69.42% | 73.09% | +3.67 pp ⚠️ |
| **C** | 68.98% | 75.18% | +6.20 pp ⚠️ |
| **D** | 72.38% | 80.88% | +8.50 pp ⚠️ |
| **E** | 71.81% | 78.44% | +6.63 pp ⚠️ |

#### Stockout Rate by Category

| Category | Round 9 | Round 10 | Change |
|----------|---------|----------|--------|
| **A** | 1.08% | 1.17% | +0.09 pp ⚠️ |
| **B** | 1.10% | 1.17% | +0.07 pp ⚠️ |
| **C** | 1.08% | 1.21% | +0.13 pp ⚠️ |
| **D** | 1.10% | 1.13% | +0.03 pp |
| **E** | 1.08% | 1.20% | +0.12 pp ⚠️ |

### Key Findings

**Priority 4 Impact Analysis**:
- **Expired Rate**: **+6.52 pp increase** - strategies had opposite effect than expected
- **Stockout Rate**: **+0.09 pp increase** - slight degradation
- **All Categories Affected**: Every category saw expired rate increase

**Why It Didn't Work**:
1. **Reduced Order Cap (14 days)**: May cause more frequent smaller orders, leading to:
   - More order arrivals (more inventory turnover)
   - Potential for more waste if orders arrive too frequently
   - Less efficient ordering patterns

2. **Consume Inventory First (12+ days delay)**: May cause:
   - Delayed reordering when inventory is high
   - Potential stockouts when delayed orders don't arrive in time
   - Catch-up orders that are larger than optimal

3. **Interaction Effects**: The two strategies may work against each other:
   - Smaller orders (14-day cap) + delayed reordering = potential gaps
   - When orders are delayed, larger catch-up orders may be needed

**Lessons Learned**:
- **Round 9 (Priority 3) was optimal** - category-specific multipliers worked best
- **Aggressive reductions** (14-day cap) may be too restrictive
- **Delay strategies** need careful tuning to avoid stockouts
- **Strategy interactions** must be considered when combining approaches

**Recommendation**: Revert to Round 9 configuration (Priority 3) or refine Priority 4 strategies with:
- Less aggressive cap (16-18 days instead of 14)
- Shorter delay threshold (8-10 days instead of 12)
- Category-specific delay thresholds

---

## Round 11: Phase 1 Strategies - Under 50% Target ⚠️

**Status**: ✅ Complete (All 500 datasets regenerated, trained, and evaluated)  
**Data Directory**: `ml/data/synthetic_bank/`  
**Model Directory**: `ml/models_under50_all/`  
**Results CSV**: `ml/results/results_under50_all.csv`

### Key Changes

**Phase 1 Strategies (Target: <50% Expired Rate)**

1. **Strategy 1: Shelf-Life Aware Ordering**
   - Reduce orders by 50% when inventory >25% of shelf life
   - Stop orders entirely when inventory >40% of shelf life
   - Prevent ordering when inventory is aging

2. **Strategy 2: Category-Specific Order Caps**
   - A: 12 days, B: 10 days, C: 12 days, D: 16 days, E: 18 days
   - More aggressive caps than Round 10 (which used 14 for all)

3. **Strategy 3: Reduced Order Buffers**
   - Category-specific: A: 2%, B: 1%, C: 2%, D: 5%, E: 8%
   - Down from 10% uniform buffer

4. **Strategy 4: Inventory Age-Based Reorder Points**
   - Raise reorder point when inventory is fresh (<15% of shelf life)
   - Lower reorder point when inventory is aging (>30% of shelf life)

### Performance Summary

| Metric | Round 9 (Priority 3) | Round 11 (Phase 1) | Change |
|--------|----------------------|---------------------|--------|
| **Stockout Rate (Mean)** | 1.09% | 1.20% | +0.11 pp ⚠️ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change ✅ |
| **Expired Rate (Mean)** | **70.22%** | 75.53% | **+5.31 pp** ⚠️ |
| **Expired Rate (Median)** | 74.32% | 74.40% | +0.08 pp ⚠️ |
| **Expired Units (Total)** | 27.6M | 26.4M | -1.3M (-4.6%) ✅ |
| **Normalized MAE (Median)** | 0.105 | 0.119 | +13.3% ⚠️ |

**Target Achievement**: ❌ **Failed to achieve <50% expired rate**
- Mean expired rate: 75.53% (target was <50%)
- 0 datasets achieved <50% expired rate
- 79.8% of datasets still have ≥70% expired rate

### Performance by Category

#### Expired Rate by Category

| Category | Round 9 | Round 11 | Change |
|----------|---------|----------|--------|
| **A** | 68.52% | 73.97% | +5.45 pp ⚠️ |
| **B** | 69.42% | 71.83% | +2.41 pp ⚠️ |
| **C** | 68.98% | 74.40% | +5.42 pp ⚠️ |
| **D** | 72.38% | 79.22% | +6.84 pp ⚠️ |
| **E** | 71.81% | 78.25% | +6.44 pp ⚠️ |

#### Stockout Rate by Category

| Category | Round 9 | Round 11 | Change |
|----------|---------|----------|--------|
| **A** | 1.08% | 1.21% | +0.13 pp ⚠️ |
| **B** | 1.10% | 1.18% | +0.08 pp ⚠️ |
| **C** | 1.08% | 1.20% | +0.12 pp ⚠️ |
| **D** | 1.10% | 1.22% | +0.12 pp ⚠️ |
| **E** | 1.08% | 1.19% | +0.11 pp ⚠️ |

### Key Findings

**Phase 1 Impact Analysis**:
- **Expired Rate**: **+5.31 pp increase** - strategies had opposite effect than expected
- **Stockout Rate**: **+0.11 pp increase** - slight degradation
- **All Categories Affected**: Every category saw expired rate increase

**Why It Didn't Work**:
1. **Shelf-Life Aware Ordering**: Stopping/reducing orders when inventory is aging may cause:
   - Stockouts due to delayed reordering
   - Catch-up orders that are larger and more wasteful
   - Timing issues where orders arrive too late

2. **Category-Specific Caps**: The 10-18 day caps may still allow too much inventory accumulation:
   - Even 10 days (Category B) may be too high for low-volume scenarios
   - Caps interact poorly with shelf-life logic

3. **Reduced Buffers**: 1-8% buffers may be too tight:
   - Insufficient safety margin leads to stockouts
   - Stockouts trigger larger catch-up orders

4. **Strategy Interactions**: Multiple aggressive strategies compound issues:
   - Shelf-life delays + reduced buffers + tight caps = timing mismatches
   - Orders arrive too late or too early, causing inventory accumulation

**Critical Insight**: 
- **Round 9 (Priority 3) remains optimal** with 70.22% expired rate
- Aggressive waste-reduction strategies consistently backfire
- **The 70.22% baseline may be near the theoretical limit** for this data structure
- To achieve <50%, we may need fundamental changes to data generation parameters (shelf life, demand patterns, etc.) rather than just ordering logic

**Recommendation**: 
- **Stick with Round 9 configuration** for production
- <50% target may require changes to underlying data assumptions (longer shelf life, different demand patterns)
- Or accept that 70% expired rate is optimal given current constraints

---

## Round 13: FEFO (First-Expiry-First-Out) Consumption ⚠️

**Status**: ✅ Complete (All 500 datasets regenerated, trained, and evaluated)  
**Data Directory**: `ml/data/synthetic_bank/`  
**Model Directory**: `ml/models_fefo_all/`  
**Results CSV**: `ml/results/results_fefo_all.csv`

### Key Changes

**FEFO (First-Expiry-First-Out) Implementation**

Changed consumption logic from FIFO to FEFO:
- **Before (FIFO)**: Sorted batches by `arrival_date` - consumed oldest batches first
- **After (FEFO)**: Sorts batches by `expiry_date` - consumes batches closest to expiration first

**Rationale**: 
- FEFO prioritizes items that will expire soon, reducing waste
- More realistic - hospitals often use FEFO in practice
- Expected to reduce expired rates by 5-15 percentage points

### Performance Summary

| Metric | Round 9 (FIFO) | Round 13 (FEFO) | Change |
|--------|----------------|-----------------|--------|
| **Stockout Rate (Mean)** | 1.09% | 1.17% | +0.08 pp ⚠️ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change ✅ |
| **Expired Rate (Mean)** | **70.22%** | 75.74% | **+5.52 pp** ⚠️ |
| **Expired Rate (Median)** | 74.32% | 74.57% | +0.25 pp ⚠️ |
| **Expired Units (Total)** | 27.6M | 26.5M | -1.2M (-4.3%) ✅ |
| **Normalized MAE (Median)** | 0.105 | 0.118 | +12.4% ⚠️ |

**Target Achievement**: ❌ **Failed - Expired rate increased**

### Performance by Category

#### Expired Rate by Category

| Category | Round 9 (FIFO) | Round 13 (FEFO) | Change |
|----------|----------------|-----------------|--------|
| **A** | 68.52% | 74.13% | +5.61 pp ⚠️ |
| **B** | 69.42% | 71.40% | +1.98 pp ⚠️ |
| **C** | 68.98% | 75.09% | +6.11 pp ⚠️ |
| **D** | 72.38% | 79.56% | +7.18 pp ⚠️ |
| **E** | 71.81% | 78.50% | +6.69 pp ⚠️ |

#### Stockout Rate by Category

| Category | Round 9 (FIFO) | Round 13 (FEFO) | Change |
|----------|----------------|-----------------|--------|
| **A** | 1.08% | 1.19% | +0.11 pp ⚠️ |
| **B** | 1.10% | 1.18% | +0.08 pp ⚠️ |
| **C** | 1.08% | 1.17% | +0.09 pp ⚠️ |
| **D** | 1.10% | 1.17% | +0.07 pp ⚠️ |
| **E** | 1.08% | 1.17% | +0.09 pp ⚠️ |

### Key Findings

**FEFO Impact Analysis**:
- **Expired Rate**: **+5.52 pp increase** - opposite of expected effect
- **Stockout Rate**: **+0.08 pp increase** - slight degradation
- **All Categories Affected**: Every category saw expired rate increase

**Why FEFO Didn't Help**:

1. **Consumption Pattern Change**:
   - FEFO consumes items closest to expiration first
   - This changes which batches are consumed, but doesn't change total inventory levels
   - The fundamental problem (over-ordering) remains

2. **Ordering Logic Unchanged**:
   - FEFO only affects consumption, not ordering decisions
   - Orders still arrive too frequently (every ~4 days)
   - Over-ordering continues, causing expiration

3. **Inventory Dynamics**:
   - FEFO might actually make ordering decisions worse:
     - By consuming expiring items first, inventory levels may drop faster
     - This could trigger more frequent reordering
     - Creates a feedback loop that increases ordering frequency

4. **Fundamental Issue Remains**:
   - The root cause (order frequency vs shelf life mismatch) is unchanged
   - Consumption method (FIFO vs FEFO) can't fix structural ordering problems
   - 70% expired rate is driven by over-ordering, not consumption pattern

**Critical Insight**: 
- **FIFO vs FEFO doesn't matter when ordering is the problem**
- Consumption optimization can't overcome structural ordering issues
- **Round 9 (FIFO) remains optimal** - the consumption pattern wasn't the issue

**Recommendation**: 
- **Revert to Round 9 (FIFO) configuration**
- Consumption method (FIFO/FEFO) is not the limiting factor
- Focus on fixing ordering frequency and initial stock parameters instead

---

## Round 8: Priority 1 + Priority 2 - Dynamic Safety Stock

**Status**: ✅ Complete (All 500 datasets regenerated, trained, and re-evaluated)  
**Data Directory**: `ml/data/synthetic_bank_priority2/`  
**Model Directory**: `ml/models_priority2_all/`  
**Results CSV**: `ml/results/results_priority2_all_reevaluated.csv`

### Key Improvements

**Priority 1 (from Round 7) + Priority 2 (Dynamic Safety Stock)**:

1. **Priority 1**: Adaptive order quantities + Inventory-aware ordering (from Round 7)
2. **Priority 2: Dynamic Safety Stock Reduction**:
   - Tracks recent stockout performance (last 30 days)
   - Adjusts Z-score (service level) based on stockout rate:
     - < 0.5% stockout → Z = 2.0 (95% service level, down from 99.5%)
     - < 1.0% stockout → Z = 2.33 (99% service level)
     - ≥ 1.0% stockout → Z = 2.576 (99.5% service level, default)
   - Reduces safety stock when stockouts are rare, preventing over-inventory

### Performance Summary

| Metric | Round 7 (Priority 1) | Round 8 (Priority 1+2) | Change |
|--------|---------------------|------------------------|--------|
| **Stockout Rate (Mean)** | 1.18% | 1.18% | No change ✅ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change ✅ |
| **Expired Rate (Mean)** | 76.44% | 76.56% | +0.12 pp |
| **Expired Rate (Median)** | 74.85% | 74.94% | +0.09 pp |
| **Expired Units (Total)** | 26.5M | 26.5M | -0.03M (0.1%) |

### Performance by Category

#### Expired Rate by Category

| Category | Round 7 | Round 8 | Change |
|----------|---------|---------|--------|
| **A** | 75.37% | 76.41% | +1.04% ⚠️ |
| **B** | 74.86% | 75.49% | +0.63% ⚠️ |
| **C** | 76.07% | 75.87% | -0.20% ✅ |
| **D** | 78.55% | 78.37% | -0.18% ✅ |
| **E** | 77.35% | 76.68% | -0.67% ✅ |

#### Stockout Rate by Category

| Category | Round 7 | Round 8 | Change |
|----------|---------|---------|--------|
| **A** | 1.21% | 1.14% | -0.07% ✅ |
| **B** | 1.23% | 1.20% | -0.02% ✅ |
| **C** | 1.17% | 1.19% | +0.02% |
| **D** | 1.17% | 1.18% | +0.01% |
| **E** | 1.12% | 1.17% | +0.05% |

### Key Findings

**Priority 2 Impact Analysis**:
- **Expired Rate**: Slight increase (+0.12 pp) - dynamic safety stock adjustment had minimal impact
- **Stockout Rate**: Maintained at 1.18% - no degradation
- **Mixed Results by Category**: Some categories improved (C, D, E), others slightly worse (A, B)

**Why Limited Impact?**
1. **Adaptive nature**: Dynamic adjustment requires 7+ days of history to take effect
2. **Already optimized**: Priority 1 already reduced waste significantly, less room for improvement
3. **Conservatism**: System maintains high service levels when stockouts occur, preventing further reduction

**Conclusion**: Priority 2 maintains performance while providing adaptive safety stock. The slight expired rate increase may be due to normal variance or the conservative nature of the adjustment logic. Stockout rates remain stable across all categories.

### Overall Progress from Round 5 → Round 8

| Metric | Round 5 | Round 8 | Total Improvement |
|--------|---------|---------|-------------------|
| **Expired Rate** | 97.58% | 76.56% | **-21.02 pp (21.5% reduction)** 🎉 |
| **Expired Units** | 321.5M | 26.5M | **-294.9M (91.7% reduction)** 🎉 |
| **Stockout Rate** | 1.17% | 1.18% | Maintained ✅ |

---

## Round 7: Priority 1 in Data Generation - Massive Waste Reduction

**Status**: ✅ Complete (All 500 datasets regenerated, trained, and re-evaluated)  
**Data Directory**: `ml/data/synthetic_bank_priority1/`  
**Model Directory**: `ml/models_priority1_all/`  
**Results CSV**: `ml/results/results_priority1_all_reevaluated.csv`

### Key Improvements

**Priority 1 Solutions Implemented in Data Generation** (this is the key difference from Round 6):

1. **Adaptive Order Quantities in Data Generation**:
   - Orders based on **recent consumption** (last 7-14 days) instead of fixed 30-45 day multipliers
   - Caps order size at 21 days supply maximum
   - Adapts to actual consumption patterns during data generation

2. **Inventory-Aware Ordering in Data Generation**:
   - Checks total available inventory (current + pending orders) before placing new orders
   - Only orders if total available < projected demand × safety factor (1.2)
   - Prevents redundant over-ordering during data generation

**Critical Difference**: Round 6 implemented Priority 1 in evaluation only (so expired rates came from old data). Round 7 implemented Priority 1 in **data generation itself**, so expired units are calculated with the improved logic.

### Performance Summary

| Metric | Round 5 | Round 7 | Change | Improvement |
|--------|---------|---------|--------|-------------|
| **Stockout Rate (Mean)** | 1.17% | 1.18% | +0.01% | Maintained ✅ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change | Maintained ✅ |
| **Expired Rate (Mean)** | 97.58% | **76.44%** | **-21.14 pp** | **21.7% reduction** 🎉 |
| **Expired Rate (Median)** | 97.45% | **74.85%** | **-22.60 pp** | **23.2% reduction** 🎉 |
| **Expired Units (Total)** | 321.5M | **26.5M** | **-294.9M** | **91.7% reduction** 🎉 |

### Performance by Category

#### Expired Rate by Category

| Category | Round 5 | Round 7 | Improvement |
|----------|---------|---------|-------------|
| **A** | 97.48% | 75.37% | -22.11 pp ✅ |
| **B** | 97.44% | 74.86% | -22.58 pp ✅ |
| **C** | 97.48% | 76.07% | -21.41 pp ✅ |
| **D** | 98.01% | 78.55% | -19.46 pp ✅ |
| **E** | 97.48% | 77.35% | -20.14 pp ✅ |

#### Stockout Rate by Category

| Category | Round 5 | Round 7 | Change |
|----------|---------|---------|--------|
| **A** | 1.21% | 1.21% | No change ✅ |
| **B** | 1.32% | 1.23% | -0.09% ✅ |
| **C** | 1.17% | 1.17% | No change ✅ |
| **D** | 0.85% | 1.17% | +0.32% ⚠️ |
| **E** | 1.26% | 1.12% | -0.14% ✅ |

### Key Achievements

1. **Massive Waste Reduction**: Expired rate reduced from 97.6% → 76.4% (21.1 percentage points)
2. **Huge Unit Savings**: Expired units reduced from 321.5M → 26.5M (91.7% reduction, 294.9M units saved)
3. **Stockout Rates Maintained**: Mean stockout rate remains at 1.18% (slight increase of 0.01%)
4. **Category D Note**: Slight stockout increase (0.85% → 1.17%) but still excellent, with expired rate improvement

### Impact Analysis

**Before (Round 5)**:
- For every 1 unit used, ~38 units expired
- Total waste: 321.5 million units
- Waste efficiency: 38x

**After (Round 7)**:
- For every 1 unit used, ~3.2 units expire (estimate based on expired rate)
- Total waste: 26.5 million units
- Waste efficiency: ~3.2x (estimated, 92% improvement)

**Net Benefit**: 
- Saved **294.9 million units** from expiring
- Reduced expired rate by **21.1 percentage points**
- Maintained low stockout rates (~1.18%)

### Conclusion

**Priority 1 implementation in data generation was highly successful!** We achieved:
- ✅ **91.7% reduction in expired units** (294.9M units saved)
- ✅ **21.7% reduction in expired rate** (97.6% → 76.4%)
- ✅ **Maintained stockout rates** at ~1.18%

The adaptive ordering logic effectively reduces over-ordering while maintaining sufficient inventory to prevent stockouts. Category D shows a slight stockout increase but remains excellent, and all categories show significant expired rate improvements.

---

## Round 6: Priority 1 Waste Reduction - Adaptive Ordering (Evaluation Only)

**Status**: ✅ Complete (All 500 datasets re-evaluated)  
**Results CSV**: `ml/results/results_priority1_waste_reduction.csv`

### Key Improvements

**Priority 1 Solutions Implemented**:

1. **Adaptive Order Quantities** (Solution 1):
   - Order quantities based on **recent consumption** (last 7-14 days) instead of fixed multipliers
   - Caps order size at 21 days supply maximum
   - Adapts to actual consumption patterns

2. **Inventory-Aware Ordering** (Solution 2):
   - Checks total available inventory (current + pending orders) before placing new orders
   - Only orders if total available < projected demand × safety factor
   - Prevents redundant over-ordering

### Performance Summary

| Metric | Round 5 | Round 6 | Change |
|--------|---------|---------|--------|
| **Stockout Rate (Mean)** | 1.17% | 1.13% | -0.04% ✅ |
| **Stockout Rate (Median)** | 1.14% | 1.14% | No change |
| **Expired Rate (Mean)** | 97.58% | 97.58% | No change* |

**Important Finding**: Expired rates did not change because they are **pre-computed in the synthetic data generation phase**, not calculated by our evaluation simulation. Our evaluation simulation uses the `expired_units` data from the test datasets, which were generated with the original ordering logic.

**To Actually Reduce Expired Rates**: We need to modify the data generation logic in `ml/data_generation/generator.py` where inventory simulation happens during dataset creation. The Priority 1 solutions improve our evaluation ordering logic, but the expired units in the data were already calculated with the old logic.

### Stockout Performance by Category

| Category | Stockout Rate | Status |
|----------|--------------|--------|
| A | 1.21% | ✅ Maintained |
| B | 1.32% | ✅ Maintained |
| C | 1.17% | ✅ Maintained |
| D | **0.85%** | ✅ Best |
| E | 1.26% | ✅ Maintained |

**Key Achievement**: Stockout rate slightly improved (1.17% → 1.13%) while maintaining low levels across all categories.

### Next Steps for Waste Reduction

To reduce expired rates, we need to:
1. **Regenerate datasets** with improved ordering logic in `generator.py`
2. **Apply Priority 1 solutions** to data generation (adaptive quantities + inventory-aware ordering)
3. **Retrain models** on regenerated datasets
4. **Re-evaluate** with new data

**Expected Impact**: Reduce expired rate from 97.6% → 85-90% when datasets are regenerated with improved ordering logic.

---

## Round 5: Improved Inventory Simulation - Zero Stockout Strategies

**Status**: ✅ Complete (All 500 datasets re-evaluated)  
**Results CSV**: `ml/results/results_improved_simulation.csv`

### Key Improvements

1. **95th Percentile Reorder Points** (was 75th)
2. **Service Level Targeting (99.5%)** with Z-score safety stock
3. **Variance-Aware Safety Stock** (accounts for demand uncertainty)
4. **Multiple Reorder Triggers** (3 triggers: look-ahead, percentile-based, early warning)
5. **Uncertainty-Adjusted Order Quantities**

### Performance Summary

| Category | Stockout Rate | Expired Rate | Waste Efficiency | Status |
|----------|--------------|--------------|------------------|--------|
| A | 1.21% | 97.48% | 39x | ✅ Good |
| B | 1.32% | 97.44% | 38x | ✅ Good |
| C | 1.17% | 97.48% | 39x | ✅ Good |
| D | **0.85%** | 98.01% | 43x | ✅ Best stockout |
| E | 1.26% | 97.48% | 39x | ✅ Good |

**Overall**: Mean stockout 1.17%, Median 1.14% | Mean expired rate 97.58% | Total waste: 321.5M units

### Stockout Improvements

- Mean stockout: **1.25% → 1.17%** (-6.4%)
- Max stockout: **4.56% → 3.42%** (-25%)
- High-stockout datasets: **48.8% average reduction**

### Waste Analysis

**Problem**: Expired rate ~97.6% (97% of units expire, only 3% used)

**Root Causes**:
1. Over-ordering due to conservative safety stock
2. Fixed order quantities don't adapt to consumption patterns
3. Shelf life (180-240 days) relative to demand patterns

**Solutions** (see recommendations below):
- Reduce safety stock when stockouts are rare
- Optimize order quantities based on actual consumption
- Implement dynamic ordering that considers current inventory

---

## Previous Rounds (Summary)

### Round 4: Asymmetric Loss + Inventory Metrics
- Custom objective: 2x penalty for underestimates
- Result: Stockout rates unchanged, prediction errors increased (trade-off)
- Key finding: **Inventory logic matters more than loss function tuning**

### Round 3: All Categories Improved
- Added 12 trend detection features
- Increased model complexity (num_leaves: 31 → 63)
- Result: Category D median MAE improved 95% (4.32 → 0.23)

### Round 2: Category D Improvement
- Focused on trending patterns (Category D)
- Added trend features: slopes, momentum, direction, strength
- Result: Median Normalized MAE 4.32 → 0.23

### Round 1: Baseline
- 20 features, num_leaves: 31
- Category D critical failure (Normalized MAE 4.32)

---

## File Locations (Latest Rounds)

### Round 13 (Latest - Experimental - FEFO Failed)
- **Data**: `ml/data/synthetic_bank/` (organized by archetype: A/, B/, C/, D/, E/)
- **Models**: `ml/models_fefo_all/` (500 models)
- **Results**: `ml/results/results_fefo_all.csv`
- **Note**: ⚠️ Round 13 (FEFO) increased expired rates - Round 9 is recommended

### Round 11 (Experimental - Failed Target)
- **Data**: `ml/data/synthetic_bank/` (organized by archetype: A/, B/, C/, D/, E/)
- **Models**: `ml/models_under50_all/` (500 models)
- **Results**: `ml/results/results_under50_all.csv`
- **Note**: ⚠️ Round 11 increased expired rates - Round 9 is recommended

### Round 10 (Experimental)
- **Data**: `ml/data/synthetic_bank/`
- **Models**: `ml/models_priority4_all/`
- **Results**: `ml/results/results_priority4_all.csv`
- **Note**: ⚠️ Increased expired rates

### Round 9 (Optimal - Recommended) ⭐
- **Data**: `ml/data/synthetic_bank/` (organized by archetype: A/, B/, C/, D/, E/)
- **Models**: `ml/models_priority3_all/` (550 models)
- **Results**: `ml/results/results_priority3_all.csv`

### Round 8
- **Data**: `ml/data/synthetic_bank_priority2/`
- **Models**: `ml/models_priority2_all/`
- **Results**: `ml/results/results_priority2_all_reevaluated.csv`

### Result CSVs
- Round 1: `ml/results/results_second_round.csv`
- Round 2: `ml/results/results_category_d_improved.csv`
- Round 3: `ml/results/results_all_categories_improved.csv`
- Round 4: `ml/results/results_asymmetric_all_500.csv`
- Round 5: `ml/results/results_improved_simulation.csv`
- Round 6: `ml/results/results_priority1_waste_reduction.csv`
- Round 7: `ml/results/results_priority1_all_reevaluated.csv`
- Round 8: `ml/results/results_priority2_all_reevaluated.csv`
- Round 9: `ml/results/results_priority3_all.csv` ⭐
- Round 10: `ml/results/results_priority4_all.csv` ⚠️
- Round 11: `ml/results/results_under50_all.csv` ⚠️
- Round 13: `ml/results/results_fefo_all.csv` ⚠️

### Model Directories
- Round 1: `ml/models/`
- Round 2: `ml/models_category_d_improved/`
- Round 3: `ml/models_all_categories_improved/`
- Round 4-5: `ml/models_all_500/`
- Round 6: `ml/models_all_500/` (re-evaluated only)
- Round 7: `ml/models_priority1_all/`
- Round 8: `ml/models_priority2_all/`
- Round 9: `ml/models_priority3_all/` ⭐
- Round 10: `ml/models_priority4_all/` ⚠️
- Round 11: `ml/models_under50_all/` ⚠️
- Round 13: `ml/models_fefo_all/` ⚠️

### Data Directories
- Round 1-5: `ml/data/synthetic_bank_organized/`
- Round 7: `ml/data/synthetic_bank_priority1/`
- Round 8: `ml/data/synthetic_bank_priority2/`
- Round 9-13: `ml/data/synthetic_bank/` (organized by archetype: A/, B/, C/, D/, E/)


### Interpretation (Tightened)
- **Lead time effects**: In the current simulator, longer lead times correlate with lower expiry, likely due to indirect effects on ordering behavior (cadence/reorder coupling). Treat this as a second-order effect and validate carefully; do not assume longer lead times reduce waste in real operations.

### Phase 1: What We Learned
1. Forecasting is not the bottleneck.
2. Expiry is driven by policy + constraints, not MSE.
3. One policy does not fit all inventory.

### Phase 2: Inventory Naturally Splits Into Regimes
| Regime | Best Policy |
| --- | --- |
| Code carts / exchange-based / intermittent | Par-driven |
| High-volume / stable demand | Forecast-driven |
| Short shelf-life specialty | Needs custom handling |

### What I’d Recommend as Next Steps (Clean + Realistic)
**Immediate**
- Lock in S14 (par-driven) as code-cart baseline.
- Document constraints + stockout tail risk (Category B).

**Short term**
- Formalize the policy layer.
- Forecast-driven with par caps.
- Or hybrid: forecast -> clipped by par.
- Add policy-level metrics: avg on-hand, order frequency, recovery time after stockout.

### Analysis Tools
- Waste analysis: `python3 ml/analyze_waste.py`
- Re-evaluation: `python3 ml/reevaluate_models.py`
- Results aggregation: `python3 ml/evaluate_results.py`

---

## Historical Details (Archived)

### 📊 Historical Rounds Comparison (Rounds 1-13)

| Round | Key Change | Datasets | Stockout Rate (Mean) | Stockout Rate (Median) | Normalized MAE (Median) | Expired Rate |
|-------|------------|----------|---------------------|----------------------|------------------------|--------------|
| **Round 1** | Baseline | 550 | 1.20% | 1.14% | 0.106 | N/A |
| **Round 2** | Category D: Trend features | 100 (D only) | 1.17% | 1.17% | 0.23 | N/A |
| **Round 3** | All: Trend features + num_leaves 63 | 400 | 1.19% | 1.14% | 0.068 | N/A |
| **Round 4** | Asymmetric loss (2:1 penalty) | 500 | 1.25% | 1.14% | 0.129 | 97.58% |
| **Round 5** | Improved inventory simulation | 500 | 1.17% | 1.14% | 0.129 | 97.58% |
| **Round 6** | Priority 1: Adaptive ordering (eval only) | 500 | 1.13% | 1.14% | 0.129 | 97.58%* |
| **Round 7** | Priority 1: In data generation | 500 | 1.18% | 1.14% | 0.138 | **76.44%** ✅ |
| **Round 8** | Priority 1 + Priority 2: Dynamic safety stock | 500 | 1.18% | 1.14% | 0.138 | 76.56% |
| **Round 9** | Priority 3: Category-specific multipliers | 550 | 1.09% | 1.14% | 0.105 | **70.22%** ✅ |
| **Round 10** | Priority 4: Reduced cap + Consume inventory first | 500 | 1.18% | 1.14% | 0.112 | 76.74% ⚠️ |
| **Round 11** | Phase 1: Shelf-life aware + Category caps + Reduced buffers | 500 | 1.20% | 1.14% | 0.119 | 75.53% ⚠️ |
| **Round 13** | FEFO (First-Expiry-First-Out) consumption | 500 | 1.17% | 1.14% | 0.118 | 75.74% ⚠️ |

**Historical Trend**:
- Expired rates: 97.58% → 70.22% (Round 9 best with original parameters)
- Round 14 (S9) achieved 7.89% with realistic parameters - validating parameter realism hypothesis

### Round 14: Realistic Parameters Sensitivity Sweep (Earlier Snapshot)

**Status**: ✅ In Progress (3/13 scenarios completed: baseline, S1, S9)  
**Purpose**: Validate that realistic hospital supply chain parameters (shelf life, lead times, ordering cadence) can achieve expired rates <50% target

**Key Parameter Changes**:
- **Shelf Life**: Increased from 240 days → 730-1095 days (2-3 years, realistic for most medications)
- **Order Cadence**: Changed from 4 days → 7 days (weekly, aligns with hospital practices)
- **Service Level**: Reduced from 99.5% → 98% for routine items (realistic target)
- **Lead Times**: Standardized to 5 days for routine, 14 days for specialty

**Sensitivity Sweep Results (Partial - In Progress)**:

| Scenario | Shelf Life | Order Cadence | Service Level | Expired Rate | vs Baseline | Status |
|----------|-----------|---------------|---------------|--------------|-------------|--------|
| **baseline** | 240 days | 4 days | 99.5% | **59.10%** | - | ✅ Complete |
| **S1** | 365 days | 4 days | 99.5% | **45.29%** | **-13.81 pp** ✅ | ✅ Complete |
| **S9** | 1095 days | 7 days | 98% | **7.89%** | **-51.21 pp** 🎯 | ✅ Complete |
| S2-S8, S10-S12 | Various | Various | Various | TBD | TBD | ⏳ Generating |

**Key Findings**:
- **Shelf Life is Primary Driver** ✅
- **Category E remains hard** (short shelf life, burst events)
- **Parameter realism > ordering logic optimization**

---
