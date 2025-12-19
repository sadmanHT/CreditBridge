/**
 * SYSTEM ROLE:
 * You are implementing route protection
 * for a fintech frontend.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK FOR COPILOT AGENT:
 * Implement a ProtectedRoute component that:
 * 1. Checks if JWT exists in localStorage
 * 2. If not, redirects to /login
 * 3. Otherwise renders child routes
 *
 * CONSTRAINTS:
 * - No role logic yet
 * - JWT presence only
 */

import { Navigate, Outlet } from 'react-router-dom';

interface ProtectedRouteProps {
  children?: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  // Check if JWT token exists in localStorage
  const token = localStorage.getItem('access_token');

  // If no token, redirect to login
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  // If token exists, render children or outlet
  return children ? <>{children}</> : <Outlet />;
}
