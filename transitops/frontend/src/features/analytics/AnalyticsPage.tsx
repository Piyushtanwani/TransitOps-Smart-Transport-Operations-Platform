import { useMemo, useState, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios, { type AxiosError } from 'axios';
import { apiClient } from '../../api/client';
import { Button } from '../../components/ui/Button';
import type { ErrorEnvelope } from '../../types/api';

interface VehicleReportRow {
  id: string;
  registration_number: string;
  name: string;
  type: string;
  region: string;
  acquisition_cost: number;
  total_distance_km: number;
  total_liters: number;
  fuel_cost: number;
  maintenance_cost: number;
  other_expenses: number;
  operational_cost: number;
  revenue: number;
  fuel_efficiency_km_l: number | null;
  roi: number;
}

interface VehicleReportTotals {
  acquisition_cost: number;
  total_distance_km: number;
  total_liters: number;
  fuel_cost: number;
  maintenance_cost: number;
  other_expenses: number;
  operational_cost: number;
  revenue: number;
}

interface VehicleReportResponse {
  rows: VehicleReportRow[];
  totals: VehicleReportTotals;
}

const EMPTY_ROWS: VehicleReportRow[] = [];
const ZERO_TOTALS: VehicleReportTotals = {
  acquisition_cost: 0,
  total_distance_km: 0,
  total_liters: 0,
  fuel_cost: 0,
  maintenance_cost: 0,
  other_expenses: 0,
  operational_cost: 0,
  revenue: 0,
};

const currency = (n: number) => `₹${Math.round(n).toLocaleString()}`;
const km = (n: number) => `${n.toLocaleString(undefined, { maximumFractionDigits: 1 })} km`;
const liters = (n: number) => `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} L`;
const efficiency = (n: number | null) =>
  n === null ? '—' : `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} km/L`;
const roiPct = (n: number) => `${n > 0 ? '+' : ''}${(n * 100).toFixed(2)}%`;

function errorEnvelope(error: unknown) {
  if (axios.isAxiosError<ErrorEnvelope>(error)) {
    return error.response?.data?.error;
  }
  return undefined;
}

function messageFor(error: unknown): string {
  return errorEnvelope(error)?.message ?? 'Something went wrong loading the report.';
}

function isForbidden(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 403;
}

function filenameFromDisposition(header: unknown): string | null {
  if (typeof header !== 'string') return null;
  const match = /filename="?([^";]+)"?/i.exec(header);
  return match?.[1] ?? null;
}

