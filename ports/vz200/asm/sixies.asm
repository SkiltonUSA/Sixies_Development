; Sixies VZ200 strawman
;
; An expanded-RAM VZ200 prototype. It keeps the core 5x5 placement and merge
; loop intentionally compact while proving the final mode-1 composition:
; board, score, next piece, cursor, and keyboard controls in 128x64 pixels.

        DEVICE  NOSLOT64K

VRAM            EQU     $7000
LATCH           EQU     $6800
LOAD_ADDR       EQU     $7AE9
LATCH_DISPLAY   EQU     %00011000       ; Mode 1 with the buff/white background.
SPEAKER_POSITIVE EQU    %00011001       ; Bit 0 drives one side of the speaker.
SPEAKER_NEGATIVE EQU    %00111000       ; Bit 5 drives the other side.
JOYSTICK_LEFT_PORT EQU  $2B             ; Left VZ joystick: U/D/L/R/Fire.
JOYSTICK_LEFT_ARM_PORT EQU $27          ; Left VZ joystick: Arm button.
JOYSTICK_IDLE   EQU     %00011111       ; All five controls are active-low.
JOYSTICK_ARM_IDLE EQU   %00010000

BOARD_CELLS     EQU     25
BOARD_SIZE      EQU     5
HIGH_SCORE_COUNT EQU    5
MERGE_CALLOUT_GENERIC_COUNT EQU 7
SCREEN_BYTES    EQU     $0800

ACTION_NONE     EQU     0
ACTION_UP       EQU     1
ACTION_DOWN     EQU     2
ACTION_LEFT     EQU     3
ACTION_RIGHT    EQU     4
ACTION_ROTATE   EQU     5
ACTION_PLACE    EQU     6
ACTION_NEW      EQU     7
ACTION_FILL     EQU     8               ; Development-only endgame shortcut.

GRID_COLOR      EQU     2               ; Magenta in the buff/white CG2 set.
CURSOR_COLOR    EQU     1               ; Cyan, distinct from the grid.
DIE_COLOR       EQU     3               ; Orange, distinct from grid and background.

        ORG     LOAD_ADDR

Start:
        DI                              ; The ROM IRQ changes the video latch.
        LD      SP, $8FFE               ; Stock-RAM stack until the expansion check passes.
        LD      A, LATCH_DISPLAY        ; Mode 1 graphics, buff/white background.
        LD      (LATCH), A
        CALL    CheckExpandedMemory
        OR      A
        JP      Z, ExpandedMemoryMissing
        LD      SP, $CFFE               ; Expanded-RAM stack above pre-rendered title frames.
        CALL    ProbeJoystickModule
        CALL    DrawExpandedMemoryFound
        CALL    ExpandedMemoryStatusDelay
        JP      RunAttractMode

; Idle boot flow. Each page is held for six seconds unless Space/Return opens
; the instructions or N starts a game, then the sequence loops from the
; presentation page.
RunAttractMode:
        LD      A, 1
        LD      (attractMode), A
AttractIntroScreen:
        CALL    DrawPresentsScreen
        CALL    WaitAttractScreen
        CP      ACTION_NEW
        JP      Z, InstructionStartGame
        CP      ACTION_PLACE
        JP      Z, TitleShowInstructions
AttractTitleScreen:
        CALL    DrawTitleScreen
        CALL    WaitAttractTitleScreen
        CP      ACTION_NEW
        JP      Z, InstructionStartGame
        CP      ACTION_PLACE
        JP      Z, TitleShowInstructions
AttractHighScoreScreen:
        CALL    DrawHighScoreScreen
        CALL    WaitAttractScreen
        CP      ACTION_NEW
        JP      Z, InstructionStartGame
        CP      ACTION_PLACE
        JP      Z, TitleShowInstructions
AttractCreditsScreen:
        CALL    DrawCreditsScreen
        CALL    WaitAttractScreen
        CP      ACTION_NEW
        JP      Z, InstructionStartGame
        CP      ACTION_PLACE
        JP      Z, TitleShowInstructions
        JR      AttractIntroScreen

; Poll every tenth of a second so Space remains responsive during the six
; second attract-page hold. Other keys are ignored until released.
WaitAttractScreen:
        LD      B, 60
WaitAttractScreenTick:
        CALL    GameOverTimeoutDelay
        CALL    PollAction
        CP      ACTION_PLACE
        RET     Z
        CP      ACTION_NEW
        RET     Z
        DJNZ    WaitAttractScreenTick
        XOR     A
        RET

; The title's stars still twinkle during its timed attract-page hold.
WaitAttractTitleScreen:
        LD      B, 60
WaitAttractTitleScreenTick:
        CALL    GameOverTimeoutDelay
        PUSH    BC
        CALL    AttractTitleTwinkleTick
        POP     BC
        CALL    PollAction
        CP      ACTION_PLACE
        RET     Z
        CP      ACTION_NEW
        RET     Z
        DJNZ    WaitAttractTitleScreenTick
        XOR     A
        RET

TitleLoop:
        CALL    PollAction
        OR      A
        JR      NZ, TitleShowInstructions
        CALL    TitleTwinkleTick
        JR      TitleLoop
TitleShowInstructions:
        XOR     A
        LD      (attractMode), A
        CALL    DrawInstructionScreen
InstructionLoop:
        CALL    PollAction
        OR      A
        JR      Z, InstructionLoop
InstructionStartGame:
        CALL    NewGame
        LD      A, 1                    ; Do not replay the title-screen key in-game.
        LD      (keyLocked), A
        CALL    DrawScreen

MainLoop:
        LD      A, (gameOver)
        OR      A
        JP      NZ, WaitForHighScoreScreen
        CALL    PollAction
        OR      A
        JR      NZ, MainLoopAction
        CALL    UpdateMergeCallout
        JR      MainLoop
MainLoopAction:
        LD      (pendingAction), A
        LD      A, (pendingAction)
        CP      ACTION_PLACE
        JR      Z, MainLoopFullRedraw
        CP      ACTION_NEW
        JR      Z, MainLoopFullRedraw
        CP      ACTION_FILL
        JR      Z, MainLoopFullRedraw
        CALL    EraseCursor
        LD      A, (pendingAction)
        CALL    HandleAction
        CALL    CalculatePlacement
        LD      A, (pendingAction)
        CP      ACTION_ROTATE
        CALL    Z, RedrawCurrentPiece
        CALL    DrawCursor
        JR      MainLoop
MainLoopFullRedraw:
        CALL    HandleAction
        CALL    DrawScreen
        JR      MainLoop

; Hold the game-over art for ten seconds, polling often enough for Space or
; Return to skip directly to the high-score page.
WaitForHighScoreScreen:
        LD      B, 100
WaitForHighScoreScreenTick:
        CALL    GameOverTimeoutDelay
        CALL    PollAction
        CP      ACTION_PLACE
        JP      Z, ShowHighScoreScreen
        DJNZ    WaitForHighScoreScreenTick
ShowHighScoreScreen:
        CALL    CheckHighScoreQualification
        OR      A
        CALL    NZ, EnterHighScoreInitials
        CALL    RecordHighScore
        CALL    DrawHighScoreScreen
HighScoreScreenLoop:
        CALL    PollAction
        OR      A
        JR      Z, HighScoreScreenLoop
        CP      ACTION_PLACE
        JR      Z, HighScoreScreenNewGame
        CP      ACTION_NEW
        JR      NZ, HighScoreScreenLoop
HighScoreScreenNewGame:
        CALL    NewGame
        CALL    DrawScreen
        JP      MainLoop

; Approximately one tenth of a second at the VZ200 clock rate.
GameOverTimeoutDelay:
        LD      DE, $3400
GameOverTimeoutDelayLoop:
        DEC     DE
        LD      A, D
        OR      E
        JR      NZ, GameOverTimeoutDelayLoop
        RET

