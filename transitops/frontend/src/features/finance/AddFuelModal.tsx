import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Select } from '../../components/ui/Select';
import { Button } from '../../components/ui/Button';
import { Textarea } from '../../components/ui/Textarea';

const addFuelSchema = z.object({
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  liters: z.coerce.number().positive('Must be positive'),
  cost: z.coerce.number().positive('Must be positive'),
  odometer: z.coerce.number().positive('Must be positive'),
  trip_id: z.string().optional(),
  notes: z.string().optional(),
});

type AddFuelInputs = z.infer<typeof addFuelSchema>;

interface AddFuelModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

export function AddFuelModal({ isOpen, onClose, availableVehicles }: AddFuelModalProps) {
  const { control, handleSubmit, formState: { errors } } = useForm<AddFuelInputs>({
    resolver: zodResolver(addFuelSchema),
    defaultValues: { vehicle_id: '', liters: undefined, cost: undefined, odometer: undefined, trip_id: '', notes: '' }
  });

  const onSubmit = (data: AddFuelInputs) => {
    console.log('Adding fuel log:', data);
    onClose();
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

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" className="bg-signal hover:bg-signal/90 text-white border-transparent">
            Save Entry
          </Button>
        </div>
      </form>
    </Modal>
  );
}
