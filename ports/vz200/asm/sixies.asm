; Sixies VZ200 strawman
;
; An expanded-RAM VZ200 prototype. It keeps the core 5x5 placement and merge
; loop intentionally compact while proving the final mode-1 composition:
; board, score, next piece, cursor, and keyboard controls in 128x64 pixels.

        DEVICE  NOSLOT64K

VRAM            EQU     $7000
LATCH           EQU     $6800
LOAD_ADDR       EQU     $7AE9

BOARD_CELLS     EQU     25
BOARD_SIZE      EQU     5
SCREEN_BYTES    EQU     $0800

ACTION_NONE     EQU     0
ACTION_UP       EQU     1
ACTION_DOWN     EQU     2
ACTION_LEFT     EQU     3
ACTION_RIGHT    EQU     4
ACTION_ROTATE   EQU     5
ACTION_PLACE    EQU     6
ACTION_NEW      EQU     7

GRID_COLOR      EQU     2               ; Magenta in the buff/white CG2 set.
CURSOR_COLOR    EQU     1               ; Cyan, distinct from the grid.
DIE_COLOR       EQU     3               ; Orange, distinct from grid and background.

        ORG     LOAD_ADDR

Start:
        DI                              ; The ROM IRQ changes the video latch.
        LD      SP, $8FFE               ; Safe base-RAM stack; program ends below $8600.
        LD      A, %00011000            ; Mode 1 graphics, buff/white background.
        LD      (LATCH), A
        CALL    NewGame
        CALL    DrawScreen

MainLoop:
        CALL    PollAction
        OR      A
        JR      Z, MainLoop
        LD      (pendingAction), A
        CP      ACTION_PLACE
        JR      Z, MainLoopFullRedraw
        CP      ACTION_NEW
        JR      Z, MainLoopFullRedraw
        CALL    EraseCursor
        LD      A, (pendingAction)
        CALL    HandleAction
        CALL    CalculatePlacement
        CALL    DrawCursor
        JR      MainLoop
MainLoopFullRedraw:
        CALL    HandleAction
        CALL    DrawScreen
        JR      MainLoop

; ---------------------------------------------------------------------------
; Input. The VZ keyboard matrix is memory mapped at $6800-$6fff. A key must
; be released before another action is accepted, which prevents uncontrolled
; cursor repeats on the original keyboard and in VZEM.
; ---------------------------------------------------------------------------

PollAction:
        LD      A, (keyLocked)
        OR      A
        JR      Z, PollActionScan
        LD      A, ($6800)
        AND     $3F
        CP      $3F
        JR      NZ, PollActionNone
        XOR     A
        LD      (keyLocked), A
PollActionNone:
        XOR     A
        RET

PollActionScan:
        LD      A, ($68FE)              ; T W - E Q R
        BIT     1, A
        JR      Z, PollActionUp
        BIT     4, A
        JR      Z, PollActionRotate
        BIT     5, A
        JR      Z, PollActionRotate

        LD      A, ($68FD)              ; G S Ctrl D A F
        BIT     1, A
        JR      Z, PollActionDown
        BIT     3, A
        JR      Z, PollActionRight
        BIT     4, A
        JR      Z, PollActionLeft

        LD      A, ($68EF)              ; N , - / Space M
        BIT     0, A
        JR      Z, PollActionNew
        BIT     4, A
        JR      Z, PollActionPlace

        LD      A, ($68BF)              ; Y O Return I P U
        BIT     2, A
        JR      Z, PollActionPlace
        XOR     A
        RET

PollActionUp:
        LD      A, ACTION_UP
        JR      PollActionFound
PollActionDown:
        LD      A, ACTION_DOWN
        JR      PollActionFound
PollActionLeft:
        LD      A, ACTION_LEFT
        JR      PollActionFound
PollActionRight:
        LD      A, ACTION_RIGHT
        JR      PollActionFound
PollActionRotate:
        LD      A, ACTION_ROTATE
        JR      PollActionFound
PollActionPlace:
        LD      A, ACTION_PLACE
        JR      PollActionFound
PollActionNew:
        LD      A, ACTION_NEW
PollActionFound:
        LD      (keyLocked), A
        RET

HandleAction:
        CP      ACTION_UP
        JR      NZ, HandleActionDown
        LD      A, (cursorY)
        OR      A
        RET     Z
        DEC     A
        LD      (cursorY), A
        RET
HandleActionDown:
        CP      ACTION_DOWN
        JR      NZ, HandleActionLeft
        LD      A, (cursorY)
        CP      4
        RET     Z
        INC     A
        LD      (cursorY), A
        RET
HandleActionLeft:
        CP      ACTION_LEFT
        JR      NZ, HandleActionRight
        LD      A, (cursorX)
        OR      A
        RET     Z
        DEC     A
        LD      (cursorX), A
        RET
HandleActionRight:
        CP      ACTION_RIGHT
        JR      NZ, HandleActionRotate
        LD      A, (cursorX)
        CP      4
        RET     Z
        INC     A
        LD      (cursorX), A
        RET
HandleActionRotate:
        CP      ACTION_ROTATE
        JR      NZ, HandleActionPlace
        LD      A, (pieceCount)
        CP      2
        RET     NZ
        LD      A, (orientation)
        INC     A
        AND     3
        LD      (orientation), A
        RET
HandleActionPlace:
        CP      ACTION_PLACE
        JR      NZ, HandleActionNew
        LD      A, (gameOver)
        OR      A
        RET     NZ
        JP      PlacePiece
HandleActionNew:
        CP      ACTION_NEW
        RET     NZ
        JP      NewGame

; ---------------------------------------------------------------------------
; Rules. This is deliberately small but follows the C64 ordering where it is
; visible: both halves are written before merges, then origin resolves before
; the second half. The RNG and merge resolution are self-contained so the
; renderer never edits board state.
; ---------------------------------------------------------------------------

NewGame:
        LD      HL, board
        LD      B, BOARD_CELLS
        XOR     A
