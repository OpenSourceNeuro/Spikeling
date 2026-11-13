from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QMessageBox, QWidget

from spikeling_gui.appearance.theme_manager import theme_manager


def themed_message_box(
    parent: QWidget | None,
    title: str,
    text: str,
    icon: QMessageBox.Icon = QMessageBox.Icon.Warning,
) -> QMessageBox:
    """Create a Qt message box styled with the active Spikeling theme."""
    box = QMessageBox(parent)
    box.setOption(QMessageBox.Option.DontUseNativeDialog)
    box.setWindowTitle(title)
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setText(text)
    box.setIcon(icon)
    box.setStandardButtons(QMessageBox.StandardButton.Ok)
    box.setStyleSheet(theme_manager.stylesheet())
    return box


def show_popup(self, Title, Text):
    parent = self if isinstance(self, QWidget) else getattr(self, "parent", None)
    themed_message_box(parent if isinstance(parent, QWidget) else None,
                       str(Title), str(Text)).exec()


def confirm_overwrite(self, file_path: Path):
    """
    Ask the user if they want to overwrite, rename, or cancel an existing file.

    Returns:
        action (str): "overwrite", "rename", or "cancel"
        path (Path): Path to use for saving (same as input or new if renamed)
    """
    parent = self if isinstance(self, QWidget) else getattr(self, "parent", None)
    if not isinstance(parent, QWidget):
        parent = None
    msg = themed_message_box(
        parent, "File Already Exists",
        f"The file '{file_path.name}' already exists.\nWhat do you want to do?",
    )
    msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
    overwrite_btn = msg.addButton("Overwrite", QMessageBox.ButtonRole.AcceptRole)
    rename_btn = msg.addButton("Rename", QMessageBox.ButtonRole.ActionRole)
    cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)

    msg.setDefaultButton(overwrite_btn)
    msg.exec()

    clicked = msg.clickedButton()
    if clicked == overwrite_btn:
        return "overwrite", file_path
    elif clicked == rename_btn:
        # Ask user for a new file name
        rename_dialog = QInputDialog(parent)
        rename_dialog.setWindowTitle("Rename File")
        rename_dialog.setLabelText("Enter new file name:")
        rename_dialog.setTextValue(file_path.stem)
        rename_dialog.setStyleSheet(theme_manager.stylesheet())
        ok = rename_dialog.exec()
        new_name = rename_dialog.textValue()
        if ok and new_name.strip():
            new_path = file_path.parent / f"{new_name.strip()}.csv"
            return "rename", new_path
        else:
            # If user cancels rename dialog, treat as cancel
            return "cancel", file_path
    else:
        return "cancel", file_path