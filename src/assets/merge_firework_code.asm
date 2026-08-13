; Three star particles burst from the merged die and fall in separate arcs.
; A five-to-six merge follows the burst with a full-height star shower.
; The effect sprites are multiplexed with the bottom New Game and Settings UI.
* = $8e00

RestoreBottomIconsDuringEffect:
    jsr ConfigureNewGameSprite
    lda #$77
    sta SPRITE0_PTR + 7
    lda settingsFocused
    beq RestoreBottomIconsDuringEffect_SettingsIdle
    lda #COLOR_YELLOW
    bne RestoreBottomIconsDuringEffect_SettingsColor
RestoreBottomIconsDuringEffect_SettingsIdle:
    lda #COLOR_LTBLUE
RestoreBottomIconsDuringEffect_SettingsColor:
    sta SPRITE0_COLOR + 7
    lda #12
    sta SPRITE0_X + 14
    lda #222
    sta SPRITE0_Y + 14

    ; Preserve sprite 5's effect state; slots 6-7 become normal-size UI icons.
    lda SPRITE_X_MSB
    and #%00111111
    ora #%10000000
    sta SPRITE_X_MSB
    lda SPRITE_X_EXPAND
    and #%00111111
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%00111111
    sta SPRITE_Y_EXPAND
    lda #%11000000
    sta uiEnableMask
    lda SPRITE_ENABLE
    and #%00011111
    ora #%11000000
    sta SPRITE_ENABLE
    rts

ConfigureMergeFireworkFrame:
    jsr ConfigureMergeFirework
    lda #0
    ldx mergeChainDepth
    cpx #2
    bcc ConfigureMergeFireworkFrame_ExpansionReady
    lda #%11100000
ConfigureMergeFireworkFrame_ExpansionReady:
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    lda SPRITE_X_MSB
    and #%00011111
    sta SPRITE_X_MSB
    lda #%11100000
    sta uiEnableMask
    ora SPRITE_ENABLE
    sta SPRITE_ENABLE
    rts

ConfigureMergeRainFrame:
    jsr ConfigureMergeFireworkFrame
    lda #0
    sta SPRITE_X_EXPAND
    sta SPRITE_Y_EXPAND
    rts

fireworkRainY0: !byte 0
fireworkRainY1: !byte 0
fireworkRainY2: !byte 0

; $8000 is outside the live screen, bitmap, sprite, and asset regions.
* = $8000

RunMergeFirework:
    inc fireworkActive
    ldx searchX
    lda BoardSpriteX,x
    sta fireworkBaseX
    ldx searchY
    lda BoardSpriteY,x
    sta fireworkBaseY

    ; Chain merges use double-sized particles centered on the merged die.
    lda mergeChainDepth
    cmp #2
    bcc RunMergeFirework_SizeReady
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
    jsr ConfigureMergeFireworkFrame
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
    sta fireworkRainY0
    sta fireworkRainY1
    sta fireworkRainY2
    sta SPRITE0_Y + 10
    sta SPRITE0_Y + 12
    sta SPRITE0_Y + 14
    jsr ConfigureMergeRainFrame
    lda #16
    sta rippleStep
RunSixStarRain_Frame:
    lda #2
    jsr WaitAnimationFrames
    jsr ConfigureMergeRainFrame
    lda fireworkRainY0
    clc
    adc #12
    sta fireworkRainY0
    sta SPRITE0_Y + 10
    lda fireworkRainY1
    clc
    adc #13
    sta fireworkRainY1
    sta SPRITE0_Y + 12
    lda fireworkRainY2
    clc
    adc #14
    sta fireworkRainY2
    sta SPRITE0_Y + 14
    dec rippleStep
    bne RunSixStarRain_Frame
    jmp RunMergeFirework_Done

SetupBottomSpritesImpl:
    lda titleScreenActive
    beq SetupBottomSpritesImpl_GameScreen
    rts
SetupBottomSpritesImpl_GameScreen:
    lda fireworkActive
    beq SetupBottomSpritesImpl_CheckScreen
    jmp RestoreBottomIconsDuringEffect
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
    lda settingsFocused
    beq SetupBottomSpritesImpl_SettingsIdle
    lda #COLOR_YELLOW
    bne SetupBottomSpritesImpl_SettingsColor
SetupBottomSpritesImpl_SettingsIdle:
    lda #COLOR_LTBLUE
SetupBottomSpritesImpl_SettingsColor:
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
