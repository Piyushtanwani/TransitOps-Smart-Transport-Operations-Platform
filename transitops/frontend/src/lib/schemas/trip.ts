import { z } from 'zod';

export const tripSchema = z.object({
  source: z.string().min(2, 'Source must be at least 2 characters').max(120),
  destination: z.string().min(2, 'Destination must be at least 2 characters').max(120),
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  driver_id: z.string().min(1, 'Driver is required'),
  cargo_weight_kg: z.coerce.number().positive('Cargo weight must be greater than 0'),
  planned_distance_km: z.coerce.number().positive('Distance must be greater than 0'),
  revenue: z.coerce.number().min(0, 'Revenue cannot be negative').optional(),
  notes: z.string().optional(),
});

export type TripFormInputs = z.infer<typeof tripSchema>;
