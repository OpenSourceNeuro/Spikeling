# Firmware Compatibility Audit

## Audit metadata

- Audit date: `2026-08-05`
- Audit method: read-only source-code inspection using Codex
- GUI baseline tag: `gui-pre-refactor-2026-08-05`
- GUI baseline commit: `b98187c`
- Hardware accessed: No
- Serial ports accessed: No
- Source files modified: No
- Application executed: No

## Purpose

This report records a source-level investigation of compatibility between the
baseline Spikeling GUI and the firmware implementations located under:

- `Firmware/Spikeling_V2.5/`
- `Firmware/Spikeling_V3/`

The investigation distinguishes:

- facts verified directly from source code;
- compatibility inferred from matching protocol implementations;
- historical indications that remain unverified;
- questions requiring physical-board testing.

Source-level compatibility does not constitute hardware-verified support.

## Scope

The investigation examined the GUI serial transport, GUI serial consumers,
firmware serial configuration, firmware command registration, binary packet
generation, and the available protocol documentation.

Principal GUI files inspected:

- `Software/GUI - PyQt6-PySide6/serial_manager.py`
- `Software/GUI - PyQt6-PySide6/Parameters_Settings.py`
- `Software/GUI - PyQt6-PySide6/Graph_Spikeling.py`
- `Software/GUI - PyQt6-PySide6/Graph_Imaging.py`
- `Software/GUI - PyQt6-PySide6/Graph_ExtraCellular.py`
- `Software/GUI - PyQt6-PySide6/Page_Spikeling_NeuronInterface.py`

Principal firmware files inspected:

- `Firmware/Spikeling_V2.5/Spikeling_V2.5.ino`
- `Firmware/Spikeling_V2.5/General_settings.h`
- `Firmware/Spikeling_V2.5/Core_functions.h`
- `Firmware/Spikeling_V2.5/Serial_functions.h`
- `Firmware/Spikeling_V3/Spikeling_V3.ino`
- `Firmware/Spikeling_V3/General_settings.h`
- `Firmware/Spikeling_V3/Core_functions.h`
- `Firmware/Spikeling_V3/Serial_functions.h`
- `Firmware/Librairies/Arduino-SerialCommand/src/SerialCommand.h`
- `Firmware/Librairies/Arduino-SerialCommand/src/SerialCommand.cpp`

Documentation inspected:

- `Firmware/README.md`
- `Documentation/docs/quickstart/what-you-need.md`
- `Documentation/docs/firmware/serial-protocol.md`

---

## Executive summary

The baseline GUI and the v2.5 and v3 firmware source trees implement matching
core serial settings and sample framing:

- baud rate: `500000`;
- data format: 8 data bits, no parity, 1 stop bit;
- flow control: none;
- GUI-to-firmware commands: newline-terminated UTF-8/ASCII text;
- firmware-to-GUI acquisition stream: binary 18-byte frames;
- frame header: `0xAA 0x55`;
- payload: eight signed little-endian 16-bit integers;
- voltage and current scale factor: 100.

The inspected source therefore supports the conclusion that both firmware
trees are compatible with the baseline GUI at the transport and binary-packet
level.

This conclusion remains subject to important limitations:

1. No physical board was tested.
2. The exact firmware currently flashed onto any board was not identified.
3. No firmware-version or protocol-version negotiation exists.
4. The same serial channel can contain both binary sample frames and ASCII
   error messages.
5. The GUI sends a `VH1` command that is not registered in either inspected
   firmware tree.
6. The firmware serial-command parser uses a 32-byte input buffer.
7. The v2.5 and v3 implementations assign different handler names and
   potentially different semantics to the `NEU` command.
8. The binary packet has no checksum, sequence number, timestamp, payload
   length, or protocol identifier.

---

# 1. Serial configuration

## 1.1 Baud rate

The baud rate is set to:

```text
500000 baud
```
