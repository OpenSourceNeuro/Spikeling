# Big Spiky serial protocol

Transport is native USB CDC with `Serial.begin(500000)`. Multi-byte integers are **little-endian**, floats
never appear on the wire, and streaming contains no unsolicited ASCII debug text. Command responses are
ASCII lines beginning `#BSOK`, `#BSERR` or `#BSSTATUS` and occur only in response to host commands.

## Protocol 1: exact Spikeling legacy frame

Select with `BSPROTO 1` (the boot default). Every 2 ms the device sends:

| Frame offset | Size | Field | Scaling / meaning |
| ---: | ---: | --- | --- |
| 0 | 1 | Header | `0xAA` |
| 1 | 1 | Header | `0x55` |
| 2 | 2 | `v_q` | `Vm × 100`, signed int16 |
| 4 | 2 | `stim_state` | Retained signed central/stimulus state |
| 6 | 2 | `Itot_q` | current × 100; clamp current in voltage-clamp mode |
| 8 | 2 | `syn1_vm_q` | analogue Vm input 1 × 100, or zero until valid |
| 10 | 2 | `Isyn1_q` | synaptic current 1 × 100 |
| 12 | 2 | `syn2_vm_q` | analogue Vm input 2 × 100, or zero until valid |
| 14 | 2 | `Isyn2_q` | synaptic current 2 × 100 |
| 16 | 2 | `trigger_q` | one-shot trigger state |

The payload after the two-byte header is exactly 16 bytes. It is not enlarged or reinterpreted as V2.

Example resting frame (`Vm = −70.00 mV`, all other fields zero):

`AA 55 A8 E4 00 00 00 00 00 00 00 00 00 00 00 00 00 00`

## Protocol 2: extended Big Spiky frame

Select with `BSPROTO 2`. The firmware sends one 82-byte frame every five model steps (100 Hz default).
The four-byte sync word is ASCII `BSPK`, chosen so a host can scan and recover after dropped bytes.

| Offset | Size | Type | Field |
| ---: | ---: | --- | --- |
| 0 | 4 | bytes | `42 53 50 4B` (`BSPK`) |
| 4 | 1 | uint8 | protocol version = 2 |
| 5 | 1 | uint8 | packet flags, currently 0 |
| 6 | 2 | uint16 | payload length = 74 bytes (offsets 8–81) |
| 8 | 4 | uint32 | sequence number, reset on protocol selection |
| 12 | 4 | uint32 | `micros()` timestamp; wrap-safe host handling required |
| 16 | 2 | int16 | Vm × 100 |
| 18 | 2 | int16 | total current × 100 |
| 20 | 1 | uint8 | physical/model output spike flag |
| 21 | 2 | uint16 | incoming-spike mask, bits 0–11 = inputs 1–12 |
| 23 | 24 | int16[12] | signed gains × 100 |
| 47 | 24 | int16[12] | synaptic currents × 100 |
| 71 | 2 | int16 | patch + external current control × 100 |
| 73 | 2 | int16 | Gaussian sigma control × 100 |
| 75 | 1 | uint8 | trigger state |
| 76 | 4 | uint32 | status/error flags |
| 80 | 2 | uint16 | CRC-16/CCITT-FALSE |

CRC parameters: polynomial `0x1021`, initial value `0xFFFF`, no reflection, no final XOR. The CRC covers
offsets 4–79 inclusive (76 bytes) and excludes the four-byte sync word and CRC field. The standard
`123456789` check value is `0x29B1`.

Status bits: 0–3 ADC-device fault, 4 ADC-channel fault, 5 model overrun, 6 serial overflow, 7 event-counter
saturation, 8 visual-queue overflow, 9 self-test active, 10 LEDs disabled, 11 quiet display, 12 voltage clamp.
Flags are sticky where they report a historical failure; live mode flags clear when the state clears.

## Indexed commands

Commands are newline terminated and arguments are separated by spaces. Indices are one-based.

| Command | Valid range | Effect |
| --- | --- | --- |
| `BSG <1..12> <gain>` | gain −20..+20 | Set signed gain and disable that channel's pot override. |
| `BSD <1..12> <decay>` | 0..1 | Set independent per-model-step current decay coefficient. |
| `BSPOT <1..12> <0|1>` | Boolean | Disable/enable physical gain pot. |
| `BSEN <1..12> <0|1>` | Boolean | Disable/enable integration; disabling clears current. |
| `BSBRI <0..100>` | Percent | Accepted range is 0–100; applied output is capped at the configured 30%. |
| `BSPROTO <1|2>` | Version | Select exact legacy or extended stream. |
| `BSSTATUS` | none | Return one diagnostics line. |
| `BSSELFTEST` | none | Start the labelled, low-brightness visual-only sequence. |

Invalid indices, missing/extra tokens, non-finite floats, trailing characters and out-of-range values are
rejected. Examples: `BSG 0 5`, `BSD 13 0.99`, `BSG 1 nan`, `BSBRI 101`.

## Retained legacy commands

`NEU`, `NE`, `PC1/PC0`, `VCM`, `VPID`, `VIL`, `VSP`, `VRS`, `NO1/NO0`, `PG1/PG0`, `SG11/SG10`,
`SD11/SD10`, `SG21/SG20`, `SD21/SD20`, `TR`, `FR1/FR0`, `ST1/ST0`, `SC1/SC0`, `LED1/LED0`,
`BZ1/BZ0`, and `CON` are parsed. `DT` is retained but only accepts 2000 in the fixed exhibition profile.
The buzzer commands are harmless compatibility no-ops because Big Spiky V1 has no buzzer output.

