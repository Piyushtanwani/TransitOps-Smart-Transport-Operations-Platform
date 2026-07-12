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

const openMaintenanceSchema = z.object({
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  title: z.string().min(3, 'Title must be at least 3 characters'),
  description: z.string().optional(),
});

type OpenMaintenanceInputs = z.infer<typeof openMaintenanceSchema>;

const emptyValues: OpenMaintenanceInputs = { vehicle_id: '', title: '', description: '' };

interface OpenMaintenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

export function OpenMaintenanceModal({ isOpen, onClose, availableVehicles }: OpenMaintenanceModalProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  // Parent remounts this component (via a `key` tied to isOpen) each time it opens, so
  // form state and serverError below always start fresh without needing a reset effect.
  const { control, handleSubmit, formState: { errors } } = useForm<OpenMaintenanceInputs>({
    resolver: zodResolver(openMaintenanceSchema),
    defaultValues: emptyValues,
  });

  const mutation = useMutation({
    mutationFn: async (payload: { vehicle_id: string; title: string; description?: string }) => {
      const { data } = await apiClient.post('/maintenance', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (error: unknown) => {
      if (isAxiosError<ErrorEnvelope>(error) && error.response?.data?.error) {
        setServerError(error.response.data.error.message);
      } else {
        setServerError('Failed to open maintenance record. Please try again.');
      }
    },
  });

  const onSubmit = (data: OpenMaintenanceInputs) => {
    setServerError(null);
    mutation.mutate({
      vehicle_id: data.vehicle_id,
      title: data.title,
      description: data.description || undefined,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Open Maintenance">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Controller
          name="vehicle_id"
          control={control}
          render={({ field }) => (
            <div>
              <Select
                label="Vehicle"
                options={[
                  { label: 'Select an available vehicle...', value: '' },
                  ...availableVehicles.map(v => ({ label: `${v.reg} — ${v.name}`, value: v.id }))
                ]}
                {...field}
              />
              <p className="text-[11px] text-ink-mute mt-1">Rule: Vehicle must be available to enter maintenance.</p>
              {errors.vehicle_id && <p className="text-xs text-danger mt-1">{errors.vehicle_id.message}</p>}
            </div>
          )}
        />

        <Controller
          name="title"
          control={control}
          render={({ field }) => (
            <Input label="Title / Issue" placeholder="e.g. Engine Overheating" error={errors.title?.message} {...field} />
          )}
        />

        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <Textarea label="Description" placeholder="Notes..." error={errors.description?.message} {...field} />
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
            Open Record
          </Button>
        </div>
      </form>
    </Modal>
  );
}