NewGameClear:
        LD      (HL), A
        INC     HL
        DJNZ    NewGameClear
        LD      (scoreLo), A
        LD      (scoreHi), A
        LD      (singlesOnly), A
        LD      (gameOver), A
        LD      (keyLocked), A
        LD      A, $5D                   ; Non-zero deterministic strawman seed.
        LD      (rngState), A
        JP      GeneratePiece

RandomByte:
        LD      A, (rngState)
        ADD     A, A
        JR      NC, RandomByteStore
        XOR     $1D
RandomByteStore:
        LD      (rngState), A
        RET

GeneratePiece:
        CALL    RandomByte
        AND     1
        INC     A
        LD      (pieceCount), A
        CALL    RandomByte
        AND     3
        INC     A
        LD      (pieceA), A
        CALL    RandomByte              ; Preserved even for a single piece.
        AND     3
        INC     A
        LD      (pieceB), A

        CALL    CountFives
        CP      5
        JR      C, GeneratePieceNoFive
        CALL    RandomByte
        AND     $0F
        JR      NZ, GeneratePieceNoFive
        LD      A, (pieceCount)
        CP      1
        JR      NZ, GeneratePieceFiveDouble
        LD      A, 5
        LD      (pieceA), A
        JR      GeneratePieceNoFive
GeneratePieceFiveDouble:
        CALL    RandomByte
        AND     1
        JR      Z, GeneratePieceFiveA
        LD      A, 5
        LD      (pieceB), A
        JR      GeneratePieceNoFive
GeneratePieceFiveA:
        LD      A, 5
        LD      (pieceA), A

GeneratePieceNoFive:
        LD      A, (pieceCount)
        CP      2
        JR      NZ, GeneratePieceMode
GeneratePieceNoDoubleFour:
        LD      A, (pieceA)
        CP      4
        JR      NZ, GeneratePieceMode
        LD      A, (pieceB)
        CP      4
        JR      NZ, GeneratePieceMode
        CALL    RandomByte
        AND     3
        INC     A
        LD      (pieceB), A
        JR      GeneratePieceNoDoubleFour

GeneratePieceMode:
        CALL    HasAdjacentEmptyPair
        OR      A
        JR      NZ, GeneratePieceModeReady
        LD      A, 1
        LD      (singlesOnly), A
GeneratePieceModeReady:
        LD      A, (singlesOnly)
        OR      A
        JR      Z, GeneratePieceCursor
        LD      A, 1
        LD      (pieceCount), A
GeneratePieceCursor:
        LD      A, 2
        LD      (cursorX), A
        LD      (cursorY), A
        XOR     A
        LD      (orientation), A
        JP      CheckGameOver

CountFives:
        LD      HL, board
        LD      B, BOARD_CELLS
        LD      C, 0
CountFivesLoop:
        LD      A, (HL)
        CP      5
        JR      NZ, CountFivesNext
        INC     C
CountFivesNext:
        INC     HL
        DJNZ    CountFivesLoop
        LD      A, C
        RET

HasEmptyCell:
        LD      HL, board
        LD      B, BOARD_CELLS
HasEmptyCellLoop:
        LD      A, (HL)
        OR      A
        JR      Z, HasEmptyCellYes
        INC     HL
        DJNZ    HasEmptyCellLoop
        XOR     A
        RET
HasEmptyCellYes:
        LD      A, 1
        RET

HasAdjacentEmptyPair:
        XOR     A
        LD      (spaceIndex), A
HasAdjacentEmptyPairLoop:
        LD      A, (spaceIndex)
        CP      BOARD_CELLS
        JR      Z, HasAdjacentEmptyPairNo
        CALL    BoardValueAtA
        OR      A
        JR      NZ, HasAdjacentEmptyPairNext

        LD      A, (spaceIndex)
        CALL    NeighborFromRight
        CALL    NeighborIsEmpty
        OR      A
        RET     NZ
        LD      A, (spaceIndex)
        CALL    NeighborFromDown
        CALL    NeighborIsEmpty
        OR      A
        RET     NZ
HasAdjacentEmptyPairNext:
        LD      A, (spaceIndex)
        INC     A
        LD      (spaceIndex), A
        JR      HasAdjacentEmptyPairLoop
HasAdjacentEmptyPairNo:
        XOR     A
        RET

NeighborIsEmpty:
        CP      $FF
        JR      Z, NeighborIsEmptyNo
        CALL    BoardValueAtA
        OR      A
        JR      NZ, NeighborIsEmptyNo
        LD      A, 1
        RET
NeighborIsEmptyNo:
        XOR     A
        RET

CheckGameOver:
        LD      A, (pieceCount)
        CP      1
        JR      NZ, CheckGameOverDouble
        CALL    HasEmptyCell
        JR      CheckGameOverStore
CheckGameOverDouble:
        CALL    HasAdjacentEmptyPair
CheckGameOverStore:
        OR      A
        JR      NZ, CheckGameOverPlayable
        LD      A, 1
        LD      (gameOver), A
        RET
CheckGameOverPlayable:
        XOR     A
        LD      (gameOver), A
        RET

CalculatePlacement:
        LD      A, $FF
        LD      (secondIndex), A
        LD      (secondX), A
        LD      (secondY), A
        LD      B, 1
        LD      A, (cursorX)
        LD      D, A
        LD      A, (cursorY)
        LD      E, A
        LD      B, D
        LD      C, E
        CALL    IndexFromXY
        LD      (originIndex), A
        CALL    BoardValueAtA
        OR      A
        JR      Z, CalculatePlacementOriginClear
        XOR     A
        LD      (placementValid), A
        JR      CalculatePlacementSecond
CalculatePlacementOriginClear:
        LD      A, 1
        LD      (placementValid), A

CalculatePlacementSecond:
        LD      A, (pieceCount)
        CP      2
        RET     NZ
        LD      A, (cursorX)
        LD      B, A
        LD      A, (cursorY)
        LD      C, A
        LD      A, (orientation)
        CP      0
        JR      NZ, CalculatePlacementDown
        LD      A, B
        CP      4
        JR      Z, CalculatePlacementOffBoard
        INC     B
        JR      CalculatePlacementSecondReady
