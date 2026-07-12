import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { ThemeToggle } from '../ThemeToggle';
import { useAuth } from '../../auth/AuthContext';
import type { Role } from '../../types/api';

const ALL_NAV_ITEMS = [
  { label: 'Dashboard', path: '/dashboard', roles: ['fleet_manager', 'dispatcher', 'safety_officer', 'financial_analyst'] },
  { label: 'Fleet', path: '/fleet', roles: ['fleet_manager', 'dispatcher', 'safety_officer', 'financial_analyst'] },
  { label: 'Drivers', path: '/drivers', roles: ['fleet_manager', 'dispatcher', 'safety_officer', 'financial_analyst'] },
  { label: 'Trips', path: '/trips', roles: ['fleet_manager', 'dispatcher'] },
  { label: 'Maintenance', path: '/maintenance', roles: ['fleet_manager', 'dispatcher', 'safety_officer', 'financial_analyst'] },
  { label: 'Fuel & Expenses', path: '/fuel', roles: ['fleet_manager', 'financial_analyst'] },
  { label: 'Analytics', path: '/analytics', roles: ['fleet_manager', 'financial_analyst'] },
  { label: 'Settings', path: '/settings', roles: ['fleet_manager'] },
];

export function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = ALL_NAV_ITEMS.filter(item => 
    !user || item.roles.includes(user.role)
  );

  const formatRoleName = (role: Role) => {
    return role.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };
  
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  return (
    <div className="flex h-screen bg-surface-0 font-sans text-on-surface overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-surface-2 bg-surface-1 flex flex-col">
        <div className="h-16 flex items-center px-6">
          <span className="font-heading text-xl font-bold tracking-tight">TransitOps</span>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-4">
            {navItems.map((item) => {
              const isActive = location.pathname.startsWith(item.path);
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    className={`flex items-center rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'border border-signal text-signal'
                        : 'text-on-surface-variant hover:bg-surface-1 hover:text-on-surface'
                    }`}
                  >
                    {item.label}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Topbar */}
        <header className="h-16 flex-shrink-0 border-b border-surface-2 bg-surface-0 px-6 flex items-center justify-between">
          <div className="w-96">
            <input
              type="text"
              placeholder="Search..."
              className="h-9 w-full rounded-full border border-surface-2 bg-surface-1 px-4 text-sm focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
            />
          </div>
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            {user && (
              <>
                <span className="text-sm font-medium">{user.full_name}</span>
                <div className="flex items-center space-x-2 rounded-full border border-surface-2 p-1 pl-3 bg-surface-1">
                  <span className="text-xs font-medium text-info">{formatRoleName(user.role)}</span>
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-info text-xs font-bold text-surface-0">
                    {getInitials(user.full_name)}
                  </div>
                </div>
                <button onClick={handleLogout} className="text-sm text-signal hover:underline ml-2">Logout</button>
              </>
            )}
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
