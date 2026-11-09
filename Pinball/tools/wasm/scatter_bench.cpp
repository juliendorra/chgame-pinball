// Headless experiments using the same solver, geometry and autoplay as Studio.
#include <CHGame.h>
#include "Physics.h"
#include "Autoplay.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#ifndef PINBALL_SCATTER_ANGLE_ZERO
#define PINBALL_SCATTER_ANGLE_ZERO 0
#endif
using namespace pinball;
extern "C" void pb_init();
static uint32_t next(uint32_t &r) { r^=r<<13;r^=r>>17;r^=r<<5;return r; }
static void tick(unsigned held=0,unsigned previous=0) {
    updateGame(held,held&~previous,previous&~held);
}
static void shots(unsigned count) {
    Table base;builtinTable(base);base.h.height=480;base.h.gravity=8;base.h.count=1;
    // All contacts occur on frame one. Then 60 frames of unobstructed flight.
    // Normal and oblique shots expose the integer-friction dead zone separately.
    for(unsigned powered=0;powered<2;++powered)
    for(int vx: {0,240,-240})for(int speed: {600,1200})for(int kick: {280,1600}) {
        if(!powered && kick==1600)continue;
        table=base;
        table.objects[0]=powered?Object{Bumper,0,64,280,8,int16_t(kick),180}:
                                  Object{Wall,0,15,200,108,200,0};
        uint32_t seedStream=0x51A77E12;
        for(unsigned i=0;i<count;++i) {
            uint32_t seed=next(seedStream);newGame(seed);
            placeBall(0,64,powered?267:205,vx,powered?speed:-speed);
            std::printf("{\"kind\":\"shot\",\"powered\":%u,\"vx\":%d,\"speed\":%d,\"kick\":%d,\"seed\":%u,\"samples\":[",powered,vx,speed,powered?kick:0,seed);
            for(unsigned frame=1;frame<=60;++frame) {
                tick();
                if(frame==1||frame==15||frame==30||frame==60) {
                    const Ball &b=game.balls[0];
                    std::printf("%s[%d,%d,%d,%d,%u]",frame==1?"":",",b.x,b.y,b.vx,b.vy,game.rng);
                }
            }
            std::puts("]}");
        }
    }
    // A genuinely soft wall contact must be identical in every configuration.
    table=base;table.objects[0]={Wall,0,15,200,108,200,0};newGame(12345);
    placeBall(0,64,205,0,-200);tick();
    std::printf("{\"kind\":\"soft\",\"rng\":%u,\"vx\":%d,\"vy\":%d}\n",game.rng,game.balls[0].vx,game.balls[0].vy);
}
int main(int argc,char **argv) {
    if(argc<5)return 2;
    unsigned seeds=std::strtoul(argv[1],nullptr,10),ticks=std::strtoul(argv[2],nullptr,10),shotSeeds=std::strtoul(argv[3],nullptr,10);
    if(!seeds||!ticks||!shotSeeds)return 3;
    pb_init();
#ifdef PINBALL_SPIN_BENCH
    std::printf("{\"kind\":\"model\",\"grip\":%u,\"forget\":%u}\n",PINBALL_SPIN_GRIP,PINBALL_SPIN_FORGET);
#endif
    std::printf("{\"kind\":\"config\",\"passive\":%u,\"powered\":%u,\"eject\":%u,\"angle_zero\":%u}\n",SCATTER_PASSIVE,SCATTER_POWERED,SCATTER_EJECT,PINBALL_SCATTER_ANGLE_ZERO);
    shots(shotSeeds);
    for(int file=4;file<argc;++file) {
        Table board={};FILE *f=std::fopen(argv[file],"rb");if(!f)return 4;
        size_t n=std::fread(&board,1,sizeof board,f);std::fclose(f);
        if(!validTable(board,n))return 5;
        uint32_t seedStream=0xA11CE517;
        for(unsigned trial=0;trial<seeds;++trial) {
            const uint32_t seed=next(seedStream);
            std::vector<unsigned char> tape(ticks);uint32_t rng=seed^0xB07B07u,inputHash=2166136261u;
            unsigned held=0;
            for(unsigned frame=0;frame<ticks;++frame) {
                if(frame%11==0){unsigned r=next(rng);held=(r&1?LEFT_BUTTON:0)|(r&2?B_BUTTON:0);}
                // Down only launches, so these pulses cannot shake or tilt.
                tape[frame]=held|(frame%120<2?DOWN_BUTTON:0);
                inputHash=(inputHash^tape[frame])*16777619u;
            }
            for(unsigned policy=0;policy<2;++policy) {
                table=board;
                std::vector<int32_t> path((ticks+59)/60*3);
                const auto e=evaluateBoard(ticks,seed,policy?2:0,policy?nullptr:tape.data(),false,path.data());
#ifdef PINBALL_SPIN_BENCH
                std::printf("{\"kind\":\"spin\",\"board\":%u,\"seed\":%u,\"policy\":\"%s\",\"frames\":%u,\"peak_q8\":%u,\"trace\":%u}\n",
                            board.h.id,seed,policy?"reactive":"fixed",e.spinFrames,e.spinPeak,e.spinTrace);
#endif
                unsigned types=0;for(unsigned k=0;k<KIND_COUNT;++k)types+=game.metrics.kinds[k]!=0;
                std::printf("{\"kind\":\"game\",\"board\":%u,\"seed\":%u,\"policy\":\"%s\",\"input_hash\":%u,\"trace\":%u,\"frames\":%u,\"score\":%u,\"over\":%u,\"lives\":%u,\"coverage\":%u,\"types\":%u,\"stalled\":%u,\"drought\":%u,\"fast\":%u,\"ramps\":%u,\"flips\":%u,\"searches\":%u,\"banks\":%u,\"lanes\":%u,\"multiballs\":%u,\"path\":[",
                    board.h.id,seed,policy?"reactive":"fixed",policy?0:inputHash,e.trace,e.frames,game.score,game.over,game.lives,e.coverage,types,e.stalled,e.drought,e.fast,game.metrics.ramps,game.metrics.flipperHits,game.metrics.searches,game.metrics.bankSets,game.metrics.laneSets,game.metrics.multiballs);
                for(unsigned i=0;i<(e.frames+59)/60*3;++i)std::printf("%s%d",i?",":"",path[i]);
                std::puts("]}");
            }
        }
    }
}
