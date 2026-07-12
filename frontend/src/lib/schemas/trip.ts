import { z } from 'zod';
import { isAxiosError } from 'axios';
import type { ErrorEnvelope } from '../../types/api';

// ---------------------------------------------------------------------------
// Domain types — mirrors docs/03-API-SPEC.md (Trips/Vehicles/Drivers). These
// are not (yet) present in src/types/api.ts, so they are defined locally here
// and shared across the trips feature files.
// ---------------------------------------------------------------------------

export type TripStatus = 'draft' | 'dispatched' | 'completed' | 'cancelled';

// NOTE: money/odometer/weight NUMERIC columns are serialized by the API as
// string-safe numbers (e.g. "450.00"), not JSON numbers — confirmed live.
// Callers must `Number(...)` these before doing arithmetic/formatting.
export interface Trip {
  id: string;
  trip_code: string;
  source: string;
  destination: string;
  vehicle_id: string;
  driver_id: string;
  cargo_weight_kg: string;
  planned_distance_km: string;
  revenue: string;
  status: TripStatus;
  start_odometer: string | null;
  end_odometer: string | null;
  notes: string | null;
  dispatched_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  created_at: string;
}

export interface VehicleOption {
  id: string;
  registration_number: string;
  name: string;
  max_load_capacity_kg: string;
  status?: string;
}

export interface DriverOption {
  id: string;
  full_name: string;
  license_number: string;
  license_expiry: string;
  safety_score: string;
  status?: string;
}

// Pagination envelope: use `Page<T>` from '../../types/api' (owned by another
// agent, kept AS-IS) rather than duplicating it here.

export interface TripAdvisorVerdictResponse {
  verdict: 'go' | 'caution' | 'block';
  hard_failures: string[];
  risk_factors: string[];
  summary: string;
}

// ---------------------------------------------------------------------------
// zod schemas
//
// zod@4 + @hookform/resolvers@5: `z.coerce.number()` gives the schema's
// *input* type as `unknown` (coerce accepts anything), which then fails to
// satisfy `useForm<Output>()`'s single-generic assumption that TFieldValues
// equals the resolver's input type ("Type 'unknown' is not assignable to
// type 'number'"). Fix: use plain `z.number()` (input === output === number)
// and convert text -> number in each field's onChange via `valueAsNumber`.
// ---------------------------------------------------------------------------

export const tripSchema = z.object({
  source: z.string().min(2, 'Source must be at least 2 characters').max(120),
  destination: z.string().min(2, 'Destination must be at least 2 characters').max(120),
  vehicle_id: z.string().min(1, 'Vehicle is required'),
  driver_id: z.string().min(1, 'Driver is required'),
  cargo_weight_kg: z
    .number({ error: 'Cargo weight is required' })
    .positive('Cargo weight must be greater than 0'),
  planned_distance_km: z
    .number({ error: 'Planned distance is required' })
    .positive('Distance must be greater than 0'),
  revenue: z.number().min(0, 'Revenue cannot be negative').optional(),
  notes: z.string().optional(),
});

export type TripFormInputs = z.infer<typeof tripSchema>;

// end_odometer's lower bound depends on the trip's start_odometer, which is
// only known at render time — build the schema per-modal-instance.
export function buildCompleteTripSchema(startOdometer: number) {
  return z
    .object({
      end_odometer: z.number({ error: 'End odometer is required' }).positive('Must be positive'),
      revenue: z.number().min(0, 'Cannot be negative').optional(),
      fuel_liters: z.number().min(0, 'Cannot be negative').optional(),
      fuel_cost: z.number().min(0, 'Cannot be negative').optional(),
    })
    .refine((data) => data.end_odometer >= startOdometer, {
      message: `Must be ≥ start (${startOdometer.toLocaleString()} km)`,
      path: ['end_odometer'],
    })
    .refine(
      (data) => {
        const hasLiters = data.fuel_liters !== undefined && data.fuel_liters > 0;
        const hasCost = data.fuel_cost !== undefined && data.fuel_cost > 0;
        return hasLiters === hasCost;
      },
      {
        message: 'Fuel liters and fuel cost must both be provided, or both left empty',
        path: ['fuel_cost'],
      }
    );
}

export type CompleteTripInputs = z.infer<ReturnType<typeof buildCompleteTripSchema>>;

// ---------------------------------------------------------------------------
// Shared API error helper — unwraps the standard { error: { code, message,
// field } } envelope (docs/03-API-SPEC.md §2) so callers can map `field`
// onto a react-hook-form field error, or fall back to a form-level banner.
// ---------------------------------------------------------------------------

export function getApiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong. Please try again.'
): { message: string; field?: string | null } {
  if (isAxiosError<ErrorEnvelope>(error) && error.response?.data?.error) {
    const { message, field } = error.response.data.error;
    return { message, field };
  }
  return { message: fallback };
}
