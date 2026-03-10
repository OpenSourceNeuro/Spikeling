<p align="left"><img width="270" height="170" src="../Documentation/Images/SpikyLogo.png">
</p>

<div align="center">

# **Upload firmware and driver installation**


<p>
  <a href="https://github.com/OpenSourceNeuro/Spikeling/blob/main/LICENSES/GPL-3.0-or-later.txt">
    <img alt="License" src="https://img.shields.io/github/license/OpenSourceNeuro/Spikeling">
  </a>
  <a href="https://github.com/OpenSourceNeuro/Spikeling/tree/main/Firmware/Spikeling_V2.5">
    <img alt="version 2" src="https://img.shields.io/badge/version_2-v2.5-blue">
  </a>
  <a href="https://opensourceneuro.github.io/Spikeling/Firmware/Spikeling_V3">
  <img alt="version 3" src="https://img.shields.io/badge/version_3-v3.1-blue">
</a>
  <a href="https://opensourceneuro.github.io/Spikeling/firmware/">
    <img alt="Docs" src="https://img.shields.io/badge/docs-wiki-green">
  </a>
</p>

<p align="right">
  developed by M.J.Y. Zimmermann<br>
  maintained by P. Rignanese & A. Koumoundourou<br>
  based on an original idea by T. Baden
</p>

</div>

<br></br>

***
## **Spikeling version 2**  

<p style='text-align: justify;'>
All version 2 are built on an Espressif ESP32 board and requires the USB to UART bridge <a href="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"> CP210x driver</a>,  which can be downloaded<a href="https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers?tab=downloads"> <strong>here</strong></a>.
</p>

<br>

## Microcontroller Arduino code

<br>

##### Arduino IDE

<br>

<p style='text-align: justify;'>
The ESP32 microcontroller runs a C++ code which can be accessed via the Arduino IDE, which can be downloaded <a href="https://www.arduino.cc/en/software">here</a>.
</p>

<br>

##### ESP32 Add-on

<br>

<img align="right" height="200" src="../Documentation/Images/Arduino01.png">

Once the IDE is installed, users needs to install the ESP32 board library:

In the Arduino IDE, go to <strong> File > Preferences </strong>

Enter the following link into the <strong>Additional Board Manager URLs</strong> field:

https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

<img align="center" height="300" src="../Documentation/Images/Arduino02.png">
Then click on the <strong>OK</strong> button.

<br></br>

Next, open the Boards Manager. Go to <strong> Tools > Board > Board Manager...</strong>

Search for ESP32 and press install button for the <strong>ESP32 by Espressif Systems</strong>.

<img align="center" height="300" src="../Documentation/Images/Arduino03.png">
Then click on the <strong>Install</strong> button.

<br></br>

##### Compiling the code

<br>

Within the Arduino IDE, user needs to select the FQBN (Fully Qualified Board Name) on which the code will be compiled for.

Here the ESP32 Dev Module needs to be selected.

Go to <strong>Tools > Board > esp32 > ESP32 Dev Module </strong>

<img align="center" src="../Documentation/Images/Arduino04.png">
The board name should be displayed  as shown.

<br></br>

Before compiling the LED Zappelin code, a few librairies need to be installed:
  - **Arduino-SerialCommand**: Library by Shyd (based on Steven Cogswell) https://github.com/shyd/Arduino-SerialCommand
  - **Gaussian**: Library by Ivan Seidel https://github.com/ivanseidel/Gaussian
  - **MCP_ADC**: Microchip SPI ADC Library by Rob Tillaart https://github.com/RobTillaart/MCP_ADC

Most of them can be downloaded from the Arduino IDE: Go to <strong>Sketch > Include Librairy > Manage Libraries</strong>, enter the library name, then install it following the same process as for the board library.

Library can also be manually placed in the library folder from <a href="https://github.com/OpenSourceNeuro/Spikeling/tree/main/Firmware/Librairies">here</a>. For Windows Users: <strong>C:/Users/x/Documents/Arduino/libraries</strong>

Now everything is set to compile and verify the code.

Users can now select the COM port on which the ESP32 is connected ( Go to <strong>Tools > port</strong> ) and upload the code onto the board.

<br></br>

***
## **Spikeling version 3**  

All version 3 are built on an Espressif ESP32 S3 board and are connected directly to their native USB. Hence no driver is required here.

These board however do not possess built-in DAC, so a DAC chip is added to the version 3 boards and an extra library is needed:

- **MCP_DAC**: Microchip SPI DAC Library by Rob Tillaart https://github.com/RobTillaart/MCP_DAC

For version 3, This board need to be selected.
<img align="center" src="../Documentation/Images/Arduino05.png">


Additionally, these parameters must be entered in the **Tool** tab:

    Core / Board --------------------------------------------------------------
      Tools > Board:                 ESP32S3 Dev Module
      Tools > USB Mode:              Hardware CDC and JTAG (wording may vary)
      Tools > USB CDC On Boot:       Enabled

    CPU / Flash / PSRAM ------------------------------------------------------
      Tools > CPU Frequency:         240MHz 
      Tools > Flash Frequency:       80MHz
      Tools > Flash Mode:            QIO 80MHz
      Tools > Flash Size:            4MB
      Tools > PSRAM:                 Disabled
