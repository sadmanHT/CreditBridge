"""
Database Repository Layer for CreditBridge

This module provides simple, safe helper functions to interact with Supabase tables.
Design goals:
- Read/write borrower profiles
- Create loan requests
- Store explainable credit decisions
- Log audit events

Constraints:
- Use the existing Supabase client
- Keep functions minimal and readable
- Do not include any paid features or extensions
"""

from typing import Dict, Any, Optional
import logging
from app.core.supabase import supabase

# Setup logging
logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """Raised when a database transaction fails and needs rollback."""
    pass


def create_borrower(user_id: str, full_name: str, gender: str, region: str) -> Dict[str, Any]:
    """
    Create a new borrower profile in the database.
    
    Args:
        user_id: Unique identifier for the user
        full_name: Full name of the borrower
        gender: Gender of the borrower
        region: Geographic region of the borrower
        
    Returns:
        Dict containing the created borrower record
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Validate inputs
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required and cannot be empty")
        if not full_name or not full_name.strip():
            raise ValueError("full_name is required and cannot be empty")
        
        response = supabase.table("borrowers").insert({
            "user_id": user_id,
            "full_name": full_name,
            "gender": gender,
            "region": region
        }).execute()
        
        if not response.data:
            raise TransactionError(
                f"Failed to create borrower for user_id={user_id}: "
                "Database returned no data. The insert operation may have been rejected."
            )
            
        logger.info(f"[Repository] Created borrower: user_id={user_id}, borrower_id={response.data[0]['id']}")
        return response.data[0]
    
    except ValueError as ve:
        logger.error(f"[Repository] Validation error creating borrower: {ve}")
        raise Exception(f"Invalid borrower data: {str(ve)}")
    except Exception as e:
        error_msg = f"Database error creating borrower for user_id={user_id}: {str(e)}"
        logger.error(f"[Repository] {error_msg}")
        raise Exception(error_msg)


def create_loan_request(borrower_id: int, requested_amount: float, purpose: str) -> Dict[str, Any]:
    """
    Create a new loan request in the database.
    
    Args:
        borrower_id: ID of the borrower requesting the loan
        requested_amount: Amount of money requested
        purpose: Purpose of the loan
        
    Returns:
        Dict containing the created loan request record
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Validate inputs
        if not borrower_id:
            raise ValueError("borrower_id is required")
        if not requested_amount or requested_amount <= 0:
            raise ValueError(f"requested_amount must be positive, got {requested_amount}")
        if not purpose or not purpose.strip():
            raise ValueError("purpose is required and cannot be empty")
        
        response = supabase.table("loan_requests").insert({
            "borrower_id": borrower_id,
            "requested_amount": requested_amount,
            "purpose": purpose,
            "status": "pending"
        }).execute()
        
        if not response.data:
            raise TransactionError(
                f"Failed to create loan request for borrower_id={borrower_id}: "
                "Database returned no data. The insert operation may have been rejected."
            )
        
        logger.info(
            f"[Repository] Created loan request: borrower_id={borrower_id}, "
            f"loan_id={response.data[0]['id']}, amount={requested_amount}"
        )
        return response.data[0]
    
    except ValueError as ve:
        logger.error(f"[Repository] Validation error creating loan request: {ve}")
        raise Exception(f"Invalid loan request data: {str(ve)}")
    except Exception as e:
        error_msg = f"Database error creating loan request for borrower_id={borrower_id}: {str(e)}"
        logger.error(f"[Repository] {error_msg}")
        raise Exception(error_msg)


