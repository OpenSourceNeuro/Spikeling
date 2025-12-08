from PySide6.QtWidgets import QMessageBox, QInputDialog
from pathlib import Path

BaudRate = 250000


DarkSolarized = [[0, 30, 38], [0, 43, 54], [7, 54, 66],                                            # 0:DarkBase01, 1:DarkBase02, 2:DarkBase03
                 [220, 50, 47], [133, 153, 0], [38, 139, 210],                                     # 3:Red, 4:Green, 5:Blue
                 [203, 75, 22], [42, 161, 152], [181, 137, 0], [108, 113, 196], [211, 54, 130],    # 6:Orange, 7:Cyan, 8:Yellow, 9:Violet, 10:Magenta
                 [88, 110, 117], [101, 123, 131], [131, 148, 150], [147, 161, 161],                # 11:Content01, 12:Content02, 13:Content03, 14:Content04
                 [238, 232, 213],[253, 246, 227],                                                  # 15:LightBase01, 16:LightBase02
                 [0,153,176],                                                                      # 17:OSH-Logo
                 [80, 110, 117]]


def show_popup(self, Title, Text):
    msg = QMessageBox()
    msg.setWindowTitle(str(Title))
    msg.setText(str(Text))
    msg.setIcon(QMessageBox.Warning)
    x = msg.exec_()


def confirm_overwrite(self, file_path: Path):
    """
    Ask the user if they want to overwrite, rename, or cancel an existing file.

    Returns:
        action (str): "overwrite", "rename", or "cancel"
        path (Path): Path to use for saving (same as input or new if renamed)
    """
    msg = QMessageBox()
    msg.setWindowTitle("File Already Exists")
    msg.setText(f"The file '{file_path.name}' already exists.\nWhat do you want to do?")
    msg.setIcon(QMessageBox.Warning)

    overwrite_btn = msg.addButton("Overwrite", QMessageBox.AcceptRole)
    rename_btn = msg.addButton("Rename", QMessageBox.ActionRole)
    cancel_btn = msg.addButton("Cancel", QMessageBox.RejectRole)

    msg.setDefaultButton(overwrite_btn)
    msg.exec()

    clicked = msg.clickedButton()
    if clicked == overwrite_btn:
        return "overwrite", file_path
    elif clicked == rename_btn:
        # Ask user for a new file name
        new_name, ok = QInputDialog.getText(None, "Rename File", "Enter new file name:", text=file_path.stem)
        if ok and new_name.strip():
            new_path = file_path.parent / f"{new_name.strip()}.csv"
            return "rename", new_path
        else:
            # If user cancels rename dialog, treat as cancel
            return "cancel", file_path
    else:
        return "cancel", file_path