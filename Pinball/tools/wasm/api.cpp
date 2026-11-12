#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include "Live.h"
#include "src/rumble/Rumble.h"
#include "SyncBuild.h"
#include <string.h>
using namespace pinball;
void setup();void loop();void studio_clock(uint32_t);
static uint32_t frames;
static uint8_t overview[(480+HEADER_HEIGHT)*GFX_FB_STRIDE+32];
// Fixed-width state ABI, independent of C++ struct padding/pointers/bool size.
static int32_t state[64];
extern "C" {
uint32_t pb_build(){return PINBALL_GAME_HASH;}
void pb_init(){setup();chgame.startExits=false;}
uint8_t *pb_input(){return reinterpret_cast<uint8_t *>(&editData());}
int pb_apply(unsigned n){
    if(n<sizeof(TableHeader) || n>sizeof(Table) || !live::apply(editData(),n))return 0;
    // Process the sketch's palette/screen transition even on a display frame
    // with no physics tick due. This cannot advance the game clock.
    chgame.lockstep=0;loop();return 1;
}
void pb_step(unsigned mask){
    studio_clock(uint64_t(++frames)*1000000/60);
    chgame.injected=mask&255;chgame.lockstep=1;loop();
}
void pb_restart(unsigned seed){newGame(seed);}
void pb_pause(unsigned on){game.paused=on!=0;}
int pb_place(int x,int y,int vx,int vy){
    if(x<10||x>108||y<12||y>=table.h.height-12||vx<-2600||vx>2600||vy<-2600||vy>2600)return 0;
    placeBall(0,x,y,vx,vy);return 1;
}
const int32_t *pb_state(){
    int viewX,viewY,viewW,viewH;cameraView(viewX,viewY,viewW,viewH);
    const int32_t values[]={
        int32_t(table.h.id),table.h.height,table.h.count,int32_t(game.score),game.lives,
        int32_t(game.ticks),game.balls[0].x,game.balls[0].y,game.balls[0].vx,game.balls[0].vy,
        game.left,game.right,game.balls[0].shooter,game.balls[0].launching,game.camera,game.zoom,
        game.paused,game.over,game.balls[0].ramp,game.balls[0].scoopTicks,game.ballSave,
        game.laneMask,game.targetMask,game.multiplier,game.tilt,game.zoomTicks,game.rampCamera,
        int32_t(game.scorePopValue),int32_t(game.scorePopTicks),game.scorePopKind,game.shakeLevel,
        game.nudgeCooldown,game.shakeTicks,game.shakeX,game.shakeY,game.shakeDirection,
        int32_t(game.metrics.searches),int32_t(game.metrics.ramps),int32_t(game.metrics.kickbacks),
        game.launchHeld,int32_t(chgame.frameCount),int32_t(activeBalls()),game.shooterFlap,
        int32_t(game.seed),int32_t(game.rng),game.bonus,game.bonusTicks,game.bonusArg,
        game.bonusNext,game.bonusNextArg,int32_t(scoreMultiplier()),int32_t(laneGoal()),int32_t(laneGroups()),
        game.balls[0].spin,viewX,viewY,viewW,viewH,table.h.idHigh
    };
    memcpy(state,values,sizeof values);return state;
}
unsigned pb_state_count(){return 59;}
const int32_t *pb_physics(){
    static const int32_t config[]={PINBALL_SPIN_GRIP,PINBALL_SPIN_FORGET,
        PINBALL_SCATTER_PASSIVE,PINBALL_SCATTER_POWERED,PINBALL_SCATTER_EJECT};
    return config;
}
const uint8_t *pb_render(){
    uint8_t *at=overview;
    drawOverview([](const uint8_t *p,unsigned n,void *ctx){
        uint8_t *&dest=*static_cast<uint8_t **>(ctx);memcpy(dest,p,n);dest+=n;
    },&at);
    return overview;
}
unsigned pb_render_size(){return (table.h.height+HEADER_HEIGHT)*GFX_FB_STRIDE+32;}
const uint8_t *pb_lcd(){return gfx_fb;}
unsigned pb_lcd_size(){return GFX_FB_BYTES;}
const uint8_t *pb_table(){return reinterpret_cast<const uint8_t *>(&table);}
unsigned pb_table_size(){return table.wireSize();}
}