def save_credit_decision(
    loan_request_id: int,
    credit_score: float,
    decision: str,
    explanation: str,
    model_version: str
) -> Dict[str, Any]:
    """
    Save a credit decision with explainability information.
    
    Args:
        loan_request_id: ID of the loan request being evaluated
        credit_score: Calculated credit score (0-1000)
        decision: Decision outcome (approved/rejected/review)
        explanation: Human-readable explanation of the decision
        model_version: Version of the AI model used
        
    Returns:
        Dict containing the created credit decision record
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # TRANSACTION BOUNDARY: This is a critical write operation
        # Validate all inputs before database write
        if not loan_request_id:
            raise ValueError("loan_request_id is required")
        if credit_score is None or not (0 <= credit_score <= 1000):
            raise ValueError(f"credit_score must be between 0 and 1000, got {credit_score}")
        
        # Extract value from DecisionType enum if needed
        if hasattr(decision, 'value'):
            decision = decision.value
        
        # Accept both uppercase and lowercase decision values
        valid_decisions = ["approved", "rejected", "review", "APPROVED", "REJECTED", "REVIEW"]
        if not decision or decision not in valid_decisions:
            raise ValueError(f"decision must be one of {valid_decisions}, got {decision}")
        
        if not model_version or not model_version.strip():
            raise ValueError("model_version is required")
        
        response = supabase.table("credit_decisions").insert({
            "loan_request_id": loan_request_id,
            "credit_score": credit_score,
            "decision": decision,
            "explanation": explanation,
            "model_version": model_version
        }).execute()
        
        if not response.data:
            raise TransactionError(
                f"Failed to save credit decision for loan_request_id={loan_request_id}: "
                "Database returned no data. This is a critical failure as the decision was not persisted."
            )
        
        logger.info(
            f"[Repository] Saved credit decision: loan_id={loan_request_id}, "
            f"decision={decision}, score={credit_score}, decision_id={response.data[0]['id']}"
        )
        return response.data[0]
    
    except ValueError as ve:
        logger.error(f"[Repository] Validation error saving credit decision: {ve}")
        raise Exception(f"Invalid credit decision data: {str(ve)}")
    except Exception as e:
        error_msg = (
            f"Database error saving credit decision for loan_request_id={loan_request_id}: {str(e)}. "
            "CRITICAL: Decision was not persisted to database."
        )
        logger.error(f"[Repository] {error_msg}")
        raise Exception(error_msg)


def log_audit_event(
    action: str,
    entity_type: str,
    entity_id: Optional[int],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log an audit event for compliance and monitoring.
    
    Args:
        action: Action performed (e.g., 'create', 'update', 'delete', 'view')
        entity_type: Type of entity affected (e.g., 'borrower', 'loan_request')
        entity_id: ID of the affected entity (optional)
        metadata: Additional context information (optional)
        
    Returns:
        Dict containing the created audit log record
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Validate required fields
        if not action or not action.strip():
            raise ValueError("action is required and cannot be empty")
        if not entity_type or not entity_type.strip():
            raise ValueError("entity_type is required and cannot be empty")
        
        response = supabase.table("audit_logs").insert({
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": metadata or {}
        }).execute()
        
        if not response.data:
            # SAFETY: Audit logging failure should not crash application
            # Log error but return empty dict to allow operation to continue
            logger.error(
                f"[Repository] Failed to log audit event: action={action}, "
                f"entity_type={entity_type}, entity_id={entity_id}"
            )
            return {"id": None, "error": "audit_log_failed"}
            
        return response.data[0]
    
    except ValueError as ve:
        logger.error(f"[Repository] Validation error logging audit event: {ve}")
        return {"id": None, "error": str(ve)}
    except Exception as e:
        # SAFETY: Never crash on audit log failure
        logger.error(f"[Repository] Error logging audit event: {str(e)}")
        return {"id": None, "error": "audit_log_exception"}


def save_decision_lineage(
    decision_id: str,
    borrower_id: str,
    data_sources: Dict[str, Any],
    models_used: Dict[str, Any],
    policy_version: str,
    fraud_checks: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save decision lineage for auditability and transparency.
    
    Records the complete decision-making process including:
    - Data sources used
    - AI models invoked
    - Policy version applied
    - Fraud detection results
    
    Args:
        decision_id: UUID of the credit decision
        borrower_id: UUID of the borrower
        data_sources: Dictionary of data sources used (e.g., credit bureau, social network)
        models_used: Dictionary of AI models and versions (e.g., credit_model, fraud_model)
        policy_version: Version of policy used for decision
        fraud_checks: Dictionary of fraud detection results and flags
        
    Returns:
        Dict containing the created decision lineage record
        
    Raises:
        Exception: If database operation fails with explicit error message
    """
    # TRANSACTION BOUNDARY: Critical write for audit trail
    # This function creates a record that must be persisted for regulatory compliance
    try:
        # Validate required parameters
        if not decision_id:
            raise ValueError("decision_id is required")
        if not borrower_id:
            raise ValueError("borrower_id is required")
        if not policy_version:
            raise ValueError("policy_version is required")
        
        # Validate data structures
        if not isinstance(data_sources, dict):
            raise ValueError("data_sources must be a dictionary")
        if not isinstance(models_used, dict):
            raise ValueError("models_used must be a dictionary")
        if not isinstance(fraud_checks, dict):
            raise ValueError("fraud_checks must be a dictionary")
        
        response = supabase.table("decision_lineage").insert({
            "decision_id": decision_id,
            "borrower_id": borrower_id,
            "data_sources": data_sources or {},
            "models_used": models_used or {},
            "policy_version": policy_version,
            "fraud_checks": fraud_checks or {}
        }).execute()
        
        if not response.data:
            raise TransactionError(
                f"Failed to save decision lineage for decision_id={decision_id}: "
                "Database returned no data. CRITICAL: Audit trail was not persisted."
            )
        
        logger.info(
            f"[Repository] Saved decision lineage: decision_id={decision_id}, "
            f"borrower_id={borrower_id}, lineage_id={response.data[0]['id']}"
        )
        return response.data[0]
    
    except ValueError as ve:
        logger.error(f"[Repository] Validation error saving decision lineage: {ve}")
        raise Exception(f"Invalid decision lineage data: {str(ve)}")
    except Exception as e:
        error_msg = (
            f"Database error saving decision lineage for decision_id={decision_id}: {str(e)}. "
            "CRITICAL: Audit trail was not persisted - regulatory compliance may be affected."
        )
        logger.error(f"[Repository] {error_msg}")
        raise Exception(error_msg)


