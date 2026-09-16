!cpu 6510

CPU_PORT        = $01
SCREEN          = $4400
SHADOW_SPRITES  = $4c00
BITMAP          = $6000
COLOR_RAM       = $d800
BORDER          = $d020
BACKGROUND      = $d021
VIC_CONTROL     = $d011
VIC_MEMORY      = $d018
VIC_MODE        = $d016
VIC_BANK        = $dd00
VIC_IRQ_STATUS  = $d019
VIC_IRQ_ENABLE  = $d01a
RASTER_LINE     = $d012
SPRITE0_X       = $d000
SPRITE0_Y       = $d001
SPRITE_X_MSB    = $d010
SPRITE_ENABLE   = $d015
SPRITE_Y_EXPAND = $d017
SPRITE_PRIORITY = $d01b
SPRITE_MULTICOLOR = $d01c
SPRITE_X_EXPAND = $d01d
SPRITE0_COLOR   = $d027
SPRITE0_PTR     = SCREEN + $03f8
SID_HW_V1_FREQ_LO = $d400
; Gameplay effects write a software voice-1 shadow. The combined audio update
; overlays it after the music player has advanced all three physical voices.
SID_V1_FREQ_LO  = sfxVoice1Shadow
SID_V1_FREQ_HI  = sfxVoice1Shadow + 1
SID_V1_PW_LO    = sfxVoice1Shadow + 2
SID_V1_PW_HI    = sfxVoice1Shadow + 3
SID_V1_CONTROL  = sfxVoice1Shadow + 4
SID_V1_AD       = sfxVoice1Shadow + 5
SID_V1_SR       = sfxVoice1Shadow + 6
SID_MODE_VOLUME = $d418
TITLE_MUSIC_INIT = $a000
TITLE_MUSIC_PLAY = $a003
IRQ_VECTOR      = $0314
CIA1_IRQ        = $dc0d
JOYSTICK2       = $dc00
KEY_CURRENT     = $cb
CURSOR_FLAG     = $cc
TV_STANDARD     = $02a6
SCNKEY          = $ff9f
GETIN           = $ffe4
IRQ_EXIT        = $ea81

PTR_LO          = $fb
PTR_HI          = $fc
SOURCE_LO       = $fd
SOURCE_HI       = $fe

COLOR_BLACK     = 0
COLOR_WHITE     = 1
COLOR_RED       = 2
COLOR_CYAN      = 3
COLOR_PURPLE    = 4
COLOR_GREEN     = 5
COLOR_YELLOW    = 7
COLOR_DKGRAY    = 11
COLOR_LTGREEN   = 13
COLOR_LTBLUE    = 14
COLOR_LTGRAY    = 15

; Audio modes are disable-bit flags: bit 0 disables effects and bit 1 disables
; music. This keeps the original three modes and adds a fully silent state.
AUDIO_BOTH       = 0
AUDIO_MUSIC_ONLY = 1
AUDIO_SFX_ONLY   = 2
AUDIO_NONE       = 3

GRID_LEFT       = 10
GRID_TOP        = 3
GRID_SPAN       = 20
GRID_LINES      = 6
BOARD_CELLS     = 25
MASCOT_ROW_START = 6
MASCOT_ROW_END   = 16
PIECE_PREVIEW_Y  = 100
GAMEPLAY_LOGO_ROW = 0
GAMEPLAY_LOGO_COL = 14
SIDE_CONTROL_ICON_Y = 218
SIDE_CONTROL_LABEL_ROW = 24
NEW_GAME_LABEL_COL = 3
SETTINGS_LABEL_COL = 34
SCORE_ROW       = 1
SCORE_COL_FOUR  = 0
SCORE_COL_THREE = 2
SCORE_COL_TWO   = 3
SCORE_COL_ONE   = 4
GAME_OVER_COL   = 11
GAME_OVER_CHARS = 9
CHAIN_MERGE_PAUSE_FRAMES = 30

ACTION_NONE     = 0
ACTION_LEFT     = 1
ACTION_RIGHT    = 2
ACTION_UP       = 3
ACTION_DOWN     = 4
ACTION_ROTATE   = 5
ACTION_PLACE    = 6
ACTION_NEW      = 7
ACTION_DEBUG_FILL = 8
ACTION_SETTINGS = 9
ACTION_ROTATE_LEFT = 10

; Sprite coordinates include the VIC-II's 24-pixel left border. The controls
; sit at the bottom of the side panels beside the lowered board.
NEW_GAME_ICON_X = 52
SETTINGS_ICON_X = 44

* = $0801
!word BasicEnd
!word 10
!byte $9e
!text "2064"
!byte 0
BasicEnd:
!word 0

* = $0810

Start:
    sei
    jsr InitVideo
    jsr ShowPresentsScreen
    cli
    lda #5
    jsr WaitStartupAttractSeconds
    sei
    jsr ShowTitleScreen
    jsr InitTitleRasterIRQ
    cli
    jsr WaitForTitleStart
    jsr StopTitleRasterIRQ
    jsr ClearBitmap
    jsr InitScreenColors
    jsr DrawGameplayLogo
    jsr DrawGrid
    jsr DrawMainMascot
    jsr DrawBottomLabels
    jsr InitSpriteHardware
    jsr ResetGameLocked
    jsr InitRasterIRQ
    cli
    jsr AnimateNewGame

MainLoop:
    jsr WaitFrame
    lda endAttractNewGame
    bne MainLoop_NewGame
    jsr UpdatePreviewBlink
    jsr ReadAction
    lda action
    beq MainLoop
    cmp #ACTION_NEW
    beq MainLoop_NewGame
    cmp #ACTION_DEBUG_FILL
    beq MainLoop_DebugFill
    cmp #ACTION_SETTINGS
    beq MainLoop_Settings

    lda gameOver
    bne MainLoop

    lda newGameFocused
    ora settingsFocused
    beq MainLoop_GridAction
    jsr HandleBottomControlAction
    cmp #ACTION_NEW
    beq MainLoop_NewGame
    cmp #ACTION_SETTINGS
    beq MainLoop_Settings
    jmp MainLoop

MainLoop_GridAction:
    lda action
    cmp #ACTION_LEFT
    beq MainLoop_Left
    cmp #ACTION_RIGHT
    beq MainLoop_Right
    cmp #ACTION_UP
    beq MainLoop_Up
    cmp #ACTION_DOWN
    beq MainLoop_Down
    cmp #ACTION_ROTATE
    beq MainLoop_Rotate
    cmp #ACTION_ROTATE_LEFT
    beq MainLoop_RotateLeft
    cmp #ACTION_PLACE
    bne MainLoop_NoGridAction
    jmp MainLoop_Place
MainLoop_NoGridAction:
    jmp MainLoop

MainLoop_NewGame:
    lda #0
    sta endAttractNewGame
    lda gameOverBlindActive
    beq MainLoop_NewGameReady
    jsr RestoreGameScreen
MainLoop_NewGameReady:
    jsr ResetGameLocked
    jsr AnimateNewGame
    jmp MainLoop

MainLoop_DebugFill:
    jsr DebugFillBoard
    jmp MainLoop

MainLoop_Settings:
    jsr ShowSettingsScreen
    jmp MainLoop

MainLoop_Left:
    lda cursorX
    beq MainLoop_Update
    dec cursorX
    jsr PlayBounce
    jmp MainLoop_Update

MainLoop_Right:
    lda cursorX
    cmp #4
    beq MainLoop_Update
    inc cursorX
    jsr PlayBounce
    jmp MainLoop_Update

MainLoop_Up:
    lda cursorY
    beq MainLoop_Update
    dec cursorY
    jsr PlayBounce
    jmp MainLoop_Update

MainLoop_Down:
    lda cursorY
    cmp #4
    bne MainLoop_MoveDown
    jsr FocusBottomOption
    jmp MainLoop
MainLoop_MoveDown:
    inc cursorY
    jsr PlayBounce
    jmp MainLoop_Update

MainLoop_RotateLeft:
    dec orientation
    dec orientation

MainLoop_Rotate:
    lda pieceCount
    cmp #2
    bne MainLoop_Update
    inc orientation
    lda orientation
    and #3
    sta orientation
    jsr PlayPortalPing

MainLoop_Update:
    jsr UpdatePlacement
    ; Input runs just after the UI raster phase. Publish the new ghost now so
    ; the next frame cannot render the cursor's previous row.
    jsr BuildDisplayBoard
    jsr UpdateCursorHighlight
    jmp MainLoop

MainLoop_Place:
    lda placementValid
    bne MainLoop_PlaceValid
    jsr PlayInvalidPlacement
    jmp MainLoop
MainLoop_PlaceValid:
    jsr PlayPortalPing
    jsr PlaceCurrentPiece
    jmp MainLoop

InitVideo:
    ; Expose RAM under BASIC ROM for the relocated title tune while retaining
    ; KERNAL and I/O access used by input, IRQ exit, VIC-II, and SID routines.
    lda #$36
    sta CPU_PORT
    lda #1
    sta CURSOR_FLAG

    lda #$7f
    sta CIA1_IRQ
    lda CIA1_IRQ

    ; VIC bank 1, screen at $4400, bitmap at $6000.
    lda VIC_BANK
    and #%11111100
    ora #%00000010
    sta VIC_BANK
    lda #$18
    sta VIC_MEMORY
    lda VIC_CONTROL
    ora #%00100000
    and #%01111111
    sta VIC_CONTROL
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE

    lda #COLOR_BLACK
    sta BORDER
    sta BACKGROUND
    rts

ShowTitleScreen:
    lda #1
    sta titleScreenActive
    lda #0
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND

    ; The title remains packed in the program image so the merge callouts can
    ; occupy their own RAM block. Expand it in five independent bands.
    lda #0
    sta titleBand
