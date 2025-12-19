/**
 * SYSTEM ROLE:
 * You are building a layout for borrower users.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK:
 * Create a layout component for borrowers that includes:
 * 1. Navigation bar with borrower-specific menu items
 * 2. Logout functionality
 * 3. Main content area with outlet for nested routes
 *
 * MENU ITEMS:
 * - Dashboard
 * - Apply for Loan
 * - My Applications
 * - Profile
 */

import { Outlet, Link, useNavigate } from 'react-router-dom';

export default function BorrowerLayout() {
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
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <Link
                  to="/dashboard/borrower"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Dashboard
                </Link>
                <Link
                  to="/dashboard/borrower/apply"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Apply for Loan
                </Link>
                <Link
                  to="/dashboard/borrower/applications"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  My Applications
                </Link>
                <Link
                  to="/dashboard/borrower/profile"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  Profile
                </Link>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center">
              <span className="text-sm text-gray-700 mr-4">
                {user.email || 'User'}
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
