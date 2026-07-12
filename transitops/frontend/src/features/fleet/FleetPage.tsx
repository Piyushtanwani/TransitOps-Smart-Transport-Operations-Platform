import { Select } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';

const vehicles = [
  { regNo: 'GJ01AB4521', name: 'VAN-05', type: 'Van', capacity: '500 kg', odometer: '74,000', cost: '6,20,000', status: 'Available', statusColor: 'bg-ok text-surface-0' },
  { regNo: 'GJ01AB9912', name: 'TRUCK-11', type: 'Truck', capacity: '5 Ton', odometer: '182,000', cost: '24,50,000', status: 'On Trip', statusColor: 'bg-info text-surface-0' },
  { regNo: 'GJ01AB1120', name: 'MINI-03', type: 'Mini', capacity: '1 Ton', odometer: '66,000', cost: '4,10,000', status: 'In Shop', statusColor: 'bg-signal text-surface-0' },
  { regNo: 'GJ01AB008', name: 'VAN-09', type: 'Van', capacity: '750 kg', odometer: '241,900', cost: '5,90,000', status: 'Retired', statusColor: 'bg-danger text-surface-0' },
];

export function FleetPage() {
  return (
    <div className="space-y-6">
      {/* Top Bar / Filters */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-4">
          <div className="w-48">
            <Select
              options={[{ label: 'Type: All', value: 'all' }]}
            />
          </div>
          <div className="w-48">
            <Select
              options={[{ label: 'Status: All', value: 'all' }]}
            />
          </div>
          <div className="w-64">
            <Input
              placeholder="Search reg. no..."
            />
          </div>
        </div>
        
        <Button className="bg-signal hover:bg-signal/90 text-white border-transparent">
          + Add Vehicle
        </Button>
      </div>

      {/* Data Table */}
      <div className="rounded-md border border-surface-2 bg-surface-1 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-on-surface-variant text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4 font-medium">REG. NO. (UNIQUE)</th>
              <th className="px-6 py-4 font-medium">NAME/MODEL</th>
              <th className="px-6 py-4 font-medium">TYPE</th>
              <th className="px-6 py-4 font-medium">CAPACITY</th>
              <th className="px-6 py-4 font-medium">ODOMETER</th>
              <th className="px-6 py-4 font-medium">ACQ. COST</th>
              <th className="px-6 py-4 font-medium">STATUS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-2">
            {vehicles.map((vehicle, idx) => (
              <tr key={idx} className="hover:bg-surface-2/50 transition-colors">
                <td className="px-6 py-4 font-data">{vehicle.regNo}</td>
                <td className="px-6 py-4">{vehicle.name}</td>
                <td className="px-6 py-4">{vehicle.type}</td>
                <td className="px-6 py-4">{vehicle.capacity}</td>
                <td className="px-6 py-4 font-data">{vehicle.odometer}</td>
                <td className="px-6 py-4 font-data">{vehicle.cost}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${vehicle.statusColor}`}>
                    {vehicle.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Helper text */}
      <div className="text-xs text-signal">
        Rule: Registration No. must be unique • Retired/In Shop vehicles are hidden from Trip Dispatcher
      </div>
    </div>
  );
}
