# Spikeling GUI Technical-Debt Register

## Purpose

This register records source-backed architectural weaknesses, protocol risks,
missing safeguards, and maintainability concerns identified during the
pre-refactor investigation.

An entry in this register is not automatically a confirmed user-visible defect.

Confirmed baseline defects belong in:

```text
docs/baseline/current-known-issues.md
```

## Baseline reference

- GUI baseline tag: `gui-pre-refactor-2026-08-05`
- GUI baseline commit: `b98187c92ae94e698c530dbe0ca1b2f31ca80090`
- Initial register date: `2026-08-05`
- Initial evidence source:
  `docs/baseline/evidence/2026-08-05_gui-pre-refactor/
  codex-firmware-compatibility-audit.md`

## Status definitions

- **Open**: identified and not yet addressed.
- **Investigating**: additional analysis or tests are underway.
- **Accepted**: retained deliberately with documented rationale.
- **Planned**: an approved remediation exists.
- **In progress**: remediation is being implemented.
- **Resolved**: remediation and verification are complete.
- **Superseded**: replaced by another entry or architecture decision.

## Priority definitions

- **P0**: immediate safety or data-integrity risk.
- **P1**: high risk to protocol compatibility, correctness, or core workflows.
- **P2**: significant maintainability, reliability, or testability concern.
- **P3**: lower-impact improvement or future-proofing concern.

## Register index

| ID | Title | Area | Priority | Status |
|---|---|---|---|---|
| TD-SERIAL-001 | No firmware or protocol version negotiation | Compatibility | P1 | Open |
| TD-SERIAL-002 | Binary samples and ASCII diagnostics share one stream | Framing and recovery | P1 | Open |
| TD-SERIAL-003 | Sample frames contain no integrity check | Data integrity | P2 | Open |
| TD-SERIAL-004 | Sample frames contain no sequence number or timestamp | Data continuity | P2 | Open |
| TD-SERIAL-005 | Sample frames contain no explicit length or protocol identifier | Framing and evolution | P2 | Open |
| TD-SERIAL-006 | Firmware command parser has a 32-byte input buffer | Command reliability | P1 | Open |
| TD-SERIAL-007 | GUI sends unregistered `VH1` command | Command compatibility | P1 | Open |
| TD-SERIAL-008 | `NEU` maps to different firmware handlers | Cross-version semantics | P2 | Open |
| TD-SERIAL-009 | GUI does not parse command acknowledgements | Error detection | P2 | Open |
| TD-SERIAL-010 | GUI serial timeouts are not explicitly configured | Connection lifecycle | P2 | Open |
| TD-SERIAL-011 | Firmware capabilities are not negotiated | Feature compatibility | P2 | Open |
| TD-DOC-001 | Serial protocol documentation is incomplete | Documentation | P1 | Open |
| TD-TEST-001 | No automated protocol characterisation suite exists | Testing | P1 | Open |
| TD-TEST-002 | No hardware-independent replay transport is established | Testing | P1 | Open |
| TD-TEST-003 | No recorded firmware/GUI compatibility matrix exists | Release assurance | P2 | Open |
| TD-BUILD-001 | USB descriptor configuration depends on build mechanism | Build and USB enumeration | P2 | Open |

## TD-SERIAL-001 — No firmware or protocol version negotiation

### Status

Open

### Priority

P1

### Evidence

No source path was identified in which the GUI:

- requests a firmware version;
- requests a protocol version;
- parses a version response;
- validates a board identifier;
- rejects an incompatible firmware.

The `CON` command is a connection-indicator action rather than a compatibility
handshake.

### Risk

An incompatible firmware can appear connected while:

- producing incorrectly framed data;
- using a different packet layout;
- accepting only some commands;
- interpreting commands differently;
- returning unexpected diagnostic output.

### Recommended direction

Introduce an explicit startup negotiation containing at least:

- firmware semantic version;
- serial-protocol version;
- hardware family;
- board revision where available;
- supported capability flags;
- expected packet size.

### Migration constraint

The current firmware must remain usable during migration.

