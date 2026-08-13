; 16x16 Sixies display font renderer for the fading Credits cards.
* = $b940

DrawSixiesFont16Text:
DrawCreditsFont16Text:
    lda highTextSourceLo
    sta DrawCreditsFont16Text_Read + 1
    sta DrawCreditsFont16Text_ColorRead + 1
    lda highTextSourceHi
    sta DrawCreditsFont16Text_Read + 2
    sta DrawCreditsFont16Text_ColorRead + 2

    lda highTextRow
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc highTextColumn
    sta PTR_LO
    bcc DrawCreditsFont16Text_ColorReady
    inc PTR_HI
DrawCreditsFont16Text_ColorReady:
    jsr DrawCreditsFont16Text_ColorRow
    lda PTR_LO
    clc
    adc #40
    sta PTR_LO
    bcc DrawCreditsFont16Text_ColorBottomReady
    inc PTR_HI
DrawCreditsFont16Text_ColorBottomReady:
    jsr DrawCreditsFont16Text_ColorRow

    lda highTextRow
    jsr SetBitmapRowPointer
    lda highTextColumn
    jsr AddColumnOffset
    lda #0
    sta highTextIndex
DrawCreditsFont16Text_Character:
    ldx highTextIndex
DrawCreditsFont16Text_Read:
    lda $ffff,x
    jsr SelectCreditsFont16Glyph
    lda SOURCE_LO
    sta DrawCreditsFont16Text_ReadTopLeft + 1
    sta DrawCreditsFont16Text_ReadTopRight + 1
    sta DrawCreditsFont16Text_ReadBottomLeft + 1
    sta DrawCreditsFont16Text_ReadBottomRight + 1
    lda SOURCE_HI
    sta DrawCreditsFont16Text_ReadTopLeft + 2
    sta DrawCreditsFont16Text_ReadTopRight + 2
    sta DrawCreditsFont16Text_ReadBottomLeft + 2
    sta DrawCreditsFont16Text_ReadBottomRight + 2
    ldx #0
    ldy #0
DrawCreditsFont16Text_Top:
DrawCreditsFont16Text_ReadTopLeft:
    lda $ffff,x
    sta (PTR_LO),y
    inx
    tya
    clc
    adc #8
    tay
DrawCreditsFont16Text_ReadTopRight:
    lda $ffff,x
    sta (PTR_LO),y
    inx
    tya
    sec
    sbc #7
    tay
    cpy #8
    bne DrawCreditsFont16Text_Top

    lda PTR_LO
    clc
    adc #$40
    sta PTR_LO
    lda PTR_HI
    adc #1
    sta PTR_HI
    ldy #0
DrawCreditsFont16Text_Bottom:
DrawCreditsFont16Text_ReadBottomLeft:
    lda $ffff,x
    sta (PTR_LO),y
    inx
    tya
    clc
    adc #8
    tay
DrawCreditsFont16Text_ReadBottomRight:
    lda $ffff,x
    sta (PTR_LO),y
    inx
    tya
    sec
    sbc #7
    tay
    cpy #8
    bne DrawCreditsFont16Text_Bottom

    sec
    lda PTR_LO
    sbc #$30
    sta PTR_LO
    lda PTR_HI
    sbc #1
    sta PTR_HI
    inc highTextIndex
    lda highTextIndex
    cmp highTextLength
    beq DrawCreditsFont16Text_Done
    jmp DrawCreditsFont16Text_Character
DrawCreditsFont16Text_Done:
    rts

; Use the original sheet palette while a card is fully visible. Gray phases
; remain monochrome so the existing fade-in/out still reads clearly.
DrawCreditsFont16Text_ColorRow:
    lda #0
    sta highTextIndex
    sta creditsFontCellOffset
DrawCreditsFont16Text_ColorCharacter:
    ldx highTextIndex
DrawCreditsFont16Text_ColorRead:
    lda $ffff,x
    jsr SelectCreditsFont16Glyph
    lda highTextColor
    cmp #COLOR_WHITE
    bne DrawCreditsFont16Text_ColorSelected
    lda creditsFontGlyphColor
DrawCreditsFont16Text_ColorSelected:
    asl
    asl
    asl
    asl
    ldy creditsFontCellOffset
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    inc creditsFontCellOffset
    inc creditsFontCellOffset
    inc highTextIndex
    lda highTextIndex
    cmp highTextLength
    bne DrawCreditsFont16Text_ColorCharacter
    rts

