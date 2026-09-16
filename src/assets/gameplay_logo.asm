; Compact version of the supplied green wordmark centered above the board.
; The bitmap data occupies the free area below screen RAM.
* = $4319

GameplayLogoBitmapData:
!bin "src/assets/gameplay_logo_bitmap.bin"

; The 64x80 mascot data ends at $4acf; merge-callout helpers begin at $4b84.
* = $4ad0

DrawGameplayBitmapLogo:
    lda #<GameplayLogoBitmapData
    sta SOURCE_LO
    lda #>GameplayLogoBitmapData
    sta SOURCE_HI
    lda #GAMEPLAY_LOGO_ROW
    sta workRow
DrawGameplayBitmapLogo_Row:
    lda workRow
    jsr SetBitmapRowPointer
    lda #GAMEPLAY_LOGO_COL
    jsr AddColumnOffset
    ldy #0
DrawGameplayBitmapLogo_Byte:
    lda (SOURCE_LO),y
    sta (PTR_LO),y
    iny
    cpy #96
    bne DrawGameplayBitmapLogo_Byte

    lda SOURCE_LO
    clc
    adc #96
    sta SOURCE_LO
    bcc DrawGameplayBitmapLogo_SourceReady
    inc SOURCE_HI
DrawGameplayBitmapLogo_SourceReady:
    lda workRow
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc #GAMEPLAY_LOGO_COL
    sta PTR_LO
    bcc DrawGameplayBitmapLogo_ScreenReady
    inc PTR_HI
DrawGameplayBitmapLogo_ScreenReady:
    ldy #0
    lda #(COLOR_LTGREEN << 4) | COLOR_BLACK
DrawGameplayBitmapLogo_Color:
    sta (PTR_LO),y
    iny
    cpy #12
    bne DrawGameplayBitmapLogo_Color

    inc workRow
    lda workRow
    cmp #(GAMEPLAY_LOGO_ROW + 2)
    bne DrawGameplayBitmapLogo_Row
    rts
