!cpu 6510

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
IRQ_VECTOR      = $0314
CIA1_IRQ        = $dc0d
JOYSTICK2       = $dc00
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
COLOR_LTBLUE    = 14
COLOR_LTGRAY    = 15

GRID_LEFT       = 10
GRID_TOP        = 1
GRID_SPAN       = 20
GRID_LINES      = 6
BOARD_CELLS     = 25
SCORE_ROW       = 1
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
    jsr ShowTitleScreen
    jsr WaitForTitleStart
    jsr ClearBitmap
    jsr InitScreenColors
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
    jsr UpdateHighlightFlash
    jsr ReadAction
    lda action
    beq MainLoop
    cmp #ACTION_NEW
    beq MainLoop_NewGame
    cmp #ACTION_DEBUG_FILL
    beq MainLoop_DebugFill

    lda gameOver
    bne MainLoop

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
    cmp #ACTION_PLACE
    beq MainLoop_Place
    jmp MainLoop

MainLoop_NewGame:
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

MainLoop_Left:
    lda cursorX
    beq MainLoop_Update
    dec cursorX
    jmp MainLoop_Update

MainLoop_Right:
    lda cursorX
    cmp #4
    beq MainLoop_Update
    inc cursorX
    jmp MainLoop_Update

MainLoop_Up:
    lda cursorY
    beq MainLoop_Update
    dec cursorY
    jmp MainLoop_Update

MainLoop_Down:
    lda cursorY
    cmp #4
    beq MainLoop_Update
    inc cursorY
    jmp MainLoop_Update

MainLoop_Rotate:
    inc orientation
    lda orientation
    and #3
    sta orientation

MainLoop_Update:
    jsr UpdatePlacement
    jsr UpdateCursorHighlight
    jmp MainLoop

MainLoop_Place:
    lda placementValid
    bne MainLoop_PlaceValid
    jmp MainLoop
MainLoop_PlaceValid:
    jsr PlaceCurrentPiece
    jmp MainLoop

InitVideo:
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
    lda #0
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND

    lda #<TitleBitmapData
    sta SOURCE_LO
    lda #>TitleBitmapData
    sta SOURCE_HI
    lda #<BITMAP
    sta PTR_LO
    lda #>BITMAP
    sta PTR_HI
    ldx #31
    lda #64
    jsr CopyTitleBlock

    lda #<TitleScreenData
    sta SOURCE_LO
    lda #>TitleScreenData
    sta SOURCE_HI
    lda #<SCREEN
    sta PTR_LO
    lda #>SCREEN
    sta PTR_HI
    ldx #3
    lda #232
    jsr CopyTitleBlock

    lda #<TitleColorData
    sta SOURCE_LO
    lda #>TitleColorData
    sta SOURCE_HI
    lda #<COLOR_RAM
    sta PTR_LO
    lda #>COLOR_RAM
    sta PTR_HI
    ldx #3
    lda #232
    jsr CopyTitleBlock

    lda VIC_MODE
    ora #%00010000
    sta VIC_MODE
    rts

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
WaitForTitleStart_Drain:
    jsr SCNKEY
    jsr GETIN
    bne WaitForTitleStart_Drain
WaitForTitleStart_ReleaseFire:
    lda JOYSTICK2
    and #$10
    beq WaitForTitleStart_ReleaseFire
WaitForTitleStart_Input:
    jsr SCNKEY
    jsr GETIN
    cmp #' '
    beq WaitForTitleStart_Done
    cmp #13
    beq WaitForTitleStart_Done
    lda JOYSTICK2
    and #$10
    bne WaitForTitleStart_Input
WaitForTitleStart_Done:
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    rts

InitRasterIRQ:
    lda #<RasterIRQ
    sta IRQ_VECTOR
    lda #>RasterIRQ
    sta IRQ_VECTOR + 1
    lda #48
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
    jsr RenderBoardRow
    jmp RasterIRQ_Schedule

RasterIRQ_UI:
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
    rts

