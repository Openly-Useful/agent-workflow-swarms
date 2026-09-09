# Runtime contract

Python 3.9+ and the standard library are sufficient. The runtime is bundled inside the skill so a host's copied skill directory remains runnable. All commands return JSON; failures exit nonzero. It runs no model, network client, shell, or scheduler itself. Explicit evaluation subprocesses retain normal host permissions and must be trusted and isolated by the caller.

Use `python <skill-dir>/scripts/loop.py --project-root <approved-project> COMMAND`.

| Command | Inputs | Result / writes |
|---|---|---|
| `status` | none | Read-only counts, no state creation |
| `retrieve --task-key KEY` | exact context key | Current accepted advisory lessons, no writes |
| `capture --input milestone.json` | milestone record below | Deduplicated milestone with artifact hashes |
| `propose --milestone ID --input proposal.json` | sanitized SFE export | Immutable proposal linked to milestone |
| `evaluate --proposal ID --input experiment.json` | explicit argv comparisons | Local command evidence, no output/transcript capture |
| `accept --experiment ID --input decision.json` | attributed reviewed decision | Lesson with expiry; failed or changed evidence is rejected |
| `retire --lesson ID --reason TEXT` | existing lesson | Append-only retirement |

Milestone input:

```json
{"milestone":"integration-check","task_key":"session-selection","revision":"source-revision","outcome":"failed","summary":"Ambiguous session selection failed the check","artifacts":["fixtures/candidate.md"]}
```

Use real relative artifact paths and source revisions. Outcomes are accepted, failed, or blocked. Repeated identical inputs deduplicate; a new revision or changed evidence is a new event. Keep summaries brief and sanitized. Private-pattern screening is defense in depth, not a guarantee that arbitrary text is safe to share. State is local-only and is never exported automatically.

Proposal input follows Skill Feedback Engine export schema 1. The runtime consumes only `schema_version`, `proposal_id`, `skill`, `suggested_change`, and `rationale`; it links its own milestone rather than importing private evidence. The SFE schema also permits title, kind, observation IDs, signals, confidence, and delivery metadata, which are not needed here. An agent-prepared fallback must disclose its provenance in the rationale.

```json
{"schema_version":1,"proposal_id":"prop-example","skill":"conductor-swarm","suggested_change":"Select a session explicitly when more than one exists","rationale":"Agent-prepared proposal from the captured failing milestone"}
```

Experiment shape:

```json
{
  "evaluator_revision":"reviewed-suite-revision",
  "lesson_artifacts":["fixtures/candidate.md"],
  "cases":[
    {"id":"ambiguity","role":"target","baseline":["python3","fixtures/check.py","baseline","ambiguity"],"candidate":["python3","fixtures/check.py","candidate","ambiguity"],"timeout_seconds":30,"artifacts":["fixtures/check.py","fixtures/candidate.md"]},
    {"id":"single-session","role":"guard","baseline":["python3","fixtures/check.py","baseline","single-session"],"candidate":["python3","fixtures/check.py","candidate","single-session"],"timeout_seconds":30,"artifacts":["fixtures/check.py","fixtures/candidate.md"]}
  ]
}
```

This is a contract illustration, not a claim that the named fixtures exist. The functional tests include runnable fixtures. Each comparison records exit codes, artifact hashes, evaluator revision, and the input contract digest. Include the baseline, candidate, and check implementation among case artifacts; include all context that determines lesson applicability in `lesson_artifacts`. Exact matching is deliberately conservative. Missing/changed applicability files suppress the lesson until reevaluated. Outputs and argv are not stored in the evidence database; retain the reviewed experiment input locally if reproduction is needed. A zero exit code is only as meaningful as the evaluator's assertions.

Acceptance input:

```json
{"reviewer":"authorized-reviewer-label","rationale":"Target improved and guard checks passed; exact evidence reviewed","expires_at":1900000000}
```

`expires_at` is a future finite Unix timestamp selected for the actual review horizon. Reviewer labels do not authenticate a person. Reaccepting the same experiment returns its existing lesson, preserving the original decision; it cannot silently renew expiry or undo retirement. Changed lessons need a newly reviewed experiment. SQLite transactions deduplicate concurrent identical records. This implementation targets local disks, not network-shared SQLite or cross-machine coordination.

Integration is instruction-driven: an enabled Conductor invokes these commands at milestones and retrieves lessons in later sessions. No background hook, fresh-agent trial runner, cloud memory, production readiness projection, or global scheduler is included.
