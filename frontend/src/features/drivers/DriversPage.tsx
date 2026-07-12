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
import { DateInput } from '../../components/ui/DateInput';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { ScoreBar } from '../../components/ui/ScoreBar';

// ---- Local types (mirrors docs/03-API-SPEC.md §4 Drivers — api/client.ts + types/api.ts stay untouched) ----
type DriverStatus = 'available' | 'on_trip' | 'off_duty' | 'suspended';
type SettableDriverStatus = 'available' | 'off_duty' | 'suspended';

interface Driver {
  id: string;
  full_name: string;
  license_number: string;
  license_category: string;
  license_expiry: string; // ISO date, e.g. "2026-08-06"
  contact_number: string;
  safety_score: string;
  status: DriverStatus;
  created_at: string;
  updated_at?: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

const DRIVER_STATUSES: { label: string; value: DriverStatus }[] = [
  { label: 'Available', value: 'available' },
  { label: 'On Trip', value: 'on_trip' },
  { label: 'Off Duty', value: 'off_duty' },
  { label: 'Suspended', value: 'suspended' },
];

const LICENSE_CATEGORIES = ['LMV', 'HMV', 'MCWG'];

const SETTABLE_STATUSES: { label: string; value: SettableDriverStatus }[] = [
  { label: 'Set Available', value: 'available' },
  { label: 'Set Off Duty', value: 'off_duty' },
  { label: 'Suspend', value: 'suspended' },
];

const PAGE_SIZE = 10;
const MS_PER_DAY = 86_400_000;

function daysUntil(dateStr: string): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const expiry = new Date(`${dateStr}T00:00:00`);
  return Math.round((expiry.getTime() - today.getTime()) / MS_PER_DAY);
}

function LicenseExpiryBadge({ expiry }: { expiry: string }) {
  const diff = daysUntil(expiry);
  const formatted = new Date(`${expiry}T00:00:00`).toLocaleDateString('en-IN', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });

  if (diff < 0) {
    return <span className="font-data text-danger font-bold uppercase">{formatted} · Expired</span>;
  }
  if (diff <= 30) {
    return (
      <span className="font-data text-warn font-bold">
        {formatted} · {diff}d left
      </span>
    );
  }
  return <span className="font-data text-ink-mute">{formatted}</span>;
}

function getErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as ErrorEnvelope | undefined;
    if (data?.error?.message) return data.error.message;
  }
  return fallback;
}

const DRIVER_FORM_FIELDS = [
  'full_name',
  'license_number',
  'license_category',
  'license_expiry',
  'contact_number',
  'safety_score',
] as const;
type DriverFormField = (typeof DRIVER_FORM_FIELDS)[number];
function isDriverFormField(x: string): x is DriverFormField {
  return (DRIVER_FORM_FIELDS as readonly string[]).includes(x);
}

// Note: plain z.number() (not z.coerce) — the <Input type="number"> onChange handler below
// already converts to a real number via valueAsNumber before it reaches RHF/zod, and using
// z.coerce here would make zodResolver's inferred *input* type diverge from DriverFormInputs
// (its output type), which useForm<DriverFormInputs> then rejects as a Resolver mismatch.
const driverSchema = z.object({
  full_name: z.string().min(2, 'Full name is required'),
  license_number: z.string().min(3, 'License number is required'),
  license_category: z.string().min(1, 'Category is required'),
  license_expiry: z.string().min(1, 'Expiry date is required'),
  contact_number: z.string().min(7, 'Contact number is required'),
  safety_score: z.number().min(0, 'Must be 0-100').max(100, 'Must be 0-100').optional(),
});
type DriverFormInputs = z.infer<typeof driverSchema>;

const EMPTY_DRIVER_FORM: DriverFormInputs = {
  full_name: '',
  license_number: '',
  license_category: 'LMV',
  license_expiry: '',
  contact_number: '',
  safety_score: 100,
};

interface AddDriverModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function AddDriverModal({ isOpen, onClose }: AddDriverModalProps) {
  const queryClient = useQueryClient();
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<DriverFormInputs>({
    resolver: zodResolver(driverSchema),
    defaultValues: EMPTY_DRIVER_FORM,
  });

  useEffect(() => {
    if (isOpen) reset(EMPTY_DRIVER_FORM);
  }, [isOpen, reset]);

  const mutation = useMutation({
    mutationFn: (data: DriverFormInputs) => apiClient.post('/drivers', data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      onClose();
    },
    onError: (err) => {
      if (axios.isAxiosError(err)) {
        const data = err.response?.data as ErrorEnvelope | undefined;
        const field = data?.error.field;
        if (field && isDriverFormField(field)) {
          setError(field, { type: 'server', message: data!.error.message });
          return;
        }
        setError('license_number', { type: 'server', message: data?.error?.message ?? 'Could not save driver.' });
      } else {
        setError('license_number', { type: 'server', message: 'Could not save driver.' });
      }
    },
  });

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Add Driver">
      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-4">
        <Controller
          name="full_name"
          control={control}
          render={({ field }) => (
            <Input label="Full Name" placeholder="e.g. Alex Kumar" error={errors.full_name?.message} {...field} />
          )}
        />
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="license_number"
            control={control}
            render={({ field }) => (
              <Input
                label="License No."
                placeholder="e.g. MH-HMV-2020-1234"
                error={errors.license_number?.message}
                {...field}
              />
            )}
          />
          <Controller
            name="license_category"
            control={control}
            render={({ field }) => (
              <Select label="Category" options={LICENSE_CATEGORIES.map((c) => ({ label: c, value: c }))} {...field} />
            )}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Controller
            name="license_expiry"
            control={control}
            render={({ field }) => <DateInput label="License Expiry" error={errors.license_expiry?.message} {...field} />}
          />
          <Controller
            name="contact_number"
            control={control}
            render={({ field }) => (
              <Input
                label="Contact Number"
                placeholder="e.g. 9876543210"
                error={errors.contact_number?.message}
                {...field}
              />
            )}
          />
        </div>
        <Controller
          name="safety_score"
          control={control}
          render={({ field: { onChange, ...field } }) => (
            <Input
              label="Safety Score (0-100)"
              type="number"
              placeholder="Optional, defaults to 100"
              onChange={(e) => onChange(e.target.valueAsNumber || undefined)}
              error={errors.safety_score?.message}
              {...field}
            />
          )}
        />

