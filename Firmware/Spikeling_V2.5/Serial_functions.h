#pragma once     

#include "General_settings.h"
#include "Mode_LEDs.h"
#include <math.h>


inline SerialCommand SCmd;



// Argument parsing helpers
static inline bool readNextFloat(float &out) {
  char *arg = SCmd.next();
  if (!arg) return false;
  out = atof(arg);
  return true;
}

static inline bool readNextInt(int &out) {
  char *arg = SCmd.next();
  if (!arg) return false;
  out = atoi(arg);
  return true;
}


static inline void setFloatParam(bool &usePotFlag, float &param, float scale = 1.0f) {
  usePotFlag = false;
  float val;
  if (readNextFloat(val)) {
    param = val * scale;
  }
}

static inline void setIntParam(bool &usePotFlag, int &param) {
  usePotFlag = false;
  int val;
  if (readNextInt(val)) {
    param = val;
  }
}



inline void SetRefreshRate(){
  int val_us;
  if (readNextInt(val_us)) {
    timing.step_us  = (uint32_t)(val_us);
  }
}


inline void applyNeuronParameters(float a, float b, float c, float d, float v_rest) {
  neuron.a = a;
  neuron.b = b;
  neuron.c = c;
  neuron.d = d;
  neuron.v_rest = v_rest;

  neuron.v = neuron.v_rest;
  neuron.u = neuron.b * neuron.v;
  neuron.v_out = neuron.v;
  neuron.total_current = 0.0f;
  neuron.spike = false;

  patch.e_int = 0.0f;
  patch.I_clamp = 0.0f;

  if (clampMode == ClampMode::VoltageClamp) {
    patch.v_hold = constrain(neuron.v_rest, neuron.Vm_min, neuron.Vm_peak);
    patch.v_cmd  = patch.v_hold;
    patch.v_step = 0.0f;
  }
}


inline void SetNeuronModel(IzhikevichModel model) {
  currentModel = model;
  const auto &p = getIzhikevichParams(model);
  applyNeuronParameters(p.a, p.b, p.c, p.d, p.v_rest);
}

inline void ApplyNeuronModeIndex(int idx) {
  if (idx < 0) idx = 0;
  if (idx >= (int)IzhikevichModelCount) idx = (int)IzhikevichModelCount - 1;
  neuron.mode = idx;                                      // Store current mode index (so it doesn’t “snap back”)
  if (idx >= LED_Num) {
    lightOff();                                           // turns all charlieplex pins to INPUT
  } 
  else {
    lightOn(idx);                                         //  Update Charlieplexed mode LED to match
  }
  SetNeuronModel(static_cast<IzhikevichModel>(idx));      // Apply parameters and reset v/u as defined by your function
}

inline void NeuronOpening() {
  ApplyNeuronModeIndex(0);   // default preset + LED behavior
}

inline void NeuronMode() {
  int idx;
  if (readNextInt(idx)) {
    ApplyNeuronModeIndex(idx);                            // Updates neuron.mode + LEDs + model params in one place
  }
}

inline void NeuronCustom() {
  float a, b, c, d; 
  // Read required parameters
  if (!readNextFloat(a)) return;
  if (!readNextFloat(b)) return;
  if (!readNextFloat(c)) return;
  if (!readNextFloat(d)) return;
  // Apply custom parameters
  neuron.a = a;
  neuron.b = b;
  neuron.c = c;
  neuron.d = d;

  // Reset neuron state to a consistent initial condition
  neuron.v = neuron.v_rest;
  neuron.u = neuron.b * neuron.v;              
  neuron.mode = -1;
  lightOff();                                               // ensure LEDs are OFF for custom mode
}



inline void StimFre_on(){
  setIntParam(pot.use_stimfrequency_pot, stim.freq);
}
inline void StimFre_off(){
  pot.use_stimfrequency_pot = true;
}


