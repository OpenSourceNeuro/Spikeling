import Settings
import numpy as np
import pyqtgraph as pg

nPages = 4

def ShowPage(self):
    if self.ui.Exercise5_OpeningFlag == False:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_505)
        self.ui.Exercise105_stackedWidget.setCurrentIndex(self.Exercice105_CurrentIndex)

    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_505)
        self.Exercice105_CurrentIndex = 0
        self.ui.Exercise105_stackedWidget.setCurrentIndex(self.Exercice105_CurrentIndex)
        self.ui.Exercise5_OpeningFlag = False


    self.ui.Exercise105_PreviousButton_pushButton.setEnabled(False)
    self.ui.Exercise105_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100);" 
                                                                "border: 2px solid rgb(80, 96, 100);" 
                                                                "border-radius: 10px;" 
                                                                "padding: 2px;"
                                                                )
    self.ui.Exercise105_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                             "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                             "border-radius: 10px" + ";\n"
                                                             "padding: 2px;"
                                                             )



def Previous(self):
    self.Exercice105_CurrentIndex = self.ui.Exercise105_stackedWidget.currentIndex()
    self.ui.Exercise105_stackedWidget.setCurrentIndex(self.Exercice105_CurrentIndex - 1)
    self.Exercice105_CurrentIndex = self.ui.Exercise105_stackedWidget.currentIndex()
    if self.Exercice105_CurrentIndex < nPages-1:
        self.ui.Exercise105_AfterButton_pushButton.setEnabled(True)
        self.ui.Exercise105_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                 "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                 "border-radius: 10px" + ";\n"
                                                                 "padding: 2px;"
                                                                 )
    if self.Exercice105_CurrentIndex == 0:
        self.ui.Exercise105_PreviousButton_pushButton.setEnabled(False)
        self.ui.Exercise105_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                    "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )


def After(self):
    self.Exercice105_CurrentIndex = self.ui.Exercise105_stackedWidget.currentIndex()
    self.ui.Exercise105_stackedWidget.setCurrentIndex(self.Exercice105_CurrentIndex + 1)
    self.Exercice105_CurrentIndex = self.ui.Exercise105_stackedWidget.currentIndex()
    if self.Exercice105_CurrentIndex > 0:
        self.ui.Exercise105_PreviousButton_pushButton.setEnabled(True)
        self.ui.Exercise105_PreviousButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                    "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )
    if self.Exercice105_CurrentIndex == nPages-1:
        self.ui.Exercise105_AfterButton_pushButton.setEnabled(False)
        self.ui.Exercise105_AfterButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                "border-radius: 10px" + ";\n"
                                                                "padding: 2px;"
                                                                )