; A VZ200 16 KB module maps RAM through $cfff. Probe a scratch byte before
; moving the stack or accessing the pre-rendered presentation assets there.
CheckExpandedMemory:
        LD      HL, $C000
        LD      A, (HL)
        LD      (memoryProbeOriginal), A
        LD      A, $55
        LD      (HL), A
        CP      (HL)
        JR      NZ, CheckExpandedMemoryMissing
        LD      A, $AA
        LD      (HL), A
        CP      (HL)
        JR      NZ, CheckExpandedMemoryMissing
        LD      A, (memoryProbeOriginal)
        LD      (HL), A
        LD      A, 1
        RET
CheckExpandedMemoryMissing:
        XOR     A
        RET

ExpandedMemoryMissing:
        CALL    DrawExpandedMemoryMissing
ExpandedMemoryMissingLoop:
        CALL    PollAction
        JR      ExpandedMemoryMissingLoop

; ---------------------------------------------------------------------------
; Input. The keyboard is memory-mapped at $6800-$6fff. The optional VZ
; joystick module is read through standard I/O ports $2B and $27. Each input
; source has a release lock, preventing uncontrolled cursor repeats.
; ---------------------------------------------------------------------------

PollAction:
        PUSH    BC                      ; Attract and timeout loops keep counters in B.
        CALL    PollKeyboardAction
        OR      A
        JR      NZ, PollActionReturn
        CALL    PollJoystickAction
PollActionReturn:
        POP     BC
        RET

PollKeyboardAction:
        LD      A, (keyLocked)
        OR      A
        JR      Z, PollKeyboardActionScan
        LD      A, ($6800)
        AND     $3F
        CP      $3F
        JR      NZ, PollKeyboardActionNone
        XOR     A
        LD      (keyLocked), A
PollKeyboardActionNone:
        XOR     A
        RET

PollKeyboardActionScan:
        LD      A, ($68FE)              ; T W - E Q R
        BIT     1, A
        JR      Z, PollKeyboardActionUp
        BIT     4, A
        JR      Z, PollKeyboardActionRotate
        BIT     3, A
        JR      Z, PollKeyboardActionRotate

        LD      A, ($68FD)              ; G S Ctrl D A F
        BIT     1, A
        JR      Z, PollKeyboardActionDown
        BIT     3, A
        JR      Z, PollKeyboardActionRight
        BIT     4, A
        JR      Z, PollKeyboardActionLeft

        LD      A, ($68EF)              ; N . , - / Space M
        BIT     0, A
        JR      Z, PollKeyboardActionNew
        BIT     1, A
        JR      Z, PollKeyboardActionFill
        BIT     4, A
        JR      Z, PollKeyboardActionPlace

        LD      A, ($68BF)              ; Y O Return I P U
        BIT     2, A
        JR      Z, PollKeyboardActionPlace
        XOR     A
        RET

PollKeyboardActionUp:
        LD      A, ACTION_UP
        JR      PollKeyboardActionFound
PollKeyboardActionDown:
        LD      A, ACTION_DOWN
        JR      PollKeyboardActionFound
PollKeyboardActionLeft:
        LD      A, ACTION_LEFT
        JR      PollKeyboardActionFound
PollKeyboardActionRight:
        LD      A, ACTION_RIGHT
        JR      PollKeyboardActionFound
PollKeyboardActionRotate:
        LD      A, ACTION_ROTATE
        JR      PollKeyboardActionFound
PollKeyboardActionPlace:
        LD      A, ACTION_PLACE
        JR      PollKeyboardActionFound
PollKeyboardActionNew:
        LD      A, ACTION_NEW
        JR      PollKeyboardActionFound
PollKeyboardActionFill:
        LD      A, ACTION_FILL
PollKeyboardActionFound:
        LD      (keyLocked), A
        RET

; The original two-button VZ interface has active-low direction, Fire, and
; Arm signals. Fire places a die; Arm rotates a double without a chord.
PollJoystickAction:
        CALL    ProbeJoystickModule
        IN      A, (JOYSTICK_LEFT_PORT)
        AND     JOYSTICK_IDLE
        LD      (joystickState), A
        IN      A, (JOYSTICK_LEFT_ARM_PORT)
        AND     JOYSTICK_ARM_IDLE
        LD      (joystickArmState), A
        LD      B, A
        LD      A, (joystickState)
        CP      JOYSTICK_IDLE
        JR      NZ, PollJoystickActionActive
        LD      A, B
        CP      JOYSTICK_ARM_IDLE
        JR      NZ, PollJoystickActionActive
        XOR     A
        LD      (joystickLocked), A
        RET
PollJoystickActionActive:
        LD      A, (joystickLocked)
        OR      A
        JR      NZ, PollJoystickActionNone
        LD      A, (joystickArmState)
        OR      A
        JR      Z, PollJoystickActionRotate
        LD      A, (joystickState)
        BIT     0, A
        JR      Z, PollJoystickActionUp
        BIT     1, A
        JR      Z, PollJoystickActionDown
        BIT     2, A
        JR      Z, PollJoystickActionLeft
        BIT     3, A
        JR      Z, PollJoystickActionRight
        LD      A, ACTION_PLACE
        JR      PollJoystickActionFound
PollJoystickActionUp:
        LD      A, ACTION_UP
        JR      PollJoystickActionFound
PollJoystickActionDown:
        LD      A, ACTION_DOWN
        JR      PollJoystickActionFound
PollJoystickActionLeft:
        LD      A, ACTION_LEFT
        JR      PollJoystickActionFound
PollJoystickActionRight:
        LD      A, ACTION_RIGHT
        JR      PollJoystickActionFound
PollJoystickActionRotate:
        LD      A, ACTION_ROTATE
PollJoystickActionFound:
        LD      B, A
        LD      A, 1
        LD      (joystickLocked), A
        LD      A, B
        RET
PollJoystickActionNone:
        XOR     A
        RET

; There is no static presence ID on the original interface: an idle module
; and an empty slot both read high. Mark it detected after any active input.
ProbeJoystickModule:
        LD      A, (joystickDetected)
        OR      A
        JR      NZ, ProbeJoystickModuleKnown
        IN      A, (JOYSTICK_LEFT_PORT)
        AND     JOYSTICK_IDLE
        CP      JOYSTICK_IDLE
        JR      NZ, ProbeJoystickModuleFound
        IN      A, (JOYSTICK_LEFT_ARM_PORT)
        AND     JOYSTICK_ARM_IDLE
        CP      JOYSTICK_ARM_IDLE
        JR      Z, ProbeJoystickModuleKnown
ProbeJoystickModuleFound:
        LD      A, 1
        LD      (joystickDetected), A
        RET
ProbeJoystickModuleKnown:
        XOR     A
        RET

HandleAction:
        CP      ACTION_UP
        JR      NZ, HandleActionDown
        LD      A, (cursorY)
        OR      A
        RET     Z
        DEC     A
        LD      (cursorY), A
        JP      PlayBounceTone
HandleActionDown:
        CP      ACTION_DOWN
        JR      NZ, HandleActionLeft
        LD      A, (cursorY)
        CP      4
        RET     Z
        INC     A
        LD      (cursorY), A
        JP      PlayBounceTone
HandleActionLeft:
        CP      ACTION_LEFT
        JR      NZ, HandleActionRight
        LD      A, (cursorX)
        OR      A
        RET     Z
        DEC     A
        LD      (cursorX), A
        JP      PlayBounceTone
HandleActionRight:
        CP      ACTION_RIGHT
        JR      NZ, HandleActionRotate
        LD      A, (cursorX)
        CP      4
        RET     Z
        INC     A
        LD      (cursorX), A
        JP      PlayBounceTone
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
        JP      PlayPlacementTone
HandleActionPlace:
        CP      ACTION_PLACE
        JR      NZ, HandleActionNew
        LD      A, (gameOver)
        OR      A
        RET     NZ
        JP      PlacePiece
