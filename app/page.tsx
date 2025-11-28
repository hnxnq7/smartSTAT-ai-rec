'use client';

import React from 'react';
import { AIRecommendations } from '@/components/AIRecommendations';
import { generateSyntheticData } from '@/lib/data';

export default function Home() {
  const data = generateSyntheticData();

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