ShowTitleScreen_Band:
    ldx titleBand
    lda TitleKoalaBitmapLo,x
    sta SOURCE_LO
    lda TitleKoalaBitmapHi,x
    sta SOURCE_HI
    lda KoalaBitmapBandLo,x
    sta PTR_LO
    lda KoalaBitmapBandHi,x
    sta PTR_HI
    jsr UnpackKoalaStream

    ldx titleBand
    lda TitleKoalaScreenLo,x
    sta SOURCE_LO
    lda TitleKoalaScreenHi,x
    sta SOURCE_HI
    lda KoalaScreenBandLo,x
    sta PTR_LO
    lda KoalaScreenBandHi,x
    sta PTR_HI
    jsr UnpackKoalaStream

    ldx titleBand
    lda TitleKoalaColorLo,x
    sta SOURCE_LO
    lda TitleKoalaColorHi,x
    sta SOURCE_HI
    lda KoalaColorBandLo,x
    sta PTR_LO
    lda KoalaColorBandHi,x
    sta PTR_HI
    jsr UnpackKoalaStream

    inc titleBand
    lda titleBand
    cmp #5
    bne ShowTitleScreen_Band

    lda #<TitlePromptSpriteData
    sta SOURCE_LO
    lda #>TitlePromptSpriteData
    sta SOURCE_HI
    lda #<SHADOW_SPRITES
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    ldx #1
    lda #128
    jsr CopyTitleBlock
    jsr SetupTitlePromptSprites

    lda VIC_MODE
    ora #%00010000
    sta VIC_MODE
    rts

SetupTitlePromptSprites:
    lda #0
    sta SPRITE_X_MSB
    sta SPRITE_MULTICOLOR
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    sta SPRITE_PRIORITY
    ; Sprite 0 contains the intro-only build counter. Title uses sprites 1-5.
    ldx #1
SetupTitlePromptSprites_Sprite:
    txa
    clc
    adc #$30
    sta SPRITE0_PTR,x
    lda #COLOR_WHITE
    sta SPRITE0_COLOR,x
    txa
    asl
    tay
    lda TitlePromptSpriteX,x
    sta SPRITE0_X,y
    lda #234
    sta SPRITE0_Y,y
    inx
    cpx #6
    bne SetupTitlePromptSprites_Sprite
    lda #%00111110
    sta SPRITE_ENABLE
    rts

TitlePromptSpriteX:
; Intro-only V1.xxx position, followed by the centered title start prompt.
!byte 32,124,148,172,196,220

CopyTitleBlock:
    sta titleCopyRemainder
CopyTitleBlock_Page:
    cpx #0
    beq CopyTitleBlock_Remainder
    ldy #0
CopyTitleBlock_PageByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    bne CopyTitleBlock_PageByte
    inc SOURCE_HI
    inc PTR_HI
    dex
    bne CopyTitleBlock_Page
CopyTitleBlock_Remainder:
    ldy #0
CopyTitleBlock_RemainderByte:
    cpy titleCopyRemainder
    beq CopyTitleBlock_Done
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    bne CopyTitleBlock_RemainderByte
CopyTitleBlock_Done:
    rts

WaitForTitleStart:
    jmp RunTitleAttractMode

InitRasterIRQ:
    lda #<RasterIRQ
    sta IRQ_VECTOR
    lda #>RasterIRQ
    sta IRQ_VECTOR + 1
    lda #64
    sta RASTER_LINE
    lda #1
    sta VIC_IRQ_STATUS
    sta VIC_IRQ_ENABLE
    lda #0
    sta irqPhase
    sta frameCounter
    sta lastFrame
    rts

RasterIRQ:
    lda VIC_IRQ_STATUS
    and #1
    beq RasterIRQ_Exit
    lda #1
    sta VIC_IRQ_STATUS

    ldx irqPhase
    cpx #5
    beq RasterIRQ_UI

    stx renderRow
    cpx #0
    bne RasterIRQ_Board
    jsr SetupPiecePreview
RasterIRQ_Board:
    ; Board sprites have the tighter DMA deadline. Render them before spending
    ; cycles retargeting preview sprites 6-7 to the lower side controls.
RasterIRQ_BoardRenderer:
    jsr RenderBoardRow
    ldx renderRow
    cpx #3
    bne RasterIRQ_Schedule
    jsr SetupBottomSprites
    jmp RasterIRQ_Schedule

RasterIRQ_UI:
    jsr UpdateTitleMusic
    jsr UpdateSoundEffects
RasterIRQ_UI_AudioDone:
RasterIRQ_UISpriteSetup:
    jsr SetupBottomSprites
    jsr SyncRenderBoard
    jsr BuildDisplayBoard
    inc frameCounter

RasterIRQ_Schedule:
    ldx irqPhase
    lda NextRasterLines,x
    sta RASTER_LINE
    inx
    cpx #6
    bne RasterIRQ_StorePhase
    ldx #0
RasterIRQ_StorePhase:
    stx irqPhase
RasterIRQ_Exit:
    jmp IRQ_EXIT

WaitFrame:
    lda frameCounter
    cmp lastFrame
    beq WaitFrame
    sta lastFrame
    jsr UpdateCreditsFade
    jsr UpdateMascotCalloutRipple
    rts

ResetGameLocked:
    lda #1
    sta boardUpdateInProgress
    jsr ResetSoundEffects
    ldx #0
    lda #0
ResetGame_ClearBoard:
    sta board,x
    inx
    cpx #BOARD_CELLS
    bne ResetGame_ClearBoard

    lda #0
    sta scoreThousands
    sta scoreHundreds
    sta scoreTens
    sta scoreOnes
    sta gameOver
    sta singlesOnlyMode
    sta joystickLatch
    sta joystickFireState
    sta settingsFocused
    sta newGameFocused
    sta ghostSuppressed
    sta BORDER
    sta mergeCalloutIndex
    jsr UpdateBottomButtonColors
    lda #1
    sta displayDirty
    lda RASTER_LINE
    eor $dc04
    ora #1
    sta rngSeed
    jsr UpdateScoreDisplay
    jsr SpawnPiece
    lda #0
    sta boardUpdateInProgress
    lda #1
    sta boardDirty
    rts

DebugFillBoard:
    lda #1
    sta boardUpdateInProgress
    sta ghostSuppressed
    ldx #0
DebugFillBoard_Cell:
    jsr RandomByte
    and #7
    cmp #6
    bcs DebugFillBoard_Cell
    clc
    adc #1
    sta board,x
    inx
    cpx #BOARD_CELLS
    bne DebugFillBoard_Cell

    lda #0
    sta boardUpdateInProgress
    lda #1
    sta boardDirty
    jsr WaitFrame
    jsr SpawnPiece
    rts

RandomByte:
    lda rngSeed
    asl
    bcc RandomByte_NoXor
    eor #$1d
RandomByte_NoXor:
    sta rngSeed
    rts

SpawnPiece:
    jsr RandomByte
    and #1
    clc
    adc #1
    sta pieceCount
    jsr RandomByte
    and #3
    clc
    adc #1
    sta pieceValue0
    jsr RandomByte
    and #3
    clc
    adc #1
    sta pieceValue1
    jsr MaybeIntroduceFiveDie

    lda pieceCount
    cmp #2
    bne SpawnPiece_ValuesReady
    lda pieceValue0
    cmp #4
    bne SpawnPiece_ValuesReady
    lda pieceValue1
    cmp #4
    bne SpawnPiece_ValuesReady
SpawnPiece_RerollSecondFour:
    jsr RandomByte
    and #3
    cmp #3
    beq SpawnPiece_RerollSecondFour
    clc
    adc #1
    sta pieceValue1
SpawnPiece_ValuesReady:

    lda singlesOnlyMode
    bne SpawnPiece_ForceSingle
    jsr CheckDoubleSpaceAvailable
    lda doubleSpaceAvailable
    bne SpawnPiece_CountReady
    lda #1
    sta singlesOnlyMode
SpawnPiece_ForceSingle:
    lda #1
    sta pieceCount
SpawnPiece_CountReady:

    lda #2
    sta cursorX
    sta cursorY
    lda #0
    sta orientation
    jsr BuildShadowDiceSprites
    jsr UpdatePlacement
    jsr CheckAnyPlacement
    lda gameOver
    bne SpawnPiece_GameOver
    jsr UpdateCursorHighlight
    rts

SpawnPiece_GameOver:
    lda highlightedIndex
    cmp #$ff
    beq SpawnPiece_GameOverDone
    jsr ClearCursorHighlights
    lda #$ff
    sta highlightedIndex
    sta highlightedSecondIndex
SpawnPiece_GameOverDone:
    jsr AnimateGameOver
    rts

MaybeIntroduceFiveDie:
    lda #0
    sta boardFiveCount
    ldx #0
MaybeIntroduceFiveDie_Count:
    lda board,x
    cmp #5
    bne MaybeIntroduceFiveDie_Next
    inc boardFiveCount
    lda boardFiveCount
    cmp #5
    bcs MaybeIntroduceFiveDie_Eligible
MaybeIntroduceFiveDie_Next:
    inx
    cpx #BOARD_CELLS
    bne MaybeIntroduceFiveDie_Count
    rts

MaybeIntroduceFiveDie_Eligible:
    jsr RandomByte
    and #$0f
    bne MaybeIntroduceFiveDie_Done
    lda pieceCount
    cmp #2
    bne MaybeIntroduceFiveDie_First
    jsr RandomByte
    and #1
    beq MaybeIntroduceFiveDie_First
    lda #5
    sta pieceValue1
    rts