HandleActionNew:
        CP      ACTION_NEW
        JR      NZ, HandleActionFill
        JP      NewGame
HandleActionFill:
        CP      ACTION_FILL
        RET     NZ
        JP      FillBoardForGameOver

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
        LD      (mergeCalloutTimer), A
        CALL    SeedRandomFromTiming
        CALL    PlayGridSetupTone
        JP      GeneratePiece

; Match the C64's per-game timing seed while guaranteeing the LFSR cannot
; enter its all-zero lock-up state. The Z80 refresh counter advances with the
; instruction stream, so start timing and input timing vary each new game.
SeedRandomFromTiming:
        LD      A, R
        OR      1
        LD      (rngState), A
        RET

RandomByte:
        LD      A, (rngState)
        ADD     A, A
        JR      NC, RandomByteStore
        XOR     $1D
RandomByteStore:
        LD      (rngState), A
        RET

; Development shortcut: fill all 25 cells with random faces 1 through 6, then
; use the normal spawn/game-over path to present the end screen.
FillBoardForGameOver:
        LD      HL, board
        LD      B, BOARD_CELLS
FillBoardForGameOverCell:
        CALL    RandomByte
        AND     7
        CP      6
        JR      NC, FillBoardForGameOverCell
        INC     A
        LD      (HL), A
        INC     HL
        DJNZ    FillBoardForGameOverCell
        JP      GeneratePiece

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
        JP      Z, PlayInvalidPlacementTone
        CALL    PlayPlacementTone
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

; The C64 uses a 3-frame bounce for cursor moves and the higher 5-frame
; portal_ping for rotations and valid placement. The VZ equivalents retain
; those pitches and approximate durations through its one-bit speaker.
PlayBounceTone:
        LD      B, 142                  ; About 730 Hz.
        LD      C, 44                   ; About 60 ms.
        JP      PlaySpeakerTone

PlayPlacementTone:
        LD      B, 214                  ; About 490 Hz, matching portal_ping.
        LD      C, 50                   ; About 100 ms.
        JP      PlaySpeakerTone

; The C64 denied-placement bonk falls from roughly 300 Hz to 120 Hz. The VZ
; cannot shape a triangle wave, so use three descending square-wave notes.
PlayInvalidPlacementTone:
        LD      B, 2
        LD      C, 12
        CALL    PlaySpeakerToneUnits
        LD      B, 3
        LD      C, 12
        CALL    PlaySpeakerToneUnits
        LD      B, 4
        LD      C, 10
        JP      PlaySpeakerToneUnits

; C64 grid setup uses a randomized sawtooth sweep. Keep this VZ version fixed
; so presentation never consumes a byte from the deterministic rules RNG.
PlayGridSetupTone:
        LD      HL, GridSetupToneNotes
        JP      PlayToneSequence

; Values 1-5 rise through the C64 merge arpeggios. Value 6 substitutes a
; descending burst for SID noise, which a one-bit speaker cannot reproduce.
PlayMergeTone:
        LD      A, (groupValue)
        DEC     A
        ADD     A, A
        LD      E, A
        LD      D, 0
        LD      HL, MergeTonePointers
        ADD     HL, DE
        LD      E, (HL)
        INC     HL
        LD      D, (HL)
        EX      DE, HL
        JP      PlayToneSequence

; Input: HL points to four (half-period, cycle-count) note pairs.
PlayToneSequence:
        LD      D, 4
PlayToneSequenceNote:
        LD      B, (HL)
        INC     HL
        LD      C, (HL)
        INC     HL
        PUSH    DE
        PUSH    HL
        CALL    PlaySpeakerTone
        POP     HL
        POP     DE
        DEC     D
        JR      NZ, PlayToneSequenceNote
        RET

; Input: B = the calibrated half-period loop count, C = full wave cycles.
PlaySpeakerTone:
        LD      A, B
        LD      (speakerHalfPeriod), A
        LD      A, C
        LD      (speakerCycles), A
PlaySpeakerToneCycle:
        LD      A, SPEAKER_POSITIVE
        LD      (LATCH), A
        CALL    SpeakerToneHalfPeriod
        LD      A, SPEAKER_NEGATIVE
        LD      (LATCH), A
        CALL    SpeakerToneHalfPeriod
        LD      A, (speakerCycles)
        DEC     A
        LD      (speakerCycles), A
        JR      NZ, PlaySpeakerToneCycle
        LD      A, LATCH_DISPLAY
        LD      (LATCH), A
        RET

; Input: B = 1 ms half-period units, C = full wave cycles. This reaches the
; C64 bonk's lower pitches without a large software delay table.
PlaySpeakerToneUnits:
        LD      A, B
        LD      (speakerHalfPeriodUnits), A
        LD      A, C
        LD      (speakerCycles), A
PlaySpeakerToneUnitsCycle:
        LD      A, SPEAKER_POSITIVE
        LD      (LATCH), A
        CALL    SpeakerToneUnitsDelay
        LD      A, SPEAKER_NEGATIVE
        LD      (LATCH), A
        CALL    SpeakerToneUnitsDelay
        LD      A, (speakerCycles)
        DEC     A
        LD      (speakerCycles), A
        JR      NZ, PlaySpeakerToneUnitsCycle
        LD      A, LATCH_DISPLAY
        LD      (LATCH), A
        RET

SpeakerToneUnitsDelay:
        LD      A, (speakerHalfPeriodUnits)
        LD      B, A
SpeakerToneUnitsDelayLoop:
        PUSH    BC
        CALL    SpeakerToneHalfPeriod
        POP     BC
        DJNZ    SpeakerToneUnitsDelayLoop
        RET

; At the VZ200's ~3.58 MHz clock, 214 loop passes plus call overhead is about
; one millisecond. The caller supplies a shorter count for higher notes.
SpeakerToneHalfPeriod:
        LD      A, (speakerHalfPeriod)
        LD      B, A
SpeakerToneHalfPeriodLoop:
        NOP
        DJNZ    SpeakerToneHalfPeriodLoop
        RET

ResolveAtActiveIndex:
        CALL    FindGroup
        LD      A, (groupCount)
        CP      3
        RET     C
        CALL    PlayMergeTone
        CALL    AnimateMergeRipple
        CALL    FlashMergeCallout
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

; Reproduce the C64 and Apple IIe merge cross on the VZ grid. Five pulses
; move in horizontally and vertically from the board edges toward activeIndex.
; Each cyan outline is restored from board state before the next pulse, so the
; effect cannot alter a die, the grid, or a later chain resolution.
AnimateMergeRipple:
        CALL    SetMergeRippleOrigin
        XOR     A
        LD      (mergeRippleStep), A
AnimateMergeRippleStep:
        XOR     A
        LD      (mergeRippleRestore), A
        CALL    DrawMergeRippleCross
        CALL    MergeRippleDelay
        LD      A, 1
        LD      (mergeRippleRestore), A
        CALL    DrawMergeRippleCross
        LD      A, (mergeRippleStep)
        INC     A
        LD      (mergeRippleStep), A
        CP      BOARD_SIZE
        JR      NZ, AnimateMergeRippleStep
        RET

; Convert the active row-major index to board coordinates once per merge.
SetMergeRippleOrigin:
        LD      A, (activeIndex)
        LD      B, 0
SetMergeRippleOriginRow:
        CP      BOARD_SIZE
        JR      C, SetMergeRippleOriginReady
        SUB     BOARD_SIZE
        INC     B
        JR      SetMergeRippleOriginRow
SetMergeRippleOriginReady:
        LD      (mergeRippleX), A
        LD      A, B
        LD      (mergeRippleY), A
        RET

; Match the Apple IIe ripple endpoints:
; left=min(step,x), right=max(4-step,x), top=min(step,y), bottom=max(4-step,y).
DrawMergeRippleCross:
        LD      A, (mergeRippleStep)
        LD      C, A
        LD      A, (mergeRippleX)
        CP      C
        JR      C, DrawMergeRippleLeftAtOrigin
        LD      B, C
        JR      DrawMergeRippleLeftReady
