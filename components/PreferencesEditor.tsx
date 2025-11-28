import React from 'react';
import { MedicationPreferences } from '@/types/inventory';
import { Input } from './ui/Input';

interface PreferencesEditorProps {
  preferences: MedicationPreferences;
  onChange: (preferences: Partial<MedicationPreferences>) => void;
}

export function PreferencesEditor({ preferences, onChange }: PreferencesEditorProps) {
  const handleChange = (field: keyof MedicationPreferences, value: number) => {
    onChange({ [field]: value });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Surplus Days (0-14)
        </label>
        <Input
          type="number"
          min="0"
          max="14"
          value={preferences.surplusDays}
          onChange={(e) => handleChange('surplusDays', Number(e.target.value))}
        />
        <p className="text-xs text-gray-500 mt-1">
          Preferred days of surplus stock to maintain
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Minimum Remaining Shelf Life (0-90 days)
        </label>
        <Input
          type="number"
          min="0"
          max="90"
          value={preferences.minRemainingShelfLife}
          onChange={(e) => handleChange('minRemainingShelfLife', Number(e.target.value))}
        />
        <p className="text-xs text-gray-500 mt-1">
          Minimum days of shelf life required at time of use
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Lead Time (days)
        </label>
        <Input
          type="number"
          min="0"
          value={preferences.leadTime}
          onChange={(e) => handleChange('leadTime', Number(e.target.value))}
        />
        <p className="text-xs text-gray-500 mt-1">
          Days from order placement to arrival
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Service Level (0.90, 0.95, or 0.99)
        </label>
        <Input
          type="number"
          min="0.90"
          max="0.99"
          step="0.01"
          value={preferences.serviceLevel || 0.95}
          onChange={(e) => handleChange('serviceLevel', Number(e.target.value))}
        />
        <p className="text-xs text-gray-500 mt-1">
          Target service level for stock availability
        </p>
      </div>
    </div>
  );
}

