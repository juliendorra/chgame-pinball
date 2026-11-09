#pragma once
#include <CHGame.h>
void budgetLine(int,int,int,int,uint8_t);
void budgetPixel(int,int,uint8_t);
void budgetHline(int,int,int,uint8_t);
void budgetSprite(const uint8_t *,int,int,const uint8_t * = nullptr,int = 256,uint8_t = 0);
