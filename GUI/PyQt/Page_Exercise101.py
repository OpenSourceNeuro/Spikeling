import numpy as np
import pyqtgraph
import Settings

nPages = 11


def ShowPage(self):
    if self.ui.Exercise1_OpeningFlag == False:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_501)
        self.ui.Exercise101_stackedWidget.setCurrentIndex(self.Exercice101_CurrentIndex)

    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_501)
        self.Exercice101_CurrentIndex = 0
        self.ui.Exercise101_stackedWidget.setCurrentIndex(self.Exercice101_CurrentIndex)
        self.ui.Exercise1_OpeningFlag = False


    self.ui.Exercise101_PreviousButton_pushButton.setEnabled(False)
    self.ui.Exercise101_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100);" 
                                                                "border: 2px solid rgb(80, 96, 100);" 
                                                                "border-radius: 10px;" 
                                                                "padding: 2px;"
                                                                )
    self.ui.Exercise101_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                             "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                             "border-radius: 10px" + ";\n"
                                                             "padding: 2px;"
                                                             )


    self.ui.FI_Curve_widget.clear()
    FI.SetGraph(self)
    self.ui.FI_Curve_widget_2.clear()
    FI.SetGraph2(self)


def Previous(self):
    self.Exercice101_CurrentIndex = self.ui.Exercise101_stackedWidget.currentIndex()
    self.ui.Exercise101_stackedWidget.setCurrentIndex(self.Exercice101_CurrentIndex - 1)
    self.Exercice101_CurrentIndex = self.ui.Exercise101_stackedWidget.currentIndex()
    if self.Exercice101_CurrentIndex < nPages-1:
        self.ui.Exercise101_AfterButton_pushButton.setEnabled(True)
        self.ui.Exercise101_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                 "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                 "border-radius: 10px" + ";\n"
                                                                 "padding: 2px;"
                                                                 )
    if self.Exercice101_CurrentIndex == 0:
        self.ui.Exercise101_PreviousButton_pushButton.setEnabled(False)
        self.ui.Exercise101_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                    "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )


def After(self):
    self.Exercice101_CurrentIndex = self.ui.Exercise101_stackedWidget.currentIndex()
    self.ui.Exercise101_stackedWidget.setCurrentIndex(self.Exercice101_CurrentIndex + 1)
    self.Exercice101_CurrentIndex = self.ui.Exercise101_stackedWidget.currentIndex()
    if self.Exercice101_CurrentIndex > 0:
        self.ui.Exercise101_PreviousButton_pushButton.setEnabled(True)
        self.ui.Exercise101_PreviousButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                    "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )
    if self.Exercice101_CurrentIndex == nPages-1:
        self.ui.Exercise101_AfterButton_pushButton.setEnabled(False)
        self.ui.Exercise101_AfterButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                "border-radius: 10px" + ";\n"
                                                                "padding: 2px;"
                                                                )



