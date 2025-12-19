# Credit Analyst & Policy Dashboard Specification

**CreditBridge — Scalable, Ethical AI Credit Infrastructure**

---

## Executive Summary

The **Credit Analyst & Policy Dashboard** is a strategic oversight platform designed for credit analysts, regulators, and policy stakeholders who need to monitor the health, fairness, and inclusiveness of the CreditBridge credit ecosystem at scale.

Unlike the [MFI Officer Dashboard](mfi_dashboard_spec.md), which focuses on **individual loan decisions**, this dashboard provides **portfolio-level insights** to answer critical questions:

- **Risk Management**: Is default risk increasing? Which segments are underperforming?
- **Fairness & Ethics**: Are approval rates equitable across gender, region, and demographics?
- **Financial Inclusion**: Are we reaching rural communities, women, and youth?
- **Early Warning**: Are there fraud concentration signals or approval anomalies?
- **Policy & Compliance**: Are AI thresholds producing fair outcomes? What needs adjustment?

**Design Philosophy**:
> "The dashboard is not just a reporting tool—it's an early-warning system and policy-tuning engine that ensures CreditBridge scales ethically and sustainably."

---

## 1. Purpose of the Analyst Dashboard

### 1.1 Portfolio Risk Monitoring
**Goal**: Track credit quality and default trends across the entire loan portfolio.

**Key Questions Answered**:
- What is the current default rate? Is it increasing or decreasing?
- Which cohorts (by region, gender, loan size) have the highest default risk?
- Are recent loan approvals performing better or worse than historical benchmarks?
- How is the TrustGraph fraud detection impacting default rates?

**Why This Matters**:
- **For Analysts**: Identifies portfolio segments that need risk mitigation (e.g., tighter approval thresholds)
- **For Regulators**: Ensures systemic risk is managed proactively
- **For Policy Teams**: Informs decisions about loan size limits, interest rates, and target demographics

---

### 1.2 Bias and Fairness Oversight
**Goal**: Monitor AI system for bias and ensure equitable access to credit.

**Key Questions Answered**:
- Are approval rates equitable across gender, region, and age groups?
- Is there evidence of disparate impact (e.g., women approved at significantly lower rates than men)?
- Are human overrides introducing bias (e.g., officers consistently rejecting women)?
- Are fairness interventions (e.g., threshold adjustments) effective?

**Why This Matters**:
- **For Analysts**: Detects bias before it becomes systemic
- **For Regulators**: Demonstrates compliance with anti-discrimination laws
- **For Policy Teams**: Ensures AI system aligns with financial inclusion goals

---

### 1.3 Inclusion Tracking
**Goal**: Measure progress toward financial inclusion for underserved populations.

**Key Questions Answered**:
- Are we reaching rural communities? What percentage of loans go to rural vs. urban areas?
- Are women applying and being approved at rates that reflect their representation in the population?
- Are youth (18-25 years old) accessing credit?
- How has inclusion changed over time?

**Why This Matters**:
- **For Analysts**: Tracks whether CreditBridge is achieving its mission
- **For Regulators**: Provides evidence of progress toward national financial inclusion targets
- **For Policy Teams**: Identifies gaps and opportunities (e.g., marketing campaigns for rural women)

---

## 2. Core Dashboard Views

### View 1: Approval Rates Over Time
**Purpose**: Track how often loan applications are approved, rejected, or flagged for review.

**Visualization**: Line chart with 3 lines:
- ✅ **Approved** (green line)
- ❌ **Rejected** (red line)
- ⚠️ **Needs Review** (orange line)

**Time Granularity**: Daily, Weekly, Monthly (user-selectable)

**Example Chart**:
```
Approval Rate Trend (Last 90 Days)
────────────────────────────────────────────────
80% ┤                               ┌─✅─┐
70% ┤               ┌─✅─┐        ✅     ✅
60% ┤       ┌─✅─┐✅               │
50% ┤   ✅─┘                       │
40% ┤                               │
30% ┤                               │
20% ┤       ┌───❌─┐               │
10% ┤   ❌─┘        └─❌───❌─────❌─┘
 0% ┤
    └────────────────────────────────────────────
    Nov 1    Nov 15    Dec 1     Dec 15

Key Insights:
- ✅ Approval rate increasing from 52% to 78% (AI learning, fewer fraud flags)
- ❌ Rejection rate decreasing from 28% to 15% (fraud detection more precise)
- ⚠️ "Needs Review" rate stable at 7% (healthy balance)
```

**Actionable Insights**:
- **If approval rate suddenly spikes**: Possible fraud ring exploiting system → Investigate
- **If rejection rate increases**: AI may be too strict → Review thresholds
- **If "needs review" rate is too high**: Officers overwhelmed → Tune anomaly detection

---

### View 2: Default Risk Trends
**Purpose**: Track loan performance and identify early signs of portfolio deterioration.

**Visualization**: 
1. **Default Rate Line Chart** (% of loans that defaulted within 90 days)
2. **Risk Score Distribution** (histogram showing credit scores of approved loans)
3. **Cohort Performance Table** (default rates by loan vintage)

