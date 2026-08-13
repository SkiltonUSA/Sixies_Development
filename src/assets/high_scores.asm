; Final-score and persistent five-entry leaderboard page.
; This region is ordinary CPU RAM outside VIC-II display memory.
* = $8200

DrawAttractHighScorePage:
    jsr PrepareHighScoreHiresPage
    jmp DrawAttractHighScorePage_Content

PrepareHighScoreHiresPage:
    lda #0
    sta titleScreenActive
    sta SPRITE_ENABLE
    sta BORDER
    sta BACKGROUND
    lda #1
    sta gameOverBlindActive
    jsr ClearBitmap
    jsr InitScreenColors
    lda VIC_MODE
    and #%11101111
    sta VIC_MODE
    rts

DrawAttractHighScorePage_Content:
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
    jsr DrawSixiesFont16Text

    lda #0
    sta highEntryIndex
DrawAttractHighScorePage_Entry:
    jsr BuildHighScoreEntryLine
    lda #<HighScoreEntryLine
    ldx #>HighScoreEntryLine
    jsr SetHighScoreTextSource
    lda #15
    sta highTextLength
    ldx highEntryIndex
    lda AttractHighScoreRows,x
    sta highTextRow
    lda #5
    sta highTextColumn
    lda HighScoreColors,x
    sta highTextColor
    jsr DrawSixiesFont16Text
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
    jmp DrawSixiesFont16Text

RunHighScorePage:
    jsr WaitHighScoreRevealDelay
    jsr PrepareHighScoreHiresPage
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
    jsr DrawEndCreditsPage
    lda #11
    jsr WaitEndAttractSeconds
    bcs RunEndAttractMode_NewGame
    lda #0
    sta creditsScreenActive
    jsr ShowTitleScreen
    lda #10
    jsr WaitEndAttractSeconds
    bcs RunEndAttractMode_NewGame
    jsr ShowEndHighScorePage
    jmp RunEndAttractMode_HighScores
RunEndAttractMode_NewGame:
    lda #0
    sta creditsScreenActive
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
    jsr PrepareHighScoreHiresPage
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
    lda scoreThousands
    cmp HighScoreScores
    bcc InstallNewTopScore_Done
    bne InstallNewTopScore_Qualified
    lda scoreHundreds
    cmp HighScoreScores + 1
    bcc InstallNewTopScore_Done
    bne InstallNewTopScore_Qualified
    lda scoreTens
    cmp HighScoreScores + 2
    bcc InstallNewTopScore_Done
    bne InstallNewTopScore_Qualified
    lda scoreOnes
    cmp HighScoreScores + 3
    bcc InstallNewTopScore_Done
    beq InstallNewTopScore_Done
InstallNewTopScore_Qualified:
    ldx #11
InstallNewTopScore_ShiftNames:
    lda HighScoreNames,x
    sta HighScoreNames + 3,x
    dex
    bpl InstallNewTopScore_ShiftNames
    ldx #15
InstallNewTopScore_ShiftScores:
    lda HighScoreScores,x
    sta HighScoreScores + 4,x
    dex
    bpl InstallNewTopScore_ShiftScores
    lda #'A'
    sta HighScoreNames
    sta HighScoreNames + 1
    sta HighScoreNames + 2
    lda scoreThousands
    sta HighScoreScores
    lda scoreHundreds
    sta HighScoreScores + 1
    lda scoreTens
    sta HighScoreScores + 2
    lda scoreOnes
    sta HighScoreScores + 3
    lda #1
    sta highScoreEntering
    lda #0
    sta highInitialPosition
    lda #$ff
    sta highScoreFlashColor
InstallNewTopScore_Done:
    rts

DrawHighScorePage:
    jsr BuildFinalScoreLine
    lda #<FinalScoreLine
    ldx #>FinalScoreLine
    jsr SetHighScoreTextSource
    lda #10
    sta highTextLength
    lda #3
    sta highTextRow
    lda #10
    sta highTextColumn
    lda #COLOR_YELLOW
    sta highTextColor
    jsr DrawSixiesFont16Text

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
    jsr DrawSixiesFont16Text

    lda #0
    sta highEntryIndex
DrawHighScorePage_Entry:
    jsr BuildHighScoreEntryLine
    lda #<HighScoreEntryLine
    ldx #>HighScoreEntryLine
    jsr SetHighScoreTextSource
    lda #15
    sta highTextLength
    ldx highEntryIndex
    lda HighScoreRows,x
    sta highTextRow
    lda #5
    sta highTextColumn
    lda HighScoreColors,x
    sta highTextColor
    jsr DrawSixiesFont16Text
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
    jsr DrawSixiesFont16Text
    jsr DrawEnteredInitials
DrawHighScorePage_Done:
    rts

BuildFinalScoreLine:
    lda scoreThousands
    beq BuildFinalScoreLine_NoThousands
    clc
    adc #$30
    sta FinalScoreLine + 6
    bne BuildFinalScoreLine_Hundreds
BuildFinalScoreLine_NoThousands:
    lda #' '
    sta FinalScoreLine + 6
