import { Select } from '../../components/ui/Select';
import { Card, CardContent } from '../../components/ui/Card';

const kpiData = [
  { label: 'ACTIVE VEHICLES', value: '53', color: 'border-l-info' },
  { label: 'AVAILABLE VEHICLES', value: '42', color: 'border-l-ok' },
  { label: 'VEHICLES IN MAINTENANCE', value: '05', color: 'border-l-signal' },
  { label: 'ACTIVE TRIPS', value: '18', color: 'border-l-info' },
  { label: 'PENDING TRIPS', value: '09', color: 'border-l-info' },
  { label: 'DRIVERS ON DUTY', value: '26', color: 'border-l-info' },
  { label: 'FLEET UTILIZATION', value: '81%', color: 'border-l-ok' },
];

const recentTrips = [
  { trip: 'TR001', vehicle: 'VAN-05', driver: 'Alex', status: 'On Trip', statusColor: 'bg-info text-surface-0', eta: '45 min' },
  { trip: 'TR002', vehicle: 'TRK-12', driver: 'John', status: 'Completed', statusColor: 'bg-ok text-surface-0', eta: '--' },
  { trip: 'TR003', vehicle: 'MINI-08', driver: 'Priya', status: 'Dispatched', statusColor: 'bg-info/80 text-surface-0', eta: '1h 10m' },
  { trip: 'TR004', vehicle: '--', driver: '--', status: 'Draft', statusColor: 'bg-surface-2 text-on-surface', eta: 'Awaiting vehicle' },
];

const vehicleStatus = [
  { label: 'Available', percent: 70, color: 'bg-ok' },
  { label: 'On Trip', percent: 25, color: 'bg-info' },
  { label: 'In Shop', percent: 10, color: 'bg-signal' },
  { label: 'Retired', percent: 5, color: 'bg-danger' },
];

export function DashboardPage() {
  return (
    <div className="space-y-8">
      {/* Filters */}
      <div className="flex space-x-4">
        <span className="self-center text-xs font-medium uppercase tracking-wider text-on-surface-variant mr-2">Filters:</span>
        <div className="w-48">
          <Select
            options={[{ label: 'Vehicle Type: All', value: 'all' }]}
          />
        </div>
        <div className="w-48">
          <Select
            options={[{ label: 'Status: All', value: 'all' }]}
          />
        </div>
        <div className="w-48">
          <Select
            options={[{ label: 'Region: All', value: 'all' }]}
          />
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        {kpiData.map((kpi, idx) => (
          <Card key={idx} className={`border-l-4 ${kpi.color} rounded-md bg-surface-1`}>
            <CardContent className="p-4 flex flex-col justify-between h-full">
              <p className="text-xs font-medium uppercase tracking-wider text-on-surface-variant mb-2">
                {kpi.label}
              </p>
              <p className="text-3xl font-heading font-semibold text-on-surface">
                {kpi.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Trips Table */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-on-surface-variant">Recent Trips</h3>
          <div className="rounded-md border border-surface-2 bg-surface-1 overflow-hidden">
            <table className="w-full text-sm text-left">
              <thead className="bg-surface-2 text-on-surface-variant text-xs uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3 font-medium">Trip</th>
                  <th className="px-6 py-3 font-medium">Vehicle</th>
                  <th className="px-6 py-3 font-medium">Driver</th>
                  <th className="px-6 py-3 font-medium">Status</th>
                  <th className="px-6 py-3 font-medium">ETA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-2">
                {recentTrips.map((trip, idx) => (
                  <tr key={idx} className="hover:bg-surface-2/50 transition-colors">
                    <td className="px-6 py-4 font-data">{trip.trip}</td>
                    <td className="px-6 py-4">{trip.vehicle}</td>
                    <td className="px-6 py-4">{trip.driver}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${trip.statusColor}`}>
                        {trip.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">{trip.eta}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Vehicle Status Chart */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium uppercase tracking-wider text-on-surface-variant">Vehicle Status</h3>
          <div className="space-y-6 mt-4">
            {vehicleStatus.map((stat, idx) => (
              <div key={idx} className="flex items-center">
                <div className="w-24 text-sm text-on-surface">{stat.label}</div>
                <div className="flex-1 h-4 bg-surface-2 rounded-sm overflow-hidden flex">
                  <div 
                    className={`h-full ${stat.color} transition-all duration-500`}
                    style={{ width: `${stat.percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
