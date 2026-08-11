; Final-score and persistent five-entry leaderboard page.
; This region is ordinary CPU RAM outside VIC-II display memory.
* = $8200

RunTitleAttractMode:
RunTitleAttractMode_DrainKeyboard:
    jsr SCNKEY
    jsr GETIN
    bne RunTitleAttractMode_DrainKeyboard
RunTitleAttractMode_ReleaseFire:
    lda JOYSTICK2
    and #$10
    beq RunTitleAttractMode_ReleaseFire
RunTitleAttractMode_Title:
    lda #5
    jsr WaitStartupAttractSeconds
    bcs RunTitleAttractMode_Start
    jsr DrawAttractHighScorePage
    lda #5
    jsr WaitStartupAttractSeconds
    bcs RunTitleAttractMode_Start
    jsr ShowTitleScreen
    jmp RunTitleAttractMode_Title
RunTitleAttractMode_Start:
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

; Raster IRQs are not active on the startup screens, so count display frames
; by waiting for raster line 250 to leave and return.
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

DrawAttractHighScorePage:
    lda #0
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND
    jsr ClearBitmap
    jsr InitScreenColors
    lda VIC_MODE
    ora #%00010000
    sta VIC_MODE

    lda #<HighScoreHeading
    ldx #>HighScoreHeading
    jsr SetHighScoreTextSource
    lda #11
    sta highTextLength
    lda #2
    sta highTextRow
    lda #9
    sta highTextColumn
    lda #COLOR_CYAN
    sta highTextColor
    jsr DrawHighScoreText

    lda #0
    sta highEntryIndex
DrawAttractHighScorePage_Entry:
    jsr BuildHighScoreEntryLine
    lda #<HighScoreEntryLine
    ldx #>HighScoreEntryLine
    jsr SetHighScoreTextSource
    lda #14
    sta highTextLength
    ldx highEntryIndex
    lda AttractHighScoreRows,x
    sta highTextRow
    lda #6
    sta highTextColumn
    lda HighScoreColors,x
    sta highTextColor
    jsr DrawHighScoreText
    inc highEntryIndex
    lda highEntryIndex
    cmp #5
    bne DrawAttractHighScorePage_Entry

    lda #<AttractPromptText
    ldx #>AttractPromptText
    jsr SetHighScoreTextSource
    lda #16
    sta highTextLength
    lda #22
    sta highTextRow
    lda #4
    sta highTextColumn
    lda #COLOR_WHITE
    sta highTextColor
    jmp DrawHighScoreText

RunHighScorePage:
    jsr WaitHighScoreRevealDelay
    jsr ClearHighScorePanel
    jsr InstallNewTopScore
    jsr DrawHighScorePage
    lda highScoreEntering
    beq RunHighScorePage_Done
    jsr EnterHighScoreInitials
RunHighScorePage_Done:
RunEndAttractMode_HighScores:
    lda #10
    jsr WaitEndAttractSeconds
    bcs RunEndAttractMode_NewGame
    jsr ShowTitleScreen
    lda #10
    jsr WaitEndAttractSeconds
    bcs RunEndAttractMode_NewGame
    jsr ShowEndHighScorePage
    jmp RunEndAttractMode_HighScores
RunEndAttractMode_NewGame:
    lda #1
    sta endAttractNewGame
    rts

WaitEndAttractSeconds:
    sta attractSeconds
WaitEndAttractSeconds_Second:
    lda TV_STANDARD
    beq WaitEndAttractSeconds_NTSC
    lda #50
    bne WaitEndAttractSeconds_SetFrames
WaitEndAttractSeconds_NTSC:
    lda #60
WaitEndAttractSeconds_SetFrames:
    sta attractFrames
WaitEndAttractSeconds_Frame:
    jsr WaitFrame
    jsr SCNKEY
    jsr GETIN
    cmp #'N'
    beq WaitEndAttractSeconds_NewGame
    dec attractFrames
    bne WaitEndAttractSeconds_Frame
    dec attractSeconds
    bne WaitEndAttractSeconds_Second
    clc
    rts
