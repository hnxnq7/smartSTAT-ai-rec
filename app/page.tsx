'use client';

import React, { useMemo } from 'react';
import { AIRecommendations } from '@/components/AIRecommendations';
import { generateSyntheticData } from '@/lib/data';

export default function Home() {
  // Use useMemo to ensure data is generated once and remains stable
  const data = useMemo(() => generateSyntheticData(), []);

  return (
    <main className="min-h-screen bg-gray-50">
      <AIRecommendations
        carts={data.carts}
        medications={data.medications}
        batches={data.batches}
        usageEvents={data.usageEvents}
        preferences={data.preferences}
      />
    </main>
  );
}