BuildFinalScoreLine_Hundreds:
    lda scoreHundreds
    clc
    adc #$30
    sta FinalScoreLine + 7
    lda scoreTens
    clc
    adc #$30
    sta FinalScoreLine + 8
    lda scoreOnes
    clc
    adc #$30
    sta FinalScoreLine + 9
    rts

BuildHighScoreEntryLine:
    lda highEntryIndex
    clc
    adc #$31
    sta HighScoreEntryLine
    ldx highEntryIndex
    lda HighScoreNameOffsets,x
    tax
    ldy #0
BuildHighScoreEntryLine_Name:
    lda HighScoreNames,x
    sta HighScoreEntryLine + 3,y
    inx
    iny
    cpy #3
    bne BuildHighScoreEntryLine_Name
    ldx highEntryIndex
    lda HighScoreScoreOffsets,x
    sta highScoreOffset
    tax
    ldy #0
BuildHighScoreEntryLine_Score:
    lda HighScoreScores,x
    clc
    adc #$30
    cpy #0
    bne BuildHighScoreEntryLine_StoreScore
    cmp #'0'
    bne BuildHighScoreEntryLine_StoreScore
    lda #' '
BuildHighScoreEntryLine_StoreScore:
    sta HighScoreEntryLine + 11,y
    inx
    iny
    cpy #4
    bne BuildHighScoreEntryLine_Score
    rts

EnterHighScoreInitials:
EnterHighScoreInitials_Drain:
    jsr SCNKEY
    jsr GETIN
    bne EnterHighScoreInitials_Drain
EnterHighScoreInitials_Wait:
    jsr WaitFrame
    jsr UpdateHighScoreEntryFlash
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
    jmp DrawSixiesFont16Text

SetHighScoreTextSource:
    sta highTextSourceLo
    stx highTextSourceHi
    rts

DrawHighScoreText:
    jmp DrawSixiesMulticolorText

DrawSixiesMulticolorText:
    lda #<HighScoreCharset
    sta highTextCharsetLo
    lda #>HighScoreCharset
    sta highTextCharsetHi

DrawBitmapText:
    lda highTextSourceLo
    sta DrawBitmapText_Read + 1
    lda highTextSourceHi
    sta DrawBitmapText_Read + 2

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
DrawBitmapText_Color:
    sta (PTR_LO),y
    iny
    dec highTextCellsRemaining
    bne DrawBitmapText_Color

    lda highTextRow
    jsr SetBitmapRowPointer
    lda highTextColumn
    jsr AddColumnOffset
    lda #0
    sta highTextIndex
DrawBitmapText_Character:
    ldx highTextIndex
DrawBitmapText_Read:
    lda $ffff,x
    sta highCharacter
    jsr SelectHighScoreGlyph
    lda #0
    sta highGlyphRow
DrawBitmapText_Row:
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
    bne DrawBitmapText_Row
    lda PTR_LO
    clc
    adc #16
    sta PTR_LO
    bcc DrawBitmapText_Next
    inc PTR_HI
DrawBitmapText_Next:
    inc highTextIndex
    lda highTextIndex
    cmp highTextLength
    bne DrawBitmapText_Character
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
    lda highCharacter
    ; The charset window starts at space; codes below it have no glyph.
    sec
    sbc #CHARSET_FIRST
    bcs SelectHighScoreGlyph_Index
    lda #0
SelectHighScoreGlyph_Index:
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
    adc highTextCharsetLo
    sta SOURCE_LO
    lda highGlyphPage
    adc highTextCharsetHi
    sta SOURCE_HI
    rts

HighScoreHeading:
!byte 'H','I','G','H',' ','S','C','O','R','E','S'
EnterInitialsText:
!byte 'E','N','T','E','R',' ','I','N','I','T','I','A','L','S'
FinalScoreLine:
!byte 'S','C','O','R','E',' ', ' ','0','0','0'
HighScoreEntryLine:
!byte '1','.',' ','D','O','M','.','.','.','.','.', ' ','2','2','0'

HighScoreNames:
!byte 'D','O','M', 'P','R','I', 'T','W','D', 'K','I','M', 'M','A','X'
HighScoreScores:
!byte 0,7,9,3, 0,6,1,3, 0,5,9,0, 0,0,8,0, 0,0,4,0
HighScoreNameOffsets:
!byte 0,3,6,9,12
HighScoreScoreOffsets:
!byte 0,4,8,12,16
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
highTextCharsetLo:   !byte 0
highTextCharsetHi:   !byte 0
highPanelRow:        !byte 0
endAttractNewGame:   !byte 0
attractSeconds:      !byte 0
attractFrames:       !byte 0

HighScoreColorRowLo:
!for row, 0, 24 { !byte <(COLOR_RAM + (row * 40)) }
HighScoreColorRowHi:
!for row, 0, 24 { !byte >(COLOR_RAM + (row * 40)) }

; Sixies glyphs generated from the supplied font sheet, indexed by character
; code less CHARSET_FIRST. The window runs from space to '_', which covers the
; letters, digits, '!' and the '[' and ']' of the settings pager; a full
; 256-entry table would spend 2048 bytes to carry 37 glyphs.
CHARSET_FIRST = $20
HighScoreCharset:
!bin "src/assets/font/SixiesFont_charset.bin"
