#include <Arduino.h>
#include "Rumble.h"

namespace rumble {
static volatile uint16_t left;
static volatile uint8_t duty, importance;
static bool enabled;
#ifdef CHSIM
static uint32_t previous;
static void output(uint8_t) {}
#else
static_assert(PIN_GPIO1 == PC0, "Rumble must use GPIO1 / PC0");
static void output(uint8_t strength) {
    TIM2->CH4CVR = unsigned(strength) * 1000 / 255;
    TIM2->SWEVGR = 1;                 // latch duty now, including an immediate off
    TIM2->INTFR = 0;
}
#endif
void stop() {
#ifndef CHSIM
    TIM2->DMAINTENR = 0;
#endif
    left = duty = importance = 0;
    output(0);
}
void begin() {
#ifndef CHSIM
    RCC->APB2PCENR |= RCC_APB2Periph_AFIO | RCC_APB2Periph_GPIOC;
    RCC->APB1PCENR |= RCC_APB1Periph_TIM2;
    GPIOC->BCR = 1;
    // X035 TIM2 remap is PCFR1[20:18], unlike the generic STM32 macros.
    // Only CH4 is enabled; the other remapped channels never drive their pins.
    AFIO->PCFR1 = (AFIO->PCFR1 & ~(7u << 18)) | (6u << 18);
    GPIOC->CFGLR = (GPIOC->CFGLR & ~15u) | 11u;
    TIM2->CTLR1 = TIM2->CTLR2 = TIM2->SMCFGR = TIM2->DMAINTENR = 0;
    TIM2->CCER = 0;
    TIM2->CHCTLR1 = 0; TIM2->CHCTLR2 = 0x6800; // CH4 PWM1 + preload
    TIM2->PSC = 47; TIM2->ATRLR = 999;          // 48 MHz / 48 / 1000 = 1 kHz
    TIM2->RPTCR = 0; TIM2->CNT = 0;
    TIM2->BDTR = 0x8000;
    TIM2->CCER = 0x1000;
    stop();
    TIM2->CTLR1 = 0x81;
    NVIC_EnableIRQ(TIM2_UP_IRQn);
#else
    previous = millis(); stop();
#endif
    enabled = true;
}
void setEnabled(bool on) { enabled = on; if (!on) stop(); }
void pulse(uint8_t strength, uint16_t ms, uint8_t priority) {
    update();
    if (!enabled || (left && priority < importance)) return;
    if (!strength || !ms) { stop(); return; }
    if (ms > MAX_PULSE_MS) ms = MAX_PULSE_MS;
#ifndef CHSIM
    TIM2->DMAINTENR = 0;
#endif
    importance = priority; duty = strength; left = ms;
    output(strength);
#ifndef CHSIM
    TIM2->DMAINTENR = 1;
#endif
}
void play(Effect effect) {
    static const uint8_t strengths[] = {120, 210, 175, 150, 180, 240, 200};
    static const uint8_t lengths[] = {35, 70, 55, 90, 95, 240, 180};
    unsigned e = unsigned(effect);
    if (e < sizeof strengths) pulse(strengths[e], lengths[e], e >= 5 ? 2 : e ? 1 : 0);
}
void update() {
#ifdef CHSIM
    uint32_t now = millis(), elapsed = now - previous; previous = now;
    if (left) { if (elapsed >= left) stop(); else left -= elapsed; }
#endif
}
uint8_t level() { update(); return duty; }
uint16_t remaining() { update(); return left; }
#ifndef CHSIM
extern "C" void TIM2_UP_IRQHandler() __attribute__((interrupt("WCH-Interrupt-fast")));
extern "C" void TIM2_UP_IRQHandler() {
    TIM2->INTFR = 0;
    if (left && !--left) stop();
}
#endif
}
