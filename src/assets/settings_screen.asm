; Modal instructions page. The board remains in RAM and is redrawn on exit.
* = $9800

ReadAction:
    lda #ACTION_NONE
    sta action

    jsr SCNKEY
    lda KEY_CURRENT
    cmp #$3d
    bne ReadAction_ReadKey
    jmp ReadAction_Settings
ReadAction_ReadKey:
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
    bne ReadAction_Store
ReadAction_Settings:
    lda #ACTION_SETTINGS
ReadAction_Store:
    sta action
    rts

ShowSettingsScreen:
    lda highlightedIndex
    cmp #$ff
    beq ShowSettingsScreen_HideBoard
    jsr ClearCursorHighlights
    lda #$ff
    sta highlightedIndex
    sta highlightedSecondIndex
ShowSettingsScreen_HideBoard:
    lda #1
    sta ghostSuppressed
    sta gameOverBlindActive
    jsr MarkDisplayDirty
    lda #5
    sta blindRow
    lda #0
    sta uiEnableMask
    jsr WaitFrame

    sei
    lda #0
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND
    jsr ClearBitmap
    jsr InitScreenColors
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    lda #0
    sta settingsPage
    lda audioMode
    beq ShowSettingsScreen_DefaultAudioSelection
    sec
    sbc #AUDIO_MUSIC_ONLY
ShowSettingsScreen_DefaultAudioSelection:
    sta settingsOptionSelection
    jsr DrawSettingsText
    cli

    jsr WaitForSettingsClose

    sei
    lda #0
    sta settingsFocused
    jsr RestoreGameScreen
    jsr UpdateScoreDisplay
    lda #0
    sta ghostSuppressed
    sta joystickLatch
    lda #1
    sta boardDirty
    jsr UpdatePlacement
    jsr BuildDisplayBoard
    jsr UpdateCursorHighlight
    cli
    rts

DrawSettingsText:
    jsr DrawSettingsArtwork
    ldx settingsPage
    lda SettingsPageStarts,x
    sta settingsLineIndex
    clc
    adc SettingsPageCounts,x
    sta settingsLineEnd
DrawSettingsText_Line:
    ldx settingsLineIndex
    lda SettingsLineLo,x
    sta highTextSourceLo
    lda SettingsLineHi,x
    sta highTextSourceHi
    lda SettingsLineLength,x
    sta highTextLength
    lda SettingsLineRow,x
    sta highTextRow
    lda SettingsLineColumn,x
    sta highTextColumn
    lda settingsLineIndex
    ldx settingsPage
    cmp SettingsPageStarts,x
    beq DrawSettingsText_Heading
    cpx #0
    beq DrawSettingsText_MenuColor
    cpx #3
    beq DrawSettingsText_OptionsColor
DrawSettingsText_DefaultColor:
    lda #COLOR_LTGRAY
    bne DrawSettingsText_Body
DrawSettingsText_OptionsColor:
    lda settingsLineIndex
    cmp #23
    bcc DrawSettingsText_DefaultColor
    cmp #25
    bcs DrawSettingsText_DefaultColor
    sec
    sbc #23
    cmp settingsOptionSelection
    beq DrawSettingsText_Selected
    lda #COLOR_DKGRAY
    bne DrawSettingsText_Body
DrawSettingsText_MenuColor:
    lda settingsLineIndex
    cmp #1
    bcc DrawSettingsText_DefaultColor
    cmp #4
    bcs DrawSettingsText_DefaultColor
    sec
    sbc #1
    cmp settingsMenuSelection
    beq DrawSettingsText_Selected
    lda #COLOR_DKGRAY
    bne DrawSettingsText_Body
DrawSettingsText_Selected:
    lda #COLOR_LTGRAY
DrawSettingsText_Body:
    sta highTextColor
    jsr DrawSixiesHiresText
    jmp DrawSettingsText_Next
DrawSettingsText_Heading:
    lda #COLOR_WHITE
    sta highTextColor
    jsr DrawSixiesFont16Text