MaybeIntroduceFiveDie_First:
    lda #5
    sta pieceValue0
MaybeIntroduceFiveDie_Done:
    rts

CheckDoubleSpaceAvailable:
    lda #0
    sta doubleSpaceAvailable
    ldx #0
CheckDoubleSpaceAvailable_Cell:
    lda board,x
    bne CheckDoubleSpaceAvailable_Next
    lda RightNeighbor,x
    cmp #$ff
    beq CheckDoubleSpaceAvailable_Down
    tay
    lda board,y
    beq CheckDoubleSpaceAvailable_Found
CheckDoubleSpaceAvailable_Down:
    lda DownNeighbor,x
    cmp #$ff
    beq CheckDoubleSpaceAvailable_Next
    tay
    lda board,y
    beq CheckDoubleSpaceAvailable_Found
CheckDoubleSpaceAvailable_Next:
    inx
    cpx #BOARD_CELLS
    bne CheckDoubleSpaceAvailable_Cell
    rts
CheckDoubleSpaceAvailable_Found:
    lda #1
    sta doubleSpaceAvailable
    rts

UpdatePlacement:
    lda #0
    sta placementValid
    lda #$ff
    sta secondIndex

    ldx cursorY
    lda RowIndexBase,x
    clc
    adc cursorX
    sta originIndex

    lda pieceCount
    cmp #2
    bne UpdatePlacement_CheckOrigin
    ldx originIndex
    lda orientation
    beq UpdatePlacement_Right
    cmp #1
    beq UpdatePlacement_Down
    cmp #2
    beq UpdatePlacement_Left
    lda UpNeighbor,x
    jmp UpdatePlacement_CheckSecond
UpdatePlacement_Right:
    lda RightNeighbor,x
    jmp UpdatePlacement_CheckSecond
UpdatePlacement_Down:
    lda DownNeighbor,x
    jmp UpdatePlacement_CheckSecond
UpdatePlacement_Left:
    lda LeftNeighbor,x
UpdatePlacement_CheckSecond:
    cmp #$ff
    beq UpdatePlacement_Done
    sta secondIndex

UpdatePlacement_CheckOrigin:
    ldx originIndex
    lda board,x
    bne UpdatePlacement_Done
    lda pieceCount
    cmp #2
    bne UpdatePlacement_Valid
    ldx secondIndex
    lda board,x
    bne UpdatePlacement_Done

UpdatePlacement_Valid:
    lda #1
    sta placementValid
UpdatePlacement_Done:
    lda #1
    sta displayDirty
    rts

CheckAnyPlacement:
    lda #0
    sta searchOrientation
CheckAnyPlacement_Orientation:
    lda #0
    sta searchY
CheckAnyPlacement_Row:
    lda #0
    sta searchX
CheckAnyPlacement_Column:
    jsr TestSearchPlacement
    bcs CheckAnyPlacement_Found

    inc searchX
    lda searchX
    cmp #5
    bne CheckAnyPlacement_Column
    inc searchY
    lda searchY
    cmp #5
    bne CheckAnyPlacement_Row

    lda pieceCount
    cmp #1
    beq CheckAnyPlacement_GameOver
    inc searchOrientation
    lda searchOrientation
    cmp #4
    bne CheckAnyPlacement_Orientation

CheckAnyPlacement_GameOver:
    lda #1
    sta gameOver
    lda #COLOR_BLACK
    sta BORDER
    lda #0
    sta placementValid
    rts

CheckAnyPlacement_Found:
    lda #0
    sta gameOver
    jsr UpdatePlacement
    rts

; Carry set means the search coordinates can accept the current piece.
; Unlike UpdatePlacement, this never touches live cursor or preview state.
TestSearchPlacement:
    ldx searchY
    lda RowIndexBase,x
    clc
    adc searchX
    tax
    lda board,x
    bne TestSearchPlacement_Invalid
    lda pieceCount
    cmp #2
    bne TestSearchPlacement_Valid

    lda searchOrientation
    beq TestSearchPlacement_Right
    cmp #1
    beq TestSearchPlacement_Down
    cmp #2
    beq TestSearchPlacement_Left
    lda UpNeighbor,x
    jmp TestSearchPlacement_Second
TestSearchPlacement_Right:
    lda RightNeighbor,x
    jmp TestSearchPlacement_Second
TestSearchPlacement_Down:
    lda DownNeighbor,x
    jmp TestSearchPlacement_Second
TestSearchPlacement_Left:
    lda LeftNeighbor,x
TestSearchPlacement_Second:
    cmp #$ff
    beq TestSearchPlacement_Invalid
    tax
    lda board,x
    bne TestSearchPlacement_Invalid
TestSearchPlacement_Valid:
    sec
    rts
TestSearchPlacement_Invalid:
    clc
    rts

PlaceCurrentPiece:
    lda #1
    sta boardUpdateInProgress
    sta ghostSuppressed
    ldx originIndex
    lda pieceValue0
    sta board,x
    lda pieceCount
    cmp #2
    bne PlaceCurrentPiece_Merge
    ldx secondIndex
    lda pieceValue1
    sta board,x

PlaceCurrentPiece_Merge:
    lda #0
    sta mergeChainDepth
    jsr AnimatePlacedPiece
    lda originIndex
    sta activeIndex
    jsr ResolveAtActiveIndex
    lda pieceCount
    cmp #2
    bne PlaceCurrentPiece_Finish
    ldx secondIndex
    lda board,x
    beq PlaceCurrentPiece_Finish
    lda secondIndex
    sta activeIndex
    jsr ResolveAtActiveIndex

PlaceCurrentPiece_Finish:
    lda #0
    sta ghostSuppressed
    jsr UpdateScoreDisplay
    jsr SpawnPiece
    lda #0
    sta boardUpdateInProgress
    lda #1
    sta boardDirty
    ; Publish the new piece preview before input can move its bottom-row cell.
    lda frameCounter
    sta lastFrame
    jsr WaitFrame
    rts

SyncRenderBoard:
    lda boardDirty
    beq SyncRenderBoard_Done
    lda boardUpdateInProgress
    bne SyncRenderBoard_Done
    lda #0
    sta boardDirty
    ldx #0
SyncRenderBoard_Copy:
    lda board,x
    sta renderBoard,x
    inx
    cpx #BOARD_CELLS
    bne SyncRenderBoard_Copy
    lda #1
    sta displayDirty
SyncRenderBoard_Done:
    rts

BuildDisplayBoard:
    lda displayDirty
    bne BuildDisplayBoard_Rebuild
    rts
BuildDisplayBoard_Rebuild:
    lda #0
    sta displayDirty
    ldx #0
BuildDisplayBoard_Cell:
    lda ghostSuppressed
    bne BuildDisplayBoard_LoadBoard
    lda placementValid
    bne BuildDisplayBoard_LoadBoard
    cpx originIndex
    beq BuildDisplayBoard_ShadowOrigin
    lda pieceCount
    cmp #2
    bne BuildDisplayBoard_LoadBoard
    cpx secondIndex
    beq BuildDisplayBoard_ShadowSecond

BuildDisplayBoard_LoadBoard:
    lda renderBoard,x
    bne BuildDisplayBoard_ValueReady
    lda ghostSuppressed
    bne BuildDisplayBoard_Empty
    lda placementValid
    beq BuildDisplayBoard_ValueReady
    cpx originIndex
    bne BuildDisplayBoard_CheckSecond
BuildDisplayBoard_GhostOrigin:
    lda pieceValue0
    ldy #$30
    bne BuildDisplayBoard_GhostReady
BuildDisplayBoard_CheckSecond:
    lda pieceCount
    cmp #2
    bne BuildDisplayBoard_Empty
    cpx secondIndex
    bne BuildDisplayBoard_Empty
BuildDisplayBoard_GhostSecond:
    lda pieceValue1
    ldy #$31
BuildDisplayBoard_GhostReady:
    sta displayValues,x
    pha
    lda highlightPhase
    and #2
    beq BuildDisplayBoard_GhostNormal
    tya
    sta displaySpritePointers,x
    pla
    tay
    lda DiceColors,y
    sta displayColors,x
    jmp BuildDisplayBoard_Next
BuildDisplayBoard_GhostNormal:
    pla
    jmp BuildDisplayBoard_ValueReady

BuildDisplayBoard_ShadowOrigin:
    ; Flash an occupied target between the invalid dither and the die below.
    lda renderBoard,x
    beq BuildDisplayBoard_ShadowOriginVisible
    lda highlightPhase
    and #2
    bne BuildDisplayBoard_LoadBoard
BuildDisplayBoard_ShadowOriginVisible:
    lda pieceValue0
    ldy #$32
    bne BuildDisplayBoard_ShadowReady
BuildDisplayBoard_ShadowSecond:
    lda renderBoard,x
    beq BuildDisplayBoard_ShadowSecondVisible
    lda highlightPhase
    and #2
    bne BuildDisplayBoard_LoadBoard
BuildDisplayBoard_ShadowSecondVisible:
    lda pieceValue1
    ldy #$33
BuildDisplayBoard_ShadowReady:
    sta displayValues,x
    tya
    sta displaySpritePointers,x
    lda #COLOR_LTGRAY
    sta displayColors,x
    jmp BuildDisplayBoard_Next

BuildDisplayBoard_Empty:
    lda #0
BuildDisplayBoard_ValueReady:
    sta displayValues,x
    beq BuildDisplayBoard_NoColor
    tay
    lda DiceSpritePointers,y
    sta displaySpritePointers,x
    lda DiceColors,y
    sta displayColors,x
    lda mergeAnimating
    beq BuildDisplayBoard_Next
    lda mergeFlashPhase
    beq BuildDisplayBoard_Next
    lda mergeCells,x
    beq BuildDisplayBoard_Next
    lda mergeFlashColor
    sta displayColors,x
    bne BuildDisplayBoard_Next
