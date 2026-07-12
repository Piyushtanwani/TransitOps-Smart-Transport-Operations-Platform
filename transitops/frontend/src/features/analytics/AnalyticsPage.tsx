import { Button } from '../../components/ui/Button';

const mockData = [
  { month: 'Jan', revenue: 45000, cost: 32000 },
  { month: 'Feb', revenue: 52000, cost: 34000 },
  { month: 'Mar', revenue: 48000, cost: 33000 },
  { month: 'Apr', revenue: 61000, cost: 38000 },
  { month: 'May', revenue: 59000, cost: 37000 },
];

export function AnalyticsPage() {
  const maxVal = Math.max(...mockData.map(d => Math.max(d.revenue, d.cost)));

  const handleExportCSV = () => {
    // Mock client-side CSV download
    const csvContent = "data:text/csv;charset=utf-8," + 
      "Month,Revenue,Cost\n" + 
      mockData.map(d => `${d.month},${d.revenue},${d.cost}`).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "financial_report.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold text-ink">Analytics & Reports</h1>
          <p className="text-sm text-ink-mute mt-1">Financial performance and fleet metrics</p>
        </div>
        <Button onClick={handleExportCSV} className="bg-surface-2 text-ink hover:bg-surface-3 border-line">
          Export CSV
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
          <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Total Revenue</p>
          <p className="text-3xl font-data text-ink">₹2,65,000</p>
          <p className="text-xs text-ok mt-2">↑ 12% vs last period</p>
        </div>
        <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
          <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Total Costs</p>
          <p className="text-3xl font-data text-ink">₹1,74,000</p>
          <p className="text-xs text-danger mt-2">↑ 5% vs last period</p>
        </div>
        <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm">
          <p className="text-xs font-semibold text-ink-mute uppercase tracking-wider mb-1">Net Margin</p>
          <p className="text-3xl font-data text-ink">34.3%</p>
          <p className="text-xs text-ok mt-2">↑ 2.1% vs last period</p>
        </div>
      </div>

      <div className="p-6 rounded-xl border border-line bg-surface-1 shadow-sm mt-6">
        <h3 className="font-semibold text-ink mb-6">Revenue vs Cost (YTD)</h3>
        
        {/* Simple CSS Bar Chart */}
        <div className="flex items-end justify-between h-48 space-x-2 pt-6">
          {mockData.map((d) => (
            <div key={d.month} className="flex-1 flex flex-col justify-end items-center space-y-2 group relative">
              
              {/* Tooltip */}
              <div className="absolute -top-12 opacity-0 group-hover:opacity-100 transition-opacity bg-surface-3 text-ink text-[10px] p-2 rounded shadow-md z-10 whitespace-nowrap pointer-events-none">
                <div className="font-bold mb-1">{d.month}</div>
                <div className="text-ok">Rev: ₹{d.revenue.toLocaleString()}</div>
                <div className="text-danger">Cost: ₹{d.cost.toLocaleString()}</div>
              </div>

              <div className="w-full max-w-[40px] flex space-x-1 items-end h-full">
                <div 
                  className="w-1/2 bg-ok rounded-t-sm opacity-80 hover:opacity-100 transition-all"
                  style={{ height: `${(d.revenue / maxVal) * 100}%` }}
                />
                <div 
                  className="w-1/2 bg-danger rounded-t-sm opacity-80 hover:opacity-100 transition-all"
                  style={{ height: `${(d.cost / maxVal) * 100}%` }}
                />
              </div>
              <span className="text-xs text-ink-mute font-medium">{d.month}</span>
            </div>
          ))}
        </div>

        <div className="flex items-center justify-center space-x-6 mt-6 border-t border-line pt-4">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-ok rounded-sm opacity-80" />
            <span className="text-xs text-ink-mute">Revenue</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-danger rounded-sm opacity-80" />
            <span className="text-xs text-ink-mute">Cost</span>
          </div>
        </div>
      </div>

    </div>
  );
}
