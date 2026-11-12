// One bounded CMD24, using the game's existing SD reader for identification.
// File allocation/commit is done by the editor; the game never exports a drive.
#include <CHGame.h>
#include <SdSpi.h>
#if __has_include(<SdWrite.h>)
#include <SdWrite.h>
#endif
#include "Live.h"
#if !CHGAME_DEBUG || defined(CHSIM)
#ifdef CHSIM
#include <stdio.h>
#include <stdlib.h>
namespace pinball { namespace live {
bool writeSector(uint32_t lba,const uint8_t *data) {
    const char *path=getenv("CHSD_CARD");FILE *f=path?fopen(path,"r+b"):nullptr;if(!f)return false;
    bool ok=!fseek(f,lba*512,SEEK_SET)&&fwrite(data,1,512,f)==512;fclose(f);return ok;
}
} }
#else
namespace pinball { namespace live {
bool writeSector(uint32_t lba,const uint8_t *data) {
    return sd::init() && sd::write(lba,data);
}
} }
#endif

#endif
