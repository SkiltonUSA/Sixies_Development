; A value-5-gated promotion helper fits after the Chain Reaction callout and
; before audio settings code.
* = $3cb0

MaybePromoteTwoToFour:
    ldx #0
MaybePromoteTwoToFour_FindBlank:
    lda board,x
    beq MaybePromoteTwoToFour_StartFiveScan
    inx
    cpx #BOARD_CELLS
    bne MaybePromoteTwoToFour_FindBlank
    rts
MaybePromoteTwoToFour_StartFiveScan:
    ldx #0
MaybePromoteTwoToFour_FindFive:
    lda board,x
    cmp #5
    beq MaybePromoteTwoToFour_HasFive
    inx
    cpx #BOARD_CELLS
    bne MaybePromoteTwoToFour_FindFive
    rts

MaybePromoteTwoToFour_HasFive:
    ldx #0
    lda pieceValue0
    cmp #2
    beq MaybePromoteTwoToFour_Roll
    lda pieceCount
    cmp #2
    bne MaybePromoteTwoToFour_Done
    lda pieceValue1
    cmp #2
    bne MaybePromoteTwoToFour_Done
    inx

; Exact 5% roll: accept 1..240, then select one residue modulo 20. Residue 6
; keeps the deterministic LFSR's value-2 single and double paths reachable.
MaybePromoteTwoToFour_Roll:
    jsr RandomByte
    cmp #241
    bcs MaybePromoteTwoToFour_Roll
    sec
    sbc #1
MaybePromoteTwoToFour_ReduceRoll:
    cmp #20
    bcc MaybePromoteTwoToFour_RollReady
    sbc #20
    jmp MaybePromoteTwoToFour_ReduceRoll
MaybePromoteTwoToFour_RollReady:
    cmp #6
    bne MaybePromoteTwoToFour_Done
    lda #4
    cpx #0
    bne MaybePromoteTwoToFour_Second
    sta pieceValue0
    rts
MaybePromoteTwoToFour_Second:
    sta pieceValue1
MaybePromoteTwoToFour_Done:
    rts

; Weighted spawn tables and the dynamic single-required helper live in the free
; gap after bottom-icon raster setup and before bottom-control input code.
* = $3dd0

; High nibble is die 0; low nibble is die 1, or zero for a single.
; Accepted RNG bytes 1..234 select six complete copies of this 39-entry table.
SpawnDealTable:
    !byte $10,$10,$10,$10,$10
    !byte $20,$20,$20
    !byte $30
    !byte $12,$12,$12,$12,$12
    !byte $13,$13,$13,$13,$13,$13,$13,$13
    !byte $21,$21,$21,$21,$21,$21,$21,$21,$21,$21
    !byte $23
    !byte $31,$31,$31,$31
    !byte $32,$32

MaybeApplyNeighborMatchBonus:
    jsr CountNeighborMatchCandidates
    lda neighborCandidateCount
    beq MaybeApplyNeighborMatchBonus_Done

; Exact 10% roll: accept 1..250, then select remainder zero modulo 10.
MaybeApplyNeighborMatchBonus_Roll:
    jsr RandomByte
    cmp #251
    bcs MaybeApplyNeighborMatchBonus_Roll
    sec
    sbc #1
MaybeApplyNeighborMatchBonus_ReduceRoll:
    cmp #10
    bcc MaybeApplyNeighborMatchBonus_RollReady
    sbc #10
    jmp MaybeApplyNeighborMatchBonus_ReduceRoll
MaybeApplyNeighborMatchBonus_RollReady:
    bne MaybeApplyNeighborMatchBonus_Done

; Choose uniformly from every occupied cell touching at least one blank.
MaybeApplyNeighborMatchBonus_Select:
    jsr RandomByte
    ldy neighborCandidateCount
    cmp NeighborCandidateMax,y
    bcc MaybeApplyNeighborMatchBonus_Accept
    beq MaybeApplyNeighborMatchBonus_Accept
    bcs MaybeApplyNeighborMatchBonus_Select
MaybeApplyNeighborMatchBonus_Accept:
    sec
    sbc #1
MaybeApplyNeighborMatchBonus_ReduceIndex:
    cmp neighborCandidateCount
    bcc MaybeApplyNeighborMatchBonus_IndexReady
    sbc neighborCandidateCount
    jmp MaybeApplyNeighborMatchBonus_ReduceIndex
MaybeApplyNeighborMatchBonus_IndexReady:
    sta neighborCandidateOrdinal
    ldx #0
MaybeApplyNeighborMatchBonus_Find:
    lda board,x
    beq MaybeApplyNeighborMatchBonus_Next
    jsr CellHasBlankNeighbor
    bcc MaybeApplyNeighborMatchBonus_Next
    lda neighborCandidateOrdinal
    beq MaybeApplyNeighborMatchBonus_Use
    dec neighborCandidateOrdinal
MaybeApplyNeighborMatchBonus_Next:
    inx
    cpx #BOARD_CELLS
    bne MaybeApplyNeighborMatchBonus_Find
    rts
MaybeApplyNeighborMatchBonus_Use:
    lda board,x
    sta pieceValue0
MaybeApplyNeighborMatchBonus_Done:
    rts

CountNeighborMatchCandidates:
    lda #0
    sta neighborCandidateCount
    ldx #0
CountNeighborMatchCandidates_Cell:
    lda board,x
    beq CountNeighborMatchCandidates_Next
    jsr CellHasBlankNeighbor
    bcc CountNeighborMatchCandidates_Next
    inc neighborCandidateCount
CountNeighborMatchCandidates_Next:
    inx
    cpx #BOARD_CELLS
    bne CountNeighborMatchCandidates_Cell
    rts

CellHasBlankNeighbor:
    lda LeftNeighbor,x
    jsr NeighborIndexIsBlank
    bcs CellHasBlankNeighbor_Yes
    lda RightNeighbor,x
    jsr NeighborIndexIsBlank
    bcs CellHasBlankNeighbor_Yes
    lda UpNeighbor,x
    jsr NeighborIndexIsBlank
    bcs CellHasBlankNeighbor_Yes
    lda DownNeighbor,x
    jsr NeighborIndexIsBlank
    bcs CellHasBlankNeighbor_Yes
    clc
    rts
CellHasBlankNeighbor_Yes:
    sec
    rts

NeighborIndexIsBlank:
    cmp #$ff
    beq NeighborIndexIsBlank_No
    tay
    lda board,y
    bne NeighborIndexIsBlank_No
    sec
    rts
NeighborIndexIsBlank_No:
    clc
    rts

; Largest multiple of each candidate count not exceeding 255.
NeighborCandidateMax:
    !byte 0,255,254,255,252,255,252,252,248,252,250,253,252
    !byte 247,252,255,240,255,252,247,240,252,242,253,240
