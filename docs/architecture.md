# CreditBridge Architecture

## High-Level System Flow

CreditBridge follows a linear, auditable pipeline designed for transparency and regulatory compliance:

**1. Borrower Interaction**  
A borrower submits a loan request through a mobile app or web interface, providing basic information: requested loan amount, purpose, and demographic data (age, gender, region). The system authenticates the borrower using JWT tokens, ensuring secure access to their profile and loan history.

**2. API Gateway**  
The request enters CreditBridge through a RESTful API built with FastAPI. The API Gateway validates the request, checks authentication, and routes it to the appropriate AI modules. All incoming requests are logged with timestamps and metadata for audit purposes.

**3. AI Credit Decision Pipeline**  
The request flows through three AI modules in sequence:

- **Credit Scoring Engine**: Evaluates the borrower's financial profile using rule-based logic (income stability, loan-to-income ratio, repayment capacity). Outputs a credit score (0–100) with reasoning.
- **TrustGraph AI**: Analyzes the borrower's social network to compute a trust score (0.0–1.0) based on peer relationships, transaction patterns, and community standing. Detects potential fraud rings by identifying unusual network clusters.
- **Fairness Monitor**: After the decision is made, the system checks recent approval patterns across gender and region demographics to detect bias. If disparate impact is found (e.g., female approval rate < 80% of male rate), the system flags the case for human review.

The AI modules combine their outputs into a final decision: **Approved** or **Rejected**, along with a detailed explanation of the reasoning.

**4. Decision Storage & Audit**  
Every credit decision is permanently stored in the database with full context: credit score, trust score, explanation, model version, and timestamp. Simultaneously, the system logs an audit event capturing the decision and all contributing factors. This creates an immutable audit trail for regulatory review.

**5. Explanation Generation**  
Once the decision is stored, the system generates two types of explanations:

- **Technical Explanation** (for compliance officers): Includes all AI model outputs, scores, and metadata.
- **Plain-Language Explanation** (for borrowers): Translates the technical reasoning into simple language (English or Bangla) with bullet points and actionable guidance.

Borrowers receive their explanation via API, which can be displayed in a mobile app with visual indicators (✓ for positive factors, ⚠ for concerns).

**6. Audit & Compliance Access**  
Regulators and compliance officers access a separate set of endpoints to review:
- Complete decision ledgers with explanations
- Audit logs showing all system actions
- Fairness summaries with bias metrics and compliance status

This separation ensures that operational decisions remain transparent while protecting borrower privacy.

---

## Backend Architecture

CreditBridge is built as a three-layer modular system: API Gateway, AI Core, and Data Layer.

### Layer 1: API Gateway (FastAPI)

The API Gateway serves as the single entry point for all external requests. It handles:

- **Authentication**: JWT-based authentication via Supabase Auth ensures only authorized users (borrowers, compliance officers) can access the system.
- **Request Validation**: Pydantic models validate incoming data, ensuring type safety and preventing malformed requests.
- **Routing**: Requests are routed to specific modules based on the endpoint (loans, compliance, explanations).
- **Error Handling**: Standardized error responses with HTTP status codes make debugging straightforward.
- **API Documentation**: Automatically generated OpenAPI/Swagger documentation at `/docs` allows developers and judges to test endpoints interactively.

The API Gateway is stateless and horizontally scalable, meaning multiple instances can run behind a load balancer to handle high traffic volumes.

### Layer 2: AI Core (Modular Intelligence)

The AI Core consists of five independent modules, each with a single responsibility:

**1. Credit Scoring (`credit_scoring.py`)**  
A rule-based engine that evaluates financial profiles using transparent logic. It checks income stability, loan amount reasonableness, and repayment capacity. The output is a credit score (0–100) with a detailed explanation of which factors contributed to the score. This module is deterministic, meaning the same inputs always produce the same outputs—critical for auditability.

