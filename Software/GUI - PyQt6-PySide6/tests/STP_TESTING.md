# Spikeling short-term plasticity — automated test battery

The tests in this directory verify the *stage 1–2* STP implementation in
the draft STP feature branch. They do **not** require a physical board.

## Run locally (Windows / PowerShell)

From \`Software/GUI - PyQt6-PySide6\`:

    py -m unittest discover -s tests -p "test_stp*.py" -v

For the Python-only mathematical and emulator-routing tests, standard-library
Python 3.10+ is sufficient:

    py -m unittest -v tests.test_stp_model tests.test_stp_battery tests.test_stp_emulator_integration

For the compiled **firmware-vs-Python parity** checks, install a host C++
compiler (g++ or clang++) and ensure it is on PATH; otherwise that entire
test class is correctly marked as **skipped**. The test compiles the real
\`Firmware/Spikeling_V3/STP_functions.h\`, not a handwritten substitute.

For the real Qt-dialog/serial-command tests, install:

    py -m pip install PySide6

For the recorded CSV content test, install:

    py -m pip install numpy pandas

No serial port is opened by the tests. On Windows, if Qt cannot initialise
without a display, run tests in an ordinary desktop session rather than
setting \`QT_QPA_PLATFORM=offscreen\`. The offscreen platform is used in CI
on Ubuntu.

## Test files

| Module | What it checks |
| --- | --- |
| \`test_stp_model.py\` | Original small STP smoke suite |
| \`test_stp_battery.py\` | Analytical paired-pulse responses, train dynamics, recovery, reset, modes, bounds, polarity and determinism |
| \`test_stp_firmware_parity.py\` | Actual C++ firmware header versus Python model, randomized schedules, resets, two synapses and 32-bit rollover |
| \`test_stp_emulator_integration.py\` | Production \`GetData\` current routing, sign, independent synapses, disabled inputs and decay, using controlled spike events |
| \`test_stp_gui_controls.py\` | Actual PySide6 dialog, combo-box events, serial payloads, reconnect replay and emulator reset, with a mocked serial port |
| \`test_stp_recording.py\` | Production packet recording and CSV extraction of both synaptic-current channels |

## What counts as a pass?

- On CI, *both* workflow jobs must pass.
- The no-dependency job explicitly skips tests that require PySide6/numpy/pandas;
  the second job installs them and must execute all Qt and CSV tests.
- All firmware/Python parity comparisons use float tolerances accounting
  for C++ \`float\` and Python \`float\` precision differences.
- Skipped tests should never be interpreted as evidence that a feature works.

## Limitations and separate hardware validation

The emulator integration suite extracts the *real* \`GetData\` function but
substitutes its presynaptic Izhikevich activity with a deterministic fake spike
source. It tests current routing, not the full Qt runtime or neuron solver.
The C++ parity tests compile only the lightweight STP header on the host;
they are not an Arduino/ESP32-S3 build.

Before merging, also verify on a physical board:
1. The Arduino firmware compiles and uploads.
2. Mode 0 gives the same trace and performance as the unmodified firmware.
3. GUI mode selection, reset and reconnect work over native USB.
4. Presynaptic TTL spike trains of known intervals produce expected PPRs.
5. Negative-gain inhibition and both independent synapses behave correctly.
6. CSV exports contain valid current increments and usable timestamps.
7. STP recovery matches *simulated* time at different speed settings.

**No code in this battery changes neuron dynamics, synaptic gain, or
plasticity state outside the test processes.**