DrawMergeRippleLeftAtOrigin:
        LD      B, A
DrawMergeRippleLeftReady:
        LD      A, (mergeRippleY)
        LD      C, A
        CALL    ProcessMergeRippleCell

        LD      A, (mergeRippleStep)
        LD      C, A
        LD      A, 4
        SUB     C
        LD      C, A
        LD      A, (mergeRippleX)
        CP      C
        JR      NC, DrawMergeRippleRightAtOrigin
        LD      B, C
        JR      DrawMergeRippleRightReady
DrawMergeRippleRightAtOrigin:
        LD      B, A
DrawMergeRippleRightReady:
        LD      A, (mergeRippleY)
        LD      C, A
        CALL    ProcessMergeRippleCell

        LD      A, (mergeRippleStep)
        LD      C, A
        LD      A, (mergeRippleY)
        CP      C
        JR      C, DrawMergeRippleTopAtOrigin
        LD      C, A
        JR      DrawMergeRippleTopReady
DrawMergeRippleTopAtOrigin:
        LD      C, A
DrawMergeRippleTopReady:
        LD      A, (mergeRippleX)
        LD      B, A
        CALL    ProcessMergeRippleCell

        LD      A, (mergeRippleStep)
        LD      C, A
        LD      A, 4
        SUB     C
        LD      C, A
        LD      A, (mergeRippleY)
        CP      C
        JR      NC, DrawMergeRippleBottomAtOrigin
        LD      C, A
        JR      DrawMergeRippleBottomReady
DrawMergeRippleBottomAtOrigin:
        LD      C, A
DrawMergeRippleBottomReady:
        LD      A, (mergeRippleX)
        LD      B, A
        JP      ProcessMergeRippleCell

; Input: B/C = a board coordinate. Draw or restore one cross endpoint.
ProcessMergeRippleCell:
        LD      A, B
        CP      BOARD_SIZE
        RET     NC
        LD      A, C
        CP      BOARD_SIZE
        RET     NC
        LD      A, (mergeRippleRestore)
        OR      A
        JP      NZ, RestoreCell
        CALL    CellCoordinates
        JP      DrawCellCursor

; Approximately two VZ video frames. Merge effects are intentionally brief so
; a chain reaction remains responsive without relying on an interrupt timer.
MergeRippleDelay:
        LD      DE, $1400
MergeRippleDelayLoop:
        DEC     DE
        LD      A, D
        OR      E
        JR      NZ, MergeRippleDelayLoop
        RET

; Start a clean sidebar callout without delaying the merge or input loop. Its
; presentation-only timer is serviced while the game continues to run.
FlashMergeCallout:
        CALL    SelectMergeCalloutText
        LD      (mergeCalloutTextPointer), HL
        LD      A, 80                   ; Four seconds at 20 non-blocking ticks/sec.
        LD      (mergeCalloutTimer), A
        CALL    ClearMergeCallout
        JP      DrawMergeCallout

; Advance the overlay only while it is visible. A short tick delay keeps the
; hold time stable enough without an interrupt timer, but input is polled
; between every tick rather than being held for the entire four seconds.
UpdateMergeCallout:
        LD      A, (mergeCalloutTimer)
        OR      A
        RET     Z
        CALL    MergeCalloutTickDelay
        LD      A, (mergeCalloutTimer)
        DEC     A
        LD      (mergeCalloutTimer), A
        RET     NZ
        JP      ClearMergeCallout

MergeCalloutTickDelay:
        LD      DE, $1A00               ; Half the calibrated tenth-second delay.
MergeCalloutTickDelayLoop:
        DEC     DE
        LD      A, D
        OR      E
        JR      NZ, MergeCalloutTickDelayLoop
        RET

DrawMergeCallout:
        LD      A, (mergeCalloutTimer)
        OR      A
        RET     Z
        LD      HL, (mergeCalloutTextPointer)
        LD      A, (mergeCalloutTextX)
        LD      B, A
        LD      C, 29
        LD      D, CURSOR_COLOR
        JP      DrawText

ClearMergeCallout:
        XOR     A
        LD      B, 60
        LD      C, 28
        LD      D, 42
        LD      E, 7
        JP      FillRect

SelectMergeCalloutText:
        LD      A, (groupValue)
        CP      4
        JR      Z, SelectMergeCalloutTextFives
        CP      5
        JR      Z, SelectMergeCalloutTextSixies
        LD      A, (mergeCalloutIndex)
        INC     A
        CP      MERGE_CALLOUT_GENERIC_COUNT
        JR      C, SelectMergeCalloutTextStore
        XOR     A
SelectMergeCalloutTextStore:
        LD      (mergeCalloutIndex), A
        LD      E, A
        LD      D, 0
        LD      HL, MergeCalloutGenericX
        ADD     HL, DE
        LD      A, (HL)
        LD      (mergeCalloutTextX), A
        LD      A, (mergeCalloutIndex)
        ADD     A, A
        LD      E, A
        LD      D, 0
        LD      HL, MergeCalloutGenericPointers
        ADD     HL, DE
        LD      E, (HL)
        INC     HL
        LD      D, (HL)
        EX      DE, HL
        RET
SelectMergeCalloutTextFives:
        LD      A, 67
        LD      (mergeCalloutTextX), A
        LD      HL, mergeCalloutFives
        RET
SelectMergeCalloutTextSixies:
        LD      A, 65
        LD      (mergeCalloutTextX), A
        LD      HL, mergeCalloutSixies
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

; Return A=1 and retain the insertion index when the completed score belongs
; in the five-entry descending RAM table. Equal scores retain their position.
CheckHighScoreQualification:
        XOR     A
        LD      (highScoreInsertIndex), A
CheckHighScoreQualificationFind:
        LD      A, (highScoreInsertIndex)
        CP      HIGH_SCORE_COUNT
        JR      NZ, CheckHighScoreQualificationCompare
        XOR     A
        RET
CheckHighScoreQualificationCompare:
        LD      E, A
        LD      D, 0
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      A, (scoreHi)
        CP      B
        JR      C, CheckHighScoreQualificationNext
        JR      NZ, CheckHighScoreQualificationYes
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      A, (scoreLo)
        CP      B
        JR      C, CheckHighScoreQualificationNext
        JR      Z, CheckHighScoreQualificationNext
CheckHighScoreQualificationYes:
        LD      A, 1
        RET
CheckHighScoreQualificationNext:
        LD      A, (highScoreInsertIndex)
        INC     A
        LD      (highScoreInsertIndex), A
        JR      CheckHighScoreQualificationFind

; Insert the completed score into the five-entry descending RAM table. This
; runs after initials are chosen when CheckHighScoreQualification succeeds.
RecordHighScore:
        XOR     A
        LD      (highScoreInsertIndex), A
RecordHighScoreFind:
        LD      A, (highScoreInsertIndex)
        CP      HIGH_SCORE_COUNT
        RET     Z
        LD      E, A
        LD      D, 0
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      A, (scoreHi)
        CP      B
        JP      C, RecordHighScoreNext
        JR      NZ, RecordHighScoreInsert
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      A, (HL)
        LD      B, A
        LD      A, (scoreLo)
        CP      B
        JP      C, RecordHighScoreNext
        JP      Z, RecordHighScoreNext
RecordHighScoreInsert:
        LD      A, HIGH_SCORE_COUNT - 1
        LD      (highScoreShiftIndex), A
RecordHighScoreShift:
        LD      A, (highScoreShiftIndex)
        LD      B, A
        LD      A, (highScoreInsertIndex)
        CP      B
        JR      Z, RecordHighScoreStore
        LD      A, B
        LD      E, A
        LD      D, 0
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      (highScoreCopyDestination), HL
        DEC     E
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      A, (HL)
        LD      HL, (highScoreCopyDestination)
        LD      (HL), A
        LD      A, B
        LD      E, A
        LD      D, 0
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      (highScoreCopyDestination), HL
        DEC     E
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      A, (HL)
        LD      HL, (highScoreCopyDestination)
        LD      (HL), A
        LD      A, B
        CALL    HighScoreNamePointer
        LD      (highScoreCopyDestination), HL
        LD      A, B
        DEC     A
        CALL    HighScoreNamePointer
        LD      C, 3
