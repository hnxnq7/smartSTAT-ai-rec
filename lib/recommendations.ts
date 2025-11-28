import {
  Cart,
  Medication,
  Batch,
  UsageEvent,
  MedicationPreferences,
  UsageStats,
  Recommendation,
  RiskFlag,
  PlanningHorizon,
} from '@/types/inventory';
import { parseISO, addDays, differenceInDays, formatISO, isAfter, isBefore } from 'date-fns';

/**
 * Calculate usage statistics for a medication on a cart
 */
export function calculateUsageStats(
  medicationId: string,
  cartId: string,
  usageEvents: UsageEvent[],
  lookbackDays: number = 45
): UsageStats {
  const now = new Date();
  const cutoffDate = addDays(now, -lookbackDays);
  
  const relevantEvents = usageEvents.filter(
    (event) =>
      event.medicationId === medicationId &&
      event.cartId === cartId &&
      parseISO(event.timestamp) >= cutoffDate
  );

  if (relevantEvents.length === 0) {
    return {
      medicationId,
      cartId,
      dailyUsageRate: 0,
      daysOfData: 0,
      lastUpdated: formatISO(now),
    };
  }

  const totalQuantity = relevantEvents.reduce((sum, event) => sum + event.quantity, 0);
  const firstEvent = relevantEvents[0];
  const lastEvent = relevantEvents[relevantEvents.length - 1];
  const daysSpan = Math.max(1, differenceInDays(parseISO(lastEvent.timestamp), parseISO(firstEvent.timestamp)) + 1);
  const dailyUsageRate = totalQuantity / daysSpan;

  return {
    medicationId,
    cartId,
    dailyUsageRate,
    daysOfData: daysSpan,
    lastUpdated: formatISO(now),
  };
}

/**
 * Get preferences for a medication-cart combination
 */
export function getPreferences(
  medicationId: string,
  cartId: string,
  preferences: MedicationPreferences[]
): MedicationPreferences {
  // First try to find cart-specific preference
  const cartSpecific = preferences.find(
    (p) => p.medicationId === medicationId && p.cartId === cartId
  );
  if (cartSpecific) return cartSpecific;

  // Then try medication-wide preference
  const medicationWide = preferences.find(
    (p) => p.medicationId === medicationId && !p.cartId
  );
  if (medicationWide) return medicationWide;

  // Default preferences
  return {
    medicationId,
    cartId,
    surplusDays: 5,
    minRemainingShelfLife: 14,
    leadTime: 3,
    serviceLevel: 0.95,
  };
}

/**
 * Calculate usable stock (considering expiration dates and min remaining shelf life)
 */
export function calculateUsableStock(
  batches: Batch[],
  medicationId: string,
  cartId: string,
  minRemainingShelfLife: number,
  planningHorizon: PlanningHorizon
): number {
  const now = new Date();
  const horizonEnd = addDays(now, planningHorizon);
  const minExpiryDate = addDays(horizonEnd, minRemainingShelfLife);

  return batches
    .filter(
      (batch) =>
        batch.medicationId === medicationId &&
        batch.cartId === cartId &&
        isAfter(parseISO(batch.expirationDate), minExpiryDate)
    )
    .reduce((sum, batch) => sum + batch.quantity, 0);
}

/**
 * Calculate total current stock
 */
export function calculateCurrentStock(
  batches: Batch[],
  medicationId: string,
  cartId: string
): number {
  return batches
    .filter((batch) => batch.medicationId === medicationId && batch.cartId === cartId)
    .reduce((sum, batch) => sum + batch.quantity, 0);
}

/**
 * Calculate days until stockout based on current stock and usage rate
 */
export function calculateDaysUntilStockout(
  currentStock: number,
  dailyUsageRate: number
): number | null {
  if (dailyUsageRate <= 0) return null;
  if (currentStock <= 0) return 0;
  return Math.floor(currentStock / dailyUsageRate);
}

/**
 * Find earliest expiring batch and calculate days until expiry
 */