BuildDisplayBoard_NoColor:
    sta displayColors,x
    sta displaySpritePointers,x
BuildDisplayBoard_Next:
    inx
    cpx #BOARD_CELLS
    beq BuildDisplayBoard_Done
    jmp BuildDisplayBoard_Cell
BuildDisplayBoard_Done:
    rts

ResolveAtActiveIndex:
    jsr FindGroup
    lda groupCount
    cmp #3
    bcc ResolveAtActiveIndex_Done
ResolveAtActiveIndex_GroupReady:
    inc mergeChainDepth
    jsr AnimateMergeGroup
    jsr AddAnimatedGroupScore

    ldx #0
ResolveAtActiveIndex_Clear:
    ldy groupCells,x
    lda #0
    sta board,y
    inx
    cpx groupCount
    bne ResolveAtActiveIndex_Clear

    lda groupValue
    cmp #6
    beq ResolveAtActiveIndex_Done
    clc
    adc #1
    ldx activeIndex
    sta board,x
    jsr FindGroup
    lda groupCount
    cmp #3
    bcc ResolveAtActiveIndex_Done
    jsr PauseBetweenChainMerges
    jmp ResolveAtActiveIndex_GroupReady
ResolveAtActiveIndex_Done:
    rts

PauseBetweenChainMerges:
    jsr PublishBoardForAnimation
    jsr ShowChainReactionSprite
    lda #CHAIN_MERGE_PAUSE_FRAMES
    jsr WaitAnimationFrames
    jmp HideChainReactionSprite

AnimateMergeGroup:
    jsr RunMergeLevelEffects
AnimateMergeGroup_Color:
    lda mergeChainDepth
    cmp #2
    bcc AnimateMergeGroup_FirstColor
    lda #COLOR_CYAN
    bne AnimateMergeGroup_StoreColor
AnimateMergeGroup_FirstColor:
    lda #COLOR_WHITE
AnimateMergeGroup_StoreColor:
    sta mergeFlashColor
    jsr BeginMascotMergeCallout
    jsr ClearMergeCellMarks
    ldx #0
AnimateMergeGroup_Mark:
    ldy groupCells,x
    lda #1
    sta mergeCells,y
    inx
    cpx groupCount
    bne AnimateMergeGroup_Mark
    jsr RunMergeGridSweep
    jsr RunMergeFirework
    jsr RunDiceFlash
    jsr EndMascotMergeCallout
    rts

AnimatePlacedPiece:
    lda #COLOR_WHITE
    sta mergeFlashColor
    jsr ClearMergeCellMarks
    lda #1
    ldx originIndex
    sta mergeCells,x
    ldx pieceCount
    dex
    beq AnimatePlacedPiece_Flash
    ldx secondIndex
    sta mergeCells,x
AnimatePlacedPiece_Flash:
    jsr RunDiceFlash
    rts

ClearMergeCellMarks:
    lda #0
    ldx #0
ClearMergeCellMarks_Next:
    sta mergeCells,x
    inx
    cpx #BOARD_CELLS
    bne ClearMergeCellMarks_Next
    rts

RunDiceFlash:
    lda #1
    sta mergeAnimating
    sta mergeFlashPhase
    jsr PublishBoardForAnimation
    lda #3
    jsr WaitAnimationFrames
    lda #0
    sta mergeFlashPhase
    jsr MarkDisplayDirty
    lda #3
    jsr WaitAnimationFrames
    lda #1
    sta mergeFlashPhase
    jsr MarkDisplayDirty
    lda #3
    jsr WaitAnimationFrames
    lda #0
    sta mergeFlashPhase
    jsr MarkDisplayDirty
    lda #2
    jsr WaitAnimationFrames
    lda #0
    sta mergeAnimating
    rts

PublishBoardForAnimation:
    lda #0
    sta boardUpdateInProgress
    lda #1
    sta boardDirty
    jsr WaitFrame
    lda #1
    sta boardUpdateInProgress
    rts

MarkDisplayDirty:
    lda #1
    sta displayDirty
    rts

WaitAnimationFrames:
    sta animationFrames
WaitAnimationFrames_Next:
    jsr WaitFrame
    lda TV_STANDARD
    bne WaitAnimationFrames_CountFrame
    ; PAL animations use 50 frames/second. Add one frame after every five
    ; NTSC frames so visible gameplay effects keep the same duration at 60 Hz.
    inc animationNtscDivider
    lda animationNtscDivider
    cmp #5
    bne WaitAnimationFrames_CountFrame
    lda #0
    sta animationNtscDivider
    jsr WaitFrame
WaitAnimationFrames_CountFrame:
    dec animationFrames
    bne WaitAnimationFrames_Next
    rts

AnimateNewGame:
    lda #1
    sta ghostSuppressed
    lda highlightedIndex
    cmp #$ff
    beq AnimateNewGame_TargetCleared
    jsr ClearCursorHighlights
    lda #$ff
    sta highlightedIndex
    sta highlightedSecondIndex
AnimateNewGame_TargetCleared:
    jsr ClearGameOverBlinds
    ; Repaint the side-control labels after restoring the grid bitmap.
    jsr DrawBottomLabels
    ; Let the lower-border phase publish the empty board without a ghost.
    jsr WaitFrame
    jsr PlayGridSetup

    lda #20
    sta highlightCellIndex
    lda #COLOR_WHITE
    sta rippleColor
    jsr FlashAnimationCellTwice

    lda #1
    sta rippleStep
AnimateNewGame_Ripple:
    ldx rippleStep
    lda RippleCellOrder,x
    sta highlightCellIndex
    lda #COLOR_LTBLUE
    cpx #(BOARD_CELLS - 1)
    bne AnimateNewGame_ColorReady
    lda #COLOR_YELLOW
AnimateNewGame_ColorReady:
    sta rippleColor
    jsr ShowAnimationCell
    lda rippleStep
    cmp #(BOARD_CELLS - 1)
    bne AnimateNewGame_RegularDelay
    lda #3
    bne AnimateNewGame_Wait
AnimateNewGame_RegularDelay:
    lda #1
AnimateNewGame_Wait:
    jsr WaitAnimationFrames
    jsr ClearHighlightCell
    inc rippleStep
    lda rippleStep
    cmp #BOARD_CELLS
    bne AnimateNewGame_Ripple

    lda #0
    sta ghostSuppressed
    jsr StopGridSetup
    jsr UpdatePlacement
    jsr UpdateCursorHighlight
    rts

AnimateGameOver:
    jsr InitTitleMusic
    lda #1
    sta ghostSuppressed
    jsr MarkDisplayDirty
    lda #(BOARD_CELLS - 1)
    sta rippleStep
AnimateGameOver_Ripple:
    ldx rippleStep
    lda RippleCellOrder,x
    sta highlightCellIndex
    lda #COLOR_RED
    sta rippleColor
    jsr ShowAnimationCell
    lda #1
    jsr WaitAnimationFrames
    jsr ClearHighlightCell
    dec rippleStep
    lda rippleStep
    cmp #$ff
    bne AnimateGameOver_Ripple

    lda #20
    sta highlightCellIndex
    lda #COLOR_RED
    sta rippleColor
    jsr FlashAnimationCellTwice
    jsr AnimateGameOverBlinds
    rts

AnimateGameOverBlinds:
    jsr PrepareGameOverKoala
    lda #1
    sta gameOverBlindActive
    lda #0
    sta blindRow
AnimateGameOverBlinds_Row:
    jsr PaintKoalaBandGray
    jsr WaitEndBandDelay
    jsr RevealKoalaBand
    inc blindRow
    lda blindRow
    cmp #5
    bne AnimateGameOverBlinds_Row
    jsr DrawGameOverScore
    jsr DrawGameOverPrompt
    jmp RunHighScorePage

PrepareGameOverKoala:
    lda #1
    sta gameOverBlindActive
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
    sta BORDER
    lda #GameOverKoalaBackground
    sta BACKGROUND
    jsr ClearBitmap
    jsr InitScreenColors
    lda VIC_MODE
    ora #%00010000
    sta VIC_MODE
    rts

RestoreGameScreen:
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    lda #0
    sta gameOverBlindActive
    sta BORDER
    sta BACKGROUND
    jsr ClearBitmap
    jsr InitScreenColors
    jsr DrawGameplayLogo
    jsr DrawGrid
    jsr DrawMainMascot
    jsr DrawBottomLabels
    jmp InitSpriteHardware

PaintKoalaBandGray:
    ldx blindRow
    lda KoalaColorBandLo,x
    sta PTR_LO
    lda KoalaColorBandHi,x
    sta PTR_HI
    ldy #0
    lda #COLOR_LTGRAY
PaintKoalaBandGray_Color:
    sta (PTR_LO),y
    iny
    cpy #200
    bne PaintKoalaBandGray_Color

    ldx blindRow
    lda KoalaBitmapBandLo,x
    sta PTR_LO
    lda KoalaBitmapBandHi,x
    sta PTR_HI
    ldx #6
    lda #$ff
PaintKoalaBandGray_BitmapPage:
    ldy #0
PaintKoalaBandGray_BitmapByte:
    sta (PTR_LO),y
    iny
    bne PaintKoalaBandGray_BitmapByte
    inc PTR_HI
    dex
    bne PaintKoalaBandGray_BitmapPage
    ldy #0
PaintKoalaBandGray_BitmapTail:
    sta (PTR_LO),y
    iny
    cpy #64
    bne PaintKoalaBandGray_BitmapTail
    rts

