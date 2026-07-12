import { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Tabs } from '../../components/ui/Tabs';
import { AddFuelModal } from './AddFuelModal';
import { AddExpenseModal } from './AddExpenseModal';

const mockFuel = [
  { id: 'f1', vehicle: 'MH-01-AB-1234', liters: 45.5, cost: 4322, odo: 45210, date: '2026-07-12', trip: 'TRP-0001' },
  { id: 'f2', vehicle: 'DL-01-ZA-1111', liters: 120, cost: 11400, odo: 120500, date: '2026-07-11', trip: '-' },
];

const mockExpenses = [
  { id: 'e1', vehicle: 'MH-01-AB-1234', type: 'toll', amount: 350, desc: 'Highway Toll Plaza', date: '2026-07-12' },
  { id: 'e2', vehicle: 'KA-05-XY-9876', type: 'fine', amount: 1500, desc: 'Speeding ticket', date: '2026-07-10' },
];

const availableVehicles = [
  { id: 'v1', reg: 'MH-01-AB-1234', name: 'Van-05' },
  { id: 'v2', reg: 'DL-01-ZA-1111', name: 'Truck-04' }
];

export function FuelExpensesPage() {
  const [activeTab, setActiveTab] = useState('fuel');
  const [isFuelModalOpen, setIsFuelModalOpen] = useState(false);
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);

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
              {mockFuel.map((f) => (
                <tr key={f.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-6 py-4 font-data text-ink-mute">{f.vehicle}</td>
                  <td className="px-6 py-4 font-data">{f.liters} L</td>
                  <td className="px-6 py-4 font-data">₹{f.cost.toLocaleString()}</td>
                  <td className="px-6 py-4 font-data text-ink-mute">{(f.cost / f.liters).toFixed(1)}</td>
                  <td className="px-6 py-4 font-data text-ink-mute">{f.odo.toLocaleString()}</td>
                  <td className="px-6 py-4 font-data">{f.date}</td>
                  <td className="px-6 py-4 font-data">{f.trip}</td>
                </tr>
              ))}
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
              {mockExpenses.map((e) => (
                <tr key={e.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-6 py-4 font-data text-ink-mute">{e.vehicle}</td>
                  <td className="px-6 py-4 uppercase text-[11px] font-medium tracking-wide text-ink-mute">{e.type}</td>
                  <td className="px-6 py-4 font-data font-medium">₹{e.amount.toLocaleString()}</td>
                  <td className="px-6 py-4">{e.desc}</td>
                  <td className="px-6 py-4 font-data">{e.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <AddFuelModal isOpen={isFuelModalOpen} onClose={() => setIsFuelModalOpen(false)} availableVehicles={availableVehicles} />
      <AddExpenseModal isOpen={isExpenseModalOpen} onClose={() => setIsExpenseModalOpen(false)} availableVehicles={availableVehicles} />
    </div>
  );
}