**2. TrustGraph AI (`trustgraph.py`)**  
A graph-based fraud detection system that analyzes social networks. Given a borrower's peer relationships (interaction counts, peer repayment histories), TrustGraph computes a trust score by evaluating:
- **Network strength**: Borrowers with strong, diverse peer networks score higher.
- **Fraud ring detection**: Unusual patterns (e.g., tight clusters of borrowers with synchronized transactions) trigger fraud alerts.
- **Peer reputation**: Connections to borrowers with good repayment histories increase trust scores.

TrustGraph uses ASCII-safe output (no Unicode characters) to ensure compatibility with all systems. This module represents CreditBridge's **10× innovation**: social network analysis for credit assessment in emerging markets.

**3. Explainability (`explainability.py`)**  
Generates human-readable explanations for credit decisions. It parses the technical outputs from the scoring and TrustGraph modules and translates them into plain language. For example, a technical output like "trust_score: 0.85, fraud_risk: low" becomes "Your community trust network is very strong, and no fraud indicators were detected."

**4. Fairness Monitor (`fairness.py`)**  
Continuously monitors credit decisions for demographic bias. After each decision, the Fairness Monitor retrieves the last 20 decisions, analyzes approval rates by gender and region, and computes disparate impact ratios. If the female approval rate is less than 80% of the male rate (per EEOC guidelines), the system flags the case and recommends human review. Importantly, fairness monitoring is **non-blocking**: even if bias is detected, the original loan decision stands, but the alert prompts a manual review.

**5. Compliance Engine (`compliance.py`)**  
Provides regulator-facing endpoints for auditing the system. Compliance officers can query:
- **Decision ledgers**: All credit decisions with full explanations
- **Audit logs**: Every system action (loan requests, decisions, fairness evaluations)
- **Fairness summaries**: Aggregated bias metrics showing compliance status

This module implements the **ExplainChain** philosophy: every decision is permanently logged with full context, creating an immutable audit trail.

### Layer 3: Data Layer (Supabase PostgreSQL)

CreditBridge uses Supabase as its database and authentication provider. The data layer consists of four core tables:

**1. `borrowers`**  
Stores borrower profiles (name, email, phone, demographics). Each borrower has a unique `borrower_id` linked to their Supabase Auth user account.

**2. `loan_requests`**  
Records every loan application with requested amount, purpose, and status. Each request is linked to a borrower via foreign key.

**3. `credit_decisions`**  
Stores the output of the AI pipeline: credit score, trust score, decision (approved/rejected), explanation, and model version. Each decision is linked to a loan request.

**4. `audit_logs`**  
A comprehensive event log capturing every system action. Each log entry includes:
- Action type (e.g., `loan_requested`, `credit_decision_with_trustgraph`, `fairness_evaluation`)
- User ID (borrower or system)
- Metadata (scores, decisions, bias metrics)
- Timestamp

The audit logs table is append-only, meaning records are never modified or deleted—ensuring regulatory compliance.

**Why Supabase?**  
Supabase provides enterprise-grade PostgreSQL with built-in authentication, real-time subscriptions, and a free tier suitable for hackathon POCs. In production, CreditBridge can migrate to any PostgreSQL-compatible database (AWS RDS, Azure Database, Google Cloud SQL).

---

## Explainability-by-Design Philosophy

CreditBridge is built on a core principle: **every decision must be explainable to three audiences**.

### 1. Borrowers (Plain Language)
Rejected borrowers often receive no feedback from traditional lenders, leaving them frustrated and excluded. CreditBridge translates technical AI outputs into simple, respectful language:

- **Summary**: One sentence explaining the decision ("Your loan was approved because you have a strong financial profile").
- **Key Points**: 5–7 bullet points breaking down the reasoning (loan amount, trust network, credit score, fraud check).
- **Helpful Tip**: Actionable guidance based on the outcome (e.g., "Consider applying for a smaller loan amount" if rejected).
- **Multilingual**: Available in English and Bangla to serve low-literacy users.

This approach empowers borrowers to understand and improve their creditworthiness, turning rejection into a learning opportunity.

### 2. Compliance Officers (Technical Audit)
Regulators need to verify that decisions are fair, unbiased, and compliant with lending laws. CreditBridge provides:

