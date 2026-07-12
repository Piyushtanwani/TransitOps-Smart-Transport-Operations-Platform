import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { apiClient } from '../../api/client';
import type { ErrorEnvelope } from '../../types/api';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

const addFuelSchema = z.object({
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  liters: z.number().positive('Must be positive'),
  cost: z.number().positive('Must be positive'),
  odometer: z.number().positive('Must be positive').optional(),
  trip_id: z.string().optional(),
  notes: z.string().optional(),
});

type AddFuelInputs = z.infer<typeof addFuelSchema>;

// Deliberately untyped (inferred) so the numeric fields can start out `undefined` in the
// form without fighting AddFuelInputs' stricter required-number types — react-hook-form's
// DefaultValues<T> accepts that shape via contextual typing at each call site below.
const emptyValues = () => ({
  vehicle_id: '',
  liters: undefined,
  cost: undefined,
  odometer: undefined,
  trip_id: '',
  notes: '',
});

interface AddFuelModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

// Backend field names -> local form field names, for surfacing 422 errors inline.
const FIELD_MAP: Record<string, keyof AddFuelInputs> = {
  vehicle_id: 'vehicle_id',
  liters: 'liters',
  cost: 'cost',
  odometer_at_fill: 'odometer',
  trip_id: 'trip_id',
};

export function AddFuelModal({ isOpen, onClose, availableVehicles }: AddFuelModalProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  // Parent remounts this component (via a `key` tied to isOpen) each time it opens, so
  // form state and serverError below always start fresh without needing a reset effect.
  const { control, handleSubmit, setError, formState: { errors } } = useForm<AddFuelInputs>({
    resolver: zodResolver(addFuelSchema),
    defaultValues: emptyValues(),
  });

  const mutation = useMutation({
    mutationFn: async (payload: {
      vehicle_id: string;
      liters: number;
      cost: number;
      odometer_at_fill?: number;
      trip_id?: string;
    }) => {
      const { data } = await apiClient.post('/fuel-logs', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fuel-logs'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (error: unknown) => {
      if (isAxiosError<ErrorEnvelope>(error) && error.response?.data?.error) {
        const { field, message } = error.response.data.error;
        const mapped = field ? FIELD_MAP[field] : undefined;
        if (mapped) {
          setError(mapped, { type: 'server', message });
        } else {
          setServerError(message);
        }
      } else {
        setServerError('Failed to save fuel entry. Please try again.');
      }
    },
  });

  const onSubmit = (data: AddFuelInputs) => {
    setServerError(null);
    mutation.mutate({
      vehicle_id: data.vehicle_id,
      liters: data.liters,
      cost: data.cost,
      odometer_at_fill: data.odometer,
      trip_id: data.trip_id || undefined,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Log Fuel Entry">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Controller
          name="vehicle_id"
          control={control}
          render={({ field }) => (
            <Select
              label="Vehicle"
              options={[
                { label: 'Select a vehicle...', value: '' },
                ...availableVehicles.map(v => ({ label: `${v.reg} — ${v.name}`, value: v.id }))
              ]}
              {...field}
              error={errors.vehicle_id?.message}
            />
          )}
        />

        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="liters"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input label="Liters" type="number" onChange={(e) => onChange(e.target.valueAsNumber || undefined)} error={errors.liters?.message} {...field} />
            )}
          />
          <Controller
            name="cost"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input label="Total Cost (₹)" type="number" onChange={(e) => onChange(e.target.valueAsNumber || undefined)} error={errors.cost?.message} {...field} />
            )}
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="odometer"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input label="Odometer (km)" type="number" onChange={(e) => onChange(e.target.valueAsNumber || undefined)} error={errors.odometer?.message} {...field} />
            )}
          />
          <Controller
            name="trip_id"
            control={control}
            render={({ field }) => (
              <Input label="Trip ID (Optional)" placeholder="e.g. TRP-0001" error={errors.trip_id?.message} {...field} />
            )}
          />
        </div>

        <Controller
          name="notes"
          control={control}
          render={({ field }) => (
            <Textarea label="Notes" placeholder="Optional..." error={errors.notes?.message} {...field} />
          )}
        />

        {serverError && (
          <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {serverError}
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" isLoading={mutation.isPending} className="bg-signal hover:bg-signal/90 text-white border-transparent">
            Save Entry
          </Button>
        </div>
      </form>
    </Modal>
  );
}
