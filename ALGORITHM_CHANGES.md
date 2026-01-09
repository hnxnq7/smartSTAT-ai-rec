# Algorithm Changes: From Inventory-Based to Usage-Only Model

## Overview
The recommendation algorithm was restructured to work without shelf inventory data (Batch tracking with expiration dates). It now relies solely on cart usage and restock events.

## Key Changes

### 1. Stock Calculation

**Before (Inventory-Based):**
```typescript
// Had Batch objects with expiration dates
currentStock = sum of all batch quantities
usableStock = sum of batches that won't expire before use
             (filtered by expirationDate > horizonEnd + minRemainingShelfLife)
```

**Now (Usage-Only):**
```typescript
// Calculate from events only
currentStock = sum(all restock events) - sum(all usage events)
// No expiration filtering needed - just net inventory from events
```

### 2. Recommendation Calculation

**Before:**
- Considered both `currentStock` and `usableStock`
- Some units might be unusable due to expiration
- Order quantity: `targetStock - usableStock`
- Had to check if batches would expire during planning horizon

**Now:**
- Only one stock value: `currentStock`
- All current stock is considered usable
- Order quantity: `targetStock - currentStock`
- Simpler calculation, no expiration checks

### 3. Forecasting (Unchanged)
The core forecasting logic remains the same:
```typescript
dailyUsageRate = totalUsage / daysOfData (from usage events only)
forecastDemand = dailyUsageRate × planningHorizon
safetyStock = z-score × √(leadTime) × dailyUsageRate
targetStock = forecastDemand + safetyStock + preferredSurplus
```

**Key difference:** Only counting `eventType === 'usage'` events for usage rate calculation (restocks are excluded).

### 4. Risk Assessment

**Before:**
- Stockout risk (based on usable stock)
- Expiry risk (batches expiring soon)
- Had to track expiration dates and quantities

**Now:**
- Only stockout risk (based on current stock)
- No expiry risk (no expiration dates to track)
- Simpler risk calculation: `daysUntilStockout = currentStock / dailyUsageRate`

### 5. Event-Based Tracking

**New Event Types:**
```typescript
UsageEvent {
  eventType: 'usage' | 'restock'
  quantity: number  // positive for restocks, used to subtract for usage
}
```

**Stock Calculation from Events:**
```typescript
currentStock = events.reduce((stock, event) => {
  if (event.eventType === 'restock') return stock + event.quantity
  else return stock - event.quantity  // usage
}, 0)
```

## Benefits of the New Approach

1. **Simpler Model:** No need to track expiration dates, batch IDs, or shelf inventory
2. **Real-time Accuracy:** Stock levels reflect actual cart activity
3. **Easier Data Collection:** Only need to track usage and restock events
4. **Focus on Cart-Level:** Matches the actual operational model (cart usage only)

## What Stayed the Same

- Daily usage rate calculation methodology
- Safety stock formula (based on service level and lead time)
- Target stock calculation (demand + safety + surplus)
- Reorder point logic
- Service level considerations

## Summary

The algorithm is now **simpler and more focused** - it treats all cart stock as immediately usable and bases recommendations purely on:
1. Historical usage patterns (usage events)
2. Current stock levels (from event history)
3. User preferences (lead time, surplus days, service level)

No expiration date complexity, no shelf inventory tracking - just cart-level usage intelligence.


