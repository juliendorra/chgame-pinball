// Host-only operation budgets. These are work ceilings, not simulated MCU cycles.
#include "render_budget.h"
#include "Physics.h"
#include "Render.h"
#include "Autoplay.h"
#include "SpriteData.h"
#include "Elements.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
// Arduino macros must not rewrite C++ standard-library declarations.
#undef min
#undef max
#include <algorithm>
using namespace pinball;
extern "C" void pb_init();
struct Work { unsigned lines,linePixels,pixels,spans,spanPixels,sprites; };
static Work work,peak;
static constexpr Work limits={64,4096,256,2048,32768,128};
static unsigned rendered;
static unsigned stressRamps;
static const char *label;
void budgetLine(int x,int y,int u,int v,uint8_t c){++work.lines;work.linePixels+=std::max(std::abs(u-x),std::abs(v-y))+1;gfx_line(x,y,u,v,c);}
void budgetPixel(int x,int y,uint8_t c){++work.pixels;gfx_pixel(x,y,c);}
void budgetHline(int x,int y,int w,uint8_t c){++work.spans;if(w>0)work.spanPixels+=w;gfx_hline(x,y,w,c);}
void budgetSprite(const uint8_t *p,int x,int y,const uint8_t *map,int scale,uint8_t flip){++work.sprites;sprite4(p,x,y,map,scale,flip);}
static void frame(){
    work={};drawTable();++rendered;
    peak.lines=std::max(peak.lines,work.lines);peak.linePixels=std::max(peak.linePixels,work.linePixels);
    peak.pixels=std::max(peak.pixels,work.pixels);peak.spans=std::max(peak.spans,work.spans);
    peak.spanPixels=std::max(peak.spanPixels,work.spanPixels);peak.sprites=std::max(peak.sprites,work.sprites);
    // Enough headroom for current boards, but reject the hundreds of layered
    // flash line calls that caused the measured 43.5 Hz ramp regression.
    // Crowded diagnostic layouts have a per-ramp work ceiling, rather than
    // pretending twelve overlapping ramps have the cost of a shipped board.
    const unsigned spanLimit=stressRamps?256+300*stressRamps:limits.spans;
    const unsigned pixelLimit=stressRamps?4096+3200*stressRamps:limits.spanPixels;
    if(work.lines>limits.lines || work.linePixels>limits.linePixels || work.pixels>limits.pixels ||
       work.spans>spanLimit || work.spanPixels>pixelLimit || work.sprites>limits.sprites){
        std::fprintf(stderr,"Render budget exceeded: %s: lines=%u linePixels=%u pixels=%u spans=%u spanPixels=%u sprites=%u\n",
            label,work.lines,work.linePixels,work.pixels,work.spans,work.spanPixels,work.sprites);std::exit(10);
    }
}
static void requireRamp(bool ok,const char *message){
    if(!ok){std::fprintf(stderr,"Gameplay regression (%s): %s\n",label,message);std::exit(11);}
}
static unsigned spriteInk(const uint8_t *p,int x,int y){
    if(x<0 || y<0 || x>=p[0] || y>=p[1])return 15;
    p+=2;while(y--){unsigned n=*p++;p+=n;}
    unsigned n=*p++;
    while(n--){unsigned r=*p++,w=(r>>4)+1;if(x<int(w))return r&15;x-=w;}
    return 15;
}
static void rampEntries(){
    label="ramp entry";unsigned contacts=0,pixels=0,underArrow=0;
    table.h.height=480;table.h.count=1;
    for(unsigned group=0;group<3;++group)for(int offset:{-4,0,4})for(int speed:{-250,-700,-1700}){
        table.objects[0]={Ramp,uint8_t(group),60,240,90,140,0};
        newGame(12345);placeBall(0,60+offset,255,0,speed);
        Ball &b=game.balls[0];
        for(unsigned n=0;n<24 && b.ramp<0;++n)updateGame(0,0,0);
        requireRamp(b.ramp==0,"upward shot was not captured at the mouth");
        requireRamp(b.y<=252*ONE && b.y>=250*ONE,"capture must meet the perimeter at the lower lip");
        ++contacts;
        for(unsigned n=0;n<90;++n){
            game.camera=172;game.zoom=256;frame();
            if(n<12){
                // Independently unpack every visible ball pixel: the opaque
                // throat must never erase part of a ball entering the ramp.
                const auto &art=SPRITES[SPR_BALL];const uint8_t *p=art.frames[0];
                int x0=b.x/ONE-art.width/2,y0=b.y/ONE-game.camera+12-art.height/2;
                unsigned at=2;
                for(unsigned y=0;y<p[1];++y){unsigned runs=p[at++],x=0;
                    while(runs--){unsigned r=p[at++],ink=r&15,w=(r>>4)+1;
                        for(unsigned i=0;i<w;++i,++x)if(ink!=15 && ink!=2){
                            int xx=x0+x,yy=y0+y;unsigned actual=(gfx_fb[yy*64+xx/2]>>((xx&1)*4))&15;
                            unsigned expected=ink==8?1:ink;
                            const auto &arrow=SPRITES[SPR_RAMP];static const int bob[]={0,-1,-2,-1};
                            unsigned cover=spriteInk(arrow.frames[1],xx-(59-arrow.width/2),yy-(240+4+bob[(game.ticks/10)&3]-172+12-arrow.height/2));
                            if(cover!=15){expected=cover==8?4:cover;++underArrow;}
                            requireRamp(actual==expected,"ball/deck/floating-arrow layers disagree");++pixels;
                        }
                    }
                }
            }
            int x=b.x,y=b.y;updateGame(0,0,0);
            if(n<RAMP_ENTRY_FRAMES)requireRamp(std::abs(b.x-x)<=ONE && std::abs(b.y-y)<=2*ONE,"entry snapped onto the curve");
            requireRamp(n==89 ? b.ramp<0 : b.ramp==0,"ride must last the full 90 frames");
        }
        requireRamp(b.x==90*ONE && b.y==140*ONE,"ride missed its configured exit");
    }
    for(int offset:{-8,8}){
        newGame(12345);placeBall(0,60+offset,252,0,-700);updateGame(0,0,0);
        requireRamp(game.balls[0].ramp<0,"a side graze entered the ramp");
    }
    newGame(12345);placeBall(0,60,251,0,700);updateGame(0,0,0);
    requireRamp(game.balls[0].ramp<0,"a downward shot entered the ramp");
    // The open front touches the felt; no transverse cast-shadow strip.
    for(auto &b:game.balls)b.active=false;game.camera=172;game.zoom=256;frame();
    // Ignore the chosen floating arrow's own board-tinted shadow.
    for(int y=250;y<=251;++y)for(int x=62;x<=62;++x){
        unsigned ink=(gfx_fb[(y-172+12)*64+x/2]>>((x&1)*4))&15;
        requireRamp(ink==0,"dark strip crosses the open entrance");
    }
    requireRamp(underArrow>0,"riding ball must pass beneath the floating arrow");
    std::printf("{\"kind\":\"ramp_entry\",\"contacts\":%u,\"visible_ball_pixels\":%u,\"under_arrow_pixels\":%u,\"rejected_shots\":3,\"ride_frames\":90}\n",contacts,pixels,underArrow);
}
static void stuckHelp(){
    label="stuck-ball help";unsigned checks=0;
    auto check=[&](bool ok,const char *why){++checks;requireRamp(ok,why);};
    for(unsigned level=0;level<256;++level)
        check(flipperPoseIndex(level)==(level*8+127)/255,"compact pose indexing must preserve every flipper stroke");
    auto reset=[](){
        table.h.height=480;table.h.gravity=12;table.h.count=1;
        table.objects[0]={Wall,0,40,220,80,220,0};
        newGame(12345);placeBall(0,60,215,0,0);
    };
    reset();
    for(unsigned n=0;n<89;++n){updateGame(0,0,0);check(!game.stuck,"shake help appeared before 1.5 s");}
    updateGame(0,0,0);check(game.stuck,"stationary ball must show large shake help");
    game.camera=195;game.zoom=256;frame();
    // The right control is a solid 3x5 triangle scaled to 6x10 pixels.
    static const unsigned triangle[]={1,3,7,3,1};
    for(unsigned y=0;y<5;++y)for(unsigned x=0;x<3;++x)for(unsigned dy=0;dy<2;++dy)for(unsigned dx=0;dx<2;++dx){
        unsigned xx=26+x*2+dx,yy=33+y*2+dy;
        unsigned ink=(gfx_fb[yy*64+xx/2]>>((xx&1)*4))&15;
        check(ink==((triangle[y]&(1u<<x))?4u:7u),"D-pad prompt must use a filled triangle before OR A");
    }
    uint8_t warning[GFX_FB_BYTES];std::memcpy(warning,gfx_fb,sizeof warning);
    game.stuck=false;frame();
    check(std::memcmp(warning,gfx_fb,sizeof warning)!=0,"help must stay visible when the stuck ball occupies the banner band");
    game.stuck=true;frame();
    // Overview stays clear of repeated LCD banners and preserves the live LCD.
    auto overview=[](){uint32_t h=2166136261u;drawOverview([](const uint8_t *p,unsigned n,void *ctx){
        auto &h=*static_cast<uint32_t *>(ctx);while(n--)h=(h^*p++)*16777619u;
    },&h);return h;};
    Game before=game;uint32_t withHelp=overview();
    check(std::memcmp(&before,&game,sizeof game)==0,"overview altered the stuck-ball state");
    check(std::memcmp(warning,gfx_fb,sizeof warning)==0,"overview did not restore the LCD warning");
    game.stuck=false;check(overview()==withHelp,"full-board editor must not repeat the shake banner");game.stuck=true;
    game.paused=true;before=game;updateGame(0,0,0);
    check(std::memcmp(&before,&game,sizeof game)==0,"pause must freeze stationary detection");
    frame();check(std::memcmp(warning,gfx_fb,sizeof warning)!=0,"pause must hide shake instructions");game.paused=false;
    game.balls[0].vx=700;for(unsigned n=0;n<3;++n)updateGame(0,0,0);check(!game.stuck,"escaping ball must clear shake help");
    for(unsigned key:{unsigned(A_BUTTON),unsigned(RIGHT_BUTTON)}){
        reset();for(unsigned n=0;n<90;++n)updateGame(0,0,0);
        updateGame(key,key,0);check(!game.stuck,"either shake key must free the fixture and clear help");
    }
    reset();for(unsigned n=0;n<220;++n)updateGame(LEFT_BUTTON|B_BUTTON,0,0);
    check(game.stuck && game.balls[0].stillTicks==180,"flipper input must not conceal a stuck ball or wrap its timer");
    check(game.metrics.searches==0,"normal play must not kick a held ball");
    for(unsigned n=0;n<8;++n)updateGame(0,0,LEFT_BUTTON|B_BUTTON);
    check(game.metrics.searches==0 && game.stuck,"flipper release must not move the ball or hide help");
    reset();placeBall(1,80,100,700,0);for(unsigned n=0;n<90;++n)updateGame(0,0,0);
    check(game.stuck,"another moving multiball must not clear a stationary ball's help");
    game.balls[0].vx=700;for(unsigned n=0;n<3;++n)updateGame(0,0,0);check(!game.stuck,"clear multiball help once all balls escape");
    // Captured on the actual console: the upper-right bat/guide traps the
    // ball at x=99.22, y=171.29..171.87. Subpixel rebound corrections must
    // not repeatedly cancel the help timer.
    for(unsigned policy=0;policy<3;++policy){
        reset();table.h.height=384;table.h.gravity=28;table.h.count=2;
        table.objects[0]={Flippers,0,22,180,98,21,0};
        table.objects[1]={Wall,0,100,160,88,178,0};
        placeBall(0,99,171,0,61);auto &ball=game.balls[0];ball.x=25401;ball.y=43921;
        int minY=ball.y,maxY=ball.y,maxStep=0;
        auto held=[&](unsigned frame){return policy==1 || (policy==2 && frame%12<6)?unsigned(LEFT_BUTTON):0u;};
        for(unsigned n=0;n<90;++n){
            int y=ball.y;updateGame(held(n),0,0);
            minY=std::min(minY,int(ball.y));maxY=std::max(maxY,int(ball.y));maxStep=std::max(maxStep,std::abs(int(ball.y)-y));
        }
        check(maxStep>64 && maxY-minY<2*ONE,"recorded fixture must reproduce the subpixel rebound that defeated the old detector");
        check(game.stuck,"recorded upper-bat trap must show help despite subpixel jitter");
        for(unsigned n=90;n<990;++n){
            updateGame(held(n),0,0);
            check(game.stuck,"help must stay visible throughout trapped-ball jitter");
            check(game.lives==3 && !game.over && !game.paused && ball.active && !ball.shooter,"stuck warning must not drain, restart or switch game states");
            check(game.metrics.searches==0,"normal trapped-ball help must not inject an automatic kick");
        }
    }
    for(unsigned direction=0;direction<3;++direction){
        reset();table.h.count=0;table.h.gravity=0;placeBall(0,40,180,0,0);
        for(unsigned n=0;n<180;++n){
            game.balls[0].vx=direction==1?0:100;game.balls[0].vy=direction==0?0:direction==1?100:-100;
            updateGame(0,0,0);check(!game.stuck,"slow horizontal/vertical/diagonal rolling must not request a shake");
        }
    }
    for(unsigned mode=0;mode<4;++mode){
        reset();auto &b=game.balls[0];b.stillTicks=180;
        if(mode==0)b.shooter=true;
        else if(mode==1){table.objects[0]={Ramp,2,60,240,90,140,0};b.ramp=0;}
        else {b.scoopTicks=60;b.scooped=mode==2;}
        for(unsigned n=0;n<30;++n){updateGame(0,0,0);check(!game.stuck,"launcher/ramp/cup holds must not request a shake");}
    }
    reset();for(unsigned n=0;n<90;++n)updateGame(0,0,0);game.tilt=3;
    for(unsigned n=0;n<95;++n){updateGame(0,0,0);check(!game.stuck,"never ask for shaking during tilt");}
    check(game.lives==2 && game.balls[0].shooter,"tilted stuck ball must still retire and serve the next ball");
    std::printf("{\"kind\":\"stuck_help\",\"checks\":%u,\"prompt_after_frames\":90,\"tilt_retire_after_frames\":180,\"stable_trap_frames\":990}\n",checks);
}
int main(int argc,char **argv){
    if(argc<2)return 2;pb_init();unsigned games=0;
    std::printf("{\"kind\":\"limits\",\"limits\":{\"line_calls\":%u,\"line_pixels\":%u,\"pixel_calls\":%u,\"span_calls\":%u,\"span_pixels\":%u,\"sprites\":%u}}\n",
        limits.lines,limits.linePixels,limits.pixels,limits.spans,limits.spanPixels,limits.sprites);
    rampEntries();
    stuckHelp();
    for(int file=1;file<argc;++file){
        Table board={};FILE *f=std::fopen(argv[file],"rb");if(!f)return 3;
        unsigned n=std::fread(&board,1,sizeof board,f);std::fclose(f);if(!validTable(board,n))return 4;
        label=board.h.title;
        for(unsigned policy=0;policy<3;++policy)for(unsigned seed:{1777u,3554u}){
            table=board;const Evaluation a=evaluateBoard(1800,seed,policy,nullptr,false,nullptr,frame);
            unsigned score=game.score,searches=game.metrics.searches;
            const Evaluation b=evaluateBoard(1800,seed,policy,nullptr,false,nullptr,frame);
            if(a.trace!=b.trace || a.spinTrace!=b.spinTrace || a.frames!=b.frames || score!=game.score){
                std::fprintf(stderr,"Nondeterministic autoplay: %s policy=%u seed=%u\n",label,policy,seed);return 5;
            }
            std::printf("{\"kind\":\"play\",\"board\":%u,\"policy\":%u,\"seed\":%u,\"frames\":%u,\"score\":%u,\"trace\":%u,\"stalled\":%u,\"searches\":%u,\"drought\":%u}\n",
                board.h.id,policy,seed,a.frames,score,a.trace,a.stalled,searches,a.drought);++games;
        }
        table=board;newGame(12345);for(auto &ball:game.balls)ball.active=false;
        // Sweep full layouts at normal zoom and 1.5x, not just whichever
        // areas a synthetic player happened to reach.
        for(unsigned zoom:{256u,384u})for(int camera=-HEADER_HEIGHT;camera<=table.h.height-108;camera+=24){
            game.camera=camera;game.zoom=zoom;frame();
        }
    }
    label="ramp stress";
    for(unsigned count:{1u,2u,3u,4u,6u,8u,12u}){
        stressRamps=count;
        table.h.count=count;table.h.height=432;
        for(unsigned i=0;i<count;++i)table.objects[i]={Ramp,uint8_t(i%2),
            int16_t(18+(i*17)%79),382,int16_t(12+(i*23)%89),80,0};
        newGame(12345);for(auto &ball:game.balls)ball.active=false;
        unsigned before=rendered,spans=0;
        for(unsigned zoom:{256u,384u})for(int camera=0;camera<=324;camera+=4){game.camera=camera;game.zoom=zoom;frame();spans=std::max(spans,work.spans);}
        std::printf("{\"kind\":\"ramp_stress\",\"ramps\":%u,\"rendered_frames\":%u,\"peak_span_calls\":%u,\"span_calls_limit\":%u}\n",count,rendered-before,spans,256+300*count);
    }
    std::printf("{\"kind\":\"summary\",\"games\":%u,\"repeat_runs\":%u,\"rendered_frames\":%u,\"peak\":{\"line_calls\":%u,\"line_pixels\":%u,\"pixel_calls\":%u,\"span_calls\":%u,\"span_pixels\":%u,\"sprites\":%u}}\n",
        games,games,rendered,peak.lines,peak.linePixels,peak.pixels,peak.spans,peak.spanPixels,peak.sprites);
}
