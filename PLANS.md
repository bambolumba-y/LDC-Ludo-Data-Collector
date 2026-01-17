# ExecPlan Rules (for agents)

## What is an ExecPlan?
An ExecPlan is a single self-contained markdown plan that an agent can follow without any prior chat context.

## Non-negotiable requirements
- The agent must follow `EXECPLAN.md` milestone-by-milestone and should not ask the user for next steps.
- The plan must be kept up to date while working:
  - Progress (checkboxes + timestamps)
  - Surprises & Discoveries
  - Decision Log
  - Outcomes & Retrospective
- The work must produce verifiable outputs (files, commands, tests), not just code changes.
- The agent must run tests and include evidence (commands run + outcomes) in the plan.
- Keep changes small and commit frequently.

## Scope constraints for this repository
- Primary goal: collect and prepare CS2 match data from Liquipedia for later ML training.
- Do NOT run long model training jobs as part of completion.
- It is allowed to write optional training code, but it must not be required for acceptance.

## Style requirements
- Use simple language; avoid jargon in documentation and comments.
- Prefer robust parsing and clear error messages over “quick hacks”.
- Respect Liquipedia request limits and caching rules.

## “Done” means
The acceptance checklist in `EXECPLAN.md` passes on a fresh run with clear commands.
