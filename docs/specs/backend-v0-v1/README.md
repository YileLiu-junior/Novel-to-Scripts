# Backend V0+V1 Spec Index

This directory contains the small-step specs for the V0+V1 backend.

The upstream plan calls them "10 small Specs", but keeps the numbering S0-S10.
This directory preserves that numbering: S0 is the operating-rule preflight,
and S1-S10 are the ten implementation-facing specs.

## Order

1. `S0-agent-operating-rules.md`
2. `S1-fixture-contract.md`
3. `S2-schema-and-id-rules.md`
4. `S3-domain-models.md`
5. `S4-api-dto-and-router.md`
6. `S5-persistence-and-artifacts.md`
7. `S6-validator.md`
8. `S7-ai-provider-and-skill-contract.md`
9. `S8-orchestrator-and-worker.md`
10. `S9-yaml-and-schema-export.md`
11. `S10-smoke-and-acceptance.md`

## Gate Rule

Each spec should leave a checkable artifact. A step is not done just because a
prompt or route exists; it must also have a fixture, schema, code boundary, test
target, or demo proof appropriate to the step.

