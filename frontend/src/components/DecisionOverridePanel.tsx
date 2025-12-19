/**
 * SYSTEM ROLE:
 * You are building human override controls
 * for AI credit decisions.
 *
 * PROJECT:
 * CreditBridge Frontend
 */

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { overrideDecision } from '../api/officer';

interface DecisionOverridePanelProps {
  decisionId: string;
  currentDecision: string;
  creditScore: number;
  onSuccess?: () => void;
}

export default function DecisionOverridePanel({ 
  decisionId, 
  currentDecision, 
  creditScore,
  onSuccess 
}: DecisionOverridePanelProps) {
  const [selectedAction, setSelectedAction] = useState<'APPROVE' | 'REJECT' | 'ESCALATE' | null>(null);
  const [reason, setReason] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);
  const queryClient = useQueryClient();

  const overrideMutation = useMutation({
    mutationFn: () => overrideDecision(decisionId, selectedAction!, reason),
    onSuccess: (data) => {
      setIsSubmitted(true);
      
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['decisionLineage', decisionId] });
      queryClient.invalidateQueries({ queryKey: ['recentDecisions'] });
      
      if (onSuccess) {
        onSuccess();
      }
    },
  });

  const handleSubmit = () => {
    if (!selectedAction || !reason.trim()) {
      return;
    }
    overrideMutation.mutate();
  };

  if (isSubmitted && overrideMutation.isSuccess) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-center">
          <svg className="h-6 w-6 text-green-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-green-900 font-semibold">Override Successful</p>
            <p className="text-green-800 text-sm mt-1">
              Decision has been overridden to <span className="font-bold">{overrideMutation.data.override_action}</span> and logged for audit.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Officer Override Controls</h2>

      {/* Warning Banner */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <div className="flex items-start">
          <svg className="h-5 w-5 text-amber-600 mr-2 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <div>
            <p className="text-sm font-semibold text-amber-900">⚠️ This overrides the AI decision</p>
            <p className="text-sm text-amber-800 mt-1">
              Manual overrides must comply with lending regulations and will be permanently recorded in the audit trail.
            </p>
          </div>
        </div>
      </div>

      {/* Current AI Decision */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
        <p className="text-sm text-gray-600 mb-1">Current AI Decision</p>
        <div className="flex items-center justify-between">
          <p className="text-lg font-bold text-gray-900 capitalize">{currentDecision}</p>
          <p className="text-sm text-gray-600">Credit Score: <span className="font-bold">{creditScore}</span></p>
        </div>
      </div>

      {/* Override Action Buttons */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-3">
          Select Override Action
        </label>
        <div className="grid gap-3 md:grid-cols-3">
          <button
            onClick={() => setSelectedAction('APPROVE')}
            disabled={isSubmitted || overrideMutation.isPending}
            className={`px-4 py-3 rounded-lg font-medium border-2 transition ${
              selectedAction === 'APPROVE'
                ? 'bg-green-600 text-white border-green-600'
                : 'bg-white text-gray-700 border-gray-300 hover:border-green-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            ✓ Approve
          </button>
          <button
            onClick={() => setSelectedAction('REJECT')}
            disabled={isSubmitted || overrideMutation.isPending}
            className={`px-4 py-3 rounded-lg font-medium border-2 transition ${
              selectedAction === 'REJECT'
                ? 'bg-red-600 text-white border-red-600'
                : 'bg-white text-gray-700 border-gray-300 hover:border-red-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            ✗ Reject
          </button>
          <button
            onClick={() => setSelectedAction('ESCALATE')}
            disabled={isSubmitted || overrideMutation.isPending}
            className={`px-4 py-3 rounded-lg font-medium border-2 transition ${
              selectedAction === 'ESCALATE'
                ? 'bg-yellow-600 text-white border-yellow-600'
                : 'bg-white text-gray-700 border-gray-300 hover:border-yellow-500'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            ⚡ Escalate
          </button>
        </div>
      </div>

      {/* Reason Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Officer Justification <span className="text-red-600">*</span>
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Provide detailed justification for this override (required for regulatory compliance)"
          rows={4}
          disabled={isSubmitted || overrideMutation.isPending}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
        />
        <p className="text-xs text-gray-500 mt-1">
          {reason.length}/500 characters • This will be permanently recorded
        </p>
      </div>

      {/* Error Display */}
      {overrideMutation.isError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-800 text-sm">
            {(overrideMutation.error as any)?.response?.data?.detail || 'Failed to submit override. Please try again.'}
          </p>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={!selectedAction || !reason.trim() || overrideMutation.isPending || isSubmitted}
          className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition"
        >
          {overrideMutation.isPending ? (
            <span className="flex items-center">
              <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Submitting...
            </span>
          ) : (
            `Submit Override${selectedAction ? ` to ${selectedAction}` : ''}`
          )}
        </button>
      </div>

      {/* Regulatory Notice */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        By submitting this override, you confirm that it complies with all applicable lending regulations and policies.
      </div>
    </div>
  );
}
