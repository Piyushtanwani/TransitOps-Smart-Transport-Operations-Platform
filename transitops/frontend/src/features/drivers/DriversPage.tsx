import { Button } from '../../components/ui/Button';

const drivers = [
  { name: 'Alex', license: 'DL-88213', category: 'LMV', expiry: '12/2028', contact: '98765xxxx', tripCompl: '96%', safety: 'Available', safetyColor: 'bg-ok text-surface-0', status: 'Available', statusColor: 'bg-ok text-surface-0' },
  { name: 'John', license: 'DL-44120', category: 'HMV', expiry: '03/2025 EXPIRE', contact: '98220xxxx', tripCompl: '81%', safety: 'Suspended', safetyColor: 'bg-signal text-surface-0', status: 'Suspended', statusColor: 'bg-signal text-surface-0' },
  { name: 'Priya', license: 'DL-77031', category: 'LMV', expiry: '08/202...', contact: '99110xxxx', tripCompl: '99%', safety: 'On Trip', safetyColor: 'bg-info text-surface-0', status: 'On Trip', statusColor: 'bg-info text-surface-0' },
  { name: 'Suresh', license: 'DL-90045', category: 'HMV', expiry: '01/2027', contact: '97410xxxx', tripCompl: '88%', safety: 'Available', safetyColor: 'bg-ok text-surface-0', status: 'Off Duty', statusColor: 'bg-surface-2 text-on-surface' },
];

export function DriversPage() {
  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex items-center justify-end">
        <Button className="bg-signal hover:bg-signal/90 text-white border-transparent">
          + Add Driver
        </Button>
      </div>

      {/* Data Table */}
      <div className="rounded-md border border-surface-2 bg-surface-1 overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-surface-2 text-on-surface-variant text-xs uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4 font-medium">DRIVER</th>
              <th className="px-6 py-4 font-medium">LICENSE NO</th>
              <th className="px-6 py-4 font-medium">CATEGORY</th>
              <th className="px-6 py-4 font-medium">EXPIRY</th>
              <th className="px-6 py-4 font-medium">CONTACT</th>
              <th className="px-6 py-4 font-medium">TRIP COMPL.</th>
              <th className="px-6 py-4 font-medium">SAFETY</th>
              <th className="px-6 py-4 font-medium">STATUS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-2">
            {drivers.map((driver, idx) => (
              <tr key={idx} className="hover:bg-surface-2/50 transition-colors">
                <td className="px-6 py-4">{driver.name}</td>
                <td className="px-6 py-4 font-data">{driver.license}</td>
                <td className="px-6 py-4">{driver.category}</td>
                <td className="px-6 py-4 font-data">
                  {driver.expiry.includes('EXPIRE') ? (
                    <span className="text-on-surface uppercase font-bold">{driver.expiry}</span>
                  ) : (
                    driver.expiry
                  )}
                </td>
                <td className="px-6 py-4 font-data">{driver.contact}</td>
                <td className="px-6 py-4 font-data">{driver.tripCompl}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${driver.safetyColor}`}>
                    {driver.safety}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${driver.statusColor}`}>
                    {driver.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Bottom Section */}
      <div className="space-y-4">
        <div className="flex flex-col space-y-2">
          <span className="text-xs font-medium uppercase tracking-wider text-on-surface-variant">TOGGLE STAT</span>
          <div className="flex space-x-2">
            <button className="px-4 py-1.5 rounded-md bg-ok text-surface-0 text-sm font-medium">Available</button>
            <button className="px-4 py-1.5 rounded-md bg-info text-surface-0 text-sm font-medium">On Trip</button>
            <button className="px-4 py-1.5 rounded-md bg-surface-2 text-on-surface text-sm font-medium">Off Duty</button>
            <button className="px-4 py-1.5 rounded-md bg-signal text-surface-0 text-sm font-medium">Suspended</button>
          </div>
        </div>
        
        <div className="text-xs text-signal">
          Rule: Expired license or Suspended status → blocked from trip assignment
        </div>
      </div>
    </div>
  );
}
