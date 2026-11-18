"""Shared recording folder controls and filename validation."""

import tempfile

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLineEdit, QMessageBox

from spikeling_gui.appearance.dialogs import themed_message_box
from spikeling_gui.appearance.theme_manager import theme_manager
from spikeling_gui.paths import recordings_directory


def configure_recording_folder(parent, display, button):
    """Show the portable folder and connect the button to the file manager."""
    folder = recordings_directory()
    if isinstance(display, QLineEdit):
        display.setEnabled(True)
        display.setReadOnly(True)
        display.setText(str(folder))
    else:
        display.setText(folder.relative_to(folder.parents[1]).as_posix())
    display.setToolTip(str(folder))
    button.setText(QCoreApplication.translate("Recording", "Open folder"))
    button.clicked.connect(lambda: open_recordings_folder(parent))


def open_recordings_folder(parent):
    folder = recordings_directory()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder))):
            raise OSError(f"Could not open {folder}")
    except OSError as error:
        themed_message_box(parent, "Cannot open recording folder", str(error)).exec()


def recording_path(filename):
    """Validate a portable CSV filename and check that the folder is writable."""
    name = filename.strip()
    if name.lower().endswith(".csv"):
        name = name[:-4].strip()

    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"COM{i}" for i in "123456789¹²³")
    reserved.update(f"LPT{i}" for i in "123456789¹²³")
    if (
        not name
        or name.endswith((".", " "))
        or any(c in '<>:"/\\|?*' or ord(c) < 32 for c in name)
        or name.split(".")[0].rstrip().upper() in reserved
    ):
        raise ValueError(
            "Enter a valid file name without a folder path. "
            "The .csv extension is added automatically."
        )

    folder = recordings_directory()
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=folder):
        pass
    return folder / f"{name}.csv"


def prepare_recording(parent, filename, sidecar_suffixes=()):
    """Resolve the destination at record start and confirm existing outputs."""
    try:
        path = recording_path(filename)
    except (OSError, ValueError) as error:
        themed_message_box(parent, "Cannot start recording", str(error)).exec()
        return None

    outputs = (path, *(path.with_name(path.stem + suffix) for suffix in sidecar_suffixes))
    existing = [output.name for output in outputs if output.exists()]
    if existing:
        box = themed_message_box(
            parent, "Recording files already exist",
            "Replace existing recording files when saving?\n\n" + "\n".join(existing),
            QMessageBox.Icon.Question,
        )
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        if box.exec() != QMessageBox.StandardButton.Yes:
            return None
    return path


def style_recording_button(button, active):
    """Mirror the physical Spikeling recorder's red/green theme-aware button."""
    palette = theme_manager.palette()
    background = palette[4] if active else palette[3]
    button.setStyleSheet(
        f"QPushButton {{color: white; background-color: rgb{tuple(background)};}}"
        "QPushButton:hover { border: 2px solid white; }"
        "QPushButton:pressed { border: 2px solid #586e75; }"
    )
