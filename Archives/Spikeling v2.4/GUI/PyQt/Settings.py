from PySide6.QtWidgets import QMessageBox

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


