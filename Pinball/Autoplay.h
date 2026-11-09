#pragma once
#include <stdint.h>
namespace pinball {
struct Evaluation {
    unsigned frames, coverage, fast, stalled, drought, peak, repeated, nudges;
    unsigned trace; // hash of gameplay state after every frame, excluding RNG
    unsigned spinFrames, spinPeak, spinTrace; // experiment telemetry, Q8 peak
};
Evaluation evaluateBoard(unsigned frames, unsigned seed, unsigned policy,
                         const unsigned char *inputTape=nullptr, bool report=true, int32_t *path=nullptr,
                         void (*onFrame)()=nullptr);
}