**Example Default Rate Chart**:
```
Default Rate by Loan Vintage (Last 6 Months)
────────────────────────────────────────────────
10% ┤                               
 9% ┤                               
 8% ┤                        ┌──┐
 7% ┤                   ┌──┐ │  │
 6% ┤              ┌──┐ │  │ │  │
 5% ┤         ┌──┐ │  │ │  │ │  │
 4% ┤    ┌──┐ │  │ │  │ │  │ │  │
 3% ┤ ┌─┐│  │ │  │ │  │ │  │ │  │
 2% ┤ │ ││  │ │  │ │  │ │  │ │  │
 1% ┤ │ ││  │ │  │ │  │ │  │ │  │
 0% ┤ │ ││  │ │  │ │  │ │  │ │  │
    └────────────────────────────────────────────
    Jul  Aug  Sep  Oct  Nov  Dec

🚨 WARNING: Default rate increasing from 3.2% (July) to 8.1% (December)

Root Cause Analysis:
- 🔴 TrustGraph fraud detection disabled for 2 weeks in November (maintenance)
- 🔴 Approval threshold lowered from 65 to 55 (policy change)
- 🟡 Seasonal effect: December weddings → income volatility

Recommended Actions:
1. Raise approval threshold back to 60 (immediate)
2. Require manual review for loans > Rs. 100,000 (short-term)
3. Investigate November cohort for fraud rings (forensic analysis)
```

**Cohort Performance Table**:
| Loan Vintage | Total Loans | Default Rate (90 days) | Avg Credit Score | Avg Loan Size |
|--------------|-------------|------------------------|------------------|---------------|
| July 2025    | 1,245       | 3.2%                   | 72               | Rs. 45,000    |
| August 2025  | 1,398       | 3.8%                   | 71               | Rs. 48,000    |
| September    | 1,502       | 5.1%                   | 68               | Rs. 52,000    |
| October      | 1,689       | 6.7%                   | 65               | Rs. 55,000    |
| November     | 1,823       | 7.9%                   | 62               | Rs. 58,000    |
| December     | 1,956       | 8.1% 🚨               | 60               | Rs. 61,000    |

---

### View 3: TrustGraph Risk Clusters (Aggregated)
**Purpose**: Identify fraud concentration signals and high-risk networks at portfolio level.

**Visualization**: 
1. **Network Graph** (clusters of borrowers with suspicious connections)
2. **Risk Heatmap** (geographic concentration of fraud)
3. **Fraud Ring Detection Summary Table**

**Example Network Graph**:
```
AGGREGATED TRUSTGRAPH ANALYSIS
(Portfolio-level view, individual identities anonymized)

┌─────────────────────────────────────────────────┐
│  HIGH-RISK CLUSTERS DETECTED (Last 30 Days)     │
└─────────────────────────────────────────────────┘

Cluster #1: Dhaka North (23 borrowers)
  ● ── ● ── ●
  │    │    │
  ● ── ● ── ●     🚨 CONFIRMED FRAUD RING
  │    │    │
  ● ── ● ── ●

  - All applied within 4 hours
  - Shared device fingerprint
  - 15 of 23 defaulted within 7 days
  - Total loss: Rs. 1.2M
  - Action: 19 rejected (AI), 4 approved (officer override)

Cluster #2: Chittagong Port Area (12 borrowers)
  ● ── ● ── ●
       │    
  ● ── ● ── ●     ⚠️ SUSPICIOUS (Under Investigation)

  - Applied within same week
  - All list same business address
  - Average trust score: 0.42 (below threshold)
  - Action: All flagged for manual review

Cluster #3: Sylhet Tea Workers (34 borrowers)
  ● ── ● ── ●
  │    │    │
  ● ── ● ── ●     ✅ LEGITIMATE (Business Cooperative)
  │    │    │
  ● ── ● ── ●

  - Tea plantation workers' collective
  - High peer reputation (0.85 avg)
  - 31 of 34 loans performing well (2.9% default rate)
  - Action: 28 approved (AI), 6 approved (officer override)
```

**Fraud Ring Detection Summary Table**:
| Cluster ID | Location         | Borrowers | Fraud Probability | AI Action | Officer Action | Total Loss |
|------------|------------------|-----------|-------------------|-----------|----------------|------------|
| #001       | Dhaka North      | 23        | 94%               | 19 Rej    | 4 Approved     | Rs. 1.2M   |
| #002       | Chittagong Port  | 12        | 78%               | 0 Rej     | 12 Review      | Rs. 0      |
| #003       | Sylhet Tea       | 34        | 12%               | 28 Appr   | 6 Appr         | Rs. 85K    |
| #004       | Rajshahi Silk    | 8         | 67%               | 8 Rej     | 0 Override     | Rs. 0      |

**Geographic Fraud Heatmap**:
```
BANGLADESH FRAUD RISK HEATMAP (Aggregated by Division)

     ┌─────────────────────────────────┐
     │  RANGPUR      SYLHET             │
     │    🟢          🟢                 │
     │                                  │
     │  RAJSHAHI     MYMENSINGH         │
     │    🟡          🟢                 │
     │                                  │
     │  DHAKA        CHITTAGONG         │
     │    🔴          🟡                 │
     │                                  │
     │  KHULNA       BARISAL            │
     │    🟢          🟢                 │
     └─────────────────────────────────┘

Legend:
🔴 High Risk (>10 fraud rings detected)
🟡 Medium Risk (3-10 fraud rings)
🟢 Low Risk (<3 fraud rings)

Dhaka Division: 🚨 ALERT
- 15 confirmed fraud rings (last 30 days)
- Total attempted fraud: Rs. 8.5M
- Amount prevented: Rs. 7.1M (84% detection rate)
- Recommendation: Increase manual review threshold for Dhaka applications
```