CalculatePlacementDown:
        CP      1
        JR      NZ, CalculatePlacementLeft
        LD      A, C
        CP      4
        JR      Z, CalculatePlacementOffBoard
        INC     C
        JR      CalculatePlacementSecondReady
CalculatePlacementLeft:
        CP      2
        JR      NZ, CalculatePlacementUp
        LD      A, B
        OR      A
        JR      Z, CalculatePlacementOffBoard
        DEC     B
        JR      CalculatePlacementSecondReady
CalculatePlacementUp:
        LD      A, C
        OR      A
        JR      Z, CalculatePlacementOffBoard
        DEC     C
CalculatePlacementSecondReady:
        LD      A, B
        LD      (secondX), A
        LD      A, C
        LD      (secondY), A
        CALL    IndexFromXY
        LD      (secondIndex), A
        CALL    BoardValueAtA
        OR      A
        RET     Z
        XOR     A
        LD      (placementValid), A
        RET
CalculatePlacementOffBoard:
        XOR     A
        LD      (placementValid), A
        RET

PlacePiece:
        CALL    CalculatePlacement
        LD      A, (placementValid)
        OR      A
        RET     Z
        LD      A, (originIndex)
        LD      E, A
        LD      D, 0
        LD      HL, board
        ADD     HL, DE
        LD      A, (pieceA)
        LD      (HL), A
        LD      A, (pieceCount)
        CP      2
        JR      NZ, PlacePieceResolveOrigin
        LD      A, (secondIndex)
        LD      E, A
        LD      D, 0
        LD      HL, board
        ADD     HL, DE
        LD      A, (pieceB)
        LD      (HL), A
PlacePieceResolveOrigin:
        LD      A, (originIndex)
        LD      (activeIndex), A
        CALL    ResolveAtActiveIndex
        LD      A, (pieceCount)
        CP      2
        JR      NZ, PlacePieceNext
        LD      A, (secondIndex)
        CALL    BoardValueAtA
        OR      A
        JR      Z, PlacePieceNext
        LD      A, (secondIndex)
        LD      (activeIndex), A
        CALL    ResolveAtActiveIndex
PlacePieceNext:
        JP      GeneratePiece

ResolveAtActiveIndex:
        CALL    FindGroup
        LD      A, (groupCount)
        CP      3
        RET     C
        CALL    AddGroupScore
        XOR     A
        LD      (groupCursor), A
ResolveAtActiveIndexClear:
        LD      A, (groupCursor)
        LD      B, A
        LD      A, (groupCount)
        CP      B
        JR      Z, ResolveAtActiveIndexUpgrade
        LD      E, B
        LD      D, 0
        LD      HL, groupCells
        ADD     HL, DE
        LD      A, (HL)
        LD      E, A
        LD      D, 0
        LD      HL, board
        ADD     HL, DE
        XOR     A
        LD      (HL), A
        LD      A, (groupCursor)
        INC     A
        LD      (groupCursor), A
        JR      ResolveAtActiveIndexClear
ResolveAtActiveIndexUpgrade:
        LD      A, (groupValue)
        CP      6
        RET     Z
        INC     A
        LD      B, A
        LD      A, (activeIndex)
        LD      E, A
        LD      D, 0
        LD      HL, board
        ADD     HL, DE
        LD      (HL), B
        JR      ResolveAtActiveIndex

AddGroupScore:
        LD      A, (groupCount)
        LD      (scoreCount), A
AddGroupScoreDie:
        LD      A, (groupValue)
        LD      (scoreValue), A
AddGroupScoreValue:
        CALL    IncrementScore
        LD      A, (scoreValue)
        DEC     A
        LD      (scoreValue), A
        JR      NZ, AddGroupScoreValue
        LD      A, (scoreCount)
        DEC     A
        LD      (scoreCount), A
        JR      NZ, AddGroupScoreDie
        RET

IncrementScore:
        LD      A, (scoreHi)
        CP      $27
        JR      C, IncrementScoreDo
        RET     NZ
        LD      A, (scoreLo)
        CP      $0F
        RET     NC
IncrementScoreDo:
        LD      A, (scoreLo)
        INC     A
        LD      (scoreLo), A
        RET     NZ
        LD      A, (scoreHi)
        INC     A
        LD      (scoreHi), A
        RET

FindGroup:
        LD      HL, visited
        LD      B, BOARD_CELLS
        XOR     A
FindGroupClear:
        LD      (HL), A
        INC     HL
        DJNZ    FindGroupClear
        LD      (groupCount), A
        LD      (queueHead), A
        LD      (queueTail), A
        LD      A, (activeIndex)
        CALL    BoardValueAtA
        OR      A
        RET     Z
        LD      (groupValue), A
        LD      A, (activeIndex)
        LD      E, A
        LD      D, 0
        LD      HL, visited
        ADD     HL, DE
        LD      A, 1
        LD      (HL), A
        LD      A, (activeIndex)
        LD      (queue), A
        LD      A, 1
        LD      (queueTail), A
FindGroupLoop:
        LD      A, (queueHead)
        LD      B, A
        LD      A, (queueTail)
        CP      B
        RET     Z
        LD      E, B
        LD      D, 0
        LD      HL, queue
        ADD     HL, DE
        LD      A, (HL)
        LD      (currentIndex), A
        LD      A, (queueHead)
        INC     A
        LD      (queueHead), A

        LD      A, (groupCount)
        LD      E, A
        LD      D, 0
        LD      HL, groupCells
        ADD     HL, DE
        LD      A, (currentIndex)
        LD      (HL), A
        LD      A, (groupCount)
        INC     A
        LD      (groupCount), A

        LD      A, (currentIndex)
        CALL    NeighborFromLeft
        CALL    TryGroupNeighbor
        LD      A, (currentIndex)
        CALL    NeighborFromRight
        CALL    TryGroupNeighbor
        LD      A, (currentIndex)
        CALL    NeighborFromUp
        CALL    TryGroupNeighbor
        LD      A, (currentIndex)
        CALL    NeighborFromDown
        CALL    TryGroupNeighbor
        JR      FindGroupLoop

