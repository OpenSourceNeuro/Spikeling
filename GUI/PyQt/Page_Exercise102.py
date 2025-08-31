import Settings

nPages = 4

def ShowPage(self):
    if self.ui.Exercise2_OpeningFlag == False:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_502)
        self.ui.Exercise102_stackedWidget.setCurrentIndex(self.Exercice102_CurrentIndex)

    else:
        self.ui.mainbody_stackedWidget.setCurrentWidget(self.ui.page_502)
        self.Exercice102_CurrentIndex = 0
        self.ui.Exercise102_stackedWidget.setCurrentIndex(self.Exercice102_CurrentIndex)
        self.ui.Exercise2_OpeningFlag = False


    self.ui.Exercise102_PreviousButton_pushButton.setEnabled(False)
    self.ui.Exercise102_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100);" 
                                                                "border: 2px solid rgb(80, 96, 100);" 
                                                                "border-radius: 10px;" 
                                                                "padding: 2px;"
                                                                )
    self.ui.Exercise102_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                             "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                             "border-radius: 10px" + ";\n"
                                                             "padding: 2px;"
                                                             )

def Previous(self):
    self.Exercice102_CurrentIndex = self.ui.Exercise102_stackedWidget.currentIndex()
    self.ui.Exercise102_stackedWidget.setCurrentIndex(self.Exercice102_CurrentIndex - 1)
    self.Exercice102_CurrentIndex = self.ui.Exercise102_stackedWidget.currentIndex()
    if self.Exercice102_CurrentIndex < nPages-1:
        self.ui.Exercise102_AfterButton_pushButton.setEnabled(True)
        self.ui.Exercise102_AfterButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                 "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                 "border-radius: 10px" + ";\n"
                                                                 "padding: 2px;"
                                                                 )
    if self.Exercice102_CurrentIndex == 0:
        self.ui.Exercise102_PreviousButton_pushButton.setEnabled(False)
        self.ui.Exercise102_PreviousButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                    "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )


def After(self):
    self.Exercice102_CurrentIndex = self.ui.Exercise102_stackedWidget.currentIndex()
    self.ui.Exercise102_stackedWidget.setCurrentIndex(self.Exercice102_CurrentIndex + 1)
    self.Exercice102_CurrentIndex = self.ui.Exercise102_stackedWidget.currentIndex()
    if self.Exercice102_CurrentIndex > 0:
        self.ui.Exercise102_PreviousButton_pushButton.setEnabled(True)
        self.ui.Exercise102_PreviousButton_pushButton.setStyleSheet("background-color: rgb" + str(tuple(Settings.DarkSolarized[2])) + ";\n"
                                                                    "border: 2px solid rgb" + str(tuple(Settings.DarkSolarized[14])) + ";\n"
                                                                    "border-radius: 10px" + ";\n"
                                                                    "padding: 2px;"
                                                                    )
    if self.Exercice102_CurrentIndex == nPages-1:
        self.ui.Exercise102_AfterButton_pushButton.setEnabled(False)
        self.ui.Exercise102_AfterButton_pushButton.setStyleSheet("background-color: rgb(80, 96, 100)" + ";\n"
                                                                "border: 2px solid rgb(80, 96, 100)" + ";\n"
                                                                "border-radius: 10px" + ";\n"
                                                                "padding: 2px;"
                                                                )


