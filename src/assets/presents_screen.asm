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
    jsr UnpackKoalaStream

    ; The build-specific V1.xxx sprite is the first tile in the title-prompt
    ; composite. Copy it into runtime sprite slot $30 for the presentation card.
    lda #<TitlePromptSpriteData
    sta SOURCE_LO
    lda #>TitlePromptSpriteData
    sta SOURCE_HI
    lda #<SHADOW_SPRITES
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    ldx #0
    lda #64
    jsr CopyTitleBlock

    lda #$30
    sta SPRITE0_PTR
    lda #COLOR_WHITE
    sta SPRITE0_COLOR
    lda #32
    sta SPRITE0_X
    lda #234
    sta SPRITE0_Y
    lda SPRITE_X_MSB
    and #%11111110
    sta SPRITE_X_MSB
    lda SPRITE_MULTICOLOR
    and #%11111110
    sta SPRITE_MULTICOLOR
    lda SPRITE_X_EXPAND
    and #%11111110
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%11111110
    sta SPRITE_Y_EXPAND
    lda SPRITE_PRIORITY
    and #%11111110
    sta SPRITE_PRIORITY
    lda #1
    sta SPRITE_ENABLE
    rts

PresentsBitmapPacked:
!bin "src/assets/presents_bitmap_packed.bin"
PresentsScreenPacked:
!bin "src/assets/presents_screen_packed.bin"
PresentsColorPacked:
!bin "src/assets/presents_color_packed.bin"
PresentsBackground:
!bin "src/assets/presents_background.bin"
