// MIDNIGHT PINBALL: original, SD-loadable tables for CHGame Rev0.
#include <CHGame.h>
#include <CHSave.h>
#include <Fat.h>
#include <string.h>
#include "Table.h"
#include "Physics.h"
#include "Render.h"
#include "Autoplay.h"
#include "Live.h"
#include "Elements.h"
#include "src/rumble/Rumble.h"

using namespace pinball;
#ifdef CHSIM
void sim_cardEject(bool out);
#endif
namespace {
enum Screen : uint8_t { Library, Play };
Screen screen = Library;
uint8_t selected = 0;
bool playing = false, resultSaved = false;
bool previewReady = false;
int previewIndex = -1;
struct Record { uint32_t id, score; };
constexpr unsigned BankSize = MAX_TABLES / 2;
struct Bank {
    Record records[BankSize];
    uint8_t soundOff, reserved[3];
    // Store the high words separately to keep the scores word aligned.
    uint16_t idHigh[BankSize];
};
constexpr chsave::Id BANKS[] = {chsave::id("com.juliendorra.pinball.v2.scores-a"),
                                 chsave::id("com.juliendorra.pinball.v2.scores-b")};
static_assert(sizeof(Bank) == 484, "score file layout");
static_assert(sizeof(Bank)<=chsave::MAX_DATA, "one sector per journal slot");
static uint64_t scoreBoard;
static uint32_t bestScore;
static bool muted;
static chsave::Store scoreSaves;

#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC push_options
#pragma GCC optimize("Oz")
#endif

bool readBank(unsigned index, Bank &out) {
    const auto &id = BANKS[index];
    if (scoreSaves.load(id, 1, &out, sizeof out)) return true;
    if (scoreSaves.status() != chsave::Status::Empty) return false;
    memset(&out, 0, sizeof out);
    return true;
}
enum ScoreAction { Read, SaveScore, SaveSettings };
void accessScores(ScoreAction action) {
    Bank bank;
    const uint32_t low = uint32_t(scoreBoard);
    const uint16_t high = scoreBoard >> 32;
    for (unsigned i = 0; i < 2; ++i) {
        if (!readBank(i, bank)) break;
        if (action == SaveSettings) {
            bank.soundOff = muted;
            if (scoreSaves.store(BANKS[i], 1, bank)) return;
            break;
        }
        if (action == Read && !i) muted = bank.soundOff;
        unsigned slot = BankSize;
        uint32_t stored = 0;
        for (unsigned j = 0; j < BankSize; ++j) {
            uint32_t id = bank.records[j].id;
            uint16_t idHigh = bank.idHigh[j];
            if (id == low && idHigh == high) { slot = j; stored = bank.records[j].score; break; }
            if (!(id | idHigh) && slot == BankSize) slot = j;
        }
        // The second journal gets entries once the first is full. When
        // both are full, reuse the final slot for a newly added board.
        if (slot == BankSize && !i) continue;
        if (slot == BankSize) --slot;
        bestScore = stored;
        if (action == Read || game.score <= stored) return;
        bank.records[slot] = {low, game.score};
        bank.idHigh[slot] = high;
        if (scoreSaves.store(BANKS[i], 1, bank)) { bestScore = game.score; return; }
        break;
    }
    if (action != Read) announce("SD SAVE FAILED", 180);
}
void loadScores() {
    scoreBoard = table.boardId();
    bestScore = 0;
    accessScores(Read);
}
uint32_t best() { return bestScore; }
void storeSettings() { accessScores(SaveSettings); }
void remember() {
    if (scoreBoard && game.score > bestScore) accessScores(SaveScore);
}

#if defined(__GNUC__) && !defined(__clang__)
#pragma GCC pop_options
#endif

void palette(const Table &source = table) {
    uint16_t colors[16];
    memcpy(colors, source.h.palette, sizeof colors);
    // A shadow is the felt with each RGB444 component halved. Derive it
    // on load too, so a custom SD palette only needs to change the felt.
    colors[2] = (colors[0] >> 1) & 0x777;
    pal::init(colors);
    pal::setCycling(false);
}
void present() {
    // The LCD transfer costs 8 ms. Keep unchanged score/message bars on the
    // panel instead of retransmitting them during every camera animation.
    static uint32_t previousTop, previousBottom;
    if (screen != Play || game.paused || game.over) { previousTop = previousBottom = 0; gfx_flushAsync(); return; }
    uint32_t top = 2166136261u, bottom = 2166136261u;
    const uint32_t *words = reinterpret_cast<const uint32_t *>(gfx_fb);
    for (unsigned i = 0; i < 12 * GFX_FB_STRIDE / 4; ++i) top = (top ^ words[i]) * 16777619u;
    for (unsigned i = 120 * GFX_FB_STRIDE / 4; i < 128 * GFX_FB_STRIDE / 4; ++i)
        bottom = (bottom ^ words[i]) * 16777619u;
    int y = top == previousTop ? 12 : 0;
    int end = bottom == previousBottom ? 120 : 128;
    gfx_flushRectAsync(0, y, 128, end - y);
    previousTop = top; previousBottom = bottom;
}
void beginTable() {
    // Keep the old score and table if a selected file fails to load.
    // Saving happens before the loader's transaction replaces its id.
    if (playing) remember();
    if (!loadTable(selected)) return;
    if (scoreBoard != table.boardId()) loadScores();
    palette();
    newGame();
    audio::setOn(!muted);
    screen = Play;
    playing = true;
    resultSaved = false;
}

#if CHGAME_DEBUG
#ifdef CHSIM
struct Timing { uint32_t update, total, wait; } timing;
#endif
void stat(const char *name, int32_t value) { char n[16]; dbg::print(name); fmtInt(n, value); dbg::print(n); }
#ifndef CHSIM
__attribute__((optimize("Oz")))
#endif
bool debugCommand(char cmd, const char *args) {
    if (cmd == '@') return live::command(args);
#ifdef CHSIM
    if (cmd == 'U') {
        stat("TIME update=", timing.update); stat(" total=", timing.total); stat(" wait=", timing.wait);
        dbg::print("\n"); timing = {}; return true;
    }
#endif
    if (cmd == 'V') {
        // One shared serializer keeps the real-device diagnostic build small.
        const int32_t values[] = {
            int32_t(screen), int32_t(libraryCount), int32_t(table.h.id),
            int32_t(table.h.height), int32_t(table.h.count), int32_t(game.score),
            int32_t(best()), int32_t(activeBalls()), int32_t(game.lives),
            int32_t(game.over), int32_t(game.paused), int32_t(game.camera),
            int32_t(game.left), int32_t(game.right), int32_t(game.launchHeld),
            int32_t(game.targetMask), int32_t(game.rubberTicks[0]), int32_t(game.rubberTicks[1]),
            int32_t(game.modeTicks), int32_t(game.ticks), int32_t(game.balls[0].x / ONE),
            int32_t(game.balls[0].y / ONE),
#ifdef CHSIM
            int32_t(selected), int32_t(game.balls[0].x), int32_t(game.balls[0].y),
            int32_t(game.balls[0].vx),
#endif
            int32_t(game.balls[0].vy), int32_t(game.balls[0].shooter), int32_t(game.balls[0].launching),
            int32_t(game.zoom), int32_t(game.rampCamera), int32_t(game.scorePopValue),
            int32_t(game.scorePopTicks), int32_t(game.scorePopKind), int32_t(game.balls[0].ramp),
#ifdef CHSIM
            int32_t(game.ballSave), int32_t(game.laneMask), int32_t(game.multiplier),
            int32_t(game.tilt), int32_t(audio::on()), int32_t(game.balls[0].scoopTicks),
            int32_t(game.zoomTicks), int32_t(game.hits), int32_t(game.metrics.ramps),
            int32_t(game.metrics.spinners), int32_t(game.metrics.drops), int32_t(game.metrics.kickbacks),
            int32_t(game.metrics.saucers),
            game.shakeLevel, game.nudgeCooldown, game.shakeTicks, game.shakeX, game.shakeY, game.shakeDirection,
#endif
            int32_t(game.metrics.searches),
#ifdef CHSIM
            table.h.idHigh,
#endif
        };
#ifdef CHSIM
        const char *names =
            "screen\0" "tables\0" "id\0"
            "height\0" "objects\0" "score\0"
            "best\0" "balls\0" "lives\0"
            "over\0" "paused\0" "camera\0"
            "left\0" "right\0" "launch_held\0"
            "target\0" "rubber_left\0" "rubber_right\0"
            "mode\0" "ticks\0" "x\0"
            "y\0"
#ifdef CHSIM
            "selected\0" "xq\0" "yq\0"
            "vx\0"
#endif
            "vy\0" "shooter\0" "launching\0"
            "zoom\0" "ramp_camera\0" "pop\0"
            "pop_ticks\0" "pop_kind\0" "ramp\0"
#ifdef CHSIM
            "save\0" "lanes\0" "mult\0"
            "tilt\0" "sound\0" "hold\0"
            "zoom_ticks\0" "hits\0" "ramps\0"
            "spinners\0" "drops\0" "kickbacks\0"
            "saucers\0" "shake_level\0" "shake_window\0" "shake_ticks\0" "shake_x\0" "shake_y\0" "shake_direction\0"
#endif
            "searches\0" "id_high\0"
            ;
        dbg::print("PIN");
        for(int32_t value:values) {
            char label[20];label[0]=' ';unsigned n=1;
            while(*names)label[n++]=*names++;
            ++names;label[n++]='=';label[n]=0;stat(label,value);
        }
#else
        // Numeric field order is decoded by verify_device.py. Avoid keeping
        // verbose diagnostic labels in the handheld's limited flash.
        dbg::print("PIN");for(int32_t value:values)stat(" ",value);
#endif
#ifdef CHSIM
        stat(" rumble=",rumble::level());stat(" rumble_ms=",rumble::remaining());
#endif
        dbg::print("\n");return true;
    }
    if (cmd == 'F') {
        selected = dbg::parseNum(args, 10);
        if (selected >= libraryCount) selected = 0;
        beginTable(); return true;
    }
    if (cmd == 'J') {
        // Debug-only ball placement: J x,y,vx,vy (velocity Q8 px/frame).
        int values[4] = {};
        for (unsigned i = 0; i < 4; ++i) {
            bool negative = *args == '-'; if (negative) ++args;
            while (*args >= '0' && *args <= '9') values[i] = values[i] * 10 + *args++ - '0';
            if (negative) values[i] = -values[i];
            if (*args == ',') ++args;
        }
        // Bound the injection too: stress tests cannot overflow the solver.
        if (values[0] < 0 || values[0] > 127 || values[1] < 0 || values[1] > table.h.height + 10 ||
            values[2] < -2600 || values[2] > 2600 || values[3] < -2600 || values[3] > 2600) return false;
        placeBall(0, values[0], values[1], values[2], values[3]); return true;
    }
    if (cmd == 'Z') { game.ballSave = 0; return true; }
    if (cmd == 'M') {
        while(*args==' ')++args;
        bool minus=*args=='-';if(minus)++args;
        unsigned row=dbg::parseNum(args,10);
        if (row > unsigned(minus ? HEADER_HEIGHT : table.h.height - 108)) return false;
        game.camera = minus ? -int(row) : int(row); return true;
    }
    if (cmd == 'O') {
        unsigned points = dbg::parseNum(args, 10);
        if (points > 1000000) return false;
        addScore(points); return true;
    }
#ifdef CHSIM
    if(cmd=='G') {
        unsigned index=dbg::parseNum(args,10);
        if(index>=table.h.count || table.objects[index].kind!=Gate)return false;
        const Object &o=table.objects[index];GuideRail arm=gateArm(o,game.elementState[index]);
        stat("GATE angle=",game.elementState[index]);stat(" x=",arm.x);stat(" y=",arm.y);
        stat(" u=",arm.u);stat(" v=",arm.v);dbg::print("\n");return true;
    }
    if(cmd=='H') {
        Serial.print("OVERVIEW ");Serial.println((table.h.height+HEADER_HEIGHT)*64+32);
        drawOverview([](const uint8_t *p,unsigned n,void *){Serial.write(p,n);},nullptr);
        if(game.over)drawGameOver(best());else if(game.paused)drawPause(!muted);
        gfx_flush();return true;
    }
    if (cmd == 'I') {
        // Isolated collision probe, simulator only: side,level,previous,
        // length,xQ8,yQ8,vx,vy. No table rails or frame update intervene.
        int v[8] = {};
        for (unsigned i=0;i<8;++i) {
            bool minus=*args=='-';if(minus)++args;
            while(*args>='0'&&*args<='9')v[i]=v[i]*10+*args++-'0';
            if(minus)v[i]=-v[i];if(*args==',')++args;
        }
        if(v[0]<0||v[0]>1||v[1]<0||v[1]>255||v[2]<0||v[2]>255||v[3]<16||v[3]>26||
           v[4]<-10000||v[4]>10000||v[5]<-10000||v[5]>10000||v[6]<-2600||v[6]>2600||v[7]<-2600||v[7]>2600)return false;
        game.balls[0]={64*ONE+v[4],200*ONE+v[5],v[6],v[7],true,false,false,0};
        collideFlipper(game.balls[0],64,200,v[3],v[0],v[1],v[2]);return true;
    }
    if (cmd == 'E') { sim_cardEject(dbg::parseNum(args, 10) != 0); return true; }
    if (cmd == 'Y') {
        unsigned values[3] = {};
        for (unsigned i = 0; i < 3; ++i) {
            while (*args >= '0' && *args <= '9') values[i] = values[i] * 10 + *args++ - '0';
            if (*args == ',') ++args;
        }
        if (!values[0] || values[0] > 60000 || values[1] > 1000000 || values[2] > 2) return false;
        evaluateBoard(values[0], values[1], values[2]); return true;
    }
#endif
    if (cmd == 'W') {
        unsigned zoom = dbg::parseNum(args, 10);
        if (zoom < 256 || zoom > 448) return false;
        gfx_wait(); game.zoom = zoom; drawTable(); gfx_flush(); return true;
    }
    if (cmd == 'C') { game.targetMask = dbg::parseNum(args, 10) & 7; return true; }
    if (cmd == 'D') { gfx_wait(); scanTables(); rescanThemeArt(); if (selected >= libraryCount) selected = 0; return true; }
    return false;
}
#endif
}  // namespace

