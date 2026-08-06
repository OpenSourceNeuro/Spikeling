Current Spikeling GUI Launch Procedure
Purpose

This document records the verified procedure for launching the last known working version of the Spikeling GUI before the architectural refactor.

It should be updated whenever the supported launch procedure changes.

Baseline reference
Git branch: main
Git commit: b98187c
Git tag: gui-pre-refactor-2026-08-05
Repository: https://github.com/OpenSourceNeuro/Spikeling
Recorded on: 2026-08-05
Operating system: Windows
Development environment: PyCharm
Python environment: local .venv
GUI source directory

From the repository root:

Software/GUI - PyQt6-PySide6
Prerequisites

The following must be installed or available:

Python version: [run python --version and insert result]
PyCharm version: [insert version]
Git
A working Python virtual environment
Required Python packages
A compatible Spikeling board and firmware, when hardware testing is required
A USB data cable
An available serial port
Python environment activation

From PowerShell, navigate to the GUI directory:

cd "Software\GUI - PyQt6-PySide6"

Activate the virtual environment:

.\.venv\Scripts\Activate.ps1

Confirm the active interpreter:

python --version
python -c "import sys; print(sys.executable)"

Expected interpreter location:

[insert the verified path to .venv\Scripts\python.exe]
Dependency installation

The current verified dependency installation command is:

[insert the actual command, such as:
python -m pip install -r requirements.txt]

The authoritative dependency file is:

[requirements.txt, pyproject.toml, environment.yml, or other file]

To record the complete baseline environment:

python -m pip freeze > docs\baseline\python-environment.txt
PyCharm run configuration

The verified PyCharm configuration is:

Configuration name: [insert name]
Script path: [insert path]
Module name, if used: [insert module or Not applicable]
Python interpreter: [insert interpreter path or project virtual environment]
Working directory: [insert working directory]
Command-line arguments: [insert arguments or None]
Environment variables: [insert variables or None]
Emulate terminal in output console: [Yes/No]
Application entry point

The current GUI entry point is:

[insert path to the main Python file]

The startup function or block is:

[for example: main(), run_app(), or if __name__ == "__main__"]
Launch from PyCharm
Open the complete Spikeling repository in PyCharm.
Select the project virtual environment.
Select the run configuration [configuration name].
Connect the Spikeling board if hardware testing is required.
Confirm that no other application is using the serial port.
Click Run.
Confirm that the main Spikeling window opens without an unhandled exception.
Launch from PowerShell

From the GUI directory:

.\.venv\Scripts\Activate.ps1
python "[insert-entry-point-file].py"

Alternatively, if the GUI is launched as a Python module:

python -m [insert.module.name]

Only retain the command that has been verified to work.

Launch without connected hardware

Current behaviour when no Spikeling board is connected:

[Describe exactly what happens:
- GUI opens normally;
- GUI displays a connection warning;
- hardware controls remain disabled;
- application exits;
- emulator is automatically selected;
- other verified behaviour.]
Launch with connected hardware
Connect the board by USB.
Confirm that Windows assigns a COM port.
Start the GUI.
Select or detect the correct serial port.
Establish the connection.
Confirm receipt of valid board data.

Expected connection indication:

[Describe the GUI indicator, message, icon or status text.]

Expected terminal or log output:

[Insert representative non-sensitive output.]
Known startup constraints
[Example: The board must be connected before opening the GUI.]
[Example: The COM port must not be open in Arduino Serial Monitor.]
[Example: The GUI must be launched from its own directory because relative paths are used.]
[Example: A specific Qt binding must be installed.]
[Add only verified constraints.]
Normal shutdown procedure
Stop any active recording or stimulation.
Disconnect from the Spikeling board using the GUI, if applicable.
Close the main window.
Confirm that the Python process terminates.
Confirm that the serial port is released.

Expected shutdown behaviour:

[Describe verified behaviour.]
Troubleshooting
GUI does not start

Check:

python --version
python -c "import sys; print(sys.executable)"
python -m pip check
Board is not detected

Check:

USB cable supports data;
board is powered;
correct COM port is present in Windows Device Manager;
Arduino Serial Monitor or another program is not using the port;
firmware is compatible with the GUI;
serial-port settings match the firmware.
Import error

Record the exact exception and verify that the active interpreter is the project .venv.

Verification status
Launch from PyCharm verified: [Yes/No]
Launch from PowerShell verified: [Yes/No]
Launch without hardware verified: [Yes/No]
Launch with hardware verified: [Yes/No]
Clean shutdown verified: [Yes/No]

Verified by: [name]
Verification date: [YYYY-MM-DD]