ReadAction:
    lda #ACTION_NONE
    sta action

    jsr SCNKEY
    jsr GETIN
    beq ReadAction_Joystick
    cmp #'A'
    beq ReadAction_Left
    cmp #'D'
    beq ReadAction_Right
    cmp #'W'
    beq ReadAction_Up
    cmp #'S'
    beq ReadAction_Down
    cmp #'R'
    beq ReadAction_Rotate
    cmp #'Q'
    beq ReadAction_Rotate
    cmp #' '
    beq ReadAction_Place
    cmp #13
    beq ReadAction_Place
    cmp #'N'
    beq ReadAction_New
    cmp #'.'
    beq ReadAction_DebugFill
    rts

ReadAction_Joystick:
    lda JOYSTICK2
    and #$1f
    cmp #$1f
    bne ReadAction_JoyPressed
    lda #0
    sta joystickLatch
    rts
ReadAction_JoyPressed:
    lda joystickLatch
    bne ReadAction_Done
    lda #1
    sta joystickLatch
    lda JOYSTICK2
    and #$04
    beq ReadAction_Left
    lda JOYSTICK2
    and #$08
    beq ReadAction_Right
    lda JOYSTICK2
    and #$01
    beq ReadAction_Up
    lda JOYSTICK2
    and #$02
    beq ReadAction_Down
    lda JOYSTICK2
    and #$10
    beq ReadAction_Place
ReadAction_Done:
    rts

ReadAction_Left:
    lda #ACTION_LEFT
    bne ReadAction_Store
ReadAction_Right:
    lda #ACTION_RIGHT
    bne ReadAction_Store
ReadAction_Up:
    lda #ACTION_UP
    bne ReadAction_Store
ReadAction_Down:
    lda #ACTION_DOWN
    bne ReadAction_Store
ReadAction_Rotate:
    lda #ACTION_ROTATE
    bne ReadAction_Store
ReadAction_Place:
    lda #ACTION_PLACE
    bne ReadAction_Store
ReadAction_New:
    lda #ACTION_NEW
    bne ReadAction_Store
ReadAction_DebugFill:
    lda #ACTION_DEBUG_FILL
ReadAction_Store:
    sta action
    rts

ResetGameLocked:
    lda #1
    sta boardUpdateInProgress
    ldx #0
    lda #0
ResetGame_ClearBoard:
    sta board,x
    inx
    cpx #BOARD_CELLS
    bne ResetGame_ClearBoard

    lda #0
    sta scoreHundreds
    sta scoreTens
    sta scoreOnes
    sta gameOver
    sta singlesOnlyMode
    sta joystickLatch
    sta BORDER
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
    rts

CheckAnyPlacement:
    lda #1
    sta ghostSuppressed
    lda cursorX
    sta savedCursorX
    lda cursorY
    sta savedCursorY
    lda orientation
    sta savedOrientation

    lda #0
    sta searchOrientation
CheckAnyPlacement_Orientation:
    lda #0
    sta searchY
CheckAnyPlacement_Row:
    lda #0
    sta searchX
CheckAnyPlacement_Column:
    lda searchX
    sta cursorX
    lda searchY
    sta cursorY
    lda searchOrientation
    sta orientation
    jsr UpdatePlacement
    lda placementValid
    bne CheckAnyPlacement_Found

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
    jmp CheckAnyPlacement_RestoreOnly

CheckAnyPlacement_Found:
    lda #0
    sta gameOver
CheckAnyPlacement_RestoreOnly:
    lda savedCursorX
    sta cursorX
    lda savedCursorY
    sta cursorY
    lda savedOrientation
    sta orientation
    lda gameOver
    bne CheckAnyPlacement_RestoreGhost
    jsr UpdatePlacement
CheckAnyPlacement_RestoreGhost:
    lda #0
    sta ghostSuppressed
CheckAnyPlacement_Done:
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
    lda #0
    sta mergeChainDepth
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
SyncRenderBoard_Done:
    rts

BuildDisplayBoard:
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
    lda pieceValue0
    bne BuildDisplayBoard_ValueReady
BuildDisplayBoard_CheckSecond:
    lda pieceCount
    cmp #2
    bne BuildDisplayBoard_Empty
    cpx secondIndex
    bne BuildDisplayBoard_Empty
    lda pieceValue1
    bne BuildDisplayBoard_ValueReady

BuildDisplayBoard_ShadowOrigin:
    lda pieceValue0
    bne BuildDisplayBoard_ShadowReady
BuildDisplayBoard_ShadowSecond:
    lda pieceValue1
