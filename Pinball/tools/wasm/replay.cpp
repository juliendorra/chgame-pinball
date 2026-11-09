// Binary test driver for the identical direct API compiled natively.
#include <stdint.h>
#include <stdio.h>
#include <CHGame.h>
#include "Elements.h"
#include "Physics.h"
#include "Render.h"
#include <math.h>
#include <initializer_list>
extern "C" {
void pb_init();uint8_t *pb_input();int pb_apply(unsigned);void pb_step(unsigned);
void pb_restart(unsigned);void pb_pause(unsigned);int pb_place(int,int,int,int);
const int32_t *pb_state();unsigned pb_state_count();
const int32_t *pb_physics();
const uint8_t *pb_render();unsigned pb_render_size();
const uint8_t *pb_lcd();unsigned pb_lcd_size();
const uint8_t *pb_table();unsigned pb_table_size();
}
static uint32_t read32(){uint32_t n=0;if(fread(&n,4,1,stdin)!=1)__builtin_trap();return n;}
static void write32(uint32_t n){fwrite(&n,4,1,stdout);}
int main(){
    pb_init();int op;
    // Test the actual integer rotation independently of collision integration.
    const pinball::Game saved=pinball::game;
    double worst=0,mean=0;unsigned samples=0;
    for(unsigned scale: {0u,2u,4u,8u,16u})for(unsigned seed=1;seed<=8192;++seed){
        pinball::game.rng=seed;pinball::game.scattered=false;
        auto &b=pinball::game.balls[0];b.vx=int(seed%2601)-1300;b.vy=900;
        int x=b.vx,y=b.vy;pinball::scatterBall(b,scale);
        if(b.vx*b.vx+b.vy*b.vy>x*x+y*y)return 5;
        double angle=atan2(double(x)*b.vy-double(y)*b.vx,double(x)*b.vx+double(y)*b.vy);
        if(fabs(angle)>31*scale/16384.0+0.002)return 6;
        if(fabs(angle)>worst)worst=fabs(angle);mean+=angle;++samples;
        int vx=b.vx,vy=b.vy;unsigned rng=pinball::game.rng;
        pinball::scatterBall(b,scale);
        if(b.vx!=vx||b.vy!=vy||pinball::game.rng!=rng)return 7;
        pinball::game.rng=seed;pinball::game.scattered=false;b.vx=x;b.vy=y;
        pinball::scatterBall(b,scale);
        if(b.vx!=vx||b.vy!=vy||pinball::game.rng!=rng)return 8;
    }
    if(fabs(mean/samples)>0.0001)return 9;
    pinball::game=saved;
    fprintf(stderr,"Scatter: %u integer-rotation checks; no energy gain; max %.3f deg, mean %.5f deg\n",samples,worst*180/3.141592653589793,mean/samples*180/3.141592653589793);
    const pinball::GuideRail closed=pinball::shooterFlapArm(0);
    int previous=closed.v;
    for(unsigned angle=10;angle<=80;angle+=10){
        const pinball::GuideRail arm=pinball::shooterFlapArm(angle);
        // Screen Y increases downward: every opening pose must lift the tip.
        if(arm.x!=closed.x || arm.y!=closed.y || arm.v>=previous)return 4;
        previous=arm.v;
    }
    for(int bend=-3;bend<=3;++bend)for(unsigned t=0;t<=256;++t){
        int lx,ly,rx,ry;
        pinball::rubberPoint(0,432,t,bend,lx,ly);
        pinball::rubberPoint(1,432,t,bend,rx,ry);
        if(lx+rx!=pinball::RUBBER_REFLECT_X || ly!=ry)return 10;
    }
    fprintf(stderr,"Rubber geometry: 1799 mirrored curve samples, including both lower joints, passed\n");
    const auto savedTable=pinball::table;
    const char *savedMessage=pinball::message;unsigned savedMessageTicks=pinball::messageTicks;
    pinball::table.h.count=0;pinball::table.h.height=432;
    auto surface=[](unsigned c){return c==1 || c==3 || c==5 || c==8 || c==14;};
    unsigned rubberPixels=0;
    for(unsigned ticks=0;ticks<=18;++ticks){
        pinball::game.camera=324;pinball::game.zoom=256;
        pinball::game.rubberTicks[0]=pinball::game.rubberTicks[1]=ticks;
        pinball::game.rubberStrength[0]=pinball::game.rubberStrength[1]=3;
        for(auto &b:pinball::game.balls)b.active=false;
        pinball::drawTable();
        for(int y=42;y<76;++y)for(int x=69;x<94;++x){
            auto pixel=[&](int u){return gfx_fb[y*64+(u>>1)]>>((u&1)*4)&15;};
            unsigned right=pixel(x),left=pixel(pinball::RUBBER_REFLECT_X-x);
            // Board-space shadows may fall on different interior pixels.
            if(surface(right)||surface(left)){if(right!=left)return 11;++rubberPixels;}
        }
    }
    pinball::table=savedTable;pinball::game=saved;
    pinball::message=savedMessage;pinball::messageTicks=savedMessageTicks;
    fprintf(stderr,"Rubber faces: %u mirrored hardware pixels through all 19 flex poses passed\n",rubberPixels);
    while((op=getchar())!=EOF){
        if(op=='C')fwrite(pb_physics(),4,5,stdout);
        else if(op=='L'){unsigned n=read32();if(n>960)return 2;fread(pb_input(),1,n,stdin);write32(pb_apply(n));}
        else if(op=='S')pb_step(read32());
        else if(op=='J'){int x=read32(),y=read32(),vx=read32(),vy=read32();write32(pb_place(x,y,vx,vy));}
        else if(op=='R')pb_restart(read32());
        else if(op=='Q')pb_pause(read32());
        else if(op=='H'){write32(pb_lcd_size());fwrite(pb_lcd(),1,pb_lcd_size(),stdout);}
        else if(op=='G'){
            fwrite(pb_state(),4,pb_state_count(),stdout);
            const uint8_t *p=pb_render();write32(pb_render_size());fwrite(p,1,pb_render_size(),stdout);
            write32(pb_lcd_size());fwrite(pb_lcd(),1,pb_lcd_size(),stdout);
            write32(pb_table_size());fwrite(pb_table(),1,pb_table_size(),stdout);
        }else return 3;
    }
    return 0;
}
