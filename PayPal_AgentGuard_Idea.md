# PayPal AgentGuard
## AI Security & Spending Control for Autonomous AI Agents

## 1. Overview

**PayPal AgentGuard** is an AI-powered payment authorization and security layer designed to help users control how autonomous AI agents spend their money.

As AI agents become capable of shopping, booking services, and completing financial tasks, users need a reliable way to define what those agents are allowed to purchase and how much they can spend.

AgentGuard sits between an AI agent and the payment execution flow. It evaluates each payment request against user-defined permissions, spending limits, and risk rules. It can approve requests that meet the configured policy, block requests that violate it, or ask the user for additional approval.

**One-line idea:** A security and authorization layer that ensures AI agents can spend money only within the permissions granted by their users.

**Core principle:** No AI agent should be able to spend a user's money beyond the permissions granted to it.

## 2. Problem Statement

AI agents are increasingly able to take actions on behalf of users. In commerce or financial workflows, an agent may select products, compare prices, build a shopping cart, request payment, and attempt to complete a purchase.

This creates risks:
- An agent may select an item above the user's budget.
- An instruction may be misunderstood.
- A compromised or misbehaving agent may request an unauthorized payment.
- A payment request may differ from the user's original intent.
- Users may lack visibility into what an agent is trying to purchase.

Users need a way to set spending permissions, inspect payment requests, and prevent unauthorized transactions before payment execution.

## 3. Proposed Solution

AgentGuard provides a centralized authorization layer for AI-initiated payments.

Before a payment is executed, AgentGuard:
1. Receives the agent's payment request.
2. Verifies the agent and request information.
3. Checks the request against user-defined spending policies.
4. Applies deterministic authorization rules.
5. Uses AI to assess additional contextual risks and explain unusual requests.
6. Approves, blocks, or escalates the request for user approval.
7. Records the decision and outcome in an audit log.

**Workflow:** Agent Registration → User Policy Setup → Payment Request → Identity & Policy Checks → Risk Analysis → Approve / Block / Ask User → PayPal Sandbox Execution → Audit Log

The final authorization decision should be governed by deterministic policy rules and explicit user permissions—not by an LLM alone.

## 4. How It Works: Example

Imagine a user asks an AI shopping agent:

> "Buy a laptop for me. My maximum budget is ₹60,000."

The agent finds a laptop costing ₹75,000 and submits a payment request to AgentGuard.

| Check | Result |
|---|---|
| User's maximum budget | ₹60,000 |
| Requested payment | ₹75,000 |
| Budget exceeded | Yes |
| Policy result | Not permitted |
| Decision | Blocked |

AgentGuard displays:

> **Payment blocked:** The requested amount of ₹75,000 exceeds your authorized spending limit of ₹60,000.

Now imagine the agent requests a laptop costing ₹55,000. If the user's policy allows automatic purchases under ₹60,000 and all other checks pass, AgentGuard may authorize the request. Otherwise, it asks the user to approve it.

*All names and amounts are illustrative.*

## 5. Core Features

### 5.1 AI Agent Identity & Registration
- Register agents that are permitted to request payments.
- Assign each agent a unique identifier.
- Associate agents with a user or organization.
- Enable, disable, or revoke an agent's permission.
- Record agent metadata and authorization status.

For an MVP, use a registered-agent record and secure API key or token. A self-reported agent name is not proof of identity.

### 5.2 User Spending Rules
Allow users to define:
- Maximum amount per transaction.
- Daily, weekly, or monthly spending limits.
- Approved and blocked merchant categories.
- Allowed currencies.
- Whether approval is required for every transaction.
- Which registered agents may request payments.

Example policy:

```json
{
  "max_transaction_amount": 60000,
  "daily_spending_limit": 80000,
  "currency": "INR",
  "require_approval_above": 25000,
  "allowlisted_categories": ["electronics", "books", "travel"],
  "blocked_categories": ["unapproved_services"]
}
```

### 5.3 Payment Request Monitoring
- Receive payment requests from registered agents.
- Validate amount, currency, merchant, order reference, and agent identity.
- Check for missing, malformed, or inconsistent information.
- Display pending requests in the dashboard.

### 5.4 Deterministic Spending Limit Enforcement
- Compare each request with the user's transaction limit.
- Check cumulative daily or monthly spending.
- Enforce merchant and category restrictions.
- Block requests that violate mandatory rules.
- Prevent duplicate execution using idempotency controls.

This core security function should use backend rules and database checks, not an LLM.