---

## 3. Fairness & Ethics Monitoring

### 3.1 Approval Parity by Gender and Region
**Purpose**: Ensure AI system does not discriminate based on gender or geography.

**Visualization**: Side-by-side bar charts comparing approval rates.

**Example Chart: Gender Parity**:
```
APPROVAL RATES BY GENDER (Last 90 Days)
────────────────────────────────────────────────
80% ┤  ┌──────┐     ┌──────┐
70% ┤  │      │     │      │
60% ┤  │ 72%  │     │ 68%  │
50% ┤  │      │     │      │
40% ┤  │      │     │      │
30% ┤  │      │     │      │
20% ┤  │      │     │      │
10% ┤  │      │     │      │
 0% ┤  └──────┘     └──────┘
    └────────────────────────────────────────────
       Male          Female

Disparate Impact Ratio: 68% / 72% = 0.94 ✅ PASS
(Threshold: 0.80 — Four-Fifths Rule)

Key Insights:
- ✅ Gender parity within acceptable range (94% ratio)
- 🟡 Female approval rate 4 percentage points lower
- 🔍 Root cause analysis:
  - Women's avg credit score: 64 (vs. men: 67)
  - Women's avg loan size: Rs. 38K (vs. men: Rs. 52K)
  - Women more likely to be first-time borrowers (62% vs. 41%)

Recommended Actions:
- No immediate intervention required (within regulatory limits)
- Monitor quarterly (ensure gap doesn't widen)
- Consider first-time borrower incentive program
```

**Example Chart: Regional Parity**:
```
APPROVAL RATES BY REGION (Last 90 Days)
────────────────────────────────────────────────
80% ┤  ┌──────┐                 ┌──────┐
70% ┤  │      │     ┌──────┐    │      │
60% ┤  │ 75%  │     │ 58%  │    │ 71%  │
50% ┤  │      │     │      │    │      │
40% ┤  │      │     │      │    │      │
30% ┤  │      │     │      │    │      │
20% ┤  │      │     │      │    │      │
10% ┤  │      │     │      │    │      │
 0% ┤  └──────┘     └──────┘    └──────┘
    └────────────────────────────────────────────
       Urban         Rural       Peri-Urban

🚨 ALERT: Rural approval rate significantly lower

Disparate Impact Ratio: 58% / 75% = 0.77 ❌ FAIL
(Below 0.80 threshold)

Root Cause Analysis:
- Rural borrowers have lower TrustGraph scores (fewer mobile money peers)
- Rural borrowers have higher fraud ring detection rate (12% vs. 6%)
- Rural borrowers more likely to fail phone verification (limited connectivity)

Recommended Actions (URGENT):
1. Lower TrustGraph threshold for rural applicants (0.60 → 0.50)
2. Add alternative verification methods (in-person visits, village elder attestation)
3. Investigate fraud ring detection algorithm for rural bias
4. Launch rural outreach campaign (educate on credit building)
```

---

### 3.2 Disparate Impact Indicators
**Purpose**: Track real-time compliance with anti-discrimination regulations (e.g., Bangladesh Bank guidelines, Four-Fifths Rule).

**Dashboard Section**: Compliance Scorecard

**Example Scorecard**:
```
┌─────────────────────────────────────────────────────────┐
│  FAIRNESS COMPLIANCE SCORECARD (December 2025)          │
└─────────────────────────────────────────────────────────┘

Metric                          Value       Status    Threshold
──────────────────────────────────────────────────────────────
Gender Parity (F/M Ratio)       0.94        ✅ PASS    ≥ 0.80
Regional Parity (Rural/Urban)   0.77        ❌ FAIL    ≥ 0.80
Age Parity (Youth/Adult)        0.88        ✅ PASS    ≥ 0.80
Default Rate Parity (F/M)       1.02        ✅ PASS    0.80-1.25
Loan Size Parity (F/M)          0.73        🟡 WARN    ≥ 0.80

Overall Fairness Score: 3/5 Metrics Passed

🚨 REGULATORY ALERT:
- Regional Parity FAILING (0.77 ratio)
- Loan Size Parity WARNING (0.73 ratio)
- Action Required: Submit corrective action plan to Bangladesh Bank within 30 days

Recommended Interventions:
1. Lower rural approval threshold (immediate)
2. Launch women's business loan program (short-term)
3. Conduct third-party fairness audit (quarterly)
```

**Historical Trend Chart**:
```
GENDER PARITY TREND (Last 12 Months)
────────────────────────────────────────────────
1.00 ┤  ┌──────────────────────✅──────────────┐
0.95 ┤  │                      ●               │
0.90 ┤  │                 ●         ●          │
0.85 ┤  │            ●                 ●       │
0.80 ┤  ├──────────────────────────────────────┤ ← Regulatory Floor
0.75 ┤  │       ●                              │
0.70 ┤  │  ●                                   │
     └────────────────────────────────────────────
     Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep

Key Insights:
- ✅ Gender parity improved from 0.71 (January) to 0.94 (September)
- 🔍 Improvement due to: First-time borrower program, lower TrustGraph threshold for women
- 🎯 On track to reach 1.00 parity by Q1 2026
```

---

