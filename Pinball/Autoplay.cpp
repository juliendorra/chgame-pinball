#include <CHGame.h>
#include "Physics.h"
#include "Autoplay.h"

#ifdef CHSIM
namespace pinball {
static void number(const char *label, uint32_t value) {
    char buf[16]; dbg::print(label); fmtInt(buf, value); dbg::print(buf);
}
static bool wantFlipper(const Ball &b, int pivot, int y, int length, bool right, int timing) {
    if (!b.active || b.shooter || b.ramp >= 0 || b.scoopTicks || b.vy < -64) return false;
    int x = b.x / ONE;
    int reach = right ? pivot - x : x - pivot;
    if (reach < -3 || reach > length + 4) return false;
    int predicted = b.y / ONE + b.vy * 3 / (2 * ONE);
    return predicted >= y - 8 + timing && b.y / ONE <= y + 10;
}
Evaluation evaluateBoard(unsigned limit, unsigned seed, unsigned policy, const unsigned char *inputTape, bool report, int32_t *path, void (*onFrame)()) {
    newGame(seed?seed:1);
    uint32_t cells[3] = {}, age[3] = {};
    int32_t previousX[3] = {}, previousY[3] = {};
    unsigned frames = 0, fast = 0, stalls = 0, drought = 0, sinceScore = 0, peak = 0;
    unsigned sinceNew = 0, repeated = 0, nudges = 0;
    unsigned launchWait = 0;
    uint8_t previous = 0, randomButtons = 0;
    uint32_t trace = 2166136261u;
    uint32_t spinTrace=2166136261u;unsigned spinFrames=0,spinPeak=0;
    uint32_t rng = seed ^ 0xB07B07u; // separate bot-input and physics streams
    if(!rng)rng=1;
    for (; frames < limit && !game.over; ++frames) {
        uint8_t held = 0;
        bool shooter = false;
        for (const Ball &b : game.balls) shooter |= b.active && b.shooter;
        if (shooter) {
            if (++launchWait < 2 + seed % 12) held = A_BUTTON;
        } else if (policy == 1) {
            launchWait = 0;
            if (frames % 11 == 0) {
                rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5;
                randomButtons = (rng & 1 ? LEFT_BUTTON : 0) | (rng & 2 ? B_BUTTON : 0);
            }
            held = randomButtons;
        } else if (policy == 2) {
            launchWait = 0;
            for (const Ball &b : game.balls) {
                int timing = int(seed % 9) - 4;
                bool left = wantFlipper(b, MAIN_LEFT, table.h.height - 25, MAIN_LENGTH, false, timing);
                bool right = wantFlipper(b, MAIN_RIGHT, table.h.height - 25, MAIN_LENGTH, true, timing);
                for (unsigned i = 0; i < table.h.count; ++i) {
                    const Object &o = table.objects[i];
                    if (o.kind == Flippers) {
                        left |= wantFlipper(b, o.x, o.y, o.v, false, timing);
                        right |= wantFlipper(b, o.u, o.y, o.v, true, timing);
                    }
                }
                if (left) held |= LEFT_BUTTON;
                if (right) held |= B_BUTTON;
            }
            for (unsigned i = 0; i < 3; ++i) if (age[i] > 60 && !game.nudgeCooldown) {
                held = game.balls[i].x < 60*ONE ? A_BUTTON : RIGHT_BUTTON; ++nudges; break;
            }
        }
        if(inputTape)held=inputTape[frames];
        uint32_t oldScore = game.score;
        updateGame(held, held & ~previous, previous & ~held);
        if(onFrame)onFrame();
        previous = held;
        auto hash=[&](uint32_t v){trace=(trace^v)*16777619u;};
        hash(game.score);hash(game.lives);hash(game.left);hash(game.right);hash(game.tilt);
        for(const Ball &b:game.balls) {
            spinTrace=(spinTrace^uint32_t(b.spin))*16777619u;
            if(b.active && !b.shooter) {
                unsigned magnitude=(b.spin<0?-b.spin:b.spin)/256;
                spinFrames+=magnitude!=0;if(magnitude>spinPeak)spinPeak=magnitude;
            }
            hash(b.x);hash(b.y);hash(b.vx);hash(b.vy);hash(b.active);
            hash(b.shooter);hash(b.launching);hash(b.ramp);hash(b.scoopTicks);
        }
        if(path && frames%60==0) {
            const Ball &b=game.balls[0];unsigned at=frames/60*3;
            path[at]=b.x;path[at+1]=b.y;path[at+2]=b.active&&!b.shooter;
        }
        if (game.score != oldScore) sinceScore = 0;
        else if (++sinceScore > 600) ++drought;
        for (unsigned i = 0; i < 3; ++i) {
            const Ball &b = game.balls[i];
            if (!b.active || b.shooter) { age[i] = 0; continue; }
            int x = b.x / ONE, y = b.y / ONE;
            if (!b.launching) {
                int row = y * 12 / table.h.height, col = x / 16;
                if (row < 0) row = 0; if (row > 11) row = 11;
                if (col < 0) col = 0; if (col > 7) col = 7;
                unsigned cell = row * 8 + col;
                if (!(cells[cell / 32] & (1u << (cell % 32)))) sinceNew = 0;
                cells[cell / 32] |= 1u << (cell % 32);
            }
            int dx = b.x - previousX[i], dy = b.y - previousY[i];
            unsigned distance = (dx < -16 * ONE || dx > 16 * ONE || dy < -16 * ONE || dy > 16 * ONE) ?
                16 * ONE + 1 : root(dx * dx + dy * dy);
            if (frames && distance > peak && distance < 16 * ONE) peak = distance;
            if (frames && distance > 6 * ONE && distance < 16 * ONE) ++fast;
            if (!b.scoopTicks && b.ramp < 0 && distance < 24) { if (++age[i] > 180) ++stalls; }
            else age[i] = 0;
            previousX[i] = b.x; previousY[i] = b.y;
        }
        if (++sinceNew > 1200) ++repeated;
    }
    unsigned coverage = 0, types = 0;
    for (uint32_t bits : cells) while (bits) { coverage += bits & 1; bits >>= 1; }
    for (unsigned i = 0; i < KIND_COUNT; ++i) if (game.metrics.kinds[i]) ++types;
    if(report) {
        number("EVAL frames=", frames); number(" score=", game.score); number(" lives=", game.lives);
        number(" over=", game.over); number(" coverage=", coverage); number(" types=", types);
        number(" fast=", fast); number(" stalled=", stalls); number(" drought=", drought); number(" peak_q8=", peak);
        number(" repeated=", repeated);
        number(" nudges=", nudges);
        number(" flips=", game.metrics.flipperHits); number(" ramps=", game.metrics.ramps);
        number(" spinners=", game.metrics.spinners); number(" drops=", game.metrics.drops);
        number(" kickbacks=", game.metrics.kickbacks); number(" saucers=", game.metrics.saucers);
        number(" multiballs=", game.metrics.multiballs); number(" lane_sets=", game.metrics.laneSets);
        number(" bank_sets=", game.metrics.bankSets); number(" searches=", game.metrics.searches); dbg::print("\n");
    }
    return {frames,coverage,fast,stalls,drought,peak,repeated,nudges,trace,spinFrames,spinPeak,spinTrace};
}
}  // namespace pinball
#endif
