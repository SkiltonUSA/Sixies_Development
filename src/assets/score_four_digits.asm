; Four-digit score arithmetic and display selection.
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

* = $93e8
UpdateScoreDisplay4_OneDigit:
    lda scoreOnes
    sta ScoreDigits
    lda #1
    sta scoreDigitCount
    lda #SCORE_COL_ONE
    sta scoreStartCol
    jmp DrawScore
