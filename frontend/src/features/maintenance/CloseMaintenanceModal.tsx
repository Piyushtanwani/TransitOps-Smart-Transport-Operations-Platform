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
import { Button } from '../../components/ui/Button';

const closeMaintenanceSchema = z.object({
  final_cost: z.number().min(0, 'Cost cannot be negative'),
});

type CloseMaintenanceInputs = z.infer<typeof closeMaintenanceSchema>;

interface CloseMaintenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordId: string;
  vehicleReg: string;
}

export function CloseMaintenanceModal({ isOpen, onClose, recordId, vehicleReg }: CloseMaintenanceModalProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  const { control, handleSubmit, formState: { errors } } = useForm<CloseMaintenanceInputs>({
    resolver: zodResolver(closeMaintenanceSchema),
    defaultValues: { final_cost: undefined },
  });

  const mutation = useMutation({
    mutationFn: async (cost: number) => {
      const { data } = await apiClient.post(`/maintenance/${recordId}/close`, { cost });
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
        setServerError('Failed to close maintenance record. Please try again.');
      }
    },
  });

  const onSubmit = (data: CloseMaintenanceInputs) => {
    setServerError(null);
    mutation.mutate(data.final_cost);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Close Maintenance for ${vehicleReg}`}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Controller
          name="final_cost"
          control={control}
          render={({ field: { onChange, ...field } }) => (
            <Input
              label="Final Cost (₹)"
              type="number"
              placeholder="e.g. 1500"
              onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
              error={errors.final_cost?.message}
              {...field}
            />
          )}
        />

        {serverError && (
          <div className="rounded-md border border-danger/30 bg-danger/10 px-3 py-2 text-sm text-danger">
            {serverError}
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" isLoading={mutation.isPending} className="bg-ok hover:bg-ok/90 text-white border-transparent">
            Submit & Close
          </Button>
        </div>
      </form>
    </Modal>
  );
}
