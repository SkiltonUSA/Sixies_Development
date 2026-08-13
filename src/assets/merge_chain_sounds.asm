; Escalating SID effects selected by the value of the dice being merged.
* = $9400

RunMergeLevelEffects:
    jsr PlayMergeValueSound
    lda mergeChainDepth
    cmp #2
    bcc RunMergeLevelEffects_Done
    jmp RunMergeGridShake
RunMergeLevelEffects_Done:
    rts

PlayMergeValueSound:
    lda groupValue
    cmp #1
    bne PlayMergeValueSound_Second
    jmp PlayFirstMerge
PlayMergeValueSound_Second:
    cmp #2
    bne PlayMergeValueSound_Third
    jmp PlaySecondMerge
PlayMergeValueSound_Third:
    cmp #3
    bne PlayMergeValueSound_Fourth
    jmp PlayThirdMerge
PlayMergeValueSound_Fourth:
    cmp #4
    bne PlayMergeValueSound_Fifth
    jmp PlayFourthMerge
PlayMergeValueSound_Fifth:
    cmp #5
    bne PlayMergeValueSound_Sixth
    jmp PlayFifthMerge
PlayMergeValueSound_Sixth:
    cmp #6
    bne PlayMergeValueSound_Done
    jmp PlaySixMerge
PlayMergeValueSound_Done:
    rts

PlayThirdMerge:
    lda #5
    ldx #0
    jmp InitHigherMergeSound

PlayFourthMerge:
    lda #6
    ldx #4
    jmp InitHigherMergeSound

PlayFifthMerge:
    lda #7
    ldx #8

InitHigherMergeSound:
    sta sfxMode
    stx higherMergeNoteIndex
    sec
    sbc #5
    tay
    lda HigherMergeGateOff,y
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda HigherMergeFreqLo,x
    sta SID_V1_FREQ_LO
    lda HigherMergeFreqHi,x
    sta SID_V1_FREQ_HI
    lda #0
    sta SID_V1_PW_LO
    lda HigherMergePulseWidth,y
    sta SID_V1_PW_HI
    lda HigherMergeAttackDecay,y
    sta SID_V1_AD
    lda HigherMergeSustainRelease,y
    sta SID_V1_SR
    lda HigherMergeGateOn,y
    sta SID_V1_CONTROL
    lda #5
    sta sfxPriority
    lda #20
    sta sfxFrames
    rts

PlaySixMerge:
    ; Three sixes vanish in a descending burst of SID noise.
    lda #$80
    sta SID_V1_CONTROL
    sta sfxGateOffControl
    lda #$ff
    sta SID_V1_FREQ_LO
    lda #$58
    sta SID_V1_FREQ_HI
    sta sfxSweepHi
    lda #0
    sta SID_V1_PW_LO
    sta SID_V1_PW_HI
    lda #$02
    sta SID_V1_AD
    lda #$b6
    sta SID_V1_SR
    lda #$81
    sta SID_V1_CONTROL
    lda #6
    sta sfxPriority
    lda #8
    sta sfxMode
    lda #24
    sta sfxFrames
    rts

UpdateSixMergeExplosion:
    lda sfxRandomSeed
    lsr
    bcc UpdateSixMergeExplosion_StoreSeed
    eor #$b8
UpdateSixMergeExplosion_StoreSeed:
    sta sfxRandomSeed
    sta SID_V1_FREQ_LO
    lda sfxSweepHi
    sec
    sbc #2
    sta sfxSweepHi
    sta SID_V1_FREQ_HI
    rts

UpdateHigherMergeNotes:
    lda sfxFrames
    cmp #15
    beq UpdateHigherMergeNotes_Advance
    cmp #10
    beq UpdateHigherMergeNotes_Advance
    cmp #5
    beq UpdateHigherMergeNotes_Advance
    rts

UpdateHigherMergeNotes_Advance:
    inc higherMergeNoteIndex
    lda sfxMode
    sec
    sbc #5
    tay
    lda HigherMergeGateOff,y
    sta SID_V1_CONTROL
    ldx higherMergeNoteIndex
    lda HigherMergeFreqLo,x
    sta SID_V1_FREQ_LO
    lda HigherMergeFreqHi,x
    sta SID_V1_FREQ_HI
    lda HigherMergeGateOn,y
    sta SID_V1_CONTROL
    rts

