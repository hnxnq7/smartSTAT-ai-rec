import {
  Cart,
  Medication,
  UsageEvent,
  MedicationPreferences,
  UsageStats,
  Recommendation,
  RiskFlag,
  PlanningHorizon,
} from '@/types/inventory';
import { parseISO, addDays, differenceInDays, formatISO } from 'date-fns';

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
  
  // Only count usage events (not restocks) for usage rate calculation
  const relevantEvents = usageEvents.filter(
    (event) =>
      event.medicationId === medicationId &&
      event.cartId === cartId &&
      event.eventType === 'usage' &&
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
    leadTime: 3,
    serviceLevel: 0.95,
  };
}

/**
 * Calculate current stock from usage and restock events
 */
export function calculateCurrentStock(
  usageEvents: UsageEvent[],
  medicationId: string,
  cartId: string
): number {
  const relevantEvents = usageEvents.filter(
    (event) =>
      event.medicationId === medicationId &&
      event.cartId === cartId
  );
  
  // Sum restocks (positive) and subtract usages (negative)
  // Ensure stock never goes negative
  const stock = relevantEvents.reduce((stock, event) => {
    if (event.eventType === 'restock') {
      return stock + event.quantity;
    } else {
      return Math.max(0, stock - event.quantity); // Prevent negative stock
    }
  }, 0);
  
  return Math.max(0, stock); // Final safety check
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

// Expiration date logic removed - we no longer track shelf inventory with expiration dates

/**
 * Generate risk flags for a medication-cart combination
 */
export function generateRiskFlags(
  daysUntilStockout: number | null,
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
  
  parts.push(`Current stock in cart: ${currentStock} units.`);
  
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
  usageEvents: UsageEvent[],
  preferences: MedicationPreferences[],
  planningHorizon: PlanningHorizon
): Recommendation {
  const usageStats = calculateUsageStats(medication.id, cart.id, usageEvents);
  const prefs = getPreferences(medication.id, cart.id, preferences);
  
  // Calculate current stock from events
  const currentStock = calculateCurrentStock(usageEvents, medication.id, cart.id);
  
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
  const recommendedOrderQuantity = Math.max(0, Math.ceil(targetStock - currentStock));
  
  // Recommended order date: order when stock drops to reorder point
  // Reorder point = (lead time * daily usage) + safety stock
  const reorderPoint = prefs.leadTime * usageStats.dailyUsageRate + safetyStock;
  const daysUntilReorder = usageStats.dailyUsageRate > 0 
    ? Math.max(0, Math.floor((currentStock - reorderPoint) / usageStats.dailyUsageRate))
    : planningHorizon;
  
  const now = new Date();
  const recommendedOrderDate = formatISO(addDays(now, daysUntilReorder), { representation: 'date' });
  
  // Calculate risk metrics
  const daysUntilStockout = calculateDaysUntilStockout(currentStock, usageStats.dailyUsageRate);
  const riskFlags = generateRiskFlags(
    daysUntilStockout,
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
    },
  };
}

/**
 * Generate all recommendations
 */
export function generateAllRecommendations(
  medications: Medication[],
  carts: Cart[],
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
        usageEvents,
        preferences,
        planningHorizon
      );
      recommendations.push(recommendation);
    });
  });
  
  return recommendations;
}


