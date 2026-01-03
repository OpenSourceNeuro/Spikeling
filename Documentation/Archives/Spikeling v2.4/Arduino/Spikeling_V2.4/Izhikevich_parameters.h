/*          ---  The Izhikevich Model  ---

Bifurcation methodologies enable us to reduce many biophysically accurate Hodgkin–Huxley-type neuronal models 
to a two-dimensional (2-D) system of ordinary differential equations of the form:
          v' = 0.04v** + 5v + 140 - u + I 
          u' = a(bv - u)
      with the auxiliary after-spike resetting:
          if v >= 30 mV, then v = c and u = u + d

Here, v and u are dimensionless variables, and a, b, c, and d are dimensionless parameters, and '= d/dt, 
where t is the time. The variable v represents the membrane potential of the neuron and u represents a membrane 
recovery variable, which accounts for the activation of K+ ionic currents and inactivation of Na+ ionic currents, 
and it provides negative feedback to v. After the spike reaches its apex (+30 mV), the membrane voltage and the 
recovery variable are reset. Synaptic currents or injected DC-currents are delivered via the variable I.

As most real neurons, the model does not have a fixed threshold; Depending on the history of the membrane potential 
prior to the spike, the threshold potential can be as low as -55 mV or as high as -40mV

• The parameter a describes the time scale of the recovery variable u. 
  Smaller values result in slower recovery. A typical value is a = 0:02.
  
• The parameter b describes the sensitivity of the recovery variable u 
  to the subthreshold fluctuations of the membrane potential v.
  Greater values couple v and u more strongly resulting in possible 
  subthreshold oscillations and low-threshold spiking dynamics. 
  A typical value is b = 0:2. The case b < a(b > a) corresponds to saddle-node (Andronov–Hopf) 
  bifurcation of the resting state

• The parameter c describes the after-spike reset value of the membrane potential v caused
  by the fast high-threshold K+ conductances. 
  A typical value is c = -65mV

• The parameter d describes after-spike reset of the recovery variable u caused by slow 
  high-threshold Na+ and K+ conductances.
  A typical value is d = 2.
  
*/

float v; // voltage in Izhikevich model
float u; // recovery variable in Izhikevich model

float timestep_ms     = 0.1;  // default 0.1. This is the "intended" refresh rate of the model.
float a_Izhikevich;   // time scale of recovery variable u. Smaller a gives slower recovery
float b_Izhikevich;   // recovery variable associated with u. greater b coules it more strongly 
float c_Izhikevich;   // after spike reset value
float d_Izhikevich;   // after spike reset of recovery variable


// From Iziekevich.org - see also https://www.izhikevich.org/publications/figure1.pdf:
float TonicSpiking[]              = { 0.02,  0.2,   -65,  6    };
float PhasicSpiking[]             = { 0.02,  0.25,  -65,  6    };
float TonicBursting[]             = { 0.02,  0.2,   -50,  2    };
float PhasicBursting[]            = { 0.02,  0.25,  -55,  0.05 };
float MixedMode[]                 = { 0.02,  0.2,   -55,  4    };
float SpikeFrequencyAdaptation[]  = { 0.01,  0.2,   -65,  8    };
float Class1[]                    = { 0.02, -0.1,   -55,  6    };
float Class2[]                    = { 0.2,   0.26,  -65,  0    };
float SpikeLatency[]              = { 0.02,  0.2,   -65,  6    };
float Custom1[]                   = { 0.05,  0.26,  -60,  0    };
float Custom2[]                   = { 0.1,   0.26,  -60,  0    };
float Custom3[]                   = { 0.02,  -0.1,  -55,  0    };

float Array_a_Izhikevich[] = { 
  TonicSpiking[0],
  PhasicSpiking[0],
  TonicBursting[0],
  PhasicBursting[0],
  MixedMode[0],
  SpikeFrequencyAdaptation[0],
  Class1[0],
  Class2[0],  
  SpikeLatency[0], 
  Custom1[0],  
  Custom2[0],  
  Custom3[0]  
  }; 
  
float Array_b_Izhikevich[] = { 
  TonicSpiking[1],
  PhasicSpiking[1],
  TonicBursting[1],
  PhasicBursting[1],
  MixedMode[1],
  SpikeFrequencyAdaptation[1],
  Class1[1],
  Class2[1],  
  SpikeLatency[1], 
  Custom1[1],  
  Custom2[1],  
  Custom3[1] 
  };     
    
float Array_c_Izhikevich[] =  { 
  TonicSpiking[2],
  PhasicSpiking[2],
  TonicBursting[2],
  PhasicBursting[2],
  MixedMode[2],
  SpikeFrequencyAdaptation[2],
  Class1[2],
  Class2[2],  
  SpikeLatency[2], 
  Custom1[2],  
  Custom2[2],  
  Custom3[2] 
  }; 
  
float Array_d_Izhikevich[] =  { 
  TonicSpiking[3],
  PhasicSpiking[3],
  TonicBursting[3],
  PhasicBursting[3],
  MixedMode[3],
  SpikeFrequencyAdaptation[3],
  Class1[3],
  Class2[3],  
  SpikeLatency[3], 
  Custom1[3],  
  Custom2[3],  
  Custom3[3] 
  }; 

void Izhikevich_opening(){
  a_Izhikevich = Array_a_Izhikevich[0];
  b_Izhikevich = Array_b_Izhikevich[0];
  c_Izhikevich = Array_c_Izhikevich[0];
  d_Izhikevich = Array_d_Izhikevich[0];
}


////////////////////////////////////////////////////////////////////////////////////////////////
//    From Iziekevich.org - see also https://www.izhikevich.org/publications/figure1.pdf:     //
////////////////////////////////////////////////////////////////////////////////////////////////
/*
      0.02      0.2     -65      6       14 ;...    % tonic spiking
      0.02      0.25    -65      6       0.5 ;...   % phasic spiking
      0.02      0.2     -50      2       15 ;...    % tonic bursting
      0.02      0.25    -55     0.05     0.6 ;...   % phasic bursting
      0.02      0.2     -55     4        10 ;...    % mixed mode
      0.01      0.2     -65     8        30 ;...    % spike frequency adaptation
      0.02      -0.1    -55     6        0  ;...    % Class 1
      0.2       0.26    -65     0        0  ;...    % Class 2
      0.02      0.2     -65     6        7  ;...    % spike latency
      0.05      0.26    -60     0        0  ;...    % subthreshold oscillations
      0.1       0.26    -60     -1       0  ;...    % resonator
      0.02      -0.1    -55     6        0  ;...    % integrator
      0.03      0.25    -60     4        0;...      % rebound spike
      0.03      0.25    -52     0        0;...      % rebound burst
      0.03      0.25    -60     4        0  ;...    % threshold variability
      1         1.5     -60     0      -65  ;...    % bistability
        1       0.2     -60     -21      0  ;...    % DAP
      0.02      1       -55     4        0  ;...    % accomodation
     -0.02      -1      -60     8        80 ;...    % inhibition-induced spiking
     -0.026     -1      -45     0        80];       % inhibition-induced bursting
*/
