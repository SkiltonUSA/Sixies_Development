; Merge cross: row and column segments travel from the grid edges to activeIndex.
* = $5ad0

RunMergeGridSweep:
    lda activeIndex
    ldx #0
RunMergeGridSweep_FindRow:
    cmp #5
    bcc RunMergeGridSweep_PositionReady
    sec
    sbc #5
    inx
    bne RunMergeGridSweep_FindRow
RunMergeGridSweep_PositionReady:
    sta searchX
    stx searchY

    lda mergeFlashColor
    sta blindFillColor
    asl
    asl
    asl
    asl
    ora blindFillColor
    sta blindFillColor
    lda #1
    sta mergeAnimating
    sta mergeFlashPhase
    jsr PublishBoardForAnimation

    lda #0
    sta rippleStep
RunMergeGridSweep_Step:
    jsr RestoreMergeGridCross

    lda rippleStep
    cmp searchX
    bcc RunMergeGridSweep_LeftReady
    lda searchX
RunMergeGridSweep_LeftReady:
    jsr ColorMergeHorizontalSegment

    lda #4
    sec
    sbc rippleStep
    cmp searchX
    bcs RunMergeGridSweep_RightReady
    lda searchX
RunMergeGridSweep_RightReady:
    jsr ColorMergeHorizontalSegment

    lda rippleStep
    cmp searchY
    bcc RunMergeGridSweep_TopReady
    lda searchY
RunMergeGridSweep_TopReady:
    jsr ColorMergeVerticalSegment

    lda #4
    sec
    sbc rippleStep
    cmp searchY
    bcs RunMergeGridSweep_BottomReady
    lda searchY
RunMergeGridSweep_BottomReady:
    jsr ColorMergeVerticalSegment

    lda #2
    jsr WaitAnimationFrames
    inc rippleStep
    lda rippleStep
    cmp #5
    bne RunMergeGridSweep_Step
    jsr RestoreMergeGridCross
    lda #0
    sta mergeFlashPhase
    rts

RestoreMergeGridCross:
    lda #0
    sta workColumn
RestoreMergeGridCross_Cell:
    ldx searchY
    lda RowIndexBase,x
    clc
    adc workColumn
    sta highlightCellIndex
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    jsr ColorHighlightedCell

    ldx workColumn
    lda RowIndexBase,x
    clc
    adc searchX
    sta highlightCellIndex
    lda #(COLOR_DKGRAY << 4) | COLOR_BLACK
    jsr ColorHighlightedCell

    inc workColumn
    lda workColumn
    cmp #5
    bne RestoreMergeGridCross_Cell
    rts

ColorMergeHorizontalSegment:
    sta workRow
    ldx searchY
    lda RowIndexBase,x
    clc
    adc workRow
    sta highlightCellIndex
    lda blindFillColor
    jmp ColorHighlightedCell

ColorMergeVerticalSegment:
    tax
    lda RowIndexBase,x
    clc
    adc searchX
    sta highlightCellIndex
    lda blindFillColor
    jmp ColorHighlightedCell
