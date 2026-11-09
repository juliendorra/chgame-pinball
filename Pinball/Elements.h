#pragma once
#include "Table.h"
namespace pinball {
// hull stores precomputed nonnegative sprite pixel corners. count uses its
// high bit to mirror the shared, width-prefixed collision mask.
struct FlipperPose { const uint8_t *data; const uint8_t *hull; const uint8_t *mask; int8_t ax, ay; uint8_t count, height; };
extern const FlipperPose FLIPPER_POSES[2][9];
constexpr int RUBBER_TIP_X=45, RUBBER_REFLECT_X=118;
// Exact for every supported 0..255 stroke level; avoid division in the hot path.
inline unsigned flipperPoseIndex(unsigned level) { return (level + 16) >> 5; }
void rubberPoint(unsigned side, int height, unsigned t, int bend, int &x, int &y);
int rubberBend(unsigned ticks, unsigned strength);
// Geometry shared by the ramp renderer, ball transport and board preview.
void rampPoint(const Object &ramp, unsigned t, int &x, int &y);
struct GuideRail { int x, y, u, v; };
// One hinged arm geometry for both visible hardware and ball contact.
GuideRail gateArm(const Object &gate, unsigned opening);
GuideRail shooterFlapArm(unsigned opening);
int gateDirection(const Object &gate);
// Shared by collision and drawing, so a visible pivot protector is solid.
unsigned flipperGuides(int left, int right, int y, bool main, GuideRail (&rails)[4]);
struct ElementDefinition { const char *name; const char *behavior; const char *sprite; };
extern const ElementDefinition ELEMENT_LIBRARY[KIND_COUNT];
}  // namespace pinball
