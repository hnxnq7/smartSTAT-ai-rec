import { Cart, Medication, Batch, UsageEvent, MedicationPreferences } from '@/types/inventory';
import { addDays, subDays, formatISO, parseISO } from 'date-fns';

// Synthetic data generation for demo

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

export function generateSyntheticData(): {
  carts: Cart[];
  medications: Medication[];
  batches: Batch[];
  usageEvents: UsageEvent[];
  preferences: MedicationPreferences[];
} {
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
    packageSize: Math.random() > 0.5 ? 10 : undefined,
    maxCapacity: Math.random() > 0.7 ? 100 : undefined,
  }));

  const now = new Date();
  const batches: Batch[] = [];
  
  // Generate batches for each medication on each cart
  medications.forEach((med) => {
    carts.forEach((cart) => {
      // 1-3 batches per medication per cart
      const batchCount = Math.floor(Math.random() * 3) + 1;
      for (let i = 0; i < batchCount; i++) {
        const daysUntilExpiry = Math.floor(Math.random() * 60) + 5; // 5-65 days
        const expirationDate = formatISO(addDays(now, daysUntilExpiry), { representation: 'date' });
        const quantity = Math.floor(Math.random() * 50) + 10; // 10-60 units
        
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
      const baseDailyUsage = Math.random() * 5 + 0.5; // 0.5-5.5 units/day
      
      // Generate events for each day
      for (let day = 0; day < 60; day++) {
        const date = addDays(startDate, day);
        // Some days have no usage, some have multiple events
        const eventsPerDay = Math.random() < 0.7 ? 1 : Math.random() < 0.9 ? 2 : 0;
        
        for (let e = 0; e < eventsPerDay; e++) {
          // Poisson-like distribution around baseDailyUsage
          const quantity = Math.max(1, Math.floor(Math.random() * baseDailyUsage * 2));
          const hour = Math.floor(Math.random() * 24);
          const minute = Math.floor(Math.random() * 60);
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
    surplusDays: Math.floor(Math.random() * 8) + 3, // 3-10 days
    minRemainingShelfLife: Math.floor(Math.random() * 30) + 7, // 7-37 days
    leadTime: Math.floor(Math.random() * 5) + 2, // 2-6 days
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