BuildDisplayBoard_ShadowReady:
    sta displayValues,x
    tay
    lda ShadowDiceSpritePointers,y
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
    jsr AddGroupScore

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
    lda #CHAIN_MERGE_PAUSE_FRAMES
    jmp WaitAnimationFrames

AnimateMergeGroup:
    lda mergeChainDepth
    cmp #2
    bcc AnimateMergeGroup_FirstColor
    lda #COLOR_CYAN
    bne AnimateMergeGroup_StoreColor
AnimateMergeGroup_FirstColor:
    lda #COLOR_WHITE
AnimateMergeGroup_StoreColor:
    sta mergeFlashColor
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
    jmp RunDiceFlash

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
    lda #3
    jsr WaitAnimationFrames
    lda #1
    sta mergeFlashPhase
    lda #3
    jsr WaitAnimationFrames
    lda #0
    sta mergeFlashPhase
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

WaitAnimationFrames:
    sta animationFrames
WaitAnimationFrames_Next:
    jsr WaitFrame
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
    ; Let the lower-border phase publish the empty board without a ghost.
    jsr WaitFrame

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
    jsr UpdatePlacement
    jsr UpdateCursorHighlight
    rts

AnimateGameOver:
    lda #1
    sta ghostSuppressed
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
    jmp DrawGameOver

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
    rts

IncrementScore:
    lda scoreHundreds
    cmp #9
    bne IncrementScore_Ones
    lda scoreTens
    cmp #9
    bne IncrementScore_Ones
    lda scoreOnes
    cmp #9
    beq IncrementScore_Done
IncrementScore_Ones:
    inc scoreOnes
    lda scoreOnes
    cmp #10
    bcc IncrementScore_Done
    lda #0
    sta scoreOnes
    inc scoreTens
    lda scoreTens
    cmp #10
    bcc IncrementScore_Done
    lda #0
    sta scoreTens
    inc scoreHundreds
IncrementScore_Done:
    rts

UpdateScoreDisplay:
    lda scoreHundreds
    beq UpdateScoreDisplay_NoHundreds
    sta ScoreDigits
    lda scoreTens
    sta ScoreDigits + 1
    lda scoreOnes
    sta ScoreDigits + 2
    lda #3
    sta scoreDigitCount
    lda #SCORE_COL_THREE
    sta scoreStartCol
    jmp DrawScore

UpdateScoreDisplay_NoHundreds:
    lda scoreTens
    beq UpdateScoreDisplay_OneDigit
    sta ScoreDigits
    lda scoreOnes
    sta ScoreDigits + 1
    lda #2
    sta scoreDigitCount
    lda #SCORE_COL_TWO
    sta scoreStartCol
    jmp DrawScore

UpdateScoreDisplay_OneDigit:
    lda scoreOnes
    sta ScoreDigits
    lda #1
    sta scoreDigitCount
    lda #SCORE_COL_ONE
    sta scoreStartCol

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
    sta SCREEN + (SCORE_ROW * 40) + SCORE_COL_THREE,x
    sta SCREEN + ((SCORE_ROW + 1) * 40) + SCORE_COL_THREE,x
    inx
    cpx #6
    bne DrawScore_Color
    rts

ClearScore:
    lda #SCORE_ROW
    jsr SetBitmapRowPointer
    lda #SCORE_COL_THREE
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearScore_Top:
    sta (PTR_LO),y
    iny
    cpy #48
    bne ClearScore_Top
    lda #(SCORE_ROW + 1)
    jsr SetBitmapRowPointer
    lda #SCORE_COL_THREE
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearScore_Bottom:
    sta (PTR_LO),y
    iny
    cpy #48
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
    jsr BuildShadowDiceSprites
    jsr SetupBottomSprites
    rts

BuildShadowDiceSprites:
    lda #<DieOneSprite
    sta SOURCE_LO
    lda #>DieOneSprite
    sta SOURCE_HI
    lda #<SHADOW_SPRITES
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    ldx #6
BuildShadowDiceSprites_Sprite:
    ldy #0
BuildShadowDiceSprites_Byte:
    lda (SOURCE_LO),y
    sta shadowSourceByte
    tya
    and #1
    beq BuildShadowDiceSprites_Even
    lda shadowSourceByte
    and #$55
    jmp BuildShadowDiceSprites_Store
BuildShadowDiceSprites_Even:
    lda shadowSourceByte
    and #$aa