; Values 3-5 rise through G major, C major, and an E minor finale.
HigherMergeFreqLo:
!byte $2c,$50,$60,$58, $9c,$b8,$58,$38, $b8,$58,$50,$70
HigherMergeFreqHi:
!byte $34,$41,$52,$68, $45,$57,$68,$8b, $57,$68,$82,$af
HigherMergeGateOff:       !byte $40,$20,$10
HigherMergeGateOn:        !byte $41,$21,$11
HigherMergePulseWidth:    !byte $04,$00,$00
HigherMergeAttackDecay:   !byte $01,$01,$00
HigherMergeSustainRelease: !byte $b4,$c5,$d6

higherMergeNoteIndex: !byte 0

; Show the points above the merged die, then carry them diagonally into the
; permanent score with one expanded three-character sprite.
AddAnimatedGroupScore:
    jsr PrepareMergeScoreGain
    jsr BuildMergeScoreSprite
    inc fireworkActive
    jsr ConfigureMergeScoreSprite
    lda #3
    jsr WaitAnimationFrames

AnimateMergeScoreSprite:
    lda mergeScoreX
    cmp mergeScoreTargetX
    beq AnimateMergeScoreSprite_XReady
    sec
    sbc #8
    cmp mergeScoreTargetX
    bcs AnimateMergeScoreSprite_StoreX
    lda mergeScoreTargetX
AnimateMergeScoreSprite_StoreX:
    sta mergeScoreX
    sta SPRITE0_X + 10
AnimateMergeScoreSprite_XReady:
    lda mergeScoreY
    cmp #58
    beq AnimateMergeScoreSprite_YReady
    bcc AnimateMergeScoreSprite_MoveDown
    sec
    sbc #8
    cmp #58
    bcs AnimateMergeScoreSprite_StoreY
    lda #58
    bne AnimateMergeScoreSprite_StoreY
AnimateMergeScoreSprite_MoveDown:
    clc
    adc #4
    cmp #58
    bcc AnimateMergeScoreSprite_StoreY
    lda #58
AnimateMergeScoreSprite_StoreY:
    sta mergeScoreY
    sta SPRITE0_Y + 10
AnimateMergeScoreSprite_YReady:
    lda #1
    jsr WaitAnimationFrames
    lda mergeScoreX
    cmp mergeScoreTargetX
    bne AnimateMergeScoreSprite
    lda mergeScoreY
    cmp #58
    bne AnimateMergeScoreSprite

    jsr AddGroupScore
    jsr UpdateScoreDisplay
    lda #2
    jsr WaitAnimationFrames

    lda SPRITE_ENABLE
    and #%00011111
    sta SPRITE_ENABLE
    lda #0
    sta uiEnableMask
    lda SPRITE_X_EXPAND
    and #%00011111
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%00011111
    sta SPRITE_Y_EXPAND
    jsr BuildShadowDiceSprites
    dec fireworkActive
    rts

* = $9380
PrepareMergeScoreGain:
    lda #0
    ldx groupCount
PrepareMergeScoreGain_Add:
    clc
    adc groupValue
    dex
    bne PrepareMergeScoreGain_Add
    sta mergeScoreRemainder

    lda #0
    sta mergeScoreDigits
    sta mergeScoreDigits + 1
PrepareMergeScoreGain_Hundreds:
    lda mergeScoreRemainder
    cmp #100
    bcc PrepareMergeScoreGain_Tens
    sec
    sbc #100
    sta mergeScoreRemainder
    inc mergeScoreDigits
    bne PrepareMergeScoreGain_Hundreds
PrepareMergeScoreGain_Tens:
    lda mergeScoreRemainder
    cmp #10
    bcc PrepareMergeScoreGain_Ones
    sec
    sbc #10
    sta mergeScoreRemainder
    inc mergeScoreDigits + 1
    bne PrepareMergeScoreGain_Tens
