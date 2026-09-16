; Modal confirmation shown beneath the live board before New Game can erase it.
; The merge-callout implementation ends below $8b60 and the grid-sweep module
; starts at $8d00, leaving this fixed executable-code gap available.
* = $8b60

ConfirmNewGame:
    jsr DrawNewGameConfirmation

    ; Drain the key that opened the prompt so its repeat cannot confirm it.
ConfirmNewGame_Release:
    jsr WaitFrame
    jsr SCNKEY
    jsr GETIN
    bne ConfirmNewGame_Release

ConfirmNewGame_Wait:
    jsr WaitFrame
    jsr SCNKEY
    jsr GETIN
    beq ConfirmNewGame_Wait
    cmp #'Y'
    beq ConfirmNewGame_Yes
    cmp #'N'
    bne ConfirmNewGame_Wait
    jsr ClearNewGameConfirmation
    clc
    rts
ConfirmNewGame_Yes:
    jsr ClearNewGameConfirmation
    sec
    rts

DrawNewGameConfirmation:
    lda #<NewGameConfirmationText
    sta highTextSourceLo
    lda #>NewGameConfirmationText
    sta highTextSourceHi
    lda #17
    sta highTextLength
    lda #24
    sta highTextRow
    lda #11
    sta highTextColumn
    lda #COLOR_YELLOW
    sta highTextColor
    jmp DrawSixiesHiresText

ClearNewGameConfirmation:
    lda #24
    jsr SetBitmapRowPointer
    lda #11
    jsr AddColumnOffset
    lda #0
    ldy #0
ClearNewGameConfirmation_Byte:
    sta (PTR_LO),y
    iny
    cpy #(17 * 8)
    bne ClearNewGameConfirmation_Byte
    rts

NewGameConfirmationText:
    !text "Y OR N TO CONFIRM"
