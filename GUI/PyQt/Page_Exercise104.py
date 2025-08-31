import Settings
import numpy as np
import pyqtgraph as pg

nPages = 6

def ShowPage(self):
    if self.ui.Exercise4_OpeningFlag == False:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_504)
        self.ui.Exercise104_stackedWidget.setCurrentIndex(self.Exercice104_CurrentIndex)

    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_504)
        self.Exercice104_CurrentIndex = 0
        self.ui.Exercise104_stackedWidget.setCurrentIndex(self.Exercice104_CurrentIndex)
        self.ui.Exercise4_OpeningFlag = False


    self.ui.Exercise104_PreviousButton_pushButton.setEnabled(False)
    self.ui.Exercise104_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100);" 
                                                                "border: 2px solid rgb(80, 96, 100);" 
                                                                "border-radius: 10px;" 
                                                                "padding: 2px;"
                                                                )
    self.ui.Exercise104_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                             "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                             "border-radius: 10px" + ";\n"
                                                             "padding: 2px;"
                                                             )

    self.ui.FI_Curve_widget_3.clear()
    FI.SetGraph(self)


def Previous(self):
    self.Exercice104_CurrentIndex = self.ui.Exercise104_stackedWidget.currentIndex()
    self.ui.Exercise104_stackedWidget.setCurrentIndex(self.Exercice104_CurrentIndex - 1)
    self.Exercice104_CurrentIndex = self.ui.Exercise104_stackedWidget.currentIndex()
    if self.Exercice104_CurrentIndex < nPages-1:
        self.ui.Exercise104_AfterButton_pushButton.setEnabled(True)
        self.ui.Exercise104_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                 "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                 "border-radius: 10px" + ";\n"
                                                                 "padding: 2px;"
                                                                 )
    if self.Exercice104_CurrentIndex == 0:
        self.ui.Exercise104_PreviousButton_pushButton.setEnabled(False)
        self.ui.Exercise104_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                    "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )


def After(self):
    self.Exercice104_CurrentIndex = self.ui.Exercise104_stackedWidget.currentIndex()
    self.ui.Exercise104_stackedWidget.setCurrentIndex(self.Exercice104_CurrentIndex + 1)
    self.Exercice104_CurrentIndex = self.ui.Exercise104_stackedWidget.currentIndex()
    if self.Exercice104_CurrentIndex > 0:
        self.ui.Exercise104_PreviousButton_pushButton.setEnabled(True)
        self.ui.Exercise104_PreviousButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                    "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )
    if self.Exercice104_CurrentIndex == nPages-1:
        self.ui.Exercise104_AfterButton_pushButton.setEnabled(False)
        self.ui.Exercise104_AfterButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                "border-radius: 10px" + ";\n"
                                                                "padding: 2px;"
                                                                )


class FI():

    def SetGraph(self):
        self.ui.FI_Curve_widget_3.showGrid(x=True, y=True)
        self.ui.FI_Curve_widget_3.setBackground(Settings.DarkSolarized[0])
        self.ui.FI_Curve_widget_3.setLabel('bottom', 'Intensity', 'a.u.')
        self.ui.FI_Curve_widget_3.setLabel('left', 'spike rate', 'Hz')

    def Plot(self):
        self.ui.FI_Curve_widget_3.clear()
        ft = [0, 10, 20, 30, 40, 50, 60]

        if self.ui.FR_50_00_lineEdit.text() == '':
            FR_50_00 = 0
        else:
            FR_50_00 = int(self.ui.FR_50_00_lineEdit.text())

        if self.ui.FR_50_10_lineEdit.text() == '':
            FR_50_10 = 0
        else:
            FR_50_10 = int(self.ui.FR_50_10_lineEdit.text())

        if self.ui.FR_50_20_lineEdit.text() == '':
            FR_50_20 = 0
        else:
            FR_50_20 = int(self.ui.FR_50_20_lineEdit.text())

        if self.ui.FR_50_30_lineEdit.text() == '':
            FR_50_30 = 0
        else:
            FR_50_30 = int(self.ui.FR_50_30_lineEdit.text())

        if self.ui.FR_50_40_lineEdit.text() == '':
            FR_50_40 = 0
        else:
            FR_50_40 = int(self.ui.FR_50_40_lineEdit.text())

        if self.ui.FR_50_50_lineEdit.text() == '':
            FR_50_50 = 0
        else:
            FR_50_50 = int(self.ui.FR_50_50_lineEdit.text())

        if self.ui.FR_50_60_lineEdit.text() == '':
            FR_50_60 = 0
        else:
            FR_50_60 = int(self.ui.FR_50_60_lineEdit.text())



        if self.ui.FR_51_00_lineEdit.text() == '':
            FR_51_00 = 0
        else:
            FR_51_00 = int(self.ui.FR_51_00_lineEdit.text())

        if self.ui.FR_51_10_lineEdit.text() == '':
            FR_51_10 = 0
        else:
            FR_51_10 = int(self.ui.FR_51_10_lineEdit.text())

        if self.ui.FR_51_20_lineEdit.text() == '':
            FR_51_20 = 0
        else:
            FR_51_20 = int(self.ui.FR_51_20_lineEdit.text())

        if self.ui.FR_51_30_lineEdit.text() == '':
            FR_51_30 = 0
        else:
            FR_51_30 = int(self.ui.FR_51_30_lineEdit.text())

        if self.ui.FR_51_40_lineEdit.text() == '':
            FR_51_40 = 0
        else:
            FR_51_40 = int(self.ui.FR_51_40_lineEdit.text())

        if self.ui.FR_51_50_lineEdit.text() == '':
            FR_51_50 = 0
        else:
            FR_51_50 = int(self.ui.FR_51_50_lineEdit.text())

        if self.ui.FR_51_60_lineEdit.text() == '':
            FR_51_60 = 0
        else:
            FR_51_60 = int(self.ui.FR_51_60_lineEdit.text())

        FR_50 = [FR_50_00, FR_50_10, FR_50_20, FR_50_30, FR_50_40, FR_50_50, FR_50_60]
        FR_51 = [FR_51_00, FR_51_10, FR_51_20, FR_51_30, FR_51_40, FR_51_50, FR_51_60]

        self.ui.FI_Curve_widget_3.addLegend()

        self.ui.FI_Curve_widget_3.plot(x=ft, y=FR_50, pen={'color': tuple(Settings.DarkSolarized[3]), 'width': 3}, name="Baseline")
        self.ui.FI_Curve_widget_3.plot(x=ft, y=FR_51, pen={'color': tuple(Settings.DarkSolarized[5]), 'width': 3}, name="Sensitised")

        self.ui.FI_Curve_widget_3.setXRange(0, 70)
        self.ui.FI_Curve_widget_3.setYRange(0, max(max(FR_50), max(FR_51)) + 2)



