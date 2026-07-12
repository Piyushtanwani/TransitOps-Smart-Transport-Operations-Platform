import { useForm, Controller } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Modal } from '../../components/ui/Modal';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

// Refined schema for paired fuel logic
const completeTripSchema = z.object({
  end_odometer: z.coerce.number().positive('Must be positive'),
  revenue: z.coerce.number().min(0, 'Cannot be negative').optional(),
  fuel_liters: z.coerce.number().min(0).optional(),
  fuel_cost: z.coerce.number().min(0).optional(),
}).refine(data => {
  // If one is provided, the other MUST be provided
  const hasLiters = data.fuel_liters !== undefined && data.fuel_liters > 0;
  const hasCost = data.fuel_cost !== undefined && data.fuel_cost > 0;
  return hasLiters === hasCost;
}, {
  message: "Fuel liters and fuel cost must both be provided, or both left empty",
  path: ["fuel_cost"]
});

type CompleteTripInputs = z.infer<typeof completeTripSchema>;

interface CompleteTripModalProps {
  isOpen: boolean;
  onClose: () => void;
  tripCode: string;
  startOdometer: number;
}

export function CompleteTripModal({ isOpen, onClose, tripCode, startOdometer }: CompleteTripModalProps) {
  const { control, handleSubmit, formState: { errors }, watch, setError } = useForm<CompleteTripInputs>({
    resolver: zodResolver(completeTripSchema),
    defaultValues: {
      end_odometer: undefined,
      revenue: undefined,
      fuel_liters: undefined,
      fuel_cost: undefined
    }
  });

  const endOdo = watch('end_odometer');

  const onSubmit = (data: CompleteTripInputs) => {
    if (data.end_odometer < startOdometer) {
      setError('end_odometer', { message: `Must be ≥ start (${startOdometer} km)` });
      return;
    }
    console.log(`Completing trip ${tripCode}:`, data);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Complete Trip ${tripCode}`}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="end_odometer"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input 
                label="End Odometer (km)" 
                type="number" 
                hint={`Start: ${startOdometer.toLocaleString()} km`}
                onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                error={errors.end_odometer?.message}
                {...field} 
              />
            )}
          />
          <Controller
            name="revenue"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input 
                label="Final Revenue (₹)" 
                type="number" 
                placeholder="Optional"
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
              render={({ field: { onChange, ...field } }) => (
                <Input 
                  label="Fuel Added (Liters)" 
                  type="number" 
                  onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                  error={errors.fuel_liters?.message}
                  {...field} 
                />
              )}
            />
            <Controller
              name="fuel_cost"
              control={control}
              render={({ field: { onChange, ...field } }) => (
                <Input 
                  label="Total Fuel Cost (₹)" 
                  type="number" 
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
          <Button type="submit" className="bg-ok hover:bg-ok/90 text-white border-transparent">
            Mark Completed
          </Button>
        </div>
      </form>
    </Modal>
  );
}
