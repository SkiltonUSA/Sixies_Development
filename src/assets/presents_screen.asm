; Packed native multicolor Koala Studio 313 presentation card.
* = $bc00

ShowPresentsScreen:
    lda #0
    sta titleScreenActive
    sta creditsScreenActive
    sta SPRITE_ENABLE
    sta BORDER
    lda PresentsBackground
    sta BACKGROUND
    lda VIC_MODE
    ora #%00010000
    sta VIC_MODE

    lda #<PresentsBitmapPacked
    sta SOURCE_LO
    lda #>PresentsBitmapPacked
    sta SOURCE_HI
    lda #<BITMAP
    sta PTR_LO
    lda #>BITMAP
    sta PTR_HI
    jsr UnpackKoalaStream

    lda #<PresentsScreenPacked
    sta SOURCE_LO
    lda #>PresentsScreenPacked
    sta SOURCE_HI
    lda #<SCREEN
    sta PTR_LO
    lda #>SCREEN
    sta PTR_HI
    jsr UnpackKoalaStream

    lda #<PresentsColorPacked
    sta SOURCE_LO
    lda #>PresentsColorPacked
    sta SOURCE_HI
    lda #<COLOR_RAM
    sta PTR_LO
    lda #>COLOR_RAM
    sta PTR_HI
    jmp UnpackKoalaStream

PresentsBitmapPacked:
!bin "src/assets/presents_bitmap_packed.bin"
PresentsScreenPacked:
!bin "src/assets/presents_screen_packed.bin"
PresentsColorPacked:
!bin "src/assets/presents_color_packed.bin"
PresentsBackground:
!bin "src/assets/presents_background.bin"