RevealKoalaBand:
    ldx blindRow
    lda GameOverKoalaBitmapLo,x
    sta SOURCE_LO
    lda GameOverKoalaBitmapHi,x
    sta SOURCE_HI
    lda KoalaBitmapBandLo,x
    sta PTR_LO
    lda KoalaBitmapBandHi,x
    sta PTR_HI
    jsr UnpackKoalaStream

    ldx blindRow
    lda GameOverKoalaScreenLo,x
    sta SOURCE_LO
    lda GameOverKoalaScreenHi,x
    sta SOURCE_HI
    lda KoalaScreenBandLo,x
    sta PTR_LO
    lda KoalaScreenBandHi,x
    sta PTR_HI
    jsr UnpackKoalaStream

    ldx blindRow
    lda GameOverKoalaColorLo,x
    sta SOURCE_LO
    lda GameOverKoalaColorHi,x
    sta SOURCE_HI
    lda KoalaColorBandLo,x
    sta PTR_LO
    lda KoalaColorBandHi,x
    sta PTR_HI
    jmp UnpackKoalaStream

UnpackKoalaStream:
    jsr ReadPackedByte
    beq UnpackKoalaStream_Done
    bmi UnpackKoalaStream_Repeat
    sta packedCount
UnpackKoalaStream_Literal:
    jsr ReadPackedByte
    ldy #0
    sta (PTR_LO),y
    jsr AdvanceKoalaTarget
    dec packedCount
    bne UnpackKoalaStream_Literal
    jmp UnpackKoalaStream
UnpackKoalaStream_Repeat:
    and #$7f
    sta packedCount
    jsr ReadPackedByte
    sta packedValue
UnpackKoalaStream_RepeatByte:
    ldy #0
    lda packedValue
    sta (PTR_LO),y
    jsr AdvanceKoalaTarget
    dec packedCount
    bne UnpackKoalaStream_RepeatByte
    jmp UnpackKoalaStream
UnpackKoalaStream_Done:
    rts

ReadPackedByte:
    ldy #0
    lda (SOURCE_LO),y
    pha
    inc SOURCE_LO
    bne ReadPackedByte_Ready
    inc SOURCE_HI
ReadPackedByte_Ready:
    pla
    rts

AdvanceKoalaTarget:
    inc PTR_LO
    bne AdvanceKoalaTarget_Done
    inc PTR_HI
AdvanceKoalaTarget_Done:
    rts

WaitEndBandDelay:
    lda TV_STANDARD
    beq WaitEndBandDelay_NTSC
    lda #5
    bne WaitEndBandDelay_Frames
WaitEndBandDelay_NTSC:
    lda #6
WaitEndBandDelay_Frames:
    jmp WaitAnimationFrames

ClearGameOverBlinds:
    lda #0
    sta gameOverBlindActive
    lda #GRID_TOP
    sta blindCharacterRow
ClearGameOverBlinds_Row:
    lda blindCharacterRow
    jsr SetScreenRowPointer
    ldy #GRID_LEFT
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
ClearGameOverBlinds_Column:
    sta (PTR_LO),y
    iny
    cpy #(GRID_LEFT + GRID_SPAN + 1)
    bne ClearGameOverBlinds_Column
    inc blindCharacterRow
    lda blindCharacterRow
    cmp #(GRID_TOP + GRID_SPAN + 1)
    bne ClearGameOverBlinds_Row
    lda #GRID_TOP
    sta blindCharacterRow
ClearGameOverBlinds_BitmapRow:
    lda blindCharacterRow
    jsr SetBitmapRowPointer
    lda #GRID_LEFT
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearGameOverBlinds_BitmapByte:
    sta (PTR_LO),y
    iny
    cpy #((GRID_SPAN + 1) * 8)
    bne ClearGameOverBlinds_BitmapByte
    inc blindCharacterRow
    lda blindCharacterRow
    cmp #(GRID_TOP + GRID_SPAN + 1)
    bne ClearGameOverBlinds_BitmapRow
    jmp DrawGrid

FlashAnimationCellTwice:
    jsr ShowAnimationCell
    lda #2
    jsr WaitAnimationFrames
    jsr ClearHighlightCell
    lda #1
    jsr WaitAnimationFrames
    jsr ShowAnimationCell
    lda #2
    jsr WaitAnimationFrames
    jsr ClearHighlightCell
    rts

ShowAnimationCell:
    lda rippleColor
    asl
    asl
    asl
    asl
    ora #COLOR_DKGRAY
    jsr ColorHighlightedCell
    jsr SetHighlightBitmapPointer
    jsr DrawHighlightRight
    jsr SetHighlightBitmapPointer
    jsr AddHighlightBottomOffset
    jsr DrawHighlightBottom
    rts

FindGroup:
    lda #0
    sta groupCount
    sta queueHead
    sta queueTail
    ldx #0
FindGroup_ClearVisited:
    sta visited,x
    inx
    cpx #BOARD_CELLS
    bne FindGroup_ClearVisited

    ldx activeIndex
    lda board,x
    beq FindGroup_Done
    sta groupValue
    lda #1
    sta visited,x
    lda activeIndex
    sta queue
    inc queueTail

FindGroup_Loop:
    lda queueHead
    cmp queueTail
    beq FindGroup_Done
    tax
    lda queue,x
    sta currentIndex
    inc queueHead
    ldx groupCount
    sta groupCells,x
    inc groupCount

    ldx currentIndex
    lda LeftNeighbor,x
    jsr TryGroupNeighbor
    ldx currentIndex
    lda RightNeighbor,x
    jsr TryGroupNeighbor
    ldx currentIndex
    lda UpNeighbor,x
    jsr TryGroupNeighbor
    ldx currentIndex
    lda DownNeighbor,x
    jsr TryGroupNeighbor
    jmp FindGroup_Loop
FindGroup_Done:
    rts

TryGroupNeighbor:
    cmp #$ff
    beq TryGroupNeighbor_Done
    sta neighborIndex
    tax
    lda visited,x
    bne TryGroupNeighbor_Done
    lda board,x
    cmp groupValue
    bne TryGroupNeighbor_Done
    lda #1
    sta visited,x
    ldx queueTail
    lda neighborIndex
    sta queue,x
    inc queueTail
TryGroupNeighbor_Done:
    rts

AddGroupScore:
    ldx mergeChainDepth
AddGroupScore_Multiplier:
    lda groupCount
    sta scoreAddCount
AddGroupScore_Die:
    lda groupValue
    sta scoreAddValue
AddGroupScore_Value:
    jsr IncrementScore
    dec scoreAddValue
    bne AddGroupScore_Value
    dec scoreAddCount
    bne AddGroupScore_Die
    dex
    bne AddGroupScore_Multiplier
    rts

IncrementScore:
    jmp IncrementScore4

UpdateScoreDisplay:
    jmp UpdateScoreDisplay4

DrawScore:
    jsr ClearScore
    lda #0
    sta scoreIndex
DrawScore_Digit:
    ldx scoreIndex
    lda ScoreDigits,x
    asl
    asl
    asl
    asl
    asl
    sta scoreGlyphOffset
    lda #0
    adc #0
    sta scoreGlyphPage
    lda scoreGlyphOffset
    clc
    adc #<LargeDigitFont
    sta SOURCE_LO
    lda scoreGlyphPage
    adc #>LargeDigitFont
    sta SOURCE_HI

    lda scoreIndex
    asl
    clc
    adc scoreStartCol
    sta scoreCharCol
    lda #0
    sta scoreHalf
DrawScore_Half:
    lda #SCORE_ROW
    clc
    adc scoreHalf
    jsr SetBitmapRowPointer
    lda scoreCharCol
    jsr AddColumnOffset
    ldy #0
DrawScore_Copy:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #16
    bne DrawScore_Copy
    lda SOURCE_LO
    clc
    adc #16
    sta SOURCE_LO
    bcc DrawScore_NextHalf
    inc SOURCE_HI
DrawScore_NextHalf:
    inc scoreHalf
    lda scoreHalf
    cmp #2
    bne DrawScore_Half
    inc scoreIndex
    lda scoreIndex
    cmp scoreDigitCount
    bne DrawScore_Digit

    lda #(COLOR_LTBLUE << 4) | COLOR_BLACK
    ldx #0
DrawScore_Color:
    sta SCREEN + (SCORE_ROW * 40) + SCORE_COL_FOUR,x
    sta SCREEN + ((SCORE_ROW + 1) * 40) + SCORE_COL_FOUR,x
    inx
    cpx #8
    bne DrawScore_Color
    rts

ClearScore:
    lda #SCORE_ROW
    jsr SetBitmapRowPointer
    lda #SCORE_COL_FOUR
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearScore_Top:
    sta (PTR_LO),y
    iny
    cpy #64
    bne ClearScore_Top
    lda #(SCORE_ROW + 1)
    jsr SetBitmapRowPointer
    lda #SCORE_COL_FOUR
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearScore_Bottom:
    sta (PTR_LO),y
    iny
    cpy #64
    bne ClearScore_Bottom
    rts

InitSpriteHardware:
    lda #0
    sta SPRITE_ENABLE
    sta SPRITE_X_MSB
    sta SPRITE_MULTICOLOR
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    sta SPRITE_PRIORITY
    ldx #0
InitSpriteHardware_BoardX:
    txa
    asl
    tay
    lda BoardSpriteX,x
    sta SPRITE0_X,y
    inx
    cpx #5
    bne InitSpriteHardware_BoardX
    jsr BuildShadowDiceSprites
    jsr SetupBottomSprites
    rts

BuildShadowDiceSprites:
    jmp BuildPreviewDiceSprites