### 5.5 AI-Based Risk Analysis
- Summarize why a request may be unusual.
- Identify inconsistencies between the user's instruction and proposed purchase, when both are available.
- Explain risk indicators in understandable language.
- Recommend escalation for human review.

AI risk analysis is advisory. It must not override hard spending limits or explicit user restrictions.

### 5.6 Human Approval Workflow
- Show amount, merchant, item, agent, and policy evaluation.
- Explain why approval is required.
- Allow the user to approve or reject.
- Record the decision, user, and timestamp.
- Bind approval to the exact request details; changed details require a new evaluation.

### 5.7 PayPal Sandbox Payment Execution
- Use PayPal Sandbox to demonstrate payment execution.
- Execute only after the authorization layer permits the exact request.
- Keep payment credentials on the backend.
- Record the PayPal transaction/order reference and resulting status.
- Never claim payment succeeded until PayPal confirms it.

For the MVP, use a controlled mock AI-agent client to submit requests to AgentGuard. The agent must not be able to bypass the authorization endpoint and call payment execution directly.

### 5.8 Suspicious Behaviour Detection
Flag patterns such as:
- Repeated attempts to exceed spending limits.
- Rapid repeated payment requests.
- Sudden changes in requested amounts.
- Requests from disabled or unregistered agents.
- Repeated requests with altered merchant or order details.

Use deterministic rules for clear signals; AI can help summarize and explain them.

### 5.9 Transaction Audit Dashboard
Display:
- Total payment requests.
- Approved, blocked, and pending requests.
- Spending by agent.
- Spending by category.
- Policy violations.
- Transaction history and decision explanations.

### 5.10 Conversational Security Assistant
Allow users to ask:
- "Why was this payment blocked?"
- "How much has my shopping agent spent today?"
- "Show me all requests above ₹10,000."
- "Which agent made the most requests this week?"

Answers must be grounded in stored transaction and policy data.

## 6. System Architecture

```text
             User / Merchant
                    |
                    v
          AgentGuard Dashboard
                    |
                    v
           User Policy Service
                    |
                    v
AI Agent ---> Payment Request API
                    |
                    v
          Identity & Request Checks
                    |
                    v
        Deterministic Policy Engine
                    |
          +---------+----------+
          |                    |
          v                    v
      Block Request       Policy Checks Pass
                               |
                               v
                       AI Risk Analysis
                               |
                               v
                    Approval Decision Layer
                       /            \\
                      /              \\
                Ask User          Authorized
                    |                 |
                    v                 v
              User Review      PayPal Sandbox
                                      |
                                      v
                             Payment Status Check
                                      |
                                      v
                              Audit & Dashboard
```

All payment execution must pass through the backend authorization service. The frontend and AI agent must never hold payment credentials or have a direct path that bypasses policy checks.

## 7. Suggested Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | Next.js, TypeScript | User dashboard and approval screens |
| UI | Tailwind CSS, shadcn/ui | Interface components |
| Backend | Python, FastAPI | Payment request and authorization APIs |
| Policy engine | Python rules/service layer | Deterministic spending enforcement |
| AI layer | Gemini or OpenAI model | Risk explanations and request summaries |
| Payments | PayPal REST APIs | Sandbox payment workflow |
| Database | PostgreSQL | Users, agents, policies, requests, approvals, audit records |
| Background jobs | Redis and Celery (optional) | Monitoring and asynchronous processing |
| Charts | Recharts | Spending and security analytics |

For a hackathon MVP, keep the architecture simple. A separate multi-agent framework is not required to prove the central idea.

## 8. PayPal Integration

Potential integration approach:
- Create a PayPal Developer application and use Sandbox credentials.
- Build a backend payment flow using the appropriate PayPal Orders or Checkout APIs.
- Route all payment execution through AgentGuard's authorization service.
- Store PayPal order and transaction references.
- Verify payment status from PayPal responses and, where appropriate, webhooks.
- Use test buyer and merchant accounts for the demonstration.

The exact API flow depends on the chosen PayPal product and current API requirements. Do not assume PayPal provides a universal API for intercepting every payment made by every third-party AI agent. In this MVP, AgentGuard controls payments only when the agent is integrated through its own request and authorization gateway.

