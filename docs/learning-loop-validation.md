# Milestone learning validation — 2026-09-08

Scope: extend Agent Workflow Swarms with the optional `loop-improvement` skill and local SQLite runtime, preserving Conductor coordination, plugin identifiers, and MIT licensing. Version 1.4.0 builds on the existing 1.3.0 delivery-loop branch and the continuity audit-write-boundary fix.

The runtime records milestone → sanitized proposal → fixed comparison → reviewed acceptance → scoped retrieval → retirement. It reuses Skill Feedback Engine export schema 1 instead of duplicating observation grouping. State is local to the explicitly selected project. Lessons are advisory and do not authorize shared skill edits or scheduling.

## Observed evidence

- 15 loop runtime tests pass, including fresh-process persistence, regression gates, timeouts, artifact invalidation, read-only state access, concurrent acceptance, retirement, and malformed inputs.
- 21 continuity tests and 4 lineage tests pass.
- 14 static instruction checks pass; these are not behavioral evaluations.
- Repository validation accepts four unique canonical skills, both plugin manifests, marketplace catalogs, publisher inventory, and consistent versions.
- A real Skill Feedback Engine observation/review/export from source commit `1700dfed328585d639e5b61af853bbd69982df09` imported successfully.
- Independent review identified an acceptance race; transaction serialization and a concurrent regression test resolved it. Focused re-review found no remaining blocker in those fixes.
- Required bundled runtime, references, metadata, and MIT license are included. No runtime lesson database is included.

## Release boundaries

These checks prove local runtime contracts, not improved fresh-agent task performance. Host installation, automatic host hooks, and a live StatusGlance adapter have not been verified or implemented. Milestone integration is instruction-driven and opt-in. Historical compatibility results remain historical.

Remaining RunGlance names in README, publisher activation metadata, and its validator are ownership-policy wording; they are not active package identifiers. The swarm's old status instruction and the new proposal examples use current identifiers.

At preparation time GitHub writes return `403 Resource not accessible by integration`, and shell Git has no authenticated credential. Local validation cannot establish remote CI success or a merge. Restore repository write access, push the reviewed commits, run CI on that exact head, and merge only after required checks pass. Do not merge the older PR head while these changes remain local. Registry publication is a separate remaining action.
