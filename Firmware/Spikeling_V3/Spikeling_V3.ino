/* SPDX-License-Identifier: GPL-3.0-or-later */
/* ========================================================================================================

  Spikeling V3.0 – Main Firmware
  ---------------------------------------------------------------------------------------------------------

  Open-source, spiking neuron simulator running an Izhikevich-style model.
    Project      : Spikeling
    Repository   : https://github.com/OpenSourceNeuro/Spikeling
    File         : Spikeling_V3.ino
    Board        : ESP32-S3-WROOM-1
    Author       : Maxime Zimmermann
    License      : GPL-3.0-or-later (https://www.gnu.org/licenses/gpl-3.0.html)

  Libraries :
    - Arduino core for ESP32
    - MCP_ADC 
    - MCP_DAC
    - SerialCommand
    - Gaussian noise library

  Description  :
    This sketch configures the Spikeling hardware, runs the Izhikevich neuron model in real time, handles 
    all analog/digital IO (Vm, synapses, photodiode, stimulus, noise), and streams compact binary packets 
    to the host GUI for oscilloscope-style visualisation and control.

  Arduino IDE — Tools menu settings used for this build :
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

  ---------------------------------------------------------------------------------------------------------
  (c) 2025 Maxime Zimmermann and contributors.
  This is free software; you can redistribute it and/or modify it under the terms of the GNU General Public
  License as published by the Free Software Foundation; 
  ====================================================================================================== */



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                        Header import                                                  */ 

  //#include "WiFi_functions.h"                                                          
  #include "Core_functions.h"
  #include "Serial_functions.h"


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                             Setup                                                     */ 

void setup() {
  HardwareSettings();                                                                           // Initialise all components
  calibrate_PhotodiodeDark();                                                                   // Set dark baseline with stim outputs forced OFF
  SerialFunctions();                                                                            // Initialise Serial commands
  //setupWifiAP();
  //Mode_opening();
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Main Loop                                                    */ 

void loop() {

  //wifiLoop();                                                                                   // Keep websocket responsive

  timing.current_us = micros();

  if ((timing.current_us - timing.lastStep_us) >= timing.step_us) {                             // It the time since the last loop has treached the set loop refresh rate
    timing.lastStep_us += timing.step_us;                                                       // keep steps evenly spaced

    const uint32_t prototype_tick_started_us = micros();
    SCmd.readSerial();                                                                          // Reads Serial for external commands
    
    poll_ToggleButtons();                                                                       // Read buzzer/LED toggle buttons (raw + time)
    update_ToggleButtons();                                                                     // Toggle buzzer/LED enable flags when pressed
    
    update_PatchInput();                                                                        // Sets Voltage membrane clamp value or inject Current      

    update_Noise();                                                                             // Sets Noise current level

    update_Photodiode();                                                                        // Sets Light generated current

    update_Synapse(syn1, syn1.defaultdecay);                                                    // Sets Synapse 1 current

    update_Synapse(syn2, syn2.defaultdecay);                                                    // Sets Synapse 2 current

    update_StimulusOutput();                                                                    // Determines Analog and Digital Values
    
    update_StimulusCurrentIn();                                                                 // Computes the dynamic Stimulus current 

    update_StimulusStatusLED();                                                                 // Mirror stimulus on RGB LED (intensity + polarity)

    // Shared inputs advance once; the selected membrane backend advances below.
                                                                 
    update_AllCurrent();                                                                        // Apply all current to the model



/*                         Selected membrane backend: passive VC or original Izhikevich CC                 */

    if (clampMode == ClampMode::VoltageClamp) {
      update_PassiveVoltageClamp();
    } else {
      // Original CC equations, sequential update order and spike reset.
      neuron.v = neuron.v + neuron.dt_ms*(0.04 * neuron.v * neuron.v + 5*neuron.v + 140 - neuron.u + neuron.total_current);
      neuron.u = neuron.u + neuron.dt_ms*(neuron.a * (neuron.b * neuron.v - neuron.u));
      if (neuron.v >= neuron.Vm_peak) {
        neuron.v = neuron.c;
        neuron.u = neuron.u + neuron.d;
      }
      if (neuron.v <= neuron.Vm_min) neuron.v = neuron.Vm_min;
    }

    update_Spike();                                                                             // Handles spike related functions and hardware (LED + Buzzer) and generate Axon Digital and Analog output

    send_SamplePacket();                                                                        // Quantize the current state data and send it as a compact binary frame.
    if (clampMode == ClampMode::VoltageClamp)
      voltageClamp.previous_loop_us = micros() - prototype_tick_started_us;
  }
}



