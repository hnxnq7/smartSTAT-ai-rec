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
  
  const expiryRisk = recommendations.filter((rec) =>
    rec.riskFlags.some((flag) => flag.type === 'expiry')
  );
  
  const projectedWaste = recommendations.reduce((sum, rec) => {
    const expiryFlags = rec.riskFlags.filter((flag) => flag.type === 'expiry');
    return sum + expiryFlags.reduce((flagSum, flag) => flagSum + flag.quantity, 0);
  }, 0);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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
            <Clock className="w-5 h-5 text-yellow-500" />
            Expiry Risk
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900">{expiryRisk.length}</div>
          <p className="text-sm text-gray-500 mt-1">
            Medications expiring soon
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="w-5 h-5 text-orange-500" />
            Projected Waste
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold text-gray-900">{projectedWaste}</div>
          <p className="text-sm text-gray-500 mt-1">
            Units at risk of expiry waste
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