A compatibility layer may be required for legacy firmware that does not support
the new handshake.

### Verification criteria

- version query and response are documented;
- GUI rejects unsupported protocol versions safely;
- legacy behaviour is explicitly defined;
- tests cover matching, older, newer, malformed, and absent version responses;
- physical verification is completed on intended board families.

## TD-SERIAL-002 — Binary samples and ASCII diagnostics share one stream

### Status

Open

### Priority

P1

### Evidence

Normal acquisition data is emitted as 18-byte binary frames.

Unknown commands generate ASCII diagnostic output through the firmware
`Unrecognized()` handler.

Both forms of output use the same serial channel.

### Risk

ASCII text can appear between binary packets and may:

- delay header resynchronisation;
- be interpreted as packet bytes;
- create transient invalid values;
- increase dropped-frame frequency;
- make parser recovery dependent on accidental byte patterns;
- obscure the actual command failure.

The confirmed `VH1` mismatch provides a plausible trigger for this condition.

### Recommended direction

Consider one or more of:

- encode errors as framed protocol messages;
- use a distinct message-type field;
- disable free-form ASCII diagnostics during binary streaming;
- route diagnostics to a separate interface;
- suspend binary streaming while returning structured command errors.

### Verification criteria

- deterministic mixed-stream fixtures exist;
- parser behaviour is tested against arbitrary ASCII insertion;
- unknown commands produce a structured, parseable result;
- no ASCII text can be mistaken for a valid sample frame;
- hardware replay confirms recovery.

## TD-SERIAL-003 — Sample frames contain no integrity check

### Status

Open

### Priority

P2

### Evidence

The sample frame contains:

- two-byte header;
- 16-byte payload.

No checksum or CRC was identified.

### Risk

A frame can have a valid header but corrupted payload values without detection.

Potential consequences include:

- implausible membrane voltages;
- incorrect currents;
- false trigger values;
- transient plot artefacts;
- corrupted recordings;
- scientific misinterpretation.

### Recommended direction

Evaluate adding:

- CRC-8;
- CRC-16;
- another lightweight checksum.

The choice should consider:

- packet rate;
- firmware CPU load;
- serial overhead;
- backward compatibility;
- recovery behaviour.

### Verification criteria

- corrupted-payload tests fail validation;
- valid legacy and new frames are distinguished;
- performance remains acceptable;
- corruption counters are exposed diagnostically.

## TD-SERIAL-004 — Sample frames contain no sequence number or timestamp

### Status

Open

### Priority

P2

### Evidence

No packet-level sequence number or firmware-generated timestamp was identified.

### Risk

The GUI cannot directly determine:

- whether packets were dropped;
- whether packets were duplicated;
- whether packet order changed;
- whether sampling intervals were irregular;
- whether a reconnect created a discontinuity.

For scientific recording, silent packet loss is particularly problematic.

### Recommended direction

Evaluate adding:

- monotonically increasing sequence number;
- firmware sample counter;
- firmware timestamp;
- explicit stream-reset marker.

### Verification criteria

- dropped and duplicate packets are detected;
- counter rollover is handled;
- reconnect discontinuities are visible;
- recordings preserve continuity metadata;
- plotting and export remain performant.

## TD-SERIAL-005 — Sample frames contain no explicit length or protocol identifier

### Status

Open

### Priority

P2

### Evidence

The current parser assumes:

- fixed two-byte header;
- fixed 16-byte payload;
- fixed field order.

No explicit frame length, message type, or protocol version is present.

### Risk

Future packet evolution can break the parser without a clean migration path.

Adding fields or alternate message types may cause:

- permanent loss of framing;
- misinterpreted values;
- silent compatibility failures;
- duplicated legacy parsers.

### Recommended direction

Design a versioned frame envelope containing:

- synchronisation marker;
- protocol version;
- message type;
- payload length;
- payload;
- integrity check.

### Verification criteria

- multiple message types can coexist;
- unknown message types can be skipped safely;
- legacy protocol remains explicitly supported or rejected;
- malformed length fields are tested.

