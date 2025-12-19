/**
 * SYSTEM ROLE:
 * You are building a deep inspection view
 * for an MFI officer reviewing an AI decision.
 *
 * PROJECT:
 * CreditBridge Frontend
 */

import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchDecisionDetail } from '../api/officer';
import DecisionOverridePanel from '../components/DecisionOverridePanel';

export default function OfficerDecisionDetail() {
  const { decisionId } = useParams<{ decisionId: string }>();
  const navigate = useNavigate();

  // Fetch decision lineage data
  const { data: lineage, isLoading, error } = useQuery({
    queryKey: ['decisionLineage', decisionId],
    queryFn: () => fetchDecisionDetail(decisionId!),
    enabled: !!decisionId,
  });

  // Get status color
  const getStatusColor = (decision: string) => {
    switch (decision?.toLowerCase()) {
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

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-indigo-600 border-t-transparent"></div>
          <p className="mt-4 text-gray-600">Loading decision details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-red-800 font-semibold mb-2">Error Loading Decision</h2>
        <p className="text-red-600">{(error as any).message || 'Failed to load decision details'}</p>
        <button
          onClick={() => navigate('/dashboard/officer')}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!lineage) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-gray-600">No decision data found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Decision Audit Trail</h1>
          <p className="text-gray-600 mt-2">Complete regulatory view of AI credit decision</p>
        </div>
        <button
          onClick={() => navigate('/dashboard/officer')}
          className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
        >
          Back to Dashboard
        </button>
      </div>

      {/* Decision Summary */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Credit Decision Summary</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Decision ID</p>
            <p className="text-sm font-mono text-gray-900">{lineage.decision_id}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Loan Request ID</p>
            <p className="text-sm font-mono text-gray-900">{(lineage as any).loan_request_id || 'N/A'}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Decision Status</p>
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor((lineage as any).decision)}`}>
              {((lineage as any).decision || 'UNKNOWN').toUpperCase()}
            </span>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Credit Score</p>
            <p className="text-3xl font-bold text-gray-900">{(lineage as any).credit_score || 'N/A'}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Model Version</p>
            <p className="text-sm font-mono text-gray-900">{(lineage as any).model_version || 'N/A'}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-600 mb-1">Policy Version</p>
            <p className="text-sm font-mono text-gray-900">{(lineage as any).policy_version || 'N/A'}</p>
          </div>
        </div>
      </div>

      {/* Explanation */}
      {(lineage as any).explanation && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">AI Explanation</h2>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-gray-700 whitespace-pre-wrap">{(lineage as any).explanation}</p>
          </div>
        </div>
      )}

      {/* Fraud Analysis */}
      {(lineage as any).fraud_checks && Object.keys((lineage as any).fraud_checks).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Fraud Analysis</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Fraud Score</p>
              <p className="text-3xl font-bold text-red-600">
                {((lineage as any).fraud_checks.fraud_score || (lineage as any).fraud_checks.score || 0).toFixed(3)}
              </p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Risk Level</p>
              <p className="text-lg font-semibold text-gray-900 capitalize">
                {(lineage as any).fraud_checks.risk_level || 'Unknown'}
              </p>
            </div>
          </div>
          {(lineage as any).fraud_checks.flags && (lineage as any).fraud_checks.flags.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Fraud Flags:</p>
              <div className="space-y-2">
                {(lineage as any).fraud_checks.flags.map((flag: string, index: number) => (
                  <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-800">{flag}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {(!(lineage as any).fraud_checks.flags || (lineage as any).fraud_checks.flags.length === 0) && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-800">✓ No fraud flags detected</p>
            </div>
          )}
        </div>
      )}

      {/* Data Sources */}
      {(lineage as any).data_sources && Object.keys((lineage as any).data_sources).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Data Sources</h2>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <pre className="text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify((lineage as any).data_sources, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Models Used */}
      {(lineage as any).models_used && Object.keys((lineage as any).models_used).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">AI Models & Versions</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries((lineage as any).models_used).map(([key, value]) => (
              <div key={key} className="border border-gray-200 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1 capitalize">{key.replace(/_/g, ' ')}</p>
                <p className="text-sm font-mono text-gray-900">
                  {typeof value === 'string' ? value : JSON.stringify(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timestamps */}
      {(lineage as any).timestamps && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Audit Timestamps</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Decision Created</p>
              <p className="text-sm text-gray-900">
                {(lineage as any).timestamps.decision_created 
                  ? new Date((lineage as any).timestamps.decision_created).toLocaleString()
                  : 'N/A'}
              </p>
            </div>
            <div className="border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Lineage Recorded</p>
              <p className="text-sm text-gray-900">
                {(lineage as any).timestamps.lineage_recorded 
                  ? new Date((lineage as any).timestamps.lineage_recorded).toLocaleString()
                  : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Officer Override Panel */}
      <DecisionOverridePanel
        decisionId={decisionId!}
        currentDecision={(lineage as any)?.decision || 'unknown'}
        creditScore={(lineage as any)?.credit_score || 0}
      />

      {/* Complete Lineage (for advanced auditing) */}
      <details className="bg-white rounded-lg shadow-md p-6">
        <summary className="text-xl font-bold text-gray-900 mb-4 cursor-pointer">
          Complete Lineage Data (JSON)
        </summary>
        <div className="mt-4 bg-gray-900 rounded-lg p-4 overflow-x-auto">
          <pre className="text-sm text-green-400">
            {JSON.stringify(lineage, null, 2)}
          </pre>
        </div>
      </details>
    </div>
  );
}
