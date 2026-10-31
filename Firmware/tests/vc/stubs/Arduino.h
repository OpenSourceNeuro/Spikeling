#pragma once
// Host IO doubles. The actual sketch and vendored SerialCommand parser are compiled.
#include <algorithm>
#include <cctype>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>
using std::isfinite;
using boolean = bool;
using byte = uint8_t;
constexpr int LOW=0, HIGH=1, INPUT=0, OUTPUT=1, INPUT_PULLDOWN=2;
inline uint32_t host_us=0;
inline int host_gpio[64]{};
inline uint32_t micros(){ return host_us; }
inline uint32_t millis(){ return host_us/1000; }
inline void delay(unsigned ms){ host_us+=ms*1000; }
inline void delayMicroseconds(unsigned us){ host_us+=us; }
inline void pinMode(int,int){}
inline int digitalRead(int pin){return host_gpio[pin];}
inline void digitalWrite(int pin,int value){host_gpio[pin]=value;}
inline void ledcWrite(int,int){}
inline bool ledcAttach(int,int,int){return true;}
inline void randomSeed(unsigned){}
inline long random(long max){return max/2;}
inline long random(long min,long max){return min+(max-min)/2;}
template<class T,class L,class H> T constrain(T v,L lo,H hi){return v<lo?T(lo):v>hi?T(hi):v;}
inline long map(long v,long a,long b,long c,long d){return (v-a)*(d-c)/(b-a)+c;}
class Stream {
 public:
  std::string input;
  std::vector<uint8_t> output;
  uint32_t next_write_delay_us=0;
  size_t next_write_limit=static_cast<size_t>(-1);
  size_t tx_capacity=256;
  uint32_t tx_timeout_ms=100, host_pause_until_us=0;
  bool host_paused=false;
  std::vector<uint8_t> pending_usb;
  size_t setTxBufferSize(size_t count){tx_capacity=count;return count;}
  void setTxTimeoutMs(uint32_t timeout){tx_timeout_ms=timeout;}
  void serviceHost(){
    if(host_paused && int32_t(host_us-host_pause_until_us)>=0)host_paused=false;
    if(!host_paused){output.insert(output.end(),pending_usb.begin(),pending_usb.end());pending_usb.clear();}
  }
  int availableForWrite(){serviceHost();return int(tx_capacity-pending_usb.size());}
  void begin(unsigned long){}
  int available(){return int(input.size());}
  int read(){int c=uint8_t(input.front());input.erase(input.begin());return c;}
  size_t write(const uint8_t* data,size_t count){
    host_us+=next_write_delay_us;next_write_delay_us=0;
    count=std::min(count,next_write_limit);next_write_limit=static_cast<size_t>(-1);
    serviceHost();
    if(host_paused){
      if(count>tx_capacity-pending_usb.size()){
        if(!tx_timeout_ms)return 0;
        host_us=host_pause_until_us;serviceHost();
      }else{pending_usb.insert(pending_usb.end(),data,data+count);return count;}
    }
    output.insert(output.end(),data,data+count);return count;
  }
  void print(const char* value){write(reinterpret_cast<const uint8_t*>(value),strlen(value));}
  void print(char value){write(reinterpret_cast<const uint8_t*>(&value),1);}
  template<class T> void print(T value){std::ostringstream s;s<<value;print(s.str().c_str());}
  void print(double value,int digits){std::ostringstream s;s<<std::fixed<<std::setprecision(digits)<<value;print(s.str().c_str());}
  void println(){print('\n');}
  template<class T> void println(T value){print(value);println();}
};
inline Stream Serial;
