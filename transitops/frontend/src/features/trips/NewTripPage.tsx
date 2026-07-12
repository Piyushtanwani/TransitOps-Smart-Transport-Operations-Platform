import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { tripSchema } from '../../lib/schemas/trip';
import type { TripFormInputs } from '../../lib/schemas/trip';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

const MOCK_VEHICLES = [
  { id: 'v1', reg: 'MH-01-AB-1234', name: 'Van-05', capacity: 500 },
  { id: 'v2', reg: 'KA-05-XY-9876', name: 'Truck-02', capacity: 2000 },
];

const MOCK_DRIVERS = [
  { id: 'd1', name: 'Alex Manager', expiry: '2028-12-01', score: 96 },
  { id: 'd2', name: 'Priya Officer', expiry: '2025-08-15', score: 99 },
];

export function NewTripPage() {
  const navigate = useNavigate();

  const { control, handleSubmit, watch, setError, clearErrors, formState: { errors } } = useForm<TripFormInputs>({
    resolver: zodResolver(tripSchema),
    defaultValues: {
      source: '',
      destination: '',
      vehicle_id: '',
      driver_id: '',
      cargo_weight_kg: undefined,
      planned_distance_km: undefined,
      revenue: undefined,
      notes: ''
    }
  });

  const vehicleId = watch('vehicle_id');
  const cargoWeight = watch('cargo_weight_kg');

  useEffect(() => {
    if (vehicleId && cargoWeight !== undefined && !isNaN(cargoWeight)) {
      const vehicle = MOCK_VEHICLES.find(v => v.id === vehicleId);
      if (vehicle && cargoWeight > vehicle.capacity) {
        setError('cargo_weight_kg', { 
          type: 'manual', 
          message: `${cargoWeight} kg exceeds ${vehicle.name} capacity of ${vehicle.capacity} kg` 
        });
      } else {
        clearErrors('cargo_weight_kg');
      }
    }
  }, [vehicleId, cargoWeight, setError, clearErrors]);

  const onSubmit = (data: TripFormInputs) => {
    console.log('Trip created:', data);
    navigate('/trips');
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-heading font-bold text-ink">New Trip</h1>
        <Button variant="ghost" onClick={() => navigate('/trips')}>Cancel</Button>
      </div>

      <div className="bg-surface-1 rounded-md border border-line p-8">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
          
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
                  render={({ field: { onChange, ...field } }) => (
                    <Input 
                      label="Planned Distance (km)" 
                      type="number" 
                      placeholder="e.g. 150"
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
                      options={[
                        { label: 'Select a vehicle...', value: '' },
                        ...MOCK_VEHICLES.map(v => ({ label: `${v.reg} — ${v.name} (${v.capacity} kg)`, value: v.id }))
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
                      options={[
                        { label: 'Select a driver...', value: '' },
                        ...MOCK_DRIVERS.map(d => ({ label: `${d.name} (Score: ${d.score}, Exp: ${d.expiry})`, value: d.id }))
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
                  render={({ field: { onChange, ...field } }) => (
                    <Input 
                      label="Cargo Weight (kg)" 
                      type="number" 
                      placeholder="e.g. 450" 
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
                  render={({ field: { onChange, ...field } }) => (
                    <Input 
                      label="Expected Revenue (₹)" 
                      type="number" 
                      placeholder="Optional" 
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
            <Button type="submit" className="bg-signal hover:bg-signal/90 border-transparent text-white px-8">
              Create Trip
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
