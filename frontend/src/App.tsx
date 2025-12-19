/**
 * TASK:
 * Wrap /dashboard routes with ProtectedRoute
 * Create nested routes:
 * /dashboard/borrower → BorrowerLayout
 * /dashboard/officer → OfficerLayout
 * /dashboard/analyst → AnalystLayout
 */

import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import ProtectedRoute from './auth/ProtectedRoute';
import BorrowerLayout from './layouts/BorrowerLayout';
import OfficerLayout from './layouts/OfficerLayout';
import AnalystLayout from './layouts/AnalystLayout';
import BorrowerDashboard from './pages/BorrowerDashboard';
import OfficerDashboard from './pages/OfficerDashboard';
import OfficerDecisionDetail from './pages/OfficerDecisionDetail';
import ApplyForLoan from './pages/ApplyForLoan';

function App() {
  return (
    <Routes>
      {/* Redirect root to login */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* Login page */}
      <Route path="/login" element={<Login />} />
      
      {/* Protected Dashboard Routes */}
      <Route element={<ProtectedRoute />}>
        {/* Redirect /dashboard to /dashboard/borrower by default */}
        <Route path="/dashboard" element={<Navigate to="/dashboard/borrower" replace />} />
        
        {/* Borrower Routes */}
        <Route path="/dashboard/borrower/*" element={<BorrowerLayout />}>
          <Route index element={<BorrowerDashboard />} />
          <Route path="apply" element={<ApplyForLoan />} />
        </Route>
        
        {/* Officer Routes */}
        <Route path="/dashboard/officer/*" element={<OfficerLayout />}>
          <Route index element={<OfficerDashboard />} />
          <Route path="decision/:decisionId" element={<OfficerDecisionDetail />} />
        </Route>
        
        {/* Analyst Routes */}
        <Route path="/dashboard/analyst/*" element={<AnalystLayout />}>
          <Route index element={<DashboardPlaceholder role="Analyst" />} />
        </Route>
      </Route>
    </Routes>
  );
}

// Placeholder dashboard component
function DashboardPlaceholder({ role }: { role: string }) {
  return (
    <div className="bg-white p-8 rounded-lg shadow-lg">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">{role} Dashboard</h1>
      <p className="text-gray-600">Dashboard content coming soon...</p>
    </div>
  );
}

export default App;

