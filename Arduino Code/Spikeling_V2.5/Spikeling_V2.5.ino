/* ==========================================================================
   Spikeling V2.5 – Main Firmware
   --------------------------------------------------------------------------
   Open-source, Arduino-compatible spiking neuron simulator
   running an Izhikevich-style model on an ESP32-WROOM-32.

   Project      : Spikeling
   Repository   : https://github.com/OpenSourceNeuro/Spikeling
   File         : Spikeling_V2.5.ino
   Board        : ESP32-WROOM-32 (ESP32 DevKit-style board)
   Author       : Maxime Zimmermann
   Contributors : Spikeling / OpenSourceNeuro community

   License      : GPL-3.0-or-later
                  See the LICENSE file in the repository for details
                  or https://www.gnu.org/licenses/gpl-3.0.html

   Dependencies :
     - Arduino core for ESP32
     - MCP_ADC (MCP3208 driver)
     - SerialCommand
     - Gaussian noise library
     - PySide6 / Qt Serial (for host GUI, not on-device)

   Description  :
     This sketch configures the Spikeling hardware, runs the Izhikevich
     neuron model in real time, handles all analog/digital IO (Vm,
     synapses, photodiode, stimulus, noise), and streams compact binary
     packets to the host GUI for oscilloscope-style visualization and
     control.

   --------------------------------------------------------------------------
   (c) 2025 Maxime Zimmermann and contributors.
   This is free software; you can redistribute it and/or modify it under the
   terms of the GNU General Public License as published by the Free Software
   Foundation; either version 3 of the License, or (at your option) any
   later version.
   ========================================================================== */
   

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                        Header import                                                  */ 
                                                            
  #include "Core_functions.h"



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                             Setup                                                     */ 

void setup() {
  HardwareSettings();                                                                         // Initialise all components
  NeuronOpening();                                                                            // Set neuron default parameters
  SerialFunctions();                                                                          // Initialise Serial commands
  Mode_opening();
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Main Loop                                                    */ 

void loop() {

  timing.current_us = micros();

  if ((timing.current_us - timing.lastStep_us) >= timing.step_us) {                           // It the time since the last loop has treached the set loop refresh rate
    timing.lastStep_us += timing.step_us;                                                     // keep steps evenly spaced

    SCmd.readSerial();                                                                        // Reads Serial for external commands

    update_NeuronMode();                                                                      // Sets izhikevich variables when changed

    update_InputCurrent();                                                                    // Sets Voltage membrane clamp value       

    update_Noise();                                                                           // Sets Noise current level

    update_Photodiode();                                                                      // Sets Light generated current

    update_Synapse(syn1, 0.995f);                                                             // Sets Synapse 1 current

    update_Synapse(syn2, 0.990f);                                                             // Sets Synapse 2 current

    update_StimulusOutput();                                                                  // Determines Analog and Digital Values

    update_StimulusCurrentIn();                                                               // Computes the dynamic Stimulus current 

    compute_AllCurrent();



/*               -----  Spikeling computation running on Izhikevich mmodel  -----                        */

    neuron.v = neuron.v + neuron.dt_ms*(0.04 * neuron.v * neuron.v  + 5*neuron.v + 140 - neuron.u + neuron.total_current);   // Compute the voltage variable
    neuron.u = neuron.u + neuron.dt_ms*(neuron.a * (neuron.b * neuron.v - neuron.u));                                        // Compute the recovery variable

    if (neuron.v >= neuron.Vm_peak){                                                          // If the voltage value is above the peak (30mV by default):
      neuron.v = neuron.c;                                                                      // The voltage variable corresponds to the "after spike reset value"
      neuron.u = neuron.u + neuron.d;                                                           // The recovery variable is incremented by the "after spike reset of recovery variable"
    }
    
    if (neuron.v <= neuron.Vm_min) {                                                          // If voltage goes below the min voltage value (-90mV by default):
      neuron.v = neuron.Vm_min;                                                                 // Keep the voltage at Vm_min : Prevent pinVm going into overdrive - but also means that it will flatline at Vm_min. 
    } 



    update_Spike();                                                                           // Handles spike related functions and hardware (LED + Buzzer) and generate Axon Digital and Analog output

    send_SamplePacket();                                                                      // Quantize the current state data and send it as a compact binary frame.

    //Serial.println(PD.current);
  }
}


