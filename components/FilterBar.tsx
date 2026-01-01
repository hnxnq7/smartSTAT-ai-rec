import React from 'react';
import { Cart, RiskFilter, PlanningHorizon, ViewMode } from '@/types/inventory';
import { Select } from './ui/Select';
import { Card, CardContent } from './ui/Card';

interface FilterBarProps {
  carts: Cart[];
  selectedCartId: string | 'all';
  selectedDepartment: string | 'all';
  planningHorizon: PlanningHorizon;
  riskFilter: RiskFilter;
  viewMode: ViewMode;
  onCartChange: (cartId: string | 'all') => void;
  onDepartmentChange: (department: string | 'all') => void;
  onHorizonChange: (horizon: PlanningHorizon) => void;
  onRiskFilterChange: (filter: RiskFilter) => void;
  onViewModeChange: (mode: ViewMode) => void;
}

export function FilterBar({
  carts,
  selectedCartId,
  selectedDepartment,
  planningHorizon,
  riskFilter,
  viewMode,
  onCartChange,
  onDepartmentChange,
  onHorizonChange,
  onRiskFilterChange,
  onViewModeChange,
}: FilterBarProps) {
  const departments = Array.from(new Set(carts.map((c) => c.department))).sort();

  return (
    <Card className="mb-6">
      <CardContent className="py-4">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              View Mode
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => onViewModeChange('by-medication')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex-1 ${
                  viewMode === 'by-medication'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                By Medication
              </button>
              <button
                onClick={() => onViewModeChange('by-cart')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex-1 ${
                  viewMode === 'by-cart'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                By Cart
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cart
            </label>
            <Select
              value={selectedCartId}
              onChange={(e) => onCartChange(e.target.value)}
            >
              <option value="all">All Carts</option>
              {carts.map((cart) => (
                <option key={cart.id} value={cart.id}>
                  {cart.name}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department
            </label>
            <Select
              value={selectedDepartment}
              onChange={(e) => onDepartmentChange(e.target.value)}
            >
              <option value="all">All Departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Planning Horizon
            </label>
            <Select
              value={planningHorizon}
              onChange={(e) => onHorizonChange(Number(e.target.value) as PlanningHorizon)}
            >
              <option value="14">14 days</option>
              <option value="30">30 days</option>
              <option value="60">60 days</option>
              <option value="90">90 days</option>
            </Select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Risk Filter
            </label>
            <Select
              value={riskFilter}
              onChange={(e) => onRiskFilterChange(e.target.value as RiskFilter)}
            >
              <option value="all">All</option>
              <option value="stockout">Stock-out Risk</option>
            </Select>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


