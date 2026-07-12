import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { AlertTriangle } from 'lucide-react';
import { apiClient } from '../../api/client';
import { Select } from '../../components/ui/Select';
import { Card, CardContent } from '../../components/ui/Card';
import { STATUS_META } from '../../components/ui/StatusBadge';

// ---- Local types (mirrors docs/03-API-SPEC.md §4 Dashboard & Reports) ----
interface DashboardKpis {
  active_vehicles: number;
  available_vehicles: number;
  in_maintenance: number;
  active_trips: number;
  pending_trips: number;
  drivers_on_duty: number;
  fleet_utilization_pct: number;
  alerts: { expiring_licenses: number };
}

interface TripsPoint {
  date: string;
  completed: number;
  dispatched: number;
}

interface CostPoint {
  vehicle: string;
  fuel: number;
  maintenance: number;
}

interface StatusPoint {
  status: string;
  count: number;
}

interface DashboardCharts {
  trips_last_14d: TripsPoint[];
  cost_breakdown: CostPoint[];
  status_distribution: StatusPoint[];
}

const VEHICLE_TYPES = [
  { label: 'Truck', value: 'truck' },
  { label: 'Van', value: 'van' },
  { label: 'Mini Truck', value: 'mini_truck' },
  { label: 'Trailer', value: 'trailer' },
];

const VEHICLE_STATUSES = [
  { label: 'Available', value: 'available' },
  { label: 'On Trip', value: 'on_trip' },
  { label: 'In Shop', value: 'in_shop' },
  { label: 'Retired', value: 'retired' },
];

const REGIONS = ['North', 'South', 'East', 'West'];

const STATUS_COLORS: Record<string, string> = {
  available: 'var(--color-ok)',
  on_trip: 'var(--color-info)',
  in_shop: 'var(--color-warn)',
  retired: 'var(--color-neutral)',
};

const KPI_TILES: { key: keyof Omit<DashboardKpis, 'alerts'>; label: string; borderClass: string; suffix?: string }[] = [
  { key: 'active_vehicles', label: 'ACTIVE VEHICLES', borderClass: 'border-l-info' },
  { key: 'available_vehicles', label: 'AVAILABLE VEHICLES', borderClass: 'border-l-ok' },
  { key: 'in_maintenance', label: 'VEHICLES IN MAINTENANCE', borderClass: 'border-l-signal' },
  { key: 'active_trips', label: 'ACTIVE TRIPS', borderClass: 'border-l-info' },
  { key: 'pending_trips', label: 'PENDING TRIPS', borderClass: 'border-l-info' },
  { key: 'drivers_on_duty', label: 'DRIVERS ON DUTY', borderClass: 'border-l-info' },
  { key: 'fleet_utilization_pct', label: 'FLEET UTILIZATION', borderClass: 'border-l-ok', suffix: '%' },
];

const tooltipContentStyle = {
  backgroundColor: 'var(--color-surface-2)',
  border: '1px solid var(--color-line)',
  borderRadius: 8,
  fontSize: 12,
};
const tooltipLabelStyle = { color: 'var(--color-ink)', fontWeight: 600 };
const tooltipItemStyle = { color: 'var(--color-ink-mute)' };
const axisTick = { fill: 'var(--color-ink-mute)', fontSize: 11 };

function ChartStatus({ label }: { label: string }) {
  return <div className="h-full flex items-center justify-center text-ink-mute text-sm">{label}</div>;
}