BuildShadowDiceSprites_Store:
    sta (PTR_LO),y
    iny
    cpy #64
    bne BuildShadowDiceSprites_Byte
    lda SOURCE_LO
    clc
    adc #64
    sta SOURCE_LO
    bcc BuildShadowDiceSprites_SourceReady
    inc SOURCE_HI
BuildShadowDiceSprites_SourceReady:
    lda PTR_LO
    clc
    adc #64
    sta PTR_LO
    bcc BuildShadowDiceSprites_TargetReady
    inc PTR_HI
BuildShadowDiceSprites_TargetReady:
    dex
    bne BuildShadowDiceSprites_Sprite
    rts

RenderBoardRow:
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
    lda #0
    sta spriteEnableMask
    ldx #0
RenderBoardRow_Column:
    txa
    asl
    tay
    lda BoardSpriteX,x
    sta SPRITE0_X,y
    lda renderSpriteY
    sta SPRITE0_Y,y

    lda renderIndex
    clc
    adc renderColumn
    sta renderCellIndex
    tay
    lda displayValues,y
    beq RenderBoardRow_Next

RenderBoardRow_ShowValue:
    ldy renderCellIndex
    lda displaySpritePointers,y
    sta SPRITE0_PTR,x
    ldy renderCellIndex
    lda displayColors,y
    sta SPRITE0_COLOR,x
    lda SpriteBitMasks,x
    ora spriteEnableMask
    sta spriteEnableMask

RenderBoardRow_Next:
    inc renderColumn
    inx
    cpx #5
    beq RenderBoardRow_Finish
    jmp RenderBoardRow_Column
RenderBoardRow_Finish:
    lda spriteEnableMask
    ora uiEnableMask
    sta SPRITE_ENABLE
    lda #0
    sta renderColumn
    rts
RenderBoardRow_Hidden:
    lda #0
    sta renderColumn
    rts

SetupPiecePreview:
    lda gameOverBlindActive
    beq SetupPiecePreview_Visible
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
    rts
SetupPiecePreview_Visible:
    lda gameOver
    beq SetupPiecePreview_Active
    lda #%11000000
    sta uiEnableMask
    lda #%10000000
    sta SPRITE_X_MSB
    jsr ConfigureNewGameSprite
    rts

SetupPiecePreview_Active:
    ldy pieceValue0
    lda DiceSpritePointers,y
    sta SPRITE0_PTR + 5
    lda DiceColors,y
    sta SPRITE0_COLOR + 5
    lda #27
    sta SPRITE0_X + 10
    lda #180
    sta SPRITE0_Y + 10
    lda #%11100000
    sta uiEnableMask

    lda pieceCount
    cmp #2
    bne SetupPiecePreview_Single
    ldy pieceValue1
    lda DiceSpritePointers,y
    sta SPRITE0_PTR + 6
    lda DiceColors,y
    sta SPRITE0_COLOR + 6
    lda #51
    sta SPRITE0_X + 12
    lda #180
    sta SPRITE0_Y + 12
    lda #%11100000
    sta SPRITE_X_MSB
    rts

SetupPiecePreview_Single:
    jsr ConfigureNewGameSprite
    lda #%10100000
    sta SPRITE_X_MSB
    rts

SetupBottomSprites:
    lda gameOverBlindActive
    beq SetupBottomSprites_Visible
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
    rts
SetupBottomSprites_Visible:
    jsr ConfigureNewGameSprite
    lda #$77
    sta SPRITE0_PTR + 7
    lda #COLOR_LTBLUE
    sta SPRITE0_COLOR + 7
    lda #12
    sta SPRITE0_X + 14
    lda #222
    sta SPRITE0_Y + 14
    lda #%10000000
    sta SPRITE_X_MSB
    lda #%11000000
    sta SPRITE_ENABLE
    rts

ConfigureNewGameSprite:
    lda #$76
    sta SPRITE0_PTR + 6
    lda #COLOR_LTBLUE
    sta SPRITE0_COLOR + 6
    lda #76
    sta SPRITE0_X + 12
    lda #222
    sta SPRITE0_Y + 12
    rts

ClearBitmap:
    lda #<BITMAP
    sta PTR_LO
    lda #>BITMAP
    sta PTR_HI
    ldx #32
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
    lda highlightedIndex
    cmp #$ff
    beq UpdateCursorHighlight_Draw
    jsr ClearCursorHighlights

