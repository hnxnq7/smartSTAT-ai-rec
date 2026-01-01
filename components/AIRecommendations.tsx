'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { parseISO } from 'date-fns';
import { Cart, Medication, UsageEvent, MedicationPreferences, Recommendation, RiskFilter, PlanningHorizon, ViewMode } from '@/types/inventory';
import { generateAllRecommendations } from '@/lib/recommendations';
import { FilterBar } from './FilterBar';
import { SummaryCards } from './SummaryCards';
import { RecommendationsTable } from './RecommendationsTable';
import { RecommendationDetails } from './RecommendationDetails';
import { Card } from './ui/Card';

interface AIRecommendationsProps {
  carts: Cart[];
  medications: Medication[];
  usageEvents: UsageEvent[];
  preferences: MedicationPreferences[];
}

export function AIRecommendations({
  carts,
  medications,
  usageEvents,
  preferences: initialPreferences,
}: AIRecommendationsProps) {
  const [selectedCartId, setSelectedCartId] = useState<string | 'all'>('all');
  const [selectedDepartment, setSelectedDepartment] = useState<string | 'all'>('all');
  const [planningHorizon, setPlanningHorizon] = useState<PlanningHorizon>(14);
  const [riskFilter, setRiskFilter] = useState<RiskFilter>('all');
  const [viewMode, setViewMode] = useState<ViewMode>('by-cart');
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
      usageEvents,
      preferences,
      planningHorizon
    );

    // Apply filters
    let filtered = allRecommendations.filter((rec) => {
      if (selectedCartId !== 'all' && rec.cartId !== selectedCartId) {
        return false;
      }
      if (selectedDepartment !== 'all' && rec.department !== selectedDepartment) {
        return false;
      }
      return true;
    });

    // Aggregate by medication if view mode is 'by-medication'
    if (viewMode === 'by-medication') {
      const aggregated = new Map<string, Recommendation>();
      
      filtered.forEach((rec) => {
        const key = rec.medicationId;
        if (!aggregated.has(key)) {
          // Create aggregated recommendation
          const firstRec = rec;
          aggregated.set(key, {
            ...firstRec,
            cartId: 'all',
            cartName: 'All Carts',
            department: 'All',
            currentStock: 0,
            recommendedOrderQuantity: 0,
            recommendedOrderDate: firstRec.recommendedOrderDate,
            riskFlags: [],
            explanation: '',
            usageStats: {
              medicationId: firstRec.medicationId,
              cartId: 'all',
              dailyUsageRate: 0,
              daysOfData: 0,
              lastUpdated: firstRec.usageStats.lastUpdated,
            },
            calculatedValues: {
              safetyStock: 0,
              targetStock: 0,
              daysUntilStockout: null,
            },
          });
        }
        
          const agg = aggregated.get(key)!;
          agg.currentStock += rec.currentStock;
          agg.forecastDemand += rec.forecastDemand;
        agg.recommendedOrderQuantity += rec.recommendedOrderQuantity;
        agg.usageStats.dailyUsageRate += rec.usageStats.dailyUsageRate;
        agg.usageStats.daysOfData = Math.max(agg.usageStats.daysOfData, rec.usageStats.daysOfData);
        agg.calculatedValues.safetyStock += rec.calculatedValues.safetyStock;
        agg.calculatedValues.targetStock += rec.calculatedValues.targetStock;
        
        // Combine risk flags
        agg.riskFlags.push(...rec.riskFlags);
        
        // Use earliest order date
        if (parseISO(rec.recommendedOrderDate) < parseISO(agg.recommendedOrderDate)) {
          agg.recommendedOrderDate = rec.recommendedOrderDate;
        }
        
        // Update days until stockout (use minimum)
        if (rec.calculatedValues.daysUntilStockout !== null) {
          if (agg.calculatedValues.daysUntilStockout === null || 
              rec.calculatedValues.daysUntilStockout < agg.calculatedValues.daysUntilStockout) {
            agg.calculatedValues.daysUntilStockout = rec.calculatedValues.daysUntilStockout;
          }
        }
      });
      
      // Generate explanation for aggregated recommendations
      Array.from(aggregated.values()).forEach((agg) => {
        const carts = filtered.filter(r => r.medicationId === agg.medicationId);
        agg.explanation = `Aggregated across ${carts.length} carts. Total daily usage: ${agg.usageStats.dailyUsageRate.toFixed(1)} units/day. Recommended total order: ${agg.recommendedOrderQuantity} units.`;
      });
      
      filtered = Array.from(aggregated.values());
    }
    
    return filtered;
  }, [medications, carts, usageEvents, preferences, planningHorizon, selectedCartId, selectedDepartment, viewMode]);

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
          Intelligent medication ordering recommendations based on cart usage patterns and your preferences.
        </p>
      </div>

      <FilterBar
        carts={carts}
        selectedCartId={selectedCartId}
        selectedDepartment={selectedDepartment}
        planningHorizon={planningHorizon}
        riskFilter={riskFilter}
        viewMode={viewMode}
        onCartChange={setSelectedCartId}
        onDepartmentChange={setSelectedDepartment}
        onHorizonChange={setPlanningHorizon}
        onRiskFilterChange={setRiskFilter}
        onViewModeChange={setViewMode}
      />

      <SummaryCards recommendations={recommendations} planningHorizon={planningHorizon} />

      <Card>
        <RecommendationsTable
          recommendations={recommendations}
          riskFilter={riskFilter}
          viewMode={viewMode}
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