DrawSettingsText_Next:
    inc settingsLineIndex
    lda settingsLineIndex
    cmp settingsLineEnd
    beq DrawSettingsText_Done
    jmp DrawSettingsText_Line
DrawSettingsText_Done:
    rts

SettingsLineLo:
    !byte <SettingsTextTitle, <SettingsTextMenuControls, <SettingsTextMenuHow
    !byte <SettingsTextMenuOptions, <SettingsTextMenuHelp, <SettingsTextTabClose
    !byte <SettingsTextControls, <SettingsTextMove, <SettingsTextRotate
    !byte <SettingsTextPlaceKey, <SettingsTextBottom, <SettingsTextNewGame
    !byte <SettingsTextTabOpenClose, <SettingsTextMenuReturn
    !byte <SettingsTextHow, <SettingsTextPlace, <SettingsTextMatch
    !byte <SettingsTextNextValue, <SettingsTextFives, <SettingsTextSixes
    !byte <SettingsTextChain, <SettingsTextMenuReturn
    !byte <SettingsTextOptions, <SettingsTextMusicOnly, <SettingsTextSfxOnly
    !byte <SettingsTextOptionHelp, <SettingsTextOptionClose
SettingsLineHi:
    !byte >SettingsTextTitle, >SettingsTextMenuControls, >SettingsTextMenuHow
    !byte >SettingsTextMenuOptions, >SettingsTextMenuHelp, >SettingsTextTabClose
    !byte >SettingsTextControls, >SettingsTextMove, >SettingsTextRotate
    !byte >SettingsTextPlaceKey, >SettingsTextBottom, >SettingsTextNewGame
    !byte >SettingsTextTabOpenClose, >SettingsTextMenuReturn
    !byte >SettingsTextHow, >SettingsTextPlace, >SettingsTextMatch
    !byte >SettingsTextNextValue, >SettingsTextFives, >SettingsTextSixes
    !byte >SettingsTextChain, >SettingsTextMenuReturn
    !byte >SettingsTextOptions, >SettingsTextMusicOnly, >SettingsTextSfxOnly
    !byte >SettingsTextOptionHelp, >SettingsTextOptionClose
SettingsLineLength:
    !byte 8,11,14,10,20,8
    !byte 8,21,19,20,22,17,18,17
    !byte 11,21,21,20,16,17,23,17
    !byte 7,13,16,19,16
SettingsLineRow:
    !byte 1,9,12,15,20,22
    !byte 1,9,11,13,15,17,19,22
    !byte 1,9,11,13,15,17,19,22
    !byte 1,9,12,20,22
SettingsLineColumn:
    !byte 11,12,12,12,10,16
    !byte 11,9,10,10,9,11,10,11
    !byte 9,9,9,10,12,11,8,11
    !byte 11,13,12,10,11

SettingsPageStarts: !byte 0,6,14,22
SettingsPageCounts: !byte 6,8,8,5

SettingsTextTitle:         !text "SETTINGS"
SettingsTextMenuControls:  !text "1. CONTROLS"
SettingsTextMenuHow:       !text "2. HOW TO PLAY"
SettingsTextMenuOptions:   !text "3. OPTIONS"
SettingsTextMenuHelp:      !text "W/S SELECT FIRE OPEN"
SettingsTextTabClose:      !text "X CLOSES"
SettingsTextControls:      !text "CONTROLS"
SettingsTextMove:          !text "WASD OR JOYSTICK MOVE"
SettingsTextRotate:        !text "R OR Q ROTATES PAIR"
SettingsTextPlaceKey:      !text "SPACE OR FIRE PLACES"
SettingsTextBottom:        !text "DOWN OPENS BOTTOM MENU"
SettingsTextNewGame:       !text "N STARTS NEW GAME"
SettingsTextTabOpenClose:  !text "TAB OPENS SETTINGS"
SettingsTextMenuReturn:    !text "M RETURNS TO MENU"
SettingsTextHow:           !text "HOW TO PLAY"
SettingsTextPlace:         !text "PLACE ONE OR TWO DICE"
SettingsTextMatch:         !text "MATCH 3 TOUCHING DICE"
SettingsTextNextValue:     !text "THREE SAME MAKE NEXT"
SettingsTextFives:         !text "FIVES MAKE SIXES"
SettingsTextSixes:         !text "THREE SIXES CLEAR"
SettingsTextChain:         !text "CHAIN MERGES SCORE MORE"
SettingsTextOptions:       !text "OPTIONS"
SettingsTextMusicOnly:     !text "1. MUSIC ONLY"
SettingsTextSfxOnly:       !text "2. SOUND FX ONLY"
SettingsTextOptionHelp:    !text "W/S SELECT FIRE SET"
SettingsTextOptionClose:   !text "M MENU  X CLOSES"