PrepareMergeScoreGain_Ones:
    sta mergeScoreDigits + 2
    lda mergeScoreDigits
    bne PrepareMergeScoreGain_ThreeDigits
    lda mergeScoreDigits + 1
    beq PrepareMergeScoreGain_OneDigit
    sta mergeScoreDigits
    lda mergeScoreDigits + 2
    sta mergeScoreDigits + 1
    lda #2
    bne PrepareMergeScoreGain_StoreCount
PrepareMergeScoreGain_OneDigit:
    lda mergeScoreDigits + 2
    sta mergeScoreDigits
    lda #1
    bne PrepareMergeScoreGain_StoreCount
PrepareMergeScoreGain_ThreeDigits:
    lda #3
PrepareMergeScoreGain_StoreCount:
    sta mergeScoreDigitCount
    rts

* = $9608
BuildMergeScoreSprite:
    lda #0
    ldy #0
BuildMergeScoreSprite_Clear:
    sta SHADOW_SPRITES,y
    sta SHADOW_SPRITES + 64,y
    sta SHADOW_SPRITES + 128,y
    iny
    cpy #64
    bne BuildMergeScoreSprite_Clear

    lda #<HighScoreCharset
    sta highTextCharsetLo
    lda #>HighScoreCharset
    sta highTextCharsetHi
    lda #0
    sta mergeScoreDigitIndex
BuildMergeScoreSprite_Digit:
    ldx mergeScoreDigitIndex
    lda mergeScoreDigits,x
    clc
    adc #'0'
    sta highCharacter
    jsr SelectHighScoreGlyph

    lda mergeScoreDigitIndex
    sta PTR_LO
    lda #>SHADOW_SPRITES
    sta PTR_HI
    ldy #0
BuildMergeScoreSprite_Row:
    lda (SOURCE_LO),y
    sta mergeScoreGlyphByte
    tya
    pha
    ldy #0
    lda mergeScoreGlyphByte
    sta (PTR_LO),y
    pla
    tay
    lda PTR_LO
    clc
    adc #3
    sta PTR_LO
    bcc BuildMergeScoreSprite_NextRow
    inc PTR_HI
BuildMergeScoreSprite_NextRow:
    iny
    cpy #8
    bne BuildMergeScoreSprite_Row
    inc mergeScoreDigitIndex
    lda mergeScoreDigitIndex
    cmp mergeScoreDigitCount
    bne BuildMergeScoreSprite_Digit
    rts

ConfigureMergeScoreSprite:
    lda #$30
    sta SPRITE0_PTR + 5
    lda #$31
    sta SPRITE0_PTR + 6
    lda #$32
    sta SPRITE0_PTR + 7
    lda #COLOR_YELLOW
    sta SPRITE0_COLOR + 5
    ldx mergeScoreDigitCount
    dex
    lda MergeScoreTargetX,x
    sta mergeScoreTargetX
    lda MergeScoreCenterOffset,x
    ldx searchX
    clc
    adc BoardSpriteX,x
    sta mergeScoreX
    sta SPRITE0_X + 10
    ldx searchY
    lda BoardSpriteY,x
    sec
    sbc #18
    sta mergeScoreY
    sta SPRITE0_Y + 10
    lda SPRITE_X_MSB
    and #%00011111
    sta SPRITE_X_MSB
    lda SPRITE_X_EXPAND
    and #%00011111
    ora #%00100000
    sta SPRITE_X_EXPAND
    lda SPRITE_Y_EXPAND
    and #%00011111
    ora #%00100000
    sta SPRITE_Y_EXPAND
    lda #%11100000
    sta uiEnableMask
    lda SPRITE_ENABLE
    and #%00011111
    ora #%11100000
    sta SPRITE_ENABLE
    rts

MergeScoreTargetX:      !byte 56,48,40
MergeScoreCenterOffset: !byte 4,$fc,$f4
mergeScoreDigits: !byte 0,0,0
mergeScoreRemainder: !byte 0
mergeScoreDigitCount: !byte 1
mergeScoreDigitIndex: !byte 0
mergeScoreGlyphByte: !byte 0
mergeScoreX: !byte 0
mergeScoreY: !byte 0
mergeScoreTargetX: !byte 0
