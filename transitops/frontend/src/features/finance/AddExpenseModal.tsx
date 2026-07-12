import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

const addExpenseSchema = z.object({
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  expense_type: z.enum(['toll', 'maintenance', 'fine', 'other']),
  amount: z.coerce.number().positive('Must be positive'),
  description: z.string().min(3, 'Description required'),
});

type AddExpenseInputs = z.infer<typeof addExpenseSchema>;

interface AddExpenseModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

export function AddExpenseModal({ isOpen, onClose, availableVehicles }: AddExpenseModalProps) {
  const { control, handleSubmit, formState: { errors } } = useForm<AddExpenseInputs>({
    resolver: zodResolver(addExpenseSchema),
    defaultValues: { vehicle_id: '', expense_type: 'other', amount: undefined, description: '' }
  });

  const onSubmit = (data: AddExpenseInputs) => {
    console.log('Adding expense log:', data);
    onClose();
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
                  { label: 'Maintenance', value: 'maintenance' },
                  { label: 'Fine', value: 'fine' },
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

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" className="bg-signal hover:bg-signal/90 text-white border-transparent">
            Save Expense
          </Button>
        </div>
      </form>
    </Modal>
  );
}
