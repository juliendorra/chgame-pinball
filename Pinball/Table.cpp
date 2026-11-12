#include <CHGame.h>
#include <Fat.h>
#include <SdSpi.h>
#include <string.h>
#include "Table.h"
#include "Builtin.h"

namespace pinball {
Table table;
Entry library[MAX_TABLES];
uint8_t libraryCount;
bool libraryFull;
static constexpr const char *noCard = PINBALL_SD_BOARDS ? "INSERT SD CARD" : "NO SD - BUILT-IN READY";
const char *cardStatus = noCard;
static Table pending;
// One unsigned comparison preserves both bounds, including negative inputs.
static bool within(int value,int low,int high) { return unsigned(value-low)<=unsigned(high-low); }
static __attribute__((noinline)) bool validLabel(const char *p,unsigned n) {
    while(n-- && *p)if(!within(*p++,32,126))return false;
    return true;
}

#if !PINBALL_SD_BOARDS
void builtinTable(Table &out) {
    memset(&out, 0, sizeof out);
    memcpy(&out, BUILTIN, sizeof BUILTIN);
}
#endif

void initialTable() {
#if PINBALL_SD_BOARDS
    memcpy(table.h.palette, MENU_PALETTE, sizeof MENU_PALETTE);
#else
    builtinTable(table);
#endif
}

bool validTable(const Table &t, unsigned size) {
    const TableHeader &h = t.h;
    if (memcmp(h.magic, "PBT1", 4) || h.version != 1 || (h.flags & ~EXPLICIT_RUBBERS) || h.theme > 8 ||
        h.count > MAX_OBJECTS || !within(h.height,256,480) ||
        !within(h.gravity,8,44) || !h.id ||
        size != sizeof(TableHeader) + h.count * sizeof(Object)) return false;
    if (!h.title[0] || h.title[19] || h.mission[23]) return false;
    if(!validLabel(h.title,19) || !validLabel(h.mission,23))return false;
    for (unsigned i = 0; i < 16; ++i) if (h.palette[i] > 0xFFF) return false;
    uint32_t hash = 2166136261u;
    const uint8_t *p = reinterpret_cast<const uint8_t *>(&t);
    for (unsigned i = 0; i < size; ++i) hash = (hash ^ (i >= 16 && i < 20 ? 0 : p[i])) * 16777619u;
    if (hash != h.checksum) return false;
    uint8_t groups = 0, lanes = 0;
    bool scoop = false;
    for (unsigned i = 0; i < h.count; ++i) {
        const Object &o = t.objects[i];
        if (o.kind >= KIND_COUNT || o.group > 2 || !within(o.x,5,108) ||
            !within(o.y,8,h.height-50) || o.value > 10000) return false;
        if (o.kind == Wall || o.kind == Gate) {
            if (!within(o.u,5,110) || !within(o.v,8,h.height-40) ||
                (o.x == o.u && o.y == o.v)) return false;
        } else if (o.kind == Flippers) {
            if (!within(o.x,20,38) || !within(o.u,82,100) ||
                !within(o.v,16,26) || o.y < 80 || o.x + 2 * o.v + 16 > o.u) return false;
        } else if (o.kind == Ramp) {
            if (!within(o.u,8,105) || !within(o.v,12,h.height-50) ||
                (o.y > o.v ? o.y - o.v : o.v - o.y) < 32) return false;
        } else if (o.kind == Target || o.kind == DropTarget) {
            if (!within(o.u,3,12) || !within(o.v,3,12)) return false;
            groups |= 1u << o.group;
        } else if (o.kind == Rubber) {
            if (!(h.flags & EXPLICIT_RUBBERS) || o.group > 1 || !within(o.u,8,24) ||
                !within(o.v,16,40) || !within(o.x + (o.group ? -o.u : o.u),8,108) ||
                o.y + o.v > h.height-8) return false;
        } else if (o.kind == Spinner) {
            if (!within(o.u,6,16)) return false;
        } else {
            if (!within(o.u,3,12) || !within(o.v,0,1600)) return false;
            if (o.kind == Lane) lanes |= 1u << o.group;
            if (o.kind == Scoop) scoop = true;
        }
    }
    return true;  // Incomplete missions are editable/playable; the editor warns.
}

static bool collect(const char *name, const fat::File &, bool dir, void *ctx) {
    if (dir || memcmp(name + 8, "PBT", 3)) return true;
    if (libraryCount == MAX_TABLES) { libraryFull = true; return false; }
    Entry &e = library[libraryCount++];
    memcpy(e.name, name, 11);
    e.name[11] = ctx ? 1 : 0;
    return true;
}

void scanTables() {
    gfx_wait();
    libraryFull = false;
#if PINBALL_SD_BOARDS
    constexpr unsigned firstSD = 0;
#else
    constexpr unsigned firstSD = 1;
    memset(&library[0], 0, sizeof(Entry));
    memcpy(library[0].name, "NEON    PBT", 11);
#endif
    libraryCount = firstSD;
    uint8_t *buf = gfx_chunkScratch();
    if (!sd::init()) { cardStatus = noCard; return; }
    int8_t err = fat::mount(buf);
    if (err) { cardStatus = err == fat::E_EXFAT ? "USE A FAT32 CARD" : "FAT READ FAILED"; return; }
    fat::File dir;
    if (fat::root(dir) || fat::list(dir, collect, nullptr, buf)) {
        libraryCount = firstSD; cardStatus = "SD READ FAILED"; return;
    }
    err = fat::folder("PINBALL    ", dir, buf);
    if (err != fat::E_NOTFOUND && (err || fat::list(dir, collect, &dir, buf))) {
        libraryCount = firstSD; cardStatus = "SD READ FAILED"; return;
    }
    cardStatus = libraryFull ? "96 TABLE LIMIT REACHED" :
        libraryCount > firstSD ? "SD TABLES READY" : "ADD PINBALL/*.PBT TO SD";
}

bool previewTable(unsigned index) {
    if (index >= libraryCount) return false;
    gfx_wait();
#if !PINBALL_SD_BOARDS
    if (!index) { builtinTable(pending); return true; }
#endif
    uint8_t *buf = gfx_chunkScratch();
    // Re-find by name on the freshly mounted volume: cached clusters must
    // never be trusted after an SD swap, even for a same-sized replacement.
    if (!sd::init() || fat::mount(buf)) { cardStatus = "RESEAT SD / READ ERROR"; return false; }
    fat::File f, dir;
    // The directory flag occupies name's NUL byte, never passed to FAT.
    int8_t err = library[index].name[11] ?
        (fat::folder("PINBALL    ", dir, buf) ? fat::E_NOTFOUND :
         fat::match(dir, library[index].name, 0, f, nullptr, buf)) :
        fat::find(library[index].name, f, buf);
    if (err) { cardStatus = "MISSING TABLE - SCAN"; return false; }
    if (f.size < 96 || f.size > sizeof pending) { cardStatus = "BAD TABLE SIZE"; return false; }
    fat::Run runs[8];
    int8_t n = fat::runs(f, runs, 8, buf);
    if (n <= 0) { cardStatus = "READ / FRAGMENT ERROR"; return false; }
    memset(&pending, 0, sizeof pending);
    for (unsigned offset = 0; offset < f.size; offset += 512) {
        if (!fat::read(runs, n, offset / 512, buf)) { cardStatus = "RESEAT SD / READ ERROR"; return false; }
        unsigned bytes = f.size - offset;
        if (bytes > 512) bytes = 512;
        memcpy(reinterpret_cast<uint8_t *>(&pending) + offset, buf, bytes);
    }
    if (!validTable(pending, f.size)) { cardStatus = "BAD TABLE / CHECKSUM"; return false; }
    cardStatus = "SD TABLE LOADED";
    return true;
}
const Table &previewData() { return pending; }
Table &editData() { return pending; }
bool loadTable(unsigned index) {
    if (!previewTable(index)) return false;
    table = pending;
    return true;
}
}  // namespace pinball