settingsFocused: !byte 0
newGameFocused:  !byte 0
settingsLineIndex: !byte 0
settingsLineEnd: !byte 0
settingsPage: !byte 0
settingsMenuSelection: !byte 0
settingsOptionSelection: !byte 0

RunTitleAttractMode:
RunTitleAttractMode_DrainKeyboard:
    jsr SCNKEY
    jsr GETIN
    bne RunTitleAttractMode_DrainKeyboard
RunTitleAttractMode_ReleaseFire:
    lda JOYSTICK2
    and #$10
    beq RunTitleAttractMode_ReleaseFire
    jsr InitTitleMusic
RunTitleAttractMode_Title:
    lda #5
    jsr WaitStartupAttractSeconds
    bcs RunTitleAttractMode_Start
    jsr DrawAttractHighScorePage
    lda #5
    jsr WaitStartupAttractSeconds
    bcs RunTitleAttractMode_Start
    jsr DrawStartupCreditsPage
    lda #11
    jsr WaitStartupAttractSeconds
    bcs RunTitleAttractMode_Start
    lda #0
    sta creditsScreenActive
    jsr ShowTitleScreen
    jmp RunTitleAttractMode_Title
RunTitleAttractMode_Start:
    lda #0
    sta creditsScreenActive
    sta titleScreenActive
    jsr StopTitleMusic
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    rts

WaitStartupAttractSeconds:
    sta attractSeconds
WaitStartupAttractSeconds_Second:
    lda TV_STANDARD
    beq WaitStartupAttractSeconds_NTSC
    lda #50
    bne WaitStartupAttractSeconds_SetFrames
WaitStartupAttractSeconds_NTSC:
    lda #60
WaitStartupAttractSeconds_SetFrames:
    sta attractFrames
WaitStartupAttractSeconds_Frame:
    jsr PollTitleStartInput
    bcs WaitStartupAttractSeconds_Pressed
    jsr WaitStartupRasterFrame
    jsr UpdateCreditsFade
    dec attractFrames
    bne WaitStartupAttractSeconds_Frame
    dec attractSeconds
    bne WaitStartupAttractSeconds_Second
    clc
    rts
WaitStartupAttractSeconds_Pressed:
    sec
    rts

PollTitleStartInput:
    jsr SCNKEY
    jsr GETIN
    cmp #' '
    beq PollTitleStartInput_Pressed
    cmp #13
    beq PollTitleStartInput_Pressed
    lda JOYSTICK2
    and #$10
    beq PollTitleStartInput_Pressed
    clc
    rts
PollTitleStartInput_Pressed:
    sec
    rts

; Count display frames by waiting for raster line 250 to leave and return.
WaitStartupRasterFrame:
    lda RASTER_LINE
    cmp #250
    bne WaitStartupRasterFrame_Arrive
WaitStartupRasterFrame_Leave:
    lda RASTER_LINE
    cmp #250
    beq WaitStartupRasterFrame_Leave
WaitStartupRasterFrame_Arrive:
    lda RASTER_LINE
    cmp #250
    bne WaitStartupRasterFrame_Arrive
    rts

