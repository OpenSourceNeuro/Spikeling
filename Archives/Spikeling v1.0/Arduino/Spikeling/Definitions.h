// -----------------------------------------------------------------------------
// Global definitions
// -----------------------------------------------------------------------------
#ifndef  Definitions_h  
#define  Definitions_h

#define  ID_V                 0
#define  ID_I_TOTAL           1
#define  ID_I_PD              2
#define  ID_I_ANALOG_IN       3
#define  ID_I_SYNAPSE         4
#define  ID_I_STIM_STATE      5
#define  ID_I_SPIKE_IN1_STATE 6
#define  ID_I_SPIKE_IN2_STATE 7
#define  ID_I_CURR_MICROSS    8

// Model output structure
//
typedef struct {
  float v, I_total, I_PD, I_AnalogIn, I_Synapse;
  int Stim_State, SpikeIn1State, SpikeIn2State;
  unsigned long currentMicros;
  int NeuronBehaviour;
  } output_t;

#endif
// -----------------------------------------------------------------------------