WaitEndAttractSeconds_NewGame:
    sec
    rts

ShowEndHighScorePage:
    jsr PrepareGameOverKoala
    jsr DrawGameOver
    jsr ClearHighScorePanel
    jmp DrawHighScorePage

WaitHighScoreRevealDelay:
    lda TV_STANDARD
    beq WaitHighScoreRevealDelay_NTSC
    lda #100
    bne WaitHighScoreRevealDelay_Wait
WaitHighScoreRevealDelay_NTSC:
    lda #120
WaitHighScoreRevealDelay_Wait:
    jmp WaitAnimationFrames

ClearHighScorePanel:
    lda #2
    sta highPanelRow
ClearHighScorePanel_Row:
    lda highPanelRow
    jsr SetBitmapRowPointer
    ldy #0
    lda #0
ClearHighScorePanel_Page:
    sta (PTR_LO),y
    iny
    bne ClearHighScorePanel_Page
    inc PTR_HI
    ldy #0
ClearHighScorePanel_Tail:
    sta (PTR_LO),y
    iny
    cpy #64
    bne ClearHighScorePanel_Tail
    inc highPanelRow
    lda highPanelRow
    cmp #23
    bne ClearHighScorePanel_Row
    rts

InstallNewTopScore:
    lda #0
    sta highScoreEntering
    lda scoreHundreds
    cmp HighScoreScores
    bcc InstallNewTopScore_Done
    bne InstallNewTopScore_Qualified
    lda scoreTens
    cmp HighScoreScores + 1
    bcc InstallNewTopScore_Done
    bne InstallNewTopScore_Qualified
    lda scoreOnes
    cmp HighScoreScores + 2
    bcc InstallNewTopScore_Done
    beq InstallNewTopScore_Done
InstallNewTopScore_Qualified:
    ldx #11
InstallNewTopScore_Shift:
    lda HighScoreNames,x
    sta HighScoreNames + 3,x
    lda HighScoreScores,x
    sta HighScoreScores + 3,x
    dex
    bpl InstallNewTopScore_Shift
    lda #'A'
    sta HighScoreNames
    sta HighScoreNames + 1
    sta HighScoreNames + 2
    lda scoreHundreds
    sta HighScoreScores
    lda scoreTens
    sta HighScoreScores + 1
    lda scoreOnes
    sta HighScoreScores + 2
    lda #1
    sta highScoreEntering
    lda #0
    sta highInitialPosition
InstallNewTopScore_Done:
    rts

DrawHighScorePage:
    jsr BuildFinalScoreLine
    lda #<FinalScoreLine
    ldx #>FinalScoreLine
    jsr SetHighScoreTextSource
    lda #9
    sta highTextLength
    lda #3
    sta highTextRow
    lda #11
    sta highTextColumn
    lda #COLOR_YELLOW
    sta highTextColor
    jsr DrawHighScoreText

    lda #<HighScoreHeading
    ldx #>HighScoreHeading
    jsr SetHighScoreTextSource
    lda #11
    sta highTextLength
    lda #6
    sta highTextRow
    lda #9
    sta highTextColumn
    lda #COLOR_CYAN
    sta highTextColor
    jsr DrawHighScoreText

    lda #0
    sta highEntryIndex
DrawHighScorePage_Entry:
    jsr BuildHighScoreEntryLine
    lda #<HighScoreEntryLine
    ldx #>HighScoreEntryLine
    jsr SetHighScoreTextSource
    lda #14
    sta highTextLength
    ldx highEntryIndex
    lda HighScoreRows,x
    sta highTextRow
    lda #6
    sta highTextColumn
    lda HighScoreColors,x
    sta highTextColor
    jsr DrawHighScoreText
    inc highEntryIndex
    lda highEntryIndex
    cmp #5
    bne DrawHighScorePage_Entry

    lda highScoreEntering
    beq DrawHighScorePage_Done
    lda #<EnterInitialsText
    ldx #>EnterInitialsText
    jsr SetHighScoreTextSource
    lda #14
    sta highTextLength
    lda #19
    sta highTextRow
    lda #6
    sta highTextColumn
    lda #COLOR_WHITE
    sta highTextColor
    jsr DrawHighScoreText
    jsr DrawEnteredInitials
