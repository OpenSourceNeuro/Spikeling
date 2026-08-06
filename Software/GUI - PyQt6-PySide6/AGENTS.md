# Spikeling GUI Agent Instructions

## Scope

These instructions apply to:

`Software/GUI - PyQt6-PySide6`

## Canonical documentation

GUI refactor documentation is stored under:

`docs/`

Use:

- `docs/baseline/` for the preserved pre-refactor state;
- `docs/architecture/` for current-system analysis, target architecture,
  roadmaps, and architecture decisions.

Do not create competing GUI-refactor documentation trees elsewhere in the
repository.

## Environment

Use the project interpreter explicitly:

`.venv/Scripts/python.exe`

Do not assume that the shell command `python` points to the project
environment.

The primary application entry point is `Main.py`.

`Tetrode.py` is both an imported GUI component and a separate standalone
entry point. Changes to it must account for both execution contexts.

## Current refactor policy

- Preserve established behaviour before restructuring.
- Add characterization tests before changing critical runtime behaviour.
- Do not migrate Qt bindings as part of an unrelated task.
- Do not redesign visual behaviour during a structural refactor.
- Do not remove apparently unused code without checking dynamic imports,
  generated UI connections, configuration references, and Qt signal wiring.

## Qt constraints

- Modify widgets only from the GUI thread.
- Do not perform blocking serial or file I/O in the GUI thread.
- Worker startup, shutdown, ownership, and cleanup must be explicit.
- Worker-to-GUI communication must use safe Qt mechanisms.
- Detect and prevent duplicate signal connections.
- Closing the application must release worker and serial resources.

## Serial and firmware constraints

- Treat packet framing, field sizes, byte order, command identifiers, and
  payload formats as public interfaces.
- Do not alter the serial protocol without explicit approval and protocol
  tests.
- Keep transport, packet decoding, application state, and widgets conceptually
  separate.
- Test partial frames, concatenated frames, malformed frames, reconnects, and
  decoder reset behaviour.
- Ordinary tests must not require physical hardware.

## Review priorities

Flag:

- firmware incompatibility;
- malformed serial parsing;
- GUI-thread violations;
- object-lifecycle errors;
- stale workers;
- duplicate signals;
- duplicated mutable state;
- direct serial decoding inside widgets;
- direct widget manipulation from transport code;
- untested behavioural changes.
