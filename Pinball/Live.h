#pragma once
#include <stdint.h>
namespace pinball { struct Table; namespace live {
// Atomic table commit shared by USB and the browser's direct engine API.
bool apply(const Table &next, unsigned size);
// The release and native simulator accept the same bounded PBT transactions.
bool command(const char *args);
void poll();
// Optional editor replay trace; sampling is inactive in standalone play.
void sample(bool playing);
void invalidatePreview();
bool changed();
bool busy();
bool writeSector(uint32_t lba,const uint8_t *data);
} }
