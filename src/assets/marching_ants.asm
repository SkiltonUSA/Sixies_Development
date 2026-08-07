; Animated two-pixel marching-ants cursor border.
* = $5a00

DrawMarchingHighlightCell:
    lda #(COLOR_YELLOW << 4) | COLOR_DKGRAY
    jsr ColorHighlightedCell
    jsr SetHighlightBitmapPointer
    lda #0
    sta workColumn
DrawMarchingHighlightCell_Row:
    ldy #0
DrawMarchingHighlightCell_Side:
    sty workRow
    tya
    clc
    adc highlightPhase
    and #3
    cmp #2
    bcs DrawMarchingHighlightCell_SideOff

    ldy workRow
    lda (PTR_LO),y
    ora #$c0
    sta (PTR_LO),y
    tya
    clc
    adc #24
    tay
    lda (PTR_LO),y
    ora #$03
    sta (PTR_LO),y
    jmp DrawMarchingHighlightCell_NextSide

DrawMarchingHighlightCell_SideOff:
    ldy workRow
    lda (PTR_LO),y
    and #$3f
    sta (PTR_LO),y
    tya
    clc
    adc #24
    tay
    lda (PTR_LO),y
    and #$fc
    sta (PTR_LO),y

DrawMarchingHighlightCell_NextSide:
    ldy workRow
    iny
    cpy #8
    bne DrawMarchingHighlightCell_Side
    jsr AdvanceHighlightBitmapRow
    inc workColumn
    lda workColumn
    cmp #4
    bne DrawMarchingHighlightCell_Row

    jsr SetHighlightBitmapPointer
    ldy #0
    lda #32
    jsr DrawMarchingHorizontal
    jsr SetHighlightBitmapPointer
    jsr AddHighlightBottomOffset
    ldy #6
    lda #38
    jmp DrawMarchingHorizontal

DrawMarchingHorizontal:
    sta workRow
    ldx highlightPhase
    lda MarchingAntPatterns,x
    sta cellBorderColor
DrawMarchingHorizontal_Character:
    lda cellBorderColor
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    tya
    clc
    adc #7
    tay
    cpy workRow
    bne DrawMarchingHorizontal_Character
    rts

RestoreMarchingHighlightCell:
    jsr SetHighlightBitmapPointer
    lda #0
    sta workColumn
RestoreMarchingHighlightCell_Row:
    ldy #0
RestoreMarchingHighlightCell_Left:
    lda (PTR_LO),y
    ora #$c0
    sta (PTR_LO),y
    iny
    cpy #8
    bne RestoreMarchingHighlightCell_Left
    jsr AdvanceHighlightBitmapRow
    inc workColumn
    lda workColumn
    cmp #4
    bne RestoreMarchingHighlightCell_Row

    jsr SetHighlightBitmapPointer
    ldy #0
RestoreMarchingHighlightCell_Top:
    lda #$ff
    sta (PTR_LO),y
    iny
    sta (PTR_LO),y
    tya
    clc
    adc #7
    tay
    cpy #32
    bne RestoreMarchingHighlightCell_Top
    rts

MarchingAntPatterns:
!byte $cc,$99,$33,$66
