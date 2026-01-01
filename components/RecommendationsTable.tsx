import React, { useState, useMemo } from 'react';
import { Recommendation, RiskFilter, ViewMode } from '@/types/inventory';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Info, ChevronUp, ChevronDown } from 'lucide-react';
import { format, parseISO } from 'date-fns';

interface RecommendationsTableProps {
  recommendations: Recommendation[];
  riskFilter: RiskFilter;
  viewMode: ViewMode;
  onViewDetails: (recommendation: Recommendation) => void;
}

type SortColumn = 'name' | 'flag';
type SortDirection = 'asc' | 'desc';

// Severity order: high = 3, medium = 2, low = 1, none = 0
const getSeverityValue = (flags: Recommendation['riskFlags']): number => {
  if (flags.length === 0) return 0;
  const highestSeverity = flags.reduce((max, flag) => {
    const val = flag.severity === 'high' ? 3 : flag.severity === 'medium' ? 2 : 1;
    return Math.max(max, val);
  }, 0);
  return highestSeverity;
};

export function RecommendationsTable({
  recommendations,
  riskFilter,
  viewMode,
  onViewDetails,
}: RecommendationsTableProps) {
  const [sortColumn, setSortColumn] = useState<SortColumn>('flag');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc'); // Default: high severity first

  // Filter recommendations based on risk filter
  const filteredRecommendations = useMemo(() => {
    let filtered = recommendations.filter((rec) => {
      if (riskFilter === 'all') return true;
      if (riskFilter === 'stockout') {
        return rec.riskFlags.some((flag) => flag.type === 'stockout');
      }
      return true;
    });

    // Apply sorting
    filtered = [...filtered].sort((a, b) => {
      if (sortColumn === 'name') {
        const comparison = a.medicationName.localeCompare(b.medicationName);
        return sortDirection === 'asc' ? comparison : -comparison;
      } else {
        // Sort by flag severity
        const aSeverity = getSeverityValue(a.riskFlags);
        const bSeverity = getSeverityValue(b.riskFlags);
        if (aSeverity === bSeverity) {
          // If same severity, sort by name as tiebreaker
          return a.medicationName.localeCompare(b.medicationName);
        }
        return sortDirection === 'desc' ? bSeverity - aSeverity : aSeverity - bSeverity;
      }
    });

    return filtered;
  }, [recommendations, riskFilter, sortColumn, sortDirection]);

  const handleSort = (column: SortColumn) => {
    if (sortColumn === column) {
      // Toggle direction if clicking same column
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // New column: default to asc for name, desc for flag (high first)
      setSortColumn(column);
      setSortDirection(column === 'name' ? 'asc' : 'desc');
    }
  };

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

  const SortableHeader = ({ 
    column, 
    children 
  }: { 
    column: SortColumn; 
    children: React.ReactNode;
  }) => (
    <th
      className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 select-none"
      onClick={() => handleSort(column)}
    >
      <div className="flex items-center gap-1">
        {children}
        {sortColumn === column && (
          sortDirection === 'asc' ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )
        )}
      </div>
    </th>
  );

  return (
    <div className="relative">
      {/* Flag Color Explanation - absolutely positioned as background overlay, above table right side */}
      <div className="absolute -top-12 right-4 text-sm text-gray-600 flex items-center gap-3 pointer-events-none z-10">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-red-100 border border-red-300"></span>
          <span>High Risk</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-100 border border-yellow-300"></span>
          <span>Medium Risk</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-blue-100 border border-blue-300"></span>
          <span>Low Risk</span>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <SortableHeader column="name">
              Medication
            </SortableHeader>
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
            <SortableHeader column="flag">
              Risk Flags
            </SortableHeader>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {filteredRecommendations.length === 0 ? (
            <tr>
              <td colSpan={viewMode === 'by-cart' ? 9 : 8} className="px-6 py-4 text-center text-gray-500">
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
    </div>
  );
}

