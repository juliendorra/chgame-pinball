#include <CHGame.h>
#include <Fat.h>
#include <string.h>
#include "Physics.h"
#include "Elements.h"
#include "src/rumble/Rumble.h"

namespace pinball {
#if defined(CHSIM) || CHGAME_DEBUG
#define METRIC(field) (++game.metrics.field)
#else
// Evaluation counters are observed only by host/debug diagnostics.
#define METRIC(field) ((void)0)
#endif
Game game;
const char *message = "";
uint8_t messageTicks;
static const int RADIUS = BALL_RADIUS;
static int clamp(int n, int lo, int hi) { return n < lo ? lo : n > hi ? hi : n; }
static void clearSpin(Ball &b) {
#if defined(CHSIM) || PINBALL_SPIN_GRIP
    b.spin=0;
#endif
}
static void contactSpin(Ball &b,int nx,int ny,int impulse,int surfaceY=0) {
#if PINBALL_SPIN_GRIP
    // Ablation keeps contact friction but discards its history before a hit.
    if(PINBALL_SPIN_FORGET)b.spin=0;
    spinContact(b.vx,b.vy,b.spin,nx,ny,impulse,PINBALL_SPIN_GRIP,0,surfaceY);
#endif
}
unsigned root(unsigned n) {
    unsigned r = 0, bit = 1u << 30;
    while (bit > n) bit >>= 2;
    while (bit) {
        if (n >= r + bit) { n -= r + bit; r = (r >> 1) + bit; }
        else r >>= 1;
        bit >>= 2;
    }
    return r;
}
void announce(const char *s, uint8_t ticks) { message = s; messageTicks = ticks; }
void celebrate(Bonus kind,uint8_t arg) {
    if(game.tilt>=3 || kind==BonusNone)return;
    if(game.bonusTicks && kind<game.bonus) {
        if(kind>=game.bonusNext){game.bonusNext=kind;game.bonusNextArg=arg;}
        return;
    }
    game.bonus=kind;game.bonusArg=arg;game.bonusTicks=BONUS_FRAMES;
    game.bonusNext=BonusNone;
}
unsigned activeBalls() {
    unsigned n = 0;
    for (const Ball &b : game.balls) if (b.active) ++n;
    return n;
}
unsigned laneGroups() {
    unsigned groups=0;
    for(unsigned i=0;i<table.h.count;++i)if(table.objects[i].kind==Lane)groups|=1u<<table.objects[i].group;
    return groups;
}
void addScore(unsigned points) {
    if (game.tilt >= 3) return;
    unsigned before = game.score;
    const unsigned total = points * scoreMultiplier();
    game.score = game.score > 99999999u - total ? 99999999u : game.score + total;
    if (game.score == before || game.scorePopCooldown) return;
    static const uint32_t milestones[] = {1000, 5000, 10000, 25000, 50000, 100000,
        250000, 500000, 1000000, 2500000, 5000000, 10000000, 25000000, 50000000, 99999999};
    static const uint32_t lucky[] = {7777, 8888, 11111, 12345, 22222, 33333, 44444,
        54321, 55555, 66666, 77777, 88888, 99999, 123456, 654321, 777777};
    uint32_t crossed = 0; uint8_t kind = 0;
    for (uint32_t n : milestones) if (before < n && game.score >= n) { crossed = n; kind = 1; }
    for (uint32_t n : lucky) if (before < n && game.score >= n && n > crossed) { crossed = n; kind = 2; }
    if (crossed) {
        game.scorePopValue = crossed; game.scorePopKind = kind;
        game.scorePopTicks = 36; game.scorePopCooldown = 120;
    }
}
void placeBall(unsigned i, int x, int y, int vx, int vy) {
    if (i >= 3) return;
    game.balls[i] = {x * ONE, y * ONE, vx, vy, true, false, false, 0};
}
static void serve() {
    memset(game.elementState, 0, sizeof game.elementState);
    game.balls[0] = {SHOOTER_X * ONE, (table.h.height - 22) * ONE, 0, 0, true, true, true, 0};
    game.camera = table.h.height - 108;
    game.launchHeld = false;
    announce("A / DOWN TO LAUNCH", 180);
}
void newGame(uint32_t seed) {
    if(!seed)seed=game.rng+table.h.id+0x9E3779B9u;
    rumble::stop();
    memset(&game, 0, sizeof game);
    game.seed=game.rng=seed?seed:1;
    game.multiplier = 1;
    game.lives = 3;
    game.zoom = ONE;
    game.started = true;
    serve();
}
void scatterBall(Ball &b, unsigned scale) {
    if(game.scattered)return;
    game.scattered=true;
    uint32_t r=game.rng;r^=r<<13;r^=r>>17;r^=r<<5;game.rng=r;
    // Symmetric triangular distribution: small angles are most likely.
    int s=(int(r&31)-int((r>>5)&31))*int(scale);
#if defined(PINBALL_SCATTER_ANGLE_ZERO) && PINBALL_SCATTER_ANGLE_ZERO
    s=0; // benchmark control: retain conservative cosine, remove angular scatter
#endif
    // Q14 rotation, rounded slightly inward so scatter never adds energy.
    int c=16384-int(scale/2),x=b.vx,y=b.vy;
    b.vx=(x*c-y*s)/16384;b.vy=(y*c+x*s)/16384;
}
void specialHit(Ball &ball) {
    if (game.zoomCooldown) return;
    game.zoomBall = &ball - game.balls;
    game.zoomTicks = 44;
    game.zoomCooldown = 90;
}
void launchBall() {
    for (Ball &b : game.balls) if (b.active && b.shooter) {
        b.shooter = false;
        b.launching = true;
        b.vy = -2800;
        b.vx = 0;
        clearSpin(b);
        game.ballSave = 480;
        celebrate(BonusBallSave,8);
        if(laneGroups()==7)celebrate(BonusMultiplier,128);
        audio::blip(900, 70, true);
        rumble::play(rumble::Effect::Launch);
        return;
    }
}

// Two quarter-time steps per frame give half-speed motion at 60 Hz. Gravity
// and impulses use the same physical clock; rubber loses normal energy on
// impact, so passive rebounds cannot send the ball through several screens.
static bool contact(Ball &b, int px, int py, int radius, int kick = 0) {
    int dx = b.x - px, dy = b.y - py;
    if (dx <= -radius || dx >= radius || dy <= -radius || dy >= radius) return false;
    unsigned d2 = dx * dx + dy * dy;
    if (d2 >= unsigned(radius * radius)) return false;
    int dist = root(d2);
    int nx = dist ? dx * ONE / dist : 0, ny = dist ? dy * ONE / dist : -ONE;
    b.x = px + nx * (radius + 16) / ONE;
    b.y = py + ny * (radius + 16) / ONE;
    int dot = (b.vx * nx + b.vy * ny) / ONE;
    if (dot < 0) {
        // A lightweight hinged flap yields while retaining exact contact.
        // Negative kick resolves penetration without reflecting the ball.
        if (kick < 0) return true;
        int impulse = -dot * 384 / ONE + kick;  // restitution 0.5, formerly 0.875
        b.vx += impulse * nx / ONE;
        b.vy += impulse * ny / ONE;
        contactSpin(b,nx,ny,impulse);
        if(dot < -ONE)scatterBall(b,kick?SCATTER_POWERED:SCATTER_PASSIVE);
        return true;
    }
    return false;
}
static bool segment(Ball &b, int ax, int ay, int bx, int by, int radius = RADIUS + ONE, int kick = 0) {
    int margin = (radius + 255) / ONE + 1;
    if (b.x / ONE < (ax < bx ? ax : bx) - margin || b.x / ONE > (ax > bx ? ax : bx) + margin ||
        b.y / ONE < (ay < by ? ay : by) - margin || b.y / ONE > (ay > by ? ay : by) + margin) return false;
    int dx = bx - ax, dy = by - ay, length = dx * dx + dy * dy;
    if (!length) return false;
    int dot = (b.x - ax * ONE) * dx + (b.y - ay * ONE) * dy;
    int t = clamp(dot * 16 / length, 0, 4096);
    return contact(b, ax * ONE + dx * t / 16, ay * ONE + dy * t / 16, radius, kick);
}
// Exact distance to the opaque, scaled pixel spans. Shadows are absent
// from these generated bounds; all upper-bat sizes use the same rounding
// and anchor as sprite4. Treat each row as its visible filled rectangle.
static unsigned artDistance(int x,int y,const FlipperPose &pose,int scale,int left,int top,int &px,int &py) {
    unsigned nearest=0xFFFFFFFFu;
    const uint8_t *data=pose.mask;unsigned width=*data++;
    bool mirror=pose.count&128;
    for(unsigned row=0;row<pose.height;++row) {
        if(*data==255){++data;continue;}
        const uint8_t *first=data,*last=data;
        while(!(last[1]&128))last+=2;
        data=last+2;
        int y0=top+(row*scale/ONE)*ONE-ONE/2,y1=top+((row+1)*scale/ONE)*ONE-ONE/2;
        // Read the mirrored row backwards, preserving the original left-to-
        // right tie order as well as the exact sprite scaling of both edges.
        for(const uint8_t *p=mirror?last:first;;p+=mirror?-2:2) {
            unsigned a=p[0],b=p[1]&127;
            if(mirror){unsigned lo=width-b;b=width-a;a=lo;}
            if(y0!=y1) {
                int x0=left+(a*scale/ONE)*ONE-ONE/2,x1=left+(b*scale/ONE)*ONE-ONE/2;
                if(x0!=x1){
                    int xx=clamp(x,x0,x1),yy=clamp(y,y0,y1),dx=x-xx,dy=y-yy;
                    unsigned d=dx*dx+dy*dy;if(d<nearest){nearest=d;px=xx;py=yy;}
                }
            }
            if(p==(mirror?first:last))break;
        }
    }
    return nearest;
}
static bool poseContact(Ball &b, const FlipperPose &pose, int pivot, int y, int length, int &normalY, int surfaceY) {
    int scale=length*ONE/23;
    int left=(pivot-pose.ax*scale/ONE)*ONE,top=(y-pose.ay*scale/ONE)*ONE;
    if(b.x<left-RADIUS||b.x>left+pose.data[0]*scale+RADIUS||
       b.y<top-RADIUS||b.y>top+pose.data[1]*scale+RADIUS)return false;
    int px=0,py=0;
    unsigned nearest=artDistance(b.x,b.y,pose,scale,left,top,px,py);
    if(nearest>=unsigned(RADIUS*RADIUS))return false;
    if(!nearest) {
        // A moving bat can cover a ball center. The art-derived hull gives
        // an escape direction; a short search finds the actual pixel face.
        unsigned closest=0xFFFFFFFFu;int nx=0,ny=-ONE;
        for(unsigned i=0;i<(pose.count&127);++i) {
            unsigned j=(i+1)%(pose.count&127);
            int ax=left+(pose.hull[i*2]*unsigned(scale)/ONE)*ONE-ONE/2;
            int ay=top+(pose.hull[i*2+1]*unsigned(scale)/ONE)*ONE-ONE/2;
            int bx=left+(pose.hull[j*2]*unsigned(scale)/ONE)*ONE-ONE/2;
            int by=top+(pose.hull[j*2+1]*unsigned(scale)/ONE)*ONE-ONE/2;
            int dx=bx-ax,dy=by-ay,len2=dx*dx+dy*dy;if(!len2)continue;
            int dot=(b.x-ax)*dx+(b.y-ay)*dy;
            int t=dot<=0?0:dot>=len2?ONE:((dot>>4)*ONE)/(len2>>4);
            int xx=ax+dx*t/ONE,yy=ay+dy*t/ONE,ex=xx-b.x,ey=yy-b.y;
            unsigned d=ex*ex+ey*ey;
            if(d<closest){closest=d;int edge=root(len2);nx=dy*ONE/edge;ny=-dx*ONE/edge;}
        }
        int lo=0,hi=24*ONE;
        for(unsigned i=0;i<10;++i) {
            int mid=(lo+hi)/2;
            unsigned d=artDistance(b.x+nx*mid/ONE,b.y+ny*mid/ONE,pose,scale,left,top,px,py);
            if(d<unsigned((RADIUS+16)*(RADIUS+16)))lo=mid;else hi=mid;
        }
        b.x+=nx*hi/ONE;b.y+=ny*hi/ONE;
        nearest=artDistance(b.x,b.y,pose,scale,left,top,px,py);
    }
    int nx=0,ny=0;
    // A rounded ball pushed off one pixel corner can meet its neighboring
    // stair step. Recheck the complete visible mask before accepting the pose.
    for(unsigned correction=0;correction<4;++correction) {
        int distance=root(nearest);if(!distance)return false;
        nx=(b.x-px)*ONE/distance;ny=(b.y-py)*ONE/distance;
        b.x=px+nx*(RADIUS+16)/ONE;b.y=py+ny*(RADIUS+16)/ONE;
        nearest=artDistance(b.x,b.y,pose,scale,left,top,px,py);
        if(nearest>=unsigned(RADIUS*RADIUS))break;
    }
    int dot=(b.vx*nx+b.vy*ny)/ONE;
    if(dot<0){
        int impulse=-dot*384/ONE;
        b.vx+=impulse*nx/ONE;b.vy+=impulse*ny/ONE;
        contactSpin(b,nx,ny,impulse,surfaceY);
    }
    normalY=ny;return true;
}
void collideFlipper(Ball &b, int pivot, int y, int length, bool right, int level, int previous) {
    unsigned current = flipperPoseIndex(level), old = flipperPoseIndex(previous);
    // Visit each crossed silhouette during a fast stroke, then resolve the
    // final visible pose. A fast bat cannot jump through a stationary ball.
    unsigned start = current > old ? old + 1 : current;
    bool struck = false;
    // Contact-point vertical bat speed in the solver's half-frame clock.
    // The existing arcade normal launch remains unchanged.
    int reach=clamp((b.x/ONE-pivot)*(right?-1:1),0,length);
    int surfaceY=(flipperTipY(y,level)-flipperTipY(y,previous))*ONE*2*reach/length;
    for (unsigned pose = start; pose <= current; ++pose) {
        int ny = 0;
        if (poseContact(b, FLIPPER_POSES[right][pose], pivot, y, length, ny, surfaceY) && ny < -40) struck = true;
    }
    if (struck && level > previous) {
        METRIC(flipperHits);
        rumble::play(rumble::Effect::Flipper);
        int progress = right ? pivot * ONE - b.x : b.x - pivot * ONE;
        int t = clamp(progress / length, 0, ONE);
        int power = -(1250 + t * 2);
        if (b.vy > power) b.vy = power;
        b.vx = b.vx / 3 + (right ? -1 : 1) * (150 + t * 3);
    }
}
static __attribute__((noinline)) void flippers(Ball &b, int left, int right, int y, int length, int previousLeft, int previousRight) {
    GuideRail guides[4];
    unsigned n = flipperGuides(left, right, y, y == table.h.height - 25, guides);
    for (unsigned i = 0; i < n; ++i) segment(b, guides[i].x, guides[i].y, guides[i].u, guides[i].v);
    collideFlipper(b, left, y, length, false, game.left, previousLeft);
    collideFlipper(b, right, y, length, true, game.right, previousRight);
}
static __attribute__((noinline)) void bounds(Ball &b) {
    const int h = table.h.height;
    // Gutters stay open past the pivot. The former inward apron diagonal
    // made a narrowing V against the right bat, trapping an eight-pixel ball.
    segment(b, 6, 28, 6, h + 6);
    segment(b, 6, 28, 23, 8);
    segment(b, 23, 8, 98, 8);
    segment(b, 98, 8, 124, 32);
    segment(b, 124, 32, 124, h - 8);
    segment(b, 112, 58, 112, h + 6);
    for (unsigned side = 0; side < 2; ++side) {
        int bend = rubberBend(game.rubberTicks[side], game.rubberStrength[side]);
        int x=side?88:30, y=h-75;
        bool hit = false;
        int speed = (b.vx < 0 ? -b.vx : b.vx) + (b.vy < 0 ? -b.vy : b.vy);
        for (unsigned t = bend?64:256; t <= 256; t += 64) {
            int u, v; rubberPoint(side, h, t, bend, u, v);
            hit |= segment(b, x, y, u, v, RADIUS + ONE, game.tilt >= 3 || game.rubberTicks[side] > 10 ? 0 : 170);
            x = u; y = v;
        }
        if (hit && game.rubberTicks[side] <= 10) {
            game.rubberTicks[side] = 18;
            game.rubberStrength[side] = speed > 700 ? 3 : 2;
            audio::blip(side ? 1050 : 900, 12, true);
            rumble::play(rumble::Effect::Sling);
        }
    }
    segment(b, 30, h - 75, 30, h - 48);
    segment(b, 30, h - 48, RUBBER_TIP_X, h - 53);
    segment(b, 88, h - 75, 88, h - 48);
    segment(b, 88, h - 48, RUBBER_REFLECT_X-RUBBER_TIP_X, h - 53);
    if (b.launching) {
        if (b.y < 58 * ONE && b.vy < 0) b.vx = -800;
        if (b.x < 108 * ONE) b.launching = false;
    } else {
        // A return contact seats the flap against its stop, even if another
        // ball has just opened it. Contact and drawing share the same arm.
        if(b.x>103*ONE && b.y>35*ONE && b.y<74*ONE && b.vx+b.vy>0)game.shooterFlap=0;
        GuideRail flap=shooterFlapArm(game.shooterFlap);
        segment(b,flap.x,flap.y,flap.u,flap.v);
        if (b.x > 112 * ONE && b.y > 52 * ONE) {
            b.x = 107 * ONE; if (b.vx > 0) b.vx = -b.vx / 2;
        }
    }
    if (b.y < RADIUS + 9 * ONE) { b.y = RADIUS + 9 * ONE; if (b.vy < 0) b.vy = -b.vy / 2; }
}
static void multiball(Ball &source) {
    METRIC(multiballs);
    game.targetMask = 0;
    game.modeTicks = 1800;
    game.ballSave = 600;
    celebrate(BonusBallSave,10);
    celebrate(BonusMultiball);
    for (unsigned i = 0; i < table.h.count; ++i)
        if (table.objects[i].kind == DropTarget) game.elementState[i] = 0;
    int direction = 1;
    for (Ball &b : game.balls) if (!b.active) {
        b = {source.x, source.y + 10 * ONE, direction * 400, 550, true, false, false, 0};
        direction = -direction;
    }
    specialHit(source);
    announce(table.h.theme == 8 ? "TREASURE MULTIBALL!" : "REACTOR MULTIBALL!", 150);
    audio::blip(2100, 150, true);
    rumble::play(rumble::Effect::Multiball);
}
static __attribute__((noinline)) void objects(Ball &b, int previousLeft, int previousRight) {
    for (unsigned i = 0; i < table.h.count; ++i) {
        const Object &o = table.objects[i];
        if (o.kind == Wall) { segment(b, o.x, o.y, o.u, o.v); continue; }
        if (o.kind == Gate) {
            GuideRail arm=gateArm(o,game.elementState[i]);
            contact(b,o.x*ONE,o.y*ONE,RADIUS+3*ONE);
            contact(b,o.u*ONE,o.v*ONE,RADIUS+ONE);
            bool push=o.group<2 && (b.vx*(o.v-o.y)-b.vy*(o.u-o.x))*gateDirection(o)>0;
            if(segment(b,arm.x,arm.y,arm.u,arm.v,RADIUS+2*ONE,push?-1:0) && push)game.cooldown[i]=18;
            continue;
        }
        if (o.kind == Flippers) { flippers(b, o.x, o.u, o.y, o.v, previousLeft, previousRight); continue; }
        bool hit = false;
        if (o.kind == Ramp) {
            // Meet the lower lip with the ball's leading edge, before the
            // opaque deck can cover it. The whole ball must fit the mouth.
            hit = b.vy < -100 && unsigned(b.x-o.x*ONE+4*ONE) <= 8*ONE &&
                unsigned(b.y-o.y*ONE) <= 8*ONE+RADIUS;
        } else {
            int extent = o.u + 6;
            // Reuse board-space offsets for both broad phase and radial triggers.
            int dx = (b.x >> 8) - o.x, dy = (b.y >> 8) - o.y;
            if (unsigned(dx+extent)>unsigned(extent*2) || unsigned(dy+extent)>unsigned(extent*2)) continue;
            if (o.kind == Bumper) hit = contact(b, o.x * ONE, o.y * ONE, o.u * ONE + RADIUS + ONE / 2,
                                              game.tilt >= 3 || game.cooldown[i] ? 0 : o.v);
            if (o.kind == Target || (o.kind == DropTarget && !game.elementState[i])) hit = segment(b, o.x - o.u / 2, o.y, o.x + o.u / 2, o.y,
                                               RADIUS + o.v * 64, game.tilt >= 3 || game.cooldown[i] ? 0 : 100);
            if (o.kind == Lane || o.kind == Scoop || o.kind == Saucer || o.kind == Kickback || o.kind == Spinner) {
                int radius = o.kind == Spinner ? 7 : o.u;
                hit = dx * dx + dy * dy < radius * radius;
                if(o.kind == Scoop) {
                    // The hood has a solid back and shoulders. Only an upward
                    // shot through its lower mouth can fall beneath the board.
                    if(dy < 0 || abs(dx) >= o.u-2) {
                        contact(b,o.x*ONE,o.y*ONE,(o.u*ONE)+RADIUS);
                        hit=false;
                    } else if(b.vy >= 0) hit=false;
                }
                if (o.kind == Kickback && game.elementState[i]) hit = false;
            }
        }
        if (!hit || game.cooldown[i] || (game.tilt >= 3 && o.kind != Ramp)) continue;
        game.cooldown[i] = o.kind == Target ? 35 : o.kind == Scoop ? 240 : 18;
#if defined(CHSIM) || CHGAME_DEBUG
        ++game.hits;
#endif
        METRIC(kinds[o.kind]);
        addScore(o.value);
        if (o.kind == Bumper) { audio::blip(1200 + o.group * 280, 24, true); rumble::play(rumble::Effect::Bumper); }
        if (o.kind == Ramp) {
            b.ramp = i; b.rampTicks = 0;
            // First roll from this exact contact position through the throat.
            // These are per-frame entry increments during scripted transport.
            b.vx = (o.x*ONE-b.x)>>RAMP_ENTRY_SHIFT; b.vy = (o.y*ONE-b.y)>>RAMP_ENTRY_SHIFT;
            clearSpin(b); // scripted transport does not simulate rolling
            game.cooldown[i] = 150; METRIC(ramps);
            rumble::play(rumble::Effect::Ramp);
            if(game.tilt < 3) {announce("RAMP SHOT!", 90); specialHit(b);} return;
        }
        if (o.kind == Spinner) {
            game.elementState[i] = 72;
            game.cooldown[i] = 12; METRIC(spinners);
            b.vx = b.vx * 7 / 8;
        }
        if (o.kind == Kickback) {
            game.elementState[i] = 1; game.cooldown[i] = 50;
            b.vx = o.x < 60 ? 380 : -380; b.vy = -1100;
            scatterBall(b,SCATTER_EJECT);
            METRIC(kickbacks); announce("KICKBACK SAVE", 70);
            celebrate(BonusKickback);
        }
        if (o.kind == Target || o.kind == DropTarget) {
            if (o.kind == DropTarget) { game.elementState[i] = 1; METRIC(drops); }
            bool newlyComplete = game.targetMask != 7 && (game.targetMask | (1u << o.group)) == 7;
            game.targetMask |= 1u << o.group;
            if (newlyComplete) { specialHit(b); METRIC(bankSets); celebrate(BonusReady); }
            announce(game.targetMask == 7 ? (table.h.theme == 8 ? "CANNON READY: HIT SCOOP" : "REACTOR READY: HIT SCOOP") :
                     (table.h.theme == 8 ? "TREASURE BANK LIT" : "POWER BANK LIT"), 65);
            audio::blip(1600 + o.group * 200, 30, true);
        }
        if (o.kind == Lane) {
            bool newLane=!(game.laneMask&(1u<<o.group));
            game.laneMask |= 1u << o.group;
            if (game.comboTicks) { if (game.combo < 9) ++game.combo; addScore(500 * game.combo); }
            else game.combo = 1;
            game.comboTicks = 180;
            if (game.laneMask == 7) {
                game.laneMask = 0;
                if (game.multiplier < 5) ++game.multiplier;
                game.ballSave = 360;
                celebrate(BonusBallSave,6);
                celebrate(BonusMultiplier,scoreMultiplier());
                METRIC(laneSets);
                for (unsigned k = 0; k < table.h.count; ++k)
                    if (table.objects[k].kind == Kickback) game.elementState[k] = 0;
                specialHit(b);
                announce("LANES LIT: BONUS UP!");
            } else {
                if(newLane && laneGroups()==7)celebrate(BonusMultiplier,128|game.laneMask);
                announce("LANE COMBO",45);
            }
            audio::blip(1900, 35, true);
        }
        if (o.kind == Scoop) {
            specialHit(b);
            if (game.targetMask == 7 && activeBalls() == 1) multiball(b);
            else if (game.modeTicks && activeBalls() > 1) { addScore(10000); announce("SUPER JACKPOT!"); celebrate(BonusJackpot); }
            else {
                // Refreshing the active window is not a newly earned mode.
                if(!game.modeTicks) {
                    announce(table.h.theme == 8 ? "BROADSIDE: DOUBLE SCORE" : "POWER RUN: DOUBLE SCORE");
                    celebrate(BonusDoubleScore);
                }
                game.modeTicks = 600;
            }
            b.vy = 800;
            b.scoopTicks = 30;
            b.scooped = true;
        } else if (o.kind == Saucer) {
            METRIC(saucers);
            game.elementState[i] = (game.elementState[i] + 1) % 3;
            addScore(o.value * game.elementState[i]);
            b.vy = 700;
            b.scoopTicks = 60; game.cooldown[i] = 240;
            b.scooped = false;
            if (!game.elementState[i]) {game.ballSave = 240;celebrate(BonusBallSave,4);}
            else celebrate(BonusSaucer);
            announce("SAUCER BONUS", 80); specialHit(b);
        } else continue;
        b.x = o.x * ONE; b.y = o.y * ONE;
        clearSpin(b); // held cup settles the ball before its scripted eject
        b.vx = o.x < 60 ? 600 : -600;
        scatterBall(b,SCATTER_EJECT);
    }
}
void updateGame(uint8_t held, uint8_t pressed, uint8_t released) {
    if (game.over || game.paused) return;
    ++game.ticks;
    bool exiting=false;
    for(const Ball &b:game.balls)
        if(b.active && !b.shooter && b.launching && b.y<76*ONE)exiting=true;
    game.shooterFlap=clamp(game.shooterFlap+(exiting?20:-4),0,80);
    if (game.scorePopTicks) --game.scorePopTicks;
    for (unsigned i = 0; i < 2; ++i) if (game.rubberTicks[i]) --game.rubberTicks[i];
    if (game.scorePopCooldown) --game.scorePopCooldown;
    if (game.zoomTicks) --game.zoomTicks;
    if (game.zoomCooldown) --game.zoomCooldown;
    if (messageTicks) --messageTicks;
    if(game.bonusTicks && !--game.bonusTicks) {
        game.bonus=game.bonusNext;game.bonusArg=game.bonusNextArg;game.bonusNext=BonusNone;
        if(game.bonus)game.bonusTicks=BONUS_FRAMES;
    }
    if (game.ballSave) --game.ballSave;
    if (game.modeTicks) --game.modeTicks;
    if (game.comboTicks) --game.comboTicks;
    if (game.nudgeCooldown) --game.nudgeCooldown;

    for (unsigned i = 0; i < table.h.count; ++i) {
        if (game.cooldown[i]) --game.cooldown[i];
        if (table.objects[i].kind == Gate) {
            bool open=table.objects[i].group==2 ? game.targetMask==7 : game.cooldown[i]!=0;
            int angle=game.elementState[i]+(open?8:-4);
            game.elementState[i]=clamp(angle,0,80);
        }
        if (table.objects[i].kind == Spinner && game.elementState[i]) {
            --game.elementState[i];
            if (game.elementState[i] % 12 == 0) addScore(table.objects[i].value);
        }
    }
    bool ready=false, live=false;
    for(const Ball &b:game.balls) if(b.active) {ready |= b.shooter;live |= !b.shooter;}
    // Press edges only: a held key (including USB heartbeat) is one shove.
    if(live && !ready && game.tilt < 3 && (pressed & (A_BUTTON|RIGHT_BUTTON))) {
        game.shakeLevel=game.nudgeCooldown ? game.shakeLevel+1 : 1;
        game.nudgeCooldown=26; // accept another press through frame 25 (~417 ms)
        game.shakeDirection=(pressed & RIGHT_BUTTON) ? 1 : -1;
        if(game.shakeLevel > SHAKE_LEVELS) {
            game.shakeLevel=SHAKE_LEVELS;game.tilt=3;game.ballSave=0;
            game.modeTicks=game.scorePopTicks=0;
            game.bonusTicks=0;game.bonusNext=BonusNone;
            // The persistent tilt warning is drawn directly from game.tilt.
            rumble::pulse(240,180,2);
        } else {
            int strength=shakeStrength();
            for(Ball &b:game.balls) if(b.active && !b.shooter && b.ramp<0 && !b.scoopTicks)
                b.vx -= game.shakeDirection*strength*256;
            if(game.shakeLevel==SHAKE_LEVELS)announce("DANGER - EASY ON SHAKING",70);
            rumble::pulse(70+strength*30,35+strength*12,1);
        }
        game.shakeTicks=42;
    }
    // Flipkit: exp(-7.5*t) * sin(52*t), plus a 0.22*sin(39*t)
    // depth wobble, sampled at 60 Hz in Q6 for 700 ms; no runtime trig.
    static const int8_t shakeX[42]={0,43,49,23,-12,-32,-27,-6,14,21,13,-2,-12,-12,-5,4,8,6,1,-4,-5,-3,1,3,3,1,-1,-2,-1,0,1,1,1,0,-1,-1,0,0,1,0,0,0};
    static const int8_t shakeY[42]={0,8,11,9,4,-1,-5,-6,-5,-2,1,3,3,2,1,-1,-2,-2,-1,0,0,1,1,1,0,0,-1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
    game.shakeX=game.shakeY=0;
    if(game.shakeTicks) {
        unsigned age=42-game.shakeTicks--;
        int strength=shakeStrength();
        // A readable first shove on the small LCD, still capped at 6 px.
        // This is visual amplitude only; free-ball inertia above is unchanged.
        game.shakeX=(shakeX[age]*(strength+3)*game.shakeDirection+32)>>6;
        game.shakeY=(shakeY[age]*(strength+3)+32)>>6;
    }
    int oldLeft = game.left, oldRight = game.right;
    bool tilt = game.tilt >= 3;
    game.stuck=false;
    game.left = clamp(game.left + ((held & LEFT_BUTTON) && !tilt ? 72 : -56), 0, 255);
    game.right = clamp(game.right + ((held & B_BUTTON) && !tilt ? 72 : -56), 0, 255);
    bool shooting = held & (A_BUTTON | DOWN_BUTTON);
    if (ready) {
        if (shooting) game.launchHeld = true;
        if (game.launchHeld && !shooting && (released & (A_BUTTON | DOWN_BUTTON))) {
            launchBall(); game.launchHeld = false;
        }
    }
    for (Ball &b : game.balls) {
        game.scattered=false;
        if (!b.active || b.shooter) continue;
        if (b.ramp >= 0) {
            b.stillTicks=0;
            const Object &ramp = table.objects[unsigned(b.ramp)];
            unsigned age=++b.rampTicks;
            if (age < RAMP_ENTRY_FRAMES) { b.x += b.vx; b.y += b.vy; continue; }
            int x, y; rampPoint(ramp, (age-RAMP_ENTRY_FRAMES) * 256 / (RAMP_RIDE_FRAMES-RAMP_ENTRY_FRAMES), x, y);
            b.x = x * ONE; b.y = y * ONE;
            if (age >= RAMP_RIDE_FRAMES) { b.ramp = -1; b.vx = x < 60 ? 250 : -250; b.vy = 350; }
            continue;
        }
        if (b.scoopTicks) {
            b.stillTicks=0;
            // Eject through the front lip and toward open playfield. Leaving
            // from the center can bounce off the cup rim into a capture loop.
            if (!--b.scoopTicks) { b.y += 14 * ONE; b.x += b.vx > 0 ? 8 * ONE : -8 * ONE; }
            continue;
        }
        b.vx = b.vx * 1023 / 1024;
#if PINBALL_SPIN_GRIP
        b.spin=b.spin*255/256; // ~3 s half-life at 60 Hz, Q16 avoids Q8 dead zone
#endif
        for (unsigned step = 0; step < 2; ++step) {
            b.vy += table.h.gravity / 4 + (step < table.h.gravity % 4 ? 1 : 0);
            b.vx = clamp(b.vx, -1280, 1280);
            b.vy = clamp(b.vy, b.launching ? -2880 : -1792, 1664);
            b.x += b.vx / 4;
            b.y += b.vy / 4;
            bounds(b);
            objects(b, oldLeft, oldRight);
            flippers(b, MAIN_LEFT, MAIN_RIGHT, table.h.height - 25, MAIN_LENGTH, oldLeft, oldRight);
            if (b.scoopTicks || b.ramp >= 0) break;
        }
        if(!b.stillTicks || (!tilt && (pressed&(A_BUTTON|RIGHT_BUTTON)))) {
            b.stillX=b.x;b.stillY=b.y;b.stillTicks=0;
        }
        // A trapped ball can repeatedly rebound across a pixel boundary.
        // Measure escape from one fixed area, not frame-to-frame jitter or
        // velocity. Slow rolling leaves this area and restarts the timer.
        if (!b.scoopTicks && b.ramp < 0 &&
            unsigned(b.x-b.stillX+2*ONE)<=4*ONE && unsigned(b.y-b.stillY+2*ONE)<=4*ONE) {
            // During play this is an informational prompt, never an automatic
            // kick or state transition. Tilt forfeits the ball separately.
            if(b.stillTicks<180)++b.stillTicks;
            if(b.stillTicks>=90 && !tilt)game.stuck=true;
            if (tilt && b.stillTicks >= 180) {
                b.stillTicks = 0; METRIC(searches);
                // Tilt already forfeits this ball. A search kick can leave
                // it trapped forever, so retire only the stalled ball and
                // let the usual last-ball drain advance the turn.
                b.active=false;continue;
            }
        } else b.stillTicks = 0;
        if (b.y > (table.h.height + 5) * ONE) {
            if (game.ballSave && !tilt) {
                b.x = SHOOTER_X * ONE; b.y = (table.h.height - 22) * ONE;
                b.vx = 0; b.vy = -2800; b.launching = true;
                clearSpin(b);
                announce("BALL SAVED");
            } else b.active = false;
        }
    }
    if (!activeBalls()) {
        game.stuck=false;
        rumble::play(rumble::Effect::Drain);
        game.modeTicks = 0;
        game.bonusTicks=0;game.bonusNext=BonusNone;
        game.tilt = 0;
        game.shakeLevel=game.shakeTicks=game.nudgeCooldown=0;
        game.shakeX=game.shakeY=0;
        game.targetMask = game.laneMask = 0;
        if (--game.lives) serve();
        else { game.over = true; announce("GAME OVER", 255); audio::blip(400, 150, true); }
    }
    int lowest = 0, lowestFree = 0, riding = -1;
    for (unsigned i = 0; i < 3; ++i) {
        const Ball &b = game.balls[i]; if (!b.active) continue;
        if (b.y / ONE > lowest) lowest = b.y / ONE;
        if (b.ramp >= 0) riding = i;
        else if (b.y / ONE > lowestFree) lowestFree = b.y / ONE;
    }
    int target = clamp(lowest - 62, -HEADER_HEIGHT, table.h.height - 108);
    int delta = target - game.camera;
    game.camera += clamp(delta, -6, 6);
    // Whip in, hold briefly, ease out, like CHChess's capture camera. The
    // simulation and inputs keep running. Restore the wide view before a
    // ball reaches the drain, including another ball during multiball.
    bool protectFlippers = lowestFree > table.h.height - 85;
    bool followRamp = riding >= 0 && activeBalls() == 1 && !game.over;
    if (followRamp) {
        game.zoomBall = riding;
        game.zoomTicks = 44;  // the whole ride, including screen crossings
    } else if (game.rampCamera) game.zoomTicks = 17;  // hold the exit, then ease out
    game.rampCamera = followRamp;
    if (protectFlippers || !game.balls[game.zoomBall].active || game.over) game.zoomTicks = 0;
    int zoomTarget = game.zoomTicks > 16 ? 384 : ONE;
    game.zoom += clamp(zoomTarget - game.zoom, protectFlippers ? -64 : -16, 32);
}
}  // namespace pinball
