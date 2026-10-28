"""Cross-language differential tests: Python emulator versus actual firmware C++.

Compiles the *real* STP_functions.h using a host C++ compiler (no Arduino
libraries needed), drives the same spike schedules through both implementations,
and compares multiplier, utilisation, and resource availability.

If no C++ compiler is installed these tests are explicitly SKIPPED, not passed.
GitHub Actions installs g++ and runs them as required checks.
"""

import math
import random
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = GUI_ROOT.parents[1]
FIRMWARE = REPO_ROOT / "Firmware" / "Spikeling_V3"

sys.path.insert(0, str(GUI_ROOT))
from stp_model import COMBINED, DEPRESSION, FACILITATION, OFF, STPState

HOST_PROGRAM = r"""
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <string>
#include "STP_functions.h"

int main() {
    STPState states[2];
    std::string op;
    std::cout << std::setprecision(9);
    while (std::cin >> op) {
        int synapse;
        if (op == "M") {
            int mode;
            if (!(std::cin >> synapse >> mode)) return 2;
            if (synapse < 0 || synapse > 1) return 3;
            STP_setMode(states[synapse], static_cast<uint8_t>(mode));
        } else if (op == "E") {
            uint32_t step;
            float dt;
            if (!(std::cin >> synapse >> step >> dt)) return 4;
            if (synapse < 0 || synapse > 1) return 5;
            STPState &state = states[synapse];
            const float m = STP_spikeMultiplier(state, step, dt);
            std::cout << m << ' ' << state.u << ' ' << state.x << '\n';
        } else if (op == "Q") {
            if (!(std::cin >> synapse)) return 6;
            STPState &state = states[synapse];
            std::cout << int(state.mode) << ' ' << state.u << ' ' << state.x << '\n';
        } else {
            return 7;
        }
    }
    return 0;
}
"""


class TestFirmwarePythonParity(unittest.TestCase):
    """Use an independent compiler/execution path for firmware regression."""

    @classmethod
    def setUpClass(cls):
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler is None:
            raise unittest.SkipTest("Host C++ compiler unavailable; firmware parity NOT checked")
        cls.temp = tempfile.TemporaryDirectory(prefix="spikeling-stp-parity-")
        root = Path(cls.temp.name)
        source = root / "stp_bridge.cpp"
        cls.binary = root / "stp_bridge"
        source.write_text(HOST_PROGRAM, encoding="utf-8")
        compilation = subprocess.run(
            [compiler, "-std=c++17", "-O2", "-Wall", "-Wextra",
             "-Werror", "-pedantic", "-I", str(FIRMWARE),
             str(source), "-o", str(cls.binary)],
            capture_output=True, text=True, check=False, timeout=60,
        )
        if compilation.returncode != 0:
            raise AssertionError(f"C++ reference compilation failed:\n{compilation.stderr}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "temp"):
            cls.temp.cleanup()

    def run_cpp(self, commands):
        program = subprocess.run(
            [str(self.binary)], input="\n".join(commands) + "\n",
            capture_output=True, text=True, check=False, timeout=15,
        )
        self.assertEqual(program.returncode, 0, program.stderr)
        return [tuple(float(v) for v in row.split())
                for row in program.stdout.splitlines()]

    def test_presets_for_all_modes_and_intervals(self):
        for mode in (OFF, FACILITATION, DEPRESSION, COMBINED):
            commands = [f"M 0 {mode}"]
            python_state = STPState()
            python_state.set_mode(mode)
            t_ms, step = 0.0, 0
            expected = []
            for delta in (0, 0, 1, 10, 500, 1000, 5000, 0, 200000):
                step += delta
                t_ms += delta * 0.1
                commands.append(f"E 0 {step} 0.1")
                multiplier = python_state.spike_multiplier(t_ms, mode)
                expected.append((multiplier, python_state.u, python_state.x))
            actual = self.run_cpp(commands)
            self.assertEqual(len(actual), len(expected))
            for n, (firmware, python_values) in enumerate(zip(actual, expected)):
                with self.subTest(mode=mode, event=n):
                    for a, b in zip(firmware, python_values):
                        self.assertTrue(math.isfinite(a))
                        self.assertAlmostEqual(a, b, delta=3e-5)

    def test_long_random_train_and_synapse_independence(self):
        rng = random.Random(458192)
        modes = (DEPRESSION, COMBINED)
        states = [STPState(), STPState()]
        commands = [f"M {n} {mode}" for n, mode in enumerate(modes)]
        for n, mode in enumerate(modes):
            states[n].set_mode(mode)
        steps = [0, 0]
        expected = []
        for _ in range(500):
            synapse = rng.randrange(2)
            steps[synapse] += rng.randrange(1, 5000)
            commands.append(f"E {synapse} {steps[synapse]} 0.1")
            mode = modes[synapse]
            amplitude = states[synapse].spike_multiplier(steps[synapse] * 0.1, mode)
            expected.append((amplitude, states[synapse].u, states[synapse].x))
        actual = self.run_cpp(commands)
        self.assertEqual(len(actual), len(expected))
        for index, (firmware, python_values) in enumerate(zip(actual, expected)):
            with self.subTest(event=index):
                for a, b in zip(firmware, python_values):
                    self.assertAlmostEqual(a, b, delta=5e-5)

    def test_reset_and_mode_changes_match(self):
        commands = ["M 0 2", "E 0 0 0.1", "E 0 1000 0.1",
                    "M 0 2", "E 0 1001 0.1", "M 0 1",
                    "E 0 1002 0.1", "M 0 0", "E 0 1003 0.1"]
        actual = self.run_cpp(commands)
        self.assertEqual(len(actual), 5)
        self.assertAlmostEqual(actual[0][0], 1.0)
        self.assertLess(actual[1][0], 1.0)
        self.assertAlmostEqual(actual[2][0], 1.0)
        self.assertAlmostEqual(actual[3][0], 1.0)
        self.assertEqual(actual[4][0], 1.0)

    def test_32_bit_step_counter_rollover(self):
        # 0xfffffff0 -> 0x00000010 is 32 model steps, not negative time.
        import math
        for mode in (FACILITATION, DEPRESSION, COMBINED):
            actual = self.run_cpp([
                f"M 0 {mode}",
                "E 0 4294967280 0.1",
                "E 0 16 0.1",
            ])
            python_state = STPState()
            python_state.spike_multiplier(0.0, mode)
            expected = python_state.spike_multiplier(3.2, mode)
            with self.subTest(mode=mode):
                self.assertAlmostEqual(actual[1][0], expected, delta=3e-5)

    def test_invalid_firmware_mode_is_ignored(self):
        result = self.run_cpp(["M 0 2", "E 0 0 0.1", "M 0 9", "Q 0"])
        self.assertEqual(result[-1][0], DEPRESSION)
        self.assertAlmostEqual(result[-1][2], 0.6, delta=1e-6)  # x depleted by U=0.4 at first spike


if __name__ == "__main__":
    unittest.main(verbosity=2)
