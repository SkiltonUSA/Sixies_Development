; Lives with the merge-shake code below the packed callouts and above the screen.
* = $4300

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