DrawStartupCreditsPage:
    jsr DrawCreditsPage
    lda #<CreditsStartPrompt
    ldx #>CreditsStartPrompt
    jsr SetHighScoreTextSource
    jmp DrawCreditsPrompt

DrawEndCreditsPage:
    jsr DrawCreditsPage
    lda #<CreditsNewGamePrompt
    ldx #>CreditsNewGamePrompt
    jsr SetHighScoreTextSource
DrawCreditsPrompt:
    lda #16
    sta highTextLength
    lda #24
    sta highTextRow
    lda #12
    sta highTextColumn
    lda #COLOR_WHITE
    sta highTextColor
    jmp DrawSixiesHiresText

DrawCreditsPage:
    lda #0
    sta titleScreenActive
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    jsr ClearBitmap
    jsr InitScreenColors
    jsr DrawCreditsLogo
    jsr DrawCreditsMascot

    lda #0
    sta creditsFadeCard
    sta creditsFadePhase
    sta creditsFadeDelay
    sta creditsFadeHold
    lda #1
    sta creditsScreenActive
    jmp DrawCreditsFadeCard

UpdateCreditsFade:
    lda creditsScreenActive
    bne UpdateCreditsFade_Active
    rts
UpdateCreditsFade_Active:
    lda creditsFadeHold
    beq UpdateCreditsFade_Tick
    dec creditsFadeHold
    rts
UpdateCreditsFade_Tick:
    inc creditsFadeDelay
    lda creditsFadeDelay
    cmp #4
    bcs UpdateCreditsFade_Advance
    rts
UpdateCreditsFade_Advance:
    lda #0
    sta creditsFadeDelay
    inc creditsFadePhase
    lda creditsFadePhase
    cmp #CREDITS_HOLD_PHASE
    bne UpdateCreditsFade_CheckEnd
    jsr StartCreditsFadeHold
    lda creditsFadePhase
UpdateCreditsFade_CheckEnd:
    cmp #CREDITS_FADE_PHASES
    bcc DrawCreditsFadeCard

    jsr ClearCreditsFadePanel
    lda #0
    sta creditsFadePhase
    inc creditsFadeCard
    lda creditsFadeCard
    cmp #CREDITS_CARD_COUNT
    bne DrawCreditsFadeCard
    lda #0
    sta creditsFadeCard

DrawCreditsFadeCard:
    ldx creditsFadePhase
    lda CreditsFadeColors,x
    sta highTextColor
    ldx creditsFadeCard
    lda CreditsCardStarts,x
    sta creditsLineIndex
    clc
    adc CreditsCardCounts,x
    sta creditsLineEnd
DrawCreditsFadeCard_Line:
    ldx creditsLineIndex
    lda creditsFadePhase
    cmp #CREDITS_HOLD_PHASE
    bne DrawCreditsFadeCard_LineColorReady
    lda CreditsLineHoldColors,x
    sta highTextColor
DrawCreditsFadeCard_LineColorReady:
    lda CreditsLineLo,x
    sta highTextSourceLo
    lda CreditsLineHi,x
    sta highTextSourceHi
    lda CreditsLineLength,x
    sta highTextLength
    lda CreditsLineRow,x
    sta highTextRow
    lda CreditsLineColumn,x
    sta highTextColumn
    jsr DrawCreditsFont16Text
    inc creditsLineIndex
    lda creditsLineIndex
    cmp creditsLineEnd
    bne DrawCreditsFadeCard_Line
UpdateCreditsFade_Done:
    rts

StartCreditsFadeHold:
    lda TV_STANDARD
    beq StartCreditsFadeHold_NTSC
    lda #100
    bne StartCreditsFadeHold_Store
StartCreditsFadeHold_NTSC:
    lda #120
StartCreditsFadeHold_Store:
    sta creditsFadeHold
    rts

ClearCreditsFadePanel:
    lda #6
    sta workRow
ClearCreditsFadePanel_Row:
    lda workRow
    jsr SetBitmapRowPointer
    lda #14
    jsr AddColumnOffset
    ldy #0
    lda #0
