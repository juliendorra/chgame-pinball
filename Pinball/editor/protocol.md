# Pinball live protocol v1

The Pinball 1.4 release uses CHGame's existing USB CDC identity and endpoint.
Connect at 115200 baud with DTR asserted. All commands are ASCII lines starting
with `@`; replies start with `LIVE`. Numbers are decimal; hex data is lowercase.
A request must finish before another request begins. Lines are limited to 95
characters. The native simulator accepts the same commands through its debug
hook, adding its standard `OK`/`ERR` terminator after the `LIVE` response.

| Command | Reply / effect |
| --- | --- |
| `@?` | `LIVE HELLO 1.4.19 PBT2 RAM SD RUBBER TRACE` |
| `@B <bytes>` | Begin a 100–964 byte PBT2 RAM upload; `LIVE OK` |
| `@D <offset> <hex>` | Append 1–32 bytes at the exact next offset; `LIVE OK` |
| `@C` | Validate complete PBT header, FNV checksum, geometry and length, then apply; `LIVE OK` |
| `@T` | Current board: `LIVE DATA <hex>` |
| `@L` | Rescan; `LIVE BOARD <index> <8-char stem>` lines, then `LIVE OK` |
| `@G <index>` | Read a built-in/SD board without replacing the active one: `LIVE DATA <hex>` |
| `@K <mask>` | Hold CHGame button bits; `LIVE OK` |
| `@R` | Restart the active board; `LIVE OK` |
| `@Q <0/1>` | Set pause; `LIVE OK` |
| `@P <x>,<y>` | Place ball 0 in validated playfield coordinates; `LIVE OK` |
| `@V` | `LIVE STATE` followed by the fields below |
| `@H` | 1.4.1: current 8192-byte packed LCD framebuffer, `LIVE DATA <hex>`; palette comes from the active PBT |
| `@M <row>` | Set a bounded camera row, `LIVE OK`; 1.4.2 accepts -24 through board-height minus 108 to include the decorative header |
| `@E` | 1.4.1: `LIVE RUMBLE <strength> <remaining-ms> <AFIO-PCFR1> <GPIOC-CFGLR> <TIM2-CH4CVR>`; the last three are hardware-only |
| `@I` | Initialize the SD card; `LIVE OK` |
| `@S <lba>` | Read a sector: `LIVE DATA <1024 hex chars>` |
| `@W <lba>` | Begin a 512-byte raw-sector transaction using the same staging buffer |
| `@F <fnv32>` | Check all 512 bytes, write the sector, read it back and check FNV32; `LIVE OK` |
| `@N` | `LIVE SHAKE <level> <combo_frames> <wobble_frames> <dx> <dy> <tilt>`; tilt is 3 when active |
| `@X` | Abort staging and release injected keys; `LIVE OK` |

`LIVE STATE` fields: id, score, lives, ticks, ball xQ8, yQ8, vx, vy, left/right
flipper levels, shooter flag, camera, zoom, paused flag, frame count. Values
use the existing signed decimal formatter; interpret ID as unsigned 32-bit.
Button bits: A 1, B 2, Up 4, Down 8, Left 16, Right 32, Start 64, Select 128.

Any refused operation replies `LIVE ERR`. Oversized, out-of-order, truncated or
corrupted PBT uploads never replace the running board. Transactions expire
when idle for three seconds. Injected controls expire after 500 ms; clients
refresh held keys every 150 ms and send zero on focus loss. Clients serialize
whole upload/save operations and do not interleave the two staging formats.

PBT2 uses FNV-1a with bytes 20–23 treated as zero. Raw-sector
writes use FNV-1a over all 512 bytes (offset basis 2166136261, prime 16777619).
The block interface has the same card-level access as the SD reader app;
`fat.py` restricts the editor's writes to the board folder and its FAT metadata.
It never exposes arbitrary block operations through the HTTP API.

The native-only `H` diagnostic command emits `OVERVIEW <bytes>`, then a packed
128 × (board-height + 24) framebuffer plus sixteen RGB565 palette entries, then `OK`.
The first 24 rows cover the decorative space above world y=0. The WebSocket
metadata reports `headerHeight: 24`; editor picking retains its original
playfield coordinates below that header.
It saves/restores camera and zoom, omits score celebrations in the overview,
and leaves physics state and time untouched. The normal LCD stream retains
all camera zooms, score popups and overlays.

A (1) launches in the shooter lane and shakes left during play; Right (32) shakes right. Down (8) only launches. Shakes use press edges. Four rapid taps within the progressive 420 ms windows reach tilt level three until drain.

`K` mirrors the current mask; it does not schedule an input at a named physics
tick. Matching seeds alone therefore does not synchronize two live games.
See [performance and synchronization](../docs/performance-and-sync.md).

The native editor state also reports `shake_direction` (-1 left, +1 right),
so the badge indicates the shove rather than the rebound of the wobble. The
release `@N` response retains its six-field format.

## Seeded scatter (1.4.9+)

`@R` or `@R 0` starts a game with the next default seed. `@R <seed>` accepts
a nonzero unsigned 32-bit decimal seed for replay. `@Z` returns the initial
seed and current RNG state as `LIVE DATA <16 hex digits>`: two uint32 values
in little-endian order. For example, `7856341278563412` means both are
`0x12345678` immediately after restart. The existing `@V` state format is unchanged.
See [physics scatter](../docs/physics-scatter.md) for bounds and determinism.