DrawHighScorePage_Done:
    rts

BuildFinalScoreLine:
    lda scoreHundreds
    clc
    adc #$30
    sta FinalScoreLine + 6
    lda scoreTens
    clc
    adc #$30
    sta FinalScoreLine + 7
    lda scoreOnes
    clc
    adc #$30
    sta FinalScoreLine + 8
    rts

BuildHighScoreEntryLine:
    lda highEntryIndex
    clc
    adc #$31
    sta HighScoreEntryLine
    ldx highEntryIndex
    lda HighScoreOffsets,x
    sta highScoreOffset
    tax
    ldy #0
BuildHighScoreEntryLine_Name:
    lda HighScoreNames,x
    sta HighScoreEntryLine + 3,y
    inx
    iny
    cpy #3
    bne BuildHighScoreEntryLine_Name
    ldx highScoreOffset
    ldy #0
BuildHighScoreEntryLine_Score:
    lda HighScoreScores,x
    clc
    adc #$30
    sta HighScoreEntryLine + 11,y
    inx
    iny
    cpy #3
    bne BuildHighScoreEntryLine_Score
    rts

EnterHighScoreInitials:
EnterHighScoreInitials_Drain:
    jsr SCNKEY
    jsr GETIN
    bne EnterHighScoreInitials_Drain
EnterHighScoreInitials_Wait:
    jsr WaitFrame
    jsr SCNKEY
    jsr GETIN
    beq EnterHighScoreInitials_Wait
    cmp #'A'
    bcc EnterHighScoreInitials_Wait
    cmp #$5b
    bcs EnterHighScoreInitials_Wait
    ldx highInitialPosition
    sta HighScoreNames,x
    inc highInitialPosition
    jsr DrawEnteredInitials
    lda highInitialPosition
    cmp #3
    bne EnterHighScoreInitials_Wait
    jsr DrawHighScorePage
    lda #0
    sta highScoreEntering
    rts

DrawEnteredInitials:
    lda #<HighScoreNames
    ldx #>HighScoreNames
    jsr SetHighScoreTextSource
    lda #3
    sta highTextLength
    lda #21
    sta highTextRow
    lda #17
    sta highTextColumn
    lda #COLOR_YELLOW
    sta highTextColor
    jmp DrawHighScoreText

SetHighScoreTextSource:
    sta highTextSourceLo
    stx highTextSourceHi
    rts

DrawHighScoreText:
    lda highTextSourceLo
    sta DrawHighScoreText_Read + 1
    lda highTextSourceHi
    sta DrawHighScoreText_Read + 2

    ; Color RAM supplies multicolor bitmap pixel value 3.
    ldx highTextRow
    lda HighScoreColorRowLo,x
    sta PTR_LO
    lda HighScoreColorRowHi,x
    sta PTR_HI
    ldy highTextColumn
    lda highTextLength
    asl
    sta highTextCellsRemaining
    lda highTextColor
DrawHighScoreText_Color:
    sta (PTR_LO),y
    iny
    dec highTextCellsRemaining
    bne DrawHighScoreText_Color

    lda highTextRow
    jsr SetBitmapRowPointer
    lda highTextColumn
    jsr AddColumnOffset
    lda #0
    sta highTextIndex
DrawHighScoreText_Character:
    ldx highTextIndex
DrawHighScoreText_Read:
    lda $ffff,x
    sta highCharacter
    jsr SelectHighScoreGlyph
    lda #0
    sta highGlyphRow