class FI():

    def SetGraph(self):
        self.ui.FI_Curve_widget.showGrid(x=True, y=True)
        self.ui.FI_Curve_widget.setBackground(Settings.DarkSolarized[0])
        self.ui.FI_Curve_widget.setLabel('bottom', 'Stimulus Intensity', 'a.u.')
        self.ui.FI_Curve_widget.setLabel('left', 'spike rate', 'Hz')


    def Plot_FI(self):
        self.ui.FI_Curve_widget.clear()
        nt = [10,20,30,40,50,60,70,80,90,100]

        if self.ui.LineEdit_PS_10.text() == '':
            PS_10 = 0
        else:
            PS_10 = int(self.ui.LineEdit_PS_10.text())

        if self.ui.LineEdit_PS_20.text() == '':
            PS_20 = 0
        else:
            PS_20 = int(self.ui.LineEdit_PS_20.text())

        if self.ui.LineEdit_PS_30.text() == '':
            PS_30 = 0
        else:
            PS_30 = int(self.ui.LineEdit_PS_30.text())

        if self.ui.LineEdit_PS_40.text() == '':
            PS_40 = 0
        else:
            PS_40 = int(self.ui.LineEdit_PS_40.text())

        if self.ui.LineEdit_PS_50.text() == '':
            PS_50 = 0
        else:
            PS_50 = int(self.ui.LineEdit_PS_50.text())

        if self.ui.LineEdit_PS_60.text() == '':
            PS_60 = 0
        else:
            PS_60 = int(self.ui.LineEdit_PS_60.text())

        if self.ui.LineEdit_PS_70.text() == '':
            PS_70 = 0
        else:
            PS_70 = int(self.ui.LineEdit_PS_70.text())

        if self.ui.LineEdit_PS_80.text() == '':
            PS_80 = 0
        else:
            PS_80 = int(self.ui.LineEdit_PS_80.text())

        if self.ui.LineEdit_PS_90.text() == '':
            PS_90 = 0
        else:
            PS_90 = int(self.ui.LineEdit_PS_90.text())

        if self.ui.LineEdit_PS_100.text() == '':
            PS_100 = 0
        else:
            PS_100 = int(self.ui.LineEdit_PS_100.text())

        PS = [PS_10, PS_20, PS_30, PS_40, PS_50, PS_60, PS_70, PS_80, PS_90, PS_100]
        self.ui.FI_Curve_widget.plot(nt, PS, pen=(Settings.DarkSolarized[16]))

        self.ui.LineEdit_PS_1_1.setText(str(PS_10))
        self.ui.LineEdit_PS_1_2.setText(str(PS_20))
        self.ui.LineEdit_PS_1_3.setText(str(PS_30))
        self.ui.LineEdit_PS_1_4.setText(str(PS_40))
        self.ui.LineEdit_PS_1_5.setText(str(PS_50))
        self.ui.LineEdit_PS_1_6.setText(str(PS_60))
        self.ui.LineEdit_PS_1_7.setText(str(PS_70))
        self.ui.LineEdit_PS_1_8.setText(str(PS_80))
        self.ui.LineEdit_PS_1_9.setText(str(PS_90))
        self.ui.LineEdit_PS_1_10.setText(str(PS_100))

    def SetGraph2(self):
        self.ui.FI_Curve_widget_2.showGrid(x=True, y=True)
        self.ui.FI_Curve_widget_2.setBackground(Settings.DarkSolarized[0])
        self.ui.FI_Curve_widget_2.setLabel('bottom', 'Stimulus Intensity', 'a.u.')
        self.ui.FI_Curve_widget_2.setLabel('left', 'spike rate', 'Hz')

    def Plot_FI2(self):
        self.ui.FI_Curve_widget_2.clear()
        nt = [10,20,30,40,50,60,70,80,90,100]


        if self.ui.LineEdit_PS_1_1.text() == '':
            PS_1_1 = 0
        else:
            PS_1_1 = int(self.ui.LineEdit_PS_1_1.text())

        if self.ui.LineEdit_PS_1_2.text() == '':
            PS_1_2 = 0
        else:
            PS_1_2 = int(self.ui.LineEdit_PS_1_2.text())

        if self.ui.LineEdit_PS_1_3.text() == '':
            PS_1_3 = 0
        else:
            PS_1_3 = int(self.ui.LineEdit_PS_1_3.text())

        if self.ui.LineEdit_PS_1_4.text() == '':
            PS_1_4 = 0
        else:
            PS_1_4 = int(self.ui.LineEdit_PS_1_4.text())

        if self.ui.LineEdit_PS_1_5.text() == '':
            PS_1_5 = 0
        else:
            PS_1_5 = int(self.ui.LineEdit_PS_1_5.text())

        if self.ui.LineEdit_PS_1_6.text() == '':
            PS_1_6 = 0
        else:
            PS_1_6 = int(self.ui.LineEdit_PS_1_6.text())

        if self.ui.LineEdit_PS_1_7.text() == '':
            PS_1_7 = 0
        else:
            PS_1_7 = int(self.ui.LineEdit_PS_1_7.text())

        if self.ui.LineEdit_PS_1_8.text() == '':
            PS_1_8 = 0
        else:
            PS_1_8 = int(self.ui.LineEdit_PS_1_8.text())

        if self.ui.LineEdit_PS_1_9.text() == '':
            PS_1_9 = 0
        else:
            PS_1_9 = int(self.ui.LineEdit_PS_1_9.text())

        if self.ui.LineEdit_PS_1_10.text() == '':
            PS_1_10 = 0
        else:
            PS_1_10 = int(self.ui.LineEdit_PS_1_10.text())

        PS1 = [PS_1_1,PS_1_2,PS_1_3,PS_1_4,PS_1_5,PS_1_6,PS_1_7,PS_1_8,PS_1_9,PS_1_10]

        if self.ui.LineEdit_PS_2_1.text() == '':
            PS_2_1 = 0
        else:
            PS_2_1 = int(self.ui.LineEdit_PS_2_1.text())

        if self.ui.LineEdit_PS_2_2.text() == '':
            PS_2_2 = 0
        else:
            PS_2_2 = int(self.ui.LineEdit_PS_2_2.text())

        if self.ui.LineEdit_PS_2_3.text() == '':
            PS_2_3 = 0
        else:
            PS_2_3 = int(self.ui.LineEdit_PS_2_3.text())

        if self.ui.LineEdit_PS_2_4.text() == '':
            PS_2_4 = 0
        else:
            PS_2_4 = int(self.ui.LineEdit_PS_2_4.text())

        if self.ui.LineEdit_PS_2_5.text() == '':
            PS_2_5 = 0
        else:
            PS_2_5 = int(self.ui.LineEdit_PS_2_5.text())

        if self.ui.LineEdit_PS_2_6.text() == '':
            PS_2_6 = 0
        else:
            PS_2_6 = int(self.ui.LineEdit_PS_2_6.text())

        if self.ui.LineEdit_PS_2_7.text() == '':
            PS_2_7 = 0
        else:
            PS_2_7 = int(self.ui.LineEdit_PS_2_7.text())

        if self.ui.LineEdit_PS_2_8.text() == '':
            PS_2_8 = 0
        else:
            PS_2_8 = int(self.ui.LineEdit_PS_2_8.text())

        if self.ui.LineEdit_PS_2_9.text() == '':
            PS_2_9 = 0
        else:
            PS_2_9 = int(self.ui.LineEdit_PS_2_9.text())

        if self.ui.LineEdit_PS_2_10.text() == '':
            PS_2_10 = 0
        else:
            PS_2_10 = int(self.ui.LineEdit_PS_2_10.text())

        PS2 = [PS_2_1, PS_2_2, PS_2_3, PS_2_4, PS_2_5, PS_2_6, PS_2_7, PS_2_8, PS_2_9, PS_2_10]

        if self.ui.LineEdit_PS_3_1.text() == '':
            PS_3_1 = 0
        else:
            PS_3_1 = int(self.ui.LineEdit_PS_3_1.text())

        if self.ui.LineEdit_PS_3_2.text() == '':
            PS_3_2 = 0
        else:
            PS_3_2 = int(self.ui.LineEdit_PS_3_2.text())

        if self.ui.LineEdit_PS_3_3.text() == '':
            PS_3_3 = 0
        else:
            PS_3_3 = int(self.ui.LineEdit_PS_3_3.text())

        if self.ui.LineEdit_PS_3_4.text() == '':
            PS_3_4 = 0
        else:
            PS_3_4 = int(self.ui.LineEdit_PS_3_4.text())

        if self.ui.LineEdit_PS_3_5.text() == '':
            PS_3_5 = 0
        else:
            PS_3_5 = int(self.ui.LineEdit_PS_3_5.text())

        if self.ui.LineEdit_PS_3_6.text() == '':
            PS_3_6 = 0
        else:
            PS_3_6 = int(self.ui.LineEdit_PS_3_6.text())

        if self.ui.LineEdit_PS_3_7.text() == '':
            PS_3_7 = 0
        else:
            PS_3_7 = int(self.ui.LineEdit_PS_3_7.text())

        if self.ui.LineEdit_PS_3_8.text() == '':
            PS_3_8 = 0
        else:
            PS_3_8 = int(self.ui.LineEdit_PS_3_8.text())

        if self.ui.LineEdit_PS_3_9.text() == '':
            PS_3_9 = 0
        else:
            PS_3_9 = int(self.ui.LineEdit_PS_3_9.text())

        if self.ui.LineEdit_PS_3_10.text() == '':
            PS_3_10 = 0
        else:
            PS_3_10 = int(self.ui.LineEdit_PS_3_10.text())

        PS3 = [PS_3_1, PS_3_2, PS_3_3, PS_3_4, PS_3_5, PS_3_6, PS_3_7, PS_3_8, PS_3_9, PS_3_10]

        self.ui.FI_Curve_widget_2.plot(x=nt, y=PS1, pen={'color': tuple(Settings.DarkSolarized[15]), 'width': 3})
        self.ui.FI_Curve_widget_2.plot(x=nt, y=PS2, pen={'color': tuple(Settings.DarkSolarized[16]), 'width': 3})
        self.ui.FI_Curve_widget_2.plot(x=nt, y=PS3, pen={'color': tuple(Settings.DarkSolarized[16]), 'width': 3})
