#include "Elements.h"
#include "SpriteData.h"
#include "FlipperData.h"
namespace pinball {
const ElementDefinition ELEMENT_LIBRARY[KIND_COUNT] = {
    {"Rail", "solid rubber rail; damped reflection", "rail"},
    {"Pop bumper", "radial powered rebound and score", "bumper"},
    {"Stand-up target", "lights a bank color on impact", "target"},
    {"Rollover", "combos, lane-set multiplier and ball save", "lane"},
    {"Lock scoop", "capture, power run, multiball, jackpot", "scoop"},
    {"Flipper pair", "tapered moving rubber; timed launch impulse", "flipper"},
    {"Side ramp", "upward entrance; elevated curved transport; return feed", "ramp"},
    {"Spinner", "pass-through rotor; spins score over time", "spinner"},
    {"Drop target", "collapses on impact; no collision while down", "drop_target"},
    {"Kickback", "one-shot outlane rescue; lane set rearms", "kickback"},
    {"One-way gate", "directional flap or bank-controlled lock", "gate"},
    {"Saucer", "timed hold; escalating award; controlled eject", "saucer"},
};
int rubberBend(unsigned ticks, unsigned strength) {
    // Compress, spring outward, then damp back to the resting band.
    static const int8_t wave[18] = {0,0,0,0,-1,-1,0,1,1,2,2,1,0,-1,-2,-3,-3,-2};
    return ticks ? wave[ticks > 18 ? 17 : ticks - 1] * int(strength) / 3 : 0;
}
void rubberPoint(unsigned side, int h, unsigned t, int bend, int &x, int &y) {
    int ax = 88, bx = RUBBER_REFLECT_X-RUBBER_TIP_X;
    int a = 256 - t;
    int cx = (ax + bx) / 2 - bend * 2;
    int cy = h - 64 - bend;
    x = (a * a * ax + 2 * a * int(t) * cx + int(t*t) * bx) >> 16;
    if(!side)x=RUBBER_REFLECT_X-x;
    y = (a * a * (h-75) + 2 * a * int(t) * cy + int(t*t) * (h-53)) >> 16;
}
void rampPoint(const Object &o, unsigned t, int &x, int &y) {
    int a = 256 - t;
    int cx = o.group == 0 ? 12 : o.group == 1 ? 101 : ((o.x + o.u) >> 1);
    int cy = ((o.y + o.v) >> 1) - 20;
    // Board coordinates and the entire curve are nonnegative: an exact Q16
    // shift avoids signed-division correction code on the small MCU.
    x = (a * a * o.x + 2 * a * int(t) * cx + int(t * t) * o.u) >> 16;
    y = (a * a * o.y + 2 * a * int(t) * cy + int(t * t) * o.v) >> 16;
}
int gateDirection(const Object &o) {
    return (o.group == 1) != (o.u < o.x || (o.u == o.x && o.v < o.y)) ? -1 : 1;
}
GuideRail gateArm(const Object &o, unsigned opening) {
    static const uint16_t cs[9] = {256,252,241,222,196,165,128,88,44};
    static const uint8_t sn[9] = {0,44,88,128,165,196,222,241,252};
    unsigned pose = opening > 80 ? 8 : (opening + 5) / 10;
    int dx=o.u-o.x,dy=o.v-o.y,s=int(sn[pose])*gateDirection(o);
    return {o.x,o.y,o.x+(dx*int(cs[pose])+dy*s)/256,o.y+(dy*int(cs[pose])-dx*s)/256};
}
GuideRail shooterFlapArm(unsigned opening) {
    // Hinge on the outer rail; the free end lifts up into the playfield.
    static const Object flap={Gate,0,124,43,111,56,0};
    return gateArm(flap,opening);
}
unsigned flipperGuides(int left, int right, int y, bool main, GuideRail (&rails)[4]) {
    if (main) {
        // Narrow outlanes outside these dividers; return lanes between the
        // dividers and slings feed directly onto the flipper rubber.
        rails[0] = {18, y - 48, 18, y - 15};
        rails[1] = {18, y - 15, left, y};
        rails[2] = {100, y - 48, 100, y - 15};
        rails[3] = {100, y - 15, right, y};
    } else {
        rails[0] = {6, y - 18, left - 10, y - 9};
        rails[1] = {left - 10, y - 9, left, y};
        rails[2] = {112, y - 18, right + 10, y - 9};
        rails[3] = {right + 10, y - 9, right, y};
    }
    return 4;
}
}  // namespace pinball