SelectCreditsFont16Glyph:
    ldx #COLOR_WHITE
    stx creditsFontGlyphColor
    cmp #' '
    beq SelectCreditsFont16Glyph_Space
    cmp #'#'
    beq SelectCreditsFont16Glyph_Hash
    cmp #'('
    beq SelectCreditsFont16Glyph_LeftParen
    cmp #')'
    beq SelectCreditsFont16Glyph_RightParen
    cmp #'['
    beq SelectCreditsFont16Glyph_LeftBracket
    cmp #']'
    beq SelectCreditsFont16Glyph_RightBracket
    cmp #'.'
    beq SelectCreditsFont16Glyph_Period
    cmp #'0'
    bcc SelectCreditsFont16Glyph_Letter
    cmp #('9' + 1)
    bcs SelectCreditsFont16Glyph_Letter
    sec
    sbc #'0'
    clc
    adc #26
    bne SelectCreditsFont16Glyph_Index
SelectCreditsFont16Glyph_Letter:
    cmp #'A'
    bcc SelectCreditsFont16Glyph_Space
    cmp #('Z' + 1)
    bcs SelectCreditsFont16Glyph_Space
    sec
    sbc #'A'
SelectCreditsFont16Glyph_Index:
    tax
    stx creditsFontGlyphIndex
    lda SixiesFontColors,x
    sta creditsFontGlyphColor
    lda #0
    sta SOURCE_HI
    lda creditsFontGlyphIndex
    !for shift, 1, 5 {
        asl
        rol SOURCE_HI
    }
    clc
    adc #<CreditsFont16Data
    sta SOURCE_LO
    lda SOURCE_HI
    adc #>CreditsFont16Data
    sta SOURCE_HI
    rts
SelectCreditsFont16Glyph_Space:
    lda #COLOR_BLACK
    sta creditsFontGlyphColor
    lda #<CreditsFont16Space
    ldx #>CreditsFont16Space
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_Hash:
    lda #<CreditsFont16Hash
    ldx #>CreditsFont16Hash
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_LeftParen:
    lda #<CreditsFont16LeftParen
    ldx #>CreditsFont16LeftParen
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_RightParen:
    lda #<CreditsFont16RightParen
    ldx #>CreditsFont16RightParen
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_Period:
    lda #<CreditsFont16Period
    ldx #>CreditsFont16Period
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_LeftBracket:
    lda #<CreditsFont16LeftBracket
    ldx #>CreditsFont16LeftBracket
    bne SelectCreditsFont16Glyph_Store
SelectCreditsFont16Glyph_RightBracket:
    lda #<CreditsFont16RightBracket
    ldx #>CreditsFont16RightBracket
SelectCreditsFont16Glyph_Store:
    sta SOURCE_LO
    stx SOURCE_HI
    rts

CreditsFont16Space: !fill 32,0
CreditsFont16Hash:
!byte $00,$00,$00,$00,$11,$00,$11,$00,$7f,$c0,$22,$00,$22,$00,$ff,$80
!byte $44,$00,$44,$00,$fe,$00,$88,$00,$88,$00,$00,$00,$00,$00,$00,$00
CreditsFont16LeftParen:
!byte $03,$00,$0c,$00,$18,$00,$30,$00,$60,$00,$60,$00,$c0,$00,$c0,$00
!byte $c0,$00,$c0,$00,$60,$00,$60,$00,$30,$00,$18,$00,$0c,$00,$03,$00
CreditsFont16RightParen:
!byte $c0,$00,$30,$00,$18,$00,$0c,$00,$06,$00,$06,$00,$03,$00,$03,$00
!byte $03,$00,$03,$00,$06,$00,$06,$00,$0c,$00,$18,$00,$30,$00,$c0,$00
CreditsFont16Period:
!fill 24,0
!byte $03,$c0,$03,$c0,$03,$c0,$00,$00
CreditsFont16LeftBracket:
!byte $0f,$f0,$0f,$f0
!for row, 1, 12 { !byte $0c,$00 }
!byte $0f,$f0,$0f,$f0
CreditsFont16RightBracket:
!byte $0f,$f0,$0f,$f0
!for row, 1, 12 { !byte $00,$30 }
!byte $0f,$f0,$0f,$f0

creditsFontCellOffset: !byte 0
creditsFontGlyphIndex: !byte 0
creditsFontGlyphColor: !byte COLOR_WHITE
