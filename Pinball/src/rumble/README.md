# CHGame rumble

Small independent PWM driver for **GPIO1 / PC0 / H1.8**, using **TIM2 CH4**
with the CH32X035 full remap. It leaves TIM1 sound and other GPIOs alone.
The pin controls the rumble pod's MOSFET gate. Copy this folder into another
sketch's `src/` directory to reuse it; no Arduino timer library is required.

```cpp
#include "src/rumble/Rumble.h"
rumble::begin();
rumble::pulse(180, 70);  // duty 0–255, milliseconds, optional priority
rumble::play(rumble::Effect::Bumper);
rumble::setEnabled(false); // immediate off for pause/menu
```

Pulses are capped at 500 ms. TIM2's 1 kHz interrupt stops them even when the
game is rendering or loading SD data. Lower priorities cannot interrupt
higher priorities. Calling `update()` in the game loop advances the same
state in the native simulator. `level()` and `remaining()` expose test state.