## TD-SERIAL-006 — Firmware command parser has a 32-byte input buffer

### Status

Open

### Priority

P1

### Evidence

The bundled `SerialCommand` parser defines a 32-byte input buffer.

The GUI can send a custom-neuron command:

```text
NE <a> <b> <c> <d>
```

The complete command length depends on:

- parameter signs;
- integer digits;
- decimal precision;
- spaces;
- newline termination.

### Risk

Long commands may be:

- truncated;
- rejected;
- split incorrectly;
- interpreted using partial arguments;
- followed by an unknown-command response;
- silently ineffective.

### Recommended direction

First determine the exact maximum command length produced by the GUI.

Then consider:

- reducing numeric formatting precision where scientifically acceptable;
- validating encoded command length before sending;
- increasing the firmware buffer;
- replacing free-form ASCII parameters with a structured binary command;
- returning explicit command errors.

### Verification criteria

- tests generate minimum and maximum supported values;
- all encoded commands remain within the supported limit;
- over-length commands are rejected before transmission;
- firmware behaviour is deterministic;
- parameter precision remains adequate.

## TD-SERIAL-007 — GUI sends unregistered `VH1` command

### Status

Open

### Priority

P1

### Evidence

The GUI sends `VH1` from:

```text
Page_Spikeling_NeuronInterface.py:242
```

No matching command registration exists in either inspected firmware tree.

Related baseline issue:

```text
GUI-BASE-001
```

### Risk

The associated GUI function may:

- have no hardware effect;
- emit an unknown-command response;
- inject ASCII into the binary stream;
- mislead the user into believing a setting was applied.

### Recommended direction

Trace the intended GUI operation before modifying the command.

Determine whether:

- `VH1` is obsolete;
- the token is misspelled;
- firmware registration is missing;
- another registered command is intended;
- the complete feature should be removed.

### Verification criteria

- intended function is documented;
- correct GUI-to-firmware command is established;
- protocol test covers the command;
- hardware behaviour is tested;
- no free-form ASCII contaminates acquisition;
- baseline issue is updated.

## TD-SERIAL-008 — `NEU` maps to different firmware handlers

### Status

Open

### Priority

P2

### Evidence

The `NEU` command maps to:

- `NeuronMode` in v2.5;
- `NeuronPreset` in v3.

### Risk

The same GUI command may have different effects across board families.

Potential consequences include:

- different neuron presets;
- different parameter resets;
- incompatible mode changes;
- inconsistent educational experiments.

### Recommended direction

Perform a focused comparison of both handlers:

- accepted argument range;
- parameter changes;
- reset behaviour;
- side effects;
- persistence;
- response behaviour.

Document whether the semantics are:

- equivalent;
- intentionally different;
- accidentally divergent.

### Verification criteria

- handler comparison is documented;
- GUI expectations are explicit;
- cross-version tests exist;
- physical behaviour is compared where possible;
- capability negotiation handles intentional differences.

## TD-SERIAL-009 — GUI does not parse command acknowledgements

### Status

Open

### Priority

P2

### Evidence

No GUI path was identified that parses textual success acknowledgements for
normal commands.

The `CON` command does not provide a GUI-consumed compatibility response.

### Risk

The GUI may display a new setting even when:

- the command was not recognised;
- the firmware rejected an argument;
- the serial write was incomplete;
- the firmware was disconnected;
- the firmware applied a different value.

This can create divergence between displayed state and hardware state.

### Recommended direction

Introduce structured command responses containing:

- command identifier;
- success or failure;
- applied value;
- error code;
- capability or range information where applicable.

### Verification criteria

- GUI distinguishes requested and confirmed state;
- failed commands are visible;
- malformed values produce explicit errors;
- timeouts and retries are defined;
- tests cover delayed, duplicate, missing, and negative acknowledgements.

## TD-SERIAL-010 — GUI serial timeouts are not explicitly configured

### Status

Open

### Priority

P2

### Evidence

The GUI uses asynchronous `QSerialPort` reception.

No explicit read or write timeout was identified.

### Risk

Although asynchronous operation avoids a blocking read timeout, the
application may lack defined timing rules for:

- connection establishment;
- first valid frame;
- command confirmation;
- stream interruption;
- stalled firmware;
- disconnect detection.

### Recommended direction

Define application-level timing policies, such as:

- maximum time to first valid frame;
- inactivity timeout;
- command-response timeout;
- reconnect backoff;
- shutdown timeout.

These policies should not block the GUI thread.

### Verification criteria

- stalled connection is detected;
- user receives a clear state indication;
- reconnect logic is bounded;
- shutdown completes deterministically;
- tests use controllable simulated timing rather than arbitrary sleeps.

## TD-SERIAL-011 — Firmware capabilities are not negotiated

### Status

Open

### Priority

P2

### Evidence

The GUI does not request a capability list before enabling controls.

The firmware trees contain potentially differing handlers and additional
commands that were not observed in the GUI.

### Risk

The GUI may expose controls that:

- are unsupported;
- use different semantics;
- require hardware absent from a board revision;
- silently fail.

Conversely, supported firmware capabilities may remain inaccessible.

### Recommended direction

Add capability negotiation covering:

- supported command groups;
- optional sensors;
- stimulation modes;
- neuron presets;
- protocol features;
- packet fields;
- hardware revision.

### Verification criteria

- unsupported controls are disabled or hidden;
- optional features are enabled from declared capabilities;
- both firmware families expose deterministic capability sets;
- unknown capability flags are ignored safely.

## TD-DOC-001 — Serial protocol documentation is incomplete

### Status

Open

### Priority

P1

### Evidence

The existing serial-protocol document contains TODO or incomplete sections.

The source code currently acts as the practical protocol specification.

### Risk

Protocol behaviour can diverge between:

- GUI implementation;
- v2.5 firmware;
- v3 firmware;
- documentation;
- future contributors’ assumptions.

This increases the probability of accidental compatibility breaks.

### Recommended direction

Create an authoritative versioned protocol specification containing:

- transport settings;
- connection lifecycle;
- textual command grammar;
- complete command registry;
- argument types and ranges;
- responses and errors;
- binary frame structure;
- scaling and units;
- version negotiation;
- capability negotiation;
- backward-compatibility policy.

### Verification criteria

- every implemented command is documented;
- every documented command is implemented or explicitly deprecated;
- GUI and firmware tests derive expectations from the specification;
- protocol changes require an architecture decision and migration note.

## TD-TEST-001 — No automated protocol characterisation suite exists

### Status

Open

### Priority

P1

### Evidence

No substantive automated GUI protocol test suite was identified during the
orientation and firmware audit.

### Risk

Refactoring can unintentionally change:

- command strings;
- newline termination;
- numeric formatting;
- frame parsing;
- resynchronisation;
- scaling;
- field order;
- reconnect behaviour.

### Recommended direction

Create unit tests for:

- complete valid frame;
- frame split across reads;
- several frames in one read;
- leading noise;
- ASCII inserted between frames;
- malformed header;
- truncated payload;
- reconnect with partial buffered frame;
- scaling;
- command encoding;
- maximum command length;
- `VH1`;
- `NEU`;
- unknown commands.

### Verification criteria

- protocol tests run without hardware;
- fixtures include real captured byte streams;
- baseline behaviour is characterised before structural changes;
- CI runs the suite on every pull request.

## TD-TEST-002 — No hardware-independent replay transport is established

### Status

Open

### Priority

P1

### Evidence

The current baseline evidence directories do not yet contain an established
replay-based acquisition mechanism.

### Risk

Testing remains dependent on:

- physical board availability;
- serial-port state;
- firmware version;
- nondeterministic timing;
- external electrical conditions.

This makes regression detection slow and unreliable.

### Recommended direction

Introduce a replay or fake transport capable of reproducing:

- recorded raw byte streams;
- controlled fragmentation;
- timing variation;
- connection loss;
- malformed packets;
- command responses.

The replay transport should feed the same decoder path used by the physical
serial transport.

### Verification criteria