### 3.3 Human Review Recommendations
**Purpose**: Guide policy decisions on when human review is required (vs. full automation).

**Dashboard Section**: Human-in-the-Loop Analytics

**Example Table**:
```
┌─────────────────────────────────────────────────────────────────┐
│  HUMAN REVIEW IMPACT ANALYSIS (Last 90 Days)                    │
└─────────────────────────────────────────────────────────────────┘

Scenario                    AI Rec    Officer Override    Impact
──────────────────────────────────────────────────────────────────
Fraud Ring (High Conf)      Reject    2% Override Rate    ✅ Good
                                      (Legit cooperatives)

Fraud Ring (Low Conf)       Reject    34% Override Rate   ⚠️ High
                                      (False positives)

High Amount + Low Score     Reject    12% Override Rate   ✅ Good
                                      (Verified income)

First-Time Borrower         Reject    8% Override Rate    ✅ Good
                                      (Thin file bias)

Gender Parity Threshold     Auto-Appr 0.3% Override Rate  ✅ Good
                                      (Rare false negatives)

Recommended Policy Changes:
1. ⚠️ Low-confidence fraud rings: Route to manual review (not auto-reject)
   → Estimated reduction in false positives: 28%
   → Cost: +2 minutes per application

2. ✅ High-confidence fraud rings: Keep auto-reject
   → Current override rate (2%) indicates AI is accurate

3. 🟡 First-time borrowers: Add alternative verification step
   → Reduce rejection rate from 47% to 35%
   → Cost: +5 minutes per application (phone verification)
```

**Officer Override Breakdown**:
```
OVERRIDE PATTERNS BY OFFICER (Last 30 Days)
────────────────────────────────────────────────
Officer Name         Overrides   Override Rate   Bias Indicator
─────────────────────────────────────────────────────────────────
Fatima Khan          12          4.2%            ✅ No Bias
Rajesh Kumar         8           3.1%            ✅ No Bias
Ayesha Begum         45          18.7%           🚨 High Override
Khalid Hassan        5           2.1%            ✅ No Bias

🚨 ALERT: Ayesha Begum's override rate (18.7%) is 4.5x higher than team average (4.1%)

Deep Dive: Ayesha Begum's Override Patterns
- 89% of overrides are AI Rejects → Officer Approves
- 67% of overrides are for female borrowers (potential gender bias?)
- 82% of overrides are for rural borrowers (compensating for rural bias?)
- Default rate on Ayesha's overrides: 6.2% (vs. portfolio avg: 5.4%)

Recommended Actions:
1. Schedule 1-on-1 coaching session with Ayesha
2. Review 10 recent override decisions (quality audit)
3. If rural/gender bias: Policy issue (not officer issue) → Adjust AI thresholds
4. If quality issue: Additional training required
```

---

## 4. Regional & Demographic Insights

### 4.1 Rural vs Urban Access
**Purpose**: Track financial inclusion progress in underserved rural areas.

**Visualization**: 
1. **Loan Distribution Map** (% of loans by region)
2. **Rural Approval Rate Trend** (monthly time series)
3. **Rural vs Urban Performance Comparison**

**Example Map**:
```
LOAN DISTRIBUTION BY REGION (Last 90 Days)
────────────────────────────────────────────────
       ┌───────────────────────────┐
       │  BANGLADESH               │
       │                           │
       │  [Urban: 58%]             │
       │  [Rural: 32%]             │
       │  [Peri-Urban: 10%]        │
       │                           │
       └───────────────────────────┘

National Population Distribution:
- Urban: 38%
- Rural: 62%

🚨 GAP ANALYSIS:
- Rural population: 62% of Bangladesh
- Rural loans: Only 32% of portfolio
- Gap: 30 percentage points (underserved)

Target (2026): 50% rural loans
Current Progress: 32% → Need +18pp improvement
```

**Rural Performance Table**:
```
┌─────────────────────────────────────────────────────────────────┐
│  RURAL VS URBAN COMPARISON (Last 90 Days)                       │
└─────────────────────────────────────────────────────────────────┘

Metric                        Urban       Rural       Gap
──────────────────────────────────────────────────────────────────
Approval Rate                 75%         58%         -17pp 🚨
Avg Credit Score              68          62          -6 pts
Avg Loan Size                 Rs. 52K     Rs. 38K     -Rs. 14K
Default Rate (90 days)        5.1%        6.8%        +1.7pp ⚠️
TrustGraph Score              0.72        0.58        -0.14 🚨
Phone Verification Success    94%         78%         -16pp ⚠️

Key Insights:
- Rural borrowers face multiple barriers (lower TrustGraph, phone verification failures)
- Rural default rate slightly higher (6.8% vs. 5.1%) but within acceptable range
- Rural-urban gap is systemic (not due to one factor)

Recommended Actions:
1. Add alternative verification: Village elder attestation, in-person visits
2. Lower TrustGraph threshold for rural applicants (0.70 → 0.50)
3. Partner with rural mobile money agents (bKash, Nagad) for peer data
4. Launch rural marketing campaign (explain credit building process)
```

---

### 4.2 Women & Youth Inclusion Metrics
**Purpose**: Track progress toward gender equality and youth empowerment goals.

**Visualization**: 
1. **Women's Loan Approval Trend** (monthly time series with target line)
2. **Youth Access Metrics** (age 18-25 approval rates)
3. **Intersectional Analysis** (rural women, urban youth, etc.)

