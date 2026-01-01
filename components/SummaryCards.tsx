import React from 'react';
import { Recommendation, PlanningHorizon } from '@/types/inventory';
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card';
import { AlertTriangle, Clock, Package } from 'lucide-react';

interface SummaryCardsProps {
  recommendations: Recommendation[];
  planningHorizon: PlanningHorizon;
}

export function SummaryCards({ recommendations, planningHorizon }: SummaryCardsProps) {
  const stockoutRisk = recommendations.filter((rec) =>
    rec.riskFlags.some((flag) => flag.type === 'stockout')
  );
  
  const totalRecommendedOrders = recommendations.reduce((sum, rec) => sum + rec.recommendedOrderQuantity, 0);
  const highRiskCount = recommendations.filter((rec) =>
    rec.riskFlags.some((flag) => flag.type === 'stockout' && flag.severity === 'high')
  ).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Stock-out Risk
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900">{stockoutRisk.length}</div>
          <p className="text-sm text-gray-500 mt-1">
            Medications at risk in next {planningHorizon} days
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-orange-500" />
            High Risk
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900">{highRiskCount}</div>
          <p className="text-sm text-gray-500 mt-1">
            Medications with high stock-out risk
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="w-5 h-5 text-blue-500" />
            Total Recommended Orders
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900">{totalRecommendedOrders}</div>
          <p className="text-sm text-gray-500 mt-1">
            Total units recommended for ordering
          </p>
        </CardContent>
      </Card>
    </div>
  );
}