export function calculateDaysUntilExpiry(
  batches: Batch[],
  medicationId: string,
  cartId: string
): { days: number | null; quantity: number } {
  const relevantBatches = batches.filter(
    (batch) => batch.medicationId === medicationId && batch.cartId === cartId
  );

  if (relevantBatches.length === 0) {
    return { days: null, quantity: 0 };
  }

  const now = new Date();
  let earliestExpiry: Date | null = null;
  let expiringQuantity = 0;

  relevantBatches.forEach((batch) => {
    const expiryDate = parseISO(batch.expirationDate);
    if (!earliestExpiry || isBefore(expiryDate, earliestExpiry)) {
      earliestExpiry = expiryDate;
      expiringQuantity = batch.quantity;
    } else if (expiryDate.getTime() === earliestExpiry.getTime()) {
      expiringQuantity += batch.quantity;
    }
  });

  if (!earliestExpiry) {
    return { days: null, quantity: 0 };
  }

  const days = differenceInDays(earliestExpiry, now);
  return { days: days > 0 ? days : 0, quantity: expiringQuantity };
}

/**
 * Generate risk flags for a medication-cart combination
 */
export function generateRiskFlags(
  daysUntilStockout: number | null,
  daysUntilExpiry: number | null,
  expiringQuantity: number,
  planningHorizon: PlanningHorizon
): RiskFlag[] {
  const flags: RiskFlag[] = [];

  // Stockout risk
  if (daysUntilStockout !== null && daysUntilStockout <= planningHorizon) {
    let severity: 'high' | 'medium' | 'low';
    if (daysUntilStockout <= planningHorizon * 0.3) {
      severity = 'high';
    } else if (daysUntilStockout <= planningHorizon * 0.6) {
      severity = 'medium';
    } else {
      severity = 'low';
    }
    flags.push({
      type: 'stockout',
      severity,
      daysUntil: daysUntilStockout,
    });
  }

  // Expiry risk
  if (daysUntilExpiry !== null && daysUntilExpiry <= planningHorizon * 1.5) {
    let severity: 'high' | 'medium' | 'low';
    if (daysUntilExpiry <= 7) {
      severity = 'high';
    } else if (daysUntilExpiry <= 14) {
      severity = 'medium';
    } else {
      severity = 'low';
    }
    flags.push({
      type: 'expiry',
      severity,
      daysUntil: daysUntilExpiry,
      quantity: expiringQuantity,
    });
  }

  return flags;
}

/**
 * Generate explanation text for a recommendation
 */
export function generateExplanation(
  medicationName: string,
  cartName: string,
  usageStats: UsageStats,
  preferences: MedicationPreferences,
  forecastDemand: number,
  currentStock: number,
  usableStock: number,
  recommendedOrderQuantity: number,
  planningHorizon: PlanningHorizon
): string {
  const parts: string[] = [];
  
  parts.push(
    `Based on the last ${usageStats.daysOfData} days, average use is ${usageStats.dailyUsageRate.toFixed(1)} units/day.`
  );
  
  parts.push(
    `With a lead time of ${preferences.leadTime} days and your preference for ${preferences.surplusDays} surplus days, we plan for ${(forecastDemand + (usageStats.dailyUsageRate * preferences.surplusDays)).toFixed(0)} units total over the next ${planningHorizon} days.`
  );
  
  if (usableStock < currentStock) {
    parts.push(
      `You currently have ${currentStock} total units, but only ${usableStock} are usable (considering expiration dates and minimum remaining shelf life of ${preferences.minRemainingShelfLife} days).`
    );
  } else {
    parts.push(`You currently have ${currentStock} usable units.`);
  }
  
  if (recommendedOrderQuantity > 0) {
    parts.push(`We recommend ordering ${recommendedOrderQuantity} units.`);
  } else {
    parts.push(`No order needed at this time.`);
  }
  
  return parts.join(' ');
}

/**
 * Generate recommendation for a medication on a cart
 */
