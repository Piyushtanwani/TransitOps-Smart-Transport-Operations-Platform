import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';
import { apiClient } from '../../api/client';
import type { Page } from '../../types/api';
import {
  getApiErrorMessage,
  type DriverOption,
  type Trip,
  type TripStatus,
  type VehicleOption,
} from '../../lib/schemas/trip';
import { Button } from '../../components/ui/Button';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Modal } from '../../components/ui/Modal';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Textarea } from '../../components/ui/Textarea';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { CompleteTripModal } from './CompleteTripModal';
import { DispatchTripModal } from './DispatchTripModal';

const PAGE_SIZE = 10;

const STATUS_OPTIONS: { label: string; value: string }[] = [
  { label: 'Status: All', value: '' },
  { label: 'Draft', value: 'draft' },
  { label: 'Dispatched', value: 'dispatched' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' },
];

function formatDate(value: string | null): string {
  if (!value) return '-';
  return new Date(value).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
}

function tripDateLabel(trip: Trip): string {
  switch (trip.status) {
    case 'completed':
      return formatDate(trip.completed_at);
    case 'dispatched':
      return formatDate(trip.dispatched_at);
    case 'cancelled':
      return formatDate(trip.cancelled_at);
    default:
      return '-';
  }
}

export function TripsPage() {
  const queryClient = useQueryClient();

  const [status, setStatus] = useState<TripStatus | ''>('');
  const [searchInput, setSearchInput] = useState('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);

  const [dispatchingTrip, setDispatchingTrip] = useState<Trip | null>(null);
  const [completingTrip, setCompletingTrip] = useState<Trip | null>(null);
  const [cancellingTrip, setCancellingTrip] = useState<Trip | null>(null);
  const [viewingTrip, setViewingTrip] = useState<Trip | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelError, setCancelError] = useState<string | null>(null);

  // Debounce free-text search so we don't refetch on every keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      setQ(searchInput.trim());
      setPage(1);
    }, 350);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const handleStatusChange = (value: TripStatus | '') => {
    setStatus(value);
    setPage(1);
  };

  const tripsQuery = useQuery({
    queryKey: ['trips', { status, q, page, page_size: PAGE_SIZE }],
    queryFn: async () => {
      const { data } = await apiClient.get<Page<Trip>>('/trips', {
        params: { status: status || undefined, q: q || undefined, page, page_size: PAGE_SIZE },
      });
      return data;
    },
    placeholderData: keepPreviousData,
  });

  // Unfiltered lookups so the table can render names for trips whose
  // vehicle/driver are no longer in the dispatchable/assignable pools
  // (e.g. a dispatched trip's vehicle is now on_trip, not available).
  const vehiclesQuery = useQuery({
    queryKey: ['vehicles', 'lookup'],
    queryFn: async () => {
      const { data } = await apiClient.get<Page<VehicleOption>>('/vehicles', {
        params: { page_size: 100 },
      });
      return data;
    },
  });

  const driversQuery = useQuery({
    queryKey: ['drivers', 'lookup'],
    queryFn: async () => {
      const { data } = await apiClient.get<Page<DriverOption>>('/drivers', {
        params: { page_size: 100 },
      });
      return data;
    },
  });

  const vehicleById = useMemo(() => {
    const map = new Map<string, VehicleOption>();
    vehiclesQuery.data?.items.forEach((v) => map.set(v.id, v));
    return map;
  }, [vehiclesQuery.data]);

  const driverById = useMemo(() => {
    const map = new Map<string, DriverOption>();
    driversQuery.data?.items.forEach((d) => map.set(d.id, d));
    return map;
  }, [driversQuery.data]);

  const cancelMutation = useMutation({
    mutationFn: async ({ tripId, reason }: { tripId: string; reason?: string }) => {
      const { data } = await apiClient.post<Trip>(`/trips/${tripId}/cancel`, reason ? { reason } : {});
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      setCancellingTrip(null);
      setCancelReason('');
      setCancelError(null);
    },
    onError: (error) => {
      setCancelError(getApiErrorMessage(error).message);
    },
  });

  const trips = tripsQuery.data?.items ?? [];
  const total = tripsQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const dispatchingVehicle = dispatchingTrip ? vehicleById.get(dispatchingTrip.vehicle_id) : undefined;
  const dispatchingDriver = dispatchingTrip ? driverById.get(dispatchingTrip.driver_id) : undefined;

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

      <div className="flex items-center space-x-4">
        <div className="w-48">
          <Select
            value={status}
            onChange={(e) => handleStatusChange(e.target.value as TripStatus | '')}
            options={STATUS_OPTIONS}
          />
        </div>
        <div className="w-64">
          <Input
            placeholder="Search code/source/destination..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>
        {tripsQuery.isFetching && <Loader2 className="h-4 w-4 animate-spin text-ink-mute" />}
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
            {tripsQuery.isLoading && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-ink-mute">Loading trips…</td>
              </tr>
            )}
            {tripsQuery.isError && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-danger">
                  {getApiErrorMessage(tripsQuery.error, 'Failed to load trips.').message}
                </td>
              </tr>
            )}
            {!tripsQuery.isLoading && !tripsQuery.isError && trips.length === 0 && (
              <tr>
                <td colSpan={8} className="px-6 py-8 text-center text-ink-mute">No trips found.</td>
              </tr>
            )}
            {trips.map((trip) => {
              const vehicle = vehicleById.get(trip.vehicle_id);
              const driver = driverById.get(trip.driver_id);
              return (
                <tr key={trip.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-6 py-4 font-data">{trip.trip_code}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{trip.source} → {trip.destination}</td>
                  <td className="px-6 py-4 font-data text-ink-mute">{vehicle?.registration_number ?? trip.vehicle_id}</td>
                  <td className="px-6 py-4">{driver?.full_name ?? trip.driver_id}</td>
                  <td className="px-6 py-4 font-data">{Number(trip.cargo_weight_kg).toLocaleString()}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={trip.status} />
                  </td>
                  <td className="px-6 py-4 font-data text-ink-mute">{tripDateLabel(trip)}</td>
                  <td className="px-6 py-4 space-x-3">
                    {trip.status === 'draft' && (
                      <>
                        <button onClick={() => setDispatchingTrip(trip)} className="text-signal hover:underline font-medium text-sm">Dispatch</button>
                        <button onClick={() => setCancellingTrip(trip)} className="text-danger hover:underline font-medium text-sm">Cancel</button>
                      </>
                    )}
                    {trip.status === 'dispatched' && (
                      <>
                        <button onClick={() => setCompletingTrip(trip)} className="text-signal hover:underline font-medium text-sm">Complete</button>
                        <button onClick={() => setCancellingTrip(trip)} className="text-danger hover:underline font-medium text-sm">Cancel</button>
                      </>
                    )}
                    {(trip.status === 'completed' || trip.status === 'cancelled') && (
                      <button onClick={() => setViewingTrip(trip)} className="text-signal hover:underline font-medium text-sm">View</button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between text-sm text-ink-mute">
        <span>{total} trip{total === 1 ? '' : 's'} • page {page} of {totalPages}</span>
        <div className="space-x-2">
          <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
            Prev
          </Button>
          <Button variant="secondary" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>
            Next
          </Button>
        </div>
      </div>

      {dispatchingTrip && (
        <DispatchTripModal
          isOpen={true}
          onClose={() => setDispatchingTrip(null)}
          tripId={dispatchingTrip.id}
          tripCode={dispatchingTrip.trip_code}
          vehicleId={dispatchingTrip.vehicle_id}
          vehicleReg={dispatchingVehicle?.registration_number ?? dispatchingTrip.vehicle_id}
          vehicleName={dispatchingVehicle?.name ?? ''}
          vehicleCapacityKg={dispatchingVehicle ? Number(dispatchingVehicle.max_load_capacity_kg) : 0}
          driverId={dispatchingTrip.driver_id}
          driverName={dispatchingDriver?.full_name ?? dispatchingTrip.driver_id}
          driverLicenseExpiry={dispatchingDriver?.license_expiry ?? '—'}
          cargoWeight={Number(dispatchingTrip.cargo_weight_kg)}
          plannedDistanceKm={Number(dispatchingTrip.planned_distance_km)}
        />
      )}

      {completingTrip && (
        <CompleteTripModal
          isOpen={true}
          onClose={() => setCompletingTrip(null)}
          tripId={completingTrip.id}
          tripCode={completingTrip.trip_code}
          startOdometer={Number(completingTrip.start_odometer ?? 0)}
        />
      )}

      {cancellingTrip && (
        <ConfirmDialog
          isOpen={true}
          title={`Cancel Trip ${cancellingTrip.trip_code}`}
          isDestructive
          message={
            <div className="space-y-4 text-left w-full">
              <p>
                This trip will move to <strong className="text-ink">cancelled</strong>
                {cancellingTrip.status === 'dispatched' ? ' and its vehicle/driver will be freed up' : ''}. This
                cannot be undone.
              </p>
              <Textarea
                label="Reason (optional)"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="e.g. Customer request, weather delay..."
              />
              {cancelError && <p className="text-sm text-danger">{cancelError}</p>}
            </div>
          }
          confirmText={cancelMutation.isPending ? 'Cancelling…' : 'Cancel Trip'}
          onConfirm={() => {
            if (cancelMutation.isPending) return;
            cancelMutation.mutate({ tripId: cancellingTrip.id, reason: cancelReason.trim() || undefined });
          }}
          onCancel={() => {
            setCancellingTrip(null);
            setCancelReason('');
            setCancelError(null);
          }}
        />
      )}

      {viewingTrip && (
        <Modal isOpen={true} onClose={() => setViewingTrip(null)} title={`Trip ${viewingTrip.trip_code}`}>
          <div className="space-y-3 text-sm text-ink">
            <div className="flex justify-between"><span className="text-ink-mute">Route</span><span>{viewingTrip.source} → {viewingTrip.destination}</span></div>
            <div className="flex justify-between"><span className="text-ink-mute">Vehicle</span><span className="font-data">{vehicleById.get(viewingTrip.vehicle_id)?.registration_number ?? viewingTrip.vehicle_id}</span></div>
            <div className="flex justify-between"><span className="text-ink-mute">Driver</span><span>{driverById.get(viewingTrip.driver_id)?.full_name ?? viewingTrip.driver_id}</span></div>
            <div className="flex justify-between"><span className="text-ink-mute">Cargo</span><span className="font-data">{Number(viewingTrip.cargo_weight_kg).toLocaleString()} kg</span></div>
            <div className="flex justify-between"><span className="text-ink-mute">Planned Distance</span><span className="font-data">{Number(viewingTrip.planned_distance_km).toLocaleString()} km</span></div>
            <div className="flex justify-between"><span className="text-ink-mute">Revenue</span><span className="font-data">₹{Number(viewingTrip.revenue).toLocaleString()}</span></div>
            {viewingTrip.start_odometer && (
              <div className="flex justify-between"><span className="text-ink-mute">Start Odometer</span><span className="font-data">{Number(viewingTrip.start_odometer).toLocaleString()} km</span></div>
            )}
            {viewingTrip.end_odometer && (
              <div className="flex justify-between"><span className="text-ink-mute">End Odometer</span><span className="font-data">{Number(viewingTrip.end_odometer).toLocaleString()} km</span></div>
            )}
            <div className="flex justify-between items-center"><span className="text-ink-mute">Status</span><StatusBadge status={viewingTrip.status} /></div>
            {viewingTrip.notes && (
              <div>
                <span className="text-ink-mute block mb-1">Notes</span>
                <p>{viewingTrip.notes}</p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