UpdateCursorHighlight_Draw:
    ldx cursorY
    lda RowIndexBase,x
    clc
    adc cursorX
    sta highlightedIndex
    lda #$ff
    sta highlightedSecondIndex
    lda pieceCount
    cmp #2
    bne UpdateCursorHighlight_Show
    lda secondIndex
    sta highlightedSecondIndex
UpdateCursorHighlight_Show:
    jmp ShowCursorHighlights

UpdateHighlightFlash:
    lda highlightedIndex
    cmp #$ff
    beq UpdateHighlightFlash_Done
    lda frameCounter
    lsr
    lsr
    and #3
    cmp highlightPhase
    beq UpdateHighlightFlash_Done
    sta highlightPhase
    jmp ShowCursorHighlights
UpdateHighlightFlash_Done:
    rts

ShowCursorHighlights:
    lda highlightedIndex
    sta highlightCellIndex
    jsr ShowHighlightCell
    lda highlightedSecondIndex
    cmp #$ff
    beq ShowCursorHighlights_Done
    sta highlightCellIndex
    jsr ShowHighlightCell
ShowCursorHighlights_Done:
    rts

ShowHighlightCell:
    jmp DrawMarchingHighlightCell

DimCursorHighlights:
    lda highlightedIndex
    sta highlightCellIndex
    jsr DimHighlightCell
    lda highlightedSecondIndex
    cmp #$ff
    beq DimCursorHighlights_Done
    sta highlightCellIndex
    jsr DimHighlightCell
DimCursorHighlights_Done:
    rts

DimHighlightCell:
    lda #(COLOR_DKGRAY << 4) | COLOR_DKGRAY
    jmp ColorHighlightedCell

ClearCursorHighlights:
    lda highlightedIndex
    sta highlightCellIndex
    jsr ClearHighlightCell
    lda highlightedSecondIndex
    cmp #$ff
    beq ClearCursorHighlights_Done
    sta highlightCellIndex
    jsr ClearHighlightCell
ClearCursorHighlights_Done:
    rts

ClearHighlightCell:
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    jsr ColorHighlightedCell
    jsr SetHighlightBitmapPointer
    jsr EraseHighlightRight
    jsr SetHighlightBitmapPointer
    jsr AddHighlightBottomOffset
    jsr EraseHighlightBottom
    jmp RestoreMarchingHighlightCell

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
    jmp DrawGameOverPrompt

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
    lda #6
    sta labelColumn
    jsr DrawLabel32
    lda #<SettingsLabel
    sta SOURCE_LO
    lda #>SettingsLabel
    sta SOURCE_HI
    lda #30
    sta labelColumn
    jsr DrawLabel32
    rts

DrawMainMascot:
    lda #<MainMascotBitmapData
    sta SOURCE_LO
    lda #>MainMascotBitmapData
    sta SOURCE_HI
    lda #4
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
    cmp #14
    bne DrawMainMascot_BitmapRow

    lda #<MainMascotScreenData
    sta SOURCE_LO
    lda #>MainMascotScreenData
    sta SOURCE_HI
    lda #4
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
    cmp #14
    bne DrawMainMascot_ScreenRow
    rts