**Example: Women's Inclusion Dashboard**:
```
┌─────────────────────────────────────────────────────────────────┐
│  WOMEN'S FINANCIAL INCLUSION METRICS (December 2025)            │
└─────────────────────────────────────────────────────────────────┘

LOAN APPLICATION VOLUME:
Women's Applications:    2,456    (41% of total) 🎯 Target: 45%
Women's Approvals:        1,670    (68% approval rate)
Men's Approvals:          2,520    (72% approval rate)

Gender Parity Ratio: 0.94 ✅ PASS (Above 0.80 threshold)

WOMEN'S LOAN PORTFOLIO:
Total Active Loans (Women):  Rs. 63.5M  (38% of portfolio)
Avg Loan Size (Women):       Rs. 38,000
Avg Loan Size (Men):         Rs. 52,000
Loan Size Parity: 0.73 🟡 WARNING (Below 0.80 threshold)

DEFAULT PERFORMANCE:
Women's Default Rate:    5.4%
Men's Default Rate:      5.3%
Performance Parity: 1.02 ✅ EXCELLENT (Women slightly outperform men)

INTERSECTIONAL INSIGHTS:
- Rural Women: 48% approval rate 🚨 (Lowest segment)
- Urban Women: 76% approval rate ✅ (At parity with urban men)
- Young Women (18-25): 62% approval rate 🟡 (Moderate gap)

Recommended Actions:
1. Launch rural women's loan program (lower threshold, village elder verification)
2. Increase loan size limits for women (close 0.73 parity gap to 0.85+)
3. Partner with women's cooperatives (e.g., BRAC, Grameen Bank)
```

**Example: Youth Inclusion Dashboard**:
```
┌─────────────────────────────────────────────────────────────────┐
│  YOUTH FINANCIAL INCLUSION METRICS (Ages 18-25)                 │
└─────────────────────────────────────────────────────────────────┘

LOAN APPLICATION VOLUME:
Youth Applications:      987     (16% of total) 🎯 Target: 20%
Youth Approvals:         651     (66% approval rate)
Adult Approvals (26+):   3,539   (71% approval rate)

Age Parity Ratio: 0.93 ✅ PASS (Above 0.80 threshold)

YOUTH LOAN PORTFOLIO:
Total Active Loans (Youth):  Rs. 24.8M  (15% of portfolio)
Avg Loan Size (Youth):       Rs. 38,000
Avg Loan Size (Adults):      Rs. 48,000

DEFAULT PERFORMANCE:
Youth Default Rate:      6.9%
Adult Default Rate:      5.2%
Performance Gap: +1.7pp ⚠️ (Youth slightly riskier but manageable)

YOUTH BORROWER PROFILES:
- University Students:   22% (Low approval: 52%)
- Small Business Owners: 38% (High approval: 78%)
- First Job (Employed):  40% (Medium approval: 64%)

KEY BARRIERS FOR YOUTH:
1. Thin credit files (no borrowing history)
2. Lower TrustGraph scores (smaller mobile money peer network)
3. Income volatility (gig economy, seasonal work)

Recommended Actions:
1. Launch youth starter loan program (Rs. 10K-25K, lower threshold)
2. Accept alternative verification (university ID, employer letter)
3. Partner with youth entrepreneurship programs
4. Add educational repayment grace period (for students)
```

---

## 5. Early-Warning Indicators

### 5.1 Sudden Approval Spikes
**Purpose**: Detect anomalies that may indicate system errors or fraud exploitation.

**Dashboard Section**: Anomaly Detection Panel

**Example Alert**:
```
┌─────────────────────────────────────────────────────────────────┐
│  🚨 ANOMALY DETECTED: Approval Spike                            │
└─────────────────────────────────────────────────────────────────┘

Event: Approval rate jumped from 72% (baseline) to 94% in 2 hours

Time: December 16, 2025, 14:00-16:00
Duration: 2 hours
Applications Affected: 287 loans (Rs. 14.5M total)

┌─────────────────────────────────────────────┐
│  APPROVAL RATE (Last 24 Hours)              │
│                                             │
│ 100% ┤                  ┌──🚨──┐           │
│  90% ┤                  │      │           │
│  80% ┤                  │      │           │
│  70% ┤──────────────────┘      └───────    │
│  60% ┤                                     │
│      └─────────────────────────────────────│
│      12pm   2pm   4pm   6pm   8pm   10pm   │
└─────────────────────────────────────────────┘

Root Cause Analysis (Automated):
- ⚠️ TrustGraph fraud detection module crashed (14:05)
- 🔴 Fraud detection layer bypassed for 287 applications
- 🟡 Credit scoring module continued operating normally

Fraud Risk Assessment:
- Estimated fraud ring applications: 23-34 (8-12% of spike)
- Potential loss exposure: Rs. 1.2M - Rs. 1.8M
- Actual fraud detected (post-hoc review): 28 applications (Rs. 1.4M)

Actions Taken (Automated):
1. ✅ TrustGraph module restarted (14:07)
2. ✅ 287 "spike" loans flagged for manual review (14:10)
3. ✅ Alert sent to compliance team (14:10)
4. ✅ Approval threshold temporarily raised 65 → 75 (14:15)

Actions Required (Human):
1. Review 287 flagged loans (Priority: High amounts first)
2. Identify and blacklist confirmed fraud rings
3. Contact legitimate borrowers (apologize for delay)
4. Implement redundancy: Backup fraud detection module
```

