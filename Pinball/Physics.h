#pragma once
#include "Table.h"
#include "Scatter.h"
#include "Spin.h"

namespace pinball {
constexpr int ONE = 256;
constexpr int HEADER_HEIGHT = 24; // decorative space above the physical roof
constexpr int BALL_RADIUS = 1024;  // 8-pixel collision diameter
constexpr int RAMP_ENTRY_SHIFT = 3, RAMP_ENTRY_FRAMES = 1 << RAMP_ENTRY_SHIFT, RAMP_RIDE_FRAMES = 90;
constexpr int SHOOTER_X = 118;
constexpr int MAIN_LEFT = 30, MAIN_RIGHT = 94, MAIN_LENGTH = 23;
constexpr unsigned SHAKE_LEVELS = 3;
inline int flipperTipY(int y, unsigned level) { return y + 10 - level * 22 / 255; }
struct Ball { int32_t x, y, vx, vy; bool active, shooter, launching; uint8_t scoopTicks;
    bool scooped = false; // hooded scoop; saucers keep their held ball visible
    int8_t ramp = -1;
    uint8_t rampTicks = 0;
    uint16_t stillTicks = 0;
    int32_t stillX = 0, stillY = 0; // fixed anchor for the stationary window
#if defined(CHSIM) || PINBALL_SPIN_GRIP
    int32_t spin = 0; // experimental omega*radius, Q16 (see Spin.h)
#endif
};
struct Metrics {
    uint32_t flipperHits, ramps, spinners, drops, kickbacks, saucers, multiballs, laneSets, bankSets, searches;
    uint16_t kinds[KIND_COUNT];
};
enum Bonus : uint8_t { BonusNone, BonusSaucer, BonusKickback, BonusMultiplier,
    BonusDoubleScore, BonusReady, BonusMultiball, BonusBallSave, BonusJackpot, BonusStuck };
constexpr unsigned BONUS_FRAMES = 84;
struct Game {
    Ball balls[3];
    uint32_t score, ticks;
    uint16_t ballSave, modeTicks, comboTicks, nudgeCooldown;
    // nudgeCooldown is the 25-frame (420 ms) progressive shake window.
    uint8_t shakeLevel, shakeTicks;
    int8_t shakeDirection, shakeX, shakeY;
    int16_t camera;
    uint16_t zoom;
    uint8_t zoomTicks, zoomCooldown, zoomBall;
    bool rampCamera;
    uint32_t scorePopValue;
    uint8_t scorePopTicks, scorePopCooldown, scorePopKind;
    uint8_t bonus, bonusTicks, bonusArg, bonusNext, bonusNextArg;
    uint8_t cooldown[MAX_OBJECTS], laneMask, targetMask, multiplier;
    uint8_t elementState[MAX_OBJECTS];
    Metrics metrics;
    uint8_t lives, left, right, tilt, combo, hits;
    uint8_t rubberTicks[2], rubberStrength[2];
    uint8_t shooterFlap; // hinge opening in degrees, 0..80
    bool scattered; // working flag, reset before processing each ball
    bool started, over, paused, launchHeld, stuck;
    uint32_t seed, rng; // replay seed and independent gameplay PRNG state
};
extern Game game;
// Three levels span the previous five-level force/rumble/wobble range.
inline unsigned shakeStrength() { return game.shakeLevel ? game.shakeLevel * 2 - 1 : 0; }
inline unsigned scoreMultiplier() { return game.multiplier * (game.modeTicks ? 2 : 1); }
inline unsigned laneGoal() { return (game.multiplier<5?game.multiplier+1:5) * (game.modeTicks?2:1); }
inline unsigned laneCount() { unsigned m=game.laneMask;return (m&1)+((m>>1)&1)+((m>>2)&1); }
unsigned laneGroups();
extern const char *message;
extern uint8_t messageTicks;
void announce(const char *s, uint8_t ticks = 100);
void celebrate(Bonus kind, uint8_t arg = 0);
void newGame(uint32_t seed = 0); // zero selects the next session seed
// Internal rotation: scales 4 (passive), 8 (eject) and 16 (powered).
void scatterBall(Ball &ball, unsigned scale);
void updateGame(uint8_t held, uint8_t pressed, uint8_t released);
unsigned activeBalls();
void addScore(unsigned points);
void launchBall();
void collideFlipper(Ball &ball, int pivot, int y, int length, bool right, int level, int previous);
void specialHit(Ball &ball);
void placeBall(unsigned index, int x, int y, int vx, int vy);
unsigned root(unsigned n);
}  // namespace pinball
