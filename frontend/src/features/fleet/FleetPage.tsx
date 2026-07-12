import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient, keepPreviousData } from '@tanstack/react-query';
import axios from 'axios';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { AlertTriangle, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { apiClient } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import type { ErrorEnvelope } from '../../types/api';
import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { StatusBadge } from '../../components/ui/StatusBadge';

// ---- Local types (mirrors docs/03-API-SPEC.md §4 Vehicles — api/client.ts + types/api.ts stay untouched) ----
type VehicleType = 'truck' | 'van' | 'mini_truck' | 'trailer';
type VehicleStatus = 'available' | 'on_trip' | 'in_shop' | 'retired';

interface Vehicle {
  id: string;
  registration_number: string;
  name: string;
  type: VehicleType;
  max_load_capacity_kg: string;
  odometer_km: string;
  acquisition_cost: string;
  region: string;
  status: VehicleStatus;
  created_at: string;
  updated_at?: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

const VEHICLE_TYPES: { label: string; value: VehicleType }[] = [
  { label: 'Truck', value: 'truck' },
  { label: 'Van', value: 'van' },
  { label: 'Mini Truck', value: 'mini_truck' },
  { label: 'Trailer', value: 'trailer' },
];

const VEHICLE_STATUSES: { label: string; value: VehicleStatus }[] = [
  { label: 'Available', value: 'available' },
  { label: 'On Trip', value: 'on_trip' },
  { label: 'In Shop', value: 'in_shop' },
  { label: 'Retired', value: 'retired' },
];

const REGIONS = ['North', 'South', 'East', 'West'];
const PAGE_SIZE = 10;

function typeLabel(type: string): string {
  return type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatINR(value: string | number): string {
  return `₹${Number(value).toLocaleString('en-IN')}`;
}

function getErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as ErrorEnvelope | undefined;
    if (data?.error?.message) return data.error.message;
  }
  return fallback;
}

const VEHICLE_FORM_FIELDS = [
  'registration_number',
  'name',
  'type',
  'max_load_capacity_kg',
  'odometer_km',
  'acquisition_cost',
  'region',
] as const;
type VehicleFormField = (typeof VEHICLE_FORM_FIELDS)[number];
function isVehicleFormField(x: string): x is VehicleFormField {
  return (VEHICLE_FORM_FIELDS as readonly string[]).includes(x);
}

// Note: plain z.number() (not z.coerce) — the <Input type="number"> onChange handlers below
// already convert to a real number via valueAsNumber before it reaches RHF/zod, and using
// z.coerce here would make zodResolver's inferred *input* type diverge from VehicleFormInputs
// (its output type), which useForm<VehicleFormInputs> then rejects as a Resolver mismatch.
const vehicleSchema = z.object({
  registration_number: z.string().min(3, 'Registration number is required'),
  name: z.string().min(2, 'Name is required'),
  type: z.enum(['truck', 'van', 'mini_truck', 'trailer']),
  max_load_capacity_kg: z.number().positive('Must be greater than 0'),
  odometer_km: z.number().min(0, 'Cannot be negative').optional(),
  acquisition_cost: z.number().positive('Must be greater than 0'),
  region: z.string().min(1, 'Region is required'),
});
type VehicleFormInputs = z.infer<typeof vehicleSchema>;

const EMPTY_VEHICLE_FORM: VehicleFormInputs = {
  registration_number: '',
  name: '',
  type: 'truck',
  max_load_capacity_kg: undefined as unknown as number,
  odometer_km: undefined,
  acquisition_cost: undefined as unknown as number,
  region: 'North',
};

interface VehicleFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  vehicle: Vehicle | null; // null = create mode, otherwise edit mode
}