        <div className="flex justify-end space-x-3 pt-4 border-t border-line">
          <Button variant="ghost" onClick={onClose} type="button">
            Cancel
          </Button>
          <Button type="submit" isLoading={mutation.isPending} className="bg-signal hover:bg-signal/90 text-white border-transparent">
            Add Driver
          </Button>
        </div>
      </form>
    </Modal>
  );
}

export function DriversPage() {
  const { user } = useAuth();
  const canManage = user?.role === 'fleet_manager' || user?.role === 'safety_officer';
  const queryClient = useQueryClient();

  const [status, setStatus] = useState('');
  const [licenseValid, setLicenseValid] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [bannerError, setBannerError] = useState<string | null>(null);

  useEffect(() => {
    const handle = setTimeout(() => {
      setQ(searchInput.trim());
      setPage(1);
    }, 400);
    return () => clearTimeout(handle);
  }, [searchInput]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ['drivers', { status, licenseValid, q, page }],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<Driver>>('/drivers', {
          params: {
            status: status || undefined,
            license_valid: licenseValid || undefined,
            q: q || undefined,
            page,
            page_size: PAGE_SIZE,
          },
        })
        .then((r) => r.data),
    placeholderData: keepPreviousData,
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status: nextStatus }: { id: string; status: SettableDriverStatus }) =>
      apiClient.post(`/drivers/${id}/status`, { status: nextStatus }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['drivers'] });
      queryClient.invalidateQueries({ queryKey: ['kpis'] });
      setBannerError(null);
    },
    onError: (err) => {
      setBannerError(getErrorMessage(err, 'Could not update driver status.'));
    },
  });

  const drivers = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const columnCount = canManage ? 8 : 7;

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
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
              options={[{ label: 'Status: All', value: '' }, ...DRIVER_STATUSES]}
            />
          </div>
          <div className="w-44">
            <Select
              value={licenseValid}
              onChange={(e) => {
                setLicenseValid(e.target.value);
                setPage(1);
              }}
              options={[
                { label: 'License: All', value: '' },
                { label: 'Valid', value: 'true' },
                { label: 'Expired', value: 'false' },
              ]}
            />
          </div>
          <div className="w-64">
            <Input
              placeholder="Search name / license no..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
            />
          </div>
        </div>

        {canManage && (
          <Button onClick={() => setIsAddOpen(true)} className="bg-signal hover:bg-signal/90 text-white border-transparent">
            + Add Driver
          </Button>
        )}
      </div>

      {/* Data Table */}
      <div className="rounded-md border border-line bg-surface-1 overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-ink-mute text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4 font-medium">Driver</th>
              <th className="px-6 py-4 font-medium">License No</th>
              <th className="px-6 py-4 font-medium">Category</th>
              <th className="px-6 py-4 font-medium">Expiry</th>
              <th className="px-6 py-4 font-medium">Contact</th>
              <th className="px-6 py-4 font-medium">Safety</th>
              <th className="px-6 py-4 font-medium">Status</th>
              {canManage && <th className="px-6 py-4 font-medium">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {isLoading && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-ink-mute">
                  <Loader2 className="h-5 w-5 animate-spin inline-block mr-2 align-middle" />
                  Loading drivers...
                </td>
              </tr>
            )}
            {!isLoading && isError && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-danger">
                  Failed to load drivers. Please try again.
                </td>
              </tr>
            )}
            {!isLoading && !isError && drivers.length === 0 && (
              <tr>
                <td colSpan={columnCount} className="px-6 py-10 text-center text-ink-mute">
                  No drivers match these filters.
                </td>
              </tr>
            )}
            {!isLoading &&
              !isError &&
              drivers.map((driver) => (
                <tr key={driver.id} className="hover:bg-surface-2/50 transition-colors">
                  <td className="px-6 py-4 text-ink">{driver.full_name}</td>
                  <td className="px-6 py-4 font-data text-ink-mute">{driver.license_number}</td>
                  <td className="px-6 py-4 text-ink-mute">{driver.license_category}</td>
                  <td className="px-6 py-4">
                    <LicenseExpiryBadge expiry={driver.license_expiry} />
                  </td>
                  <td className="px-6 py-4 font-data text-ink-mute">{driver.contact_number}</td>
                  <td className="px-6 py-4">
                    <ScoreBar score={Number(driver.safety_score)} />
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={driver.status} />
                  </td>
                  {canManage && (
                    <td className="px-6 py-4 space-x-3 whitespace-nowrap">
                      {SETTABLE_STATUSES.filter((s) => s.value !== driver.status).map((s) => (
                        <button
                          key={s.value}
                          onClick={() => statusMutation.mutate({ id: driver.id, status: s.value })}
                          className="text-signal hover:underline font-medium text-sm"
                        >
                          {s.label}
                        </button>
                      ))}
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
            ? '0 drivers'
            : `Showing ${(page - 1) * PAGE_SIZE + 1}-${Math.min(page * PAGE_SIZE, total)} of ${total} drivers`}
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

      <div className="text-xs text-signal">
        Rule: Expired license or Suspended status → blocked from trip assignment
      </div>

      <AddDriverModal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} />
    </div>
  );
}
