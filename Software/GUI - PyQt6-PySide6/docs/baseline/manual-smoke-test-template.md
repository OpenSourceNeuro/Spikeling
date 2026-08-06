Spikeling GUI Manual Smoke Test
Purpose

This smoke test verifies that the most important baseline GUI workflows remain operational.

It is not a complete validation of every GUI function. It should be run:

before architectural refactoring begins;
after a significant refactor;
before merging a major pull request;
before a GUI release;
after changing firmware-facing code.
Test record
Date: [YYYY-MM-DD]
Tester: [name]
Operating system: [version]
Python version: [version]
GUI commit: [commit]
GUI tag or branch: [tag/branch]
Hardware version: [version or No hardware]
Firmware version: [version/commit or No hardware]
Serial port: [COM port or Not applicable]
Qt binding: [PyQt6/PySide6]
Result definitions
PASS: observed behaviour matches expectation.
FAIL: observed behaviour differs from expectation.
BLOCKED: test cannot be completed because a prerequisite is unavailable.
NOT APPLICABLE: test does not apply to this configuration.
1. Environment
Test	Expected result	Result	Notes
Virtual environment activates	Project interpreter is active	[ ]

Dependencies import	No import error	[ ]

GUI entry point is available	Entry file or module exists	[ ]

No unexpected uncommitted changes	Working tree state is understood	[ ]


Suggested commands:

python --version
python -c "import sys; print(sys.executable)"
python -m pip check
git status
2. Application launch
Test	Expected result	Result	Notes
Start GUI	Main window opens	[ ]

Startup responsiveness	Window remains responsive	[ ]

Main pages load	No unhandled exception	[ ]

Icons and resources load	No missing-resource indicators	[ ]

Initial state is coherent	Controls reflect disconnected or connected state correctly	[ ]

3. Launch without hardware
Test	Expected result	Result	Notes
Start with no board connected	GUI handles absence of hardware cleanly	[ ]

Hardware controls	Disabled or otherwise safely handled	[ ]

Error message	Clear and non-repeating, if applicable	[ ]

GUI remains responsive	No freeze or infinite retry loop	[ ]

Application closes	Process terminates cleanly	[ ]

4. Hardware discovery and connection
Test	Expected result	Result	Notes
Connect board by USB	Board powers and COM port appears	[ ]

Refresh port list	Correct COM port appears	[ ]

Select port	Selection is accepted	[ ]

Connect	Connection succeeds	[ ]

Status indicator	GUI reports connected state	[ ]

Initial data	Valid data begins arriving	[ ]

No parser errors	No repeated malformed-packet errors	[ ]

5. Live neuron display
Test	Expected result	Result	Notes
Membrane-potential trace appears	Continuous plausible trace	[ ]

Spike events appear	Spikes are visible when generated	[ ]

GUI remains responsive	Controls and window remain usable	[ ]

Plot updates continuously	No unexplained stalls	[ ]

Values are plausible	No obvious scaling or decoding errors	[ ]


Record representative observations:

Approximate sample rate:
Approximate membrane-potential range:
Approximate spike rate:
Any visual lag:
Any dropped or malformed frames:
6. Parameter controls

Test every hardware or software parameter currently exposed by the GUI.

Parameter/control	Action	Expected result	Result	Notes
[parameter]	Change value	Board or GUI state updates correctly	[ ]

[parameter]	Change value	Observable neuron behaviour changes	[ ]

[parameter]	Restore default	Default behaviour returns	[ ]


Check:

minimum value;
maximum value;
intermediate value;
rapid successive changes;
invalid or out-of-range values, where the GUI allows entry.
7. Stimulation
Test	Expected result	Result	Notes
Configure stimulus	Values are accepted	[ ]

Start stimulus	Stimulation begins	[ ]

Neural response	Expected response is visible	[ ]

Stop stimulus	Stimulation stops	[ ]

Repeat stimulus	Second run works without restart	[ ]

Disconnect during inactive state	Safe disconnection	[ ]


Do not intentionally disconnect during active stimulation unless this has been established as safe.

8. Recording
Test	Expected result	Result	Notes
Start recording	Recording state is indicated	[ ]

Acquire representative data	Data accumulates	[ ]

Stop recording	Recording stops cleanly	[ ]

Save recording	File is created	[ ]

Inspect saved file	Format and contents are plausible	[ ]

Start second recording	Works without restarting GUI	[ ]


Saved test file:

[repository-relative fixture path or external path]
9. Data import and export
Test	Expected result	Result	Notes
Open existing recording	File loads	[ ]

Display imported data	Data appears correctly	[ ]

Export data	Output file is created	[ ]

Inspect exported data	Columns and values are plausible	[ ]

Cancel file dialog	GUI returns safely	[ ]

Invalid file	Clear error without crash	[ ]

10. GUI pages and workflows

Add one row for every current major page.

Page	Opens	Core workflow works	No exception	Notes
Neuron	[ ]	[ ]	[ ]

Imaging	[ ]	[ ]	[ ]

Extracellular	[ ]	[ ]	[ ]

Data Analysis	[ ]	[ ]	[ ]

Emulator	[ ]	[ ]	[ ]

[other page]	[ ]	[ ]	[ ]

11. Disconnection and reconnection
Test	Expected result	Result	Notes
Disconnect through GUI	Serial port closes	[ ]

Controls update	Disconnected state is shown	[ ]

Plotting stops safely	No error loop	[ ]

Reconnect same board	Connection succeeds again	[ ]

Data resumes	Valid stream resumes	[ ]

No duplicate updates	Plot/data rate is not multiplied	[ ]


The duplicate-update check is important because repeated connections can accidentally create repeated Qt signal connections.

12. Shutdown
Test	Expected result	Result	Notes
Close while disconnected	Application exits	[ ]

Close after connection	Workers and serial port stop	[ ]

Python process terminates	No orphan process remains	[ ]

Reopen application	Application launches normally	[ ]

Reconnect board	COM port is available	[ ]

13. Error observations

Record all warnings and exceptions, even when the test passes:

Timestamp:
Action:
Message or traceback:
Visible consequence:
Reproducible:
Related known-issue ID:
14. Final result
Overall result: [PASS / FAIL / BLOCKED]
Critical failures: [number]
High-severity failures: [number]
New known issues created: [IDs]
Hardware-dependent tests omitted: [list or None]
Acceptance criterion

The baseline is considered preserved when:

all previously passing critical workflows still pass;
no new unhandled exceptions occur;
serial data remains correctly decoded;
the GUI remains responsive;
connection, disconnection and reconnection remain functional;
recording and export retain expected behaviour;
the application shuts down cleanly.