RenderBoardRow:
    lda titleScreenActive
    beq RenderBoardRow_GameScreen
    rts
RenderBoardRow_GameScreen:
    ; Previous-row sprites have finished; disable them before assigning new Y values.
    lda uiEnableMask
    sta SPRITE_ENABLE
    lda gameOverBlindActive
    beq RenderBoardRow_Visible
    lda renderRow
    cmp blindRow
    bcc RenderBoardRow_Hidden
    beq RenderBoardRow_Hidden
RenderBoardRow_Visible:
    ldx renderRow
    lda RowIndexBase,x
    sta renderIndex
    lda BoardSpriteY,x
    sta renderSpriteY
    sta SPRITE0_Y
    sta SPRITE0_Y + 2
    sta SPRITE0_Y + 4
    sta SPRITE0_Y + 6
    sta SPRITE0_Y + 8
    lda #0
    sta spriteEnableMask
    ldx #0
RenderBoardRow_Column:
    txa
    clc
    adc renderIndex
    sta renderCellIndex
    tay
    lda displayValues,y
    beq RenderBoardRow_Next

RenderBoardRow_ShowValue:
    ldy renderCellIndex
    lda displaySpritePointers,y
    sta SPRITE0_PTR,x
    lda displayColors,y
    sta SPRITE0_COLOR,x
    lda SpriteBitMasks,x
    ora spriteEnableMask
    sta spriteEnableMask

RenderBoardRow_Next:
    inx
    cpx #5
    beq RenderBoardRow_Finish
    jmp RenderBoardRow_Column
RenderBoardRow_Finish:
    lda spriteEnableMask
    ora uiEnableMask
    sta SPRITE_ENABLE
    rts
RenderBoardRow_Hidden:
    rts

SetupPiecePreview:
    lda titleScreenActive
    beq SetupPiecePreview_GameScreen
    rts
SetupPiecePreview_GameScreen:
    lda chainReactionActive
    beq SetupPiecePreview_CheckEffect
    ; The chain banner owns UI sprites 5-7 during the inter-merge pause.
    rts
SetupPiecePreview_CheckEffect:
    lda fireworkActive
    beq SetupPiecePreview_CheckScreen
    ; Merge effects own sprites 5-7 and their enable mask until completion.
    rts
SetupPiecePreview_CheckScreen:
    lda gameOverBlindActive
    beq SetupPiecePreview_Visible
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
    rts
SetupPiecePreview_Visible:
    lda gameOver
    beq SetupPiecePreview_Active
    lda #0
    sta uiEnableMask
    sta SPRITE_X_MSB
    rts

SetupPiecePreview_Active:
    ldy pieceValue0
    lda DiceSpritePointers,y
    sta SPRITE0_PTR + 5
    lda DiceColors,y
    sta SPRITE0_COLOR + 5

    lda pieceCount
    cmp #2
    bne SetupPiecePreview_Single
    ldy pieceValue1
    lda DiceSpritePointers,y
    sta SPRITE0_PTR + 6
    lda DiceColors,y
    sta SPRITE0_COLOR + 6
    ldx orientation
    lda PiecePreviewX0,x
    sta SPRITE0_X + 10
    lda PiecePreviewY0,x
    sta SPRITE0_Y + 10
    lda PiecePreviewX1,x
    sta SPRITE0_X + 12
    lda PiecePreviewY1,x
    sta SPRITE0_Y + 12
    lda #%01100000
    sta uiEnableMask
    sta SPRITE_X_MSB
    rts

SetupPiecePreview_Single:
    lda #27
    sta SPRITE0_X + 10
    lda #PIECE_PREVIEW_Y
    sta SPRITE0_Y + 10
    lda #%00100000
    sta uiEnableMask
    sta SPRITE_X_MSB
    rts

SetupBottomSprites:
    lda chainReactionActive
    bne SetupBottomSprites_Return
    jmp SetupBottomSpritesImpl
SetupBottomSprites_Return:
    rts

EnableBottomSprites:
    ; Row 4 may already be visible when the side controls are retargeted.
    ; Preserve sprites 0-4 instead of replacing the complete enable mask.
    ora SPRITE_ENABLE
    sta SPRITE_ENABLE
    rts

ConfigureNewGameSprite:
    lda #$76
    sta SPRITE0_PTR + 6
    lda newGameFocused
    beq ConfigureNewGameSprite_Idle
    lda #COLOR_YELLOW
    bne ConfigureNewGameSprite_ColorReady
ConfigureNewGameSprite_Idle:
    lda #COLOR_LTBLUE
ConfigureNewGameSprite_ColorReady:
    sta SPRITE0_COLOR + 6
    lda #NEW_GAME_ICON_X
    sta SPRITE0_X + 12
    lda #SIDE_CONTROL_ICON_Y
    sta SPRITE0_Y + 12
    rts

; Focus colors are refreshed by the UI raster phase on the next frame.
UpdateBottomButtonColors:
    rts

ClearBitmap:
    lda #<BITMAP
    sta PTR_LO
    lda #>BITMAP
    sta PTR_HI
    ; Clear only the 8,000 visible bytes; $7f40-$7fff holds utility code.
    ldx #31
    lda #0
ClearBitmap_Page:
    ldy #0
ClearBitmap_Byte:
    sta (PTR_LO),y
    iny
    bne ClearBitmap_Byte
    inc PTR_HI
    dex
    bne ClearBitmap_Page
    ldy #0
ClearBitmap_FinalVisibleBytes:
    sta (PTR_LO),y
    iny
    cpy #64
    bne ClearBitmap_FinalVisibleBytes
    rts

InitScreenColors:
    lda #<SCREEN
    sta PTR_LO
    lda #>SCREEN
    sta PTR_HI
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    ldx #4
InitScreenColors_Page:
    ldy #0
InitScreenColors_Byte:
    sta (PTR_LO),y
    iny
    bne InitScreenColors_Byte
    inc PTR_HI
    dex
    bne InitScreenColors_Page
    rts

UpdateCursorHighlight:
    ldx cursorY
    lda RowIndexBase,x
    clc
    adc cursorX
    sta highlightedIndex
    lda #$ff
    sta highlightedSecondIndex
    lda pieceCount
    cmp #2
    bne UpdateCursorHighlight_Done
    lda secondIndex
    sta highlightedSecondIndex
UpdateCursorHighlight_Done:
    rts

UpdatePreviewBlink:
    lda highlightedIndex
    cmp #$ff
    beq UpdatePreviewBlink_Done
    lda frameCounter
    lsr
    lsr
    ; Hold each normal/inverse preview phase for 16 video frames.
    lsr
    and #3
    cmp highlightPhase
    beq UpdatePreviewBlink_Done
    sta highlightPhase
    jmp MarkDisplayDirty
UpdatePreviewBlink_Done:
    rts

ClearCursorHighlights:
    ; Cursor selection is represented by its blinking preview dice only.
    ; Never erase bitmap edges here: those pixels belong to the shared grid.
    rts

ClearHighlightCell:
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    jsr ColorHighlightedCell
    jsr SetHighlightBitmapPointer
    jsr EraseHighlightRight
    jsr SetHighlightBitmapPointer
    jsr AddHighlightBottomOffset
    jmp EraseHighlightBottom

ColorHighlightedCell:
    sta cellBorderColor
    ldx highlightCellIndex
    lda CellScreenLo,x
    sta PTR_LO
    lda CellScreenHi,x
    sta PTR_HI
    ldx #4
ColorHighlightedCell_Row:
    ldy #3
ColorHighlightedCell_Column:
    lda cellBorderColor
    sta (PTR_LO),y
    dey
    bpl ColorHighlightedCell_Column
    lda PTR_LO
    clc
    adc #40
    sta PTR_LO
    bcc ColorHighlightedCell_NextRow
    inc PTR_HI
ColorHighlightedCell_NextRow:
    dex
    bne ColorHighlightedCell_Row
    rts

SetHighlightBitmapPointer:
    ldx highlightCellIndex
    lda CellBitmapLo,x
    sta PTR_LO
    lda CellBitmapHi,x
    sta PTR_HI
    rts

AdvanceHighlightBitmapRow:
    lda PTR_LO
    clc
    adc #$40
    sta PTR_LO
    lda PTR_HI
    adc #1
    sta PTR_HI
    rts

DrawHighlightRight:
    ldx #0
DrawHighlightRight_Row:
    ldy HighlightRightStart,x
DrawHighlightRight_Byte:
    lda (PTR_LO),y
    ora #$03
    sta (PTR_LO),y
    iny
    cpy #32
    bne DrawHighlightRight_Byte
    jsr AdvanceHighlightBitmapRow
    inx
    cpx #4
    bne DrawHighlightRight_Row
    rts

EraseHighlightRight:
    ldx #0
EraseHighlightRight_Row:
    ldy HighlightRightStart,x
EraseHighlightRight_Byte:
    lda (PTR_LO),y
    and #$fc
    sta (PTR_LO),y
    iny
    cpy #32
    bne EraseHighlightRight_Byte
    jsr AdvanceHighlightBitmapRow
    inx
    cpx #4
    bne EraseHighlightRight_Row
    rts

AddHighlightBottomOffset:
    lda PTR_LO
    clc
    adc #$c0
    sta PTR_LO
    lda PTR_HI
    adc #3
    sta PTR_HI
    rts

DrawHighlightBottom:
    ldy #6
    lda (PTR_LO),y
    ora #$3f
    sta (PTR_LO),y
    iny
    lda (PTR_LO),y
    ora #$3f
    sta (PTR_LO),y
    ldy #14
