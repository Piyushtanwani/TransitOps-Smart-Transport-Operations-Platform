import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

const closeMaintenanceSchema = z.object({
  final_cost: z.coerce.number().min(0, 'Cost cannot be negative'),
});

type CloseMaintenanceInputs = z.infer<typeof closeMaintenanceSchema>;

interface CloseMaintenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  recordId: string;
  vehicleReg: string;
}

export function CloseMaintenanceModal({ isOpen, onClose, recordId, vehicleReg }: CloseMaintenanceModalProps) {
  const { control, handleSubmit, formState: { errors } } = useForm<CloseMaintenanceInputs>({
    resolver: zodResolver(closeMaintenanceSchema),
    defaultValues: { final_cost: undefined }
  });

  const onSubmit = (data: CloseMaintenanceInputs) => {
    console.log(`Closing record ${recordId} with cost ${data.final_cost}`);
    onClose();
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

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
          <Button type="submit" className="bg-ok hover:bg-ok/90 text-white border-transparent">
            Submit & Close
          </Button>
        </div>
      </form>
    </Modal>
  );
}
