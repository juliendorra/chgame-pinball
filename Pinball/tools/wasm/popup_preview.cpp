// Render scripted presentation states through the unmodified game renderer.
#include <CHGame.h>
#include "Physics.h"
#include "Render.h"
#include "popup_layout_probe.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
using namespace pinball;
extern "C" void pb_init();
extern "C" uint8_t *pb_input();
extern "C" int pb_apply(unsigned);
int main(int argc,char **argv) {
    if(argc!=4)return 2;
    pb_init();
    for(unsigned theme=0;theme<9;++theme) {
        char path[1024];std::snprintf(path,sizeof path,"%s/theme-%u.pbt",argv[2],theme);
        FILE *board=std::fopen(path,"rb");if(!board)return 3;
        unsigned n=std::fread(pb_input(),1,sizeof table,board);std::fclose(board);
        if(!pb_apply(n))return 4;
        std::ifstream cases(argv[1]);std::string slug;
        unsigned bonus,arg,mask,mult,mode,value,kind,view;
        while(cases>>slug>>bonus>>arg>>mask>>mult>>mode>>value>>kind>>view) {
            std::string footer;std::getline(cases,footer);if(!footer.empty())footer.erase(0,1);
            newGame(12345);game.camera=120;game.zoom=256;game.multiplier=mult;
            game.modeTicks=mode;game.laneMask=mask;game.score=value?value:12500;
            for(Ball &b:game.balls)b.active=false;
            placeBall(0,60,200,0,0);messageTicks=0;
            unsigned duration=(bonus||view)?BONUS_FRAMES:36;
            if(view==4 || view==5){game.shakeTicks=30;game.shakeLevel=view==4?2:3;game.shakeDirection=1;}
            if(view==6)game.tilt=3;
            if(view==7)announce(footer.c_str(),180);
            for(unsigned frame=0;frame<12;++frame) {
                unsigned age=frame*(duration-1)/11;
                game.ticks=age;game.bonus=bonus;game.bonusArg=arg;
                game.stuck=bonus==BonusStuck;
                game.bonusTicks=bonus?duration-age:0;
                game.scorePopKind=kind;game.scorePopValue=value;game.scorePopTicks=(bonus||view)?0:duration-age;
                beginPopupLayout(slug.c_str(),theme);drawTable();checkScoreCaptionPadding();
                if(view==1 || view==2)drawPause(view==1);
                if(view==3){drawGameOver(game.score>50000?game.score:50000);checkGameOverLayout();}
                if(!std::strcmp(argv[3],"-"))continue;
                std::snprintf(path,sizeof path,"%s/t%u-%s-%02u.fb",argv[3],theme,slug.c_str(),frame);
                FILE *f=std::fopen(path,"wb");if(!f)return 5;
                std::fwrite(gfx_fb,1,GFX_FB_BYTES,f);uint16_t colors[16];
                for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);
                std::fwrite(colors,1,sizeof colors,f);std::fclose(f);
            }
        }
    }
    std::printf("PASS %u popup layout checks across all themes and animation samples\n",popupLayoutChecks());
}
