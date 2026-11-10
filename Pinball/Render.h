#pragma once
#include "Physics.h"
namespace pinball {
void drawTable();
void center(int y, const char *s, uint8_t color);
void drawLibrary(unsigned selected, bool playing, bool previewReady);
void drawPause(bool sound);
void drawGameOver(uint32_t best);
#ifdef CHSIM
// The console's actual zoom/camera crop, in playfield coordinates.
void cameraView(int &x,int &y,int &width,int &height);
// Render the entire playfield without advancing or changing game state.
void drawOverview(void (*write)(const uint8_t *, unsigned, void *), void *context);
#endif
}  // namespace pinball
