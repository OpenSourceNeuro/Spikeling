# Spikeling Repository Agent Instructions

## Project status

The Spikeling GUI is undergoing a controlled architectural audit and
incremental refactor.

The Git tag `gui-pre-refactor-2026-08-05` identifies the preserved
pre-refactor application baseline.

## Mandatory scope control

- Do not modify files unless the task explicitly authorizes modifications.
- Read-only tasks must remain strictly read-only.
- Do not change Git branches, stage files, commit, push, pull, merge, reset,
  clean, or rewrite history unless explicitly instructed.
- Do not install or update dependencies unless explicitly instructed.
- Do not access physical hardware or serial ports unless explicitly instructed.
- Do not perform repository-wide rewrites.
- Do not combine unrelated changes.
- Separate verified facts, inferences, concerns, and recommendations.

## Before modifying code

1. Trace the affected runtime path.
2. Identify callers and dependants.
3. Identify public interfaces.
4. Identify firmware and protocol consequences.
5. Identify Qt signal, threading, lifecycle, and state consequences.
6. Identify existing tests and missing characterization tests.
7. Present a bounded implementation plan.
8. Wait for approval when requested.

## Verification

After an authorized code change:

- run the smallest relevant tests first;
- run the complete non-hardware test suite;
- report all commands executed;
- report changed files;
- report unresolved risks;
- do not commit automatically.
