#pragma once

#include <WiFi.h>
#include <WebSocketsServer.h> // (by Markus Sattler / Links2004)
#include <ArduinoJson.h>  //(by Benoit Blanchon)

// Pulls in: timing, stim, IC, noise, syn1, syn2, PD, pkt, scaling constants, etc.
#include "Serial_functions.h"   // includes General_settings.h

// -----------------------------
// WiFi / WebSocket configuration
// -----------------------------
static const char* WIFI_SSID = "SpikelingAP";
static const char* WIFI_PASS = "spiky";
static constexpr uint16_t WS_PORT = 81;

// If you want the WiFi stream to include your 0xAA 0x55 header:
// - OFF: WS frame is exactly 16 bytes (= SamplePacket)
// - ON : WS frame is 18 bytes (= header + SamplePacket)
static constexpr bool WIFI_SEND_SERIAL_HEADER = false;

// -----------------------------
// Streaming control
// -----------------------------
struct WifiStreamCtrl {
  volatile bool enabled = false;
  volatile uint16_t decim = 5;   // send 1 out of N samples
  uint16_t cnt = 0;
};

inline WifiStreamCtrl wifiStream;
inline WebSocketsServer ws(WS_PORT);

// -----------------------------
// Helpers (mirror your Serial handlers’ semantics)
// -----------------------------
static inline void applyFloat(bool &enableFlag, float &param, float v, float scale = 1.0f) {
  enableFlag = false;          // manual override active
  param = v * scale;
}

static inline void applyInt(bool &enableFlag, int &param, int v) {
  enableFlag = false;          // manual override active
  param = v;
}

// Route a “SerialCommand-like token” coming from WiFi
static inline void dispatchToken(const String& cmd, bool hasVal, float v) {

  // --- Timing / model
  if (cmd == "DT" && hasVal) {
    int val_us = (int)v;
    if (val_us < 1000) val_us = 1000;
    if (val_us > 1000000) val_us = 1000000;
    timing.step_us = (uint32_t)val_us;
    return;
  }

  if (cmd == "NEU" && hasVal) {
    int idx = (int)v;
    auto model = clampToModel((std::size_t)idx);
    SetNeuronModel(model);
    return;
  }

  // --- Stimulus
  if (cmd == "FR1" && hasVal) { applyInt(stim.frequency_enable, stim.freq, (int)v); return; }
  if (cmd == "FR0")           { stim.frequency_enable = true; return; }

  if (cmd == "ST1" && hasVal) {
    stim.strength_enable = false;
    int val = (int)v;
    stim.str_digital = val;
    stim.str_analog  = val;
    return;
  }
  if (cmd == "ST0") { stim.strength_enable = true; return; }

  if (cmd == "SC1" && hasVal) { applyInt(stim.custom_enable, stim.value_custom, (int)v); return; }
  if (cmd == "SC0")           { stim.custom_enable = true; return; }

  if (cmd == "TR")            { stim.serialTrigger_enable = true; return; }

  // --- Photodiode
  if (cmd == "PG1" && hasVal) { applyFloat(PD.gain_enable, PD.gain, v, 0.1f); return; }
  if (cmd == "PG0")           { PD.gain_enable = true; return; }

  if (cmd == "PD1" && hasVal) { applyFloat(PD.decay_enable, PD.decay, v); return; }
  if (cmd == "PD0")           { PD.decay_enable = true; return; }

  if (cmd == "PR1" && hasVal) { applyFloat(PD.recovery_enable, PD.recovery, v); return; }
  if (cmd == "PR0")           { PD.recovery_enable = true; return; }

  // --- Current clamp
  if (cmd == "IC1" && hasVal) { applyFloat(IC.enable, IC.current_clamp, v); return; }
  if (cmd == "IC0")           { IC.enable = true; return; }

  // --- Noise
  if (cmd == "NO1" && hasVal) { applyFloat(noise.enable, noise.current, v); return; }
  if (cmd == "NO0")           { noise.enable = true; return; }

  // --- Synapses
  if (cmd == "SG11" && hasVal){ applyFloat(syn1.gain_enable,  syn1.gain,  v, 0.25f); return; }
  if (cmd == "SG10")          { syn1.gain_enable = true; return; }

  if (cmd == "SD11" && hasVal){ applyFloat(syn1.decay_enable, syn1.decay, v, 1.0f/1000.0f); return; }
  if (cmd == "SD10")          { syn1.decay_enable = true; return; }

  if (cmd == "SG21" && hasVal){ applyFloat(syn2.gain_enable,  syn2.gain,  v, 0.25f); return; }
  if (cmd == "SG20")          { syn2.gain_enable = true; return; }

  if (cmd == "SD21" && hasVal){ applyFloat(syn2.decay_enable, syn2.decay, v, 1.0f/1000.0f); return; }
  if (cmd == "SD20")          { syn2.decay_enable = true; return; }

  // --- UI / indicators
  if (cmd == "BZ1") { Buzzer_on();  return; }
  if (cmd == "BZ0") { Buzzer_off(); return; }
  if (cmd == "LED1"){ LED_on();     return; }
  if (cmd == "LED0"){ LED_off();    return; }
  if (cmd == "CON"){ Connected();   return; }

  // Optional: report unknown command back to client (debug)
  // (Keep it short to avoid spamming)
  // ws.broadcastTXT("{\"type\":\"err\",\"msg\":\"Unknown cmd\"}");
}

