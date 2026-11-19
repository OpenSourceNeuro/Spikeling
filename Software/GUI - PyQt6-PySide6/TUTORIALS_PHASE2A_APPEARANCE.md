# Spikeling Tutorial Phase 2A — visual integration correction

This appearance-only patch fixes the Phase 2A tutorial popup's inherited main-window stylesheet. Its **Qt Designer form is the source of truth** for the visual design, using colours from Spikeling's factory Solarized palette. These values are automatically substituted by `theme_manager` when users switch between dark/light/custom themes.

## Changes

- The instruction block is a wrapping, selectable `QLabel`, rather than a vertically expanding `QTextBrowser` that leaves a black empty region.
- The dialogue uses Segoe UI with 10 pt body text, a 13 pt main title, 12 pt step title and 9 pt secondary text, following Spikeling's typography.
- A distinct **frameless, draggable header** includes the tutorial title, close button, step counter and narrow progress indicator. A resize grip sits in the bottom-right corner.
- Scientific instructions, predictions, confirmations, targets and hints occupy a vertically scrollable central section. The response box is placed immediately under the question.
- An always-visible footer contains the status and clearly outlined action/navigation buttons; Continue is the accented primary action.
- The full confirmation instruction wraps separately from the short `I confirm I completed this action` checkbox label, avoiding horizontal overflow.
- Qt Designer controls the layout and styles; the Python controller only changes `QTextBrowser.setPlainText()` to `QLabel.setText()`, shows/hides complete sections and scrolls new steps back to the top.

The patch does not change the tutorial curriculum, progress storage, firmware, main window, `UI_Spikeling.ui` or experiment controllers.

## Installation

Extract the ZIP to Downloads. In `Software\\GUI - PyQt6-PySide6` on Windows PowerShell:

```powershell
$patchTheme = Join-Path $env:USERPROFILE 'Downloads\spikeling_tutorials_phase2a_appearance\apply_tutorial_appearance.py'
python $patchTheme --root . --check
python $patchTheme --root . --apply
python -m pytest -q tests/test_tutorials_phase1.py tests/test_tutorials_phase2a.py tests/test_tutorials_phase2a_appearance.py
python Main.py
```

### Rollback

Close the GUI, then run:

```powershell
python $patchTheme --root . --rollback
```

Rollback will refuse to overwrite files modified since the patch was applied. The original Phase 2A tutorial files are kept in `Data/Tutorials/.phase2a_appearance_backup`.

## Manual GUI review

1. Open NI-04 at a prediction step and confirm the question and answer box are adjacent, with no huge empty text area.
2. Confirm that header, scrollable body, live status, action buttons and primary Continue button are visually distinct and match the Solarized GUI.
3. Test a physical confirmation step to verify long text wraps and the checkbox remains clickable.
4. Change between the existing dark and light themes, and verify background/text/button contrast.
5. Drag the popup by its custom header, resize it using the bottom-right grip, reveal a hint, then confirm the footer remains visible while the central section scrolls.
6. Confirm Back, Continue, Skip, Hint and Exit still behave as in Phase 2A.

No Qt GUI rendering or physical-board acceptance was performed by the automatic patch tests; visual acceptance must be checked in the running application.
