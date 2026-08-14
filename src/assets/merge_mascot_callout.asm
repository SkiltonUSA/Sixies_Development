; Supplied hi-res comic bursts, decoded directly into the 80x80 sidebar.
; This avoids the merge-time sprite contention of the previous implementation.
* = $8a00

BeginMascotMergeCallout:
    sei
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    cli
    lda #2
    jsr WaitAnimationFrames
    sei
    lda #COLOR_BLACK
    jsr SetMascotPanelColor
    cli
    lda #1
    jsr WaitAnimationFrames

    sei
    jsr ClearMascotPanel
    jsr SelectMascotMergeCallout
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    jsr DecodeMascotMergeCallout
    cli
    lda #2
    jsr WaitAnimationFrames

    sei
    lda #COLOR_LTGRAY
    jsr SetMascotPanelColor
    cli
    lda #2
    jsr WaitAnimationFrames

    jmp ApplyMascotCalloutMergeColors

EndMascotMergeCallout:
    lda #0
    sta calloutRippleActive
    sei
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    cli
    lda #2
    jsr WaitAnimationFrames
    sei
    lda #COLOR_BLACK
    jsr SetMascotPanelColor
    ; Callout and mascot both own the full ten-column sidebar.
    jsr ClearMascotPanel
    jsr DrawMainMascot
    cli
    rts

SelectMascotMergeCallout:
    lda groupValue
    cmp #5
    beq SelectMascotMergeCallout_Fives
    cmp #6
    beq SelectMascotMergeCallout_Sixies
    ldx mergeCalloutIndex
    inc mergeCalloutIndex
    lda mergeCalloutIndex
    cmp #MergeCalloutGeneralCount
    bcc SelectMascotMergeCallout_IndexReady
    lda #0
    sta mergeCalloutIndex
    beq SelectMascotMergeCallout_IndexReady
SelectMascotMergeCallout_Fives:
    ldx #MergeCalloutFivesIndex
    bne SelectMascotMergeCallout_IndexReady
SelectMascotMergeCallout_Sixies:
    ldx #MergeCalloutSixiesIndex
SelectMascotMergeCallout_IndexReady:
    lda MergeCalloutOffsetLo,x
    clc
    adc #<MergeCalloutPackedData
    sta SOURCE_LO
    lda MergeCalloutOffsetHi,x
    adc #>MergeCalloutPackedData
    sta SOURCE_HI
    rts

DecodeMascotMergeCallout:
    lda #4
    sta workRow
    jsr SetMascotCalloutBitmapRow
DecodeMascotMergeCallout_Packet:
    jsr ReadMascotCalloutByte
    ; ReadMascotCalloutByte advances SOURCE_LO, which changes the flags.
    ; Test the returned packet explicitly before choosing its decode path.
    cmp #0
    beq DecodeMascotMergeCallout_Done
    cmp #$80
    bcs DecodeMascotMergeCallout_Run
    sta packedCount
DecodeMascotMergeCallout_Literal:
    jsr ReadMascotCalloutByte
    jsr StoreMascotCalloutByte
    bcs DecodeMascotMergeCallout_Done
    dec packedCount
    bne DecodeMascotMergeCallout_Literal
    jmp DecodeMascotMergeCallout_Packet
DecodeMascotMergeCallout_Run:
    and #$7f
    sta packedCount
    jsr ReadMascotCalloutByte
    sta packedValue
DecodeMascotMergeCallout_RunByte:
    lda packedValue
    jsr StoreMascotCalloutByte
    bcs DecodeMascotMergeCallout_Done
    dec packedCount
    bne DecodeMascotMergeCallout_RunByte
    jmp DecodeMascotMergeCallout_Packet
DecodeMascotMergeCallout_Done:
    rts

ReadMascotCalloutByte:
    ldy #0
    lda (SOURCE_LO),y
    inc SOURCE_LO
    bne ReadMascotCalloutByte_Done
    inc SOURCE_HI
ReadMascotCalloutByte_Done:
    rts

StoreMascotCalloutByte:
    ldy calloutDestinationOffset
    sta (PTR_LO),y
    inc calloutDestinationOffset
    lda calloutDestinationOffset
    cmp #80
    bne StoreMascotCalloutByte_Next
    inc workRow
    lda workRow
    cmp #14
    beq StoreMascotCalloutByte_Done
    jsr SetMascotCalloutBitmapRow
StoreMascotCalloutByte_Next:
    clc
    rts
StoreMascotCalloutByte_Done:
    sec
    rts

SetMascotCalloutBitmapRow:
    lda workRow
    jsr SetBitmapRowPointer
    lda #0
    sta calloutDestinationOffset
    rts

SetMascotPanelColor:
    asl
    asl
    asl
    asl
    sta mascotPanelColor
    lda #4
    sta workRow
SetMascotPanelColor_Row:
    lda workRow
    jsr SetScreenRowPointer
    ldy #0
SetMascotPanelColor_Cell:
    lda mascotPanelColor
    sta (PTR_LO),y
    iny
    cpy #10
    bne SetMascotPanelColor_Cell
    inc workRow
    lda workRow
    cmp #14
    bne SetMascotPanelColor_Row
    rts

ClearMascotPanel:
    lda #4
    sta workRow
ClearMascotPanel_Row:
    lda workRow
    jsr SetBitmapRowPointer
    ldy #0
ClearMascotPanel_Byte:
    lda #0
    sta (PTR_LO),y
    iny
    cpy #80
    bne ClearMascotPanel_Byte
    inc workRow
    lda workRow
    cmp #14
    bne ClearMascotPanel_Row
    rts

