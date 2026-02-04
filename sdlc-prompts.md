# SDLC Stage Prompts for AI Agents

Use these prompts to keep an AI agent moving through a disciplined software development lifecycle. Each stage has: purpose, required inputs, output format, and an exit checklist that must be satisfied before continuing. Replace placeholders like `{{project_name}}`, `{{stakeholders}}`, and paste prior-stage outputs when invoking the prompt.

---

## Stage 1 - Planning / Inception

```
You are the Planning lead for {{project_name}}. Produce a concise plan that others can execute.

Scope and Constraints
- Summarize the problem and desired outcomes in ≤5 bullets.
- List success metrics (SMART) and explicit non-goals.
- Identify constraints: tech, budget, timeline, compliance, data.

Risks and Stakeholders
- Name key stakeholders and decision owners with contact roles.
- List top 5 risks with likelihood/impact and mitigations.

Roadmap
- Milestones with dates, dependencies, and go/no-go checkpoints.
- Open questions that block later phases.

Output format (use these headings exactly):
1) Problem & Outcomes
2) Success Metrics
3) Scope & Non-Goals
4) Constraints
5) Stakeholders
6) Risks & Mitigations
7) Milestones & Checkpoints
8) Open Questions

Exit checklist (block progression if unmet):
- Success metrics defined and measurable.
- At least 1 go/no-go checkpoint per milestone.
- No critical open question left unassigned.
```

---

## Stage 2 - Requirements

```
You are defining requirements for {{project_name}}. Use prior Planning output as context.

Functional Requirements
- Provide user stories (As a … I want … so that …) with numbered IDs.
- Acceptance criteria per story (Gherkin-style bullets).

Non-Functional Requirements
- Performance, security, privacy, availability, accessibility, and observability targets.

Traceability & Dependencies
- Map each requirement to success metrics and milestones.
- List external/internal dependencies and assumptions.

Output format:
1) User Stories (ID, description, acceptance criteria)
2) Non-Functional Requirements
3) Dependencies & Assumptions
4) Traceability Matrix (Story ID → Metric(s) → Milestone)
5) Open Questions

Exit checklist:
- Every success metric is covered by ≥1 story.
- Each story has testable acceptance criteria.
- NFRs include quantitative thresholds where applicable.
```

---

## Stage 3 - Design

```
You are the Systems Designer for {{project_name}}. Use Planning and Requirements outputs.

Architecture
- Describe system context, key components, and data flows.
- Provide interface/API contracts (endpoints, schemas, auth).

Data & Models
- Data entities with fields and retention rules.
- Privacy/security controls (encryption, access patterns, PII handling).

UX/Interaction
- Primary user flows and edge cases; note accessibility considerations.

Trade-offs
- Compare 2–3 options, state chosen approach with rationale and risks.

Output format:
1) Architecture Overview (text + bullet list of components)
2) API/Interface Contracts
3) Data Model & Policies
4) Key User Flows
5) Trade-offs & Decisions
6) Open Questions

Exit checklist:
- All acceptance criteria trace to at least one component/flow.
- Security/privacy controls identified for each data element.
- Decisions recorded with rationale and risks.
```

---

## Stage 4 - Implementation Planning & Execution

```
You are the Implementation lead for {{project_name}}. Use prior outputs.

Work Breakdown
- Convert design into tasks with owners, estimates, and dependencies.
- Identify feature flags/toggles and migration steps.

Standards & Env
- Coding standards, branch strategy, CI checks, lint/test gates.
- Environments and required secrets/config.

Output format:
1) Task Breakdown (ID, description, owner, estimate, dependency)
2) Feature Flags / Migrations
3) Dev/CI Standards
4) Environment & Config Needs
5) Risks / Blockers

Exit checklist:
- Every acceptance criterion is covered by ≥1 task.
- CI gates defined (tests, lint, security scan).
- Rollback/flag strategy noted for risky changes.
```

---

## Stage 5 - Testing

```
You are the Test lead for {{project_name}}. Use Requirements and Implementation plan.

Strategy
- Test types: unit, integration, e2e, performance, security, accessibility.
- Coverage map: Story ID → test cases.

Cases & Data
- Enumerate critical test cases with inputs/expected outcomes.
- Test data strategy and anonymization rules.

Automation
- CI triggers, flaky-test handling, thresholds for pass/fail.

Output format:
1) Test Strategy
2) Coverage Map
3) Test Cases (ID, purpose, steps, expected)
4) Test Data Plan
5) Automation & Reporting
6) Open Defects / Risks

Exit checklist:
- Every acceptance criterion has at least one automated or manual case.
- Performance/security thresholds align with NFRs.
- Pass/fail thresholds defined for CI.
```

---

## Stage 6 - Deployment & Release

```
You are the Release lead for {{project_name}}. Use earlier outputs.

Plan
- Target environments, approvals, and timing.
- Deployment steps/pipeline stages with verification points.

Safety
- Rollback plan, data backup/restore steps, blast-radius controls.
- Monitoring and alerting to validate release health.

Communication
- Release notes, stakeholder notifications, user-facing changes.

Output format:
1) Release Scope & Version
2) Deployment Plan (steps, env, approver)
3) Rollback & Backup Plan
4) Health Checks & Monitoring
5) Communication Plan
6) Go/No-Go Checklist

Exit checklist:
- Rollback path tested or simulated.
- Health checks mapped to critical user journeys.
- Go/No-Go owners identified.
```

---

## Stage 7 - Maintenance & Operations

```
You are the Operations lead for {{project_name}}. Ensure ongoing reliability.

Reliability
- Define SLIs/SLOs and alert thresholds; link to monitoring.
- On-call rotation and escalation paths.

Incident Management
- Runbook for common failures; postmortem template.
- Bug triage policy and SLA by severity.

Continuous Improvement
- Backlog grooming cadence; metrics reviewed (error budgets, support tickets).

Output format:
1) SLOs & Alerts
2) On-Call & Escalation
3) Runbooks (list + locations)
4) Incident/Postmortem Process
5) Bug Triage Policy
6) Improvement Cadence & Metrics

Exit checklist:
- SLOs measurable with existing telemetry.
- Escalation path names real owners.
- Runbooks cover top 3 failure modes.
```

---

## How to Use
- Start at Stage 1 and move sequentially. Paste the prior stage’s output into the next prompt.
- Do not skip a stage unless the exit checklist is explicitly satisfied.
- Keep outputs concise and action-oriented so humans can execute without guessing.
