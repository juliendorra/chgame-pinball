"""chcart: the reference implementation of the .chgame format (spec/chgame.md)
and of its runtime preparation for the CHGame's SD menu (spec/card.md).

    model.py    the format: Cart and Game, info.json in and out, validation
    zipio.py    reading a .chgame safely, writing one byte for byte the same
    sources.py  games from sketches, .bin, .hex, .chg and other .chgame files
    runtime.py  a cart to the card's files: GAMES/ (CHG files, MENU.IDX,
                MENU.BG) and the games' SD files; a FAT32 image
    deploy.py   flashing a game, writing a card, the deploy rules
    background.py  the menu's picture from any image, its preview, the default
    fixtures.py the conformance fixtures in spec/fixtures
    cli.py      `chgame export`, `chgame cart ...`, `chgame background`

Only Python 3.10 and Pillow are needed; flashing also needs pyserial (the
uploader in platform/bootloader/host/py).
"""
