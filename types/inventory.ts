export interface Cart {
  id: string;
  name: string;
  department: string; // ED, OR, ICU, Pharmacy, etc.
}

export interface Medication {
  id: string;
  name: string;
  packageSize?: number; // Optional: units per package
  maxCapacity?: number; // Optional: max units that can be stored
}

export interface UsageEvent {
  timestamp: string; // ISO datetime
  cartId: string;
  medicationId: string;
  quantity: number; // Units removed/used from cart (negative for restocks)
  eventType: 'usage' | 'restock'; // Type of event
}

export interface RestockEvent {
  timestamp: string; // ISO datetime
  cartId: string;
  medicationId: string;
  quantity: number; // Units added to cart
}

export interface MedicationPreferences {
  medicationId: string;
  cartId?: string; // If undefined, applies to all carts for this medication
  surplusDays: number; // 0-14 days of surplus stock preferred
  leadTime: number; // Days from order to arrival
  serviceLevel?: number; // Optional: 0.90, 0.95, 0.99 (90%, 95%, 99%)
}

export interface UsageStats {
  medicationId: string;
  cartId: string;
  dailyUsageRate: number; // λ: average units per day
  daysOfData: number; // Number of days used for calculation
  lastUpdated: string; // ISO datetime
}

export interface Recommendation {
  medicationId: string;
  medicationName: string;
  cartId: string;
  cartName: string;
  department: string;
  currentStock: number; // Current units in cart (calculated from events)
  forecastDemand: number; // Expected demand over planning horizon
  preferredSurplus: number; // Surplus stock in units (based on surplusDays)
  recommendedOrderQuantity: number; // How much to order
  recommendedOrderDate: string; // ISO date - when to place order
  riskFlags: RiskFlag[];
  explanation: string; // Human-readable explanation
  usageStats: UsageStats;
  preferences: MedicationPreferences;
  calculatedValues: {
    safetyStock: number;
    targetStock: number;
    daysUntilStockout: number | null; // null if no risk
  };
}

export type RiskFlag = 
  | { type: 'stockout'; severity: 'high' | 'medium' | 'low'; daysUntil: number };

export type RiskFilter = 'all' | 'stockout';
export type PlanningHorizon = 14 | 30 | 60 | 90;
export type ViewMode = 'by-cart' | 'by-medication';







