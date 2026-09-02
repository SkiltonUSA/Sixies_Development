; Atari 8-bit OS shadow registers and hardware registers used by Sixies.
; Names follow the Atari Hardware/OS manuals and cc65 atari.inc conventions.

RTCLOK          = $0012
ATRACT          = $004D
SDLSTL          = $0230
SDMCTL          = $022F
GPRIOR          = $026F
STICK0          = $0278
STICK1          = $0279
STRIG0          = $0284
STRIG1          = $0285
CH              = $02FC
CH_NONE         = $FF
KEY_CODE_MASK   = $3F       ; Ignore Shift/Control modifier bits for controls.
COLOR0          = $02C4
COLOR1          = $02C5
COLOR2          = $02C6
COLOR3          = $02C7
COLOR4          = $02C8

HPOSP0          = $D000
COLPM0          = $D012
COLPF0          = $D016
COLPF1          = $D017
COLPF2          = $D018
COLPF3          = $D019
COLBK           = $D01A
PRIOR           = $D01B
CONSOL          = $D01F

AUDF1           = $D200
AUDC1           = $D201
AUDF2           = $D202
AUDC2           = $D203
AUDF3           = $D204
AUDC3           = $D205
AUDF4           = $D206
AUDC4           = $D207
AUDCTL          = $D208
KBCODE          = $D209
RANDOM          = $D20A
SKCTL           = $D20F

PORTB           = $D301

DMACTL          = $D400
CHACTL          = $D401
DLISTL          = $D402
DLISTH          = $D403
VCOUNT          = $D40B
NMIEN           = $D40E

; Atari keyboard scan codes (unshifted). Atari800's second keyboard-joystick
; layout also supplies host WASD through STICK1 for reliable emulator input.
KEY_RETURN      = $0C
KEY_I           = $0D
KEY_SPACE       = $21
KEY_N           = $23
KEY_M           = $25
KEY_E           = $2A
KEY_Y           = $2B
KEY_W           = $2E
KEY_Q           = $2F
KEY_D           = $3A
KEY_S           = $3E
KEY_A           = $3F

SCREEN          = $8000
SCREEN_BYTES    = 40
SCREEN_LINES    = 192
SCREEN_SPLIT    = 100
SCREEN_SECOND   = $9000
SCREEN_PHYSICAL_PAGES = $1F
SCREEN_PHYSICAL_END = SCREEN + SCREEN_PHYSICAL_PAGES * $100

BOARD_X_BYTES   = 10
BOARD_TOP       = 26
CELL_BYTES      = 4
CELL_HEIGHT     = 28

ACTION_NONE     = 0
ACTION_LEFT     = 1
ACTION_RIGHT    = 2
ACTION_UP       = 3
ACTION_DOWN     = 4
ACTION_ROTATE   = 5
ACTION_PLACE    = 6
ACTION_NEW      = 7
ACTION_INFO     = 8
ACTION_MUTE     = 9
ACTION_YES      = 10
