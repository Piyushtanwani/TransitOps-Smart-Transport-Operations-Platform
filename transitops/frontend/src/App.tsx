import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeToggle } from './components/ThemeToggle';
import { LoginPage } from './features/auth/LoginPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-surface-0 font-sans text-on-surface selection:bg-signal selection:text-white">
        <div className="fixed right-4 top-4 z-50">
          <ThemeToggle />
        </div>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<LoginPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
