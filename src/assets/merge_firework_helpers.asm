; Uses the final bytes before the runtime shadow-sprite bank at $4c00.
* = $4be6

ConfigureMergeFirework:
    ldx #2
    lda #$6f
ConfigureMergeFirework_Pointer:
    sta SPRITE0_PTR + 5,x
    dex
    bpl ConfigureMergeFirework_Pointer
    lda #COLOR_YELLOW
    sta SPRITE0_COLOR + 5
    sta SPRITE0_COLOR + 7
    lda mergeFlashColor
    sta SPRITE0_COLOR + 6
    rts