- **Complete decision ledgers**: Every credit decision with full AI model outputs, scores, and reasoning.
- **Audit logs**: Every system action logged with timestamps and metadata.
- **Fairness summaries**: Aggregated bias metrics showing disparate impact ratios, bias alert rates, and compliance status.

Compliance officers can drill down into individual decisions or analyze trends across thousands of applications—without needing technical AI expertise.

### 3. Developers (Model Transparency)
The AI modules are designed to be inspectable and auditable:

- **Rule-based logic**: Credit scoring uses transparent rules (no "black box" ML models in the POC).
- **Graph algorithms**: TrustGraph uses documented graph analysis techniques (peer reputation, fraud ring detection).
- **Versioned models**: Every decision records the model version used (e.g., `rule-based-v1.0+trustgraph-v1.0`), enabling version tracking and A/B testing.

In production, CreditBridge can integrate ML models (e.g., XGBoost) with SHAP explainability, maintaining transparency even with complex models.

---

## Why This Architecture Scales Nationally

CreditBridge is designed to handle millions of loan applications across Bangladesh and other emerging markets. Here's how the architecture supports national-scale deployment:

### 1. Stateless API Gateway
The FastAPI backend is stateless, meaning it doesn't store session data between requests. This allows horizontal scaling: deploy 10, 100, or 1,000 API instances behind a load balancer, and each instance can handle requests independently. Cloud platforms like AWS, Azure, or Google Cloud support auto-scaling, automatically adding instances during peak traffic (e.g., end-of-month loan surges).

### 2. Modular AI Core
Each AI module (credit scoring, TrustGraph, fairness, explainability) is independent and can scale separately. For example:
- **TrustGraph** is computationally intensive (graph analysis). In production, it can run on dedicated GPU instances or as a separate microservice.
- **Fairness monitoring** is non-blocking and can run as a background worker, processing batches of decisions asynchronously without slowing down real-time loan approvals.

This separation of concerns ensures that one slow module doesn't bottleneck the entire system.

### 3. Database Optimization
Supabase (PostgreSQL) supports:
- **Indexing**: Fast lookups on foreign keys (e.g., `loan_request_id`, `borrower_id`).
- **Read replicas**: For high-traffic compliance queries, read replicas offload read operations from the primary database.
- **Connection pooling**: Efficiently manages thousands of concurrent database connections.

In production, CreditBridge can partition the database by region (e.g., Dhaka, Chittagong, Sylhet), reducing query load and improving response times.

### 4. Asynchronous Processing
For non-critical operations (fairness monitoring, compliance report generation), CreditBridge can use background task queues (e.g., Celery, Redis). This decouples real-time loan decisions from batch analytics, ensuring borrowers receive instant feedback while compliance metrics are computed in the background.

### 5. Cloud-Native Deployment
CreditBridge is Docker-ready and can deploy on any cloud platform:
- **AWS**: ECS (Elastic Container Service) or Lambda for serverless
- **Azure**: App Service or Container Instances
- **Google Cloud**: Cloud Run or Kubernetes

Cloud-native deployment enables:
- **Geographic distribution**: Deploy instances in multiple regions (Dhaka, Chittagong) to reduce latency.
- **Disaster recovery**: Automatic failover if one region goes down.
- **Cost efficiency**: Pay only for actual usage (serverless) rather than maintaining idle servers.

### 6. API Rate Limiting & Caching
To handle traffic spikes (e.g., viral marketing campaigns), CreditBridge can implement:
- **Rate limiting**: Prevent abuse by limiting requests per user (e.g., 10 loan applications per day).
- **Caching**: Store frequently accessed data (e.g., borrower profiles) in Redis, reducing database load.

---

## Why This Architecture Is Regulator-Ready

Financial services are heavily regulated to protect consumers and ensure fair lending. CreditBridge's architecture anticipates regulatory requirements:

### 1. Immutable Audit Trail
The `audit_logs` table records every system action in an append-only format. Records are never modified or deleted, creating a tamper-proof audit trail. Regulators can trace:
- **Who** requested a loan (borrower ID)
- **When** the decision was made (timestamp)
- **Why** the decision was made (AI scores, explanations)
- **What** model was used (version tracking)

