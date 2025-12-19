/**
 * SYSTEM ROLE:
 * You are building a borrower dashboard
 * that shows AI credit decisions clearly.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * TASK FOR COPILOT AGENT:
 * Build a borrower dashboard that:
 * 1. Fetches borrower loan decisions on load
 * 2. Displays:
 *    - Decision status
 *    - Credit score
 *    - Created date
 * 3. Allows user to click "View Explanation"
 * 4. Fetches explanation from backend
 * 5. Displays explanation summary + bullet points
 *
 * UI REQUIREMENTS:
 * - Simple card layout
 * - Green / yellow / red status indicator
 * - Tailwind styling
 *
 * CONSTRAINTS:
 * - No mock data
 * - Handle loading + error states
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchBorrowerDecisions, fetchLoanExplanation } from '../api/borrower';
import type { LoanExplanation } from '../api/borrower';
import LoanRequestForm from '../components/LoanRequestForm';

export default function BorrowerDashboard() {
  const [selectedLoanId, setSelectedLoanId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<LoanExplanation | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);

  // Fetch borrower decisions
  const { data, isLoading, error } = useQuery({
    queryKey: ['borrowerDecisions'],
    queryFn: fetchBorrowerDecisions,
  });

  // Handle view explanation
  const handleViewExplanation = async (loanRequestId: string) => {
    setSelectedLoanId(loanRequestId);
    setLoadingExplanation(true);
    setExplanationError(null);

    try {
      const result = await fetchLoanExplanation(loanRequestId);
      setExplanation(result);
    } catch (err: any) {
      setExplanationError(err.response?.data?.detail || 'Failed to load explanation');
    } finally {
      setLoadingExplanation(false);
    }
  };

  // Close explanation modal
  const handleCloseExplanation = () => {
    setSelectedLoanId(null);
    setExplanation(null);
    setExplanationError(null);
  };

  // Get status color
  const getStatusColor = (decision: string) => {
    switch (decision.toLowerCase()) {
      case 'approved':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'rejected':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Loading your decisions...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-red-800 font-semibold mb-2">Error Loading Decisions</h2>
        <p className="text-red-600">{(error as any).message || 'Failed to load decisions'}</p>
      </div>
    );
  }

  // Empty state
  if (!data || data.decisions.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-12 text-center">
        <div className="text-gray-400 mb-4">
          <svg className="mx-auto h-24 w-24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No Loan Applications Yet</h2>
        <p className="text-gray-600 mb-6">You haven't submitted any loan applications.</p>
        <button className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition">
          Apply for a Loan
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Loan Request Form */}
      <div className="mb-8">
        <LoanRequestForm />
      </div>

      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">My Loan Applications</h1>
        <p className="text-gray-600 mt-2">View your loan application decisions and AI explanations</p>
      </div>

      {/* Decisions Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {data.decisions.map((decision) => (
          <div key={decision.loan_request_id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition">
            {/* Status Badge */}
            <div className="flex items-center justify-between mb-4">
              <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor(decision.decision)}`}>
                {decision.decision.toUpperCase()}
              </span>
              <span className="text-sm text-gray-500">
                {new Date(decision.timestamp).toLocaleDateString()}
              </span>
            </div>

            {/* Credit Score */}
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-1">Credit Score</p>
              <p className="text-4xl font-bold text-gray-900">{decision.score}</p>
            </div>

            {/* Loan ID */}
            <div className="mb-4">
              <p className="text-xs text-gray-500">Loan Request ID</p>
              <p className="text-sm font-mono text-gray-700">{decision.loan_request_id}</p>
            </div>

            {/* Reasoning Preview */}
            {decision.reasoning && (
              <div className="mb-4 p-3 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-700 line-clamp-2">{decision.reasoning}</p>
              </div>
            )}

            {/* View Explanation Button */}
            <button
              onClick={() => handleViewExplanation(decision.loan_request_id)}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition font-medium"
            >
              View AI Explanation
            </button>
          </div>
        ))}
      </div>

      {/* Explanation Modal */}
      {selectedLoanId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">AI Explanation</h2>
              <button
                onClick={handleCloseExplanation}
                className="text-gray-400 hover:text-gray-600 transition"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6">
              {loadingExplanation && (
                <div className="text-center py-12">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
                  <p className="mt-4 text-gray-600">Loading explanation...</p>
                </div>
              )}

              {explanationError && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-6">
                  <div className="flex items-start">
                    <svg className="h-6 w-6 text-amber-600 mr-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <p className="text-amber-900 font-semibold mb-2">Explanation Not Available</p>
                      <p className="text-amber-800 text-sm">
                        This loan decision doesn't have a detailed explanation yet. This may occur for older decisions or if the explanation hasn't been generated. Please contact support if you need more information about this decision.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {explanation && !loadingExplanation && (
                <div>
                  {/* Decision Summary */}
                  <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getStatusColor(explanation.decision)}`}>
                        {explanation.decision.toUpperCase()}
                      </span>
                      <span className="text-2xl font-bold text-gray-900">{explanation.credit_score}</span>
                    </div>
                  </div>

                  {/* Summary */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Summary</h3>
                    <p className="text-gray-700 leading-relaxed">{explanation.summary}</p>
                  </div>

                  {/* Key Points */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Factors</h3>
                    <div className="space-y-3">
                      {explanation.key_points && explanation.key_points.map((point, index) => (
                        <div key={index} className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition">
                          <div className="flex items-start">
                            <span className="flex-shrink-0 w-6 h-6 bg-indigo-100 text-indigo-800 rounded-full flex items-center justify-center text-sm font-semibold mr-3">
                              {index + 1}
                            </span>
                            <p className="text-gray-700 flex-1">{point}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