RecordHighScoreShiftName:
        LD      A, (HL)
        INC     HL
        LD      DE, (highScoreCopyDestination)
        LD      (DE), A
        INC     DE
        LD      (highScoreCopyDestination), DE
        DEC     C
        JR      NZ, RecordHighScoreShiftName
        LD      A, (highScoreShiftIndex)
        DEC     A
        LD      (highScoreShiftIndex), A
        JR      RecordHighScoreShift
RecordHighScoreStore:
        LD      A, (highScoreInsertIndex)
        LD      E, A
        LD      D, 0
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      A, (scoreLo)
        LD      (HL), A
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      A, (scoreHi)
        LD      (HL), A
        LD      A, (highScoreInsertIndex)
        CALL    HighScoreNamePointer
        LD      DE, highScoreCurrentName
        LD      B, 3
RecordHighScoreStoreName:
        LD      A, (DE)
        LD      (HL), A
        INC     DE
        INC     HL
        DJNZ    RecordHighScoreStoreName
        RET
RecordHighScoreNext:
        LD      A, (highScoreInsertIndex)
        INC     A
        LD      (highScoreInsertIndex), A
        JP      RecordHighScoreFind

; Input: A = table index. Output: HL = its three-character initials.
HighScoreNamePointer:
        LD      E, A
        ADD     A, A
        ADD     A, E
        LD      E, A
        LD      D, 0
        LD      HL, highScoreNames
        ADD     HL, DE
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
        LD      A, (gameOver)
        OR      A
        JP      NZ, DrawGameOverScreen
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
        CALL    CalculatePlacement
        CALL    DrawCursor
        CALL    DrawMergeCallout
        CALL    DrawNextPiece
        LD      HL, newLabel
        LD      B, 58
        LD      C, 56
        LD      D, 1
        JP      DrawText

; The game-over art is a pre-rendered 88x50 four-color frame at (20, 0),
; preserving two footer rows for the final score.
DrawGameOverScreen:
        CALL    ClearVideo
        LD      HL, GameOverFrame
        LD      DE, VRAM + 5
        LD      B, GAME_OVER_FRAME_HEIGHT
DrawGameOverFrameRow:
        PUSH    BC
        LD      BC, GAME_OVER_FRAME_ROW_BYTES
        LDIR
        LD      A, E
        ADD     A, 10
        LD      E, A
        JR      NC, DrawGameOverFrameNextRow
        INC     D
DrawGameOverFrameNextRow:
        POP     BC
        DJNZ    DrawGameOverFrameRow
        LD      HL, yourScoreLabel
        LD      B, 39
        LD      C, 51
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      B, 60
        LD      C, 58
        LD      D, CURSOR_COLOR
        JP      DrawScoreAt

; Qualifying players choose three initials before their score is committed.
; Keyboard W/S changes a letter, A/D changes slot, and Space confirms; the
; joystick maps its stick and Fire button to the same actions.
EnterHighScoreInitials:
        LD      HL, highScoreCurrentName
        LD      (HL), 'A'
        INC     HL
        LD      (HL), 'A'
        INC     HL
        LD      (HL), 'A'
        XOR     A
        LD      (highScoreInitialPosition), A
        CALL    DrawHighScoreEntryScreen
EnterHighScoreInitialsLoop:
        CALL    PollAction
        OR      A
        JR      Z, EnterHighScoreInitialsLoop
        CP      ACTION_UP
        JR      Z, HighScoreInitialPreviousLetter
        CP      ACTION_DOWN
        JR      Z, HighScoreInitialNextLetter
        CP      ACTION_LEFT
        JR      Z, HighScoreInitialPreviousSlot
        CP      ACTION_RIGHT
        JR      Z, HighScoreInitialNextSlot
        CP      ACTION_PLACE
        JR      Z, HighScoreInitialConfirm
        JR      EnterHighScoreInitialsLoop

HighScoreInitialPreviousLetter:
        CALL    HighScoreInitialPointer
        LD      A, (HL)
        CP      'A'
        JR      NZ, HighScoreInitialPreviousLetterDecrement
        LD      A, 'Z'
        JR      HighScoreInitialStoreLetter
HighScoreInitialPreviousLetterDecrement:
        DEC     A
        JR      HighScoreInitialStoreLetter
HighScoreInitialNextLetter:
        CALL    HighScoreInitialPointer
        LD      A, (HL)
        INC     A
        CP      $5B                    ; One byte beyond Z.
        JR      NZ, HighScoreInitialStoreLetter
        LD      A, 'A'
HighScoreInitialStoreLetter:
        LD      (HL), A
        CALL    DrawHighScoreEntryInitials
        JR      EnterHighScoreInitialsLoop

HighScoreInitialPreviousSlot:
        LD      A, (highScoreInitialPosition)
        OR      A
        JR      Z, EnterHighScoreInitialsLoop
        DEC     A
        LD      (highScoreInitialPosition), A
        CALL    DrawHighScoreEntryInitials
        JR      EnterHighScoreInitialsLoop
HighScoreInitialNextSlot:
        LD      A, (highScoreInitialPosition)
        CP      2
        JR      Z, EnterHighScoreInitialsLoop
        INC     A
        LD      (highScoreInitialPosition), A
        CALL    DrawHighScoreEntryInitials
        JR      EnterHighScoreInitialsLoop
HighScoreInitialConfirm:
        LD      A, (highScoreInitialPosition)
        CP      2
        RET     Z
        INC     A
        LD      (highScoreInitialPosition), A
        CALL    DrawHighScoreEntryInitials
        JR      EnterHighScoreInitialsLoop

; Output HL = the selected byte within highScoreCurrentName.
HighScoreInitialPointer:
        LD      A, (highScoreInitialPosition)
        LD      E, A
        LD      D, 0
        LD      HL, highScoreCurrentName
        ADD     HL, DE
        RET

DrawHighScoreEntryScreen:
        CALL    ClearVideo
        LD      HL, newHighScoreTitle
        LD      B, 29
        LD      C, 4
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, yourScoreLabel
        LD      B, 39
        LD      C, 13
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      B, 60
        LD      C, 13
        LD      D, CURSOR_COLOR
        CALL    DrawScoreAt
        LD      HL, enterInitialsLabel
        LD      B, 29
        LD      C, 22
        LD      D, GRID_COLOR
        CALL    DrawText
        CALL    DrawHighScoreEntryInitials
        LD      HL, highScoreEntryMoveLabel
        LD      B, 17
        LD      C, 42
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, highScoreEntryConfirmLabel
        LD      B, 19
        LD      C, 48
        LD      D, CURSOR_COLOR
        JP      DrawText

DrawHighScoreEntryInitials:
        XOR     A
        LD      B, 58
        LD      C, 29
        LD      D, 15
        LD      E, 8
        CALL    FillRect
        LD      HL, highScoreCurrentName
        LD      B, 58
        LD      C, 30
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      A, (highScoreInitialPosition)
        LD      E, A
        ADD     A, A
        ADD     A, A
        ADD     A, E
        ADD     A, 58
        LD      B, A
        LD      C, 36
        LD      D, 4
        LD      E, 1
        LD      A, GRID_COLOR
        JP      FillRect

