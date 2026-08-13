; Pulse both diagonals through a five-to-six merge during the cross sweep.
; The routine is split across two small fixed gaps in the packed memory map.
* = $97c2

UpdateSixDiagonalSweep:
    lda groupValue
    cmp #5
    beq UpdateSixDiagonalSweep_Active
    rts
UpdateSixDiagonalSweep_Active:
    lda rippleStep
    and #1
    beq UpdateSixDiagonalSweep_Bright
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    bne UpdateSixDiagonalSweep_StoreColor
UpdateSixDiagonalSweep_Bright:
    lda blindFillColor
UpdateSixDiagonalSweep_StoreColor:
    sta diagonalSweepColor
    lda #0
    sta diagonalSweepCell
UpdateSixDiagonalSweep_Cell:
    lda diagonalSweepCell
    ldy #0
UpdateSixDiagonalSweep_FindRow:
    cmp #5
    bcc UpdateSixDiagonalSweep_PositionReady
    sec
    sbc #5
    iny
    bne UpdateSixDiagonalSweep_FindRow
UpdateSixDiagonalSweep_PositionReady:
    sec
    sbc searchX
    bcs UpdateSixDiagonalSweep_XReady
    eor #$ff
    clc
    adc #1
UpdateSixDiagonalSweep_XReady:
    sta diagonalSweepDistance
    jmp UpdateSixDiagonalSweep_CompareY

* = $91d2
UpdateSixDiagonalSweep_CompareY:
    tya
    sec
    sbc searchY
    bcs UpdateSixDiagonalSweep_YReady
    eor #$ff
    clc
    adc #1
UpdateSixDiagonalSweep_YReady:
    cmp diagonalSweepDistance
    bne UpdateSixDiagonalSweep_Next
    lda diagonalSweepCell
    sta highlightCellIndex
    lda diagonalSweepColor
    jsr ColorHighlightedCell
UpdateSixDiagonalSweep_Next:
    inc diagonalSweepCell
    lda diagonalSweepCell
    cmp #BOARD_CELLS
    beq UpdateSixDiagonalSweep_Done
    jmp UpdateSixDiagonalSweep_Cell
UpdateSixDiagonalSweep_Done:
    rts

diagonalSweepCell:     !byte 0
diagonalSweepDistance: !byte 0
diagonalSweepColor:    !byte 0
