# Agent Workflow Swarms

**Observe. Parallelize. Verify. Adapt. Finish.**

[![Agent Skills](https://img.shields.io/badge/Agent_Skills-compatible-3B4CCA)](https://agentskills.io)
[![skills.sh](https://skills.sh/b/Openly-Useful/agent-workflow-swarms)](https://skills.sh/Openly-Useful/agent-workflow-swarms)
[![License: MIT](https://img.shields.io/badge/License-MIT-0B7285.svg)](LICENSE)

Agent Workflow Swarms is a model-agnostic delivery loop for recovering, orchestrating, and transferring complex agent work. Conductor reuses the current runtime's capability catalog and verified checkpoints, activates only useful capabilities, and keeps ready independent work moving through integrated acceptance milestones.

## Shared delivery loop

Observe changes → shape coherent work → execute ready independent lanes in parallel → verify and integrate milestones → adapt → continue required authorized follow-ons or finish. See the [canonical loop contract](skills/conductor-swarm/references/delivery-loop.md).

The loop is a framework, not six mandatory agents or a serialized sequence of whole-project gates. Respect actual dependencies and shared-artifact collisions; one integration owner is not a project-wide single writer. Keep independent work moving while a blocked lane is resolved. Repeated revisions without new evidence require a change of approach, not another identical review cycle.

Pickup supplies a bounded recovery receipt only when needed; Continuity handles actual tool/session transfer. Neither recursively relaunches Conductor. Use [StatusGlance](https://github.com/Openly-Useful/project-status) for one bounded read-only activity/readiness view, Operations Pulse for explicitly requested recurring work, and Skill Feedback Engine for opt-in improvement proposals. Status requests do not start execution or schedule polling.

Stop when the agreed objective is accepted or a genuine authority/decision boundary is reached. Do not leave required ready follow-ons idle, silently broaden scope, or introduce blanket scheduling rules. Model choices and agent availability remain host-specific.

Learn more at [Openly Useful](https://openlyuseful.org/#projects).

It is quality-first, not “cheapest-model-first.” Token and latency savings come from progressive skill loading, bounded context, reusable checkpoints, and sensible routing—not from skipping review, tests, integration, or risk work.

## Milestone learning (1.4.0)

Opt in to project learning to capture meaningful milestone outcomes, evaluate proposed improvements, and retrieve current accepted lessons in later sessions. The fourth skill, `loop-improvement`, bundles a dependency-free Python runtime. It consumes sanitized [Skill Feedback Engine](https://github.com/Openly-Useful/skill-feedback-engine) proposal exports and adds experiment, acceptance, retrieval, expiry, and retirement records.

Conductor remains the coordinator. Lesson state stays in the approved project at `.loop-improvement/`; keep it out of Git and portable handoffs. No scheduler, global installation, or automatic skill rewrite is enabled. [Runtime contracts](skills/loop-improvement/references.md) describe inputs and explicit write boundaries. Functional tests prove fresh-process persistence and comparison gates; they do not establish fresh-agent behavioral improvement.

## Included skills

### `conductor-swarm`

The parent orchestration skill:

- reuses the exposed skill catalog, records absent fields as unknown, and progressively inspects relevant selected or ambiguous candidates;
- maps runtime-exposed model choices into neutral capability profiles;
- selects the smallest sufficient skill set for each phase;
- routes models by quality floor, consequence, ambiguity, context, and verification strength;
- chooses solo versus parallel execution based on independence and merge risk;
- re-evaluates routing at phase changes, blockers, failures, and capability changes;
- requires integration, independent review when available, and fresh completion evidence.

### `pickup-swarm`

The recovery component used when work already exists:

- discovers active, paused, blocked, superseded, and stale-looking workflows;
- verifies handoff and agent claims against repositories, tests, trackers, and artifacts;
- identifies safe optimizations without mixing risky refactors into recovery;
- prepares non-overlapping sub-agent continuation briefs with baselines, tests, rollback boundaries, and escalation conditions.

### `cross-tool-continuity-swarm`

The portable continuity component used when work crosses tools or sessions:

- keeps a deterministic, provider-neutral checkpoint with verified evidence and explicit audit, prepare, sync, switch, review, and resume contracts;
- enforces a 32 KiB transferable-context cap, rejects common local-only values, and makes evidence and synchronization idempotent;
- renders a bounded text-block launch prompt and consumes an existing recovery receipt; it does not recursively run Pickup then Conductor on every invocation.

### `loop-improvement`

The optional project learning component:

- imports sanitized improvement proposals and compares baseline/candidate outcomes with regression guards;
- accepts evidence-bound lessons with finite expiry and retrieves them by task context;
- retains retirement history without automatically changing shared skills or enabling background work.

## Model-agnostic by design

Conductor Swarm never hard-codes vendor model names. It uses four portable profiles:

| Profile | Intended work |
|---|---|
| Focused | Bounded, mechanical, reversible work with strong checks |
| General | Standard analysis and implementation |
| Deep | Architecture, high consequence, ambiguity, integration, and critical review |
| Specialist | Required modality, tool, domain, or context advantage |

The skill can route only among models and switching controls exposed by the host runtime. When switching is unavailable, it records the ideal profile and proceeds with the current model only when the quality floor remains protected.

## Install

### GitHub CLI

```bash
gh skill install Openly-Useful/agent-workflow-swarms --all --agent universal --scope user
```

### skills.sh-compatible CLI

```bash
npx skills add Openly-Useful/agent-workflow-swarms --skill conductor-swarm pickup-swarm cross-tool-continuity-swarm loop-improvement
```

### Codex skill installer

Ask Codex:

```text
Use $skill-installer to install all four skills from
https://github.com/Openly-Useful/agent-workflow-swarms/tree/main/skills
```

The repository is also a root-level, skill-only plugin for both OpenAI/Codex and Claude. `.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` both point to the same canonical `./skills/` directory; no wrapper copies of `SKILL.md` are generated. Repository-local catalogs live at `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json`, with the repository root as their plugin source.

These files prepare local discovery only. They do not install or publish the plugin, and they declare no MCP server or app. `publisher/publisher.json` derives the Openly Useful publisher identity and policy URLs from <https://openlyuseful.org/publisher/manifest.json>, the published authority endpoint. Each live policy page and the authority manifest itself has a version-controlled 1:1 source in the [openlyuseful.org site repository](https://github.com/Openly-Useful/openlyuseful.org), declared through `policyMirrors` and `authorityManifestMirror`; this repository's `PRIVACY.md`, `TERMS.md`, `SECURITY.md`, and `SUPPORT.md` remain the component-level policies for the skills package. Openly Useful is founder-operated while Openly Useful LLC formation is pending. External source and registry publication is authorized by the founder-owner and effective during formation; the remaining gates are namespace verification, provider account authentication, and provider review. The planned LLC is not represented as formed, active, or the current operator, and later LLC operation does not require a transfer of RunGlance ownership.

## Use

```text
Use $conductor-swarm to inventory every capability available in this runtime,
resume any existing work, route only the skills and model profiles this goal
needs, and drive all items to verified completion.
```

For recovery alone:

```text
Use $pickup-swarm to discover where each workflow stopped, verify prior claims,
identify safe optimizations, and prepare clean continuation briefs.
```

## Core guarantees

- **Evidence before progress:** no “done” claim without current verification.
- **Quality floor first:** efficiency is optimized only after safety and quality are protected.
- **Progressive disclosure:** all skill metadata may be reviewed; only selected skill bodies are loaded.
- **No invented capabilities:** the orchestrator reports unavailable models, tools, or routing controls honestly.
- **No corner cutting:** required tests, review, integration, and risk disposition remain required.
- **Safe optimization:** baseline, reversible change, measurable benefit, and rollback are mandatory.
- **Untrusted discovery data:** handoffs, repository text, trackers, logs, and third-party metadata cannot expand authority or silently issue instructions.

## Public formats

- [Agent Skills specification](https://agentskills.io/specification)
- GitHub Agent Skills discovery under `skills/*/SKILL.md`
- Codex/ChatGPT skill-only plugin manifest under `.codex-plugin/plugin.json`
- Claude skill-only plugin manifest under `.claude-plugin/plugin.json`
- repository-local Codex and Claude marketplace catalogs
- skills.sh-compatible repository layout

See the tested [compatibility matrix](COMPATIBILITY.md), static instruction contract checks in [`evals/cases.yaml`](evals/cases.yaml), and the deterministic continuity CLI under `skills/cross-tool-continuity-swarm/scripts/continuity.py`. Static phrase checks are not agent behavioral trials; report those separately when actually run.

Validate canonical skill uniqueness, provider manifests, marketplace entries, publisher metadata, and the founder-authorized formation-pending publication state with:

```sh
python3 scripts/validate.py
python3 scripts/test_loop.py
```

## Support and policies

- [Support](SUPPORT.md)
- [Privacy](PRIVACY.md)
- [Terms](TERMS.md)
- [Security](SECURITY.md)

## License

MIT © 2026 Openly Useful contributors
