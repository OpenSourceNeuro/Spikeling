# Current Supported Firmware

## Purpose

This document records the firmware implementations that appear compatible with
the pre-refactor Spikeling GUI baseline.

It distinguishes:

- compatibility verified from source code;
- compatibility verified on physical hardware;
- historical compatibility;
- unknown compatibility.

This document must not describe a firmware as hardware-supported unless a
physical-board test has been completed and recorded.

## Baseline reference

- GUI baseline tag: `gui-pre-refactor-2026-08-05`
- GUI baseline commit: `b98187c`
- GUI primary entry point:
  `Software/GUI - PyQt6-PySide6/Main.py`
- Investigation date: `2026-08-05`
- Investigation method: read-only source-code inspection
- Hardware accessed during source investigation: No
- Serial ports accessed during source investigation: No

Detailed supporting evidence:

```text
docs/baseline/evidence/2026-08-05_gui-pre-refactor/
codex-firmware-compatibility-audit.md
```

## Compatibility terminology

### Source-level compatible

The inspected GUI and firmware source agree on the core serial configuration,
command framing, binary sample frame, payload size, field ordering, and scaling.

This does not prove that the software has been tested successfully on physical
hardware.

### Hardware verified

The firmware has been built, flashed, and tested on a documented physical board
using the baseline GUI.

The test record must include:

- hardware revision;
- exact firmware commit;
- GUI commit;
- operating system;
- USB interface;
- serial port;
- connection result;
- acquisition result;
- command tests;
- reconnect test;
- shutdown test.

### Historically tested

The firmware was previously reported to work, but it has not been retested
against the documented GUI baseline.

### Unknown

No reliable compatibility evidence is available.

## Compatibility matrix

| Firmware source | Intended hardware family | Source-level compatibility | Hardware verification | Current classification |
|---|---|---:|---:|---|
| `Firmware/Spikeling_V2.5/Spikeling_V2.5.ino` | Spikeling v2.x / v2.5 | Yes | Not completed | Source-level compatible, hardware-unverified |
| `Firmware/Spikeling_V3/Spikeling_V3.ino` | Spikeling v3.x | Yes | Not completed | Source-level compatible, hardware-unverified |

No exact flashed-firmware commit has yet been recorded for a physical test
session.

The term “source-level compatible” means that the inspected transport and
packet implementations match. It does not mean that every GUI control or
physical function has been tested successfully.

## Serial configuration

The baseline GUI and both inspected firmware trees use:

- baud rate: `500000`;
- data bits: `8`;
- parity: none;
- stop bits: `1`;
- flow control: none.

Equivalent notation:

```text
500000 8N1
```

### Timeouts

The GUI does not explicitly configure a serial read or write timeout.

Reception is asynchronous through:

- `QSerialPort.readyRead`;
- `QSerialPort.readAll()`.

No blocking wait-based serial call was identified in the inspected GUI path.

## Command protocol

GUI commands are encoded as UTF-8 text.

Each command is terminated with:

```text
\n
```

Arguments are separated by spaces.

The firmware uses the bundled `SerialCommand` parser with:

- newline command terminator;
- space argument delimiter;
- 32-byte input buffer;
- maximum command token length of 8 characters.

Representative commands include:

```text
CON
DT <value>
BZ0
BZ1
LED0
LED1
FR0
FR1
ST0
ST1
SC0
SC1 <value>
TR
PG0
PG1 <value>
PD0
PD1 <value>
PR0
PR1 <value>
PC0
PC1 <value>
VCM 0
VCM 1
NO0
NO1 <value>
SG10
SG11 <value>
SD10
SD11 <value>
SG20
SG21 <value>
SD20
SD21 <value>
NEU <index>
NE <a> <b> <c> <d>
```

This list is a baseline source inventory rather than a final public protocol
specification.

## Acquisition protocol

The firmware sends a binary acquisition stream.

Each frame contains:

```text
0xAA 0x55
8 × signed little-endian int16
```

Total frame size:

```text
18 bytes
```

Payload order:

1. membrane voltage;
2. stimulus state;
3. total current;
4. synapse 1 membrane voltage;
5. synapse 1 current;
6. synapse 2 membrane voltage;
7. synapse 2 current;
8. trigger state.

Voltage and current fields use a scale factor of 100.

The frame does not include an identified:

- checksum;
- sequence number;
- timestamp;
- explicit payload length;
- firmware version;
- protocol version.

## Responses and acknowledgements

The GUI does not parse textual acknowledgements for normal commands.

The `CON` command invokes a firmware-side connection-indicator action but does
not provide a GUI-consumed version or compatibility response.

Unknown firmware commands produce ASCII text in the form:

```text
Unknown command: ...
```

This text is emitted on the same serial channel as the binary acquisition
frames.

## Known compatibility concern

### Unregistered `VH1` command

The GUI sends:

```text
VH1
```

from a custom-stimulus path in:

```text
Page_Spikeling_NeuronInterface.py
```

No `VH1` registration or handler was found in either:

- `Firmware/Spikeling_V2.5/Serial_functions.h`;
- `Firmware/Spikeling_V3/Serial_functions.h`.

Classification:

```text
Confirmed code-level mismatch; physical effect unverified
```

Required test:

1. Connect a documented v2.5 board.
2. Trigger the corresponding GUI control.
3. Observe whether the firmware emits `Unknown command: VH1`.
4. Record whether the intended hardware action occurs.
5. Repeat on v3 hardware.
6. Preserve serial output and video evidence.

The command must not be removed or replaced until its intended GUI behaviour
has been identified.

## Difference in `NEU` implementation

The `NEU` token is registered in both firmware trees, but it maps to:

- `NeuronMode` in v2.5;
- `NeuronPreset` in v3.

The source-level audit did not establish whether these handlers have equivalent
semantics.

This requires:

- handler-level source comparison;
- GUI intent analysis;
- physical verification where behaviour differs.

## Firmware-version negotiation

No firmware-version or protocol-version negotiation is implemented.

The GUI does not:

- request a firmware version;
- request a protocol version;
- validate a board identifier;
- validate board capabilities;
- reject an incompatible firmware before acquisition.

The `CON` command is not a version handshake.

Consequently, a serial port can appear connected without proving protocol
compatibility.

## Required hardware verification

For every firmware family intended to remain supported, record:

- board hardware revision;
- board identifier;
- firmware source directory;
- exact firmware commit;
- firmware build date;
- compiler or Arduino toolchain version;
- selected board definition;
- USB interface;
- Windows driver;
- COM port;
- GUI baseline commit;
- connection result;
- continuous packet reception;
- startup or diagnostic text;
- command-by-command behaviour;
- `VH1` result;
- `NEU` result;
- disconnect and reconnect result;
- clean shutdown result;
- long-duration acquisition result.

Until these checks are completed, both firmware families remain classified as:

```text
Source-level compatible, hardware-unverified
```
