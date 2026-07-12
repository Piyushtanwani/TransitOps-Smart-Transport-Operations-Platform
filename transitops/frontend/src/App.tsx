import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './features/auth/LoginPage';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './features/dashboard/DashboardPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected Routes (Shell) */}
        <Route element={<AppShell />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/fleet" element={<div className="p-6">Fleet Placeholder</div>} />
          <Route path="/drivers" element={<div className="p-6">Drivers Placeholder</div>} />
          <Route path="/trips" element={<div className="p-6">Trips Placeholder</div>} />
          <Route path="/maintenance" element={<div className="p-6">Maintenance Placeholder</div>} />
          <Route path="/fuel" element={<div className="p-6">Fuel & Expenses Placeholder</div>} />
          <Route path="/analytics" element={<div className="p-6">Analytics Placeholder</div>} />
          <Route path="/settings" element={<div className="p-6">Settings Placeholder</div>} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