**Spike Detection Rules**:
```
ANOMALY DETECTION THRESHOLDS:
────────────────────────────────────────────────
Metric                  Baseline    Spike Trigger    Action
───────────────────────────────────────────────────────────
Approval Rate Jump      ±10%        >20% in 1 hour   🚨 Alert
Rejection Rate Drop     ±10%        >25% in 1 hour   🚨 Alert
Avg Loan Size Jump      ±15%        >30% in 1 hour   ⚠️ Review
Application Volume      ±20%        >50% in 1 hour   ⚠️ Review
Fraud Ring Detections   ±5          >15 in 1 hour    🚨 Alert
Default Rate (Cohort)   ±2%         >5% in 30 days   🚨 Alert
```

---

### 5.2 Fraud Concentration Signals
**Purpose**: Identify geographic or demographic clusters of fraud before losses escalate.

**Dashboard Section**: Fraud Concentration Map

**Example Alert**:
```
┌─────────────────────────────────────────────────────────────────┐
│  🚨 FRAUD CONCENTRATION ALERT: Dhaka North                      │
└─────────────────────────────────────────────────────────────────┘

Location: Dhaka North Division, Uttara Sector 11
Time Window: December 10-16, 2025 (7 days)
Fraud Rings Detected: 8 (vs. baseline: 1-2 per week)

┌─────────────────────────────────────────────┐
│  FRAUD RING DETECTION TREND (Dhaka North)   │
│                                             │
│  10 ┤                              ●       │
│   9 ┤                        ●             │
│   8 ┤                  ●                   │
│   7 ┤            ●                         │
│   6 ┤      ●                               │
│   5 ┤                                      │
│   4 ┤                                      │
│   3 ┤                                      │
│   2 ┤──●───────────────────────────────────│ ← Baseline
│   1 ┤                                      │
│     └─────────────────────────────────────│
│     Dec 1  Dec 5  Dec 10  Dec 15          │
└─────────────────────────────────────────────┘

Fraud Pattern Analysis:
- 🚨 8 fraud rings share same IP address block (likely internet cafe)
- 🚨 62 borrowers involved (avg 7.8 per ring)
- 🚨 All applications submitted between 6pm-9pm (after work hours)
- 🚨 87% used same device fingerprint (shared smartphone)

Financial Impact:
- Total attempted fraud: Rs. 3.2M
- Amount blocked (AI): Rs. 2.8M (88% detection rate)
- Amount approved (officer override): Rs. 0.4M (needs investigation)

Recommended Actions (URGENT):
1. Blacklist IP address block (temporary, 30 days)
2. Require in-person verification for Uttara Sector 11 (immediate)
3. Contact officers who overrode AI (investigate 0.4M in approvals)
4. Alert local law enforcement (potential organized fraud operation)
5. Increase fraud detection sensitivity for Dhaka North (+20% threshold)
```

**Fraud Heatmap with Drill-Down**:
```
BANGLADESH FRAUD CONCENTRATION (Last 30 Days)
────────────────────────────────────────────────
     ┌─────────────────────────────────┐
     │  RANGPUR      SYLHET             │
     │    🟢 (2)      🟢 (3)             │
     │                                  │
     │  RAJSHAHI     MYMENSINGH         │
     │    🟡 (7)      🟢 (4)             │
     │                                  │
     │  DHAKA        CHITTAGONG         │
     │    🔴 (15)     🟡 (8)             │
     │                                  │
     │  KHULNA       BARISAL            │
     │    🟢 (2)      🟢 (1)             │
     └─────────────────────────────────┘

🔴 Dhaka (15 fraud rings): Click to drill down ↓

DHAKA DIVISION DRILL-DOWN:
────────────────────────────
- Uttara Sector 11:    8 rings 🚨 HOTSPOT
- Mirpur 10:           3 rings ⚠️ Elevated
- Dhanmondi 15:        2 rings ✅ Normal
- Gulshan 2:           1 ring  ✅ Normal
- Mohammadpur:         1 ring  ✅ Normal

Recommended Actions:
- Uttara: Immediate intervention (blacklist, in-person verification)
- Mirpur: Increased monitoring (lower auto-approval threshold)
- Others: Standard fraud detection protocols
```

---

## 6. How Analysts Use This Dashboard

### 6.1 Policy Tuning
**Use Case**: Adjust AI approval thresholds to balance inclusion and risk.

