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

    update_VoltageClampPI();                                                                    // If in voltage-clamp mode, compute PI clamp current
                                                                 
    update_AllCurrent();                                                                        // Apply all current to the model



/*               -----  Spikeling computation running on Izhikevich mmodel  -----                        */

    neuron.v = neuron.v + neuron.dt_ms*(0.04 * neuron.v * neuron.v  + 5*neuron.v + 140 - neuron.u + neuron.total_current);   // Compute the voltage variable
    neuron.u = neuron.u + neuron.dt_ms*(neuron.a * (neuron.b * neuron.v - neuron.u));                                        // Compute the recovery variable

    if (clampMode != ClampMode::VoltageClamp){                                                  // If voltage clamp is off
      if (neuron.v >= neuron.Vm_peak){                                                            // If the membrane voltage has crossed the spike threshold (30mV by default):
        neuron.v = neuron.c;                                                                        // Reset membrane potential to the model’s reset value “c” (represents rapid repolarisation after an action potential).
        neuron.u = neuron.u + neuron.d;                                                             // Increase recovery/adaptation variable by “d” (represents spike-triggered adaptation / after-spike conductances).
      }
    }


/*                          -----  Voltage clamp numeric safety  -----                                   */

    if (clampMode == ClampMode::VoltageClamp) {
      if (!isfinite(neuron.v) || !isfinite(neuron.u)) {
        neuron.v = constrain(patch.v_cmd, neuron.Vm_min, neuron.Vm_peak);
        neuron.u = neuron.b * neuron.v;                                                         // Reinitialize recovery variable consistently
        patch.e_int   = 0.0f;                                                                   // Reset PI history (it will also be invalid)
        patch.I_clamp = 0.0f;
      }

      static uint8_t vc_clip_ctr = 0;
      if (neuron.v >= (neuron.Vm_peak - 1e-3f)) vc_clip_ctr++; else vc_clip_ctr = 0;

      if (vc_clip_ctr >= 3) {
        neuron.v = constrain(patch.v_cmd, neuron.Vm_min, neuron.Vm_peak - 1.0f);
        neuron.u = neuron.b * neuron.v;
        patch.e_int   = 0.0f;
        patch.I_clamp = 0.0f;
        vc_clip_ctr = 0;
      }      
      neuron.v = constrain(neuron.v, neuron.Vm_min, neuron.Vm_peak);                            // Hard-bound Vm so the quadratic term can never run away in V-clamp.
    }
    
    if (neuron.v <= neuron.Vm_min) {                                                            // If voltage goes below the min voltage value (-90mV by default):
      neuron.v = neuron.Vm_min;                                                                   // Keep the voltage at Vm_min : Prevent pinVm going into overdrive - but also means that it will flatline at Vm_min. 
    } 

    update_Spike();                                                                             // Handles spike related functions and hardware (LED + Buzzer) and generate Axon Digital and Analog output

    send_SamplePacket();                                                                        // Quantize the current state data and send it as a compact binary frame.
  }
}



