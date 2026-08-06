# Behavioural Evidence Manifest

## Session identity

- Date:
- Tester:
- Git commit: `b98187c`
- Git tag: `gui-pre-refactor-2026-08-05`
- Git branch:
- Python version:
- Qt binding:
- PyCharm version:
- Operating system:

## Hardware

- Spikeling board version:
- Board identifier:
- Firmware version:
- Firmware commit:
- USB serial port:
- Power source:
- Connected peripherals:
- External stimulus source:
- Oscilloscope or acquisition equipment:

## Physical configuration

- Knob positions:
- Switch positions:
- Jumper positions:
- Connected inputs:
- Connected outputs:
- Light level or sensor conditions:
- Other relevant environmental conditions:

## Scenarios captured

| ID | Scenario | Inputs | Expected observation | Evidence files |
|---|---|---|---|---|
| BASE-001 | Launch without hardware | No board connected | GUI opens and remains responsive | |
| BASE-002 | Connect to board | Board connected on COM port | Connected state appears | |
| BASE-003 | Spontaneous activity | Baseline knob settings | Vm and spikes are displayed | |
| BASE-004 | Parameter change | Change one parameter | Display and board behaviour update | |
| BASE-005 | Stimulation | Apply configured stimulus | Evoked response is visible | |
| BASE-006 | Recording and export | Record representative activity | Valid file is created | |
| BASE-007 | Disconnect and reconnect | Disconnect and reconnect | Stream resumes once | |
| BASE-008 | Shutdown | Close connected GUI | Process exits and port is released | |

## Important observations

-
-
-

## Existing defects observed

-
-
-

## Deviations from the manual smoke test

-
-
- 