void pinball::live::invalidatePreview() { previewIndex=-1; }

void setup() {
    chgame.boot();
    dbg::begin("MPIN 1.4.16");
#if CHGAME_DEBUG
    dbg::hook = debugCommand;
#endif
    gfx_begin(GFX_DIV2, GFX_12BPP);
    initialTable();
#if PINBALL_SD_BOARDS
    scanTables();
    previewReady = loadTable(0);
    previewIndex = 0;
#endif
    palette();
    loadScores();
    audio::begin(nullptr, 0, !muted);
    rumble::begin();
#if !PINBALL_SD_BOARDS
    scanTables();
#endif
    chgame.setFrameRate(60);
}

void loop() {
    rumble::update();
    dbg::poll();live::poll();
    if (live::changed()) {
        gfx_wait();
        if (scoreBoard != table.boardId()) loadScores();
        palette();
        screen = Play;
        playing = true;
        resultSaved = false;
        previewIndex = -1;
    }
    if(screen==Library && live::busy())return;
    if (!chgame.nextFrame()) return;
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t totalStart = micros();
#endif
    chgame.pollButtons();
    live::sample(screen==Play);
    // Physics does not touch the framebuffer, so overlap it with the last
    // LCD transfer. UI, SD, palette and save transitions still wait first.
    if(screen!=Play || game.over || game.paused || (chgame.justPressedMask() & (SELECT_BUTTON | START_BUTTON)))gfx_wait();
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t updateStart = micros();
#endif
    dbg::markUpdateStart();
    if (screen == Library) {
        if ((chgame.repeat(UP_BUTTON) || chgame.repeat(LEFT_BUTTON)) && selected) --selected;
        if ((chgame.repeat(DOWN_BUTTON) || chgame.repeat(RIGHT_BUTTON)) && selected + 1 < libraryCount) ++selected;
        if (chgame.justPressed(SELECT_BUTTON)) {
            scanTables();
            rescanThemeArt();
            if (selected >= libraryCount) selected = 0;
            previewIndex = -1;
        }
        if (chgame.justPressed(B_BUTTON) && playing) { screen = Play; palette(); }
        else if (chgame.justPressed(A_BUTTON)) beginTable();
    } else {
        if (!live::busy() && chgame.justPressed(SELECT_BUTTON)) { screen = Library; previewIndex = -1; }
        else if (game.over) {
            if (!resultSaved) { remember(); resultSaved = true; }
            if (chgame.justPressed(A_BUTTON) || chgame.justPressed(DOWN_BUTTON)) { newGame(); resultSaved = false; }
        } else {
            if (chgame.justPressed(START_BUTTON) || (game.paused && chgame.justPressed(A_BUTTON))) {
                game.paused = !game.paused;
                audio::setOn(!game.paused && !muted);
            } else if (game.paused && chgame.justPressed(B_BUTTON)) {
                muted = !muted;
                storeSettings();
            } else updateGame(chgame.buttons(), chgame.justPressedMask(), chgame.justReleased(A_BUTTON | DOWN_BUTTON) ?
                             (A_BUTTON | DOWN_BUTTON) : 0);
        }
    }
    if (screen == Library && previewIndex != selected) {
        previewReady = previewTable(selected);
        previewIndex = selected;
        if (previewReady) palette(previewData());
    }
    audio::update();
    if (screen != Play || game.paused || live::busy()) rumble::stop();
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t updateTime = micros() - updateStart;
    if (updateTime > timing.update) timing.update = updateTime;
#endif
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t waitStart=micros();
#endif
    gfx_wait();
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t waitTime=micros()-waitStart;
    if(waitTime>timing.wait)timing.wait=waitTime;
#endif
    dbg::markRenderStart();
    if (screen == Library) drawLibrary(selected, playing, previewReady);
    else {
        drawTable();
        if (game.over) drawGameOver(best());
        else if (game.paused) drawPause(!muted);
    }
    dbg::markRenderEnd();
    present();
#if CHGAME_DEBUG && defined(CHSIM)
    uint32_t totalTime = micros() - totalStart;
    if (totalTime > timing.total) timing.total = totalTime;
#endif
}
