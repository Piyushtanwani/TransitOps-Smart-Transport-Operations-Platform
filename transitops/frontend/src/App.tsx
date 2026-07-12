import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { RequireRole } from './auth/RequireRole';
import { LoginPage } from './features/auth/LoginPage';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { FleetPage } from './features/fleet/FleetPage';
import { DriversPage } from './features/drivers/DriversPage';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forbidden" element={<div className="p-12 text-center text-danger font-bold text-2xl">403 Forbidden</div>} />
          
          {/* Protected Routes (Shell) */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              
              {/* Fleet is accessible by all roles */}
              <Route path="/fleet" element={<FleetPage />} />
              
              {/* Drivers accessible by FM, D, SO, FA */}
              <Route path="/drivers" element={<DriversPage />} />
              
              <Route path="/trips" element={<div className="p-6">Trips Placeholder</div>} />
              <Route path="/maintenance" element={<div className="p-6">Maintenance Placeholder</div>} />
              
              {/* Fuel and Expenses accessible by FM, FA */}
              <Route element={<RequireRole roles={['fleet_manager', 'financial_analyst']} />}>
                <Route path="/fuel" element={<div className="p-6">Fuel & Expenses Placeholder</div>} />
                <Route path="/analytics" element={<div className="p-6">Analytics Placeholder</div>} />
              </Route>
              
              {/* Settings (Users, AI) accessible by FM only */}
              <Route element={<RequireRole roles={['fleet_manager']} />}>
                <Route path="/settings" element={<div className="p-6">Settings Placeholder</div>} />
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