TryGroupNeighbor:
        CP      $FF
        RET     Z
        LD      (neighborIndex), A
        LD      E, A
        LD      D, 0
        LD      HL, visited
        ADD     HL, DE
        LD      A, (HL)
        OR      A
        RET     NZ
        LD      A, (neighborIndex)
        CALL    BoardValueAtA
        LD      B, A
        LD      A, (groupValue)
        CP      B
        RET     NZ
        LD      A, (neighborIndex)
        LD      E, A
        LD      D, 0
        LD      HL, visited
        ADD     HL, DE
        LD      A, 1
        LD      (HL), A
        LD      A, (queueTail)
        LD      E, A
        LD      D, 0
        LD      HL, queue
        ADD     HL, DE
        LD      A, (neighborIndex)
        LD      (HL), A
        LD      A, (queueTail)
        INC     A
        LD      (queueTail), A
        RET

; ---------------------------------------------------------------------------
; Rendering. Mode 1 is 32 bytes by 64 rows, with four two-bit pixels in each
; byte. VZ color codes are green=$00, yellow=$55, blue=$aa, red=$ff.
; ---------------------------------------------------------------------------

DrawScreen:
        CALL    ClearVideo
        LD      HL, titleText
        LD      B, 72
        LD      C, 2
        LD      D, 2
        CALL    DrawText
        LD      HL, scoreLabel
        LD      B, 59
        LD      C, 12
        LD      D, 1
        CALL    DrawText
        CALL    DrawScore
        CALL    DrawGrid
        CALL    DrawBoard
        LD      A, (gameOver)
        OR      A
        JR      NZ, DrawScreenGameOver
        CALL    CalculatePlacement
        CALL    DrawCursor
        LD      HL, newLabel
        LD      B, 58
        LD      C, 56
        LD      D, 1
        JP      DrawText
DrawScreenGameOver:
        LD      HL, gameText
        LD      B, 65
        LD      C, 38
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, overText
        LD      B, 65
        LD      C, 46
        LD      D, 3
        JP      DrawText

ClearVideo:
        LD      HL, VRAM
        LD      BC, SCREEN_BYTES
        LD      D, 0
ClearVideoLoop:
        LD      (HL), D
        INC     HL
        DEC     BC
        LD      A, B
        OR      C
        JR      NZ, ClearVideoLoop
        RET

DrawGrid:
        LD      A, 8
        LD      (gridCoordinate), A
        LD      B, 6
DrawGridHorizontal:
        LD      A, (gridCoordinate)
        LD      C, A
        LD      B, 1
        LD      D, 46
        LD      A, GRID_COLOR
        CALL    DrawHLine
        LD      A, (gridCoordinate)
        ADD     A, 10
        LD      (gridCoordinate), A
        LD      A, (gridLineCount)
        ; Fall through via a separate loop counter stored in memory.
        LD      A, (drawLineCounter)
        INC     A
        LD      (drawLineCounter), A
        CP      6
        JR      NZ, DrawGridHorizontal
        XOR     A
        LD      (drawLineCounter), A
        LD      A, 1
        LD      (gridCoordinate), A
DrawGridVertical:
        LD      A, (gridCoordinate)
        LD      B, A
        LD      C, 8
        LD      D, 51
        LD      A, GRID_COLOR
        CALL    DrawVLine
        LD      A, (gridCoordinate)
        ADD     A, 9
        LD      (gridCoordinate), A
        LD      A, (drawLineCounter)
        INC     A
        LD      (drawLineCounter), A
        CP      6
        JR      NZ, DrawGridVertical
        XOR     A
        LD      (drawLineCounter), A
        RET

DrawBoard:
        XOR     A
        LD      (drawRow), A
        LD      (drawIndex), A
DrawBoardRow:
        XOR     A
        LD      (drawColumn), A
DrawBoardColumn:
        LD      A, (drawIndex)
        CALL    BoardValueAtA
        OR      A
        JR      Z, DrawBoardNext
        LD      (dieValue), A
        LD      A, (drawColumn)
        LD      B, A
        LD      A, (drawRow)
        LD      C, A
        CALL    CellCoordinates
        LD      A, (dieValue)
        LD      D, 3
        CALL    DrawDie
DrawBoardNext:
        LD      A, (drawIndex)
        INC     A
        LD      (drawIndex), A
        LD      A, (drawColumn)
        INC     A
        LD      (drawColumn), A
        CP      BOARD_SIZE
        JR      NZ, DrawBoardColumn
        LD      A, (drawRow)
        INC     A
        LD      (drawRow), A
        CP      BOARD_SIZE
        JR      NZ, DrawBoardRow
        RET

DrawCursor:
        LD      A, (cursorX)
        LD      B, A
        LD      A, (cursorY)
        LD      C, A
        CALL    CellCoordinates
        LD      A, B
        LD      (previewCellX), A
        LD      A, C
        LD      (previewCellY), A
        LD      A, (placementValid)
        OR      A
        JR      Z, DrawCursorOriginBorder
        LD      A, (pieceA)
        CALL    DrawPreviewDie
DrawCursorOriginBorder:
        LD      A, (previewCellX)
        LD      B, A
        LD      A, (previewCellY)
        LD      C, A
        CALL    DrawCellCursor
        LD      A, (secondX)
        CP      $FF
        RET     Z
        LD      B, A
        LD      A, (secondY)
        LD      C, A
        CALL    CellCoordinates
        LD      A, B
        LD      (previewCellX), A
        LD      A, C
        LD      (previewCellY), A
        LD      A, (placementValid)
        OR      A
        JR      Z, DrawCursorSecondBorder
        LD      A, (pieceB)
        CALL    DrawPreviewDie
