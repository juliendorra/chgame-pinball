#include <CHGame.h>
#include <SdSpi.h>
#include <string.h>
#include "Live.h"
#include "src/rumble/Rumble.h"
#include "Physics.h"
#include "SyncBuild.h"

#ifndef CHSIM
extern "C" {
uint8_t CDC_available(void), CDC_write_nb(char), CDC_enumerated(void), CDC_dtr(void);
int16_t CDC_read_nb(void);
void CDC_flush(void);
}
#endif
#if CHGAME_DEBUG && !defined(CHSIM)
// Keep the full diagnostic renderer/probes within Rev0 flash. The normal
// release and native editor build carry the live protocol.
namespace pinball { namespace live {
bool command(const char *){return false;}
void poll(){}
void sample(bool){}
bool changed(){return false;}
bool busy(){return false;}
} }
#else
namespace pinball { namespace live {
static uint16_t expected, received;
static uint32_t block, touched, keysAt;
static bool raw, applied, keys;
static struct { uint32_t frame, build; uint8_t flags, runs[64]; } trace;
static uint8_t traceUsed;
static bool tracing;
static uint8_t *staging() { return reinterpret_cast<uint8_t *>(&editData()); }
static void output(const char *p,unsigned n) {
#ifdef CHSIM
    Serial.write(reinterpret_cast<const uint8_t *>(p),n);
#else
    if(!CDC_enumerated() || !CDC_dtr())return;
    uint32_t start=millis();
    while(n) {
        if(CDC_write_nb(*p)){++p;--n;start=millis();}
        else if(!CDC_enumerated() || millis()-start>50)return;
    }
    CDC_flush();
#endif
}
static void say(const char *text) {output(text,strlen(text));}
static void number(uint32_t n) {char b[16];fmtInt(b,n);say(b);}
static void reply(bool ok) {say(ok?"LIVE OK\n":"LIVE ERR\n");}
static uint32_t number(const char *&p) {
    while(*p==' ' || *p==',')++p;
    uint32_t v=0;while(*p>='0'&&*p<='9'){if(v>429496729u)return 0xFFFFFFFFu;v=v*10+*p++-'0';}return v;
}
static int nibble(char c) {return c>='0'&&c<='9'?c-'0':c>='a'&&c<='f'?c-'a'+10:-1;}
static void data(const uint8_t *p,unsigned n) {
    static const char hex[]="0123456789abcdef";
    say("LIVE DATA ");
    char out[64];
    while(n){unsigned count=n>32?32:n;for(unsigned i=0;i<count;++i){out[i*2]=hex[p[i]>>4];out[i*2+1]=hex[p[i]&15];}output(out,count*2);p+=count;n-=count;}
    say("\n");
}
static void traceReply() {
    data(reinterpret_cast<const uint8_t *>(&trace),9+traceUsed);
    traceUsed=0;
}
void sample(bool playing) {
    if(!tracing)return;
    if(millis()-touched>3000){tracing=false;return;}
    ++trace.frame;
    if(!playing)trace.flags|=2;
    unsigned mask=chgame.buttons();
    if(traceUsed && trace.runs[traceUsed-2]==mask && trace.runs[traceUsed-1]<255)++trace.runs[traceUsed-1];
    else if(traceUsed<sizeof trace.runs){trace.runs[traceUsed++]=mask;trace.runs[traceUsed++]=1;}
    else trace.flags|=1;
}
static uint32_t hash(const uint8_t *p,unsigned n) {uint32_t h=2166136261u;while(n--)h=(h^*p++)*16777619u;return h;}
bool busy() {return expected && millis()-touched<3000;}
bool changed() {bool result=applied;applied=false;return result;}
bool apply(const Table &next, unsigned size) {
    if(!validTable(next,size))return false;
    bool reset=!game.started || table.boardId()!=next.boardId() || table.h.height!=next.h.height;
    if(!reset) {
        uint8_t cooldown[MAX_OBJECTS]={},states[MAX_OBJECTS]={};
        int8_t ramps[3]={-1,-1,-1};
        bool used[MAX_OBJECTS]={};
        for(unsigned i=0;i<next.h.count;++i) {
            const Object &o=next.objects[i];
            for(unsigned j=0;j<table.h.count;++j)if(!used[j] && !memcmp(&o,&table.objects[j],sizeof o)){
                used[j]=true;cooldown[i]=game.cooldown[j];states[i]=game.elementState[j];
                for(unsigned b=0;b<3;++b)if(game.balls[b].ramp==int(j))ramps[b]=i;
                break;
            }
        }
        memcpy(game.cooldown,cooldown,sizeof cooldown);memcpy(game.elementState,states,sizeof states);
        for(unsigned b=0;b<3;++b)game.balls[b].ramp=ramps[b];
    }
    table=next;if(reset)newGame();
    invalidatePreview();applied=true;return true;
}
bool command(const char *p) {
    invalidatePreview();
    while(*p==' ')++p;
    char cmd=*p++;touched=millis();bool ok=false;
    if(cmd=='?'){say("LIVE HELLO 1.4.19 PBT2 RAM SD RUBBER TRACE\n");return true;}
#if PINBALL_SD_BOARDS
    if (!table.h.version && (cmd=='R' || cmd=='Y' || cmd=='M' || cmd=='P' || cmd=='T')) {
        reply(false);
        return false;
    }
#endif
    if(cmd=='Y') {
        uint32_t seed=number(p);
        if(seed>1) {
            if(chgame.buttons()){reply(false);return false;}
            newGame(seed);applied=true;trace.frame=0;trace.build=PINBALL_GAME_HASH;
            trace.flags=traceUsed=0;tracing=true;
        }
        if(seed!=1 || tracing) {
            traceReply();if(!seed)tracing=false;return true;
        }
        reply(false);return false;
    }
    if(cmd=='H'){gfx_wait();data(gfx_fb,GFX_FB_BYTES);return true;}
    if(cmd=='M'){
        while(*p==' ')++p;bool minus=*p=='-';if(minus)++p;
        unsigned row=number(p);ok=row<=unsigned(minus?HEADER_HEIGHT:table.h.height-108);
        if(ok){game.camera=minus?-int(row):int(row);applied=true;}
    }
    else if(cmd=='E') {
        // Read the actual PWM setup too, so target tests catch a wrong remap.
        say("LIVE RUMBLE ");number(rumble::level());say(" ");number(rumble::remaining());
#ifndef CHSIM
        say(" ");number(AFIO->PCFR1);say(" ");number(GPIOC->CFGLR);say(" ");number(TIM2->CH4CVR);
#endif
        say("\n");return true;
    }
    else if(cmd=='B' || cmd=='W') {
        uint32_t n=number(p);raw=cmd=='W';block=n;
        expected=raw?512:(n>=sizeof(TableHeader)&&n<=sizeof(Table)?n:0);received=0;ok=expected!=0;
    } else if(cmd=='D') {
        unsigned at=number(p);while(*p==' ')++p;
        unsigned n=strlen(p);
        ok=busy() && at==received && n && !(n&1) && n<=64 && received+n/2<=expected;
        for(unsigned i=0;ok&&i<n;++i)if(nibble(p[i])<0)ok=false;
        if(ok)for(unsigned i=0;i<n;i+=2)staging()[received++]=(nibble(p[i])<<4)|nibble(p[i+1]);
    } else if(cmd=='C') {
        ok=expected && !raw && received==expected && apply(editData(),expected);
        expected=received=0;
    } else if(cmd=='F') {
        uint32_t h=number(p);
        ok=expected==512 && raw && received==512 && hash(staging(),512)==h;
        if(ok){gfx_wait();ok=writeSector(block,staging()) && sd::read(block,gfx_chunkScratch()) && hash(gfx_chunkScratch(),512)==h;}
        expected=received=0;
    } else if(cmd=='T') {data(reinterpret_cast<const uint8_t *>(&table),table.wireSize());return true;}
    else if(cmd=='G') {
        unsigned index=number(p);expected=received=0;
        ok=previewTable(index);
        if(ok){data(reinterpret_cast<const uint8_t *>(&previewData()),previewData().wireSize());return true;}
    } else if(cmd=='L') {
        expected=received=0;scanTables();
        for(unsigned i=0;i<libraryCount;++i){say("LIVE BOARD ");number(i);say(" ");output(library[i].name,8);say("\n");}
        ok=true;
    } else if(cmd=='S') {
        uint32_t lba=number(p);gfx_wait();ok=sd::read(lba,gfx_chunkScratch());
        if(ok){data(gfx_chunkScratch(),512);return true;}
    } else if(cmd=='I') {gfx_wait();ok=sd::init();}
    else if(cmd=='K') {unsigned n=number(p);ok=n<=255;if(ok){chgame.injected=n;keys=true;keysAt=millis();}}
    else if(cmd=='N') {
        int32_t v[]={game.shakeLevel,game.nudgeCooldown,game.shakeTicks,game.shakeX,game.shakeY,game.tilt};
        say("LIVE SHAKE");for(int32_t n:v){say(" ");number(n);}say("\n");return true;
    }
    else if(cmd=='V') {
        int32_t values[]={int32_t(table.h.id),int32_t(game.score),game.lives,int32_t(game.ticks),
            game.balls[0].x,game.balls[0].y,game.balls[0].vx,game.balls[0].vy,game.left,game.right,
            game.balls[0].shooter,game.camera,game.zoom,game.paused,int32_t(chgame.frameCount)};
        say("LIVE STATE");for(int32_t value:values){say(" ");number(value);}say("\n");return true;
    }
    else if(cmd=='Q'){unsigned n=number(p);ok=n<=1;if(ok)game.paused=n;}
    else if(cmd=='R'){newGame(number(p));applied=true;ok=true;}
    else if(cmd=='Z'){data(reinterpret_cast<const uint8_t *>(&game.seed),8);return true;}
    else if(cmd=='P') {
        unsigned x=number(p),y=number(p);ok=x>=10&&x<=108&&y>=12&&y<table.h.height-12;
        if(ok){placeBall(0,x,y,0,0);applied=true;}
    } else if(cmd=='X'){expected=received=0;chgame.injected=0;keys=false;ok=true;}
    if(ok && tracing && (cmd=='C' || cmd=='R' || cmd=='Q' || cmd=='P'))traceReply();
    else reply(ok);
    return ok;
}
__attribute__((noinline)) void poll() {
    if(expected && millis()-touched>=3000)expected=received=0;
    if(keys && millis()-keysAt>500){chgame.injected=0;keys=false;}
#if !CHGAME_DEBUG && !defined(CHSIM)
    static char line[96];static unsigned length;static bool overflow;
    while(CDC_available()) {
        int c=CDC_read_nb();if(c<0)break;
        if(c=='\n') {
            line[length]=0;
            if(!overflow && length && line[0]=='@')command(line+1);
            else if(length)reply(false);
            length=0;overflow=false;
        } else if(c!='\r') {
            if(length+1<sizeof line)line[length++]=c;else overflow=true;
        }
    }
#endif
}
} }

#endif