DrawHighScoreText_Row:
    ldy highGlyphRow
    lda (SOURCE_LO),y
    sta highGlyphBits
    lsr
    lsr
    lsr
    lsr
    tax
    lda GameOverMulticolorExpand,x
    ldy highGlyphRow
    sta (PTR_LO),y
    lda highGlyphBits
    and #$0f
    tax
    lda GameOverMulticolorExpand,x
    sta highGlyphBits
    ldy highGlyphRow
    tya
    clc
    adc #8
    tay
    lda highGlyphBits
    sta (PTR_LO),y
    inc highGlyphRow
    lda highGlyphRow
    cmp #8
    bne DrawHighScoreText_Row
    lda PTR_LO
    clc
    adc #16
    sta PTR_LO
    bcc DrawHighScoreText_Next
    inc PTR_HI
DrawHighScoreText_Next:
    inc highTextIndex
    lda highTextIndex
    cmp highTextLength
    bne DrawHighScoreText_Character
    rts

SelectHighScoreGlyph:
    lda highCharacter
    cmp #'.'
    bne SelectHighScoreGlyph_Charset
    lda #<HighScoreDotGlyph
    sta SOURCE_LO
    lda #>HighScoreDotGlyph
    sta SOURCE_HI
    rts
SelectHighScoreGlyph_Charset:
    sta highGlyphOffset
    lda #0
    sta highGlyphPage
    asl highGlyphOffset
    rol highGlyphPage
    asl highGlyphOffset
    rol highGlyphPage
    asl highGlyphOffset
    rol highGlyphPage
    lda highGlyphOffset
    clc
    adc #<HighScoreCharset
    sta SOURCE_LO
    lda highGlyphPage
    adc #>HighScoreCharset
    sta SOURCE_HI
    rts

HighScoreHeading:
!byte 'H','I','G','H',' ','S','C','O','R','E','S'
EnterInitialsText:
!byte 'E','N','T','E','R',' ','I','N','I','T','I','A','L','S'
FinalScoreLine:
!byte 'S','C','O','R','E',' ', '0','0','0'
HighScoreEntryLine:
!byte '1','.',' ','D','O','M','.','.','.','.','.', '2','2','0'

HighScoreNames:
!byte 'D','O','M', 'S','H','A', 'A','C','E', 'K','I','M', 'M','A','X'
HighScoreScores:
!byte 2,2,0, 1,6,3, 1,2,0, 0,8,0, 0,4,0
HighScoreOffsets:
!byte 0,3,6,9,12
HighScoreRows:
!byte 8,10,12,14,16
AttractHighScoreRows:
!byte 5,8,11,14,17
HighScoreColors:
!byte COLOR_YELLOW,COLOR_WHITE,COLOR_LTBLUE,COLOR_GREEN,COLOR_PURPLE
HighScoreDotGlyph:
!byte $00,$00,$00,$00,$00,$00,$18,$18
AttractPromptText:
!byte 'P','R','E','S','S',' ','F','I','R','E',' ','S','T','A','R','T'

highScoreEntering:   !byte 0
highInitialPosition: !byte 0
highEntryIndex:      !byte 0
highScoreOffset:     !byte 0
highTextSourceLo:    !byte 0
highTextSourceHi:    !byte 0
highTextLength:      !byte 0
highTextRow:         !byte 0
highTextColumn:      !byte 0
highTextColor:       !byte 0
highTextCellsRemaining: !byte 0
highTextIndex:       !byte 0
highCharacter:       !byte 0
highGlyphRow:        !byte 0
highGlyphBits:       !byte 0
highGlyphOffset:     !byte 0
highGlyphPage:       !byte 0
highPanelRow:        !byte 0
endAttractNewGame:   !byte 0
attractSeconds:      !byte 0
attractFrames:       !byte 0

HighScoreColorRowLo:
!for row, 0, 24 { !byte <(COLOR_RAM + (row * 40)) }
HighScoreColorRowHi:
!for row, 0, 24 { !byte >(COLOR_RAM + (row * 40)) }

; ASCII-indexed Sixies glyphs generated from the supplied font sheet.
HighScoreCharset:
!bin "src/assets/font/SixiesFont_charset.bin"
