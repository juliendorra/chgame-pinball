#pragma once
// Standard contact-spin model: no synthetic angle variation.
// Experiments explicitly override these defaults for historical comparisons.
#ifndef PINBALL_SCATTER_PASSIVE
#define PINBALL_SCATTER_PASSIVE 0
#endif
#ifndef PINBALL_SCATTER_POWERED
#define PINBALL_SCATTER_POWERED 0
#endif
#ifndef PINBALL_SCATTER_EJECT
#define PINBALL_SCATTER_EJECT 0
#endif
namespace pinball {
constexpr unsigned SCATTER_PASSIVE = PINBALL_SCATTER_PASSIVE;
constexpr unsigned SCATTER_POWERED = PINBALL_SCATTER_POWERED;
constexpr unsigned SCATTER_EJECT = PINBALL_SCATTER_EJECT;
constexpr bool validScatter(unsigned s) { return s==0 || s==2 || s==4 || s==8 || s==16; }
// The conservative Q14 cosine is energy-safe for these strengths.
static_assert(validScatter(SCATTER_PASSIVE) && validScatter(SCATTER_POWERED) &&
              validScatter(SCATTER_EJECT), "Unsupported scatter strength: check rotation energy bound");
}
