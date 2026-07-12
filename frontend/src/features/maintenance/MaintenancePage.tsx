import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../../auth/AuthContext';
import { apiClient } from '../../api/client';
import { Button } from '../../components/ui/Button';
import { OpenMaintenanceModal } from './OpenMaintenanceModal';
import { CloseMaintenanceModal } from './CloseMaintenanceModal';

interface VehicleLite {
  id: string;
  registration_number: string;
  name: string;
}

interface MaintenanceRecord {
  id: string;
  vehicle_id: string;
  title: string;
  description: string | null;
  cost: string;
  status: 'open' | 'closed';
  opened_at: string;
  closed_at: string | null;
  created_by: string;
}

interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export function MaintenancePage() {
  const { user } = useAuth();
  const isFM = user?.role === 'fleet_manager';

  const [isNewOpen, setIsNewOpen] = useState(false);
  const [closingRecord, setClosingRecord] = useState<MaintenanceRecord | null>(null);

  // All vehicles (any status) — used to join registration numbers onto rows.
  const vehiclesQuery = useQuery({
    queryKey: ['vehicles', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<VehicleLite>>('/vehicles', {
        params: { page_size: 100 },
      });
      return data.items;
    },
  });

  // Only available vehicles may enter the shop — feeds the Open modal's picker.
  const availableVehiclesQuery = useQuery({
    queryKey: ['vehicles', 'available'],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<VehicleLite>>('/vehicles', {
        params: { status: 'available', page_size: 100 },
      });
      return data.items;
    },
    enabled: isFM,
  });

  const maintenanceQuery = useQuery({
    queryKey: ['maintenance', { page: 1, page_size: 100 }],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<MaintenanceRecord>>('/maintenance', {
        params: { page: 1, page_size: 100 },
      });
      return data;
    },
  });

  const vehicleMap = useMemo(() => {
    const map = new Map<string, VehicleLite>();
    for (const v of vehiclesQuery.data ?? []) map.set(v.id, v);
    return map;
  }, [vehiclesQuery.data]);

  const vehicleReg = (vehicleId: string) => vehicleMap.get(vehicleId)?.registration_number ?? vehicleId;

  const records = maintenanceQuery.data?.items ?? [];

  const availableVehicles = (availableVehiclesQuery.data ?? []).map((v) => ({
    id: v.id,
    reg: v.registration_number,
    name: v.name,
  }));

  const columnCount = isFM ? 6 : 5;

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
            {maintenanceQuery.isLoading ? (
              <tr>
                <td colSpan={columnCount} className="px-6 py-8 text-center text-ink-mute">
                  Loading maintenance records...
                </td>
              </tr>
            ) : maintenanceQuery.isError ? (
              <tr>
                <td colSpan={columnCount} className="px-6 py-8 text-center text-danger">
                  Failed to load maintenance records.
                </td>
              </tr>
            ) : records.length === 0 ? (
              <tr>
                <td colSpan={columnCount} className="px-6 py-8 text-center text-ink-mute">
                  No maintenance records found.
                </td>
              </tr>
            ) : (
              records.map((rec) => {
                const costNum = Number(rec.cost);
                return (
                  <tr key={rec.id} className="hover:bg-surface-2/50 transition-colors">
                    <td className="px-6 py-4 font-data text-ink-mute">{vehicleReg(rec.vehicle_id)}</td>
                    <td className="px-6 py-4">{rec.title}</td>
                    <td className="px-6 py-4 font-data">{costNum > 0 ? costNum.toLocaleString() : '—'}</td>
                    <td className="px-6 py-4 font-data text-ink-mute">{rec.opened_at.slice(0, 10)}</td>
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
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <OpenMaintenanceModal
        key={isNewOpen ? 'open' : 'closed'}
        isOpen={isNewOpen}
        onClose={() => setIsNewOpen(false)}
        availableVehicles={availableVehicles}
      />

      {closingRecord && (
        <CloseMaintenanceModal
          isOpen={true}
          onClose={() => setClosingRecord(null)}
          recordId={closingRecord.id}
          vehicleReg={vehicleReg(closingRecord.vehicle_id)}
        />
      )}
    </div>
  );
}
