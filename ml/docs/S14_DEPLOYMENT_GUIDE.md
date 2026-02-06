# S14 Deployment Guide: Code Cart Par-Driven Ordering

**Configuration**: S14 (Code Cart with Par-Driven Ordering)  
**Expired Rate**: 4.46% (excellent, within 5-15% well-managed range)  
**Status**: ⚠️ Stockout validation pending (see validation section)

---

## Use Case

**Inventory Type**: Code carts, emergency kits, fixed-par stock locations
- Low-to-moderate volume items
- Safety-critical (high service level required)
- Exchange-based replenishment (monthly/quarterly)
- Case pack constraints (MOQ/SPQ)

**Not Suitable For**:
- High-turnover consumables (use forecast-driven instead)
- Just-in-time inventory
- Items without fixed par levels

---

## Inputs Required

### From Pipeline
1. **Par Level** (days of coverage): Default 30 days
   - Calculate: `par_level_units = avg_daily_usage * par_level_days`
   - Adjust based on criticality and exchange cadence

2. **Exchange Cadence** (days): Default 30 days (monthly)
   - Typical: 30 days (monthly) or 90 days (quarterly)
   - Must align with actual cart exchange schedule

3. **Shelf Life at Receipt**:
   - **Labeled expiry**: Manufacturer expiration date
   - **Pull buffer**: 60-120 days (default: 90 days)
   - **Effective shelf life** = labeled - pull buffer
   - Example: 12 months labeled - 90 days buffer = 300 days effective

4. **Lead Times**:
   - **Median**: 7-21 days typical (default: 10 days)
   - **95th percentile**: 30-90 days during shortages (default: 60 days)
   - Use log-normal distribution for realistic long tail

5. **MOQ/SPQ** (case pack constraints):
   - Default: 25 units (middle of 10-50 unit range)
   - Adjust based on actual case pack sizes

---

## Output Format

### Recommended Order Quantities
- **When**: On exchange cadence days (e.g., monthly)
- **Quantity**: `max(0, par_level_units - current_inventory - pending_orders)`
- **Rounded**: Up to nearest MOQ/SPQ multiple
- **Condition**: Only order if `current_inventory < par_level_units`

### Exchange Schedule
- **Frequency**: Based on `order_cadence_days` (e.g., every 30 days)
- **Action**: Restore inventory to par level
- **Timing**: Account for lead time (order `lead_time` days before exchange)

---

## Safe Defaults & Guardrails

### Hard Caps
- **Max order quantity**: `par_level_units * 1.5` (50% buffer max)
- **Do not order if**: `current_inventory >= par_level_units`
- **Min order**: Respect MOQ (if below MOQ and inventory < par, order MOQ)

### Escalation Behavior
- **If stockout risk rises** (inventory < 7 days coverage):
  - Flag for immediate review
  - Consider emergency order (bypass cadence)
  - Adjust par level if pattern persists

### Validation Checks
- **Par level sanity**: `par_level_days` between 14-90 days
- **Exchange cadence**: Must be >= lead time + 7 days buffer
- **Shelf life**: Effective shelf life must be > exchange cadence

---

## What Needs Real Data

### Must Calibrate from Production
1. **Par levels**: Actual target inventory levels per cart/location
2. **Exchange schedule**: Real cart exchange dates and frequency
3. **Shelf life at receipt**: Actual remaining shelf life when items arrive
4. **Case pack sizes**: Actual MOQ/SPQ from suppliers
5. **Lead time distribution**: Historical lead time data for log-normal parameters

### Can Use Defaults Initially
- Pull buffer: 90 days (conservative)
- Lead time median: 10 days (adjust after data)
- Lead time p95: 60 days (adjust after data)

---

## Configuration Example

```yaml
# Code cart configuration
ordering_mode: "par_driven"
par_level:
  days_coverage: 30  # Adjust per cart based on usage

shelf_life:
  mode: "effective"
  pull_buffer_days: 90  # 60-120 day range

order_cadence_days: 30  # Monthly exchanges

lead_time:
  distribution: "lognormal"
  median_days: 10
  p95_days: 60

moq_enabled: true
moq_units: 25  # Case pack size
spq_units: 25
```

---

## Known Limitations

1. **Stockout Validation**: Test datasets show inventory continuity issue (train/test split artifact)
   - **Workaround**: Validate using full time series or regenerate with continuity
   - **Action**: Fix data generation before production deployment

2. **Category B (Low-Volume)**: 29.47% expired rate (acceptable but could improve)
   - **Future enhancement**: Category-specific par levels (lower for low-volume)

3. **Category E (Short Shelf Life)**: 15.72% expired rate (acceptable for specialty items)
   - **Future enhancement**: Shorter par levels or more frequent exchanges

---

## Deployment Checklist

- [ ] Validate stockout rates using full dataset (fix inventory continuity issue)
- [ ] Calibrate par levels from production data
- [ ] Confirm exchange cadence matches actual schedule
- [ ] Verify shelf life at receipt (labeled - buffer calculation)
- [ ] Test with historical data (if available)
- [ ] Set up monitoring for stockout risk escalation
- [ ] Document category-specific adjustments (B, E)

---

**Last Updated**: Based on S14 validation results
