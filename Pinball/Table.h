#pragma once
#include <stdint.h>
#include <stddef.h>
#include <Fat.h>

namespace pinball {
constexpr unsigned MAX_OBJECTS = 72;
constexpr unsigned MAX_TABLES = 96;
enum Kind : uint8_t { Wall, Bumper, Target, Lane, Scoop, Flippers,
    Ramp, Spinner, DropTarget, Kickback, Gate, Saucer, Rubber, KIND_COUNT };

constexpr uint8_t EXPLICIT_RUBBERS = 1; // Otherwise retain the legacy cabinet pair.

// PBT1 is explicitly little endian, with no compiler-dependent padding.
// Wire sizes stay fixed; aligned storage lets the MCU load 16/32-bit fields
// directly instead of reconstructing every value from individual bytes.
struct __attribute__((packed,aligned(4))) TableHeader {
    char magic[4];
    uint8_t version, theme, count, flags;
    uint16_t height, gravity;
    uint32_t id, checksum;
    char title[20], mission[24];
    uint16_t palette[16];
};
struct __attribute__((packed,aligned(4))) Object {
    uint8_t kind, group;
    int16_t x, y, u, v;
    uint16_t value;
};
struct Table { TableHeader h; Object objects[MAX_OBJECTS]; };
static_assert(sizeof(TableHeader) == 96 && sizeof(Object) == 12, "PBT1 wire layout");
static_assert(offsetof(Table,objects)==96 && offsetof(TableHeader,palette)==64 &&
              offsetof(Object,x)==2 && offsetof(Object,value)==10, "PBT1 wire offsets");
struct Entry { char name[12]; };  // name[11]: PINBALL folder flag

extern Table table;
extern Entry library[MAX_TABLES];
extern uint8_t libraryCount;
extern bool libraryFull;
extern const char *cardStatus;
void builtinTable(Table &out);
bool validTable(const Table &t, unsigned size);
void scanTables();
// The current table is assigned only after a complete, validated read.
bool loadTable(unsigned index);
bool previewTable(unsigned index);
const Table &previewData();
Table &editData();  // Reuse the existing staging table; no second RAM copy.
}  // namespace pinball