- one real baseline recording can be replayed deterministically;
- decoded values match expected results;
- GUI or application-state integration works without hardware;
- replay speed can be controlled;
- CI uses replay tests.

## TD-TEST-003 — No recorded firmware/GUI compatibility matrix exists

### Status

Open

### Priority

P2

### Evidence

The source-level compatibility investigation identified two relevant firmware
trees, but no complete physical compatibility record was available.

### Risk

Support claims may be based on memory rather than reproducible evidence.

A GUI change may break one board family while still working on another.

### Recommended direction

Maintain a compatibility matrix containing:

- GUI version or commit;
- hardware revision;
- firmware version or commit;
- operating system;
- USB interface;
- driver;
- result of automated protocol tests;
- result of manual smoke tests;
- known exceptions.

### Verification criteria

- every supported release has at least one recorded matrix entry;
- hardware-unverified combinations are labelled clearly;
- release notes identify protocol compatibility;
- unsupported combinations are not implied to work.

## TD-BUILD-001 — USB descriptor configuration depends on build mechanism

### Status

Open

### Priority

P2

### Evidence

Historical Git-object comparison showed two different v3 descriptor mechanisms.

At the preserved baseline commit
`b98187c92ae94e698c530dbe0ca1b2f31ca80090`, the firmware:

- included `USB.h`;
- included `USBCDC.h`;
- configured USB manufacturer and product descriptors through runtime API
  calls;
- used manufacturer `Open Source Neuro`;
- used product `Spikeling v3.2`.

At the later checkout
`5b2ce9fdde6f4fa630ac9bf3c6ba601b165eabd3`, runtime descriptor calls were
removed and `Firmware/Spikeling_V3/build_opt.h` was added with:

```text
-DUSB_MANUFACTURER="Open Source Neuro"
-DUSB_PRODUCT="Spikeling"
-DUSB_SERIAL="__MAC__"
```

The historical comparison found no serial command or binary-packet change.

### Risk

USB manufacturer, product, and serial descriptors may depend on:

- Arduino core behaviour;
- whether the selected build tool recognises `build_opt.h`;
- selected ESP32-S3 board definition;
- native USB mode;
- compiler flags;
- clean versus incremental builds;
- operating-system enumeration and descriptor caching.

A build can therefore preserve the serial protocol while presenting unexpected
USB metadata or enumerating differently.

Potential consequences include:

- changed device names in operating-system interfaces;
- inconsistent serial-port identification;
- inability to distinguish multiple boards;
- user confusion during connection;
- differences between IDE, CLI, and CI builds;
- apparent regressions caused by stale cached descriptors.

### Recommended direction

Define and document one supported descriptor mechanism for the v3 firmware.

The build documentation should specify:

- supported Arduino IDE or CLI version;
- ESP32 Arduino core version;
- selected board definition;
- native USB options;
- whether `build_opt.h` is mandatory;
- expected manufacturer, product, and serial values;
- clean-build requirements;
- how descriptor changes are versioned.

Where practical, add an automated build check that confirms the expected
compiler options are applied.

### Verification criteria

- compile the baseline and current v3 firmware with the documented toolchain;
- confirm whether `build_opt.h` is consumed;
- inspect manufacturer, product, and serial descriptors on physical hardware;
- verify enumeration after erase, flash, reset, disconnect, and reconnect;
- test at least the supported Windows environment;
- document descriptor caching behaviour;
- verify that descriptor changes do not alter sample framing or command
  behaviour;
- record the exact toolchain, core version, board definition, firmware commit,
  and observed descriptors.

## Review and maintenance policy

Each technical-debt entry should be reviewed when:

- a related refactor is proposed;
- a protocol change is proposed;
- a firmware release is prepared;
- a GUI release is prepared;
- a related defect is reproduced;
- new hardware support is added.

Closing an entry requires:

1. an implementation or explicit acceptance decision;
2. test evidence;
3. updated documentation;
4. relevant hardware verification where necessary;
5. the resolving commit or pull request;
6. assessment of backward compatibility.

Technical-debt remediation should be performed through bounded, independently
reviewed changes rather than a single protocol rewrite.
