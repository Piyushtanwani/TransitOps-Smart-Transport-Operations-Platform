import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { apiClient } from '../../api/client';
import { Button } from '../../components/ui/Button';
import { Tabs } from '../../components/ui/Tabs';
import { AddFuelModal } from './AddFuelModal';
import { AddExpenseModal } from './AddExpenseModal';

interface VehicleLite {
  id: string;
  registration_number: string;
  name: string;
}

interface FuelLog {
  id: string;
  vehicle_id: string;
  trip_id: string | null;
  liters: string;
  cost: string;
  odometer_at_fill: string | null;
  filled_at: string;
  created_at: string;
}

interface Expense {
  id: string;
  vehicle_id: string;
  trip_id: string | null;
  type: 'toll' | 'parking' | 'fine' | 'loading' | 'other';
  amount: string;
  description: string | null;
  incurred_at: string;
  created_at: string;
}

interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// Fuel/expense reads are restricted to fleet_manager + financial_analyst; other roles get a 403.
function isForbidden(error: unknown): boolean {
  return isAxiosError(error) && error.response?.status === 403;
}

export function FuelExpensesPage() {
  const [activeTab, setActiveTab] = useState('fuel');
  const [isFuelModalOpen, setIsFuelModalOpen] = useState(false);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);

  const vehiclesQuery = useQuery({
    queryKey: ['vehicles', 'all'],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<VehicleLite>>('/vehicles', {
        params: { page_size: 100 },
      });
      return data.items;
    },
  });

  const fuelQuery = useQuery({
    queryKey: ['fuel-logs', { page: 1, page_size: 100 }],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<FuelLog>>('/fuel-logs', {
        params: { page: 1, page_size: 100 },
      });
      return data;
    },
    retry: (failureCount, error) => !isForbidden(error) && failureCount < 2,
  });

  const expensesQuery = useQuery({
    queryKey: ['expenses', { page: 1, page_size: 100 }],
    queryFn: async () => {
      const { data } = await apiClient.get<Paginated<Expense>>('/expenses', {
        params: { page: 1, page_size: 100 },
      });
      return data;
    },
    retry: (failureCount, error) => !isForbidden(error) && failureCount < 2,
  });

  const vehicleMap = useMemo(() => {
    const map = new Map<string, VehicleLite>();
    for (const v of vehiclesQuery.data ?? []) map.set(v.id, v);
    return map;
  }, [vehiclesQuery.data]);

  const vehicleReg = (vehicleId: string) => vehicleMap.get(vehicleId)?.registration_number ?? vehicleId;

  const availableVehicles = (vehiclesQuery.data ?? []).map((v) => ({
    id: v.id,
    reg: v.registration_number,
    name: v.name,
  }));

  const fuelLogs = fuelQuery.data?.items ?? [];
  const expenses = expensesQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">Fuel & Expenses</h1>
          <p className="text-sm text-ink-mute mt-1">Track financial logs and efficiency</p>
        </div>
        <div className="space-x-3">
          <Button onClick={() => setIsExpenseModalOpen(true)}>
            + Add Expense
          </Button>
          <Button onClick={() => setIsFuelModalOpen(true)} className="bg-signal text-white hover:bg-signal/90 border-transparent">
            + Log Fuel
          </Button>
        </div>
      </div>

      <Tabs
        tabs={[{ id: 'fuel', label: 'Fuel Logs' }, { id: 'expenses', label: 'Other Expenses' }]}
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      <div className="rounded-md border border-line bg-surface-1 overflow-hidden">
        {activeTab === 'fuel' ? (
          <table className="w-full text-sm text-left">
            <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
              <tr>
                <th className="px-6 py-4">VEHICLE</th>
                <th className="px-6 py-4">LITERS</th>
                <th className="px-6 py-4">COST (₹)</th>
                <th className="px-6 py-4">₹ / L</th>
                <th className="px-6 py-4">ODOMETER</th>
                <th className="px-6 py-4">DATE</th>
                <th className="px-6 py-4">TRIP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-ink">
              {isForbidden(fuelQuery.error) ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-ink-mute">Not available for your role.</td>
                </tr>
              ) : fuelQuery.isLoading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-ink-mute">Loading fuel logs...</td>
                </tr>
              ) : fuelQuery.isError ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-danger">Failed to load fuel logs.</td>
                </tr>
              ) : fuelLogs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-ink-mute">No fuel logs found.</td>
                </tr>
              ) : (
                fuelLogs.map((f) => {
                  const liters = Number(f.liters);
                  const cost = Number(f.cost);
                  return (
                    <tr key={f.id} className="hover:bg-surface-2/50 transition-colors">
                      <td className="px-6 py-4 font-data text-ink-mute">{vehicleReg(f.vehicle_id)}</td>
                      <td className="px-6 py-4 font-data">{liters} L</td>
                      <td className="px-6 py-4 font-data">₹{cost.toLocaleString()}</td>
                      <td className="px-6 py-4 font-data text-ink-mute">{liters > 0 ? (cost / liters).toFixed(1) : '—'}</td>
                      <td className="px-6 py-4 font-data text-ink-mute">
                        {f.odometer_at_fill ? Number(f.odometer_at_fill).toLocaleString() : '—'}
                      </td>
                      <td className="px-6 py-4 font-data">{f.filled_at}</td>
                      <td className="px-6 py-4 font-data">{f.trip_id ? `${f.trip_id.slice(0, 8)}…` : '-'}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
              <tr>
                <th className="px-6 py-4">VEHICLE</th>
                <th className="px-6 py-4">TYPE</th>
                <th className="px-6 py-4">AMOUNT (₹)</th>
                <th className="px-6 py-4">DESCRIPTION</th>
                <th className="px-6 py-4">DATE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line text-ink">
              {isForbidden(expensesQuery.error) ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-ink-mute">Not available for your role.</td>
                </tr>
              ) : expensesQuery.isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-ink-mute">Loading expenses...</td>
                </tr>
              ) : expensesQuery.isError ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-danger">Failed to load expenses.</td>
                </tr>
              ) : expenses.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-ink-mute">No expenses found.</td>
                </tr>
              ) : (
                expenses.map((e) => (
                  <tr key={e.id} className="hover:bg-surface-2/50 transition-colors">
                    <td className="px-6 py-4 font-data text-ink-mute">{vehicleReg(e.vehicle_id)}</td>
                    <td className="px-6 py-4 uppercase text-[11px] font-medium tracking-wide text-ink-mute">{e.type}</td>
                    <td className="px-6 py-4 font-data font-medium">₹{Number(e.amount).toLocaleString()}</td>
                    <td className="px-6 py-4">{e.description ?? '—'}</td>
                    <td className="px-6 py-4 font-data">{e.incurred_at}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}
      </div>

      <AddFuelModal
        key={isFuelModalOpen ? 'open' : 'closed'}
        isOpen={isFuelModalOpen}
        onClose={() => setIsFuelModalOpen(false)}
        availableVehicles={availableVehicles}
      />
      <AddExpenseModal
        key={isExpenseModalOpen ? 'open' : 'closed'}
        isOpen={isExpenseModalOpen}
        onClose={() => setIsExpenseModalOpen(false)}
        availableVehicles={availableVehicles}
      />
    </div>
  );
}
