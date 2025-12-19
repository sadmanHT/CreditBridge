/**
 * SYSTEM ROLE:
 * You are creating an analyst/regulator dashboard shell.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK FOR COPILOT AGENT:
 * Build a layout component that:
 * 1. Has a clean dashboard layout
 * 2. Shows "Analyst & Compliance Dashboard"
 * 3. Renders nested routes via <Outlet />
 *
 * UI REQUIREMENTS:
 * - Minimal, professional
 * - Placeholder navigation for:
 *   - Fairness
 *   - Risk
 *   - Regulatory Reports
 */

import { Outlet, Link, useNavigate } from 'react-router-dom';

export default function AnalystLayout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear authentication data
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Redirect to login
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            {/* Logo and Nav Links */}
            <div className="flex">
              <div className="flex-shrink-0 flex items-center">
                <h1 className="text-xl font-bold text-indigo-600">CreditBridge</h1>
                <span className="ml-2 text-sm text-gray-500">Analyst & Compliance Dashboard</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard/analyst"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/dashboard/analyst/fairness"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Fairness
                </Link>
                <Link
                  to="/dashboard/analyst/risk"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Risk
                </Link>
                <Link
                  to="/dashboard/analyst/regulatory-reports"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Regulatory Reports
                </Link>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center">
              <span className="text-sm text-gray-700 mr-4">
                {user.email || 'Analyst'}
              </span>
              <button
                onClick={handleLogout}
                className="bg-white px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 border border-gray-300 rounded-md"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