DrawHighlightBottom_Full:
    lda #$ff
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    tya
    clc
    adc #7
    tay
    cpy #38
    bne DrawHighlightBottom_Full
    rts

EraseHighlightBottom:
    ldy #6
    lda (PTR_LO),y
    and #$c0
    sta (PTR_LO),y
    iny
    lda (PTR_LO),y
    and #$c0
    sta (PTR_LO),y
    ldy #14
EraseHighlightBottom_Full:
    lda #0
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    tya
    clc
    adc #7
    tay
    cpy #38
    bne EraseHighlightBottom_Full
    rts

DrawGrid:
    lda #0
    sta lineIndex
DrawGrid_Vertical:
    ldx lineIndex
    lda GridColumns,x
    sta gridColumn
    jsr DrawVerticalLine
    inc lineIndex
    lda lineIndex
    cmp #GRID_LINES
    bne DrawGrid_Vertical
    lda #0
    sta lineIndex
DrawGrid_Horizontal:
    ldx lineIndex
    lda GridRows,x
    sta gridRow
    jsr DrawHorizontalLine
    inc lineIndex
    lda lineIndex
    cmp #GRID_LINES
    bne DrawGrid_Horizontal
    rts

DrawGameplayLogo:
    jmp DrawGameplayBitmapLogo

DrawGameOver:
    lda #<GameOverLabel
    sta SOURCE_LO
    lda #>GameOverLabel
    sta SOURCE_HI
    lda #<(BITMAP + (GAME_OVER_COL * 8))
    sta PTR_LO
    lda #>(BITMAP + (GAME_OVER_COL * 8))
    sta PTR_HI
    lda #GAME_OVER_CHARS
    sta labelColumn
DrawGameOver_Character:
    ldy #0
    jsr DrawGameOver_Half

    clc
    lda PTR_LO
    adc #$40
    sta PTR_LO
    lda PTR_HI
    adc #1
    sta PTR_HI
    ldy #4
    jsr DrawGameOver_Half

    sec
    lda PTR_LO
    sbc #$30
    sta PTR_LO
    lda PTR_HI
    sbc #1
    sta PTR_HI
    clc
    lda SOURCE_LO
    adc #8
    sta SOURCE_LO
    dec labelColumn
    bne DrawGameOver_Character

    ldx #((GAME_OVER_CHARS * 2) - 1)
    lda #COLOR_RED
SetGameOverColors_Character:
    sta COLOR_RAM + GAME_OVER_COL,x
    sta COLOR_RAM + 40 + GAME_OVER_COL,x
    dex
    bpl SetGameOverColors_Character
    jsr DrawGameOverPrompt
    rts

DrawGameOver_Half:
    lda #4
    sta workColumn
DrawGameOver_Row:
    sty workRow
    lda (SOURCE_LO),y
    sta shadowSourceByte
    lsr
    lsr
    lsr
    lsr
    tax
    lda GameOverMulticolorExpand,x
    sta cellBorderColor
    lda shadowSourceByte
    and #$0f
    tax
    lda GameOverMulticolorExpand,x
    sta packedValue

    ldy workRow
    tya
    and #3
    asl
    tay
    lda cellBorderColor
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    tya
    clc
    adc #7
    tay
    lda packedValue
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    ldy workRow
    iny
    dec workColumn
    bne DrawGameOver_Row
    rts

DrawVerticalLine:
    lda #GRID_TOP
    sta workRow
DrawVerticalLine_Row:
    lda workRow
    jsr SetBitmapRowPointer
    lda gridColumn
    jsr AddColumnOffset
    ldy #0
    lda #%11000000
DrawVerticalLine_Byte:
    sta (PTR_LO),y
    iny
    cpy #8
    bne DrawVerticalLine_Byte
    inc workRow
    lda workRow
    cmp #(GRID_TOP + GRID_SPAN)
    bne DrawVerticalLine_Row
    rts

DrawHorizontalLine:
    lda gridRow
    jsr SetBitmapRowPointer
    lda #GRID_LEFT
    sta workColumn
DrawHorizontalLine_Column:
    lda workColumn
    jsr AddColumnOffset
    ldy #0
    lda #$ff
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    lda gridRow
    jsr SetBitmapRowPointer
    inc workColumn
    lda workColumn
    cmp #(GRID_LEFT + GRID_SPAN)
    bne DrawHorizontalLine_Column
    lda gridRow
    jsr SetBitmapRowPointer
    lda #(GRID_LEFT + GRID_SPAN)
    jsr AddColumnOffset
    ldy #0
    lda #%11000000
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    rts

DrawBottomLabels:
    lda #<NewGameLabel
    sta SOURCE_LO
    lda #>NewGameLabel
    sta SOURCE_HI
    lda #NEW_GAME_LABEL_COL
    sta labelColumn
    jsr DrawLabel32
    lda #<SettingsLabel
    sta SOURCE_LO
    lda #>SettingsLabel
    sta SOURCE_HI
    lda #SETTINGS_LABEL_COL
    sta labelColumn
    jsr DrawLabel32
    rts

DrawMainMascot:
    lda #<MainMascotBitmapData
    sta SOURCE_LO
    lda #>MainMascotBitmapData
    sta SOURCE_HI
    lda #MASCOT_ROW_START
    sta workRow
DrawMainMascot_BitmapRow:
    lda workRow
    jsr SetBitmapRowPointer
    lda #1
    jsr AddColumnOffset
    ldy #0
DrawMainMascot_BitmapByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #64
    bne DrawMainMascot_BitmapByte
    lda SOURCE_LO
    clc
    adc #64
    sta SOURCE_LO
    bcc DrawMainMascot_BitmapSourceReady
    inc SOURCE_HI
DrawMainMascot_BitmapSourceReady:
    inc workRow
    lda workRow
    cmp #MASCOT_ROW_END
    bne DrawMainMascot_BitmapRow

    lda #<MainMascotScreenData
    sta SOURCE_LO
    lda #>MainMascotScreenData
    sta SOURCE_HI
    lda #MASCOT_ROW_START
    sta workRow
DrawMainMascot_ScreenRow:
    lda workRow
    jsr SetScreenRowPointer
    inc PTR_LO
    bne DrawMainMascot_ScreenReady
    inc PTR_HI
DrawMainMascot_ScreenReady:
    ldy #0
DrawMainMascot_ScreenByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #8
    bne DrawMainMascot_ScreenByte
    lda SOURCE_LO
    clc
    adc #8
    sta SOURCE_LO
    bcc DrawMainMascot_ScreenSourceReady
    inc SOURCE_HI
DrawMainMascot_ScreenSourceReady:
    inc workRow
    lda workRow
    cmp #MASCOT_ROW_END
    bne DrawMainMascot_ScreenRow
    rts

DrawLabel32:
    lda #SIDE_CONTROL_LABEL_ROW
    jsr SetBitmapRowPointer
    lda labelColumn
    jsr AddColumnOffset
    ldy #0
DrawLabel32_Copy:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #32
    bne DrawLabel32_Copy
    lda #<(SCREEN + (SIDE_CONTROL_LABEL_ROW * 40))
    sta PTR_LO
    lda #>(SCREEN + (SIDE_CONTROL_LABEL_ROW * 40))
    sta PTR_HI
    ldy labelColumn
    lda #(COLOR_LTBLUE << 4) | COLOR_BLACK
    ldx #4
DrawLabel32_Color:
    sta (PTR_LO),y
    iny
    dex
    bne DrawLabel32_Color
    rts

SetBitmapRowPointer:
    tax
    lda BitmapRowLo,x
    sta PTR_LO
    lda BitmapRowHi,x
    sta PTR_HI
    rts

SetScreenRowPointer:
    tax
    lda ScreenRowLo,x
    sta PTR_LO
    lda ScreenRowHi,x
    sta PTR_HI
    rts

AddColumnOffset:
    tax
    lda PTR_LO
    clc
    adc ColumnOffsetLo,x
    sta PTR_LO
    lda PTR_HI
    adc ColumnOffsetHi,x
    sta PTR_HI
    rts

RowIndexBase:
!byte 0, 5, 10, 15, 20
CellScreenLo:
!byte <(SCREEN+130),<(SCREEN+134),<(SCREEN+138),<(SCREEN+142),<(SCREEN+146)
!byte <(SCREEN+290),<(SCREEN+294),<(SCREEN+298),<(SCREEN+302),<(SCREEN+306)
!byte <(SCREEN+450),<(SCREEN+454),<(SCREEN+458),<(SCREEN+462),<(SCREEN+466)
!byte <(SCREEN+610),<(SCREEN+614),<(SCREEN+618),<(SCREEN+622),<(SCREEN+626)
!byte <(SCREEN+770),<(SCREEN+774),<(SCREEN+778),<(SCREEN+782),<(SCREEN+786)
CellScreenHi:
!byte >(SCREEN+130),>(SCREEN+134),>(SCREEN+138),>(SCREEN+142),>(SCREEN+146)
!byte >(SCREEN+290),>(SCREEN+294),>(SCREEN+298),>(SCREEN+302),>(SCREEN+306)
!byte >(SCREEN+450),>(SCREEN+454),>(SCREEN+458),>(SCREEN+462),>(SCREEN+466)
!byte >(SCREEN+610),>(SCREEN+614),>(SCREEN+618),>(SCREEN+622),>(SCREEN+626)
!byte >(SCREEN+770),>(SCREEN+774),>(SCREEN+778),>(SCREEN+782),>(SCREEN+786)
CellBitmapLo:
!byte <$6410,<$6430,<$6450,<$6470,<$6490
!byte <$6910,<$6930,<$6950,<$6970,<$6990
!byte <$6e10,<$6e30,<$6e50,<$6e70,<$6e90
!byte <$7310,<$7330,<$7350,<$7370,<$7390
!byte <$7810,<$7830,<$7850,<$7870,<$7890
CellBitmapHi:
!byte >$6410,>$6430,>$6450,>$6470,>$6490
!byte >$6910,>$6930,>$6950,>$6970,>$6990
!byte >$6e10,>$6e30,>$6e50,>$6e70,>$6e90
!byte >$7310,>$7330,>$7350,>$7370,>$7390
!byte >$7810,>$7830,>$7850,>$7870,>$7890
HighlightRightStart:
!byte 26,24,24,24
RippleCellOrder:
!byte 20,15,10,5,0,1,2,3,4,9,14,19,24,23,22,21,16,11,6,7,8,13,18,17,12
GridColumns:
!byte 10, 14, 18, 22, 26, 30
GridRows:
!byte 3, 7, 11, 15, 19, 23

