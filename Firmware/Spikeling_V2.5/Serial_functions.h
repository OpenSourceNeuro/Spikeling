#pragma once     
#include "Mode_LEDS.h"


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


static inline void setFloatParam(bool &enableFlag, float &param, float scale = 1.0f) {
  enableFlag = false;
  float val;
  if (readNextFloat(val)) {
    param = val * scale;
  }
}

static inline void setIntParam(bool &enableFlag, int &param) {
  enableFlag = false;
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

inline void SetNeuronModel(IzhikevichModel model) {
  currentModel = model;
  const auto &p = getIzhikevichParams(model);
  neuron.a      = p.a;
  neuron.b      = p.b;
  neuron.c      = p.c;
  neuron.d      = p.d;
  neuron.v_rest = p.v_rest;
  neuron.v      = neuron.v_rest;
  neuron.u      = neuron.b * neuron.v;
}

inline void NeuronOpening() {
  SetNeuronModel(IzhikevichModel::TonicSpiking);
}

inline void NeuronMode() {
  int idx;
  if (readNextInt(idx)) {
    auto model = clampToModel(static_cast<std::size_t>(idx));
    SetNeuronModel(model);
  }
}

inline void StimFre_on(){
  setIntParam(stim.frequency_enable, stim.freq);
}
inline void StimFre_off(){
  stim.frequency_enable = true;
}


inline void StimStr_on(){
  stim.strength_enable = false;
  int val;
  if (readNextInt(val)) {
    stim.str_digital = val;
    stim.str_analog = val;
  }
}
inline void StimStr_off(){
  stim.strength_enable = true;
}


inline void StimCus_on(){
  setIntParam(stim.custom_enable, stim.value_custom);
}
inline void StimCus_off(){
  stim.custom_enable = true;
}


inline void Serial_Trigger(){
  stim.serialTrigger_enable = true;
}


inline void PDGain_on(){
  setFloatParam(PD.gain_enable, PD.gain, 0.1f);
}
inline void PDGain_off(){
  PD.gain_enable = true;
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


inline void IC_on(){
  setFloatParam(IC.enable, IC.current_clamp);
}
inline void IC_off(){
  IC.enable = true;
}



inline void VClampMode(){
  int val;
  if (readNextInt(val)) {
    setClampMode(val ? ClampMode::VoltageClamp : ClampMode::CurrentClamp);
  }
}

// Voltage command (hold) for voltage clamp mode
inline void VHold_on(){
  setFloatParam(IC.vcmd_enable, IC.v_cmd);               // disables pot by setting vcmd_enable=false and uses provided value
}
inline void VHold_off(){
  IC.vcmd_enable = true;                                 // re-enable pot reading for v_cmd
}

// Set PI gains for voltage clamp: "VPID <Kp> <Ki>"
inline void VPID_set(){
  float kp;
  if (readNextFloat(kp)) IC.Kp = kp;
  float ki;
  if (readNextFloat(ki)) IC.Ki = ki;
}

// Set compliance limits for clamp current: "VIL <Imin> <Imax>"
inline void VILIM_set(){
  float mn, mx;
  if (readNextFloat(mn) && readNextFloat(mx)) {
    IC.I_min = mn;
    IC.I_max = mx;
  }
}

// Set pot span around v_rest for command voltage: "VSP <span_mV>"
inline void VSpan_set(){
  float span;
  if (readNextFloat(span)) {
    IC.v_cmd_span = span;
  }
}

// Reset PI integrator/state: "VRS"
inline void VClampReset(){
  IC.e_int = 0.0f;
  IC.I_clamp = 0.0f;
}


inline void Noise_on(){
  setFloatParam(noise.enable, noise.current);
}
inline void Noise_off(){
  noise.enable = true;
}


inline void Syn1Gain_on(){
  setFloatParam(syn1.gain_enable, syn1.gain, 0.25f);
}
inline void Syn1Gain_off(){
  syn1.gain_enable = true;
}


inline void Syn1Decay_on(){
  setFloatParam(syn1.decay_enable, syn1.decay, 1.0f / 1000.0f);
}
inline void Syn1Decay_off(){
  syn1.decay_enable = true;
}


inline void Syn2Gain_on(){
  setFloatParam(syn2.gain_enable, syn2.gain, 0.25f);
}
inline void Syn2Gain_off(){
  syn2.gain_enable = true;
}


inline void Syn2Decay_on(){
  setFloatParam(syn2.decay_enable, syn2.decay, 1.0f / 1000.0f);
}
inline void Syn2Decay_off(){
  syn2.decay_enable = true;
}


inline void Buzzer_on(){
  Buzzer_enable = true;
}

inline void Buzzer_off(){
  Buzzer_enable = false;
  digitalWrite(pins.gpio.spike, LOW);
}


inline void LED_on(){
  LED_enable = true;
}


inline void LED_off(){
  LED_enable = false;
  ledcWrite(pins.gpio.led_r, 0);
  ledcWrite(pins.gpio.led_g, 0);
  ledcWrite(pins.gpio.led_b, 0);
}


inline void Connected(){
  digitalWrite(pins.gpio.led_r,HIGH);delay(5);
  digitalWrite(pins.gpio.led_g,HIGH);digitalWrite(pins.gpio.led_r,LOW);delay(5);
  digitalWrite(pins.gpio.led_b,HIGH);digitalWrite(pins.gpio.led_g,LOW);delay(5);
  digitalWrite(pins.gpio.led_b,LOW);delay(5);
}


inline void Unrecognized(const char *cmd) {
  Serial.print("Unknown command: ");
  Serial.println(cmd);
}


inline void SerialFunctions(){
  SCmd.addCommand("DT",SetRefreshRate);
  SCmd.addCommand("NEU",NeuronMode);
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
  SCmd.addCommand("IC1",IC_on);
  SCmd.addCommand("IC0",IC_off);
  SCmd.addCommand("VCM",VClampMode);        // 0=current clamp, 1=voltage clamp
  SCmd.addCommand("VH1",VHold_on);          // set v_cmd from serial and disable pot
  SCmd.addCommand("VH0",VHold_off);         // re-enable pot for v_cmd
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