DrawCursorSecondBorder:
        LD      A, (previewCellX)
        LD      B, A
        LD      A, (previewCellY)
        LD      C, A
        JP      DrawCellCursor

; Input: A = die value, B/C = cell pixel origin. The caller retains the
; placement coordinates in previewCellX/Y because DrawDie uses B/C internally.
DrawPreviewDie:
        LD      D, DIE_COLOR
        JP      DrawDie

; Restore every cell touched by the previous placement preview before moving
; or rotating it. This removes the preview die, grid highlight, and any pips.
EraseCursor:
        LD      A, (cursorX)
        LD      B, A
        LD      A, (cursorY)
        LD      C, A
        CALL    RestoreCell
        LD      A, (secondX)
        CP      $FF
        RET     Z
        LD      B, A
        LD      A, (secondY)
        LD      C, A
        JP      RestoreCell

; Input: B = board x, C = board y. Restore the authoritative cell contents.
RestoreCell:
        CALL    IndexFromXY
        LD      (restoreCellIndex), A
        CALL    CellCoordinates
        LD      A, B
        LD      (restoreCellX), A
        LD      A, C
        LD      (restoreCellY), A

        ; Clear the full cursor outline. The cell interior is 8x8, but the
        ; cursor also occupies the top/side grid edges and its own bottom edge.
        LD      A, (restoreCellX)
        DEC     A
        LD      B, A
        LD      A, (restoreCellY)
        DEC     A
        LD      C, A
        LD      D, 10
        LD      E, 10
        XOR     A
        CALL    FillRect

        ; FillRect uses B/C internally, so restore the cell origin before
        ; redrawing its three static grid edges.
        LD      A, (restoreCellX)
        DEC     A
        LD      B, A
        LD      A, (restoreCellY)
        DEC     A
        LD      C, A
        LD      D, 10
        LD      A, GRID_COLOR
        CALL    DrawHLine

        LD      A, (restoreCellX)
        DEC     A
        LD      B, A
        LD      A, (restoreCellY)
        DEC     A
        LD      C, A
        LD      D, 10
        LD      A, GRID_COLOR
        CALL    DrawVLine

        LD      A, (restoreCellX)
        ADD     A, 8
        LD      B, A
        LD      A, (restoreCellY)
        DEC     A
        LD      C, A
        LD      D, 10
        LD      A, GRID_COLOR
        CALL    DrawVLine

        LD      A, (restoreCellIndex)
        CALL    BoardValueAtA
        OR      A
        RET     Z
        ; Keep the authoritative die face while B/C are prepared for DrawDie.
        PUSH    AF
        LD      D, DIE_COLOR
        LD      A, (restoreCellX)
        LD      B, A
        LD      A, (restoreCellY)
        LD      C, A
        POP     AF
        JP      DrawDie

DrawCellCursor:
        LD      A, B
        DEC     A
        LD      (cursorDrawX), A
        LD      A, C
        DEC     A
        LD      (cursorDrawY), A
        LD      A, (cursorDrawX)
        LD      B, A
        LD      A, (cursorDrawY)
        LD      C, A
        LD      D, 10
        LD      A, CURSOR_COLOR
        CALL    DrawHLine
        LD      A, (cursorDrawY)
        ADD     A, 9
        LD      C, A
        LD      A, (cursorDrawX)
        LD      B, A
        LD      D, 10
        LD      A, CURSOR_COLOR
        CALL    DrawHLine
        LD      A, (cursorDrawX)
        LD      B, A
        LD      A, (cursorDrawY)
        LD      C, A
        LD      D, 10
        LD      A, CURSOR_COLOR
        CALL    DrawVLine
        LD      A, (cursorDrawX)
        ADD     A, 9
        LD      B, A
        LD      A, (cursorDrawY)
        LD      C, A
        LD      D, 10
        LD      A, CURSOR_COLOR
        JP      DrawVLine

DrawNextPiece:
        LD      A, (pieceCount)
        CP      2
        JR      NZ, DrawNextSingle
        LD      A, (orientation)
        CP      0
        JR      NZ, DrawNextPieceDown
        LD      B, 48
        LD      C, 39
        CALL    DrawNextPieceFirst
        LD      B, 56
        LD      C, 39
        JP      DrawNextPieceSecond
DrawNextPieceDown:
        CP      1
        JR      NZ, DrawNextPieceLeft
        LD      B, 52
        LD      C, 34
        CALL    DrawNextPieceFirst
        LD      B, 52
        LD      C, 44
        JP      DrawNextPieceSecond
DrawNextPieceLeft:
        CP      2
        JR      NZ, DrawNextPieceUp
        LD      B, 56
        LD      C, 39
        CALL    DrawNextPieceFirst
        LD      B, 48
        LD      C, 39
        JP      DrawNextPieceSecond
DrawNextPieceUp:
        LD      B, 52
        LD      C, 44
        CALL    DrawNextPieceFirst
        LD      B, 52
        LD      C, 34
        JP      DrawNextPieceSecond
DrawNextPieceFirst:
        LD      A, (pieceA)
        LD      D, DIE_COLOR
        CALL    DrawDie
        RET
DrawNextPieceSecond:
        LD      A, (pieceB)
        LD      D, DIE_COLOR
        JP      DrawDie
DrawNextSingle:
        LD      B, 52
        LD      C, 39
        LD      A, (pieceA)
        LD      D, DIE_COLOR
        JP      DrawDie

; Redrawing this small panel keeps rotation feedback visible without a full
; screen refresh.
RedrawCurrentPiece:
        LD      B, 47
        LD      C, 33
        LD      D, 17
        LD      E, 20
        XOR     A
        CALL    FillRect
        JP      DrawNextPiece

DrawDie:
        LD      (dieValue), A
        LD      A, D
        LD      (dieColor), A
        LD      A, B
        LD      (dieX), A
        LD      A, C
        LD      (dieY), A
        LD      A, (dieColor)
        LD      D, 8
        ; Fill through the row immediately above the next horizontal grid line.
        LD      E, 9
        CALL    FillRect
        LD      A, (dieValue)
        CP      1
        JR      NZ, DrawDieTwo
        CALL    DrawPipCenter
        RET
