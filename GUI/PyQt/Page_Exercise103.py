import Settings
import numpy as np
import pyqtgraph as pg

nPages = 6

def ShowPage(self):
    if self.ui.Exercise3_OpeningFlag == False:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_503)
        self.ui.Exercise103_stackedWidget.setCurrentIndex(self.Exercice103_CurrentIndex)

    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_503)
        self.Exercice103_CurrentIndex = 0
        self.ui.Exercise103_stackedWidget.setCurrentIndex(self.Exercice103_CurrentIndex)
        self.ui.Exercise3_OpeningFlag = False


    self.ui.Exercise103_PreviousButton_pushButton.setEnabled(False)
    self.ui.Exercise103_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100);" 
                                                                "border: 2px solid rgb(80, 96, 100);" 
                                                                "border-radius: 10px;" 
                                                                "padding: 2px;"
                                                                )
    self.ui.Exercise103_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                             "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                             "border-radius: 10px" + ";\n"
                                                             "padding: 2px;"
                                                             )

    self.ui.FiringRate_Histo_widget.clear()
    FiringRate.SetGraph(self)


def Previous(self):
    self.Exercice103_CurrentIndex = self.ui.Exercise103_stackedWidget.currentIndex()
    self.ui.Exercise103_stackedWidget.setCurrentIndex(self.Exercice103_CurrentIndex - 1)
    self.Exercice103_CurrentIndex = self.ui.Exercise103_stackedWidget.currentIndex()
    if self.Exercice103_CurrentIndex < nPages-1:
        self.ui.Exercise103_AfterButton_pushButton.setEnabled(True)
        self.ui.Exercise103_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                 "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                 "border-radius: 10px" + ";\n"
                                                                 "padding: 2px;"
                                                                 )
    if self.Exercice103_CurrentIndex == 0:
        self.ui.Exercise103_PreviousButton_pushButton.setEnabled(False)
        self.ui.Exercise103_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                    "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )


def After(self):
    self.Exercice103_CurrentIndex = self.ui.Exercise103_stackedWidget.currentIndex()
    self.ui.Exercise103_stackedWidget.setCurrentIndex(self.Exercice103_CurrentIndex + 1)
    self.Exercice103_CurrentIndex = self.ui.Exercise103_stackedWidget.currentIndex()
    if self.Exercice103_CurrentIndex > 0:
        self.ui.Exercise103_PreviousButton_pushButton.setEnabled(True)
        self.ui.Exercise103_PreviousButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                    "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )
    if self.Exercice103_CurrentIndex == nPages-1:
        self.ui.Exercise103_AfterButton_pushButton.setEnabled(False)
        self.ui.Exercise103_AfterButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                "border-radius: 10px" + ";\n"
                                                                "padding: 2px;"
                                                                )


class FiringRate():

    def SetGraph(self):
        self.ui.FiringRate_Histo_widget.setBackground(Settings.DarkSolarized[0])


    def Plot(self):

        if self.ui.FR_lineEdit_00.text() == '':
            FR_00 = 0
        else:
            FR_00 = int(self.ui.FR_lineEdit_00.text())

        if self.ui.FR_lineEdit_01.text() == '':
            FR_01 = 0
        else:
            FR_01 = int(self.ui.FR_lineEdit_01.text())

        if self.ui.FR_lineEdit_02.text() == '':
            FR_02 = 0
        else:
            FR_02 = int(self.ui.FR_lineEdit_02.text())

        if self.ui.FR_lineEdit_03.text() == '':
            FR_03 = 0
        else:
            FR_03 = int(self.ui.FR_lineEdit_03.text())

        if self.ui.FR_lineEdit_10.text() == '':
            FR_10 = 0
        else:
            FR_10 = int(self.ui.FR_lineEdit_10.text())

        if self.ui.FR_lineEdit_11.text() == '':
            FR_11 = 0
        else:
            FR_11 = int(self.ui.FR_lineEdit_11.text())

        if self.ui.FR_lineEdit_12.text() == '':
            FR_12 = 0
        else:
            FR_12 = int(self.ui.FR_lineEdit_12.text())

        if self.ui.FR_lineEdit_13.text() == '':
            FR_13 = 0
        else:
            FR_13 = int(self.ui.FR_lineEdit_13.text())

        if self.ui.FR_lineEdit_20.text() == '':
            FR_20 = 0
        else:
            FR_20 = int(self.ui.FR_lineEdit_20.text())

        if self.ui.FR_lineEdit_21.text() == '':
            FR_21 = 0
        else:
            FR_21 = int(self.ui.FR_lineEdit_21.text())

        if self.ui.FR_lineEdit_22.text() == '':
            FR_22 = 0
        else:
            FR_22 = int(self.ui.FR_lineEdit_22.text())

        if self.ui.FR_lineEdit_23.text() == '':
            FR_23 = 0
        else:
            FR_23 = int(self.ui.FR_lineEdit_23.text())

            # Data
            bar_width = 0.3
            x = np.arange(3)

            data_a = [FR_01,FR_11,FR_21]
            data_b = [FR_03,FR_13,FR_23]

            # ViewBox to attach graphics items in plot coords
            vb = self.ui.FiringRate_Histo_widget.plotItem.vb

            # Draw dataset A as filled rectangles
            for i, y in enumerate(data_a):
                rect = pg.QtWidgets.QGraphicsRectItem(x[i] - bar_width, 0, bar_width, y)
                rect.setBrush(pg.mkBrush(tuple(Settings.DarkSolarized[3])))
                rect.setPen(pg.mkPen(tuple(Settings.DarkSolarized[14])))
                rect.setZValue(10)
                vb.addItem(rect)

            # Draw dataset B as filled rectangles
            for i, y in enumerate(data_b):
                rect = pg.QtWidgets.QGraphicsRectItem(x[i], 0, bar_width, y)
                rect.setBrush(pg.mkBrush(tuple(Settings.DarkSolarized[5])))
                rect.setPen(pg.mkPen(tuple(Settings.DarkSolarized[14])))
                rect.setZValue(10)
                vb.addItem(rect)

            # Add labels for x-axis
            labels = [(0,"Gain = 0"), (1,"Gain = positive"), (2,"Gain = negative")]
            self.ui.FiringRate_Histo_widget.getAxis("bottom").setTicks([labels])


            # Legend (fake legend using ScatterPlotItem handles)
            legend = self.ui.FiringRate_Histo_widget.addLegend()
            legend.addItem(pg.ScatterPlotItem(pen=None, brush=tuple(Settings.DarkSolarized[3]), size=10), "Presynaptic")
            legend.addItem(pg.ScatterPlotItem(pen=None, brush=tuple(Settings.DarkSolarized[5]), size=10), "Postsynaptic")

            self.ui.FiringRate_Histo_widget.setXRange(-1, 3 + 1)
            self.ui.FiringRate_Histo_widget.setYRange(0, max(max(data_a), max(data_b)) + 2)
            self.ui.FiringRate_Histo_widget.showGrid(x=True, y=True)