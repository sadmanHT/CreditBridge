/**
 * SYSTEM ROLE:
 * You are implementing MFI officer API calls
 * for a fintech dashboard.
 *
 * PROJECT:
 * CreditBridge Frontend
 *
 * CONSTRAINTS:
 * - Use Axios client
 * - JWT-authenticated
 */

import apiClient from './client';

export interface MfiOverview {
  total_loans: number;
  approved_count: number;
  rejected_count: number;
  review_count: number;
  average_credit_score: number;
  flagged_fraud_count: number;
}

export interface RecentDecision {
  id: string;
  loan_request_id: string;
  decision: 'approved' | 'rejected' | 'review' | 'pending';
  credit_score: number;
  fraud_score: number;
  created_at: string;
}

export interface RecentDecisionsResponse {
  count: number;
  decisions: RecentDecision[];
}

/**
 * Fetch MFI overview statistics
 * @returns Promise with MFI overview data
 */
export const fetchMfiOverview = async (): Promise<MfiOverview> => {
  const response = await apiClient.get<MfiOverview>('/dashboard/mfi/overview');
  return response.data;
};

/**
 * Fetch recent credit decisions for MFI dashboard
 * @param limit - Number of items per page (default: 20)
 * @returns Promise with recent decisions list
 */
export const fetchRecentDecisions = async (
  limit: number = 20
): Promise<RecentDecisionsResponse> => {
  const response = await apiClient.get<RecentDecisionsResponse>(
    '/dashboard/mfi/recent-decisions',
    {
      params: { limit }
    }
  );
  return response.data;
};

export interface DecisionLineage {
  decision_id: string;
  borrower_id: string;
  credit_check: any;
  fraud_checks: any;
  fairness_flags: any;
  ensemble_output: any;
  context: any;
  created_at: string;
}

/**
 * Fetch detailed decision lineage for regulatory compliance
 * @param decisionId - The ID of the credit decision
 * @returns Promise with complete decision lineage including AI model details
 */
export const fetchDecisionDetail = async (
  decisionId: string
): Promise<DecisionLineage> => {
  const response = await apiClient.get<DecisionLineage>(
    `/regulatory/lineage/${decisionId}`
  );
  return response.data;
};

export interface DecisionOverrideRequest {
  decision_id: string;
  action: 'APPROVE' | 'REJECT' | 'ESCALATE';
  reason: string;
}

export interface DecisionOverrideResponse {
  success: boolean;
  decision_id: string;
  original_decision: string;
  override_action: string;
  message: string;
  audit_logged: boolean;
}

/**
 * Override an AI credit decision with manual officer action
 * @param decisionId - The ID of the credit decision
 * @param action - Override action (APPROVE, REJECT, or ESCALATE)
 * @param reason - Officer's justification for the override
 * @returns Promise with override confirmation
 */
export const overrideDecision = async (
  decisionId: string,
  action: 'APPROVE' | 'REJECT' | 'ESCALATE',
  reason: string
): Promise<DecisionOverrideResponse> => {
  const response = await apiClient.post<DecisionOverrideResponse>('/loans/override', {
    decision_id: decisionId,
    action,
    reason
  });
  return response.data;
};
