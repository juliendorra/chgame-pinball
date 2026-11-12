// Draw the browser draft between acknowledged console edits. Only the
// shared renderer sees the temporary table and game state.
#include <CHGame.h>
#include <cstring>
#include "Physics.h"

using namespace pinball;
extern "C" const uint8_t *pb_render();

extern "C" const uint8_t *pb_render_draft(unsigned size) {
    const Table &draft = editData();
    if (size < sizeof(TableHeader) || size > sizeof(Table) || !validTable(draft, size)) return nullptr;

    const Table previous = table;
    const Game state = game;
    uint8_t lcd[GFX_FB_BYTES];
    std::memcpy(lcd, gfx_fb, sizeof lcd);

    if (draft.boardId() == previous.boardId() && draft.h.height == previous.h.height) {
        // Match unchanged parts by content, even if insertion or deletion
        // moved their index. A changed part starts with its idle appearance.
        std::memset(game.cooldown, 0, sizeof game.cooldown);
        std::memset(game.elementState, 0, sizeof game.elementState);
        for (Ball &ball : game.balls) ball.ramp = -1;
        bool used[MAX_OBJECTS] = {};
        for (unsigned i = 0; i < draft.h.count; ++i) {
            for (unsigned j = 0; j < previous.h.count; ++j) {
                if (used[j] || std::memcmp(&draft.objects[i], &previous.objects[j], sizeof(Object))) continue;
                used[j] = true;
                game.cooldown[i] = state.cooldown[j];
                game.elementState[i] = state.elementState[j];
                for (unsigned ball = 0; ball < 3; ++ball) {
                    if (state.balls[ball].ramp == int(j)) game.balls[ball].ramp = i;
                }
                break;
            }
        }
    } else {
        // A different table has no acknowledged ball positions yet.
        game = {};
        game.zoom = 256;
        game.multiplier = 1;
        game.lives = 3;
    }

    table = draft;
    const uint8_t *pixels = pb_render();
    table = previous;
    game = state;
    std::memcpy(gfx_fb, lcd, sizeof lcd);
    return pixels;
}