function VehicleFormModal({ isOpen, onClose, vehicle }: VehicleFormModalProps) {
  const queryClient = useQueryClient();
  const isEdit = vehicle !== null;

  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<VehicleFormInputs>({
    resolver: zodResolver(vehicleSchema),
    defaultValues: EMPTY_VEHICLE_FORM,
  });

  useEffect(() => {
    if (!isOpen) return;
    if (vehicle) {
      reset({
        registration_number: vehicle.registration_number,
        name: vehicle.name,
        type: vehicle.type,
        max_load_capacity_kg: Number(vehicle.max_load_capacity_kg),
        odometer_km: Number(vehicle.odometer_km),
        acquisition_cost: Number(vehicle.acquisition_cost),
        region: vehicle.region,
      });
    } else {
      reset(EMPTY_VEHICLE_FORM);
    }
  }, [isOpen, vehicle, reset]);

  const mutation = useMutation({
    mutationFn: (data: VehicleFormInputs) => {
      if (isEdit) {
        const patchable = {
          name: data.name,
          type: data.type,
          max_load_capacity_kg: data.max_load_capacity_kg,
          odometer_km: data.odometer_km,
          acquisition_cost: data.acquisition_cost,
          region: data.region,
        };
        return apiClient.patch(`/vehicles/${vehicle!.id}`, patchable).then((r) => r.data);
      }
      return apiClient.post('/vehicles', data).then((r) => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as ErrorEnvelope | undefined;
        const field = data?.error.field;
        if (field && isVehicleFormField(field)) {
          setError(field, { type: 'server', message: data!.error.message });
          return;
        }
        setError('registration_number', { type: 'server', message: data?.error?.message ?? 'Could not save vehicle.' });
      } else {
        setError('registration_number', { type: 'server', message: 'Could not save vehicle.' });
      }
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? `Edit ${vehicle?.registration_number}` : 'Add Vehicle'}>
      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <Controller
          name="registration_number"
          control={control}
          render={({ field }) => (
            <Input
              label="Registration No."
              placeholder="e.g. GJ01AB4521"
              error={errors.registration_number?.message}
              disabled={isEdit}
              hint={isEdit ? 'Registration number cannot be changed after creation.' : undefined}
              {...field}
            />
          )}
        />
        <Controller
          name="name"
          control={control}
          render={({ field }) => (
            <Input label="Name / Model" placeholder="e.g. BharatBenz 2823" error={errors.name?.message} {...field} />
          )}
        />
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="type"
            control={control}
            render={({ field }) => <Select label="Type" options={VEHICLE_TYPES} {...field} />}
          />
          <Controller
            name="region"
            control={control}
            render={({ field }) => (
              <Select label="Region" options={REGIONS.map((r) => ({ label: r, value: r }))} {...field} />
            )}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="max_load_capacity_kg"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input
                label="Max Load (kg)"
                type="number"
                onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                error={errors.max_load_capacity_kg?.message}
                {...field}
              />
            )}
          />
          <Controller
            name="odometer_km"
            control={control}
            render={({ field: { onChange, ...field } }) => (
              <Input
                label="Odometer (km)"
                type="number"
                placeholder="Optional"
                onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
                error={errors.odometer_km?.message}
                {...field}
              />
            )}
          />
        </div>
        <Controller
          name="acquisition_cost"
          control={control}
          render={({ field: { onChange, ...field } }) => (
            <Input
              label="Acquisition Cost (₹)"
              type="number"
              onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
              error={errors.acquisition_cost?.message}
              {...field}
            />
          )}
        />

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button type="submit" isLoading={mutation.isPending} className="bg-signal hover:bg-signal/90 text-white border-transparent">
            {isEdit ? 'Save Changes' : 'Add Vehicle'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export function FleetPage() {
  const { user } = useAuth();
  const isFM = user?.role === 'fleet_manager';
  const queryClient = useQueryClient();

  const [status, setStatus] = useState('');
  const [type, setType] = useState('');
  const [region, setRegion] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);

  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<{ action: 'retire' | 'unretire'; vehicle: Vehicle } | null>(null);
  const [bannerError, setBannerError] = useState<string | null>(null);

  // Debounce free-text search so we don't fire a request per keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      setQ(searchInput.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ['vehicles', { status, type, region, q, page }],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<Vehicle>>('/vehicles', {
          params: {
            status: status || undefined,
            type: type || undefined,
            region: region || undefined,
            q: q || undefined,
            page,
            page_size: PAGE_SIZE,
          },
        })
        .then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  const lifecycleMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: 'retire' | 'unretire' }) =>
      apiClient.post(`/vehicles/${id}/${action}`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vehicles'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      setBannerError(null);
      setConfirmTarget(null);
    },
    onError: (err) => {
      setBannerError(getErrorMessage(err, 'Could not update this vehicle.'));
      setConfirmTarget(null);
    },
  });

  const vehicles = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const columnCount = isFM ? 9 : 8;

  return (
    <div className="space-y-6">
      {bannerError && (
        <div className="flex items-start justify-between rounded-md border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{bannerError}</span>
          </div>
          <button onClick={() => setBannerError(null)} aria-label="Dismiss" className="text-danger/70 hover:text-danger">
            ✕
          </button>
        </div>
      )}

      {/* Top Bar / Filters */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex flex-wrap gap-4">
          <div className="w-44">
            <Select
              value={type}
              onChange={(e) => {
                setType(e.target.value);
                setPage(1);
              }}
              options={[{ label: 'Type: All', value: '' }, ...VEHICLE_TYPES]}
            />
          </div>
          <div className="w-44">
            <Select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              options={[{ label: 'Status: All', value: '' }, ...VEHICLE_STATUSES]}
            />
          </div>
          <div className="w-44">
            <Select
              value={region}
              onChange={(e) => {
                setRegion(e.target.value);
                setPage(1);
              }}
              options={[{ label: 'Region: All', value: '' }, ...REGIONS.map((r) => ({ label: r, value: r }))]}
            />
          </div>
          <div className="w-64">
            <Input
              placeholder="Search reg. no. / name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
        </div>

        {isFM && (
          <Button
            onClick={() => {
              setEditingVehicle(null);
              setIsFormOpen(true);
            }}
            className="bg-signal hover:bg-signal/90 text-white border-transparent"
          >
            + Add Vehicle
          </Button>
        )}
      </div>

      {/* Data Table */}
      <div className="rounded-md border border-line bg-surface-1 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-ink-mute text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4 font-medium">Reg. No.</th>
              <th className="px-6 py-4 font-medium">Name/Model</th>
              <th className="px-6 py-4 font-medium">Type</th>
              <th className="px-6 py-4 font-medium">Region</th>
              <th className="px-6 py-4 font-medium">Capacity</th>
              <th className="px-6 py-4 font-medium">Odometer</th>
              <th className="px-6 py-4 font-medium">Acq. Cost</th>
              <th className="px-6 py-4 font-medium">Status</th>
              {isFM && <th className="px-6 py-4 font-medium">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {isLoading && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-ink-mute">
                  <Loader2 className="h-5 w-5 animate-spin inline-block mr-2 align-middle" />
                  Loading vehicles...
                </td>
              </tr>
            )}
            {!isLoading && isError && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-danger">
                  Failed to load vehicles. Please try again.
                </td>
              </tr>
            )}
            {!isLoading && !isError && vehicles.length === 0 && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-ink-mute">
                  No vehicles match these filters.
                </td>
              </tr>
            )}
            {!isLoading &&
              !isError &&
              vehicles.map((vehicle) => (
                <tr key={vehicle.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-6 py-4 font-data text-ink">{vehicle.registration_number}</td>
                  <td className="px-6 py-4 text-ink">{vehicle.name}</td>
                  <td className="px-6 py-4 text-ink-mute">{typeLabel(vehicle.type)}</td>
                  <td className="px-6 py-4 text-ink-mute">{vehicle.region}</td>
                  <td className="px-6 py-4 font-data text-ink-mute">
                    {Number(vehicle.max_load_capacity_kg).toLocaleString('en-IN')} kg
                  </td>
                  <td className="px-6 py-4 font-data text-ink-mute">
                    {Number(vehicle.odometer_km).toLocaleString('en-IN')} km
                  </td>
                  <td className="px-6 py-4 font-data text-ink-mute">{formatINR(vehicle.acquisition_cost)}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={vehicle.status} />
                  </td>
                  {isFM && (
                    <td className="px-6 py-4 space-x-3 whitespace-nowrap">
                      <button
                        onClick={() => {
                          setEditingVehicle(vehicle);
                          setIsFormOpen(true);
                        }}
                        className="text-signal hover:underline font-medium text-sm"
                      >
                        Edit
                      </button>
                      {vehicle.status === 'retired' ? (
                        <button
                          onClick={() => setConfirmTarget({ action: 'unretire', vehicle })}
                          className="text-ok hover:underline font-medium text-sm"
                        >
                          Unretire
                        </button>
                      ) : (
                        <button
                          onClick={() => setConfirmTarget({ action: 'retire', vehicle })}
                          className="text-danger hover:underline font-medium text-sm"
                        >
                          Retire
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm text-ink-mute">
        <span>
          {total === 0
            ? '0 vehicles'
            : `Showing ${(page - 1) * PAGE_SIZE + 1}-${Math.min(page * PAGE_SIZE, total)} of ${total} vehicles`}
          {isFetching && !isLoading && ' · refreshing...'}
        </span>
        <div className="flex items-center space-x-2">
          <Button variant="secondary" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span>
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page >= totalPages}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Helper text */}
      <div className="text-xs text-signal">
        Rule: Registration No. must be unique • Retired/In Shop vehicles are hidden from Trip Dispatcher
      </div>

      <VehicleFormModal isOpen={isFormOpen} onClose={() => setIsFormOpen(false)} vehicle={editingVehicle} />

      {confirmTarget && (
        <ConfirmDialog
          isOpen={true}
          title={confirmTarget.action === 'retire' ? 'Retire Vehicle' : 'Unretire Vehicle'}
          message={
            confirmTarget.action === 'retire'
              ? `Retire ${confirmTarget.vehicle.registration_number}? It will be hidden from the Trip Dispatcher.`
              : `Unretire ${confirmTarget.vehicle.registration_number}? It will become available again.`
          }
          confirmText={confirmTarget.action === 'retire' ? 'Retire' : 'Unretire'}
          isDestructive={confirmTarget.action === 'retire'}
          onConfirm={() => lifecycleMutation.mutate({ id: confirmTarget.vehicle.id, action: confirmTarget.action })}
          onCancel={() => setConfirmTarget(null)}
        />
      )}
    </div>
  );
}
