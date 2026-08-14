; Value-scaled impact shake for the second and later merges in one turn.
; Lives in the gap between packed merge callouts and the screen at $4400.
* = $4220

RunMergeGridShake:
    lda VIC_MODE
    sta mergeShakeSavedMode
    and #%11111000
    sta mergeShakeModeBase

    lda groupValue
    sec
    sbc #1
    tax
    lda MergeShakePatternStart,x
    sta mergeShakePattern
    lda MergeShakeFrameDelay,x
    sta mergeShakeDelay

    ldx #0
RunMergeGridShake_Phase:
    txa
    clc
    adc mergeShakePattern
    tay
    lda mergeShakeSavedMode
    and #7
    clc
    adc MergeShakeOffsets,y
    and #7
    ora mergeShakeModeBase
    sta VIC_MODE

    lda MergeShakeDeltas,y
    sta mergeShakeDelta
    ldy #0
RunMergeGridShake_Sprites:
    lda BoardSpriteX,y
    clc
    adc mergeShakeDelta
    sta BoardSpriteX,y
    iny
    cpy #5
    bne RunMergeGridShake_Sprites

    txa
    pha
    lda mergeShakeDelay
    jsr WaitAnimationFrames
    pla
    tax
    inx
    cpx #7
    bne RunMergeGridShake_Phase

    lda mergeShakeSavedMode
    sta VIC_MODE
    rts

MergeShakePatternStart: !byte 0,7,14,21,28,35
MergeShakeFrameDelay:   !byte 1,1,1,1,1,2

; Absolute fine-scroll positions for merge values 1 through 6.
MergeShakeOffsets:
!byte 1,7,1,7,1,7,0
!byte 1,7,2,6,1,7,0
!byte 2,6,2,6,2,6,0
!byte 2,6,3,5,2,6,0
!byte 3,5,3,5,3,5,0
!byte 3,5,3,5,3,5,0

; Signed sprite deltas matching each absolute fine-scroll position above.
MergeShakeDeltas:
!byte 1,$fe,2,$fe,2,$fe,1
!byte 1,$fe,3,$fc,3,$fe,1
!byte 2,$fc,4,$fc,4,$fc,2
!byte 2,$fc,5,$fa,5,$fc,2
!byte 3,$fa,6,$fa,6,$fa,3
!byte 3,$fa,6,$fa,6,$fa,3

mergeShakeSavedMode: !byte 0
mergeShakeModeBase:  !byte 0
mergeShakePattern:   !byte 0
mergeShakeDelay:     !byte 1
mergeShakeDelta:     !byte 0