def save_model_features(
    borrower_id: str,
    feature_set: str,
    feature_version: str,
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Save computed model features to the model_features table.
    
    Args:
        borrower_id: UUID of the borrower
        feature_set: Name of the feature set (e.g., 'core_behavioral')
        feature_version: Version of feature computation logic (e.g., 'v1')
        features: Dictionary of computed feature values
        
    Returns:
        Dict containing the created feature record
        
    Raises:
        Exception: If database operation fails with clear error message
    """
    try:
        # Validate required parameters
        if not borrower_id:
            raise ValueError("borrower_id is required")
        if not feature_set:
            raise ValueError("feature_set is required")
        if not feature_version:
            raise ValueError("feature_version is required")
        if not features:
            raise ValueError("features dictionary is required")
        
        from datetime import datetime, timezone
        
        response = supabase.table("model_features").insert({
            "borrower_id": borrower_id,
            "feature_set": feature_set,
            "feature_version": feature_version,
            "features": features,
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "source_event_count": features.get("event_count", 0)
        }).execute()
        
        if not response.data:
            raise Exception("Failed to save model features: No data returned from database")
            
        return response.data[0]
    except ValueError as ve:
        raise Exception(f"Validation error saving model features: {str(ve)}")
    except Exception as e:
        raise Exception(f"Error saving model features: {str(e)}")


def get_latest_features(
    borrower_id: str,
    feature_set: str,
    client = None
) -> Dict[str, Any]:
    """
    Retrieve the latest computed features for a borrower.
    
    Uses deterministic selection by computed_at timestamp (descending).
    
    Args:
        borrower_id: UUID of the borrower
        feature_set: Name of the feature set (e.g., 'core_behavioral')
        client: Optional custom Supabase client (useful for testing with service role)
        
    Returns:
        Dict containing the latest feature record
        
    Raises:
        Exception: If no features found or database operation fails
    """
    try:
        # Validate required parameters
        if not borrower_id:
            raise ValueError("borrower_id is required")
        if not feature_set:
            raise ValueError("feature_set is required")
        
        # Use provided client or default supabase client
        db_client = client or supabase
        
        response = db_client.table("model_features").select("*").eq(
            "borrower_id", borrower_id
        ).eq(
            "feature_set", feature_set
        ).order("computed_at", desc=True).limit(1).execute()
        
        if not response.data:
            raise Exception(
                f"No features found for borrower_id={borrower_id}, "
                f"feature_set={feature_set}"
            )
            
        return response.data[0]
    except ValueError as ve:
        raise Exception(f"Validation error getting latest features: {str(ve)}")
    except Exception as e:
        raise Exception(f"Error getting latest features: {str(e)}")