export function generateRecommendation(
  medication: Medication,
  cart: Cart,
  batches: Batch[],
  usageEvents: UsageEvent[],
  preferences: MedicationPreferences[],
  planningHorizon: PlanningHorizon
): Recommendation {
  const usageStats = calculateUsageStats(medication.id, cart.id, usageEvents);
  const prefs = getPreferences(medication.id, cart.id, preferences);
  
  const currentStock = calculateCurrentStock(batches, medication.id, cart.id);
  const usableStock = calculateUsableStock(
    batches,
    medication.id,
    cart.id,
    prefs.minRemainingShelfLife,
    planningHorizon
  );
  
  // Forecast demand over planning horizon
  const forecastDemand = usageStats.dailyUsageRate * planningHorizon;
  
  // Safety stock (based on service level and lead time variability)
  // Simplified: safety stock = z-score * sqrt(lead time) * daily usage rate
  // For 95% service level, z ≈ 1.65
  const zScore = prefs.serviceLevel ? (prefs.serviceLevel === 0.99 ? 2.33 : prefs.serviceLevel === 0.95 ? 1.65 : 1.28) : 1.65;
  const safetyStock = zScore * Math.sqrt(prefs.leadTime) * usageStats.dailyUsageRate;
  
  // Preferred surplus in units
  const preferredSurplus = usageStats.dailyUsageRate * prefs.surplusDays;
  
  // Target stock = forecast demand + safety stock + preferred surplus
  const targetStock = forecastDemand + safetyStock + preferredSurplus;
  
  // Recommended order quantity
  const recommendedOrderQuantity = Math.max(0, Math.ceil(targetStock - usableStock));
  
  // Recommended order date: order when stock drops to reorder point
  // Reorder point = (lead time * daily usage) + safety stock
  const reorderPoint = prefs.leadTime * usageStats.dailyUsageRate + safetyStock;
  const daysUntilReorder = usageStats.dailyUsageRate > 0 
    ? Math.max(0, Math.floor((usableStock - reorderPoint) / usageStats.dailyUsageRate))
    : planningHorizon;
  
  const now = new Date();
  const recommendedOrderDate = formatISO(addDays(now, daysUntilReorder), { representation: 'date' });
  
  // Calculate risk metrics
  const daysUntilStockout = calculateDaysUntilStockout(usableStock, usageStats.dailyUsageRate);
  const expiryInfo = calculateDaysUntilExpiry(batches, medication.id, cart.id);
  const riskFlags = generateRiskFlags(
    daysUntilStockout,
    expiryInfo.days,
    expiryInfo.quantity,
    planningHorizon
  );
  
  // Generate explanation
  const explanation = generateExplanation(
    medication.name,
    cart.name,
    usageStats,
    prefs,
    forecastDemand,
    currentStock,
    usableStock,
    recommendedOrderQuantity,
    planningHorizon
  );
  
  return {
    medicationId: medication.id,
    medicationName: medication.name,
    cartId: cart.id,
    cartName: cart.name,
    department: cart.department,
    currentStock,
    usableStock,
    forecastDemand,
    preferredSurplus,
    recommendedOrderQuantity,
    recommendedOrderDate,
    riskFlags,
    explanation,
    usageStats,
    preferences: prefs,
    calculatedValues: {
      safetyStock,
      targetStock,
      daysUntilStockout,
      daysUntilExpiry: expiryInfo.days,
    },
  };
}

/**
 * Generate all recommendations
 */
export function generateAllRecommendations(
  medications: Medication[],
  carts: Cart[],
  batches: Batch[],
  usageEvents: UsageEvent[],
  preferences: MedicationPreferences[],
  planningHorizon: PlanningHorizon
): Recommendation[] {
  const recommendations: Recommendation[] = [];
  
  medications.forEach((medication) => {
    carts.forEach((cart) => {
      const recommendation = generateRecommendation(
        medication,
        cart,
        batches,
        usageEvents,
        preferences,
        planningHorizon
      );
      recommendations.push(recommendation);
    });
  });
  
  return recommendations;
}