export function DashboardPage() {
  const [type, setType] = useState('');
  const [status, setStatus] = useState('');
  const [region, setRegion] = useState('');

  const {
    data: kpis,
    isLoading: kpisLoading,
    isError: kpisError,
  } = useQuery({
    queryKey: ['kpis', { type, status, region }],
    queryFn: () =>
      apiClient
        .get<DashboardKpis>('/dashboard/kpis', {
          params: {
            type: type || undefined,
            status: status || undefined,
            region: region || undefined,
          },
        })
        .then((r) => r.data),
  });

  const {
    data: charts,
    isLoading: chartsLoading,
    isError: chartsError,
  } = useQuery({
    queryKey: ['charts'],
    queryFn: () => apiClient.get<DashboardCharts>('/dashboard/charts').then((r) => r.data),
  });

  const statusChartData =
    charts?.status_distribution.map((s) => ({
      ...s,
      label: STATUS_META[s.status]?.label ?? s.status.toUpperCase(),
    })) ?? [];

  return (
    <div className="space-y-8">
      {!kpisLoading && kpis && kpis.alerts.expiring_licenses > 0 && (
        <div className="flex items-center justify-between rounded-md border border-warn/40 bg-warn/10 px-4 py-3 text-sm text-warn">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            <span>
              {kpis.alerts.expiring_licenses} licence{kpis.alerts.expiring_licenses === 1 ? '' : 's'} expiring within 30
              days
            </span>
          </div>
          <Link to="/drivers" className="font-medium underline hover:no-underline">
            View drivers →
          </Link>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <span className="self-center text-xs font-medium uppercase tracking-wider text-ink-mute mr-2">Filters:</span>
        <div className="w-48">
          <Select value={type} onChange={(e) => setType(e.target.value)} options={[{ label: 'Vehicle Type: All', value: '' }, ...VEHICLE_TYPES]} />
        </div>
        <div className="w-48">
          <Select value={status} onChange={(e) => setStatus(e.target.value)} options={[{ label: 'Status: All', value: '' }, ...VEHICLE_STATUSES]} />
        </div>
        <div className="w-48">
          <Select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            options={[{ label: 'Region: All', value: '' }, ...REGIONS.map((r) => ({ label: r, value: r }))]}
          />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {KPI_TILES.map((tile) => (
          <Card key={tile.key} className={`border-l-4 ${tile.borderClass} rounded-md bg-surface-1`}>
            <CardContent className="p-4 flex flex-col justify-between h-full">
              <p className="text-xs font-medium uppercase tracking-wider text-ink-mute mb-2">{tile.label}</p>
              {kpisLoading ? (
                <div className="h-8 w-16 rounded bg-surface-2 animate-pulse" />
              ) : kpisError || !kpis ? (
                <p className="text-3xl font-heading font-semibold text-ink-mute">—</p>
              ) : (
                <p className="text-3xl font-heading font-semibold text-ink">
                  {kpis[tile.key]}
                  {tile.suffix ?? ''}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Trips last 14 days */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-ink-mute">Trips — Last 14 Days</h3>
          <div className="rounded-md border border-line bg-surface-1 p-4" style={{ height: 300 }}>
            {chartsLoading ? (
              <ChartStatus label="Loading chart..." />
            ) : chartsError || !charts ? (
              <div className="h-full flex items-center justify-center text-danger text-sm">Failed to load chart data.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={charts.trips_last_14d} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value) =>
                      new Date(`${value}T00:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
                    }
                    tick={axisTick}
                    stroke="var(--color-line)"
                  />
                  <YAxis allowDecimals={false} tick={axisTick} stroke="var(--color-line)" />
                  <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                  <Legend wrapperStyle={{ fontSize: 12, color: 'var(--color-ink-mute)' }} />
                  <Bar dataKey="dispatched" name="Dispatched" fill="var(--color-info)" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="completed" name="Completed" fill="var(--color-ok)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Vehicle Status distribution */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-ink-mute">Vehicle Status</h3>
          <div className="rounded-md border border-line bg-surface-1 p-4" style={{ height: 300 }}>
            {chartsLoading ? (
              <ChartStatus label="Loading chart..." />
            ) : chartsError || !charts ? (
              <div className="h-full flex items-center justify-center text-danger text-sm">Failed to load chart data.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={statusChartData} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} tick={axisTick} stroke="var(--color-line)" />
                  <YAxis type="category" dataKey="label" tick={axisTick} stroke="var(--color-line)" width={80} />
                  <Tooltip contentStyle={tooltipContentStyle} labelStyle={tooltipLabelStyle} itemStyle={tooltipItemStyle} />
                  <Bar dataKey="count" name="Vehicles" radius={[0, 3, 3, 0]}>
                    {statusChartData.map((entry) => (
                      <Cell key={entry.status} fill={STATUS_COLORS[entry.status] ?? 'var(--color-neutral)'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Cost breakdown */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium uppercase tracking-wider text-ink-mute">Cost Breakdown by Vehicle</h3>
        <div className="rounded-md border border-line bg-surface-1 p-4" style={{ height: 320 }}>
          {chartsLoading ? (
            <ChartStatus label="Loading chart..." />
          ) : chartsError || !charts ? (
            <div className="h-full flex items-center justify-center text-danger text-sm">Failed to load chart data.</div>
          ) : charts.cost_breakdown.length === 0 ? (
            <ChartStatus label="No cost data yet." />
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.cost_breakdown} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" horizontal={false} />
                <XAxis
                  type="number"
                  tick={axisTick}
                  stroke="var(--color-line)"
                  tickFormatter={(value) => `₹${Number(value).toLocaleString('en-IN')}`}
                />
                <YAxis type="category" dataKey="vehicle" tick={axisTick} stroke="var(--color-line)" width={110} />
                <Tooltip
                  formatter={(value, name) => [`₹${Number(value ?? 0).toLocaleString('en-IN')}`, name]}
                  contentStyle={tooltipContentStyle}
                  labelStyle={tooltipLabelStyle}
                  itemStyle={tooltipItemStyle}
                />
                <Legend wrapperStyle={{ fontSize: 12, color: 'var(--color-ink-mute)' }} />
                <Bar dataKey="fuel" name="Fuel" stackId="cost" fill="var(--color-info)" />
                <Bar dataKey="maintenance" name="Maintenance" stackId="cost" fill="var(--color-signal)" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