DrawDieTwo:
        CP      2
        JR      NZ, DrawDieThree
        CALL    DrawPipTopLeft
        JP      DrawPipBottomRight
DrawDieThree:
        CP      3
        JR      NZ, DrawDieFour
        CALL    DrawPipTopLeft
        CALL    DrawPipCenter
        JP      DrawPipBottomRight
DrawDieFour:
        CP      4
        JR      NZ, DrawDieFive
        CALL    DrawPipTopLeft
        CALL    DrawPipTopRight
        CALL    DrawPipBottomLeft
        JP      DrawPipBottomRight
DrawDieFive:
        CP      5
        JR      NZ, DrawDieSix
        CALL    DrawPipTopLeft
        CALL    DrawPipTopRight
        CALL    DrawPipCenter
        CALL    DrawPipBottomLeft
        JP      DrawPipBottomRight
DrawDieSix:
        CALL    DrawPipTopLeft
        CALL    DrawPipMiddleLeft
        CALL    DrawPipBottomLeft
        CALL    DrawPipTopRight
        CALL    DrawPipMiddleRight
        JP      DrawPipBottomRight

DrawPipTopLeft:
        LD      B, 1
        LD      C, 1
        JR      DrawPip
DrawPipTopRight:
        LD      B, 5
        LD      C, 1
        JR      DrawPip
DrawPipCenter:
        LD      B, 3
        LD      C, 3
        JR      DrawPip
DrawPipMiddleLeft:
        LD      B, 1
        LD      C, 3
        JR      DrawPip
DrawPipMiddleRight:
        LD      B, 5
        LD      C, 3
        JR      DrawPip
DrawPipBottomLeft:
        LD      B, 1
        LD      C, 5
        JR      DrawPip
DrawPipBottomRight:
        LD      B, 5
        LD      C, 5
DrawPip:
        LD      A, (dieX)
        ADD     A, B
        LD      B, A
        LD      A, (dieY)
        ADD     A, C
        LD      C, A
        LD      A, (dieValue)
        CP      6
        JR      NZ, DrawPipLarge
        ; The nine-pixel die body gives the six face one extra row to center.
        INC     C
        JR      DrawPipSix
DrawPipLarge:
        LD      D, 2
        LD      E, 2
        JR      DrawPipColor
DrawPipSix:
        ; Small pips leave a gutter between the three rows on a six.
        LD      D, 1
        LD      E, 1
DrawPipColor:
        XOR     A
        JP      FillRect

DrawScore:
        CALL    BuildScoreText
        LD      HL, scoreText
        LD      B, 60
        LD      C, 20
        LD      D, 1
        JP      DrawText

BuildScoreText:
        LD      A, (scoreLo)
        LD      (scoreTempLo), A
        LD      A, (scoreHi)
        LD      (scoreTempHi), A
        XOR     A
        LD      (scoreDigitIndex), A
BuildScoreTextDigit:
        LD      A, (scoreDigitIndex)
        CP      4
        RET     Z
        LD      E, A
        LD      D, 0
        LD      HL, ScoreDenomLo
        ADD     HL, DE
        LD      A, (HL)
        LD      (denomLo), A
        LD      HL, ScoreDenomHi
        ADD     HL, DE
        LD      A, (HL)
        LD      (denomHi), A
        LD      A, '0'
        LD      (scoreDigit), A
BuildScoreTextSubtract:
        LD      A, (scoreTempHi)
        LD      B, A
        LD      A, (denomHi)
        CP      B
        JR      C, BuildScoreTextDoSubtract
        JR      NZ, BuildScoreTextStore
        LD      A, (scoreTempLo)
        LD      B, A
        LD      A, (denomLo)
        CP      B
        JR      C, BuildScoreTextDoSubtract
        JR      Z, BuildScoreTextDoSubtract
        JR      BuildScoreTextStore
BuildScoreTextDoSubtract:
        LD      A, (denomLo)
        LD      B, A
        LD      A, (scoreTempLo)
        SUB     B
        LD      (scoreTempLo), A
        LD      A, (denomHi)
        LD      B, A
        LD      A, (scoreTempHi)
        SBC     A, B
        LD      (scoreTempHi), A
        LD      A, (scoreDigit)
        INC     A
        LD      (scoreDigit), A
        JR      BuildScoreTextSubtract
BuildScoreTextStore:
        LD      A, (scoreDigitIndex)
        LD      E, A
        LD      D, 0
        LD      HL, scoreText
        ADD     HL, DE
        LD      A, (scoreDigit)
        LD      (HL), A
        LD      A, (scoreDigitIndex)
        INC     A
        LD      (scoreDigitIndex), A
        JR      BuildScoreTextDigit

; ---------------------------------------------------------------------------
; Small 4x5 bitmap font and two-bit pixel primitives.
; ---------------------------------------------------------------------------

DrawText:
        LD      (textPointer), HL
        LD      A, B
        LD      (textX), A
        LD      A, C
        LD      (textY), A
        LD      A, D
        LD      (textColor), A
DrawTextNext:
        LD      HL, (textPointer)
        LD      A, (HL)
        OR      A
        RET     Z
        INC     HL
        LD      (textPointer), HL
        CALL    GlyphIndex
        LD      B, A
        LD      A, (textX)
        LD      C, A
        LD      A, (textY)
        LD      D, A
        LD      A, (textColor)
        LD      E, A
        LD      A, B
        LD      B, C
        LD      C, D
        LD      D, E
        CALL    DrawGlyph
        LD      A, (textX)
        ADD     A, 5
        LD      (textX), A
        JR      DrawTextNext

GlyphIndex:
        CP      ' '
        JR      Z, GlyphIndexSpace
        CP      '0'
        JR      C, GlyphIndexSpace
        CP      ':'
        JR      C, GlyphIndexDigit
        SUB     'A'
        RET
GlyphIndexDigit:
        SUB     '0'
        ADD     A, 26
        RET
