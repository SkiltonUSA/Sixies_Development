; Value-matched comic artwork displayed beneath the mascot during a merge.
* = $1bf1

ShowMergeExclamation:
    ; The board raster IRQ also uses PTR_LO/PTR_HI and SOURCE_LO/SOURCE_HI.
    ; Keep the short decode atomic so an IRQ cannot redirect sprite writes.
    sei
    ldx groupValue
    dex
    lda ExclamationDataLo,x
    sta SOURCE_LO
    lda ExclamationDataHi,x
    sta SOURCE_HI
    lda #<SHADOW_SPRITES
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    lda #0
    sta exclamationOutputCount
    sta SHADOW_SPRITES + 63
    sta SHADOW_SPRITES + 127
    sta SHADOW_SPRITES + 191
UnpackMergeExclamation:
    jsr ReadExclamationByte
    ; ReadExclamationByte advances SOURCE_LO, which changes the N flag.
    ; Test the returned packet byte explicitly instead of relying on BMI.
    cmp #$80
    bcs UnpackMergeExclamation_ZeroRun
    sta exclamationPacketCount
UnpackMergeExclamation_Literal:
    jsr ReadExclamationByte
    jsr StoreExclamationByte
    dec exclamationPacketCount
    bne UnpackMergeExclamation_Literal
    jmp UnpackMergeExclamation_Check
UnpackMergeExclamation_ZeroRun:
    and #$7f
    sta exclamationPacketCount
UnpackMergeExclamation_Zero:
    lda #0
    jsr StoreExclamationByte
    dec exclamationPacketCount
    bne UnpackMergeExclamation_Zero
UnpackMergeExclamation_Check:
    lda exclamationOutputCount
    cmp #189
    bne UnpackMergeExclamation
    cli
    inc fireworkActive
    jmp RestoreMergeExclamationSprites

HideMergeExclamation:
    lda SPRITE_ENABLE
    and #%00011111
    sta SPRITE_ENABLE
    lda #0
    sta uiEnableMask
    dec fireworkActive
    jmp BuildShadowDiceSprites

* = $4390
ReadExclamationByte:
    ldy #0
    lda (SOURCE_LO),y
    inc SOURCE_LO
    bne ReadExclamationByte_Done
    inc SOURCE_HI
ReadExclamationByte_Done:
    rts

StoreExclamationByte:
    ldy #0
    sta (PTR_LO),y
    inc PTR_LO
    bne StoreExclamationByte_Count
    inc PTR_HI
StoreExclamationByte_Count:
    inc exclamationOutputCount
    lda exclamationOutputCount
    cmp #63
    beq StoreExclamationByte_SkipPad
    cmp #126
    bne StoreExclamationByte_Done
StoreExclamationByte_SkipPad:
    inc PTR_LO
    bne StoreExclamationByte_Done
    inc PTR_HI
StoreExclamationByte_Done:
    rts

ExclamationSpriteX:     !byte 28,52,76
exclamationPacketCount: !byte 0
exclamationOutputCount: !byte 0

* = $43bf
RestoreMergeExclamationSprites:
    ldx #2
RestoreMergeExclamationSprites_Next:
    txa
    clc
    adc #$30
    sta SPRITE0_PTR + 5,x
    lda mergeFlashColor
    sta SPRITE0_COLOR + 5,x
    txa
    asl
    tay
    lda ExclamationSpriteX,x
    sta SPRITE0_X + 10,y
    lda #164
    sta SPRITE0_Y + 10,y
    dex
    bpl RestoreMergeExclamationSprites_Next
    lda SPRITE_X_MSB
    and #%00011111
    sta SPRITE_X_MSB
    lda #0
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    lda #%11100000
    sta uiEnableMask
    ora SPRITE_ENABLE
    sta SPRITE_ENABLE
    rts

!source "src/assets/exclamation_sprites_data.asm"
