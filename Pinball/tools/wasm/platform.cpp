// Browser transport only. All game, input, palette and drawing code is shared.
// There is no serial protocol or emulated USB in the browser engine.
#include <CHGame.h>
#include <SdSpi.h>

// x86 vectorized CHGfx code assumes the ABI's 16-byte array alignment.
uint8_t gfx_fb[GFX_FB_BYTES] __attribute__((aligned(16)));
CHGfx Gfx;
SimSerial Serial;
static uint8_t scratch[2*GFX_CHUNK_BYTES] __attribute__((aligned(4)));
static uint32_t clockUs;
static uint8_t mode=GFX_12BPP,divider=GFX_DIV2;
uint32_t micros(){return clockUs;}
uint32_t millis(){return clockUs/1000;}
void delay(uint32_t ms){clockUs+=ms*1000;}
void delayMicroseconds(uint32_t us){clockUs+=us;}
void studio_clock(uint32_t us){clockUs=us;}
void pinMode(uint32_t,uint32_t){}
void digitalWrite(uint32_t,uint32_t){}
int digitalRead(uint32_t){return HIGH;}
uint8_t chgame_readButtons(){return 0;}
long random(long n){return n>0?rand()%n:0;}
long random(long lo,long hi){return lo+random(hi-lo);}
void randomSeed(unsigned long s){srand(s);}
int SimSerial::available(){return 0;}
int SimSerial::read(){return -1;}
size_t SimSerial::write(uint8_t){return 1;}
size_t SimSerial::write(const uint8_t *,size_t n){return n;}
size_t SimSerial::print(const char *p){return strlen(p);}
int SimSerial::printf(const char *,...){return 0;}

// The framebuffer is consumed directly; LCD transfers do not advance time.
void gfx__begin(uint8_t d,uint8_t m){divider=d;mode=m;memset(gfx_fb,0,sizeof gfx_fb);}
void gfx__begin12(uint8_t d){gfx__begin(d,GFX_12BPP);}
void gfx_wait(){}
bool gfx_busy(){return false;}
int gfx_flushRow(){return GFX_H;}
void gfx_waitRow(int){}
void gfx_flush(){}
void gfx_flushAsync(){}
void gfx_flushRect(int,int,int,int){}
void gfx_flushRectAsync(int,int,int,int){}
uint8_t *gfx_chunkScratch(){return scratch;}
void gfx_setSpiDiv(uint8_t d){divider=d;}
void gfx_setColorMode(uint8_t m){mode=m;}
uint8_t gfx_colorMode(){return mode;}
uint8_t gfx_spiDiv(){return divider;}
uint32_t gfx_spiHz(){return F_CPU/divider;}
void gfx_setPanelOffsets(uint8_t,uint8_t,uint8_t){}
void gfx_setInverted(bool){}
void gfx_setPanelFrameRate(uint8_t,uint8_t,uint8_t){}
// Browser boards arrive as validated PBT data, never as an emulated SD image.
namespace sd {
bool init(){return false;}
bool read(uint32_t,uint8_t *){return false;}
bool stream(uint32_t,uint32_t,uint8_t *,uint8_t *,BlockFn,void *){return false;}
}