GlyphIndexSpace:
        LD      A, 36
        RET

DrawGlyph:
        LD      A, B
        LD      (glyphX), A
        LD      A, C
        LD      (glyphY), A
        LD      A, D
        LD      (drawColor), A
        LD      A, B
        LD      E, A
        ADD     A, A
        ADD     A, A
        ADD     A, E
        LD      E, A
        LD      D, 0
        LD      HL, Font4x5
        ADD     HL, DE
        LD      (glyphPointer), HL
        XOR     A
        LD      (glyphRow), A
DrawGlyphRow:
        LD      A, (glyphRow)
        CP      5
        RET     Z
        LD      HL, (glyphPointer)
        LD      A, (HL)
        INC     HL
        LD      (glyphPointer), HL
        LD      (glyphBits), A
        XOR     A
        LD      (glyphColumn), A
DrawGlyphColumn:
        LD      A, (glyphColumn)
        CP      4
        JR      Z, DrawGlyphNextRow
        LD      E, A
        LD      D, 0
        LD      HL, GlyphBitMasks
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      A, (glyphBits)
        AND     B
        JR      Z, DrawGlyphSkipPixel
        LD      A, (glyphX)
        LD      B, A
        LD      A, (glyphColumn)
        ADD     A, B
        LD      B, A
        LD      A, (glyphY)
        LD      C, A
        LD      A, (glyphRow)
        ADD     A, C
        LD      C, A
        LD      A, (drawColor)
        CALL    PlotPixel
DrawGlyphSkipPixel:
        LD      A, (glyphColumn)
        INC     A
        LD      (glyphColumn), A
        JR      DrawGlyphColumn
DrawGlyphNextRow:
        LD      A, (glyphRow)
        INC     A
        LD      (glyphRow), A
        JR      DrawGlyphRow

DrawHLine:
        LD      E, 1
        JP      FillRect

DrawVLine:
        LD      E, D
        LD      D, 1
        JP      FillRect

FillRect:
        LD      (fillColor), A
        LD      A, B
        LD      (fillLeft), A
        LD      A, C
        LD      (fillTop), A
        LD      A, D
        LD      (fillWidth), A
        LD      A, E
        LD      (fillHeight), A
        XOR     A
        LD      (fillY), A
FillRectRow:
        XOR     A
        LD      (fillX), A
FillRectColumn:
        LD      A, (fillX)
        LD      B, A
        LD      A, (fillLeft)
        ADD     A, B
        LD      B, A
        LD      A, (fillY)
        LD      C, A
        LD      A, (fillTop)
        ADD     A, C
        LD      C, A
        LD      A, (fillColor)
        CALL    PlotPixel
        LD      A, (fillX)
        INC     A
        LD      (fillX), A
        LD      B, A
        LD      A, (fillWidth)
        CP      B
        JR      NZ, FillRectColumn
        LD      A, (fillY)
        INC     A
        LD      (fillY), A
        LD      B, A
        LD      A, (fillHeight)
        CP      B
        JR      NZ, FillRectRow
        RET

PlotPixel:
        LD      (plotColor), A
        LD      A, B
        AND     3
        LD      (plotShift), A
        LD      H, 0
        LD      L, C
        ADD     HL, HL
        ADD     HL, HL
        ADD     HL, HL
        ADD     HL, HL
        ADD     HL, HL
        LD      DE, VRAM
        ADD     HL, DE
        LD      A, B
        SRL     A
        SRL     A
        LD      E, A
        LD      D, 0
        ADD     HL, DE
        LD      (plotAddress), HL
        LD      A, (plotShift)
        LD      E, A
        LD      D, 0
        LD      HL, PixelClearMasks
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      HL, (plotAddress)
        LD      A, (HL)
        AND     B
        LD      B, A
        LD      A, (plotColor)
        ADD     A, A
        ADD     A, A
        LD      E, A
        LD      A, (plotShift)
        ADD     A, E
        LD      E, A
        LD      D, 0
        LD      HL, PixelSetMasks
        ADD     HL, DE
        LD      A, (HL)
        OR      B
        LD      HL, (plotAddress)
        LD      (HL), A
        RET

; ---------------------------------------------------------------------------
; Board helpers and lookup tables.
; ---------------------------------------------------------------------------

IndexFromXY:
        LD      A, C
        LD      E, A
        LD      D, 0
        LD      HL, RowBase
        ADD     HL, DE
        LD      A, (HL)
        ADD     A, B
        RET

CellCoordinates:
        LD      A, B
        LD      E, A
        LD      D, 0
        LD      HL, CellX
        ADD     HL, DE
        LD      B, (HL)
        LD      A, C
        LD      E, A
        LD      D, 0
        LD      HL, CellY
        ADD     HL, DE
        LD      C, (HL)
        RET

BoardValueAtA:
        LD      E, A
        LD      D, 0
        LD      HL, board
        ADD     HL, DE
        LD      A, (HL)
        RET

NeighborFromLeft:
        LD      E, A
        LD      D, 0
        LD      HL, LeftNeighbors
        ADD     HL, DE
        LD      A, (HL)
        RET
NeighborFromRight:
        LD      E, A
        LD      D, 0
        LD      HL, RightNeighbors
        ADD     HL, DE
        LD      A, (HL)
        RET
NeighborFromUp:
        LD      E, A
        LD      D, 0
        LD      HL, UpNeighbors
        ADD     HL, DE
        LD      A, (HL)
        RET
NeighborFromDown:
        LD      E, A
        LD      D, 0
        LD      HL, DownNeighbors
        ADD     HL, DE
        LD      A, (HL)
        RET

titleText:      DB      "SIXIES", 0
scoreLabel:     DB      "SCORE", 0
nextLabel:      DB      "DIE", 0
newLabel:       DB      "N NEW", 0
gameText:       DB      "GAME", 0
overText:       DB      "OVER", 0
scoreText:      DB      "0000", 0

