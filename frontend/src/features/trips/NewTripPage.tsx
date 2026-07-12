import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import type { Page } from '../../types/api';
import {
  tripSchema,
  getApiErrorMessage,
  type TripFormInputs,
  type Trip,
  type VehicleOption,
  type DriverOption,
} from '../../lib/schemas/trip';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

const TRIP_FORM_FIELDS = [
  'source',
  'destination',
  'vehicle_id',
  'driver_id',
  'cargo_weight_kg',
  'planned_distance_km',
  'revenue',
  'notes',
] as const;

export function NewTripPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    watch,
    setError,
    clearErrors,
    formState: { errors },
  } = useForm<TripFormInputs>({
    resolver: zodResolver(tripSchema),
    defaultValues: {
      source: '',
      destination: '',
      vehicle_id: '',
      driver_id: '',
      cargo_weight_kg: undefined,
      planned_distance_km: undefined,
      revenue: undefined,
      notes: '',
    },
  });

  // Vehicle/driver pickers: dispatchable/assignable pools only (BR-2/BR-3).
  const vehiclesQuery = useQuery({
    queryKey: ['vehicles', 'dispatchable'],
    queryFn: async () => {
      const { data } = await apiClient.get<Page<VehicleOption>>('/vehicles', {
        params: { dispatchable: true, page_size: 100 },
      });
      return data;
    },
  });

  const driversQuery = useQuery({
    queryKey: ['drivers', 'assignable'],
    queryFn: async () => {
      const { data } = await apiClient.get<Page<DriverOption>>('/drivers', {
        params: { assignable: true, page_size: 100 },
      });
      return data;
    },
  });

  const vehicleId = watch('vehicle_id');
  const cargoWeight = watch('cargo_weight_kg');

  // Live client-side capacity check — flags the error before submit.
  useEffect(() => {
    if (!vehicleId || typeof cargoWeight !== 'number' || Number.isNaN(cargoWeight)) {
      clearErrors('cargo_weight_kg');
      return;
    }
    const vehicle = vehiclesQuery.data?.items.find((v) => v.id === vehicleId);
    if (!vehicle) return;
    const capacity = Number(vehicle.max_load_capacity_kg);
    if (cargoWeight > capacity) {
      setError('cargo_weight_kg', {
        type: 'manual',
        message: `${cargoWeight} kg exceeds ${vehicle.name} capacity of ${capacity} kg`,
      });
    } else {
      clearErrors('cargo_weight_kg');
    }
  }, [vehicleId, cargoWeight, vehiclesQuery.data, setError, clearErrors]);

  const createTripMutation = useMutation({
    mutationFn: async (payload: TripFormInputs) => {
      const { data } = await apiClient.post<Trip>('/trips', {
        source: payload.source,
        destination: payload.destination,
        vehicle_id: payload.vehicle_id,
        driver_id: payload.driver_id,
        cargo_weight_kg: payload.cargo_weight_kg,
        planned_distance_km: payload.planned_distance_km,
        revenue: payload.revenue,
        notes: payload.notes || undefined,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      navigate('/trips');
    },
    onError: (error) => {
      const { message, field } = getApiErrorMessage(error);
      if (field && (TRIP_FORM_FIELDS as readonly string[]).includes(field)) {
        setError(field as (typeof TRIP_FORM_FIELDS)[number], { type: 'server', message });
      } else {
        setFormError(message);
      }
    },
  });

  const onSubmit = (data: TripFormInputs) => {
    setFormError(null);
    createTripMutation.mutate(data);
  };

  const noVehicles = !vehiclesQuery.isLoading && (vehiclesQuery.data?.items.length ?? 0) === 0;
  const noDrivers = !driversQuery.isLoading && (driversQuery.data?.items.length ?? 0) === 0;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-heading font-bold text-ink">New Trip</h1>
        <Button variant="ghost" onClick={() => navigate('/trips')}>Cancel</Button>
      </div>

      <div className="bg-surface-1 rounded-md border border-line p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          {formError && (
            <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
              {formError}
            </div>
          )}

          {/* Route Section */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-mute mb-4 border-b border-line pb-2">Route Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Controller
                  name="source"
                  control={control}
                  render={({ field }) => (
                    <Input label="Source" placeholder="e.g. Mumbai Hub" {...field} error={errors.source?.message} />
                  )}
                />
              </div>
              <div>
                <Controller
                  name="destination"
                  control={control}
                  render={({ field }) => (
                    <Input label="Destination" placeholder="e.g. Pune Depot" {...field} error={errors.destination?.message} />
                  )}
                />
              </div>
              <div>
                <Controller
                  name="planned_distance_km"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <Input
                      label="Planned Distance (km)"
                      type="number"
                      placeholder="e.g. 150"
                      value={value ?? ''}
                      onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                      {...field}
                      error={errors.planned_distance_km?.message}
                    />
                  )}
                />
              </div>
            </div>
          </div>

          {/* Asset Section */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-mute mb-4 border-b border-line pb-2">Assets</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Controller
                  name="vehicle_id"
                  control={control}
                  render={({ field }) => (
                    <Select
                      label="Vehicle"
                      hint={noVehicles ? 'No available vehicles — check Maintenance.' : undefined}
                      options={[
                        { label: vehiclesQuery.isLoading ? 'Loading vehicles…' : 'Select a vehicle...', value: '' },
                        ...(vehiclesQuery.data?.items ?? []).map((v) => ({
                          label: `${v.registration_number} — ${v.name} (${Number(v.max_load_capacity_kg).toLocaleString()} kg)`,
                          value: v.id,
                        })),
                      ]}
                      {...field}
                    />
                  )}
                />
                {errors.vehicle_id && <p className="mt-1 text-xs text-danger">{errors.vehicle_id.message}</p>}
              </div>
              <div>
                <Controller
                  name="driver_id"
                  control={control}
                  render={({ field }) => (
                    <Select
                      label="Driver"
                      hint={noDrivers ? 'No assignable drivers available.' : undefined}
                      options={[
                        { label: driversQuery.isLoading ? 'Loading drivers…' : 'Select a driver...', value: '' },
                        ...(driversQuery.data?.items ?? []).map((d) => ({
                          label: `${d.full_name} (Score: ${Math.round(Number(d.safety_score))}, Exp: ${d.license_expiry})`,
                          value: d.id,
                        })),
                      ]}
                      {...field}
                    />
                  )}
                />
                {errors.driver_id && <p className="mt-1 text-xs text-danger">{errors.driver_id.message}</p>}
              </div>
            </div>
          </div>

          {/* Cargo & Finance Section */}
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-ink-mute mb-4 border-b border-line pb-2">Cargo & Finances</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Controller
                  name="cargo_weight_kg"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <Input
                      label="Cargo Weight (kg)"
                      type="number"
                      placeholder="e.g. 450"
                      value={value ?? ''}
                      onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                      {...field}
                      error={errors.cargo_weight_kg?.message}
                    />
                  )}
                />
              </div>
              <div>
                <Controller
                  name="revenue"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <Input
                      label="Expected Revenue (₹)"
                      type="number"
                      placeholder="Optional"
                      value={value ?? ''}
                      onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                      {...field}
                      error={errors.revenue?.message}
                    />
                  )}
                />
              </div>
            </div>
          </div>

          {/* Notes */}
          <div>
            <Controller
              name="notes"
              control={control}
              render={({ field }) => (
                <Textarea label="Notes" placeholder="Any special instructions..." {...field} />
              )}
            />
          </div>

          <div className="pt-4 border-t border-line flex justify-end">
            <Button
              type="submit"
              isLoading={createTripMutation.isPending}
              className="bg-signal hover:bg-signal/90 border-transparent text-white px-8"
            >
              Create Trip
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