inline void StimStr_on(){
  pot.use_stimstrength_pot = false;
  int val;
  if (readNextInt(val)) {
    stim.str_digital = val;
    stim.str_analog = val;
  }
}
inline void StimStr_off(){
  pot.use_stimstrength_pot = true;
}


inline void StimCus_on(){
  setIntParam(stim.custom_disable, stim.value_custom);
}
inline void StimCus_off(){
  stim.custom_disable = true; // Exit custom mode -> return to pot/square mode
}


inline void Serial_Trigger(){
  stim.serialTrigger_enable = true;
}


inline void PDGain_on(){
  setFloatParam(pot.use_photodiode_pot, PD.gain, 0.1f);
}
inline void PDGain_off(){
  pot.use_photodiode_pot = true;
}


inline void PDDecay_on(){
  setFloatParam(PD.decay_enable, PD.decay);
}
inline void PDDecay_off(){
  PD.decay_enable = true;
}


inline void PDRecovery_on(){
  setFloatParam(PD.recovery_enable, PD.recovery);
}
inline void PDRecovery_off(){
  PD.recovery_enable = true;
}


inline void patch_on() {
  float val;
  if (!readNextFloat(val)) return;

  if (clampMode == ClampMode::VoltageClamp) {
    // In V-clamp, PC1 sets the holding potential (Vhold). The "Current In" knob is ignored as an injected current.
    const float old_hold = patch.v_hold;

    pot.use_patch_pot = false;  // GUI overrides the voltage-command potentiometer in VC mode
    patch.v_hold = val;
    patch.v_cmd  = constrain(patch.v_hold + patch.v_step, neuron.Vm_min, neuron.Vm_peak);  // keep v_cmd coherent immediately
    patch.current_input = 0.0f;  // No disturbance current labs: ensure current injection is not active in VC mode

    // Only reset PI history if the command actually changed (prevents "strobing" the integrator if GUI re-sends same value).
    if (fabsf(patch.v_hold - old_hold) > 0.05f) {
      patch.e_int   = 0.0f;
      patch.I_clamp = 0.0f;
    }
    return;
  } 
  else {
    pot.use_patch_pot = false;                      // GUI overrides the current-command potentiometer in CC mode
    patch.current_clamp = val;
  }
}
inline void patch_off() {
  pot.use_patch_pot = true;    // re-enable voltage pot (VC hold pot)
}



inline void VClampMode(){
  int val;
  if (readNextInt(val)) {
    setClampMode(val ? ClampMode::VoltageClamp : ClampMode::CurrentClamp);
  }
}

// Set PI gains for voltage clamp: "VPID <Kp> <Ki>"
inline void VPID_set(){
  float kp;
  if (readNextFloat(kp)) patch.Kp = kp;
  float ki;
  if (readNextFloat(ki)) patch.Ki = ki;
}

// Set compliance limits for clamp current: "VIL <Imin> <Imax>"
inline void VILIM_set(){
  float mn, mx;
  if (readNextFloat(mn) && readNextFloat(mx)) {
    patch.I_min = mn;
    patch.I_max = mx;
  }
}

// Set pot span around v_rest for command voltage: "VSP <span_mV>"
inline void VSpan_set(){
  float span;
  if (readNextFloat(span)) {
    patch.v_cmd_span = span;
  }
}

// Reset PI integrator/state: "VRS"
inline void VClampReset(){
  patch.e_int = 0.0f;
  patch.I_clamp = 0.0f;
}


inline void Noise_on(){
  setFloatParam(pot.use_noise_pot, noise.current);
}
inline void Noise_off(){
  pot.use_noise_pot = true;
}


inline void Syn1Gain_on(){
  setFloatParam(syn1.use_syn_pot, syn1.gain, 0.25f);
}
inline void Syn1Gain_off(){
  syn1.use_syn_pot = true;
}


