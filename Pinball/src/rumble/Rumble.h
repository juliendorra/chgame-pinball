#pragma once
#include <stdint.h>

// CHGame Rev0, H1.8: GPIO1 / PC0, TIM2 channel 4 (full remap).
// Independent of TIM1/PB10 audio. Strength is PWM duty, 0–255.
namespace rumble {
enum class Effect : uint8_t { Flipper, Bumper, Sling, Launch, Ramp, Multiball, Drain };
void begin();                         // output starts off
void pulse(uint8_t strength, uint16_t milliseconds, uint8_t priority = 0);
void play(Effect effect);
void stop();
void setEnabled(bool enabled);        // disabling also stops immediately
void update();                       // simulator clock; hardware uses its timer IRQ
uint8_t level();
uint16_t remaining();
constexpr uint16_t MAX_PULSE_MS = 500;
}
