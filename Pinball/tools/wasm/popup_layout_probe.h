// Host-only draw-call probes; the production renderer calls the same SDK
// routines with identical arguments. No instrumentation enters firmware.
#pragma once
#include <CHGame.h>
void checkedPopupText(int,int,const char *,uint8_t);
void checkedPopupSprite(const uint8_t *,int,int,const uint8_t * = nullptr,int = 256,uint8_t = 0);
void beginPopupLayout(const char *,unsigned);
void checkScoreCaptionPadding();
void checkGameOverLayout();
unsigned popupLayoutChecks();