ClearCreditsFadePanel_Byte:
    sta (PTR_LO),y
    iny
    cpy #208
    bne ClearCreditsFadePanel_Byte
    inc workRow
    lda workRow
    cmp #23
    bne ClearCreditsFadePanel_Row
    rts

DrawCreditsLogo:
    lda #<CreditsLogoBitmapData
    sta SOURCE_LO
    lda #>CreditsLogoBitmapData
    sta SOURCE_HI
    lda #0
    sta workRow
DrawCreditsLogo_BitmapRow:
    lda workRow
    jsr SetBitmapRowPointer
    lda #12
    jsr AddColumnOffset
    ldy #0
DrawCreditsLogo_BitmapByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #128
    bne DrawCreditsLogo_BitmapByte
    lda SOURCE_LO
    clc
    adc #128
    sta SOURCE_LO
    bcc DrawCreditsLogo_BitmapSourceReady
    inc SOURCE_HI
DrawCreditsLogo_BitmapSourceReady:
    inc workRow
    lda workRow
    cmp #5
    bne DrawCreditsLogo_BitmapRow

    lda #<CreditsLogoScreenData
    sta SOURCE_LO
    lda #>CreditsLogoScreenData
    sta SOURCE_HI
    lda #0
    sta workRow
DrawCreditsLogo_ScreenRow:
    lda workRow
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc #12
    sta PTR_LO
    bcc DrawCreditsLogo_ScreenReady
    inc PTR_HI
DrawCreditsLogo_ScreenReady:
    ldy #0
DrawCreditsLogo_ScreenByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #16
    bne DrawCreditsLogo_ScreenByte
    lda SOURCE_LO
    clc
    adc #16
    sta SOURCE_LO
    bcc DrawCreditsLogo_ScreenSourceReady
    inc SOURCE_HI
DrawCreditsLogo_ScreenSourceReady:
    inc workRow
    lda workRow
    cmp #5
    bne DrawCreditsLogo_ScreenRow
    rts

DrawCreditsMascot:
    lda #<CreditsMascotBitmapData
    sta SOURCE_LO
    lda #>CreditsMascotBitmapData
    sta SOURCE_HI
    lda #6
    sta workRow
DrawCreditsMascot_BitmapRow:
    lda workRow
    jsr SetBitmapRowPointer
    lda #1
    jsr AddColumnOffset
    ldy #0
DrawCreditsMascot_BitmapByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #96
    bne DrawCreditsMascot_BitmapByte
    lda SOURCE_LO
    clc
    adc #96
    sta SOURCE_LO
    bcc DrawCreditsMascot_BitmapSourceReady
    inc SOURCE_HI
DrawCreditsMascot_BitmapSourceReady:
    inc workRow
    lda workRow
    cmp #22
    bne DrawCreditsMascot_BitmapRow

    lda #<CreditsMascotScreenData
    sta SOURCE_LO
    lda #>CreditsMascotScreenData
    sta SOURCE_HI
    lda #6
    sta workRow
DrawCreditsMascot_ScreenRow:
    lda workRow
    jsr SetScreenRowPointer
    inc PTR_LO
    bne DrawCreditsMascot_ScreenReady
    inc PTR_HI
DrawCreditsMascot_ScreenReady:
    ldy #0
DrawCreditsMascot_ScreenByte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #12
    bne DrawCreditsMascot_ScreenByte
    lda SOURCE_LO
    clc
    adc #12
    sta SOURCE_LO
    bcc DrawCreditsMascot_ScreenSourceReady
    inc SOURCE_HI
DrawCreditsMascot_ScreenSourceReady:
    inc workRow
    lda workRow
    cmp #22
    bne DrawCreditsMascot_ScreenRow
    rts

DrawSixiesHiresText:
    lda #<HighScoreCharset
    sta highTextCharsetLo
    lda #>HighScoreCharset
    sta highTextCharsetHi
