import React from 'react';
import { Recommendation } from '@/types/inventory';
import { Sheet } from './ui/Sheet';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { PreferencesEditor } from './PreferencesEditor';
import { format } from 'date-fns';
import { parseISO } from 'date-fns';

interface RecommendationDetailsProps {
  recommendation: Recommendation | null;
  isOpen: boolean;
  onClose: () => void;
  onPreferencesChange: (medicationId: string, cartId: string, preferences: Partial<Recommendation['preferences']>) => void;
}

export function RecommendationDetails({
  recommendation,
  isOpen,
  onClose,
  onPreferencesChange,
}: RecommendationDetailsProps) {
  if (!recommendation) return null;

  const handlePreferencesChange = (prefs: Partial<Recommendation['preferences']>) => {
    onPreferencesChange(recommendation.medicationId, recommendation.cartId, prefs);
  };

  return (
    <Sheet isOpen={isOpen} onClose={onClose} title="Recommendation Details">
      <div className="space-y-6">
        {/* Overview */}
        <Card>
          <CardHeader>
            <CardTitle>{recommendation.medicationName}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-500">Cart:</span>
                <span className="ml-2 font-medium">{recommendation.cartName}</span>
              </div>
              <div>
                <span className="text-gray-500">Department:</span>
                <span className="ml-2 font-medium">{recommendation.department}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Explanation */}
        <Card>
          <CardHeader>
            <CardTitle>Explanation</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-700 leading-relaxed">
              {recommendation.explanation}
            </p>
          </CardContent>
        </Card>

        {/* Usage Statistics */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Daily Usage Rate (λ):</span>
                <span className="font-medium">{recommendation.usageStats.dailyUsageRate.toFixed(2)} units/day</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Days of Data:</span>
                <span className="font-medium">{recommendation.usageStats.daysOfData} days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Last Updated:</span>
                <span className="font-medium">
                  {format(parseISO(recommendation.usageStats.lastUpdated), 'MMM d, yyyy HH:mm')}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Calculated Values */}
        <Card>
          <CardHeader>
            <CardTitle>Calculated Values</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Forecast Demand:</span>
                <span className="font-medium">{recommendation.forecastDemand.toFixed(1)} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Safety Stock:</span>
                <span className="font-medium">{recommendation.calculatedValues.safetyStock.toFixed(1)} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Target Stock:</span>
                <span className="font-medium">{recommendation.calculatedValues.targetStock.toFixed(1)} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Current Stock:</span>
                <span className="font-medium">{recommendation.currentStock} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Usable Stock:</span>
                <span className="font-medium">{recommendation.usableStock} units</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Recommended Order:</span>
                <span className="font-medium text-blue-600">{recommendation.recommendedOrderQuantity} units</span>
              </div>
              {recommendation.calculatedValues.daysUntilStockout !== null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Days Until Stockout:</span>
                  <span className="font-medium text-red-600">
                    {recommendation.calculatedValues.daysUntilStockout} days
                  </span>
                </div>
              )}
              {recommendation.calculatedValues.daysUntilExpiry !== null && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Days Until Expiry:</span>
                  <span className="font-medium text-yellow-600">
                    {recommendation.calculatedValues.daysUntilExpiry} days
                  </span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Preferences Editor */}
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
          </CardHeader>
          <CardContent>
            <PreferencesEditor
              preferences={recommendation.preferences}
              onChange={handlePreferencesChange}
            />
          </CardContent>
        </Card>
      </div>
    </Sheet>
  );
}