export function AnalyticsPage() {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const { data, isLoading, isFetching, isError, error, refetch } = useQuery<
    VehicleReportResponse,
    AxiosError<ErrorEnvelope>
  >({
    queryKey: ['reports', 'vehicles'],
    queryFn: async () => {
      const res = await apiClient.get<VehicleReportResponse>('/reports/vehicles');
      return res.data;
    },
    retry: (failureCount, err) => !isForbidden(err) && failureCount < 2,
  });

  const rows = data?.rows ?? EMPTY_ROWS;
  const totals = data?.totals ?? ZERO_TOTALS;
  const forbidden = isError && isForbidden(error);

  const rankedByRoi = useMemo(() => [...rows].sort((a, b) => b.roi - a.roi), [rows]);
  const maxAbsRoi = useMemo(() => Math.max(0.01, ...rows.map((r) => Math.abs(r.roi))), [rows]);
  const fleetEfficiency = useMemo(() => {
    if (totals.total_liters <= 0) return null;
    return totals.total_distance_km / totals.total_liters;
  }, [totals]);

  const handleExportCSV = async () => {
    setDownloadError(null);
    setIsDownloading(true);
    try {
      const res = await apiClient.get<Blob>('/reports/vehicles.csv', { responseType: 'blob' });
      const filename = filenameFromDisposition(res.headers['content-disposition']) ?? 'transitops_vehicle_report.csv';
      const url = window.URL.createObjectURL(res.data);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError(isForbidden(err) ? 'Reports are available to Finance and Fleet Managers' : messageFor(err));
    } finally {
      setIsDownloading(false);
    }
  };

  let content: ReactNode;
  if (forbidden) {
    content = (
      <div className="p-12 rounded-xl border border-line bg-surface-1 text-center">
        <p className="text-sm text-ink-mute">Reports are available to Finance and Fleet Managers</p>
      </div>
    );
  } else if (isLoading) {
    content = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[0, 1, 2].map((i) => (
            <div key={i} className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm animate-pulse">
              <div className="h-3 w-24 bg-surface-2 rounded mb-3" />
              <div className="h-7 w-32 bg-surface-2 rounded" />
            </div>
          ))}
        </div>
        <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm mt-6 animate-pulse">
          <div className="h-4 w-40 bg-surface-2 rounded mb-6" />
          <div className="space-y-3">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className="h-3 bg-surface-2 rounded" />
            ))}
          </div>
        </div>
      </>
    );
  } else if (isError) {
    content = (
      <div className="p-6 rounded-xl border border-line bg-surface-1 text-center space-y-3">
        <p className="text-sm text-ink-mute">{messageFor(error)}</p>
        <Button onClick={() => refetch()} className="bg-surface-2 text-ink hover:bg-surface-3 border-line">
          Retry
        </Button>
      </div>
    );
  } else {
    content = (
      <>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
            <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Total Revenue</p>
            <p className="text-3xl font-data text-ink">{currency(totals.revenue)}</p>
            <p className="text-xs text-ink-mute mt-2">
              Across {rows.length} vehicle{rows.length === 1 ? '' : 's'}
            </p>
          </div>
          <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
            <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Total Operational Cost</p>
            <p className="text-3xl font-data text-ink">{currency(totals.operational_cost)}</p>
            <p className="text-xs text-ink-mute mt-2">Fuel + maintenance + other</p>
          </div>
          <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
            <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Fleet Fuel Efficiency</p>
            <p className="text-3xl font-data text-ink">{efficiency(fleetEfficiency)}</p>
            <p className="text-xs text-ink-mute mt-2">Fleet-wide average</p>
          </div>
        </div>

        <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm mt-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="font-semibold text-ink">ROI by Vehicle</h3>
            {isFetching && <span className="text-xs text-ink-mute">Refreshing…</span>}
          </div>

          {rankedByRoi.length === 0 ? (
            <p className="text-sm text-ink-mute text-center py-8">No vehicle data yet.</p>
          ) : (
            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
              {rankedByRoi.map((row) => (
                <div key={row.id} className="flex items-center gap-3">
                  <div className="w-36 shrink-0">
                    <p className="text-xs font-data text-ink truncate">{row.registration_number}</p>
                    <p className="text-[11px] text-ink-mute truncate">{row.name}</p>
                  </div>
                  <div className="flex-1 h-3 bg-surface-2 rounded-sm overflow-hidden">
                    <div
                      className={`h-full rounded-sm opacity-80 ${row.roi >= 0 ? 'bg-ok' : 'bg-danger'}`}
                      style={{ width: `${Math.min(100, (Math.abs(row.roi) / maxAbsRoi) * 100)}%` }}
                    />
                  </div>
                  <div
                    className={`w-20 shrink-0 text-right text-xs font-data ${row.roi >= 0 ? 'text-ok' : 'text-danger'}`}
                  >
                    {roiPct(row.roi)}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-center space-x-6 mt-6 border-t border-line pt-4">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-ok rounded-sm opacity-80" />
              <span className="text-xs text-ink-mute">Positive ROI</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-danger rounded-sm opacity-80" />
              <span className="text-xs text-ink-mute">Negative ROI</span>
            </div>
          </div>
        </div>

        <div className="rounded-md border border-line bg-surface-1 overflow-hidden mt-6">
          <div className="p-4 bg-surface-2 border-b border-line">
            <h2 className="font-semibold text-ink text-sm uppercase tracking-wider">Vehicle Report</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface-2 text-ink-mute text-[11px] uppercase tracking-wider font-medium">
                <tr>
                  <th className="px-6 py-4">Reg. No.</th>
                  <th className="px-6 py-4">Name</th>
                  <th className="px-6 py-4">Type</th>
                  <th className="px-6 py-4">Region</th>
                  <th className="px-6 py-4">Distance</th>
                  <th className="px-6 py-4">Fuel (L)</th>
                  <th className="px-6 py-4">Fuel Cost</th>
                  <th className="px-6 py-4">Maintenance</th>
                  <th className="px-6 py-4">Other</th>
                  <th className="px-6 py-4">Op. Cost</th>
                  <th className="px-6 py-4">Revenue</th>
                  <th className="px-6 py-4">Efficiency</th>
                  <th className="px-6 py-4">ROI</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink">
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={13} className="px-6 py-8 text-center text-ink-mute">
                      No vehicle data yet.
                    </td>
                  </tr>
                ) : (
                  rows.map((row) => (
                    <tr key={row.id} className="hover:bg-surface-2/50 transition-colors">
                      <td className="px-6 py-4 font-data">{row.registration_number}</td>
                      <td className="px-6 py-4">{row.name}</td>
                      <td className="px-6 py-4 text-ink-mute capitalize">{row.type.replace(/_/g, ' ')}</td>
                      <td className="px-6 py-4 text-ink-mute">{row.region}</td>
                      <td className="px-6 py-4 font-data text-ink-mute">{km(row.total_distance_km)}</td>
                      <td className="px-6 py-4 font-data text-ink-mute">{liters(row.total_liters)}</td>
                      <td className="px-6 py-4 font-data">{currency(row.fuel_cost)}</td>
                      <td className="px-6 py-4 font-data">{currency(row.maintenance_cost)}</td>
                      <td className="px-6 py-4 font-data">{currency(row.other_expenses)}</td>
                      <td className="px-6 py-4 font-data font-medium">{currency(row.operational_cost)}</td>
                      <td className="px-6 py-4 font-data">{currency(row.revenue)}</td>
                      <td className="px-6 py-4 font-data text-ink-mute">{efficiency(row.fuel_efficiency_km_l)}</td>
                      <td className={`px-6 py-4 font-data font-medium ${row.roi >= 0 ? 'text-ok' : 'text-danger'}`}>
                        {roiPct(row.roi)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">Analytics & Reports</h1>
          <p className="text-sm text-ink-mute mt-1">Financial performance and fleet metrics</p>
        </div>
        {!forbidden && (
          <Button
            onClick={handleExportCSV}
            isLoading={isDownloading}
            disabled={isLoading}
            className="bg-surface-2 text-ink hover:bg-surface-3 border-line"
          >
            Export CSV
          </Button>
        )}
      </div>

      {downloadError && <div className="text-xs text-danger">{downloadError}</div>}

      {content}
    </div>
  );
}
