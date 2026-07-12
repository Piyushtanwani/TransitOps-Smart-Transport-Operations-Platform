import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { getApiErrorMessage, type Trip, type TripAdvisorVerdictResponse } from '../../lib/schemas/trip';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';

interface DispatchTripModalProps {
  isOpen: boolean;
  onClose: () => void;
  tripId: string;
  tripCode: string;
  vehicleId: string;
  vehicleReg: string;
  vehicleName: string;
  vehicleCapacityKg: number;
  driverId: string;
  driverName: string;
  driverLicenseExpiry: string;
  cargoWeight: number;
  plannedDistanceKm: number;
}

const VERDICT_META: Record<
  TripAdvisorVerdictResponse['verdict'],
  { label: string; badgeClass: string; barClass: string }
> = {
  go: { label: 'Go', badgeClass: 'bg-ok/20 text-ok border-ok/30', barClass: 'bg-ok' },
  caution: { label: 'Caution', badgeClass: 'bg-warn/20 text-warn border-warn/30', barClass: 'bg-warn' },
  block: { label: 'Block', badgeClass: 'bg-danger/20 text-danger border-danger/30', barClass: 'bg-danger' },
};

export function DispatchTripModal({
  isOpen,
  onClose,
  tripId,
  tripCode,
  vehicleId,
  vehicleReg,
  vehicleName,
  vehicleCapacityKg,
  driverId,
  driverName,
  driverLicenseExpiry,
  cargoWeight,
  plannedDistanceKm,
}: DispatchTripModalProps) {
  const queryClient = useQueryClient();
  const [serverError, setServerError] = useState<string | null>(null);

  // Advisory only (docs/06 §6) — never gates the Dispatch button below.
  const advisorQuery = useQuery({
    queryKey: ['trip-advisor', vehicleId, driverId, cargoWeight, plannedDistanceKm],
    queryFn: async () => {
      const { data } = await apiClient.post<TripAdvisorVerdictResponse>('/ai/trip-advisor', {
        vehicle_id: vehicleId,
        driver_id: driverId,
        cargo_weight_kg: cargoWeight,
        planned_distance_km: plannedDistanceKm,
      });
      return data;
    },
    enabled: isOpen,
    retry: false,
    staleTime: 60_000,
  });

  const dispatchMutation = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<Trip>(`/trips/${tripId}/dispatch`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trips'] });
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (error) => {
      setServerError(getApiErrorMessage(error).message);
    },
  });

  const handleDispatch = () => {
    if (dispatchMutation.isPending) return;
    setServerError(null);
    dispatchMutation.mutate();
  };

  const verdict = advisorQuery.data?.verdict;
  const verdictMeta = verdict ? VERDICT_META[verdict] : null;

  return (
    <ConfirmDialog
      isOpen={isOpen}
      title={`Dispatch Trip ${tripCode}`}
      message={
        <div className="space-y-4 text-left w-full mt-2">
          <ul className="list-disc pl-5 space-y-1 text-ink-mute">
            <li><strong className="text-ink">{vehicleReg}</strong> — {vehicleName} is available</li>
            <li><strong className="text-ink">{driverName}</strong> license valid till {driverLicenseExpiry}</li>
            <li>Cargo <strong className="text-ink">{cargoWeight}/{vehicleCapacityKg} kg</strong> within capacity</li>
          </ul>

          {advisorQuery.isLoading && (
            <p className="text-xs text-ink-mute">Checking AI Trip Advisor…</p>
          )}

          {advisorQuery.isError && (
            <p className="text-xs text-ink-mute">AI Trip Advisor unavailable — proceeding on deterministic checks only.</p>
          )}

          {advisorQuery.data && verdictMeta && (
            <div className="mt-6 p-4 rounded-lg bg-surface-1 border border-line relative overflow-hidden">
              <div className={`absolute top-0 left-0 w-1 h-full ${verdictMeta.barClass}`}></div>
              <div className="flex justify-between items-start mb-2">
                <h4 className="font-semibold text-sm flex items-center text-ink">
                  <svg className="w-4 h-4 mr-2 text-signal" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                  AI Trip Advisor
                </h4>
                <span className={`border text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${verdictMeta.badgeClass}`}>
                  {verdictMeta.label}
                </span>
              </div>
              <p className="text-sm text-ink-mute">{advisorQuery.data.summary}</p>
              {advisorQuery.data.hard_failures.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-sm text-danger">
                  {advisorQuery.data.hard_failures.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
              {advisorQuery.data.risk_factors.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-sm text-warn">
                  {advisorQuery.data.risk_factors.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {serverError && <p className="text-sm text-danger">{serverError}</p>}
        </div>
      }
      confirmText={dispatchMutation.isPending ? 'Dispatching…' : 'Dispatch Now'}
      onConfirm={handleDispatch}
      onCancel={onClose}
    />
  );
}
