#include <CHGame.h>
#include <string.h>
#include "Render.h"
#include "Elements.h"
#include "SpriteData.h"
#include "ScoreData.h"
#include "BorderData.h"

namespace pinball {
#ifdef CHSIM
void drawOverview(void (*write)(const uint8_t *, unsigned, void *), void *context) {
    gfx_wait();
    int camera=game.camera,zoom=game.zoom,pop=game.scorePopTicks,bonus=game.bonusTicks;
    bool stuck=game.stuck;game.stuck=false;
    int sx=game.shakeX,sy=game.shakeY,st=game.shakeTicks;
    game.shakeX=game.shakeY=game.shakeTicks=0;game.zoom=256;game.scorePopTicks=game.bonusTicks=0;
    for(int y=-HEADER_HEIGHT;y<table.h.height;y+=108) {
        game.camera=y;drawTable();unsigned rows=table.h.height-y;if(rows>108)rows=108;
        write(gfx_fb+12*GFX_FB_STRIDE,rows*GFX_FB_STRIDE,context);
    }
    uint16_t colors[16];for(unsigned i=0;i<16;++i)colors[i]=gfx_paletteOut(i);
    write(reinterpret_cast<const uint8_t *>(colors),sizeof colors,context);
    game.camera=camera;game.zoom=zoom;game.scorePopTicks=pop;
    game.bonusTicks=bonus;
    game.stuck=stuck;
    game.shakeX=sx;game.shakeY=sy;game.shakeTicks=st;drawTable();
}
#endif
enum : uint8_t { BG, WHITE, GRID, METAL, CYAN, DIM, RED, PANEL, PINK, ORANGE, GOLD, GREEN, BLUE, PURPLE, SILVER, GLOW };
static int clipX, clipY = 12, clipW = 128, clipH = 108;
static int mirrorSling; // zero, or the reflection axis doubled
static int sy(int y) { return y - game.camera + 12; }
static uint8_t scoreColor(unsigned theme = table.h.theme);
static __attribute__((noinline)) void resultText(int y,const char *text,uint8_t color) {
    text35x2(64-text35Width(text),y,text,color);
}
static const uint8_t laneColors[]={CYAN,PINK,GOLD};
void center(int y, const char *s, uint8_t c) { text35((128 - text35Width(s)) / 2, y, s, c); }
static void line(int x, int y, int u, int v, uint8_t c) {
    int a = sy(y), b = sy(v);
    if ((a < 12 && b < 12) || (a >= 120 && b >= 120)) return;
    gfx_line(x, a, u, b, c);
}
// A five-pixel rounded extrusion: lit shoulder, two-pixel rubber crown,
// shaded side and dark foot. Walk each beam once in SRAM rather than
// layering several full Bresenham lines from flash.
static inline __attribute__((always_inline)) void beamPixel(int x, int y, uint8_t c) {
    if ((unsigned)(x - clipX) >= (unsigned)clipW || (unsigned)(y - clipY) >= (unsigned)clipH) return;
    uint8_t *p = gfx_fb + y * GFX_FB_STRIDE + (x >> 1);
    if (x & 1) *p = (*p & 15) | (c << 4);
    else *p = (*p & 240) | c;
}
RAMFUNC(pinballBeam) static void beam(int x, int y, int u, int v, uint8_t c, bool shadow, unsigned caps) {
    int dx = u > x ? u - x : x - u, dy = v > y ? v - y : y - v;
    int sx = x < u ? 1 : -1, stepY = y < v ? 1 : -1, err = dx - dy;
    bool vertical = dy > dx;
    const int ex = x, ey = y, eu = u, ev = v;
    // Bit 4 selects a flat ramp deck; caps then gives its half-width.
    // Share the SRAM walker instead of layering flash gfx_line/gfx_pixel calls.
    bool deck=c&16;
    uint8_t inks[5] = {SILVER, c, c, METAL, DIM};
    if(vertical && mirrorSling){inks[0]=DIM;inks[1]=METAL;inks[3]=c;inks[4]=SILVER;}
    if (shadow) for (unsigned i = 0; i < 5; ++i) inks[i] = GRID;
    // Long cabinet rails span several screens. Trim those walks before
    // rasterizing rather than visiting hundreds of invisible cross-sections.
    if (!dx) {
        if (y > v) { int t = y; y = v; v = t; }
        if (y < clipY) y = clipY;
        if (v >= clipY + clipH) v = clipY + clipH - 1;
        if (y > v) return;
        stepY = 1;
    } else if (!dy) {
        if (x > u) { int t = x; x = u; u = t; }
        if (x < clipX) x = clipX;
        if (u >= clipX + clipW) u = clipX + clipW - 1;
        if (x > u) return;
        sx = 1;
    }
    for (;;) {
        if(deck) {
            gfx_hline(x-int(caps),y,caps*2+1,c&15);
        } else if (vertical && y >= clipY && y < clipY + clipH && x - 2 >= clipX && x + 2 < clipX + clipW) {
            // Five lit pixels take three byte stores, with one ragged end.
            uint8_t *p = gfx_fb + y * GFX_FB_STRIDE + ((x - 2) >> 1);
            if (x & 1) {
                p[0] = (p[0] & 15) | (inks[0] << 4);
                p[1] = inks[1] | (inks[2] << 4); p[2] = inks[3] | (inks[4] << 4);
            } else {
                p[0] = inks[0] | (inks[1] << 4); p[1] = inks[2] | (inks[3] << 4);
                p[2] = (p[2] & 240) | inks[4];
            }
        } else {
            for (int k = -2; k <= 2; ++k) {
                beamPixel(x + (vertical ? k : 0), y + (vertical ? 0 : k), inks[k + 2]);
            }
        }
        if (x == u && y == v) break;
        int e2 = err * 2;
        if (e2 > -dy) { err -= dy; x += sx; }
        if (e2 < dx) { err += dx; y += stepY; }
    }
    if(deck)return;
    // Only paint the outward half of each rounded cap: the beam already
    // contains the other half. This avoids redrawing every short ramp join.
    int direction = vertical ? (ev > ey ? 1 : -1) : (eu > ex ? 1 : -1);
    for (unsigned end = 0; end < 2; ++end) {
        if (!(caps & (1u << end))) continue;
        int px = end ? eu : ex, py = end ? ev : ey;
        for (int d = 1; d <= 2; ++d) {
            int r = d == 1 ? 2 : 1, along = d * (end ? direction : -direction);
            for (int k = -r; k <= r; ++k) {
                beamPixel(px + (vertical ? k : along), py + (vertical ? along : k), inks[k + 2]);
            }
        }
    }
}
static void railPart(int x, int y, int u, int v, uint8_t c, bool shadow, unsigned caps) {
    if(mirrorSling){x=mirrorSling-x;u=mirrorSling-u;}
    int a = sy(y), b = sy(v);
    if ((a < clipY - 5 && b < clipY - 5) || (a > clipY + clipH + 2 && b > clipY + clipH + 2) ||
        (x < clipX - 4 && u < clipX - 4) || (x > clipX + clipW + 2 && u > clipX + clipW + 2)) return;
    // All light comes from upper left; shadows stay registered to the
    // board when it scrolls and scale with the same camera transform.
    int offset = shadow ? 2 : 0, down = shadow ? 3 : 0;
    beam(x + offset, a + down, u + offset, b + down, c, shadow, caps);
}
static void rail(int x, int y, int u, int v, uint8_t c = CYAN) {
    railPart(x,y,u,v,c,true,3); railPart(x,y,u,v,c,false,3);
}
struct RailPoint { int16_t x, y; };
static void railRun(const RailPoint *p, unsigned count, uint8_t color, bool roundBends = true, unsigned firstPass = 0, unsigned lastPass = 2) {
    int low=p[0].y,high=low;
    for(unsigned i=1;i<count;++i){if(p[i].y<low)low=p[i].y;if(p[i].y>high)high=p[i].y;}
    if(sy(high)<clipY-5 || sy(low)>clipY+clipH+2)return;
    // Shadow the complete run before drawing any of its metal. Interior
    // joints have no end caps, so they cannot cut a stripe across a rail.
    for (unsigned pass = firstPass; pass < lastPass; ++pass) {
        int x = p[0].x, y = p[0].y;
        bool first = true;
        for (unsigned i = 1; i < count; ++i) {
            int u = p[i].x, v = p[i].y, ex = u, ey = v;
            bool bend = roundBends && i + 1 < count && sy(v) >= clipY-10 && sy(v) < clipY+clipH+10;
            if (bend) {
                int dx = p[i-1].x-u, dy = p[i-1].y-v, dx2 = p[i+1].x-u, dy2 = p[i+1].y-v;
                int a = root(dx*dx+dy*dy), b = root(dx2*dx2+dy2*dy2);
                int radius = a < b ? a/3 : b/3; if (radius > 5) radius = 5;
                if (radius && a && b) {
                    ex = u + dx2*radius/b; ey = v + dy2*radius/b;
                    int entryX = u + dx*radius/a, entryY = v + dy*radius/a;
                    railPart(x,y,entryX,entryY,color,pass==0,first ? 1 : 0);
                    x = entryX; y = entryY; first = false;
                    for (int t = 1; t <= 3; ++t) {
                        int k = 3-t;
                        int xx = (k*k*entryX+2*k*t*u+t*t*ex)/9;
                        int yy = (k*k*entryY+2*k*t*v+t*t*ey)/9;
                        if (x != xx || y != yy) railPart(x,y,xx,yy,color,pass==0,0);
                        x=xx; y=yy;
                    }
                    continue;
                }
            }
            railPart(x,y,u,v,color,pass==0,(first ? 1 : 0) | (i+1==count ? 2 : 0));
            first = false; x=ex; y=ey;
        }
    }
}

struct ZoomMap { uint16_t sample[64]; uint8_t count[4]; };
RAMFUNC(pinballZoomRow) static void stretchRow(uint8_t *dst, const uint8_t *source, const ZoomMap *map) {
    uint32_t words[16];
    // Volatile prevents the compiler replacing this short SRAM loop with
    // an out-of-line flash memcpy in every row of the camera animation.
    const volatile uint32_t *src = reinterpret_cast<const volatile uint32_t *>(source);
    for (unsigned i = 0; i < 16; ++i) words[i] = src[i];
    const uint8_t *row = reinterpret_cast<const uint8_t *>(words);
    const uint16_t *op=map->sample;
    // Group operations by kind once per frame. The inner row loops then
    // have no per-pixel branches during the zoom's easing frames.
    for(unsigned n=map->count[0];n;--n){unsigned p=*op++;dst[p>>6]=row[p&63];}
    for(unsigned n=map->count[1];n;--n){unsigned p=*op++,a=p&63;dst[p>>6]=(row[a]>>4)|(row[a+1]<<4);}
    for(unsigned n=map->count[2];n;--n){unsigned p=*op++;dst[p>>6]=(row[p&63]&15)*17;}
    for(unsigned n=map->count[3];n;--n){unsigned p=*op++;dst[p>>6]=(row[p&63]>>4)*17;}
}
RAMFUNC(pinballZoomCopy) static void copyZoomRow(uint8_t *dst, const uint8_t *source) {
    uint32_t *d = reinterpret_cast<uint32_t *>(dst);
    const volatile uint32_t *s = reinterpret_cast<const volatile uint32_t *>(source);
    for (unsigned i = 0; i < 16; ++i) d[i] = s[i];
}
RAMFUNC(pinballZoom150) static void stretchRow150(uint8_t *dst, const uint8_t *source, int x0) {
    // At 1.5x, six destination pixels always come from four source pixels.
    // Expand packed nibbles in groups instead of sampling each pixel.
    uint32_t words[16];
    const volatile uint32_t *src = reinterpret_cast<const volatile uint32_t *>(source);
    for (unsigned i = 0; i < 16; ++i) words[i] = src[i];
    const uint8_t *row = reinterpret_cast<const uint8_t *>(words) + (x0 >> 1);
    if (x0 & 1) {
        for (unsigned i = 0; i < 21; ++i) {
            uint8_t a = row[i * 2], b = row[i * 2 + 1], c = row[i * 2 + 2];
            dst[i * 3] = (a >> 4) * 17;
            dst[i * 3 + 1] = b; dst[i * 3 + 2] = (b >> 4) | (c << 4);
        }
        dst[63] = (row[42] >> 4) * 17;
    } else {
        for (unsigned i = 0; i < 21; ++i) {
            uint8_t a = row[i * 2], b = row[i * 2 + 1];
            dst[i * 3] = (a & 15) * 17;
            dst[i * 3 + 1] = (a >> 4) | (b << 4); dst[i * 3 + 2] = b;
        }
        dst[63] = (row[42] & 15) * 17;
    }
}
static void zoomRegion(int &x0, int &y0, int &width, int &height) {
    const Ball &ball = game.balls[game.zoomBall];
    const int zoom = game.zoom;
    width = 1 + 127 * ONE / zoom; height = 1 + 107 * ONE / zoom;
    x0 = (ball.x >> 8) - 64 * ONE / zoom;
    y0 = (ball.y >> 8) - game.camera - 54 * ONE / zoom;
    if (x0 < 0) x0 = 0;
    if (x0 > 128 - width) x0 = 128 - width;
    if (y0 < 0) y0 = 0;
    if (y0 > 108 - height) y0 = 108 - height;
}
static void zoomPlayfield() {
    if (game.zoom <= ONE) return;
    int x0, y0, width, height; zoomRegion(x0, y0, width, height);
    const int zoom = game.zoom;
    uint8_t operations[64];
    ZoomMap map;
    for (int x = 0; x < 64; ++x) {
        int a = x0 + x * 2 * ONE / zoom, b = x0 + (x * 2 + 1) * ONE / zoom;
        // Adjacent samples either copy a packed byte, straddle two bytes,
        // or duplicate one nibble. Compile that choice once for all rows.
        int kind = a == b ? 2 + (a & 1) : a & 1;
        operations[x] = (a >> 1) | (kind << 6);
    }
    unsigned at=0;
    for(unsigned kind=0;kind<4;++kind){
        unsigned first=at;
        for(unsigned x=0;x<64;++x)if((operations[x]>>6)==kind)map.sample[at++]=(x<<6)|(operations[x]&63);
        map.count[kind]=at-first;
    }
    int split = 12;
    int lastSource = -1, lastDestination = 0;
    for (; split < 120; ++split) {
        int source = 12 + y0 + (split - 12) * ONE / zoom;
        if (source <= split) break;
        if (source == lastSource) copyZoomRow(gfx_fb + split * GFX_FB_STRIDE, gfx_fb + lastDestination * GFX_FB_STRIDE);
        else if (zoom == 384) stretchRow150(gfx_fb + split * GFX_FB_STRIDE, gfx_fb + source * GFX_FB_STRIDE, x0);
        else stretchRow(gfx_fb + split * GFX_FB_STRIDE, gfx_fb + source * GFX_FB_STRIDE, &map);
        lastSource = source; lastDestination = split;
    }
    lastSource = -1;
    for (int y = 119; y >= split; --y) {
        uint8_t *dst = gfx_fb + y * GFX_FB_STRIDE;
        int sourceY = 12 + y0 + (y - 12) * ONE / zoom;
        const uint8_t *source = gfx_fb + sourceY * GFX_FB_STRIDE;
        if (sourceY == lastSource) copyZoomRow(dst, gfx_fb + lastDestination * GFX_FB_STRIDE);
        else if (zoom == 384) stretchRow150(dst, source, x0);
        else stretchRow(dst, source, &map);
        lastSource = sourceY; lastDestination = y;
    }
}
static void elementSprite(SpriteId id, unsigned frame, int x, int y, uint8_t color, int scale = 256) {
    const SpriteAnimation &a = SPRITES[id];
    const uint8_t *data = a.frames[frame % a.count];
    // Sprite extents/scales are nonnegative Q8 sizes, even off-screen.
    int left = x - ((a.width * scale) >> 9), top = y - ((a.height * scale) >> 9);
    if (left >= clipX + clipW || top >= clipY + clipH || left + ((data[0] * scale) >> 8) <= clipX ||
        top + ((data[1] * scale) >> 8) <= clipY) return;
    uint8_t remap[16]; for (unsigned i = 0; i < 16; ++i) remap[i] = i;
    remap[8] = color;
    sprite4(data, left, top, remap, scale);
}
static void bats(int left, int right, int y, int length) {
    GuideRail guides[4];
    unsigned n = flipperGuides(left, right, y, y == table.h.height - 25, guides);
    for (unsigned i = 0; i < n; i += 2) {
        RailPoint path[3] = {{int16_t(guides[i].x),int16_t(guides[i].y)},
            {int16_t(guides[i].u),int16_t(guides[i].v)}, {int16_t(guides[i+1].u),int16_t(guides[i+1].v)}};
        railRun(path,3,GOLD);
    }
    int py = sy(y);
    if (py < clipY - 20 || py >= clipY + clipH + 20) return;
    for (unsigned side = 0; side < 2; ++side) {
        int x = side ? right : left;
        const FlipperPose &pose = FLIPPER_POSES[side][flipperPoseIndex(side ? game.right : game.left)];
        int scale = length * 256 / 23;
        sprite4(pose.data, x - pose.ax * scale / 256, py - pose.ay * scale / 256, nullptr, scale);
    }
}
__attribute__((noinline)) static void sling(const Object &o,unsigned ticks,unsigned strength) {
    // Rasterize one handed shape, including its face lighting; cast shadows
    // always remain down/right in board space. Collision uses these same points.
    mirrorSling=o.group?0:o.x*2;
    int a=o.x,b=a-o.u,tip=o.y+22*o.v/27,bottom=o.y+o.v;
    for(int world=o.y;world<=bottom;++world) {
        int y=sy(world);if(y<12 || y>=120)continue;
        int t=world<tip?(world-o.y)*256/(tip-o.y):(bottom-world)*256/(bottom-tip);
        int edge=a+(b-a)*t/256;
        gfx_hline(mirrorSling?mirrorSling-a:edge,y,a-edge+1,PANEL);
    }
    RailPoint frame[3]={{int16_t(a),o.y},{int16_t(a),int16_t(bottom)},{int16_t(b),int16_t(tip)}};
    RailPoint band[5];Object right=o;right.group=1;
    int bend=rubberBend(ticks,strength);
    for(unsigned i=0;i<5;++i) {
        int x,y;rubberPoint(right,i*64,bend,x,y);band[i]={int16_t(x),int16_t(y)};
    }
    for(unsigned pass=0;pass<2;++pass) {
        railRun(frame,3,DIM,true,pass,pass+1);
        railRun(band,5,PINK,false,pass,pass+1);
    }
    mirrorSling=false;
}
static const uint8_t rampWidths[19] PB_SPRITE={6,6,5,4,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3};
static __attribute__((noinline)) void rampDeck(const RailPoint *path) {
    // Paint each cross-section once, including the flared throat and shadow.
    for(int offset=2;offset>=0;offset-=2)for(unsigned i=offset?2:1;i<19;++i) {
        int down=offset?3:0;
        // The open lip touches the felt: its shadow belongs underneath the
        // rising deck, never as a dark transverse step in front of the mouth.
        int y=sy(path[i-1].y)+down,v=sy(path[i].y)+down;
        if((y<clipY && v<clipY) || (y>=clipY+clipH && v>=clipY+clipH))continue;
        beam(path[i-1].x+offset,y,path[i].x+offset,v,
             (offset?GRID:DIM)|16,false,rampWidths[i-1]+offset);
    }
}
static __attribute__((noinline)) void drawRamp(const Object &o) {
    // A shallow metal pan rises from the felt; its open mouth and the
    // elevated track share one continuous, gradually narrowing rail run.
    RailPoint path[19];
    path[0]={o.x,int16_t(o.y+8)};path[1]={o.x,int16_t(o.y+4)};
    for (unsigned i=0;i<17;++i) {
        int x,y;rampPoint(o,i*16,x,y);
        path[i+2]={int16_t(x),int16_t(y)};
    }
    rampDeck(path);
    if (sy(o.y) >= -16 && sy(o.y) < 136)
        elementSprite(SPR_RAMP, 0, o.x, sy(o.y), CYAN);
    for (unsigned side = 0; side < 2; ++side) {
        for(unsigned i=0;i<19;++i)path[i].x+=(side?2:-1)*rampWidths[i];
        railRun(path,19,side ? SILVER : DIM,false,1);
    }
}
static void drawBalls(bool onRamp) {
    for (const Ball &b : game.balls) if (b.active && (b.ramp >= 0) == onRamp) {
        int x=b.x>>8,y=sy(b.y>>8);
        if(b.scooped && b.scoopTicks) {
            unsigned hold=b.scoopTicks;
            if(hold<27 && hold>8)continue;
            // Sink behind the hood, then emerge through the same mouth.
            int floor=y+2;
            if(hold>=27)y+=(hold-26)*2;
            else {x+=(b.vx>0?1:-1)*(8-int(hold));y+=(8-int(hold))*14/8;}
            int top=floor>clipY?floor:clipY;
            gfx_setClip(clipX,top,clipW,clipY+clipH>top?clipY+clipH-top:0);
        }
        elementSprite(SPR_BALL, 0, x, y, WHITE);
        gfx_setClip(clipX,clipY,clipW,clipH);
    }
}
static void drawRampMarkers() {
    static const int8_t bob[]={0,-1,-2,-1};
    for(unsigned i=0;i<table.h.count;++i)if(table.objects[i].kind==Ramp) {
        const Object &o=table.objects[i];
        elementSprite(SPR_RAMP,1,o.x-1,sy(o.y+4+bob[(game.ticks/10)&3]),CYAN);
    }
}
// Translate only the playfield, keeping score and warnings steady. A padded
// row handles half-byte shifts without per-pixel bounds checks.
RAMFUNC(pinballShake) static void shakePlayfield() {
    int dx=game.shakeX,dy=game.shakeY;if(!dx&&!dy)return;
    uint32_t storage[18]={};uint8_t *row=reinterpret_cast<uint8_t *>(storage);
    for(int n=0;n<108;++n) {
        int y=dy>0?119-n:12+n,source=y-dy;
        uint8_t *dst=gfx_fb+y*64;
        if(source<12||source>=120) {
            volatile uint32_t *d=reinterpret_cast<volatile uint32_t *>(dst);
            for(unsigned i=0;i<16;++i)d[i]=0;
        } else {
            const volatile uint32_t *src=reinterpret_cast<const volatile uint32_t *>(gfx_fb+source*64);
            for(unsigned i=0;i<16;++i)storage[i+1]=src[i];
            const uint8_t *p=row+4+((-dx)>>1);
            for(unsigned i=0;i<64;++i)dst[i]=(dx&1)?(p[i]>>4)|(p[i+1]<<4):p[i];
        }
    }
}
static uint8_t scoreColor(unsigned theme) {
    static const uint8_t colors[9] = {CYAN, CYAN, SILVER, GOLD, GOLD, PURPLE, PINK, GREEN, GOLD};
    return colors[theme];
}
// Two short edge pulses confined to the cabinet margins.
static void shakeImpact() {
    if(game.shakeTicks<=24)return;
    unsigned age=41-game.shakeTicks;
    if(age%12>=6)return;
    uint8_t c=age<6 ? WHITE : game.shakeLevel==SHAKE_LEVELS ? RED : GOLD;
    for(int x=0;x<=126;x+=126) {
        gfx_fillRect(x,14,2,25,c);gfx_fillRect(x,93,2,25,c);
        for(int y=49;y<=77;y+=14) {
            int a=x?125:2,tip=a+game.shakeDirection*2;
            gfx_line(a,y-3,tip,y,c);gfx_line(tip,y,a,y+3,c);
        }
    }
}
static int scoreWidth(const char *digits, int scale) { return (strlen(digits) * 8 - 1) * scale / 256; }
// Decode each theme's four-color, two-bit glyphs without changing their art.
// Cache the last glyph too, so an unchanged single-digit score costs no decode.
static void scoreGlyph(const uint8_t *packed,uint8_t *data) {
    static const uint8_t *previous;
    if(packed==previous)return;
    previous=packed;data[0]=7;data[1]=9;unsigned at=2;
    const uint8_t *palette=SCORE_PALETTES[table.h.theme];
    for(unsigned row=0;row<9;++row) {
        unsigned count=at++;data[count]=0;
#if SCORE_ROW_CODED
        unsigned bits=SCORE_ROWS[packed[row]];
        auto pixel=[&](unsigned x){return palette[(bits>>(x*2))&3];};
#else
        auto pixel=[&](unsigned x){unsigned p=row*7+x;return palette[(packed[p/4]>>((p&3)*2))&3];};
#endif
        for(unsigned x=0;x<7;) {
            unsigned color=pixel(x),n=1;
            while(x+n<7 && pixel(x+n)==color)++n;
            data[at++]=((n-1)<<4)|color;++data[count];x+=n;
        }
    }
}
static void scoreDigits(const char *digits, int x, int y, int scale, bool shadow, bool flash = false) {
    static uint8_t data[74];
    uint8_t remap[16];
    for (unsigned i = 0; i < 16; ++i) remap[i] = i;
    remap[8] = flash ? WHITE : scoreColor();
    uint8_t shade[16]; memset(shade, GRID, sizeof shade);
    for (unsigned i = 0; digits[i]; ++i) {
        const uint8_t *packed = SCORE_DIGITS[table.h.theme][digits[i] - '0'];
        scoreGlyph(packed,data);
        int dx = x + i * 8 * scale / 256;
        if (shadow) sprite4(data, dx + 1, y + 1, shade, scale);
        sprite4(data, dx, y, remap, scale);
    }
}
static bool popupClear() {
    // Fixed top anchor: multiball must never make an announcement jump.
    // Hide briefly if a ball crosses the full banner/shadow band instead.
    int x0 = 0, y0 = 0, width, height;
    if (game.zoom > ONE) zoomRegion(x0, y0, width, height);
    for (const Ball &b : game.balls) if (b.active && !b.shooter) {
        int x = (b.x / ONE - x0) * game.zoom / ONE + game.shakeX;
        int y = 12 + (b.y / ONE - game.camera - y0) * game.zoom / ONE + game.shakeY;
        if (x >= -8 && x <= 136 && y >= 4 && y < 58) return false;
    }
    return true;
}
static __attribute__((noinline)) void scorePopup() {
    if (!game.scorePopTicks) return;
    if(!popupClear())return;
    unsigned age = 36 - game.scorePopTicks;
    // Present the newly changed score first, then expand the celebration
    // once that HUD transfer has finished on the single-buffer display.
    if (age < 2) return;
    age -= 2;
    int scale = age < 8 ? 448 - age * 8 : 384;
    char digits[16]; fmtInt(digits, game.scorePopValue);
    const char *label = game.scorePopKind == 2 ? "LUCKY SCORE!" : "SCORE MILESTONE!";
    int w = scoreWidth(digits, scale), labelWidth = text35Width(label);
    int box = (w > labelWidth ? w : labelWidth) + 10;
    int y = 14 - age / 18;
    // Keep a separate label row, with a visible gap below its descenders.
    int h = 9 * scale / 256 + 15;
    gfx_fillRoundRect((128 - box) / 2, y, box, h, 3, PANEL);
    gfx_roundRect((128 - box) / 2, y, box, h, 3, scoreColor());
    scoreDigits(digits, (128 - w) / 2, y + 2, scale, true, game.scorePopTicks & 4);
    center(y + h - 9, label, GOLD);
}
static __attribute__((noinline)) void bonusPopup(unsigned bonus) {
    bool stuck=bonus==BonusStuck;
    // A stationary ball cannot leave the banner band to reveal its help.
    if(!stuck && !popupClear())return;
    static const char *const titles[]={"SAUCER BONUS", "KICKBACK!", "BONUS UP!",
        "DOUBLE SCORE!", "MULTIBALL~READY", "MULTIBALL!", "BALL SAVE", "SUPER JACKPOT!", "BALL STUCK!"};
    static const char *const details[]={"KEEP GOING!", "BALL SAVED", "", "BIG POINTS!",
        "SHOOT SCOOP!", "3 BALLS!", "", "BIG POINTS!", "> OR A SHAKE"};
    char detail[16];const char *first=titles[bonus-1],*second=details[bonus-1];
    bool lanes=bonus==BonusMultiplier && (game.bonusArg&128);
    if(lanes) {
        unsigned mask=game.bonusArg&7;
        unsigned count=(mask&1)+((mask>>1)&1)+((mask>>2)&1);
        static const char *const goals[]={"LIGHT A B C", "2 MORE LANES!", "1 MORE LANE!"};
        first=goals[count];
        if(game.multiplier>=5)second="BALL SAVE";
        else {strcpy(detail,"FOR X");fmtInt(detail+5,laneGoal());second=detail;}
    } else if(bonus==BonusBallSave || bonus==BonusMultiplier) {
        fmtInt(detail,game.bonusArg);
        strcat(detail,bonus==BonusBallSave?" SECONDS!":"X SCORING!");second=detail;
    }
    unsigned ticks=stuck?60:game.bonusTicks,age=BONUS_FRAMES-ticks;
    static const int8_t bounce[]={12,8,4,0,-2,-1,0};
    int offset=age<14?bounce[age/2]:ticks<10?10-ticks:0;
    int y=14-offset;
    uint8_t accent=scoreColor(),pulse=age&8?accent:GOLD;
    gfx_setClip(0,12,128,108);
    gfx_fillRoundRect(3,y+2,122,37,4,GRID);
    gfx_fillRoundRect(2,y,122,37,4,PANEL);
    gfx_roundRect(2,y,122,37,4,pulse);
    resultText(y+4,first,WHITE);
    // Reuse the playfield art, including its group ink and animation. Icons
    // live in screen space and stay readable while the playfield zooms.
    clipX=0;clipY=12;clipW=128;clipH=108;
    int textX=26;
    if(lanes) {
        for(unsigned g=0;g<3;++g)if(!(game.bonusArg&(1u<<g))) {
            elementSprite(SPR_LANE,0,textX-13,y+25,laneColors[g]);
            char letter[]={char('A'+g),0};text35(textX-14,y+23,letter,WHITE);
            textX+=14;
        }
        textX-=18;
    } else {
        static const uint8_t icons[]={SPR_SAUCER,SPR_KICKBACK,SPR_LANE,SPR_SCOOP,
            SPR_SCOOP,SPR_BALL,SPR_BALL,SPR_SCOOP,SPR_BALL};
        SpriteId icon=SpriteId(icons[bonus-1]);uint8_t color=accent;
        for(unsigned i=0;i<table.h.count;++i) {
            const Object &o=table.objects[i];
            if((icon==SPR_SCOOP && o.kind==Scoop) || (icon==SPR_SAUCER && o.kind==Saucer)) {
                color=laneColors[o.group];break;
            }
        }
        elementSprite(icon,game.ticks/8,14,y+22,color);
    }
    int detailX=60+(textX>>1)-text35Width(second);
    text35x2(detailX,y+19,second,accent);
    if(stuck) {
        // Fill the existing > font glyph into the console's solid D-pad icon.
        gfx_fillRect(detailX,y+21,2,6,accent);
        gfx_fillRect(detailX+2,y+23,2,2,accent);
    }
    for(unsigned i=0;i<4;++i) {
        int x=9+((i*31+age*2)%110);
        gfx_hline(x,y+1,3,WHITE);
    }
    gfx_resetClip();
}
static __attribute__((noinline)) void footer(const char *text,uint8_t color) {
    if(laneGroups()!=7){center(122,text,color);return;}
    for(unsigned g=0;g<3;++g) {
        bool lit=game.laneMask&(1u<<g);int x=1+g*5;char letter[]={char('A'+g),0};
        gfx_fillRect(x,121,5,7,lit?laneColors[g]:DIM);
        text35(x+1,122,letter,lit?PANEL:(game.ticks&16?laneColors[g]:WHITE));
    }
    text35(18+(110-text35Width(text))/2,122,text,color);
}
static __attribute__((noinline)) void borderSkins() {
    const BoardBorder &skin=BOARD_BORDERS[table.h.theme];
    uint8_t remap[16];for(unsigned i=0;i<16;++i)remap[i]=i;
    remap[8]=scoreColor();
    if(sy(34)>clipY && sy(-HEADER_HEIGHT)<clipY+clipH) {
        sprite4(skin.top,0,sy(6),remap);
        // The large theme crest rises from the roof on joined, shaded
        // brackets. Empty pixels expose the same felt as the playfield.
        RailPoint left[]={{23,8},{29,-5},{44,-5}},right[]={{84,-5},{92,-5},{98,8}};
        railRun(left,3,scoreColor());railRun(right,3,scoreColor());
        sprite4(skin.side,20,sy(-12),remap);
        sprite4(skin.side,96,sy(-12),remap);
        sprite4(skin.emblem,46,sy(-22),remap,768);
        // Fill the felt cheeks outside the sloping roof rails. At 16x11
        // pixels the skull, ghost, rocket, etc. remain legible on the LCD
        // and in Studio's full-table view; transparent edges follow the rail.
        sprite4(skin.emblem,0,sy(7),remap,352);
        sprite4(skin.emblem,112,sy(7),remap,352);
    }
    // Tile only visible world rows. Both the printed face and its shadow
    // remain registered to the actual cabinet rails at x=6 and x=124.
    int first=28;
    if(game.camera>44)first+=((game.camera-44)/32)*32;
    for(int world=first;world<table.h.height+6 && sy(world)<clipY+clipH;world+=32) {
        int y=sy(world);if(y+16<=clipY)continue;
        sprite4(skin.side,0,y,remap);
        // The right skin uses the same rail profile. Crop away its outer
        // ornaments so the plunger lane remains fully visible and clear.
        int start=clipX>122?clipX:122;
        int end=clipX+clipW<128?clipX+clipW:128;
        if(end>start){gfx_setClip(start,clipY,end-start,clipH);sprite4(skin.side,118,y,remap);}
        gfx_setClip(clipX,clipY,clipW,clipH);
    }
}
__attribute__((noinline)) void drawTable() {
    const int h = table.h.height;
    gfx_clear(BG);
    clipX = 0; clipY = 12; clipW = 128; clipH = 108;
    if (game.zoom > ONE) { zoomRegion(clipX, clipY, clipW, clipH); clipY += 12; }
    gfx_setClip(clipX, clipY, clipW, clipH);
    // Every visible shape is playfield hardware. No background illustrations.
    RailPoint cabinet[]={{6,int16_t(h+6)},{6,28},{23,8},{98,8},{124,32},{124,int16_t(h-8)}};
    railRun(cabinet,6,scoreColor());
    RailPoint shooter[]={{112,int16_t(h+6)},{112,58},{111,56}};
    railRun(shooter,3,SILVER);
    borderSkins();
    GuideRail flap=shooterFlapArm(game.shooterFlap);
    rail(flap.x,flap.y,flap.u,flap.v,SILVER);
    gfx_fillRoundRect(122,sy(41),4,4,1,GOLD);
    if(!(table.h.flags & EXPLICIT_RUBBERS))for(unsigned side=0;side<2;++side)
        sling(defaultRubber(side,h),game.rubberTicks[side],game.rubberStrength[side]);
    for(unsigned i=0;i<table.h.count;++i)if(table.objects[i].kind==Rubber)
        sling(table.objects[i],game.cooldown[i],game.elementState[i]);
    for (unsigned i = 0; i < table.h.count; ++i) {
        const Object &o = table.objects[i];
        int y = sy(o.y);
        if (o.kind == Ramp || o.kind == Rubber) continue;
        if (o.kind != Wall && o.kind != Gate && o.kind != Rubber && (y < -8 || y >= 140)) continue;
        uint8_t color = laneColors[o.group];
        bool flash = game.cooldown[i] && (game.cooldown[i] & 4);
        if (o.kind == Wall) rail(o.x, o.y, o.u, o.v, SILVER);
        else if (o.kind == Gate) {
            GuideRail arm=gateArm(o,game.elementState[i]);
            rail(arm.x,arm.y,arm.u,arm.v,GOLD);
            elementSprite(SPR_GATE,0,o.x,y,GOLD);
            gfx_fillRoundRect(o.u,sy(o.v)+1,3,3,1,GRID);
            gfx_fillRoundRect(o.u-1,sy(o.v)-1,3,3,1,SILVER);
            int dx=o.u-o.x,dy=o.v-o.y,len=root(dx*dx+dy*dy);
            if(len) {
                int nx=dy*gateDirection(o)*256/len,ny=-dx*gateDirection(o)*256/len;
                int x=(o.x+o.u)/2+nx*8/256,z=(o.y+o.v)/2+ny*8/256;
                if(o.group==2)for(unsigned bank=0;bank<3;++bank)
                    gfx_fillRect(x-4+int(bank)*3,sy(z),2,2,game.targetMask&(1u<<bank)?(bank==0?CYAN:bank==1?PINK:GOLD):DIM);
                else {
                    line(x-nx*2/256-dx*2/len,z-ny*2/256-dy*2/len,x+nx*2/256,z+ny*2/256,GOLD);
                    line(x-nx*2/256+dx*2/len,z-ny*2/256+dy*2/len,x+nx*2/256,z+ny*2/256,GOLD);
                }
            }
        }
        else if (o.kind == Flippers) bats(o.x, o.u, o.y, o.v);
        else if (o.kind == Bumper) {
            elementSprite(SPR_BUMPER, flash ? 1 : 0, o.x, y, color, (2 * o.u + 3) * 256 / 19);
        } else if (o.kind == Target || o.kind == DropTarget) {
            bool lit = game.targetMask & (1u << o.group);
            unsigned frame = o.kind == DropTarget && game.elementState[i] ? (game.cooldown[i] > 12 ? 1 : 2) : lit ? 1 : 0;
            elementSprite(o.kind == DropTarget ? SPR_DROP_TARGET : SPR_TARGET, frame, o.x, y, color);
        } else if (o.kind == Lane) {
            bool lit=game.laneMask&(1u<<o.group);
            if(!lit)gfx_circle(o.x,y,o.u+2,game.ticks&16?color:DIM);
            elementSprite(SPR_LANE,lit?1:0,o.x,y,color);
            char letter[]={char('A'+o.group),0};if(y>=14 && y<120)text35(o.x-1,y-2,letter,lit?PANEL:WHITE);
        } else if (o.kind == Scoop) elementSprite(SPR_SCOOP, game.targetMask == 7 ? 1 : 0, o.x, y, color);
        else if (o.kind == Spinner) elementSprite(SPR_SPINNER, game.elementState[i] ? game.ticks / 3 : 0, o.x, y, color);
        else if (o.kind == Kickback) elementSprite(SPR_KICKBACK, game.cooldown[i] ? 1 : game.elementState[i] ? 2 : 0, o.x, y, GREEN);
        else if (o.kind == Saucer) {
            // elementState counts completed awards: points, more points,
            // then ball save. Keep the metal bowl steady; only its lamp changes.
            static const uint8_t rewards[]={CYAN,GOLD,GREEN};
            elementSprite(SPR_SAUCER,0,o.x,y,rewards[game.elementState[i]]);
        }
    }
    bats(MAIN_LEFT, MAIN_RIGHT, h - 25, MAIN_LENGTH);
    drawBalls(false);
    // Elevated ramp rails occlude the moving hardware underneath them.
    // Keep this pass before zoom/shake so both views compose identically.
    for (unsigned i = 0; i < table.h.count; ++i)
        if (table.objects[i].kind == Ramp) drawRamp(table.objects[i]);
    // A captured rider is on the elevated surface, above its rails.
    drawBalls(true);
    // A floating direction marker remains above the passing rider.
    drawRampMarkers();
    // Fixed-power plunger: only its physical head is visible, no force bar.
    gfx_fillRoundRect(115, sy(h - 13), 6, 3, 1, SILVER);
    zoomPlayfield();
    shakePlayfield();
    gfx_resetClip();
    shakeImpact();
    gfx_fillRect(0, 0, 128, 12, PANEL);
    char num[16]; fmtInt(num, game.score);
    scoreDigits(num, 3, 0, 256, false);
    text35(77, 3, "X", GOLD); fmtInt(num, scoreMultiplier()); text35(82, 3, num, GOLD);
    text35(100, 3, "BALL", DIM); fmtInt(num, game.lives ? 4 - game.lives : 3); text35(120, 3, num, CYAN);
    gfx_hline(0, 10, 128, SILVER);
    gfx_fillRect(0, 120, 128, 8, PANEL);
    for(unsigned i=0;i<SHAKE_LEVELS;++i) gfx_fillRect(66+i*3,9-i*2,2,i*2+1,
        game.tilt>=3 ? RED : game.nudgeCooldown && i<game.shakeLevel ? (game.shakeLevel==SHAKE_LEVELS ? RED : CYAN) : DIM);
    if(game.tilt>=3) center(122,"TILT - WAIT FOR DRAIN",RED);
    else if(game.shakeTicks) {
        uint8_t c=game.shakeLevel==SHAKE_LEVELS ? RED : game.shakeLevel==2 ? ORANGE : GOLD;
        for(unsigned i=0;i<SHAKE_LEVELS;++i)gfx_fillRect(3+i*9,122,6,5,i<game.shakeLevel?c:DIM);
        text35(39,122,game.shakeLevel==SHAKE_LEVELS?"DANGER":"SHAKE",c);
        text35(71,122,game.shakeDirection<0?"<<<":">>>",WHITE);
        fmtInt(num,game.shakeLevel);text35(101,122,num,WHITE);text35(105,122,"/3",SILVER);
    }
    else if (messageTicks) footer(message,game.targetMask == 7 ? GOLD : CYAN);
    else if (game.modeTicks) footer(activeBalls() > 1 ? "MULTIBALL - SCOOP JACKPOT" : "POWER RUN: DOUBLE SCORE",GOLD);
    else if (game.ballSave && (game.ticks & 32)) footer("BALL SAVE ACTIVE",GREEN);
    else if(laneGroups()==7) {
        char hint[24]="LANES: 3 LEFT >X";hint[7]='0'+3-laneCount();
        if(game.multiplier>=5)strcpy(hint+14,"SAVE");else fmtInt(hint+16,laneGoal());
        footer(hint,GOLD);
    } else footer("LEFT/B FLIP A/RIGHT SHAKE",DIM);
    unsigned bonus=game.stuck && !game.paused?BonusStuck:game.bonusTicks?game.bonus:BonusNone;
    if(bonus)bonusPopup(bonus);else scorePopup();
}

static void thumbnail(const Table &t) {
    const int x = 10, y = 43, w = 43, h = 66;
    auto px = [&](int value) { return x + value * w / 128; };
    auto py = [&](int value) { return y + value * h / t.h.height; };
    gfx_fillRoundRect(x - 2, y - 2, w + 5, h + 5, 3, BG);
    gfx_roundRect(x, y, w, h, 4, METAL); gfx_vline(x + w - 5, y + 8, h - 8, DIM);
    for (unsigned i = 0; i < t.h.count; ++i) {
        const Object &o = t.objects[i]; int a = px(o.x), b = py(o.y);
        uint8_t color = o.group == 0 ? CYAN : o.group == 1 ? PINK : GOLD;
        if (o.kind == Wall || o.kind == Gate) gfx_line(a, b, px(o.u), py(o.v), SILVER);
        else if (o.kind == Ramp) {
            int x = o.x, y = o.y;
            for (unsigned t = 32; t <= 256; t += 32) { int u,v; rampPoint(o,t,u,v); gfx_line(px(x),py(y),px(u),py(v),GOLD);x=u;y=v; }
        }
        else if (o.kind == Flippers) {
            gfx_line(a, b, px(o.x + o.v), b + 2, WHITE);
            gfx_line(px(o.u), b, px(o.u - o.v), b + 2, WHITE);
        } else if (o.kind == Bumper) { gfx_fillCircle(a, b, 3, METAL); gfx_fillCircle(a, b, 2, color); }
        else if (o.kind == Target || o.kind == DropTarget) gfx_fillRect(a - 1, b - 1, 3, 2, color);
        else if (o.kind == Lane) gfx_pixel(a, b, color);
        else if (o.kind == Scoop) { gfx_fillCircle(a, b, 3, WHITE); gfx_fillCircle(a, b, 1, BG); }
        else if (o.kind == Saucer) { gfx_circle(a,b,3,PINK);gfx_pixel(a,b,WHITE); }
        else if (o.kind == Spinner) gfx_line(a-2,b-2,a+2,b+2,CYAN);
        else if (o.kind == Kickback) gfx_fillRect(a-1,b-2,3,5,GREEN);
    }
    gfx_line(px(MAIN_LEFT), y + h - 5, px(MAIN_LEFT + MAIN_LENGTH), y + h - 3, WHITE);
    gfx_line(px(MAIN_RIGHT), y + h - 5, px(MAIN_RIGHT - MAIN_LENGTH), y + h - 3, WHITE);
}
void drawLibrary(unsigned selected, bool playing, bool previewReady) {
    gfx_clear(BG);
    center(3, "MIDNIGHT PINBALL - CHOOSE", CYAN);
    gfx_hline(4, 11, 120, METAL);
    const Table &t = previewData();
    char title[20];
    const char *name = previewReady ? t.h.title : "INVALID TABLE";
    unsigned length = 0;
    while (name[length] && length < 19) { char c = name[length]; title[length++] = c >= 'a' && c <= 'z' ? c - 32 : c; }
    title[length] = 0;
    if (length <= 15) text35x2s((128 - text35x2Width(title)) / 2, 19, title, WHITE, PANEL);
    else {
        unsigned split = 14; while (split && title[split] != ' ') --split;
        if (!split) split = 14;
        char rest[20]; strcpy(rest, title + split + (title[split] == ' ')); title[split] = 0;
        text35x2(4, 15, title, WHITE); text35x2(4, 29, rest, WHITE);
    }
    panel(5, 38, 54, 76, 3, PANEL, METAL);
    if (previewReady) thumbnail(t);
    // Use the selected preview's theme, even while another board is suspended.
    if(previewReady) {
        uint8_t remap[16];for(unsigned i=0;i<16;++i)remap[i]=i;
        remap[8]=scoreColor(t.h.theme);
        sprite4(BOARD_BORDERS[t.h.theme].emblem,70,41,remap,1024);
    }
    const char *source=selected ? "SD TABLE" : "BUILT IN";
    text35(94-text35Width(source)/2,90,source,CYAN);
    unsigned bumpers = 0, tiers = 1;
    if (previewReady) for (unsigned i = 0; i < t.h.count; ++i) {
        if (t.objects[i].kind == Bumper) ++bumpers;
        if (t.objects[i].kind == Flippers) ++tiers;
    }
    char num[16]; fmtInt(num, bumpers); text35(65, 98, num, GOLD); text35(73, 98, "BUMPERS", SILVER);
    fmtInt(num, tiers); text35(65, 106, num, GOLD); text35(73, 106, "TIERS", SILVER);
    fmtInt(num, selected + 1); char *end = fmtStr(num + strlen(num), "/"); fmtInt(end, libraryCount);
    text35x2(94-text35x2Width(num)/2,77,num,WHITE);
    text35(64,80,"<",CYAN);text35(121,80,">",CYAN);
    center(116, previewReady ? "A PLAY   B RESUME" : cardStatus, previewReady ? GOLD : RED);
    center(123, "SELECT RESCAN SD", SILVER);
    (void)playing;
}
void drawPause(bool sound) {
    dither(0, 12, 128, 108, BG, 0);
    panel(8, 32, 112, 65, 3, PANEL, PURPLE);
    text35x2(40, 38, "PAUSE", WHITE); center(55, "A / START RESUME", CYAN);
    center(68, sound ? "B SOUND ON" : "B SOUND OFF", GOLD); center(81, "SELECT TABLE LIBRARY", DIM);
}
static void resultScore(int y,uint32_t value) {
    char digits[16];fmtInt(digits,value);
    scoreDigits(digits,(128-scoreWidth(digits,384))/2,y,384,true);
}
void drawGameOver(uint32_t best) {
    panel(3,14,122,112,4,PANEL,scoreColor());
    resultText(20,"GAME OVER",WHITE);
    resultText(35,"SCORE",SILVER);resultScore(48,game.score);
    resultText(66,"BEST",SILVER);resultScore(79,best);
    resultText(99,"A RETRY",WHITE);
    resultText(112,"SELECT TABLES",CYAN);
}
}  // namespace pinball