static inline void handleCommandJson(const String& s) {
  StaticJsonDocument<256> doc;
  auto err = deserializeJson(doc, s);
  if (err) return;

  const char* type = doc["type"] | "";

  // {"type":"stream","enable":true,"decim":5}
  if (!strcmp(type, "stream")) {
    if (doc.containsKey("enable")) wifiStream.enabled = (bool)doc["enable"];
    if (doc.containsKey("decim")) {
      int d = (int)doc["decim"];
      if (d < 1) d = 1;
      if (d > 500) d = 500;
      wifiStream.decim = (uint16_t)d;
    }
    return;
  }

  // {"type":"scmd","cmd":"IC1","v":120.0}
  // {"type":"scmd","cmd":"TR"}        (no value)
  if (!strcmp(type, "scmd")) {
    const char* c = doc["cmd"];
    if (!c) return;
    bool hasVal = doc.containsKey("v");
    float v = hasVal ? (float)doc["v"] : 0.0f;
    dispatchToken(String(c), hasVal, v);
    return;
  }

  // {"type":"ping"} -> {"type":"pong",...}
  if (!strcmp(type, "ping")) {
    StaticJsonDocument<128> out;
    out["type"] = "pong";
    out["ws"] = WS_PORT;
    String resp;
    serializeJson(out, resp);
    ws.broadcastTXT(resp);
    return;
  }
}

static inline void onWsEvent(uint8_t num, WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED: {
      IPAddress ip = WiFi.softAPIP();
      String hello = String("{\"type\":\"hello\",\"ip\":\"") + ip.toString() +
                     String("\",\"ws\":") + WS_PORT +
                     String(",\"proto\":\"SamplePacket16\"}");
      ws.sendTXT(num, hello);
    } break;

    case WStype_TEXT: {
      String msg((char*)payload, length);
      // JSON or fallback "TOKEN value"
      if (msg.length() && msg[0] == '{') {
        handleCommandJson(msg);
      } else {
        // minimal plain-text support: "IC1 120.0"
        int sp = msg.indexOf(' ');
        String c = (sp >= 0) ? msg.substring(0, sp) : msg;
        String rest = (sp >= 0) ? msg.substring(sp + 1) : "";
        rest.trim();
        bool hasVal = rest.length() > 0;
        float v = hasVal ? rest.toFloat() : 0.0f;
        dispatchToken(c, hasVal, v);
      }
    } break;

    default:
      break;
  }
}

static inline void setupWifiAP() {
  WiFi.mode(WIFI_AP);
  WiFi.setSleep(false); // lower latency for streaming
  WiFi.softAP(WIFI_SSID, WIFI_PASS);

  ws.begin();
  ws.onEvent(onWsEvent);

  // Optional heartbeat to keep Android WebSocket stable:
  // ws.enableHeartbeat(15000, 3000, 2);
}

static inline void wifiLoop() {
  ws.loop();
}

static inline void wifiSendSamplePacket(const SamplePacket& p) {
  if (!wifiStream.enabled) return;
  if (++wifiStream.cnt < wifiStream.decim) return;
  wifiStream.cnt = 0;

  if constexpr (!WIFI_SEND_SERIAL_HEADER) {
    ws.broadcastBIN((const uint8_t*)&p, sizeof(p));              // 16 bytes
  } else {
    uint8_t buf[2 + sizeof(SamplePacket)];
    buf[0] = 0xAA; buf[1] = 0x55;
    memcpy(&buf[2], &p, sizeof(p));
    ws.broadcastBIN(buf, sizeof(buf));                           // 18 bytes
  }
}