DrawHighScoreScreen:
        CALL    ClearVideo
        LD      HL, HighScoreMascot
        LD      B, 2
        LD      C, 17
        LD      D, 38
        LD      E, 30
        CALL    DrawTitleSprite
        LD      HL, highScoreTitle
        LD      B, 36
        LD      C, 1
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, scoreLabel
        LD      B, 35
        LD      C, 9
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      B, 65
        LD      C, 9
        LD      D, CURSOR_COLOR
        CALL    DrawScoreAt
        LD      HL, bestFiveLabel
        LD      B, 43
        LD      C, 23
        LD      D, GRID_COLOR
        CALL    DrawText
        XOR     A
        LD      (highScoreDisplayIndex), A
        LD      A, 29
        LD      (highScoreDisplayY), A
DrawHighScoreScreenLine:
        LD      A, (highScoreDisplayIndex)
        CALL    BuildHighScoreName
        LD      HL, highScoreNameText
        LD      B, 43
        LD      A, (highScoreDisplayY)
        LD      C, A
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      A, (highScoreDisplayIndex)
        LD      B, 60
        LD      A, (highScoreDisplayY)
        LD      C, A
        LD      D, DIE_COLOR
        LD      A, (highScoreDisplayIndex)
        CALL    DrawHighScoreAt
        LD      A, (highScoreDisplayIndex)
        INC     A
        LD      (highScoreDisplayIndex), A
        CP      HIGH_SCORE_COUNT
        JR      Z, DrawHighScoreScreenPrompt
        LD      A, (highScoreDisplayY)
        ADD     A, 6
        LD      (highScoreDisplayY), A
        JR      DrawHighScoreScreenLine
DrawHighScoreScreenPrompt:
        LD      A, (attractMode)
        OR      A
        JR      NZ, DrawHighScoreScreenAttractPrompt
        LD      HL, highScorePrompt
        LD      B, 29
        LD      C, 59
        LD      D, CURSOR_COLOR
        JP      DrawText
DrawHighScoreScreenAttractPrompt:
        LD      HL, titlePrompt
        LD      B, 35
        LD      C, 59
        LD      D, CURSOR_COLOR
        JP      DrawText

; A native VZ200 interpretation of the supplied C64 credits reference. The
; existing dice illustration avoids a lossy full-screen artwork conversion.
DrawCreditsScreen:
        CALL    ClearVideo
        LD      HL, HighScoreMascot
        LD      B, 88
        LD      C, 15
        LD      D, 38
        LD      E, 30
        CALL    DrawTitleSprite
        LD      HL, titleText
        LD      B, 14
        LD      C, 4
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, creditsDesigned
        LD      B, 12
        LD      C, 16
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, creditsDeveloped
        LD      B, 4
        LD      C, 25
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, creditsName
        LD      B, 14
        LD      C, 34
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, creditsCopyright
        LD      B, 20
        LD      C, 43
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, creditsPrompt
        LD      B, 35
        LD      C, 58
        LD      D, CURSOR_COLOR
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

DrawExpandedMemoryFound:
        CALL    ClearVideo
        LD      HL, memoryFoundLineOne
        LD      B, 26
        LD      C, 18
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, memoryFoundLineTwo
        LD      B, 39
        LD      C, 26
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, joystickModuleLineOne
        LD      B, 26
        LD      C, 36
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      A, (joystickDetected)
        OR      A
        JR      Z, DrawJoystickModuleMissing
        LD      HL, joystickModuleFoundLine
        JR      DrawJoystickModuleStatus
DrawJoystickModuleMissing:
        LD      HL, joystickModuleMissingLine
DrawJoystickModuleStatus:
        LD      B, 29
        LD      C, 44
        LD      D, DIE_COLOR
        JP      DrawText

DrawExpandedMemoryMissing:
        CALL    ClearVideo
        LD      HL, memoryMissingLineOne
        LD      B, 26
        LD      C, 20
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, memoryMissingLineTwo
        LD      B, 24
        LD      C, 28
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, memoryMissingLineThree
        LD      B, 19
        LD      C, 36
        LD      D, CURSOR_COLOR
        JP      DrawText

; Full-width 128x56 intro art leaves room for a caption below it.
DrawPresentsScreen:
        CALL    ClearVideo
        LD      HL, PresentsFrame
        LD      DE, VRAM
        LD      BC, PRESENTS_FRAME_BYTES
        LDIR
        LD      HL, presentationText
        LD      B, 34
        LD      C, 58
        LD      D, CURSOR_COLOR
        JP      DrawText

; Keep the successful memory probe visible briefly before the title appears.
ExpandedMemoryStatusDelay:
        LD      B, 4
ExpandedMemoryStatusDelayPass:
        LD      DE, 0
ExpandedMemoryStatusDelayInner:
        DEC     DE
        LD      A, D
        OR      E
        JR      NZ, ExpandedMemoryStatusDelayInner
        PUSH    BC
        CALL    ProbeJoystickModule
        OR      A
        CALL    NZ, DrawExpandedMemoryFound
        POP     BC
        DJNZ    ExpandedMemoryStatusDelayPass
        RET

DrawTitleScreen:
        CALL    ClearVideo
        CALL    DrawTitleFrame
        LD      HL, titlePrompt
        LD      B, 35
        LD      C, 56
        LD      D, CURSOR_COLOR
        CALL    DrawText
        XOR     A
        LD      (titleTwinklePhase), A
        LD      HL, 0
        LD      (titleTwinkleTimer), HL
        JP      DrawTitleTwinkle

; The source title stays static. Every interval restores only its 112x45
; rectangle, then swaps a small transparent star arrangement over the logo.
TitleTwinkleTick:
        LD      HL, (titleTwinkleTimer)
        LD      DE, 1
        JP      TitleTwinkleAdvance

; The attract loop polls every tenth of a second rather than every CPU frame.
; Advance the same timer by 2,048 counts to retain a visible one-second blink.
AttractTitleTwinkleTick:
        LD      HL, (titleTwinkleTimer)
        LD      DE, $0800
TitleTwinkleAdvance:
        ADD     HL, DE
        LD      (titleTwinkleTimer), HL
        LD      A, H
        CP      $40                    ; About one second on the title loop.
        RET     C
        LD      HL, 0
        LD      (titleTwinkleTimer), HL
        LD      A, (titleTwinklePhase)
        XOR     1
        LD      (titleTwinklePhase), A
        CALL    DrawTitleFrame
        JP      DrawTitleTwinkle

DrawTitleTwinkle:
        LD      A, (titleTwinklePhase)
        OR      A
        JR      NZ, DrawTitleTwinkleSecond
        LD      HL, TitleStarPurple
        LD      B, 8
        LD      C, 5
        CALL    DrawTitleSprite20
        LD      HL, TitleStarGold
        LD      B, 82
        LD      C, 29
        CALL    DrawTitleSprite20
        LD      HL, TitleSparkYellow
        LD      B, 108
        LD      C, 45
        JP      DrawTitleSprite5
DrawTitleTwinkleSecond:
        LD      HL, TitleStarGreen
        LD      B, 98
        LD      C, 5
        CALL    DrawTitleSprite20
        LD      HL, TitleSparkOrange
        LD      B, 10
        LD      C, 45
        JP      DrawTitleSprite5

; Input: HL = one byte per pixel (zero is transparent), B/C = top-left,
; D/E = width/height. The tiny source sprites make PlotPixel fast enough for
; an intentionally slow title-screen effect.
DrawTitleSprite:
        LD      (titleSpritePointer), HL
        LD      A, B
        LD      (titleSpriteX), A
        LD      A, C
        LD      (titleSpriteY), A
        LD      A, D
        LD      (titleSpriteWidth), A
        LD      A, E
        LD      (titleSpriteHeight), A
        XOR     A
        LD      (titleSpriteRow), A
DrawTitleSpriteRow:
        LD      A, (titleSpriteRow)
        LD      B, A
        LD      A, (titleSpriteHeight)
        CP      B
        RET     Z
        XOR     A
        LD      (titleSpriteColumn), A