DrawHiresText:
    lda highTextSourceLo
    sta DrawSixiesHiresText_Read + 1
    lda highTextSourceHi
    sta DrawSixiesHiresText_Read + 2

    lda highTextRow
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc highTextColumn
    sta PTR_LO
    bcc DrawSixiesHiresText_ColorReady
    inc PTR_HI
DrawSixiesHiresText_ColorReady:
    lda highTextColor
    asl
    asl
    asl
    asl
    ldy #0
DrawSixiesHiresText_Color:
    sta (PTR_LO),y
    iny
    cpy highTextLength
    bne DrawSixiesHiresText_Color

    lda highTextRow
    jsr SetBitmapRowPointer
    lda highTextColumn
    jsr AddColumnOffset
    lda #0
    sta highTextIndex
DrawSixiesHiresText_Character:
    ldx highTextIndex
DrawSixiesHiresText_Read:
    lda $ffff,x
    sta highCharacter
    jsr SelectHighScoreGlyph
    ldy #0
DrawSixiesHiresText_Row:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #8
    bne DrawSixiesHiresText_Row
    lda PTR_LO
    clc
    adc #8
    sta PTR_LO
    bcc DrawSixiesHiresText_Next
    inc PTR_HI
DrawSixiesHiresText_Next:
    inc highTextIndex
    lda highTextIndex
    cmp highTextLength
    bne DrawSixiesHiresText_Character
    rts

CREDITS_CARD_COUNT = 3
CREDITS_FADE_PHASES = 7
CREDITS_HOLD_PHASE = 3

CreditsLineLo:
    !byte <CreditsTextDesigned, <CreditsTextCharset
    !byte <CreditsTextBitmapsBy, <CreditsTextDSkilton
    !byte <CreditsTextMusic, <CreditsTextTrack
    !byte <CreditsTextComposerFirst, <CreditsTextComposerLast, <CreditsTextSonix
    !byte <CreditsTextStudio313, <CreditsTextGames, <CreditsTextYear
CreditsLineHi:
    !byte >CreditsTextDesigned, >CreditsTextCharset
    !byte >CreditsTextBitmapsBy, >CreditsTextDSkilton
    !byte >CreditsTextMusic, >CreditsTextTrack
    !byte >CreditsTextComposerFirst, >CreditsTextComposerLast, >CreditsTextSonix
    !byte >CreditsTextStudio313, >CreditsTextGames, >CreditsTextYear
CreditsLineLength:
    !byte 8,7,10,8,8,11,10,11,7,10,5,8
CreditsLineRow:
    !byte 7,10,13,16,6,9,12,15,18,8,11,14
CreditsLineColumn:
    !byte 19,20,17,19,19,15,16,15,20,17,22,19
CreditsCardStarts:
    !byte 0,4,9
CreditsCardCounts:
    !byte 4,5,3
CreditsFadeColors:
    !byte COLOR_BLACK,COLOR_DKGRAY,COLOR_LTGRAY,COLOR_WHITE
    !byte COLOR_LTGRAY,COLOR_DKGRAY,COLOR_BLACK

CreditsTextDesigned:   !text "DESIGNED"
CreditsTextCharset:    !text "CHARSET"
CreditsTextBitmapsBy:  !text "BITMAPS BY"
CreditsTextDSkilton:   !text "DSKILTON"
CreditsTextTrack:      !text "ETERNITY #1"
CreditsTextComposerFirst: !text "PRZEMYSLAW"
CreditsTextComposerLast: !text "LEWANDOWSKI"
CreditsTextSonix:      !text "(SONIX)"
CreditsTextStudio313:  !text "STUDIO 313"
CreditsTextGames:      !text "GAMES"
CreditsTextYear:       !text "(C) 2026"
CreditsStartPrompt:    !text "PRESS FIRE START"
CreditsNewGamePrompt:  !text "PRESS N NEW GAME"

creditsLineIndex: !byte 0
creditsScreenActive: !byte 0
creditsFadeCard: !byte 0
creditsFadePhase: !byte 0
creditsFadeDelay: !byte 0
creditsFadeHold: !byte 0
