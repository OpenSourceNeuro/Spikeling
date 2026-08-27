#!/usr/bin/env bash
set -euo pipefail
test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
build_dir="${1:-$test_dir/build}"
mkdir -p "$build_dir"
cxx_flags=(-std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror)
g++ "${cxx_flags[@]}" "$test_dir/test_bigspiky_logic.cpp" -o "$build_dir/test_bigspiky_logic"
g++ "${cxx_flags[@]}" "$test_dir/timing_sim.cpp" -o "$build_dir/timing_sim"
g++ "${cxx_flags[@]}" -I"$test_dir/stubs" -I"$test_dir/.." \
  -x c++ -c "$test_dir/../BigSpiky_V1.ino" -o "$build_dir/firmware_api_smoke.o"
"$build_dir/test_bigspiky_logic"
"$build_dir/timing_sim"
echo "ARDUINO API SMOKE COMPILE PASSED"
