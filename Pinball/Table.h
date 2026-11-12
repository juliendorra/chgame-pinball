#pragma once
#include <stdint.h>
#include <stddef.h>
#include <Fat.h>

#ifndef PINBALL_SD_BOARDS
#if defined(CHSIM)
#define PINBALL_SD_BOARDS 0
#else
#define PINBALL_SD_BOARDS 1
#endif
#endif

namespace pinball {
constexpr unsigned MAX_OBJECTS = 72;
constexpr unsigned MAX_TABLES = 96;
enum Kind : uint8_t { Wall, Bumper, Target, Lane, Scoop, Flippers,
    Ramp, Spinner, DropTarget, Kickback, Gate, Saucer, Rubber, KIND_COUNT };

constexpr uint8_t EXPLICIT_RUBBERS = 1; // Otherwise retain the legacy cabinet pair.

// PBT is explicitly little endian, with no compiler-dependent padding.
// Wire sizes stay fixed; aligned storage lets the MCU load 16/32-bit fields
// directly instead of reconstructing every value from individual bytes.
struct __attribute__((packed,aligned(4))) TableHeader {
    char magic[4];
    uint8_t version, theme, count, flags;
    uint16_t height, gravity;
    uint32_t id;
    uint16_t idHigh, reserved;
    uint32_t checksum;
    char title[20], mission[24];
    uint16_t palette[16];
};
struct __attribute__((packed,aligned(4))) Object {
    uint8_t kind, group;
    int16_t x, y, u, v;
    uint16_t value;
};
struct Table {
    TableHeader h;
    Object objects[MAX_OBJECTS];
    unsigned wireSize() const { return sizeof(h) + h.count * sizeof(Object); }
    uint64_t boardId() const { return (uint64_t(h.idHigh) << 32) | h.id; }
};
static_assert(sizeof(TableHeader) == 100 && sizeof(Object) == 12, "PBT2 wire layout");
static_assert(offsetof(Table,objects)==100 && offsetof(TableHeader,checksum)==20 &&
              offsetof(TableHeader,palette)==68 && offsetof(Object,x)==2 &&
              offsetof(Object,value)==10, "PBT2 wire offsets");
struct Entry { char name[12]; };  // name[11]: PINBALL folder flag

extern Table table;
extern Entry library[MAX_TABLES];
extern uint8_t libraryCount;
extern bool libraryFull;
extern const char *cardStatus;
void initialTable();
#if !PINBALL_SD_BOARDS
void builtinTable(Table &out);
#endif
bool validTable(const Table &t, unsigned size);
void scanTables();
// The current table is assigned only after a complete, validated read.
bool loadTable(unsigned index);
bool previewTable(unsigned index);
const Table &previewData();
Table &editData();  // Reuse the existing staging table; no second RAM copy.
}  // namespace pinball