**Example Workflow**:
```
SCENARIO: Rural approval rate is 58% (vs. urban 75%), failing disparate impact test

Step 1: Identify Root Cause
Analyst reviews "Rural vs Urban Comparison" table:
- Rural TrustGraph scores are 0.14 points lower (0.58 vs. 0.72)
- Rural phone verification fails 16% more often (78% vs. 94% success)

Step 2: Simulate Policy Changes
Analyst runs "What-If" analysis:
┌─────────────────────────────────────────────────────────────────┐
│  POLICY SIMULATION: Lower Rural TrustGraph Threshold            │
└─────────────────────────────────────────────────────────────────┘

Current Threshold: 0.70 (All regions)
Proposed Threshold: 0.50 (Rural only), 0.70 (Urban/Peri-Urban)

Projected Impact:
- Rural approval rate: 58% → 71% (+13pp) ✅
- Rural-urban parity: 0.77 → 0.95 ✅ PASS
- Rural default rate: 6.8% → 8.2% (+1.4pp) ⚠️ Acceptable
- Estimated additional defaults: 15 loans (Rs. 570K loss)
- Estimated financial inclusion benefit: 245 new rural borrowers (Rs. 9.3M access)

Cost-Benefit Analysis:
- Loss from defaults: Rs. 570K
- Benefit from inclusion: Rs. 9.3M in credit access
- Net Benefit: Rs. 8.7M (15x return)

Step 3: Implement Policy Change
Analyst clicks "Approve Policy Change" → System updates threshold
- Effective date: December 20, 2025
- Auto-review date: January 20, 2026 (1 month check-in)
- Rollback trigger: If default rate exceeds 10%

Step 4: Monitor Impact (30 days later)
Dashboard shows:
- Rural approval rate: 69% (vs. projected 71%) ✅
- Rural-urban parity: 0.92 ✅ PASS
- Rural default rate: 7.8% (vs. projected 8.2%) ✅ Better than expected
- Policy change: SUCCESS → Make permanent
```

---

### 6.2 Threshold Adjustments
**Use Case**: Respond to portfolio deterioration (rising default rates).

**Example Workflow**:
```
SCENARIO: Default rate increasing from 5.4% (Q3) to 8.1% (Q4)

Step 1: Root Cause Analysis
Analyst reviews "Default Risk Trends" chart:
- November cohort: 7.9% default rate (vs. historical 5.4%)
- December cohort: 8.1% default rate (trend worsening)
- Correlation: Approval threshold was lowered from 65 to 55 in October

Step 2: Identify At-Risk Segments
Analyst drills down into "Cohort Performance" table:
- Low credit score (50-59): 14.2% default rate 🚨
- Medium credit score (60-69): 6.8% default rate ⚠️
- High credit score (70+): 2.1% default rate ✅

Step 3: Propose Threshold Change
Analyst simulates raising threshold from 55 to 65:
┌─────────────────────────────────────────────────────────────────┐
│  POLICY SIMULATION: Raise Credit Score Threshold                │
└─────────────────────────────────────────────────────────────────┘

Current Threshold: 55 (All applicants)
Proposed Threshold: 65 (All applicants)

Projected Impact:
- Approval rate: 78% → 64% (-14pp) ⚠️
- Default rate: 8.1% → 5.2% (-2.9pp) ✅
- Applications rejected (monthly): +280
- Estimated default prevention: Rs. 2.4M per month
- Financial inclusion cost: 280 borrowers lose access (Rs. 10.6M)

Alternative: Tiered Thresholds
- First-time borrowers: Threshold 65 (stricter)
- Repeat borrowers: Threshold 55 (maintain current)

Projected Impact (Tiered):
- Approval rate: 78% → 72% (-6pp) ✅ Better
- Default rate: 8.1% → 6.4% (-1.7pp) ✅ Improved
- Applications rejected: +120 (vs. +280 in full raise)
- Default prevention: Rs. 1.5M per month

Step 4: Implement Tiered Threshold (Balanced Approach)
Analyst selects tiered threshold → Policy updated
- Monitor weekly for 4 weeks
- Review monthly performance
- Adjust if default rate doesn't decrease to <7%
```

---

### 6.3 Regulatory Reporting
**Use Case**: Generate quarterly fairness reports for Bangladesh Bank.

**Example Workflow**:
```
SCENARIO: Bangladesh Bank requires Q4 2025 fairness report (due January 15, 2026)

Step 1: Generate Compliance Report
Analyst clicks "Export Regulatory Report" → System generates PDF

┌─────────────────────────────────────────────────────────────────┐
│  CREDITBRIDGE FAIRNESS REPORT — Q4 2025                         │
│  Submitted to: Bangladesh Bank, Financial Inclusion Division    │
└─────────────────────────────────────────────────────────────────┘

EXECUTIVE SUMMARY:
- Total Loan Applications: 18,456
- Total Approvals: 13,245 (72% approval rate)
- Portfolio Value: Rs. 634M
- Default Rate: 6.2% (within regulatory limits)

FAIRNESS METRICS:
1. Gender Parity (Female/Male Approval Ratio): 0.94 ✅ PASS
   - Female approval rate: 68%
   - Male approval rate: 72%
   - Complies with Four-Fifths Rule (0.80 threshold)

2. Regional Parity (Rural/Urban Approval Ratio): 0.82 ✅ PASS*
   - Rural approval rate: 61%
   - Urban approval rate: 75%
   - *Note: Improved from 0.77 (Q3) due to threshold adjustment
   - Corrective action plan implemented (see Appendix A)

3. Age Parity (Youth/Adult Approval Ratio): 0.93 ✅ PASS
   - Youth (18-25) approval rate: 66%
   - Adult (26+) approval rate: 71%

DEFAULT PERFORMANCE BY DEMOGRAPHICS:
- Female default rate: 5.4% (vs. Male: 5.3%) ✅ At parity
- Rural default rate: 6.8% (vs. Urban: 5.1%) ⚠️ Elevated but acceptable
- Youth default rate: 6.9% (vs. Adult: 5.2%) ⚠️ Elevated but acceptable

COMPLIANCE STATUS: ✅ COMPLIANT
- All fairness metrics meet or exceed regulatory thresholds
- Corrective action plan in progress for rural parity
- No enforcement actions recommended

Step 2: Submit to Bangladesh Bank
Analyst uploads PDF to regulatory portal
- Confirmation: Report #2025-Q4-CREDITBRIDGE received
- Review period: 30 days
- Next report due: April 15, 2026 (Q1 2026)

Step 3: Internal Stakeholder Briefing
Analyst prepares presentation for CreditBridge leadership:
- Slide 1: Executive summary (compliance status: PASS)
- Slide 2: Gender parity improvement (0.71 → 0.94 over 12 months)
- Slide 3: Rural parity challenges (corrective actions working)
- Slide 4: Portfolio growth (Rs. 634M, +28% QoQ)
- Slide 5: Risk management (default rate stable at 6.2%)
```