Official documentation:
- [PayPal Developer](https://developer.paypal.com/)
- [PayPal Orders API](https://developer.paypal.com/docs/api/orders/v2/)
- [PayPal Checkout](https://developer.paypal.com/docs/checkout/)

## 9. Hackathon MVP Scope

Build a working end-to-end demonstration rather than attempting every advanced feature.

### Must-have
1. User can create an account or use a seeded demo profile.
2. User can register or select a demo AI agent.
3. User can configure a maximum transaction amount and spending rules.
4. A mock AI agent submits a payment request to AgentGuard.
5. Backend validates the agent and request.
6. Deterministic policy engine approves or blocks the request.
7. AI generates a concise explanation or risk summary.
8. Requests requiring approval appear in a review screen.
9. Only authorized requests can proceed to PayPal Sandbox execution.
10. The result appears in transaction history and the audit dashboard.

### Nice-to-have
- Daily and monthly spending limits.
- Merchant/category allowlists and blocklists.
- Agent-specific permissions.
- Anomaly detection.
- Conversational security assistant.
- Spending analytics.
- Multiple approval levels for business accounts.

Implement and test the must-have flow before adding optional features.

## 10. Three-Minute Demo Plan

1. **Set permissions:** Configure a maximum transaction amount of ₹60,000 and register a shopping agent.
2. **Agent requests an expensive purchase:** The demo agent submits a ₹75,000 laptop payment request.
3. **AgentGuard blocks it:** The policy engine detects that the request exceeds the user's limit and explains why.
4. **Agent requests an allowed purchase:** The agent submits a ₹55,000 request. AgentGuard checks the policy and routes it according to the user's approval settings.
5. **PayPal Sandbox payment:** The user approves the exact request, and the backend executes the permitted Sandbox payment.
6. **Audit dashboard:** Show approved and blocked requests, spending totals, and explanations.

The demo should make it clear that a blocked request never reaches payment execution.

## 11. Success Metrics

- 100% of requests above a hard spending limit are blocked in the test suite.
- Requests from unregistered or revoked agents are rejected.
- Duplicate requests do not cause duplicate payment execution.
- Approval is bound to the exact amount, merchant, and request.
- No payment executes without authorization.
- Payment status matches the PayPal Sandbox result.
- Every decision is recorded in the audit log.
- AI explanations accurately reflect the underlying policy and request data.

## 12. Security, Privacy, and Reliability

- Keep PayPal credentials and secrets on the backend.
- Never store raw card details.
- Authenticate and authorize every agent request.
- Use HTTPS in deployed environments.
- Validate amounts, currencies, merchant identifiers, and request data.
- Enforce spending limits on the server, not just in the frontend.
- Use idempotency keys and duplicate-request protection.
- Bind approvals to immutable request details.
- Expire old approval requests.
- Log decisions without unnecessarily exposing sensitive personal data.
- Treat AI output as untrusted input; never execute instructions or payments directly from an LLM response.
- Use PayPal Sandbox for the hackathon demonstration.

## 13. What Makes AgentGuard Different?

AgentGuard is not simply a fraud dashboard. It is a **payment authorization layer for AI-initiated transactions**.

Traditional payment systems process authorized payment requests. AgentGuard adds a policy checkpoint before a connected AI agent's request reaches the payment execution flow.

It helps users:
- Define what an AI agent is allowed to spend.
- Set transaction and cumulative spending limits.
- Restrict merchants and categories.
- Review unusual or high-value requests.
- Block requests that violate permissions.
- See a clear record of every decision.

The key differentiator is the combination of deterministic permission enforcement, contextual AI risk explanations, and a user-controlled approval workflow.

## 14. Limitations and Scope Boundaries

- AgentGuard can control only payment flows integrated through its authorization gateway. It cannot automatically intercept every payment made by unrelated third-party agents or applications.
- AI risk analysis cannot guarantee that a transaction is fraudulent or safe.
- A request within the user's budget is not automatically trustworthy; merchant, identity, and other configured policy checks still matter.
- PayPal Sandbox demonstrates the integrated flow but does not prove universal compatibility with all PayPal products or third-party agent platforms.
- The hackathon prototype should clearly distinguish simulated agent requests from real PayPal Sandbox transactions.

## 15. Final Pitch

"AI agents are moving beyond answering questions. They are beginning to shop, book services, and make purchases on behalf of people. But when an AI agent can spend money, how do we make sure it follows the user's permissions?

PayPal AgentGuard is an AI-powered payment authorization layer for autonomous AI agents. Users define spending limits and permissions. When an agent requests a payment, AgentGuard validates its identity, checks the request against those rules, analyses additional risk signals, and approves, blocks, or asks the user for confirmation.

Only authorized requests can proceed to the integrated PayPal payment flow, and every decision is recorded.

**Before an AI agent spends your money, AgentGuard makes sure it has permission.**"