RowBase:        DB      0, 5, 10, 15, 20
CellX:          DB      2, 11, 20, 29, 38
CellY:          DB      9, 19, 29, 39, 49
ScoreDenomLo:   DB      $E8, $64, $0A, $01
ScoreDenomHi:   DB      $03, $00, $00, $00
GlyphBitMasks:  DB      8, 4, 2, 1
PixelClearMasks: DB     $3F, $CF, $F3, $FC
PixelSetMasks:
                DB      $00, $00, $00, $00
                DB      $40, $10, $04, $01
                DB      $80, $20, $08, $02
                DB      $C0, $30, $0C, $03

; A-Z, 0-9, space. Each glyph is five rows, four bits per row.
Font4x5:
        DB $06,$09,$0F,$09,$09 ; A
        DB $0E,$09,$0E,$09,$0E ; B
        DB $07,$08,$08,$08,$07 ; C
        DB $0E,$09,$09,$09,$0E ; D
        DB $0F,$08,$0E,$08,$0F ; E
        DB $0F,$08,$0E,$08,$08 ; F
        DB $07,$08,$0B,$09,$07 ; G
        DB $09,$09,$0F,$09,$09 ; H
        DB $0E,$04,$04,$04,$0E ; I
        DB $03,$01,$01,$09,$06 ; J
        DB $09,$0A,$0C,$0A,$09 ; K
        DB $08,$08,$08,$08,$0F ; L
        DB $09,$0F,$0F,$09,$09 ; M
        DB $09,$0D,$0B,$09,$09 ; N
        DB $06,$09,$09,$09,$06 ; O
        DB $0E,$09,$0E,$08,$08 ; P
        DB $06,$09,$09,$0B,$07 ; Q
        DB $0E,$09,$0E,$0A,$09 ; R
        DB $07,$08,$06,$01,$0E ; S
        DB $0F,$04,$04,$04,$04 ; T
        DB $09,$09,$09,$09,$06 ; U
        DB $09,$09,$09,$06,$06 ; V
        DB $09,$09,$0F,$0F,$09 ; W
        DB $09,$06,$06,$06,$09 ; X
        DB $09,$09,$06,$04,$04 ; Y
        DB $0F,$02,$04,$08,$0F ; Z
        DB $06,$09,$09,$09,$06 ; 0
        DB $04,$0C,$04,$04,$0E ; 1
        DB $06,$09,$02,$04,$0F ; 2
        DB $0E,$01,$06,$01,$0E ; 3
        DB $09,$09,$0F,$01,$01 ; 4
        DB $0F,$08,$0E,$01,$0E ; 5
        DB $06,$08,$0E,$09,$06 ; 6
        DB $0F,$01,$02,$04,$04 ; 7
        DB $06,$09,$06,$09,$06 ; 8
        DB $06,$09,$07,$01,$06 ; 9
        DB $00,$00,$00,$00,$00 ; space

LeftNeighbors:
        DB $FF,0,1,2,3, $FF,5,6,7,8, $FF,10,11,12,13, $FF,15,16,17,18, $FF,20,21,22,23
RightNeighbors:
        DB 1,2,3,4,$FF, 6,7,8,9,$FF, 11,12,13,14,$FF, 16,17,18,19,$FF, 21,22,23,24,$FF
UpNeighbors:
        DB $FF,$FF,$FF,$FF,$FF, 0,1,2,3,4, 5,6,7,8,9, 10,11,12,13,14, 15,16,17,18,19
DownNeighbors:
        DB 5,6,7,8,9, 10,11,12,13,14, 15,16,17,18,19, 20,21,22,23,24, $FF,$FF,$FF,$FF,$FF

; Rules state.
board:          DS      BOARD_CELLS
visited:        DS      BOARD_CELLS
queue:          DS      BOARD_CELLS
groupCells:     DS      BOARD_CELLS
scoreLo:        DB      0
scoreHi:        DB      0
rngState:       DB      0
cursorX:        DB      0
cursorY:        DB      0
pieceCount:     DB      0
pieceA:         DB      0
pieceB:         DB      0
orientation:    DB      0
singlesOnly:    DB      0
gameOver:       DB      0
placementValid: DB      0
originIndex:    DB      0
secondIndex:    DB      0
secondX:        DB      0
secondY:        DB      0
activeIndex:    DB      0
groupCount:     DB      0
groupValue:     DB      0
groupCursor:    DB      0
queueHead:      DB      0
queueTail:      DB      0
currentIndex:   DB      0
neighborIndex:  DB      0
scoreCount:     DB      0
scoreValue:     DB      0
spaceIndex:     DB      0
keyLocked:      DB      0
pendingAction:  DB      0

; Renderer workspace.
gridCoordinate: DB      0
gridLineCount:  DB      0
drawLineCounter: DB     0
drawRow:        DB      0
drawColumn:     DB      0
drawIndex:      DB      0
cursorDrawX:    DB      0
cursorDrawY:    DB      0
previewCellX:   DB      0
previewCellY:   DB      0
restoreCellX:   DB      0
restoreCellY:   DB      0
restoreCellIndex: DB    0
dieX:           DB      0
dieY:           DB      0
dieValue:       DB      0
dieColor:       DB      0
scoreTempLo:    DB      0
scoreTempHi:    DB      0
denomLo:        DB      0
denomHi:        DB      0
scoreDigitIndex: DB     0
scoreDigit:     DB      0
textPointer:    DW      0
textX:          DB      0
textY:          DB      0
textColor:      DB      0
glyphPointer:   DW      0
glyphX:         DB      0
glyphY:         DB      0
glyphRow:       DB      0
glyphColumn:    DB      0
glyphBits:      DB      0
drawColor:      DB      0
fillColor:      DB      0
fillLeft:       DB      0
fillTop:        DB      0
fillWidth:      DB      0
fillHeight:     DB      0
fillX:          DB      0
fillY:          DB      0
plotColor:      DB      0
plotShift:      DB      0
plotAddress:    DW      0

CodeEnd:
        SAVEBIN "build/vz200/sixies-vz200.bin", Start, CodeEnd - Start