DrawTitleSpriteColumn:
        LD      A, (titleSpriteColumn)
        LD      B, A
        LD      A, (titleSpriteWidth)
        CP      B
        JR      Z, DrawTitleSpriteNextRow
        LD      HL, (titleSpritePointer)
        LD      A, (HL)
        INC     HL
        LD      (titleSpritePointer), HL
        OR      A
        JR      Z, DrawTitleSpriteSkipPixel
        LD      (titleSpriteColor), A
        LD      A, (titleSpriteX)
        LD      B, A
        LD      A, (titleSpriteColumn)
        ADD     A, B
        LD      B, A
        LD      A, (titleSpriteY)
        LD      C, A
        LD      A, (titleSpriteRow)
        ADD     A, C
        LD      C, A
        LD      A, (titleSpriteColor)
        CALL    PlotPixel
DrawTitleSpriteSkipPixel:
        LD      A, (titleSpriteColumn)
        INC     A
        LD      (titleSpriteColumn), A
        JR      DrawTitleSpriteColumn
DrawTitleSpriteNextRow:
        LD      A, (titleSpriteRow)
        INC     A
        LD      (titleSpriteRow), A
        JR      DrawTitleSpriteRow

DrawTitleSprite20:
        LD      D, 20
        LD      E, 20
        JP      DrawTitleSprite

DrawTitleSprite5:
        LD      D, 5
        LD      E, 4
        JP      DrawTitleSprite

DrawInstructionScreen:
        CALL    ClearVideo
        CALL    DrawInstructionTitleBox
        LD      HL, instructionTitle
        LD      B, 34
        LD      C, 2
        LD      D, DIE_COLOR
        CALL    DrawText
        LD      HL, instructionPlace
        LD      B, 11
        LD      C, 10
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, instructionMatch
        LD      B, 19
        LD      C, 16
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, instructionMerge
        LD      B, 14
        LD      C, 22
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, instructionSixes
        LD      B, 21
        LD      C, 28
        LD      D, GRID_COLOR
        CALL    DrawText
        LD      HL, instructionGameOver
        LD      B, 11
        LD      C, 34
        LD      D, GRID_COLOR
        CALL    DrawText
        CALL    DrawInstructionKeysBox
        LD      HL, instructionMove
        LD      B, 14
        LD      C, 40
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, instructionRotate
        LD      B, 17
        LD      C, 46
        LD      D, CURSOR_COLOR
        CALL    DrawText
        LD      HL, instructionPlaceKey
        LD      B, 11
        LD      C, 58
        LD      D, CURSOR_COLOR
        JP      DrawText

; The VZ adaptation keeps the reference card's title and control panels
; while leaving enough scan lines for a readable rules summary and prompt.
DrawInstructionTitleBox:
        LD      A, DIE_COLOR
        LD      B, 4
        LD      C, 0
        LD      D, 120
        CALL    DrawHLine
        LD      A, DIE_COLOR
        LD      B, 4
        LD      C, 7
        LD      D, 120
        CALL    DrawHLine
        LD      A, DIE_COLOR
        LD      B, 4
        LD      C, 0
        LD      D, 8
        CALL    DrawVLine
        LD      A, DIE_COLOR
        LD      B, 123
        LD      C, 0
        LD      D, 8
        JP      DrawVLine

DrawInstructionKeysBox:
        LD      A, CURSOR_COLOR
        LD      B, 4
        LD      C, 39
        LD      D, 120
        CALL    DrawHLine
        LD      A, CURSOR_COLOR
        LD      B, 4
        LD      C, 53
        LD      D, 120
        CALL    DrawHLine
        LD      A, CURSOR_COLOR
        LD      B, 4
        LD      C, 39
        LD      D, 15
        CALL    DrawVLine
        LD      A, CURSOR_COLOR
        LD      B, 123
        LD      C, 39
        LD      D, 15
        JP      DrawVLine

; Copy the static four-color 112x45 title frame at (8, 5). It contains 28
; bytes per row; the visible 128-pixel VRAM stride is 32 bytes per row.
DrawTitleFrame:
        LD      HL, TitleFrame
        LD      DE, VRAM + (5 * 32) + 2
        LD      B, 45
DrawTitleFrameRow:
        PUSH    BC
        LD      BC, 28
        LDIR
        LD      A, E
        ADD     A, 4
        LD      E, A
        JR      NC, DrawTitleFrameNextRow
        INC     D
DrawTitleFrameNextRow:
        POP     BC
        DJNZ    DrawTitleFrameRow
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
        LD      B, 70
        LD      C, 41
        CALL    DrawNextPieceFirst
        LD      B, 80
        LD      C, 41
        JP      DrawNextPieceSecond
DrawNextPieceDown:
        CP      1
        JR      NZ, DrawNextPieceLeft
        LD      B, 75
        LD      C, 36
        CALL    DrawNextPieceFirst
        LD      B, 75
        LD      C, 46
        JP      DrawNextPieceSecond
DrawNextPieceLeft:
        CP      2
        JR      NZ, DrawNextPieceUp
        LD      B, 80
        LD      C, 41
        CALL    DrawNextPieceFirst
        LD      B, 70
        LD      C, 41
        JP      DrawNextPieceSecond
DrawNextPieceUp:
        LD      B, 75
        LD      C, 46
        CALL    DrawNextPieceFirst
        LD      B, 75
        LD      C, 36
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
        LD      B, 75
        LD      C, 41
        LD      A, (pieceA)
        LD      D, DIE_COLOR
        JP      DrawDie

; Redrawing this small panel keeps rotation feedback visible without a full
; screen refresh.
RedrawCurrentPiece:
        LD      B, 68
        LD      C, 34
        LD      D, 22
        LD      E, 21
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
        LD      B, 60
        LD      C, 20
        LD      D, CURSOR_COLOR
        JP      DrawScoreAt

; Input: B/C = text coordinate, D = color. The shared formatter is used for
; the current score and each persistent high-score table entry.
DrawScoreAt:
        LD      A, B
        LD      (scoreDrawX), A
        LD      A, C
        LD      (scoreDrawY), A
        LD      A, D
        LD      (scoreDrawColor), A
        CALL    BuildScoreText
        JP      DrawFormattedScore

; Input: A = high-score index, B/C = text coordinate, D = color.
DrawHighScoreAt:
        LD      (highScoreDrawIndex), A
        LD      A, B
        LD      (scoreDrawX), A
        LD      A, C
        LD      (scoreDrawY), A
        LD      A, D
        LD      (scoreDrawColor), A
        CALL    BuildHighScoreText
DrawFormattedScore:
        LD      HL, scoreText
        LD      A, (scoreDrawX)
        LD      B, A
        LD      A, (scoreDrawY)
        LD      C, A
        LD      A, (scoreDrawColor)
        LD      D, A
        JP      DrawText

BuildScoreText:
        LD      A, (scoreLo)
        LD      (scoreTempLo), A
        LD      A, (scoreHi)
        LD      (scoreTempHi), A
        JR      BuildScoreTextPrepare

BuildHighScoreText:
        LD      A, (highScoreDrawIndex)
        LD      E, A
        LD      D, 0
        LD      HL, highScoreLo
        ADD     HL, DE
        LD      A, (HL)
        LD      (scoreTempLo), A
        LD      HL, highScoreHi
        ADD     HL, DE
        LD      A, (HL)
        LD      (scoreTempHi), A
        JP      BuildScoreTextPrepare

; Input: A = high-score index. Build a null-terminated string for DrawText.
BuildHighScoreName:
        CALL    HighScoreNamePointer
        LD      DE, highScoreNameText
        LD      B, 3
BuildHighScoreNameCopy:
        LD      A, (HL)
        LD      (DE), A
        INC     HL
        INC     DE
        DJNZ    BuildHighScoreNameCopy
        XOR     A
        LD      (DE), A
        RET

BuildScoreTextPrepare:
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
        CP      '!'
        JR      Z, GlyphIndexExclamation
        CP      ' '
        JR      Z, GlyphIndexSpace
        CP      '.'
        JR      Z, GlyphIndexDot
        CP      '+'
        JR      Z, GlyphIndexPlus
        CP      '/'
        JR      Z, GlyphIndexSlash
        CP      '('
        JR      Z, GlyphIndexLeftParenthesis
        CP      ')'
        JR      Z, GlyphIndexRightParenthesis
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
GlyphIndexExclamation:
        LD      A, 37
        RET
