import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
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

interface OpenMaintenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableVehicles: { id: string; reg: string; name: string }[];
}

export function OpenMaintenanceModal({ isOpen, onClose, availableVehicles }: OpenMaintenanceModalProps) {
  const { control, handleSubmit, formState: { errors } } = useForm<OpenMaintenanceInputs>({
    resolver: zodResolver(openMaintenanceSchema),
    defaultValues: { vehicle_id: '', title: '', description: '' }
  });

  const onSubmit = (data: OpenMaintenanceInputs) => {
    console.log('Opening maintenance:', data);
    // TODO: show toast "Moved to In Shop"
    onClose();
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

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" className="bg-signal hover:bg-signal/90 text-white border-transparent">
            Open Record
          </Button>
        </div>
      </form>
    </Modal>
  );
}
