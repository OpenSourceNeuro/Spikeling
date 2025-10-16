<p align="left"><img width="270" height="170" src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/SpikyLogo.png">

<h1 align="center"> Instruction Manual</h1></p>

<h1 align="left"> Overview</h1></p>

<p style='text-align: justify;'>

This document contains detailed instructions to connect, install and use Spikeling v2.2

The hardware itself is controlled by a <a href="https://www.espressif.com/en/products/devkits/esp32-devkitc">ESP-32 development board</a> (ESP-32 WROVER-E). It runs on a C++ code which can be updated through the <a href="https://www.arduino.cc">Arduino IDE</a>. The <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/Arduino%20Code">Arduino Code session</a> in this repository details how to modify the Spikeling code.


<strong>In order to communicate with the ESP-32 micro-controller, users must first install the latest SiLabs <a href="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers">CP210x driver</a></strong>

The software itself consists on a Graphical User Interface (GUI) built on python using the pyqt6/pyside6 library packages:
  - Users can run the <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/GUI/PyQt">python code</a> directly by executing the <strong>Main.py</strong> file.
  - A Windows executable file is also available and can be found <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/GUI/Windows/Spikeling.exe">here</a>
  - A Linux version is available <a href="">here</a>
  - And a Mac version <a href="">here</a>

  </p>

  ***

  ## Driver Installation

  <br>

  Spikeling runs on an Espressif ESP32 board and requires the USB to UART bridge <a href="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"> CP210x driver</a>,  which can be downloaded<a href="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads"> <strong>here</strong></a>.

  Once the driver has been installed, users can operated the GUI (c.f. <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/GUI"> GUI UserManual</a>) or modify the <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/Arduino%20Code/Spikeling_V2_2">microcontroller code</a> through the Arduino Integrated Development Environment (IDE).

  <br></br>


  ## Microcontroller Arduino code

  <br>

  ##### Arduino IDE

  <br>

  The ESP32 microcontroller runs a C++ code which can be accessed via the Arduino IDE, which can be downloaded <a href="https://www.arduino.cc/en/software">here</a>.

  <br>

  ##### ESP32 Add-on

  <br>

  <img align="right" height="200" src="./Images/Arduino01.png">

  Once the IDE is installed, users needs to install the ESP32 board library:

  In the Arduino IDE, go to <strong> File > Preferences </strong>

  Enter the following link into the <strong>Additional Board Manager URLs</strong> field:

  https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

  <img align="center" height="300" src="./Images/Arduino02.png">
  Then click on the <strong>OK</strong> button.

  <br></br>

  Next, open the Boards Manager. Go to <strong> Tools > Board > Board Manager...</strong>

  Search for ESP32 and press install button for the <strong>ESP32 by Espressif Systems</strong>.

  <img align="center" height="300" src="./Images/Arduino03.png">
  Then click on the <strong>Install</strong> button.

  <br></br>

  ##### Compiling the code

  <br>

  Within the Arduino IDE, user needs to select the FQBN (Fully Qualified Board Name) on which the code will be compiled for.

  Here the ESP32 Dev Module needs to be selected.

  Go to <strong>Tools > Board > esp32 > ESP32 Dev Module </strong>

  <img align="center" src="./Images/Arduino04.png">
  The board name should be displayed  as shown.

  <br></br>

 ##### Installing Libraries

  <br>

  Before compiling the Spikeling code, a few libraries need to be installed:
    - Arduino-SerialCommand
    - MCP3208 by Rodolfo Pietro
    - Gaussian by Ivan Seidel

  Most of them can be downloaded from the Arduino IDE: Go to <strong>Sketch > Include Library > Manage Libraries</strong>, enter the library name, then install it following the same process as for the board library.

  We however recommend for the Arduino-SerialCommand library to manually place the library folder which can be found <a href="https://github.com/OpenSourceNeuro/Spikeling-V2/tree/main/Arduino%20Code/Librairies">here</a> into the library folder. For Windows Users: <strong>C:/Users/x/Documents/Arduino/libraries</strong>

  Now everything is set to compile and verify the code.

  Users can now select the COM port on which the ESP32 is connected ( Go to <strong>Tools > port</strong> ) and upload the code onto the board.
