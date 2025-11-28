'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { Cart, Medication, Batch, UsageEvent, MedicationPreferences, Recommendation, RiskFilter, PlanningHorizon } from '@/types/inventory';
import { generateAllRecommendations } from '@/lib/recommendations';
import { FilterBar } from './FilterBar';
import { SummaryCards } from './SummaryCards';
import { RecommendationsTable } from './RecommendationsTable';
import { RecommendationDetails } from './RecommendationDetails';
import { Card } from './ui/Card';

interface AIRecommendationsProps {
  carts: Cart[];
  medications: Medication[];
  batches: Batch[];
  usageEvents: UsageEvent[];
  preferences: MedicationPreferences[];
}

export function AIRecommendations({
  carts,
  medications,
  batches,
  usageEvents,
  preferences: initialPreferences,
}: AIRecommendationsProps) {
  const [selectedCartId, setSelectedCartId] = useState<string | 'all'>('all');
  const [selectedDepartment, setSelectedDepartment] = useState<string | 'all'>('all');
  const [planningHorizon, setPlanningHorizon] = useState<PlanningHorizon>(14);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');
  const [selectedRecommendation, setSelectedRecommendation] = useState<Recommendation | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [preferences, setPreferences] = useState<MedicationPreferences[]>(initialPreferences);

  // Update preferences when user changes them
  const handlePreferencesChange = useCallback((
    medicationId: string,
    cartId: string,
    updatedPrefs: Partial<MedicationPreferences>
  ) => {
    setPreferences((prev) => {
      const newPrefs = [...prev];
      const index = newPrefs.findIndex(
        (p) => p.medicationId === medicationId && (p.cartId === cartId || (!p.cartId && cartId === 'all'))
      );
      
      if (index >= 0) {
        newPrefs[index] = { ...newPrefs[index], ...updatedPrefs };
      } else {
        // Create new preference
        newPrefs.push({
          medicationId,
          cartId: cartId !== 'all' ? cartId : undefined,
          ...updatedPrefs,
        } as MedicationPreferences);
      }
      
      return newPrefs;
    });
  }, []);

  // Generate recommendations based on current state
  const recommendations = useMemo(() => {
    const allRecommendations = generateAllRecommendations(
      medications,
      carts,
      batches,
      usageEvents,
      preferences,
      planningHorizon
    );

    // Apply filters
    return allRecommendations.filter((rec) => {
      if (selectedCartId !== 'all' && rec.cartId !== selectedCartId) {
        return false;
      }
      if (selectedDepartment !== 'all' && rec.department !== selectedDepartment) {
        return false;
      }
      return true;
    });
  }, [medications, carts, batches, usageEvents, preferences, planningHorizon, selectedCartId, selectedDepartment]);

  // Update selected recommendation when recommendations are recalculated
  useEffect(() => {
    if (selectedRecommendation) {
      const updated = recommendations.find(
        (r) => r.medicationId === selectedRecommendation.medicationId && r.cartId === selectedRecommendation.cartId
      );
      if (updated) {
        setSelectedRecommendation(updated);
      }
    }
  }, [recommendations, selectedRecommendation?.medicationId, selectedRecommendation?.cartId]);

  const handleViewDetails = useCallback((recommendation: Recommendation) => {
    setSelectedRecommendation(recommendation);
    setIsDetailsOpen(true);
  }, []);

  const handleCloseDetails = useCallback(() => {
    setIsDetailsOpen(false);
    // Keep selectedRecommendation for a moment to allow smooth closing
    setTimeout(() => setSelectedRecommendation(null), 300);
  }, []);

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">AI Recommendations</h1>
        <p className="text-gray-600 mt-2">
          Intelligent medication ordering recommendations based on usage patterns, expiration dates, and your preferences.
        </p>
      </div>

      <FilterBar
        carts={carts}
        selectedCartId={selectedCartId}
        selectedDepartment={selectedDepartment}
        planningHorizon={planningHorizon}
        riskFilter={riskFilter}
        onCartChange={setSelectedCartId}
        onDepartmentChange={setSelectedDepartment}
        onHorizonChange={setPlanningHorizon}
        onRiskFilterChange={setRiskFilter}
      />

      <SummaryCards recommendations={recommendations} planningHorizon={planningHorizon} />

      <Card>
        <RecommendationsTable
          recommendations={recommendations}
          riskFilter={riskFilter}
          onViewDetails={handleViewDetails}
        />
      </Card>

      <RecommendationDetails
        recommendation={selectedRecommendation}
        isOpen={isDetailsOpen}
        onClose={handleCloseDetails}
        onPreferencesChange={handlePreferencesChange}
      />
    </div>
  );
}