LeftNeighbor:
!byte $ff,0,1,2,3, $ff,5,6,7,8, $ff,10,11,12,13, $ff,15,16,17,18, $ff,20,21,22,23
RightNeighbor:
!byte 1,2,3,4,$ff, 6,7,8,9,$ff, 11,12,13,14,$ff, 16,17,18,19,$ff, 21,22,23,24,$ff
UpNeighbor:
!byte $ff,$ff,$ff,$ff,$ff, 0,1,2,3,4, 5,6,7,8,9, 10,11,12,13,14, 15,16,17,18,19
DownNeighbor:
!byte 5,6,7,8,9, 10,11,12,13,14, 15,16,17,18,19, 20,21,22,23,24, $ff,$ff,$ff,$ff,$ff

BoardSpriteX:
!byte 108,140,172,204,236
BoardSpriteY:
!byte 81,113,145,177,209
PiecePreviewX0:
!byte 27,39,51,39
PiecePreviewY0:
!byte PIECE_PREVIEW_Y,PIECE_PREVIEW_Y,PIECE_PREVIEW_Y,PIECE_PREVIEW_Y + 24
PiecePreviewX1:
!byte 51,39,27,39
PiecePreviewY1:
!byte PIECE_PREVIEW_Y,PIECE_PREVIEW_Y + 24,PIECE_PREVIEW_Y,PIECE_PREVIEW_Y
SpriteBitMasks:
!byte 1,2,4,8,16
DiceSpritePointers:
!byte 0,$70,$71,$72,$73,$74,$75
DiceColors:
!byte COLOR_BLACK,COLOR_LTGRAY,COLOR_LTBLUE,COLOR_GREEN,COLOR_PURPLE,COLOR_YELLOW,COLOR_CYAN
NextRasterLines:
; The optimized row setup fits before the next Y trigger while leaving a full
; idle raster line after the previous 21-line sprite has finished.
!byte 104,136,168,200,232,64

ColumnOffsetLo:
!for column, 0, 39 { !byte <(column * 8) }
ColumnOffsetHi:
!for column, 0, 39 { !byte >(column * 8) }
BitmapRowLo:
!for row, 0, 24 { !byte <(BITMAP + (row * 320)) }
BitmapRowHi:
!for row, 0, 24 { !byte >(BITMAP + (row * 320)) }
ScreenRowLo:
!for row, 0, 24 { !byte <(SCREEN + (row * 40)) }
ScreenRowHi:
!for row, 0, 24 { !byte >(SCREEN + (row * 40)) }
KoalaBitmapBandLo:
!for band, 0, 4 { !byte <(BITMAP + (band * 1600)) }
KoalaBitmapBandHi:
!for band, 0, 4 { !byte >(BITMAP + (band * 1600)) }
KoalaScreenBandLo:
!for band, 0, 4 { !byte <(SCREEN + (band * 200)) }
KoalaScreenBandHi:
!for band, 0, 4 { !byte >(SCREEN + (band * 200)) }
KoalaColorBandLo:
!for band, 0, 4 { !byte <(COLOR_RAM + (band * 200)) }
KoalaColorBandHi:
!for band, 0, 4 { !byte >(COLOR_RAM + (band * 200)) }

board:             !fill BOARD_CELLS,0
renderBoard:       !fill BOARD_CELLS,0
displayValues:     !fill BOARD_CELLS,0
displayColors:     !fill BOARD_CELLS,0
displaySpritePointers: !fill BOARD_CELLS,0
mergeCells:        !fill BOARD_CELLS,0
visited:           !fill BOARD_CELLS,0
queue:             !fill BOARD_CELLS,0
groupCells:        !fill BOARD_CELLS,0

cursorX:           !byte 0
cursorY:           !byte 0
orientation:       !byte 0
pieceCount:        !byte 1
pieceValue0:       !byte 1
pieceValue1:       !byte 1
placementValid:    !byte 0
ghostSuppressed:   !byte 0
originIndex:       !byte 0
secondIndex:       !byte $ff
gameOver:          !byte 0
singlesOnlyMode:   !byte 0
doubleSpaceAvailable: !byte 0
boardDirty:        !byte 0
displayDirty:      !byte 1
boardUpdateInProgress: !byte 0
rngSeed:           !byte 1
boardFiveCount:    !byte 0
scoreThousands:    !byte 0
scoreHundreds:     !byte 0
scoreTens:         !byte 0
scoreOnes:         !byte 0
ScoreDigits:       !byte 0,0,0,0
scoreDigitCount:   !byte 1
scoreStartCol:     !byte SCORE_COL_ONE
scoreIndex:        !byte 0
scoreCharCol:      !byte 0
scoreHalf:         !byte 0
scoreGlyphOffset:  !byte 0
scoreGlyphPage:    !byte 0
action:            !byte 0
joystickLatch:     !byte 0
joystickFireState: !byte 0
frameCounter:      !byte 0
lastFrame:         !byte 0
irqPhase:          !byte 0
renderRow:         !byte 0
renderIndex:       !byte 0
renderColumn:      !byte 0
renderCellIndex:   !byte 0
renderSpriteY:     !byte 0
spriteEnableMask:  !byte 0
uiEnableMask:      !byte $e0
activeIndex:       !byte 0
currentIndex:      !byte 0
neighborIndex:     !byte 0
groupValue:        !byte 0
groupCount:        !byte 0
queueHead:         !byte 0
queueTail:         !byte 0
scoreAddCount:     !byte 0
scoreAddValue:     !byte 0
searchX:           !byte 0
searchY:           !byte 0
searchOrientation: !byte 0
gridColumn:        !byte 0
gridRow:           !byte 0
workColumn:        !byte 0
workRow:           !byte 0
lineIndex:         !byte 0
labelColumn:       !byte 0
highlightedIndex:  !byte $ff
highlightedSecondIndex: !byte $ff
highlightCellIndex: !byte 0
cellBorderColor:   !byte 0
highlightVisible:  !byte 1
highlightPhase:    !byte 0
mergeAnimating:    !byte 0
mergeFlashPhase:   !byte 0
mergeFlashColor:   !byte COLOR_WHITE
mergeChainDepth:   !byte 0
animationFrames:   !byte 0
animationNtscDivider: !byte 0
rippleColor:       !byte COLOR_LTBLUE
rippleStep:        !byte 0
blindRow:          !byte 0
gameOverBlindActive: !byte 0
blindFillColor:    !byte 0
; 0=inactive, 1=single-sprite score flight, 2=three-sprite particle burst.
fireworkActive:    !byte 0
chainReactionActive: !byte 0
blindCharacterRow: !byte 0
fireworkBaseX:     !byte 0
fireworkBaseY:     !byte 0
mergeCalloutIndex: !byte 0
shadowSourceByte:  !byte 0
titleCopyRemainder: !byte 0
titleBand:          !byte 0
titleScreenActive: !byte 0
packedCount:       !byte 0
packedValue:       !byte 0

!source "src/assets/title_screen.asm"
!source "src/assets/merge_firework_code.asm"
!source "src/assets/high_scores.asm"
!source "src/assets/sound_effects.asm"
!source "src/assets/title_prompt.asm"
!source "src/assets/score_four_digits.asm"
!source "src/assets/merge_chain_sounds.asm"
!source "src/assets/joystick_chord.asm"
!source "src/assets/credits_mascot.asm"
!source "src/assets/credits_font.asm"
!source "src/assets/presents_screen.asm"
!source "src/assets/title_music.asm"
!source "src/assets/merge_diagonal_sweep.asm"
!source "src/assets/merge_mascot_callout.asm"
!source "src/assets/bottom_controls.asm"
!source "src/assets/settings_screen.asm"
!source "src/assets/settings_art.asm"
!source "src/assets/main_mascot.asm"
!source "src/assets/shadow_sprite_workspace.asm"
!source "src/assets/preview_dice_effects.asm"
!source "src/assets/game_over_prompt.asm"
!source "src/assets/merge_shake.asm"
!source "src/assets/merge_firework_helpers.asm"
!source "src/assets/gameplay_logo.asm"
!source "src/assets/game_over_screen.asm"
!source "src/assets/merge_firework_paths.asm"
!source "src/assets/chain_reaction_sprite.asm"
!source "src/assets/merge_grid_sweep.asm"
!source "src/assets/merge_firework_sprite.asm"
!source "src/assets/die_one.asm"
!source "src/assets/die_two.asm"
!source "src/assets/die_three.asm"
!source "src/assets/die_four.asm"
!source "src/assets/die_five.asm"
!source "src/assets/die_six.asm"
!source "src/assets/new_game.asm"
!source "src/assets/settings.asm"
!source "src/assets/bottom_labels.asm"
!source "src/assets/bottom_icon_control.asm"
!source "src/assets/large_digits.asm"
!source "src/assets/game_over.asm"
