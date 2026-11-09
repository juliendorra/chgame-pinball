#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
using namespace pinball;
extern "C" void pb_init();
static unsigned checks;
static void check(bool ok,const char *why){++checks;if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}}
static void tick(){updateGame(0,0,0);}
static void lab(Object o){builtinTable(table);table.h.height=480;table.h.count=1;table.objects[0]=o;newGame(12345);}
static void shot(const char *dir,const char *name){
    drawTable();char path[1024];std::snprintf(path,sizeof path,"%s/%s.fb",dir,name);
    FILE *f=std::fopen(path,"wb");check(f,"screenshot file");std::fwrite(gfx_fb,1,GFX_FB_BYTES,f);
    uint16_t palette[16];for(unsigned i=0;i<16;++i)palette[i]=gfx_paletteOut(i);
    std::fwrite(palette,1,sizeof palette,f);std::fclose(f);
}
static std::vector<uint8_t> render(bool banner){
    unsigned ticks=game.bonusTicks;game.bonusTicks=banner?ticks:0;drawTable();
    std::vector<uint8_t> p(gfx_fb,gfx_fb+GFX_FB_BYTES);game.bonusTicks=ticks;return p;
}
int main(int argc,char **argv){
    check(argc==2,"output directory");pb_init();
    lab({Scoop,0,60,180,8,0,100});game.targetMask=7;placeBall(0,60,180,0,0);tick();
    check(activeBalls()==3 && game.ballSave==600,"real multiball grants ten-second save");
    check(game.bonus==BonusBallSave && game.bonusArg==10 && game.bonusTicks==BONUS_FRAMES,"immediate BALL SAVE 10 SECONDS announcement");
    check(game.bonusNext==BonusMultiball,"multiball celebration queues behind save notice");
    game.camera=120;game.zoom=256;game.zoomTicks=0;game.scorePopTicks=0;
    const Game multiball=game;
    for(unsigned frame=0;frame<168;++frame) {
        if(frame%4==0){char name[32];std::snprintf(name,sizeof name,"animation-%03u",frame);shot(argv[1],name);}
        tick();
    }
    game=multiball;
    shot(argv[1],"save-entry");game.bonusTicks=BONUS_FRAMES-20;shot(argv[1],"save-top");
    const auto visible=render(true),hidden=render(false);
    check(visible!=hidden,"large bonus is visible");
    check(!std::memcmp(visible.data(),hidden.data(),12*GFX_FB_STRIDE),"banner preserves score HUD");
    check(!std::memcmp(visible.data()+120*GFX_FB_STRIDE,hidden.data()+120*GFX_FB_STRIDE,8*GFX_FB_STRIDE),"banner preserves footer");
    game.bonusTicks=BONUS_FRAMES-24;check(render(true)!=visible,"border/sparkle animation changes pixels");
    for(Ball &b:game.balls)b.active=false;placeBall(0,60,145,0,0);
    const auto safe=render(true),plain=render(false);
    // Crossing the top band may hide the banner, but never relocates it.
    check(safe==plain,"top ball hides banner without moving it to the bottom");
    shot(argv[1],"save-top-blocked");
    placeBall(1,60,210,0,0); // LCD y=102; both popup bands are occupied
    check(render(true)==render(false),"defer drawing rather than obscure balls at both ends");
    game.balls[0].y=180*ONE;game.balls[1].active=false;
    const auto returned=render(true),returnedPlain=render(false);
    check(returned!=returnedPlain,"banner returns when top band clears");
    check(!std::memcmp(returned.data()+60*64,returnedPlain.data()+60*64,60*64),"returned banner stays at top, never bottom");
    // Sweep three moving balls through both bands, including zoom and shake.
    for(int zoom:{256,384})for(int y:{120,145,165,180,210}) {
        game.zoom=zoom;game.shakeX=3;game.shakeY=1;
        placeBall(0,60,y,0,0);placeBall(1,25,210,0,0);placeBall(2,90,180,0,0);
        auto a=render(true),b=render(false);
        check(!std::memcmp(a.data()+60*64,b.data()+60*64,60*64),"multiball never draws bonus in bottom band");
    }
    game=multiball;game.paused=true;for(unsigned i=0;i<20;++i)tick();
    check(game.bonusTicks==multiball.bonusTicks && game.bonusNext==BonusMultiball,"pause freezes active and queued banners");
    game.paused=false;game.bonusTicks=1;tick();
    check(game.bonus==BonusMultiball && game.bonusTicks==BONUS_FRAMES && !game.bonusNext,"queued banner starts once");
    game.camera=120;game.zoom=256;game.bonusTicks-=20;shot(argv[1],"multiball");
    // A real jackpot is higher priority than incidental rewards.
    lab({Scoop,0,60,180,8,0,100});game.modeTicks=600;game.multiplier=3;
    placeBall(0,60,180,0,0);placeBall(1,90,240,0,0);tick();
    check(game.bonus==BonusJackpot && game.score==60600,"real jackpot announcement preserves exact scoring");
    game.camera=120;game.zoom=256;game.bonusTicks-=20;shot(argv[1],"jackpot");
    // Score milestones use the same fixed top band.
    game.bonusTicks=0;game.scorePopTicks=20;game.scorePopValue=5000;
    for(Ball &b:game.balls)b.active=false;placeBall(0,60,145,0,0);
    drawTable();std::vector<uint8_t> blockedScore(gfx_fb,gfx_fb+GFX_FB_BYTES);
    game.scorePopTicks=0;drawTable();check(!std::memcmp(gfx_fb,blockedScore.data(),GFX_FB_BYTES),"score milestone also hides rather than changing anchor");
    placeBall(0,60,180,0,0);game.scorePopTicks=20;drawTable();
    std::vector<uint8_t> topScore(gfx_fb,gfx_fb+GFX_FB_BYTES);game.scorePopTicks=0;drawTable();
    check(std::memcmp(gfx_fb,topScore.data(),60*64)!=0 && !std::memcmp(gfx_fb+60*64,topScore.data()+60*64,60*64),"score milestone remains in top band");
    lab({Scoop,0,60,180,8,0,100});placeBall(0,60,180,0,0);tick();
    check(game.bonus==BonusDoubleScore,"single-ball scoop announces double score");
    // Re-entering a temporary scoring mode must not repeat its announcement.
    game.bonusTicks=40;game.cooldown[0]=0;messageTicks=0;placeBall(0,60,180,0,0);tick();
    check(game.modeTicks==600 && game.score==300,"repeat scoop preserves double scoring and refreshes the existing timer");
    check(game.bonus==BonusDoubleScore && game.bonusTicks==39 && !game.bonusNext && !messageTicks,"repeat scoop does not restart active banner or footer");
    game.bonusTicks=0;game.cooldown[0]=0;placeBall(0,60,180,0,0);tick();
    check(!game.bonusTicks && !game.bonusNext && !messageTicks,"expired banner stays silent while scoring mode is still active");
    celebrate(BonusSaucer);game.bonusTicks=40;game.cooldown[0]=0;placeBall(0,60,180,0,0);tick();
    check(game.bonus==BonusSaucer && game.bonusTicks==39 && !game.bonusNext,"refresh cannot replace a different reward banner");
    celebrate(BonusJackpot);game.bonusTicks=40;game.cooldown[0]=0;placeBall(0,60,180,0,0);tick();
    check(game.bonus==BonusJackpot && game.bonusTicks==39 && !game.bonusNext,"refresh cannot queue another double-score banner behind a jackpot");
    game.modeTicks=1;game.bonusTicks=0;game.cooldown[0]=0;messageTicks=0;
    unsigned beforeRenewal=game.score;placeBall(0,60,180,0,0);tick();
    check(game.modeTicks==600 && game.score==beforeRenewal+100 && game.bonus==BonusDoubleScore && game.bonusTicks==BONUS_FRAMES && messageTicks,"new bonus after actual expiry is announced again");
    // A jackpot is a new award on each qualified hit, even within one mode.
    game.cooldown[0]=0;placeBall(1,90,240,0,0);placeBall(0,60,180,0,0);tick();
    check(game.bonus==BonusJackpot && game.bonusTicks==BONUS_FRAMES,"new jackpot reward still announces during active double scoring");
    lab({Target,2,60,180,8,6,100});game.targetMask=3;placeBall(0,60,176,0,512);tick();
    check(game.bonus==BonusReady,"completed target banks announce multiball ready");
    game.camera=120;game.zoom=256;game.bonusTicks-=20;shot(argv[1],"multiball-ready");
    lab({Lane,2,60,180,8,0,100});game.laneMask=3;placeBall(0,60,180,0,0);tick();
    check(game.multiplier==2 && game.ballSave==360 && game.bonus==BonusBallSave && game.bonusArg==6 && game.bonusNext==BonusMultiplier,"lane bonus announces six seconds and multiplier");
    lab({Lane,2,60,180,8,0,100});game.multiplier=2;game.modeTicks=600;game.laneMask=3;
    placeBall(0,60,180,0,0);tick();
    check(game.multiplier==3 && scoreMultiplier()==6 && game.bonusNextArg==6,"stacked lane announcement uses effective six-times scoring");
    for(unsigned base=1;base<=5;++base)for(unsigned doubled=0;doubled<2;++doubled) {
        newGame(12345);game.multiplier=base;game.modeTicks=doubled?600:0;addScore(100);
        check(scoreMultiplier()==base*(doubled?2:1) && game.score==100*scoreMultiplier(),"effective HUD multiplier matches actual score award, including times ten");
    }
    newGame(12345);game.multiplier=2;drawTable();std::vector<uint8_t> normalHud(gfx_fb,gfx_fb+12*64);
    game.modeTicks=600;drawTable();check(std::memcmp(normalHud.data(),gfx_fb,12*64)!=0,"HUD visibly changes from times two to times four");
    shot(argv[1],"multiplier-stacked");game.modeTicks=0;drawTable();check(!std::memcmp(normalHud.data(),gfx_fb,12*64),"HUD returns to base multiplier when double scoring ends");
    lab({Kickback,0,20,180,8,0,100});placeBall(0,20,180,0,0);tick();
    check(game.bonus==BonusKickback,"kickback announces rescue");
    lab({Saucer,0,60,180,8,0,100});placeBall(0,60,180,0,0);tick();
    check(game.bonus==BonusSaucer,"saucer announces bonus");
    // Three real lane groups teach a set, then retain progress between hits.
    builtinTable(table);table.h.height=480;table.h.count=4;
    for(unsigned g=0;g<3;++g)table.objects[g]={Lane,uint8_t(g),int16_t(25+g*30),180,8,0,100};
    table.objects[3]={Scoop,1,60,250,8,0,100};newGame(12345);
    launchBall();check(laneGroups()==7 && game.bonusNext==BonusMultiplier && game.bonusNextArg==128,"launch queues all three lane goals after ball-save notice");
    game.bonusTicks=0;celebrate(BonusMultiplier,128);
    check(laneGoal()==2 && laneCount()==0,"mission starts with three missing lanes and times-two reward");
    game.balls[0].shooter=false;game.balls[0].launching=false;game.camera=120;game.zoom=256;
    game.bonusTicks-=20;placeBall(0,60,220,0,0);shot(argv[1],"lanes-intro");
    for(unsigned g=0;g<2;++g) {
        placeBall(0,25+g*30,180,0,0);tick();
        check(game.laneMask==((1u<<(g+1))-1) && laneCount()==g+1,"real lane hit records unique group progress");
        check(game.bonus==BonusMultiplier && game.bonusArg==(128|game.laneMask),"progress message identifies remaining lanes");
        game.camera=120;game.zoom=256;game.bonusTicks-=20;placeBall(0,60,220,0,0);
        shot(argv[1],g?"lanes-one-left":"lanes-two-left");
    }
    game.cooldown[0]=0;game.bonusTicks=30;placeBall(0,25,180,0,0);tick();
    check(game.laneMask==3 && game.bonusTicks==29,"repeat hit does not restart the mission or celebration");
    placeBall(0,85,180,0,0);tick();
    check(game.multiplier==2 && game.laneMask==0 && game.bonusNext==BonusMultiplier && game.bonusNextArg==2,"third distinct lane earns multiplier and resets next set");
    game.multiplier=5;check(laneGoal()==5,"maximum multiplier stays capped");
    game.bonusTicks=0;celebrate(BonusReady);game.bonusTicks-=20;game.camera=120;game.zoom=256;placeBall(0,60,220,0,0);
    shot(argv[1],"scoop-target-icon");
    // The icon follows the real target's group color, independently of theme.
    const auto scoopPink=render(true);table.objects[3].group=2;const auto scoopGold=render(true);
    check(scoopPink!=scoopGold,"message scoop uses the board target's own color");
    table.objects[3].group=1;
    game.zoom=384;const auto zoomIcon=render(true);check(zoomIcon!=render(false),"screen-space target icon survives playfield zoom");
    game.paused=true;const Game frozen=game;tick();check(game.bonusTicks==frozen.bonusTicks && game.laneMask==frozen.laneMask,"pause freezes mission feedback");
    builtinTable(table);newGame(12345);check(laneGroups()==7 && !game.bonusTicks && !game.bonusNext,"restart clears prior messages, lane mission remains in footer");
    // Drawing and bonus state must not change the synthetic player's path.
    lab({Bumper,0,64,180,8,280,100});placeBall(0,60,165,100,600);const Game initial=game;
    struct Frame {Ball balls[3];uint32_t score,rng;};std::vector<Frame> tape;
    for(unsigned i=0;i<180;++i){tick();Frame f;std::memcpy(f.balls,game.balls,sizeof f.balls);f.score=game.score;f.rng=game.rng;tape.push_back(f);}
    game=initial;celebrate(BonusBallSave,10);
    for(unsigned i=0;i<180;++i){tick();drawTable();check(!std::memcmp(game.balls,tape[i].balls,sizeof game.balls) && game.score==tape[i].score && game.rng==tape[i].rng,"presentation leaves physics and RNG unchanged");}
    newGame(12345);check(!game.bonusTicks && !game.bonusNext,"restart clears banners");
    std::printf("PASS %u bonus checks: real triggers, timer text, queue, pause, safe bands, animation, HUD and physics independence\n",checks);
}
