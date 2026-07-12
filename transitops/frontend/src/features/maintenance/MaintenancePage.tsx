import { useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/ui/Button';
import { OpenMaintenanceModal } from './OpenMaintenanceModal';
import { CloseMaintenanceModal } from './CloseMaintenanceModal';

const mockRecords = [
  { id: 'm1', vehicle: 'MH-01-AB-1234', title: 'Brake Pad Replacement', cost: 1200, opened: '2026-07-10', status: 'closed' },
  { id: 'm2', vehicle: 'DL-01-ZA-1111', title: 'Engine Oil Change', cost: null, opened: '2026-07-12', status: 'open' },
  { id: 'm3', vehicle: 'KA-05-XY-9876', title: 'Suspension Check', cost: null, opened: '2026-07-11', status: 'open' },
];

const availableVehicles = [
  { id: 'v1', reg: 'TN-07-AA-2222', name: 'Pickup-01' },
  { id: 'v2', reg: 'GJ-01-AB-1234', name: 'Truck-04' }
];

export function MaintenancePage() {
  const { user } = useAuth();
  const isFM = user?.role === 'fleet_manager';
  
  const [isNewOpen, setIsNewOpen] = useState(false);
  const [closingRecord, setClosingRecord] = useState<typeof mockRecords[0] | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">Maintenance</h1>
          <p className="text-sm text-ink-mute mt-1">Vehicle service logs and repairs</p>
        </div>
        {isFM && (
          <Button onClick={() => setIsNewOpen(true)} className="bg-signal text-white hover:bg-signal/90 border-transparent">
            + Open Maintenance
          </Button>
        )}
      </div>

      <div className="rounded-md border border-line bg-surface-1 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
            <tr>
              <th className="px-6 py-4">VEHICLE</th>
              <th className="px-6 py-4">TITLE</th>
              <th className="px-6 py-4">COST (₹)</th>
              <th className="px-6 py-4">OPENED</th>
              <th className="px-6 py-4">STATUS</th>
              {isFM && <th className="px-6 py-4">ACTIONS</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line text-ink">
            {mockRecords.map((rec) => (
              <tr key={rec.id} className="hover:bg-surface-2/50 transition-colors">
                <td className="px-6 py-4 font-data text-ink-mute">{rec.vehicle}</td>
                <td className="px-6 py-4">{rec.title}</td>
                <td className="px-6 py-4 font-data">{rec.cost ? rec.cost.toLocaleString() : '—'}</td>
                <td className="px-6 py-4 font-data text-ink-mute">{rec.opened}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    rec.status === 'open' ? 'bg-warn/20 text-warn border border-warn/30' : 'bg-surface-2 text-ink-mute border border-line'
                  }`}>
                    {rec.status.toUpperCase()}
                  </span>
                </td>
                {isFM && (
                  <td className="px-6 py-4">
                    {rec.status === 'open' && (
                      <button onClick={() => setClosingRecord(rec)} className="text-signal hover:underline font-medium text-sm">Close</button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <OpenMaintenanceModal 
        isOpen={isNewOpen} 
        onClose={() => setIsNewOpen(false)} 
        availableVehicles={availableVehicles}
      />

      {closingRecord && (
        <CloseMaintenanceModal
          isOpen={true}
          onClose={() => setClosingRecord(null)}
          recordId={closingRecord.id}
          vehicleReg={closingRecord.vehicle}
        />
      )}
    </div>
  );
}
