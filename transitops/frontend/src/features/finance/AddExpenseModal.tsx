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

const addExpenseSchema = z.object({
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  expense_type: z.enum(['toll', 'parking', 'fine', 'loading', 'other']),
  amount: z.number().positive('Must be positive'),
  description: z.string().min(3, 'Description required'),
});

type AddExpenseInputs = z.infer<typeof addExpenseSchema>;

// Deliberately untyped (inferred) so `amount` can start out `undefined` in the form without
// fighting AddExpenseInputs' stricter required-number type — react-hook-form's
// DefaultValues<T> accepts this shape via contextual typing at each call site below.
const emptyValues = () => ({
  vehicle_id: '',
  expense_type: 'other' as const,
  amount: undefined,
  description: '',
});

interface AddExpenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

// Backend field names -> local form field names, for surfacing 422 errors inline.
const FIELD_MAP: Record<string, keyof AddExpenseInputs> = {
  vehicle_id: 'vehicle_id',
  type: 'expense_type',
  amount: 'amount',
  description: 'description',
};

export function AddExpenseModal({ isOpen, onClose, availableVehicles }: AddExpenseModalProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  // Parent remounts this component (via a `key` tied to isOpen) each time it opens, so
  // form state and serverError below always start fresh without needing a reset effect.
  const { control, handleSubmit, setError, formState: { errors } } = useForm<AddExpenseInputs>({
    resolver: zodResolver(addExpenseSchema),
    defaultValues: emptyValues(),
  });

  const mutation = useMutation({
    mutationFn: async (payload: { vehicle_id: string; type: string; amount: number; description?: string }) => {
      const { data } = await apiClient.post('/expenses', payload);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] });
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
        setServerError('Failed to save expense. Please try again.');
      }
    },
  });

  const onSubmit = (data: AddExpenseInputs) => {
    setServerError(null);
    mutation.mutate({
      vehicle_id: data.vehicle_id,
      type: data.expense_type,
      amount: data.amount,
      description: data.description,
    });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Log Expense">
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
            name="expense_type"
            control={control}
            render={({ field }) => (
              <Select
                label="Type"
                options={[
                  { label: 'Toll', value: 'toll' },
                  { label: 'Parking', value: 'parking' },
                  { label: 'Fine', value: 'fine' },
                  { label: 'Loading', value: 'loading' },
                  { label: 'Other', value: 'other' },
                ]}
                {...field}
                error={errors.expense_type?.message}
              />
            )}
          />
          <Controller
            name="amount"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input label="Amount (₹)" type="number" onChange={(e) => onChange(e.target.valueAsNumber || undefined)} error={errors.amount?.message} {...field} />
            )}
          />
        </div>

        <Controller
          name="description"
          control={control}
          render={({ field }) => (
            <Textarea label="Description" placeholder="Details..." error={errors.description?.message} {...field} />
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
            Save Expense
          </Button>
        </div>
      </form>
    </Modal>
  );
}
