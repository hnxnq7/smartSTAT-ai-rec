import React from 'react';
import { Recommendation, RiskFilter, ViewMode } from '@/types/inventory';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Info } from 'lucide-react';
import { format, parseISO } from 'date-fns';

interface RecommendationsTableProps {
  recommendations: Recommendation[];
  riskFilter: RiskFilter;
  viewMode: ViewMode;
  onViewDetails: (recommendation: Recommendation) => void;
}

export function RecommendationsTable({
  recommendations,
  riskFilter,
  viewMode,
  onViewDetails,
}: RecommendationsTableProps) {
  // Filter recommendations based on risk filter
  const filteredRecommendations = recommendations.filter((rec) => {
    if (riskFilter === 'all') return true;
    if (riskFilter === 'stockout') {
      return rec.riskFlags.some((flag) => flag.type === 'stockout');
    }
    return true;
  });

  const getRiskBadgeVariant = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Medication
            </th>
            {viewMode === 'by-cart' && (
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cart / Location
              </th>
            )}
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Current Stock
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Forecast Demand
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Recommended Qty
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Order Date
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Risk Flags
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredRecommendations.length === 0 ? (
            <tr>
              <td colSpan={9} className="px-6 py-4 text-center text-gray-500">
                No recommendations match the current filters.
              </td>
            </tr>
          ) : (
            filteredRecommendations.map((rec) => (
              <tr key={`${rec.medicationId}-${rec.cartId}`} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{rec.medicationName}</div>
                </td>
                {viewMode === 'by-cart' && (
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{rec.cartName}</div>
                    <div className="text-xs text-gray-500">{rec.department}</div>
                  </td>
                )}
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rec.currentStock}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {rec.forecastDemand.toFixed(1)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {rec.recommendedOrderQuantity}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {format(parseISO(rec.recommendedOrderDate), 'MMM d, yyyy')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex flex-wrap gap-1">
                    {rec.riskFlags.map((flag, idx) => (
                      <Badge
                        key={idx}
                        variant={getRiskBadgeVariant(flag.severity)}
                      >
                        {`Stockout (${flag.daysUntil}d)`}
                      </Badge>
                    ))}
                    {rec.riskFlags.length === 0 && (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewDetails(rec)}
                  >
                    <Info className="w-4 h-4 mr-1" />
                    Details
                  </Button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

