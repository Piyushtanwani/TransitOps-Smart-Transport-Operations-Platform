export const STATUS_META: Record<string, { label: string, colorClass: string }> = {
  // Vehicle Statuses
  available: { label: 'AVAILABLE', colorClass: 'bg-ok text-surface-0' },
  on_trip: { label: 'ON TRIP', colorClass: 'bg-info text-surface-0' },
  in_shop: { label: 'IN SHOP', colorClass: 'bg-warn text-surface-0' },
  retired: { label: 'RETIRED', colorClass: 'bg-surface-2 text-on-surface' },
  // Trip Statuses
  draft: { label: 'DRAFT', colorClass: 'bg-surface-2 text-on-surface' },
  dispatched: { label: 'DISPATCHED', colorClass: 'bg-info text-surface-0' },
  completed: { label: 'COMPLETED', colorClass: 'bg-ok text-surface-0' },
  cancelled: { label: 'CANCELLED', colorClass: 'bg-danger text-surface-0' },
  // Driver Statuses
  off_duty: { label: 'OFF DUTY', colorClass: 'bg-surface-2 text-on-surface' },
  suspended: { label: 'SUSPENDED', colorClass: 'bg-danger text-surface-0' },
};

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const meta = STATUS_META[status.toLowerCase()] || { label: status.toUpperCase(), colorClass: 'bg-surface-2 text-on-surface' };
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] uppercase tracking-wide font-medium ${meta.colorClass}`}>
      {meta.label}
    </span>
  );
}
