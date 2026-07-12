import { useMemo, useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import {
  buildCompleteTripSchema,
  getApiErrorMessage,
  type CompleteTripInputs,
  type Trip,
} from '../../lib/schemas/trip';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

const COMPLETE_FORM_FIELDS = ['end_odometer', 'revenue', 'fuel_liters', 'fuel_cost'] as const;

interface CompleteTripModalProps {
  isOpen: boolean;
  onClose: () => void;
  tripId: string;
  tripCode: string;
  startOdometer: number;
}

export function CompleteTripModal({ isOpen, onClose, tripId, tripCode, startOdometer }: CompleteTripModalProps) {
  const queryClient = useQueryClient();
  const [formError, setFormError] = useState<string | null>(null);

  // end_odometer's floor depends on this trip's start_odometer.
  const schema = useMemo(() => buildCompleteTripSchema(startOdometer), [startOdometer]);

  const {
    control,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<CompleteTripInputs>({
    resolver: zodResolver(schema),
    defaultValues: {
      end_odometer: undefined,
      revenue: undefined,
      fuel_liters: undefined,
      fuel_cost: undefined,
    },
  });

  const completeMutation = useMutation({
    mutationFn: async (payload: CompleteTripInputs) => {
      const { data } = await apiClient.post<Trip>(`/trips/${tripId}/complete`, payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (error) => {
      const { message, field } = getApiErrorMessage(error);
      if (field && (COMPLETE_FORM_FIELDS as readonly string[]).includes(field)) {
        setError(field as (typeof COMPLETE_FORM_FIELDS)[number], { type: 'server', message });
      } else {
        setFormError(message);
      }
    },
  });

  const onSubmit = (data: CompleteTripInputs) => {
    setFormError(null);
    completeMutation.mutate(data);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Complete Trip ${tripCode}`}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {formError && (
          <div className="rounded-md border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
            {formError}
          </div>
        )}
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="end_odometer"
            control={control}
            render={({ field: { onChange, value, ...field } }) => (
              <Input
                label="End Odometer (km)"
                type="number"
                hint={`Start: ${startOdometer.toLocaleString()} km`}
                value={value ?? ''}
                onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                error={errors.end_odometer?.message}
                {...field}
              />
            )}
          />
          <Controller
            name="revenue"
            control={control}
            render={({ field: { onChange, value, ...field } }) => (
              <Input
                label="Final Revenue (₹)"
                type="number"
                placeholder="Optional"
                value={value ?? ''}
                onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                error={errors.revenue?.message}
                {...field}
              />
            )}
          />
        </div>

        <div className="border-t border-line pt-4">
          <h3 className="text-xs uppercase font-semibold text-ink-mute mb-4">Fuel Log (Optional)</h3>
          <div className="grid grid-cols-2 gap-4">
            <Controller
              name="fuel_liters"
              control={control}
              render={({ field: { onChange, value, ...field } }) => (
                <Input
                  label="Fuel Added (Liters)"
                  type="number"
                  value={value ?? ''}
                  onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                  error={errors.fuel_liters?.message}
                  {...field}
                />
              )}
            />
            <Controller
              name="fuel_cost"
              control={control}
              render={({ field: { onChange, value, ...field } }) => (
                <Input
                  label="Total Fuel Cost (₹)"
                  type="number"
                  value={value ?? ''}
                  onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                  error={errors.fuel_cost?.message}
                  {...field}
                />
              )}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-3 pt-6 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button
            type="submit"
            isLoading={completeMutation.isPending}
            className="bg-ok hover:bg-ok/90 text-white border-transparent"
          >
            Mark Completed
          </Button>
        </div>
      </form>
    </Modal>
  );
}
