; Four-digit score arithmetic and display selection.
; The firework routine ends at $8109, leaving this scoring gap before the
; original four-digit counter at $814a.
* = $810a

AddGroupScore:
    jsr LoadChainScoreMultiplier
AddGroupScore_Multiplier:
    lda #3
    sta scoreAddCount
AddGroupScore_Die:
    lda groupValue
    sta scoreAddValue
AddGroupScore_Value:
    jsr IncrementScore
    dec scoreAddValue
    bne AddGroupScore_Value
    dec scoreAddCount
    bne AddGroupScore_Die
    dex
    bne AddGroupScore_Multiplier
    lda groupValue
    cmp #6
    bne AddGroupScore_Done
    ldx #150
AddGroupScore_SixBonus:
    jsr IncrementScore
    dex
    bne AddGroupScore_SixBonus
AddGroupScore_Done:
    rts

* = $814a

IncrementScore4:
    lda scoreThousands
    cmp #9
    bne IncrementScore4_Ones
    lda scoreHundreds
    cmp #9
    bne IncrementScore4_Ones
    lda scoreTens
    cmp #9
    bne IncrementScore4_Ones
    lda scoreOnes
    cmp #9
    beq IncrementScore4_Done
IncrementScore4_Ones:
    inc scoreOnes
    lda scoreOnes
    cmp #10
    bcc IncrementScore4_Done
    lda #0
    sta scoreOnes
    inc scoreTens
    lda scoreTens
    cmp #10
    bcc IncrementScore4_Done
    lda #0
    sta scoreTens
    inc scoreHundreds
    lda scoreHundreds
    cmp #10
    bcc IncrementScore4_Done
    lda #0
    sta scoreHundreds
    inc scoreThousands
IncrementScore4_Done:
    rts

UpdateScoreDisplay4:
    lda scoreThousands
    beq UpdateScoreDisplay4_NoThousands
    sta ScoreDigits
    lda scoreHundreds
    sta ScoreDigits + 1
    lda scoreTens
    sta ScoreDigits + 2
    lda scoreOnes
    sta ScoreDigits + 3
    lda #4
    sta scoreDigitCount
    lda #SCORE_COL_FOUR
    sta scoreStartCol
    jmp DrawScore
UpdateScoreDisplay4_NoThousands:
    lda scoreHundreds
    beq UpdateScoreDisplay4_NoHundreds
    sta ScoreDigits
    lda scoreTens
    sta ScoreDigits + 1
    lda scoreOnes
    sta ScoreDigits + 2
    lda #3
    sta scoreDigitCount
    lda #SCORE_COL_THREE
    sta scoreStartCol
    jmp DrawScore
UpdateScoreDisplay4_NoHundreds:
    lda scoreTens
    bne UpdateScoreDisplay4_TwoDigits
    jmp UpdateScoreDisplay4_OneDigit
UpdateScoreDisplay4_TwoDigits:
    sta ScoreDigits
    lda scoreOnes
    sta ScoreDigits + 1
    lda #2
    sta scoreDigitCount
    lda #SCORE_COL_TWO
    sta scoreStartCol
    jmp DrawScore

; The spawn probability data ends at $3eb9 and the bottom-control code begins
; at $3ed0. Keep the compact multiplier selector in that verified code gap.
* = $3eba

LoadChainScoreMultiplier:
    ldx mergeChainDepth
    dex
    cpx #6
    bcc LoadChainScoreMultiplier_InRange
    ldx #5
LoadChainScoreMultiplier_InRange:
    lda ChainScoreMultipliers,x
    tax
    rts

; Chain links five and later continue doubling through x40, then remain at x40.
ChainScoreMultipliers:
    !byte 1, 2, 5, 10, 20, 40

; Build the three-digit BCD amount used by the animated merge-score sprite.
; The visible amount must exactly match AddGroupScore, including the six bonus.
; The side-icon configuration ends at $59a0 and firework tables begin at $59e3.
* = $59a1

CalculateMergeScoreGain:
    php
    sei
    sed
    lda #0
    sta scoreAddCount
    sta scoreAddValue
    jsr LoadChainScoreMultiplier
CalculateMergeScoreGain_Multiplier:
    ldy #3
CalculateMergeScoreGain_Add:
    lda scoreAddCount
    clc
    adc groupValue
    sta scoreAddCount
    bcc CalculateMergeScoreGain_NoHundredsCarry
    inc scoreAddValue
CalculateMergeScoreGain_NoHundredsCarry:
    dey
    bne CalculateMergeScoreGain_Add
    dex
    bne CalculateMergeScoreGain_Multiplier
    lda groupValue
    cmp #6
    bne CalculateMergeScoreGain_Done
    lda scoreAddCount
    clc
    adc #$50
    sta scoreAddCount
    lda scoreAddValue
    adc #$01
    sta scoreAddValue
CalculateMergeScoreGain_Done:
    plp
    rts

* = $93e8
UpdateScoreDisplay4_OneDigit:
    lda scoreOnes
    sta ScoreDigits
    lda #1
    sta scoreDigitCount
    lda #SCORE_COL_ONE
    sta scoreStartCol
    jmp DrawScore
