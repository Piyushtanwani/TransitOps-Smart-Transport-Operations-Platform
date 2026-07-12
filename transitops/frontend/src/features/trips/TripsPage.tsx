import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { CompleteTripModal } from './CompleteTripModal';
import { DispatchTripModal } from './DispatchTripModal';

const trips = [
  { code: 'TRP-0001', route: 'MUM → PNE', vehicle: 'MH-01-AB-1234', driver: 'Alex Manager', cargo: 450, status: 'dispatched', date: '2026-07-12' },
  { code: 'TRP-0002', route: 'BLR → HYD', vehicle: 'KA-05-XY-9876', driver: 'Priya Officer', cargo: 800, status: 'completed', date: '2026-07-11' },
  { code: 'TRP-0003', route: 'DEL → JAI', vehicle: 'DL-01-ZA-1111', driver: 'John Doe', cargo: 1200, status: 'draft', date: '-' },
  { code: 'TRP-0004', route: 'CHE → MAA', vehicle: 'TN-07-AA-2222', driver: 'Suresh Kumar', cargo: 300, status: 'cancelled', date: '2026-07-10' },
];

export function TripsPage() {
  const [completingTrip, setCompletingTrip] = useState<typeof trips[0] | null>(null);
  const [dispatchingTrip, setDispatchingTrip] = useState<typeof trips[0] | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">Trips</h1>
          <p className="text-sm text-ink-mute mt-1">Manage dispatch and trip lifecycle</p>
        </div>
        <Link to="/trips/new">
          <Button className="bg-signal text-white hover:bg-signal/90 border-transparent">
            + New Trip
          </Button>
        </Link>
      </div>

      <div className="rounded-md border border-line bg-surface-1 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
            <tr>
              <th className="px-6 py-4">CODE</th>
              <th className="px-6 py-4">ROUTE</th>
              <th className="px-6 py-4">VEHICLE</th>
              <th className="px-6 py-4">DRIVER</th>
              <th className="px-6 py-4">CARGO (KG)</th>
              <th className="px-6 py-4">STATUS</th>
              <th className="px-6 py-4">DATE</th>
              <th className="px-6 py-4">ACTIONS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line text-ink">
            {trips.map((trip) => (
              <tr key={trip.code} className="hover:bg-surface-2/50 transition-colors">
                <td className="px-6 py-4 font-data">{trip.code}</td>
                <td className="px-6 py-4 whitespace-nowrap">{trip.route}</td>
                <td className="px-6 py-4 font-data text-ink-mute">{trip.vehicle}</td>
                <td className="px-6 py-4">{trip.driver}</td>
                <td className="px-6 py-4 font-data">{trip.cargo}</td>
                <td className="px-6 py-4">
                  <StatusBadge status={trip.status} />
                </td>
                <td className="px-6 py-4 font-data text-ink-mute">{trip.date}</td>
                <td className="px-6 py-4 space-x-2">
                  {trip.status === 'draft' && (
                    <button onClick={() => setDispatchingTrip(trip)} className="text-signal hover:underline font-medium text-sm">Dispatch</button>
                  )}
                  {trip.status === 'dispatched' && (
                    <button onClick={() => setCompletingTrip(trip)} className="text-signal hover:underline font-medium text-sm">Complete</button>
                  )}
                  {(trip.status === 'completed' || trip.status === 'cancelled') && (
                    <button className="text-signal hover:underline font-medium text-sm">View</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {dispatchingTrip && (
        <DispatchTripModal 
          isOpen={true} 
          onClose={() => setDispatchingTrip(null)}
          tripCode={dispatchingTrip.code}
          vehicleReg={dispatchingTrip.vehicle}
          driverName={dispatchingTrip.driver}
          cargoWeight={dispatchingTrip.cargo}
        />
      )}

      {completingTrip && (
        <CompleteTripModal
          isOpen={true}
          onClose={() => setCompletingTrip(null)}
          tripCode={completingTrip.code}
          startOdometer={45210} 
        />
      )}
    </div>
  );
}
