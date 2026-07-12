import type { Role } from '../../types/api';

interface RoleBadgeProps {
  role: Role;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  const formatRole = (r: string) => r.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-surface-2 text-info border border-line">
      {formatRole(role)}
    </span>
  );
}
