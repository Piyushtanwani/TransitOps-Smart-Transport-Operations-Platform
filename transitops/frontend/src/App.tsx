import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { RequireRole } from './auth/RequireRole';
import { LoginPage } from './features/auth/LoginPage';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { FleetPage } from './features/fleet/FleetPage';
import { DriversPage } from './features/drivers/DriversPage';
import { ComponentKit } from './features/dev/ComponentKit';
import { TripsPage } from './features/trips/TripsPage';
import { NewTripPage } from './features/trips/NewTripPage';
import { MaintenancePage } from './features/maintenance/MaintenancePage';
import { FuelExpensesPage } from './features/finance/FuelExpensesPage';
import { AnalyticsPage } from './features/analytics/AnalyticsPage';
import { SettingsPage } from './features/settings/SettingsPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dev/kit" element={<ComponentKit />} />
          <Route path="/forbidden" element={<div className="p-12 text-center text-danger font-bold text-2xl">403 Forbidden</div>} />
          
          {/* Protected Routes (Shell) */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/fleet" element={<FleetPage />} />
              <Route path="/drivers" element={<DriversPage />} />
              
              <Route element={<RequireRole roles={['fleet_manager', 'dispatcher']} />}>
                <Route path="/trips" element={<TripsPage />} />
                <Route path="/trips/new" element={<NewTripPage />} />
              </Route>
              
              <Route path="/maintenance" element={<MaintenancePage />} />
              
              {/* Fuel and Expenses accessible by FM, FA */}
              <Route element={<RequireRole roles={['fleet_manager', 'financial_analyst']} />}>
                <Route path="/fuel" element={<FuelExpensesPage />} />
              </Route>
              
              {/* Reports and Admin FM only (mostly) */}
              <Route element={<RequireRole roles={['fleet_manager']} />}>
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>
            </Route>
          </Route>
          
          <Route path="*" element={<div className="p-12 text-center text-on-surface">404 Not Found</div>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