inline void Syn1Decay_on(){
  setFloatParam(syn1.decay_enable, syn1.decay, 1.0f / 1000.0f);
}
inline void Syn1Decay_off(){
  syn1.decay_enable = true;
}


inline void Syn2Gain_on(){
  setFloatParam(syn2.use_syn_pot, syn2.gain, 0.25f);
}
inline void Syn2Gain_off(){
  syn2.use_syn_pot = true;
}


inline void Syn2Decay_on(){
  setFloatParam(syn2.decay_enable, syn2.decay, 1.0f / 1000.0f);
}
inline void Syn2Decay_off(){
  syn2.decay_enable = true;
}


inline void Buzzer_on(){
  spike.Buzzer_enable = true;
}
inline void Buzzer_off(){
  spike.Buzzer_enable = false;
  digitalWrite(pins.gpio.spike, LOW);
}


inline void LED_on(){
  spike.LED_enable = true;
}
inline void LED_off() {
  spike.LED_enable = false;
  setRgbLedOff();
}


inline void Connected() {
  // Short safe connection blink using the faulty-board LED helpers.
  // First red, then white, then off.
  setRgbLedOff();
  delay(20);

  setVmRgbLed(spike.ledc_Max / 3);
  delay(80);

  setRgbLedOff();
  delay(40);

  setSpikeRgbLedWhite();
  delay(80);

  setRgbLedOff();
}


inline void Unrecognized(const char *cmd) {
  Serial.print("Unknown command: ");
  Serial.println(cmd);
}


inline void SerialFunctions(){
  SCmd.addCommand("DT",SetRefreshRate);
  SCmd.addCommand("NEU",NeuronMode);
  SCmd.addCommand("NE", NeuronCustom); 
  SCmd.addCommand("FR1",StimFre_on);
  SCmd.addCommand("FR0",StimFre_off);
  SCmd.addCommand("ST1",StimStr_on);
  SCmd.addCommand("ST0",StimStr_off);
  SCmd.addCommand("SC1",StimCus_on);
  SCmd.addCommand("SC0",StimCus_off);
  SCmd.addCommand("TR",Serial_Trigger);
  SCmd.addCommand("PG1",PDGain_on);
  SCmd.addCommand("PG0",PDGain_off);
  SCmd.addCommand("PD1",PDDecay_on);
  SCmd.addCommand("PD0",PDDecay_off);
  SCmd.addCommand("PR1",PDRecovery_on);
  SCmd.addCommand("PR0",PDRecovery_off);
  SCmd.addCommand("PC1",patch_on);
  SCmd.addCommand("PC0",patch_off);
  SCmd.addCommand("VCM",VClampMode);        // 0=current clamp, 1=voltage clamp
  SCmd.addCommand("VPID",VPID_set);         // set PI gains
  SCmd.addCommand("VIL",VILIM_set);         // set clamp current limits
  SCmd.addCommand("VSP",VSpan_set);         // set pot span around v_rest
  SCmd.addCommand("VRS",VClampReset);       // reset PI state
  SCmd.addCommand("NO1",Noise_on);
  SCmd.addCommand("NO0",Noise_off);
  SCmd.addCommand("SG11",Syn1Gain_on);
  SCmd.addCommand("SG10",Syn1Gain_off);
  SCmd.addCommand("SD11",Syn1Decay_on);
  SCmd.addCommand("SD10",Syn1Decay_off);
  SCmd.addCommand("SG21",Syn2Gain_on);
  SCmd.addCommand("SG20",Syn2Gain_off);
  SCmd.addCommand("SD21",Syn2Decay_on);
  SCmd.addCommand("SD20",Syn2Decay_off);
  SCmd.addCommand("BZ1",Buzzer_on);
  SCmd.addCommand("BZ0",Buzzer_off);
  SCmd.addCommand("LED1",LED_on);
  SCmd.addCommand("LED0",LED_off);
  SCmd.addCommand("CON",Connected);
  SCmd.setDefaultHandler(Unrecognized);
}



