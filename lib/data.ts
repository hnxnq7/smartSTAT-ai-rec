import { Cart, Medication, Batch, UsageEvent, MedicationPreferences } from '@/types/inventory';
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
  batches: Batch[];
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
  const batches: Batch[] = [];
  
  // Generate batches for each medication on each cart
  medications.forEach((med) => {
    carts.forEach((cart) => {
      // 1-3 batches per medication per cart
      const batchCount = Math.floor(rng.next() * 3) + 1;
      for (let i = 0; i < batchCount; i++) {
        const daysUntilExpiry = Math.floor(rng.next() * 60) + 5; // 5-65 days
        const expirationDate = formatISO(addDays(now, daysUntilExpiry), { representation: 'date' });
        const quantity = Math.floor(rng.next() * 50) + 10; // 10-60 units
        
        batches.push({
          id: `batch-${med.id}-${cart.id}-${i}`,
          medicationId: med.id,
          cartId: cart.id,
          quantity,
          expirationDate,
        });
      }
    });
  });

  // Generate usage events over the last 60 days
  const usageEvents: UsageEvent[] = [];
  const startDate = subDays(now, 60);
  
  medications.forEach((med) => {
    carts.forEach((cart) => {
      // Each medication-cart combo has a base usage rate
      const baseDailyUsage = rng.next() * 5 + 0.5; // 0.5-5.5 units/day
      
      // Generate events for each day
      for (let day = 0; day < 60; day++) {
        const date = addDays(startDate, day);
        // Some days have no usage, some have multiple events
        const eventsPerDay = rng.next() < 0.7 ? 1 : rng.next() < 0.9 ? 2 : 0;
        
        for (let e = 0; e < eventsPerDay; e++) {
          // Poisson-like distribution around baseDailyUsage
          const quantity = Math.max(1, Math.floor(rng.next() * baseDailyUsage * 2));
          const hour = Math.floor(rng.next() * 24);
          const minute = Math.floor(rng.next() * 60);
          const eventDate = new Date(date);
          eventDate.setHours(hour, minute, 0, 0);
          const timestamp = formatISO(eventDate);
          
          usageEvents.push({
            timestamp,
            cartId: cart.id,
            medicationId: med.id,
            quantity,
          });
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
    minRemainingShelfLife: Math.floor(rng.next() * 30) + 7, // 7-37 days
    leadTime: Math.floor(rng.next() * 5) + 2, // 2-6 days
    serviceLevel: 0.95, // 95% default
  }));

  return {
    carts,
    medications,
    batches,
    usageEvents,
    preferences,
  };
}