UpdateMascotCalloutRipple:
    lda calloutRippleActive
    beq UpdateMascotCalloutRipple_Done
    inc calloutRippleTimer
    lda calloutRippleTimer
    cmp #3
    bcc UpdateMascotCalloutRipple_Done
    lda #0
    sta calloutRippleTimer
    inc calloutRipplePhase
    lda calloutRippleActive
    cmp #2
    beq UpdateMascotCalloutRipple_BandPhase
    lda calloutRipplePhase
    and #7
    sta calloutRipplePhase
    jsr RenderMascotCalloutRipple
    rts
UpdateMascotCalloutRipple_BandPhase:
    lda calloutRipplePhase
    cmp #11
    bcc UpdateMascotCalloutRipple_PhaseReady
    lda #0
UpdateMascotCalloutRipple_PhaseReady:
    sta calloutRipplePhase
    jsr RenderMascotCalloutBands
UpdateMascotCalloutRipple_Done:
    rts

ApplyMascotCalloutMergeColors:
    lda #0
    sta calloutRippleActive
    sta calloutRipplePhase
    sta calloutRippleTimer
    lda groupValue
    cmp #4
    bcs ApplyMascotCalloutMergeColors_Ripple
    cmp #3
    beq ApplyMascotCalloutMergeColors_Three
    cmp #2
    beq ApplyMascotCalloutMergeColors_Two

    ; Merging 1s keeps the word still and bright without a color pattern.
    sei
    lda #COLOR_WHITE
    jsr SetMascotPanelColor
    cli
    rts
ApplyMascotCalloutMergeColors_Two:
    lda #COLOR_LTBLUE
    sta calloutBandColors
    lda #COLOR_LTGRAY
    sta calloutBandColors + 1
    jmp ApplyMascotCalloutMergeColors_Bands
ApplyMascotCalloutMergeColors_Three:
    lda #COLOR_GREEN
    sta calloutBandColors
    lda #COLOR_WHITE
    sta calloutBandColors + 1
ApplyMascotCalloutMergeColors_Bands:
    lda #2
    sta calloutRippleActive
    jmp RenderMascotCalloutBands
ApplyMascotCalloutMergeColors_Ripple:
    lda #1
    sta calloutRippleActive
    jmp RenderMascotCalloutRipple

RenderMascotCalloutBands:
    sei
    lda #0
    sta calloutRippleCell
    lda #4
    sta workRow
RenderMascotCalloutBands_Row:
    lda workRow
    jsr SetScreenRowPointer
    lda #0
    sta workColumn
RenderMascotCalloutBands_Cell:
    lda groupValue
    cmp #2
    beq RenderMascotCalloutBands_BlueToGray
    ldx #1
    lda workColumn
    cmp calloutRipplePhase
    bne RenderMascotCalloutBands_ColorReady
    ldx #0
    jmp RenderMascotCalloutBands_ColorReady
RenderMascotCalloutBands_BlueToGray:
    ldx #0
    lda workColumn
    cmp calloutRipplePhase
    bcs RenderMascotCalloutBands_ColorReady
    ldx #1
RenderMascotCalloutBands_ColorReady:
    lda calloutBandColors,x
    asl
    asl
    asl
    asl
    ldy workColumn
    sta (PTR_LO),y
    inc calloutRippleCell
    inc workColumn
    lda workColumn
    cmp #10
    bne RenderMascotCalloutBands_Cell
    inc workRow
    lda workRow
    cmp #14
    bne RenderMascotCalloutBands_Row
    cli
    rts

RenderMascotCalloutRipple:
    sei
    lda #0
    sta calloutRippleCell
    lda #4
    sta workRow
RenderMascotCalloutRipple_Row:
    lda workRow
    jsr SetScreenRowPointer
    lda #0
    sta workColumn
RenderMascotCalloutRipple_Cell:
    ldy calloutRippleCell
    lda CalloutRippleDistance,y
    clc
    adc calloutRipplePhase
    and #7
    tax
    lda CalloutRippleColors,x
    asl
    asl
    asl
    asl
    ldy workColumn
    sta (PTR_LO),y
    inc calloutRippleCell
    inc workColumn
    lda workColumn
    cmp #10
    bne RenderMascotCalloutRipple_Cell
    inc workRow
    lda workRow
    cmp #14
    bne RenderMascotCalloutRipple_Row
    cli
    rts

; Concentric square distance from the center of the 10x10 sidebar. Values 4-6
; use this table; values 2-3 instead sweep one colored column left-to-right.
CalloutRippleDistance:
    !byte 4,4,4,4,4,4,4,4,4,4
    !byte 4,3,3,3,3,3,3,3,3,4
    !byte 4,3,2,2,2,2,2,2,3,4
    !byte 4,3,2,1,1,1,1,2,3,4
    !byte 4,3,2,1,0,0,1,2,3,4
    !byte 4,3,2,1,0,0,1,2,3,4
    !byte 4,3,2,1,1,1,1,2,3,4
    !byte 4,3,2,2,2,2,2,2,3,4
    !byte 4,3,3,3,3,3,3,3,3,4
    !byte 4,4,4,4,4,4,4,4,4,4

; Red, light red, orange, yellow, light green, cyan, light blue, purple.
CalloutRippleColors: !byte 2,10,8,7,13,3,14,4

calloutDestinationOffset: !byte 0
mascotPanelColor: !byte 0
calloutRippleActive: !byte 0
calloutRipplePhase:  !byte 0
calloutRippleTimer:  !byte 0
calloutRippleCell:   !byte 0
calloutBandColors:   !byte COLOR_WHITE,COLOR_WHITE

!source "src/assets/merge_callout_data.asm"
