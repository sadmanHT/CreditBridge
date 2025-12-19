/**
 * SYSTEM ROLE:
 * You are building an MFI officer dashboard
 * to review AI credit decisions.
 *
 * PROJECT:
 * CreditBridge Frontend
 */

import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchMfiOverview, fetchRecentDecisions } from '../api/officer';

export default function OfficerDashboard() {
  const navigate = useNavigate();

  // Fetch MFI overview statistics
  const { data: overview, isLoading: overviewLoading, error: overviewError } = useQuery({
    queryKey: ['mfiOverview'],
    queryFn: fetchMfiOverview,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch recent decisions
  const { data: decisionsData, isLoading: decisionsLoading, error: decisionsError } = useQuery({
    queryKey: ['recentDecisions'],
    queryFn: () => fetchRecentDecisions(20),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Get status color
  const getStatusColor = (decision: string) => {
    switch (decision.toLowerCase()) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
      case 'review':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Get risk level color
  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return 'text-green-600';
      case 'medium':
        return 'text-yellow-600';
      case 'high':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  // Loading state
  if (overviewLoading || decisionsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (overviewError || decisionsError) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-red-800 font-semibold mb-2">Error Loading Dashboard</h2>
        <p className="text-red-600">
          {(overviewError as any)?.message || (decisionsError as any)?.message || 'Failed to load dashboard data'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">MFI Officer Dashboard</h1>
        <p className="text-gray-600 mt-2">Monitor loan applications and credit decisions</p>
      </div>

      {/* KPI Cards */}
      {overview && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {/* Total Loans */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Loans</h3>
              <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{overview.total_loans.toLocaleString()}</p>
            <p className="text-sm text-gray-500 mt-1">Total processed</p>
          </div>

          {/* Approved */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Approved</h3>
              <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{overview.approved_count.toLocaleString()}</p>
            <p className="text-sm text-green-600 mt-1">
              {overview.total_loans > 0 ? ((overview.approved_count / overview.total_loans) * 100).toFixed(1) : 0}% approval rate
            </p>
          </div>

          {/* Rejected */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Rejected</h3>
              <svg className="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{overview.rejected_count.toLocaleString()}</p>
            <p className="text-sm text-red-600 mt-1">
              {overview.total_loans > 0 ? ((overview.rejected_count / overview.total_loans) * 100).toFixed(1) : 0}% rejection rate
            </p>
          </div>

          {/* Review */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Needs Review</h3>
              <svg className="h-8 w-8 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{overview.review_count.toLocaleString()}</p>
            <p className="text-sm text-yellow-600 mt-1">Awaiting manual review</p>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {overview && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {/* Average Credit Score */}
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Average Credit Score</p>
              <p className="text-2xl font-bold text-gray-900">{overview.average_credit_score.toFixed(0)}</p>
            </div>

            {/* Flagged Fraud */}
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Flagged Fraud</p>
              <p className="text-2xl font-bold text-red-600">{overview.flagged_fraud_count}</p>
            </div>

            {/* Approval Rate */}
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Approval Rate</p>
              <p className="text-2xl font-bold text-green-600">
                {overview.total_loans > 0 ? ((overview.approved_count / overview.total_loans) * 100).toFixed(1) : 0}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Recent Decisions Table */}
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Recent Credit Decisions</h2>
          <p className="text-sm text-gray-600 mt-1">Latest AI-powered loan decisions</p>
        </div>

        {decisionsData && decisionsData.decisions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Loan Request ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Credit Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fraud Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Decision
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {decisionsData.decisions.map((decision) => (
                  <tr 
                    key={decision.id} 
                    onClick={() => navigate(`/dashboard/officer/decision/${decision.id}`)}
                    className={`cursor-pointer ${decision.decision === 'review' ? 'bg-yellow-50 hover:bg-yellow-100' : 'hover:bg-gray-50'}`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-xs text-gray-500 font-mono">
                        {decision.loan_request_id ? decision.loan_request_id.substring(0, 8) + '...' : 'N/A'}
                      </p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <p className="text-2xl font-bold text-gray-900">{decision.credit_score}</p>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-lg font-semibold text-gray-900">{decision.fraud_score.toFixed(2)}</p>
                        <p className={`text-xs font-medium ${decision.fraud_score > 0.5 ? 'text-red-600' : 'text-green-600'}`}>
                          {decision.fraud_score > 0.5 ? 'High Risk' : 'Low Risk'}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(decision.decision)}`}>
                        {decision.decision.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm text-gray-900">
                          {new Date(decision.created_at).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(decision.created_at).toLocaleTimeString()}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="text-indigo-600 hover:text-indigo-900 font-medium">
                        View Details →
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="mt-4 text-gray-600">No recent decisions found</p>
          </div>
        )}
      </div>
    </div>
  );
}
