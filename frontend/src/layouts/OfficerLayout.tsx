/**
 * SYSTEM ROLE:
 * You are building a layout for loan officer users.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK:
 * Create a layout component for loan officers that includes:
 * 1. Navigation bar with officer-specific menu items
 * 2. Logout functionality
 * 3. Main content area with outlet for nested routes
 *
 * MENU ITEMS:
 * - Dashboard
 * - Review Applications
 * - Approved Loans
 * - Declined Loans
 * - Reports
 */

import { Outlet, Link, useNavigate } from 'react-router-dom';

export default function OfficerLayout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Clear authentication data
    localStorage.removeItem('access_token');
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
                <span className="ml-2 text-sm text-gray-500">Officer Portal</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard/officer"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/dashboard/officer/review"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Review Applications
                </Link>
                <Link
                  to="/dashboard/officer/approved"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Approved
                </Link>
                <Link
                  to="/dashboard/officer/declined"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Declined
                </Link>
                <Link
                  to="/dashboard/officer/reports"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Reports
                </Link>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center">
              <span className="text-sm text-gray-700 mr-4">
                {user.email || 'Officer'}
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
