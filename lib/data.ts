import { Cart, Medication, UsageEvent, MedicationPreferences } from '@/types/inventory';
import { addDays, subDays, formatISO, parseISO } from 'date-fns';

// Synthetic data generation for demo

// Seeded random number generator for deterministic data
class SeededRandom {
  private seed: number;

  constructor(seed: number) {
    this.seed = seed;
  }

  next(): number {
    this.seed = (this.seed * 9301 + 49297) % 233280;
    return this.seed / 233280;
  }
}

const DEPARTMENTS = ['ED', 'OR', 'ICU', 'Pharmacy', 'Ward A', 'Ward B'];
const MEDICATION_NAMES = [
  'Morphine 10mg',
  'Fentanyl 50mcg',
  'Propofol 200mg',
  'Midazolam 5mg',
  'Atropine 1mg',
  'Epinephrine 1mg',
  'Lidocaine 100mg',
  'Dexamethasone 4mg',
  'Ondansetron 4mg',
  'Metoclopramide 10mg',
  'Furosemide 40mg',
  'Heparin 5000 units',
  'Insulin Regular 100 units',
  'Norepinephrine 4mg',
  'Dopamine 200mg',
];

// Use a fixed seed for deterministic data generation
const DATA_SEED = 12345;

export function generateSyntheticData(): {
  carts: Cart[];
  medications: Medication[];
  usageEvents: UsageEvent[];
  preferences: MedicationPreferences[];
} {
  const rng = new SeededRandom(DATA_SEED);
  
  const carts: Cart[] = DEPARTMENTS.flatMap((dept, deptIdx) => {
    const cartCount = dept === 'ED' ? 3 : dept === 'OR' ? 4 : dept === 'ICU' ? 2 : 1;
    return Array.from({ length: cartCount }, (_, i) => ({
      id: `cart-${deptIdx}-${i}`,
      name: `${dept} Cart ${i + 1}`,
      department: dept,
    }));
  });

  const medications: Medication[] = MEDICATION_NAMES.map((name, idx) => ({
    id: `med-${idx}`,
    name,
    packageSize: rng.next() > 0.5 ? 10 : undefined,
    maxCapacity: rng.next() > 0.7 ? 100 : undefined,
  }));

  const now = new Date();
  
  // Generate usage and restock events over the last 60 days
  const usageEvents: UsageEvent[] = [];
  const startDate = subDays(now, 60);
  
  medications.forEach((med) => {
    carts.forEach((cart) => {
      // Each medication-cart combo has a base usage rate
      const baseDailyUsage = rng.next() * 4 + 1; // 1-5 units/day (more realistic)
      
      // Start with varying initial stock levels - some carts low, some high
      // Create variability: some carts are well-stocked, some need restocking
      const initialStockType = rng.next();
      let currentStock: number;
      if (initialStockType < 0.3) {
        // 30% start low (5-25 units) - will need orders soon
        currentStock = Math.floor(rng.next() * 20) + 5;
      } else if (initialStockType < 0.7) {
        // 40% start medium (25-60 units)
        currentStock = Math.floor(rng.next() * 35) + 25;
      } else {
        // 30% start high (60-100 units) - well stocked
        currentStock = Math.floor(rng.next() * 40) + 60;
      }
      
      // Restock frequency varies - some carts get restocked more often
      const restockFrequency = Math.floor(rng.next() * 7) + 5; // 5-11 days between restocks
      
      // Generate events for each day
      for (let day = 0; day < 60; day++) {
        const date = addDays(startDate, day);
        
        // Usage events (removals) - more realistic pattern
        const eventsPerDay = rng.next() < 0.6 ? 1 : rng.next() < 0.85 ? 2 : 0;
        
        for (let e = 0; e < eventsPerDay; e++) {
          // Usage quantities: typically 1-3 units per event, occasionally more
          const usageMultiplier = rng.next() < 0.8 ? 1 : rng.next() < 0.95 ? 2 : 3;
          const quantity = Math.max(1, Math.floor(baseDailyUsage * 0.4 * usageMultiplier + rng.next() * 2));
          const hour = Math.floor(rng.next() * 24);
          const minute = Math.floor(rng.next() * 60);
          const eventDate = new Date(date);
          eventDate.setHours(hour, minute, 0, 0);
          const timestamp = formatISO(eventDate);
          
          // Only record usage if there's stock available (can't use more than available)
          const actualUsage = Math.min(quantity, currentStock);
          if (actualUsage > 0) {
            usageEvents.push({
              timestamp,
              cartId: cart.id,
              medicationId: med.id,
              quantity: actualUsage,
              eventType: 'usage',
            });
            
            currentStock -= actualUsage;
            currentStock = Math.max(0, currentStock); // Ensure never negative
          }
        }
        
        // Restock events - less frequent, smaller quantities
        // Restock when it's been enough days OR stock is critically low (< 5 units)
        const daysSinceLastRestock = day % restockFrequency;
        const shouldRestock = (daysSinceLastRestock === 0 && day > 0) || (currentStock < 5 && day > 0);
        
        if (shouldRestock) {
          // Restock quantities: typically 30-80 units (more realistic for cart capacity)
          // But vary based on usage rate - high usage carts get more
          const baseRestock = Math.floor(baseDailyUsage * 10); // Enough for ~10 days
          const restockQuantity = Math.floor(baseRestock * (0.8 + rng.next() * 0.4)); // ±20% variation
          const restockQty = Math.max(20, Math.min(100, restockQuantity)); // Cap between 20-100 units
          
          const hour = Math.floor(rng.next() * 8) + 6; // Restocks typically 6am-2pm
          const minute = Math.floor(rng.next() * 60);
          const eventDate = new Date(date);
          eventDate.setHours(hour, minute, 0, 0);
          const timestamp = formatISO(eventDate);
          
          usageEvents.push({
            timestamp,
            cartId: cart.id,
            medicationId: med.id,
            quantity: restockQty,
            eventType: 'restock',
          });
          
          currentStock += restockQty;
        }
      }
    });
  });

  // Sort usage events by timestamp
  usageEvents.sort((a, b) => parseISO(a.timestamp).getTime() - parseISO(b.timestamp).getTime());

  // Generate default preferences for each medication
  const preferences: MedicationPreferences[] = medications.map((med) => ({
    medicationId: med.id,
    surplusDays: Math.floor(rng.next() * 8) + 3, // 3-10 days
    leadTime: Math.floor(rng.next() * 5) + 2, // 2-6 days
    serviceLevel: 0.95, // 95% default
  }));

  return {
    carts,
    medications,
    usageEvents,
    preferences,
  };
}

