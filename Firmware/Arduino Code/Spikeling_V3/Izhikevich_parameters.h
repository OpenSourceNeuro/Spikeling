#pragma once      

#include <cstdint>   // for uint8_t
#include <cstddef>   // for std::size_t



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                  Neurons parameters definition                                  */ 

/*                ---  c.f. https://www.izhikevich.org/publications/figure1.pdf  ---               */

enum class IzhikevichModel : uint8_t {
  TonicSpiking = 0,
  PhasicSpiking,
  TonicBursting,
  PhasicBursting,
  MixedMode,
  SpikeFrequencyAdaptation,
  Class1,
  Class2,
  SpikeLatency,
  SubThresholdOscillations,
  Resonator,
  Integrator,
  ReboundSpike,
  ReboundBurst,
  ThresholdVariability,
  Bistability,
  DAP,
  Accommodation,
  InhibitionInducedSpiking,
  InhibitionInducedBursting,

  Count                                       // Sentinel: number of valid models (not a model itself)               
};



struct IzhikevichParams {
  float a;                                    // Time scale of recovery variable u
  float b;                                    // Sensitivity of u to subthreshold v
  float c;                                    // After-spike reset value of v (mV)
  float d;                                    // After-spike reset of u
  float v_rest;                               // Resting membrane potential (mV), not in original 4-param model
};


/*              - Number of defined Izhikevich models -             */
inline constexpr std::size_t IzhikevichModelCount = static_cast<std::size_t>(IzhikevichModel::Count);



/*       - Lookup table: parameters for each IzhikevichModel -      */
inline constexpr IzhikevichParams izhikevich[] = {
//    a       b        c       d       v_rest 
  { 0.02f,  0.20f,  -65.0f,   6.0f,   -70.0f },   // TonicSpiking
  { 0.02f,  0.25f,  -65.0f,   6.0f,   -64.0f },   // PhasicSpiking
  { 0.02f,  0.20f,  -50.0f,   2.0f,   -70.0f },   // TonicBursting
  { 0.02f,  0.25f,  -55.0f,   0.05f,  -64.0f },   // PhasicBursting
  { 0.02f,  0.20f,  -55.0f,   4.0f,   -70.0f },   // MixedMode
  { 0.01f,  0.20f,  -65.0f,   8.0f,   -70.0f },   // SpikeFrequencyAdaptation
  { 0.02f, -0.10f,  -55.0f,   6.0f,   -60.0f },   // Class1
  { 0.20f,  0.26f,  -65.0f,   0.0f,   -64.0f },   // Class2
  { 0.02f,  0.20f,  -65.0f,   6.0f,   -70.0f },   // SpikeLatency
  { 0.05f,  0.26f,  -60.0f,   0.0f,   -62.0f },   // SubThresholdOscillations
  { 0.10f,  0.26f,  -60.0f,  -1.0f,   -62.0f },   // Resonator
  { 0.02f, -0.10f,  -55.0f,   6.0f,   -60.0f },   // Integrator
  { 0.03f,  0.25f,  -60.0f,   4.0f,   -64.0f },   // ReboundSpike
  { 0.03f,  0.25f,  -52.0f,   0.0f,   -64.0f },   // ReboundBurst
  { 0.03f,  0.25f,  -60.0f,   4.0f,   -64.0f },   // ThresholdVariability
  { 0.10f,  0.26f,  -60.0f,   0.0f,   -61.0f },   // Bistability
  { 1.00f,  0.20f,  -60.0f,  -21.0f,  -70.0f },   // DAP
  { 0.02f,  1.00f,  -55.0f,   4.0f,   -65.0f },   // Accommodation
  { 0.02f,  1.00f,  -60.0f,   8.0f,   -63.8f },   // InhibitionInducedSpiking
  { 0.026f, -1.00f, -45.0f,  -2.0f,   -63.8f },   // InhibitionInducedBursting
};



/*  Compile-time check that the enum and lookup table stay in sync  */
static_assert(IzhikevichModelCount == (sizeof(izhikevich) / sizeof(izhikevich[0])),"IzhikevichModel enum and izhikevich parameter table size mismatch");



/*          - Convenience helper to get parameters safely -         */   //Usage: const auto& p = getIzhikevichParams(IzhikevichModel::TonicSpiking);
inline constexpr const IzhikevichParams& getIzhikevichParams(IzhikevichModel model) {
  return izhikevich[static_cast<std::size_t>(model)];
}

inline constexpr IzhikevichModel clampToModel(std::size_t index) {
  if (index >= IzhikevichModelCount) {
    index = 0; 
  }
  return static_cast<IzhikevichModel>(index);
}

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                    ---  The Izhikevich Model  ---                                     */ 

/*Bifurcation methodologies enable us to reduce many biophysically accurate Hodgkin–Huxley-type neuronal models 
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


  https://www.izhikevich.org/publications/whichmod.htm
  https://www.izhikevich.org/publications/whichmod.pdf
  https://www.izhikevich.org/publications/figure1.m

*/