DrawLabel32:
    lda #24
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
    lda #<(SCREEN + (24 * 40))
    sta PTR_LO
    lda #>(SCREEN + (24 * 40))
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
!byte <(SCREEN+50),<(SCREEN+54),<(SCREEN+58),<(SCREEN+62),<(SCREEN+66)
!byte <(SCREEN+210),<(SCREEN+214),<(SCREEN+218),<(SCREEN+222),<(SCREEN+226)
!byte <(SCREEN+370),<(SCREEN+374),<(SCREEN+378),<(SCREEN+382),<(SCREEN+386)
!byte <(SCREEN+530),<(SCREEN+534),<(SCREEN+538),<(SCREEN+542),<(SCREEN+546)
!byte <(SCREEN+690),<(SCREEN+694),<(SCREEN+698),<(SCREEN+702),<(SCREEN+706)
CellScreenHi:
!byte >(SCREEN+50),>(SCREEN+54),>(SCREEN+58),>(SCREEN+62),>(SCREEN+66)
!byte >(SCREEN+210),>(SCREEN+214),>(SCREEN+218),>(SCREEN+222),>(SCREEN+226)
!byte >(SCREEN+370),>(SCREEN+374),>(SCREEN+378),>(SCREEN+382),>(SCREEN+386)
!byte >(SCREEN+530),>(SCREEN+534),>(SCREEN+538),>(SCREEN+542),>(SCREEN+546)
!byte >(SCREEN+690),>(SCREEN+694),>(SCREEN+698),>(SCREEN+702),>(SCREEN+706)
CellBitmapLo:
!byte <$6190,<$61b0,<$61d0,<$61f0,<$6210
!byte <$6690,<$66b0,<$66d0,<$66f0,<$6710
!byte <$6b90,<$6bb0,<$6bd0,<$6bf0,<$6c10
!byte <$7090,<$70b0,<$70d0,<$70f0,<$7110
!byte <$7590,<$75b0,<$75d0,<$75f0,<$7610
CellBitmapHi:
!byte >$6190,>$61b0,>$61d0,>$61f0,>$6210
!byte >$6690,>$66b0,>$66d0,>$66f0,>$6710
!byte >$6b90,>$6bb0,>$6bd0,>$6bf0,>$6c10
!byte >$7090,>$70b0,>$70d0,>$70f0,>$7110
!byte >$7590,>$75b0,>$75d0,>$75f0,>$7610
HighlightRightStart:
!byte 26,24,24,24
RippleCellOrder:
!byte 20,15,10,5,0,1,2,3,4,9,14,19,24,23,22,21,16,11,6,7,8,13,18,17,12
GridColumns:
!byte 10, 14, 18, 22, 26, 30
GridRows:
!byte 1, 5, 9, 13, 17, 21

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
!byte 65,97,129,161,193
SpriteBitMasks:
!byte 1,2,4,8,16
DiceSpritePointers:
!byte 0,$70,$71,$72,$73,$74,$75
ShadowDiceSpritePointers:
!byte 0,$30,$31,$32,$33,$34,$35
DiceColors:
!byte COLOR_BLACK,COLOR_LTGRAY,COLOR_LTBLUE,COLOR_GREEN,COLOR_PURPLE,COLOR_YELLOW,COLOR_CYAN
NextRasterLines:
!byte 86,118,150,182,214,48

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
boardUpdateInProgress: !byte 0
rngSeed:           !byte 1
boardFiveCount:    !byte 0
scoreHundreds:     !byte 0
scoreTens:         !byte 0
scoreOnes:         !byte 0
ScoreDigits:       !byte 0,0,0
scoreDigitCount:   !byte 1
scoreStartCol:     !byte SCORE_COL_ONE
scoreIndex:        !byte 0
scoreCharCol:      !byte 0
scoreHalf:         !byte 0
scoreGlyphOffset:  !byte 0
scoreGlyphPage:    !byte 0
action:            !byte 0
joystickLatch:     !byte 0
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
savedCursorX:      !byte 0
savedCursorY:      !byte 0
savedOrientation:  !byte 0
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
rippleColor:       !byte COLOR_LTBLUE
rippleStep:        !byte 0
blindRow:          !byte 0
gameOverBlindActive: !byte 0
blindFillColor:    !byte 0
blindEdgeColor:    !byte 0
blindCharacterRow: !byte 0
blindCharacterEnd: !byte 0
revealRowsRemaining: !byte 0
shadowSourceByte:  !byte 0
titleCopyRemainder: !byte 0
packedCount:       !byte 0
packedValue:       !byte 0

!source "src/assets/title_screen.asm"
!source "src/assets/main_mascot.asm"
!source "src/assets/game_over_prompt.asm"
!source "src/assets/game_over_screen.asm"
!source "src/assets/marching_ants.asm"
!source "src/assets/merge_grid_sweep.asm"
!source "src/assets/die_one.asm"
!source "src/assets/die_two.asm"
!source "src/assets/die_three.asm"
!source "src/assets/die_four.asm"
!source "src/assets/die_five.asm"
!source "src/assets/die_six.asm"
!source "src/assets/new_game.asm"
!source "src/assets/settings.asm"
!source "src/assets/bottom_labels.asm"
!source "src/assets/large_digits.asm"
!source "src/assets/game_over.asm"
