#include <CHGame.h>
#include "Physics.h"
#include <cstdio>
#include <cstdlib>
using namespace pinball;
extern "C" void pb_init();
static unsigned checks;
static void check(bool ok,const char *why){++checks;if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}}
static void tick(){updateGame(0,0,0);}
static void trapped(bool tilted) {
    builtinTable(table);table.h.height=480;table.h.count=4;
    table.objects[0]={Wall,0,35,180,85,180,0};
    table.objects[1]={Wall,0,35,140,35,180,0};
    table.objects[2]={Wall,0,85,140,85,180,0};
    table.objects[3]={Wall,0,35,140,85,140,0};
    newGame(12345);placeBall(0,60,175,0,0);game.tilt=tilted?3:0;
}
int main(){
    pb_init();
    trapped(true);game.score=12345;game.ballSave=600;
    for(unsigned f=0;f<179;++f)tick();
    check(game.tilt==3 && game.lives==3 && game.balls[0].stillTicks==179,"tilted trapped ball is detected without player input");
    game.paused=true;for(unsigned f=0;f<300;++f)tick();
    check(game.balls[0].stillTicks==179 && game.lives==3,"pause freezes stuck-ball timeout");
    game.paused=false;tick();
    check(game.lives==2 && game.tilt==0 && game.balls[0].shooter,"three-second tilted stall advances to next ball");
    check(game.score==12345 && !game.bonusTicks && game.metrics.searches==1,"tilted recovery awards no points or bonus");
    check(game.balls[0].vx==0 && game.balls[0].vy==0,"tilted ball is not relaunched by active ball save");
    trapped(true);game.lives=1;for(unsigned f=0;f<180;++f)tick();
    check(game.over && game.lives==0 && activeBalls()==0,"final tilted trapped ball reaches game over");
    trapped(true);for(unsigned f=0;f<179;++f)tick();
    placeBall(1,100,200,100,300);tick();
    check(!game.balls[0].active && game.balls[1].active && game.tilt==3 && game.lives==3,"multiball retires only stalled ball and keeps tilt until all drain");
    placeBall(1,100,490,0,300);tick();
    check(game.lives==2 && game.tilt==0 && game.balls[0].shooter,"remaining multiball drain loses exactly one life");
    trapped(false);for(unsigned f=0;f<180;++f)tick();
    check(game.lives==3 && game.balls[0].active && !game.balls[0].shooter && game.metrics.searches==1,"normal-play trapped ball still receives the existing search nudge");
    check(game.balls[0].vy==-360 && game.balls[0].stillTicks==0,"normal search impulse is unchanged");
    trapped(true);placeBall(0,100,150,600,100);for(unsigned f=0;f<20;++f)tick();
    check(game.lives==3 && game.metrics.searches==0,"moving tilted ball is allowed to drain naturally");
    std::printf("PASS %u tilt stuck-ball checks: real enclosed trap, three-second timeout, pause, score, saves, multiball and final life\n",checks);
}
