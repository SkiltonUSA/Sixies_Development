; Supplied hi-res comic bursts, decoded into the right sidebar below the
; upcoming-piece preview. Keeping the panel outside the board preserves every
; grid line while the merge animation runs.
MERGE_CALLOUT_COLUMN = GRID_LEFT + GRID_SPAN + 1
MERGE_CALLOUT_ROW = 12
MERGE_CALLOUT_WIDTH_BYTES = 72
MERGE_CALLOUT_WIDTH_CHARS = 9
MERGE_CALLOUT_HEIGHT_ROWS = 8

* = $8a00

BeginMascotMergeCallout:
    jsr SetMergeCalloutPosition
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
    sei
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    cli
    lda #2
    jsr WaitAnimationFrames
    sei
    lda #COLOR_BLACK
    jsr SetMascotPanelColor
    jsr ClearMascotPanel
    lda #COLOR_DKGRAY
    jsr SetMascotPanelColor
    jsr DrawGrid
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
    lda calloutPanelRow
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
    cmp #MERGE_CALLOUT_WIDTH_BYTES
    bne StoreMascotCalloutByte_Next
    inc workRow
    lda workRow
    cmp calloutPanelEndRow
    beq StoreMascotCalloutByte_Done
    jsr SetMascotCalloutBitmapRow
StoreMascotCalloutByte_Next:
    clc
    rts
StoreMascotCalloutByte_Done:
    sec
    rts

SetMascotCalloutBitmapRow:
    jmp SetMascotCalloutBitmapRowInGap

SetMascotPanelColor:
    asl
    asl
    asl
    asl
    sta mascotPanelColor
    lda calloutPanelRow
    sta workRow
SetMascotPanelColor_Row:
    jsr SetMascotCalloutScreenRow
    ldy #0
SetMascotPanelColor_Cell:
    lda mascotPanelColor
    sta (PTR_LO),y
    iny
    cpy #MERGE_CALLOUT_WIDTH_CHARS
    bne SetMascotPanelColor_Cell
    inc workRow
    lda workRow
    cmp calloutPanelEndRow
    bne SetMascotPanelColor_Row
    rts

ClearMascotPanel:
    lda calloutPanelRow
    sta workRow
ClearMascotPanel_Row:
    lda workRow
    jsr SetBitmapRowPointer
    lda calloutPanelColumn
    jsr AddColumnOffset
    ldy #0
ClearMascotPanel_Byte:
    lda #0
    sta (PTR_LO),y
    iny
    cpy #MERGE_CALLOUT_WIDTH_BYTES
    bne ClearMascotPanel_Byte
    inc workRow
    lda workRow
    cmp calloutPanelEndRow
    bne ClearMascotPanel_Row
    rts

UpdateMascotCalloutRipple:
    rts

ApplyMascotCalloutMergeColors:
    sei
    lda #COLOR_WHITE
    jsr SetMascotPanelColor
    cli
    rts

; The removed gameplay-sidebar logo leaves this fixed helper gap available.
* = $4b84

SetMergeCalloutPosition:
    lda #MERGE_CALLOUT_COLUMN
    sta calloutPanelColumn
    lda #MERGE_CALLOUT_ROW
    sta calloutPanelRow
    clc
    adc #MERGE_CALLOUT_HEIGHT_ROWS
    sta calloutPanelEndRow
    rts

SetMascotCalloutScreenRow:
    lda workRow
    jsr SetScreenRowPointer
    lda PTR_LO
    clc
    adc calloutPanelColumn
    sta PTR_LO
    bcc SetMascotCalloutScreenRow_Done
    inc PTR_HI
SetMascotCalloutScreenRow_Done:
    rts

SetMascotCalloutBitmapRowInGap:
    lda workRow
    jsr SetBitmapRowPointer
    lda calloutPanelColumn
    jsr AddColumnOffset
    lda #0
    sta calloutDestinationOffset
    rts

calloutDestinationOffset: !byte 0
mascotPanelColor: !byte 0
calloutPanelColumn:  !byte MERGE_CALLOUT_COLUMN
calloutPanelRow:     !byte MERGE_CALLOUT_ROW
calloutPanelEndRow:  !byte MERGE_CALLOUT_ROW + MERGE_CALLOUT_HEIGHT_ROWS

!source "src/assets/merge_callout_data.asm"