---

## 7. Technical Specifications

### 7.1 Performance Requirements
- Dashboard load time: <2 seconds (all charts rendered)
- Data refresh rate: Every 5 minutes (real-time anomaly detection)
- Report generation: <30 seconds (quarterly compliance reports)
- Query response time: <500ms (drill-down interactions)

### 7.2 Data Architecture
- Data source: PostgreSQL (Supabase) with read replicas
- Aggregation: Pre-computed daily rollups (performance optimization)
- Retention: 24 months of historical data (regulatory requirement)
- Backup: Daily snapshots, 7-year retention (audit compliance)

### 7.3 User Access Control
**Role-Based Access Control (RBAC)**:
- **Credit Analysts**: Full dashboard access, policy simulation, threshold adjustments
- **Compliance Officers**: Fairness metrics, audit trails, regulatory reports
- **Regulators (Bangladesh Bank)**: Read-only access, quarterly reports
- **Policy Stakeholders**: High-level metrics, inclusion trends (no PII)

### 7.4 Export & Integration
- **Export Formats**: PDF (regulatory reports), CSV (data analysis), JSON (API integration)
- **API Access**: RESTful API for third-party analytics tools
- **Alerting**: Email/SMS notifications for anomalies, Slack integration for team alerts

---

## 8. Summary: Why This Dashboard Matters

### For Credit Analysts
- **Risk Management**: Detect portfolio deterioration early, adjust thresholds proactively
- **Policy Optimization**: Simulate policy changes before implementation, balance inclusion vs. risk
- **Efficiency**: Automated reporting saves 20+ hours per quarter

### For Regulators
- **Transparency**: Real-time compliance monitoring, quarterly fairness reports
- **Accountability**: Audit trails for all policy changes, human override tracking
- **Confidence**: Demonstrates CreditBridge's commitment to ethical AI and financial inclusion

### For Policy Stakeholders
- **Inclusion Tracking**: Measure progress toward rural, women's, and youth access goals
- **Impact Assessment**: Quantify benefits of policy interventions (e.g., rural threshold adjustment)
- **Strategic Planning**: Identify underserved segments, prioritize outreach campaigns

### For CreditBridge's Mission
> "The analyst dashboard ensures that CreditBridge scales responsibly—balancing financial inclusion with portfolio health, and ensuring AI fairness through continuous monitoring and transparent reporting."

---

## Appendix: Dashboard Mockup (High-Level Layout)

```
┌───────────────────────────────────────────────────────────────────┐
│  CREDITBRIDGE ANALYST DASHBOARD                                   │
│  User: Dr. Rahman (Credit Analyst) | Date: Dec 16, 2025           │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [PORTFOLIO OVERVIEW]  [FAIRNESS METRICS]  [EARLY WARNINGS]      │
│                                                                   │
├─────────────────────────────────┬─────────────────────────────────┤
│  APPROVAL RATE TREND            │  DEFAULT RISK TREND             │
│  ────────────────────────       │  ────────────────────────       │
│  [Line chart: 90 days]          │  [Line chart: 6 months]         │
│  Current: 72% ✅                 │  Current: 8.1% 🚨               │
│                                 │                                 │
├─────────────────────────────────┼─────────────────────────────────┤
│  FAIRNESS COMPLIANCE            │  TRUSTGRAPH RISK CLUSTERS       │
│  ────────────────────────       │  ────────────────────────       │
│  Gender Parity: 0.94 ✅          │  [Network graph]                │
│  Regional Parity: 0.82 🟡       │  15 clusters detected           │
│  Age Parity: 0.93 ✅             │  Dhaka North: 🚨 ALERT          │
│                                 │                                 │
├─────────────────────────────────┴─────────────────────────────────┤
│  🚨 ALERTS (3 Active)                                             │
│  1. Approval spike detected (14:00-16:00) — 287 loans flagged     │
│  2. Dhaka North fraud concentration — 8 rings in 7 days           │
│  3. Regional parity at risk (0.82) — Corrective action required   │
│                                                                   │
│  [View Details] [Dismiss] [Export Report]                        │
└───────────────────────────────────────────────────────────────────┘
```

---

**END OF SPECIFICATION**

**Next Steps**:
1. Review with CreditBridge leadership (ensure alignment with strategic goals)
2. Validate with Bangladesh Bank (confirm regulatory compliance requirements)
3. Design high-fidelity UI mockups (wireframes → prototype)
4. Develop data pipelines (pre-computed aggregations for performance)
5. Conduct user testing with credit analysts (usability, actionability)
6. Launch beta version (Q1 2026)