This meets the **ExplainChain** standard: every decision is a permanent link in an auditable chain of events.

### 2. Fairness Monitoring with 80% Rule
CreditBridge implements the **disparate impact test** (80% rule) mandated by the U.S. Equal Employment Opportunity Commission (EEOC) and adopted by financial regulators worldwide. If the approval rate for any protected demographic (e.g., female borrowers) falls below 80% of the majority group (male borrowers), the system flags potential bias. This proactive monitoring helps lenders avoid discriminatory practices and comply with anti-discrimination laws.

### 3. Explainability for Adverse Action Notices
In many jurisdictions, lenders must provide **adverse action notices** explaining why a loan was rejected. CreditBridge's plain-language explanation module satisfies this requirement by automatically generating borrower-facing explanations with:
- Clear reasoning (e.g., "Your loan amount exceeds our recommended limit for your income level")
- No jargon or technical terms
- Actionable guidance (e.g., "Consider applying for a smaller amount")

Regulators can verify that rejected borrowers receive adequate explanations, reducing complaints and legal disputes.

### 4. Data Privacy & Security
CreditBridge follows **privacy-by-design** principles:
- **Minimal data collection**: Only essential information (name, demographics, loan details) is stored.
- **Encryption**: All data is encrypted at rest (database) and in transit (HTTPS).
- **Access controls**: JWT authentication ensures borrowers can only access their own data, while compliance officers have read-only access to anonymized aggregates.
- **GDPR-ready**: Borrowers can request data deletion (right to be forgotten), though audit logs remain for regulatory compliance.

### 5. Model Versioning & Rollback
Every credit decision records the AI model version used (e.g., `rule-based-v1.0+trustgraph-v1.0`). If regulators identify a problem with a specific model version, CreditBridge can:
- **Identify affected decisions**: Query all decisions using the problematic version.
- **Rollback**: Revert to a previous model version without losing audit history.
- **A/B testing**: Run multiple model versions simultaneously and compare fairness metrics.

This version control ensures regulatory investigations can trace decisions to specific model configurations.

### 6. Third-Party Audits
CreditBridge's modular architecture supports third-party audits:
- **AI modules**: Independent auditors can review the credit scoring and TrustGraph logic without accessing the database.
- **Audit logs**: Compliance officers can export audit logs for external review.
- **Fairness reports**: Regulators can request aggregated fairness summaries (no individual borrower data required).

This transparency builds trust with regulators, investors, and civil society organizations.

---

## Future Enhancements

While the current architecture is production-ready for a POC, these enhancements would prepare CreditBridge for national deployment:

1. **Machine Learning Models**: Replace rule-based credit scoring with XGBoost or LightGBM, adding SHAP explainability for transparency.
2. **Real-Time TrustGraph**: Integrate with mobile money platforms (bKash, Nagad) to build real borrower social networks from transaction data.
3. **Background Workers**: Move fairness monitoring and compliance report generation to asynchronous task queues (Celery, Redis).
4. **Multi-Language Support**: Add Hindi, Tamil, and other regional languages for pan-South Asian deployment.
5. **Admin Dashboard**: Build a web UI for compliance officers to review flagged cases, approve exceptions, and generate reports.
6. **Blockchain Audit Trail**: Store audit log hashes on a blockchain for ultimate tamper-proof compliance.
7. **API Gateway Rate Limiting**: Implement Redis-based rate limiting to prevent abuse and DDoS attacks.

---

## Conclusion

CreditBridge's architecture balances three critical goals: **transparency** (explainable AI), **scalability** (modular design), and **compliance** (immutable audit trail). By separating concerns into independent layers (API Gateway, AI Core, Data Layer), the system can scale from a hackathon POC to a national lending platform serving millions of unbanked borrowers.

The architecture is judge-ready, investor-ready, and regulator-ready—demonstrating that responsible AI isn't a constraint, but a foundation for building trust at scale.
