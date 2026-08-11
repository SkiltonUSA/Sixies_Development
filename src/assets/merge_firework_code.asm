; Three star particles burst from the merged die and fall in separate arcs.
; A five-to-six merge follows the burst with a full-height star shower.
; $8000 is outside the live screen, bitmap, sprite, and asset regions.
* = $8000

RunMergeFirework:
    inc fireworkActive
    lda #0
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    ldx searchX
    lda BoardSpriteX,x
    sta fireworkBaseX
    ldx searchY
    lda BoardSpriteY,x
    sta fireworkBaseY
    jsr ConfigureMergeFirework

    ; Chain merges use double-sized particles centered on the merged die.
    lda mergeChainDepth
    cmp #2
    bcc RunMergeFirework_SizeReady
    lda #%11100000
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    lda fireworkBaseX
    sec
    sbc #12
    sta fireworkBaseX
    lda fireworkBaseY
    sec
    sbc #10
    sta fireworkBaseY
RunMergeFirework_SizeReady:

    ; Preview sprite 7 normally crosses X=255; particles remain inside the grid.
    lda SPRITE_X_MSB
    and #%00011111
    sta SPRITE_X_MSB
    lda #0
    sta rippleStep
RunMergeFirework_Frame:
    ldx rippleStep
    lda fireworkBaseX
    sec
    sbc FireworkSideX,x
    sta SPRITE0_X + 10
    lda fireworkBaseX
    sta SPRITE0_X + 12
    clc
    adc FireworkSideX,x
    sta SPRITE0_X + 14

    lda fireworkBaseY
    clc
    adc FireworkSideY,x
    sta SPRITE0_Y + 10
    sta SPRITE0_Y + 14
    lda fireworkBaseY
    clc
    adc FireworkCenterY,x
    sta SPRITE0_Y + 12

    lda #2
    jsr WaitAnimationFrames
    inc rippleStep
    lda rippleStep
    cmp #9
    bne RunMergeFirework_Frame
    lda #0
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    lda groupValue
    cmp #5
    beq RunSixStarRain
RunMergeFirework_Done:
    dec fireworkActive
    rts

RunSixStarRain:
    ; Reveal the upgraded six before its celebration begins.
    lda #6
    ldx activeIndex
    sta board,x
    jsr PublishBoardForAnimation

    ; Spread three stars across the board and let each descend at a unique speed.
    lda #108
    sta SPRITE0_X + 10
    lda #172
    sta SPRITE0_X + 12
    lda #236
    sta SPRITE0_X + 14
    lda #42
    sta SPRITE0_Y + 10
    sta SPRITE0_Y + 12
    sta SPRITE0_Y + 14
    lda #16
    sta rippleStep
RunSixStarRain_Frame:
    lda #2
    jsr WaitAnimationFrames
    lda SPRITE0_Y + 10
    clc
    adc #12
    sta SPRITE0_Y + 10
    lda SPRITE0_Y + 12
    clc
    adc #13
    sta SPRITE0_Y + 12
    lda SPRITE0_Y + 14
    clc
    adc #14
    sta SPRITE0_Y + 14
    dec rippleStep
    bne RunSixStarRain_Frame
    jmp RunMergeFirework_Done

SetupBottomSpritesImpl:
    lda fireworkActive
    beq SetupBottomSpritesImpl_CheckScreen
    lda #%11100000
    sta uiEnableMask
    lda SPRITE_ENABLE
    ora #%11100000
    sta SPRITE_ENABLE
    rts
SetupBottomSpritesImpl_CheckScreen:
    lda gameOverBlindActive
    beq SetupBottomSpritesImpl_Visible
    lda #0
    sta uiEnableMask
    sta SPRITE_ENABLE
    rts
SetupBottomSpritesImpl_Visible:
    jsr ConfigureNewGameSprite
    lda #$77
    sta SPRITE0_PTR + 7
    lda #COLOR_LTBLUE
    sta SPRITE0_COLOR + 7
    lda #12
    sta SPRITE0_X + 14
    lda #222
    sta SPRITE0_Y + 14
    lda #%10000000
    sta SPRITE_X_MSB
    ; Preserve row-5 sprites until row 0 safely reassigns them next frame.
    lda SPRITE_ENABLE
    and #%00011111
    ora #%11000000
    sta SPRITE_ENABLE
    rts
