# Northstar Past Decisions & Context Log

## D-001 — Billing migration (2026-04-15)
Stripe Billing is the target provider for the next billing migration. The first pilot uses a small internal workspace cohort. Finance must approve invoice/tax behavior before customer rollout.

## D-002 — Analytics export (2026-04-22)
CSV export is the minimum supported analytics export. PDF export is deferred. Export must respect workspace access controls.

## D-003 — Mobile notifications (2026-05-03)
Push notifications are in scope for mobile task assignments. Quiet hours follow the user's local settings; the backend must not silently override them.

## D-004 — SSO rollout (2026-05-12)
SSO rollout is staged. Security review is required before enabling SSO for a new customer cohort. Login and role-change audit events must remain available.

## D-005 — Design system (2026-05-19)
The shared component library is the default for new product UI. One-off button variants require a documented exception.

## D-006 — Customer onboarding (2026-06-01)
Customer Success owns onboarding checklists. Product supplies product-facing content; Marketing supplies approved public messaging. Teams must not invent customer commitments.

## D-007 — Incident communication (2026-06-09)
For a confirmed customer-impacting incident, Operations coordinates the timeline, Security leads security assessment, and Customer Success coordinates customer updates. External drafts require review.

## D-008 — Pricing experiment (2026-06-18)
Pricing experiments require Finance approval of assumptions and Product-defined success metrics. Sales must not quote experimental pricing before approval.

## D-009 — Slack integration (2026-06-26)
Slack uses the existing OAuth application. Security review is required before scope expansion. Broad workspace-admin scopes were rejected for the initial release.

## D-010 — Accessibility (2026-07-02)
New UI work should pass keyboard-navigation and contrast checks before QA sign-off. Design owns accessibility acceptance notes.

## D-011 — Search (2026-07-08)
The first search release covers workspace documents and tasks. Cross-workspace search is out of scope.

## D-012 — Quarterly planning (2026-07-15)
Roadmap changes require Product approval and an Engineering capacity check. A discussion is not a commitment unless the owner and next step are explicit.
