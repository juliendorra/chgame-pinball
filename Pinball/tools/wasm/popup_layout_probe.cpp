#include "popup_layout_probe.h"
#include "Physics.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
using namespace pinball;
static unsigned checks,textCalls,theme;
static int iconRight,panelY;
static int textBottom;
static const char *slug;
static void check(bool ok,const char *why) {
    ++checks;
    if(!ok){std::fprintf(stderr,"Layout FAIL theme=%u %s: %s\n",theme,slug,why);std::exit(7);}
}
void beginPopupLayout(const char *name,unsigned ink){slug=name;theme=ink;textCalls=0;iconRight=0;textBottom=0;}
static bool gameOver(){return !std::strcmp(slug,"overlay-3") || !std::strcmp(slug,"gameover-max");}
unsigned popupLayoutChecks(){return checks;}
void checkedPopupText(int x,int y,const char *text,uint8_t ink) {
    if(gameOver()) {
        check(x>=9 && x+text35Width(text)*2<=119,"game-over text needs generous side padding");
        check(y>=19 && y+10<=122,"game-over text must stay inside its panel");
        check(y>=textBottom+3,"game-over text rows need visible separation");
        textBottom=y+10;++textCalls;
    }
    if(game.bonusTicks) {
        int width=text35Width(text)*2;
        check(x>=6 && x+width<=122,"large text must stay inside panel with side padding");
        if(textCalls)check(x>=iconRight+2,"detail text must have a gap after its target sprites");
        else panelY=y-4;
        ++textCalls;
    }
    text35x2(x,y,text,ink);
}
void checkedPopupSprite(const uint8_t *data,int x,int y,const uint8_t *remap,int scale,uint8_t flip) {
    if(gameOver() && textCalls) {
        check(x>=9 && x+data[0]*scale/256<=119,"eight-digit result scores must fit with side padding");
        check((y>=48 && y+data[1]*scale/256<=63) || (y>=79 && y+data[1]*scale/256<=94),"result digits and their shadows need space between labels");
    }
    if(game.bonusTicks && textCalls) {
        int right=x+data[0]*scale/256,bottom=y+data[1]*scale/256;
        check(x>=6 && right<=122,"target sprite must stay inside panel sides");
        if(panelY>=14)check(y>=panelY+2 && bottom<=panelY+35,"target sprite needs a blank row above bottom outline");
        if(right>iconRight)iconRight=right;
    }
    sprite4(data,x,y,remap,scale,flip);
}
void checkGameOverLayout(){check(textCalls==5,"game-over title, both labels and both controls must use large text");}
static unsigned pixel(int x,int y){return(gfx_fb[y*GFX_FB_STRIDE+x/2]>>((x&1)*4))&15;}
void checkScoreCaptionPadding() {
    if(game.bonusTicks || !game.scorePopTicks || game.scorePopTicks>34)return;
    // Locate the actual top and bottom outline as long uninterrupted runs.
    // Glyphs cannot produce a 45-pixel run: each character has spacing.
    static const uint8_t inks[]={4,4,14,10,10,13,8,11,10};
    int edges=0,bottom=-1;
    for(int y=12;y<58 && edges<2;++y) {
        unsigned run=0,best=0;
        for(int x=3;x<125;++x){run=pixel(x,y)==inks[theme]?run+1:0;if(run>best)best=run;}
        if(best>=45){++edges;bottom=y;}
    }
    check(edges==2,"score popup must have two visible complete horizontal outlines");
    const char *label=game.scorePopKind==2?"LUCKY SCORE!":"SCORE MILESTONE!";
    int width=text35Width(label),left=(128-width)/2;
    for(int y=bottom-3;y<bottom;++y)for(int x=left;x<left+width;++x)
        check(pixel(x,y)==7,"score caption needs three empty panel rows below it");
}