GlyphIndexDot:
        LD      A, 42
        RET
GlyphIndexPlus:
        LD      A, 38
        RET
GlyphIndexSlash:
        LD      A, 39
        RET
GlyphIndexLeftParenthesis:
        LD      A, 40
        RET
GlyphIndexRightParenthesis:
        LD      A, 41
        RET

DrawGlyph:
        LD      (glyphIndex), A
        LD      A, B
        LD      (glyphX), A
        LD      A, C
        LD      (glyphY), A
        LD      A, D
        LD      (drawColor), A
        LD      A, (glyphIndex)
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
titlePrompt:    DB      "PRESS SPACE", 0
highScoreTitle: DB      "HIGH SCORES", 0
newHighScoreTitle: DB   "NEW HIGH SCORE", 0
yourScoreLabel: DB      "YOUR SCORE", 0
bestFiveLabel:  DB      "BEST FIVE", 0
highScorePrompt: DB    "SPACE NEW GAME", 0
enterInitialsLabel: DB  "ENTER INITIALS", 0
highScoreEntryMoveLabel: DB "W/S LETTER A/D SLOT", 0
highScoreEntryConfirmLabel: DB "SPACE FIRE CONFIRM", 0
presentationText: DB     "PRESENTATION", 0
creditsDesigned: DB      "DESIGNED AND", 0
creditsDeveloped: DB     "DEVELOPED BY", 0
creditsName: DB          "DSKILTON", 0
creditsCopyright: DB     "(C)2026", 0
creditsPrompt: DB        "PRESS SPACE", 0
memoryFoundLineOne: DB  "EXPANDED MEMORY", 0
memoryFoundLineTwo: DB  "FOUND...OK", 0
joystickModuleLineOne: DB "JOYSTICK MODULE", 0
joystickModuleFoundLine: DB "DETECTED....OK", 0
joystickModuleMissingLine: DB "DETECTED....NO", 0
memoryMissingLineOne: DB "EXPANDED MEMORY", 0
memoryMissingLineTwo: DB "REQUIRED TO PLAY", 0
memoryMissingLineThree: DB "INSTALL 16K MODULE", 0
instructionTitle: DB    "SIXIES RULES", 0
instructionPlace: DB    "PLACE ROTATE DICE 5X5", 0
instructionMatch: DB    "MATCH 3+ SAME DICE", 0
instructionMerge: DB    "THEY MERGE UP A FACE", 0
instructionSixes: DB    "SIXES CLEAR SPACE", 0
instructionGameOver: DB  "CHAIN REACTIONS SCORE", 0
instructionMove: DB     "WASD MOVE Q/E ROTATE", 0
instructionRotate: DB   "SPACE/RETURN PLACES", 0
instructionPlaceKey: DB "PRESS ANY KEY TO PLAY", 0
scoreLabel:     DB      "SCORE", 0
mergeCalloutYes: DB     "YES!", 0
mergeCalloutBoom: DB    "BOOM!", 0
mergeCalloutLetsGo: DB  "LETS GO!", 0
mergeCalloutAwesome: DB "AWESOME!", 0
mergeCalloutSixies: DB  "SIXIES!", 0
mergeCalloutFives: DB   "FIVES!", 0
mergeCalloutWow: DB     "WOW!", 0
mergeCalloutWhoa: DB    "WHOA!", 0
mergeCalloutDang: DB    "DANG!!", 0
; FIVES and SIXIES are deliberately absent from the generic rotation. They
; are reserved for merges of value-4 and value-5 dice respectively.
MergeCalloutGenericPointers:
        DW      mergeCalloutYes, mergeCalloutBoom, mergeCalloutLetsGo
        DW      mergeCalloutAwesome, mergeCalloutWow, mergeCalloutWhoa
        DW      mergeCalloutDang
MergeCalloutGenericX:
        DB      72, 70, 62, 62, 72, 70, 67
GridSetupToneNotes:
        DB      180, 10, 140, 14, 100, 20, 70, 28
MergeToneOneNotes:
        DB      255, 10, 202, 12, 160, 15, 100, 22
MergeToneTwoNotes:
        DB      202, 12, 153, 16, 126, 19, 100, 22
MergeToneThreeNotes:
        DB      132, 18, 106, 22, 84, 28, 67, 34
MergeToneFourNotes:
        DB      100, 22, 80, 28, 67, 34, 50, 43
MergeToneFiveNotes:
        DB      80, 28, 67, 34, 54, 42, 43, 52
MergeToneSixNotes:
        DB      43, 52, 60, 38, 86, 27, 128, 18
MergeTonePointers:
        DW      MergeToneOneNotes, MergeToneTwoNotes, MergeToneThreeNotes
        DW      MergeToneFourNotes, MergeToneFiveNotes, MergeToneSixNotes
newLabel:       DB      "N NEW", 0
scoreText:      DB      "0000", 0
highScoreNameText: DS    4
highScoreCurrentName: DB "AAA", 0

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

; A-Z, 0-9, space, !, +, /, parentheses, and dot. Each glyph is five rows,
; four bits per row.
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
        DB $04,$04,$04,$00,$04 ; !
        DB $00,$04,$0E,$04,$00 ; +
        DB $01,$02,$04,$08,$00 ; /
        DB $02,$04,$04,$04,$02 ; (
        DB $04,$02,$02,$02,$04 ; )
        DB $00,$00,$00,$00,$04 ; .

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
; Session-seeded five-score table requested for the VZ200 presentation.
highScoreLo:    DB      $6D, $00, $66, $C8, $85
highScoreHi:    DB      $05, $04, $03, $01, $01
highScoreNames: DB      "DOM", "TAN", "TWD", "PRI", "BOB"
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
joystickLocked: DB      0
joystickDetected: DB    0
joystickState:  DB      JOYSTICK_IDLE
joystickArmState: DB    JOYSTICK_ARM_IDLE
pendingAction:  DB      0
memoryProbeOriginal: DB 0
mergeRippleStep: DB     0
mergeRippleRestore: DB  0
mergeRippleX:    DB      0
mergeRippleY:    DB      0
mergeCalloutIndex: DB    0
mergeCalloutTextX: DB     0
mergeCalloutTimer: DB     0
mergeCalloutTextPointer: DW 0
speakerHalfPeriod: DB      0
speakerHalfPeriodUnits: DB 0
speakerCycles: DB          0
highScoreInsertIndex: DB 0
highScoreShiftIndex: DB  0
highScoreInitialPosition: DB 0
highScoreCopyDestination: DW 0
attractMode:    DB      0

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
scoreDrawX:     DB      0
scoreDrawY:     DB      0
scoreDrawColor: DB      0
highScoreDrawIndex: DB  0
highScoreDisplayIndex: DB 0
highScoreDisplayY: DB    0
textPointer:    DW      0
textX:          DB      0
textY:          DB      0
textColor:      DB      0
glyphPointer:   DW      0
glyphIndex:     DB      0
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
titleTwinkleTimer: DW   0
titleTwinklePhase: DB   0
titleSpritePointer: DW  0
titleSpriteX:    DB      0
titleSpriteY:    DB      0
titleSpriteWidth: DB     0
titleSpriteHeight: DB    0
titleSpriteRow:  DB      0
titleSpriteColumn: DB    0
titleSpriteColor: DB     0

        INCLUDE "title_frames.asm"
        INCLUDE "title_stars.asm"
        INCLUDE "high_score_mascot.asm"
        INCLUDE "game_over_frame.asm"
        INCLUDE "presents_frame.asm"

CodeEnd:
        SAVEBIN "build/vz200/sixies-vz200.bin", Start, CodeEnd - Start
