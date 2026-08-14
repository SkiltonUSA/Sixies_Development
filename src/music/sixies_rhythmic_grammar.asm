; Sixies - Rhythmic Grammar
; Original PAL SID tune informed by measured timing and synthesis behavior,
; without reusing melody or harmony from the reference performances.
;
; Load/init: $1000, play: $1003, PAL 50 Hz.
; Six frames per sixteenth note (125 BPM), 128 steps, 15.36 second loop.

SID = $d400

* = $1000
    jmp MusicInit
    jmp MusicPlay

MusicInit:
    lda #0
    ldx #24
MusicInit_ClearSid:
    sta SID,x
    dex
    bpl MusicInit_ClearSid
    sta frameDivider
    sta sequenceStep
    sta modulationPhase
    sta filterPhase
    sta filterDivider
    sta leadGateFrames
    sta bassGateFrames
    sta voice3GateFrames
    sta arpPhase
    sta voice3Noise

    lda #$24
    sta SID + 5
    lda #$a8
    sta SID + 6
    lda #$12
    sta SID + 12
    lda #$98
    sta SID + 13
    lda #$02
    sta SID + 19
    lda #$68
    sta SID + 20
    lda #$a6                ; Resonance 10, filter voices 2 and 3.
    sta SID + 23
    lda #$60
    sta SID + 22
    lda #$1f                ; Low-pass filter, maximum volume.
    sta SID + 24
    rts

MusicPlay:
    jsr UpdateGateCounters
    lda frameDivider
    bne MusicPlay_Modulate
    jsr ProcessMusicStep
MusicPlay_Modulate:
    jsr UpdatePulseWidth
    jsr UpdateArpeggio
    jsr UpdateFilter
    inc modulationPhase
    inc frameDivider
    lda frameDivider
    cmp #6
    bne MusicPlay_Done
    lda #0
    sta frameDivider
    inc sequenceStep
    bpl MusicPlay_Done
    sta sequenceStep
MusicPlay_Done:
    rts

UpdateGateCounters:
    lda leadGateFrames
    beq UpdateGateCounters_Bass
    dec leadGateFrames
    bne UpdateGateCounters_Bass
    lda leadControl
    and #$fe
    sta SID + 4
UpdateGateCounters_Bass:
    lda bassGateFrames
    beq UpdateGateCounters_Voice3
    dec bassGateFrames
    bne UpdateGateCounters_Voice3
    lda bassControl
    and #$fe
    sta SID + 11
UpdateGateCounters_Voice3:
    lda voice3GateFrames
    beq UpdateGateCounters_Done
    dec voice3GateFrames
    bne UpdateGateCounters_Done
    lda #$40
    sta SID + 18
UpdateGateCounters_Done:
    rts

ProcessMusicStep:
    lda sequenceStep
    lsr
    lsr
    lsr
    lsr
    tay
    sta barIndex
    lda LeadControls,y
    sta leadControl
    lda BassControls,y
    sta bassControl

    ldx sequenceStep
    lda LeadNotes,x
    beq ProcessMusicStep_Bass
    jsr TriggerLead
ProcessMusicStep_Bass:
    ldx sequenceStep
    lda BassNotes,x
    beq ProcessMusicStep_Voice3
    jsr TriggerBass
ProcessMusicStep_Voice3:
    lda sequenceStep
    and #$0f
    tax
    lda DrumPattern,x
    beq TriggerArpeggio
    jmp TriggerNoise

TriggerLead:
    pha
    lda leadControl
    and #$fe
    sta SID + 4
    pla
    jsr SelectNote
    lda NoteFreqLo,x
    sta SID
    lda NoteFreqHi,x
    sta SID + 1
    lda leadControl
    ora #1
    sta SID + 4
    lda sequenceStep
    and #7
    bne TriggerLead_Short
    lda #9
    bne TriggerLead_LengthReady
TriggerLead_Short:
    lda #3
TriggerLead_LengthReady:
    sta leadGateFrames
    rts

TriggerBass:
    pha
    lda bassControl
    and #$fe
    sta SID + 11
    pla
    jsr SelectNote
    lda NoteFreqLo,x
    sta SID + 7
    lda NoteFreqHi,x
    sta SID + 8
    lda bassControl
    ora #1
    sta SID + 11
    lda #10
    sta bassGateFrames
    rts

TriggerArpeggio:
    lda #0
    sta voice3Noise
    sta arpPhase
    lda #$40
    sta SID + 18
    jsr SetArpeggioPitch
    lda #$41
    sta SID + 18
    lda #5
    sta voice3GateFrames
    rts

TriggerNoise:
    sta drumType
    lda #1
    sta voice3Noise
    lda #$80
    sta SID + 18
    lda drumType
    cmp #2
    beq TriggerNoise_Snare
    cmp #3
    beq TriggerNoise_Accent
    lda #$00
    sta SID + 14
    lda #$24
    sta SID + 15
    lda #$02
    sta SID + 19
    lda #$20
    sta SID + 20
    lda #1
    bne TriggerNoise_Gate
TriggerNoise_Snare:
    lda #$00
    sta SID + 14
    lda #$08
    sta SID + 15
    lda #$06
    sta SID + 19
    lda #$40
    sta SID + 20
    lda #3
    bne TriggerNoise_Gate
TriggerNoise_Accent:
    lda #$00
    sta SID + 14
    lda #$12
    sta SID + 15
    lda #$09
    sta SID + 19
    lda #$60
    sta SID + 20
    lda #4
TriggerNoise_Gate:
    sta voice3GateFrames
    lda #$81
    sta SID + 18
    rts

UpdateArpeggio:
    lda voice3Noise
    bne UpdateArpeggio_Done
    lda frameDivider
    and #1
    bne UpdateArpeggio_Done
    jsr SetArpeggioPitch
    inc arpPhase
    lda arpPhase
    cmp #3
    bne UpdateArpeggio_Done
    lda #0
    sta arpPhase
UpdateArpeggio_Done:
    rts

SetArpeggioPitch:
    ldy barIndex
    lda arpPhase
    beq SetArpeggioPitch_Root
    cmp #1
    beq SetArpeggioPitch_Third
    lda ArpFifths,y
    bne SetArpeggioPitch_NoteReady
SetArpeggioPitch_Root:
    lda ArpRoots,y
    bne SetArpeggioPitch_NoteReady
SetArpeggioPitch_Third:
    lda ArpThirds,y
SetArpeggioPitch_NoteReady:
    jsr SelectNote
    lda NoteFreqLo,x
    sta SID + 14
    lda NoteFreqHi,x
    sta SID + 15
    rts

UpdatePulseWidth:
    lda modulationPhase
    and #$3f
    cmp #$20
    bcc UpdatePulseWidth_Rising
    eor #$3f
UpdatePulseWidth_Rising:
    asl
    asl
    sta SID + 2
    eor #$78
    sta SID + 16
    lda modulationPhase
    and #3
    clc
    adc #7
    sta SID + 3
    eor #$0f
    and #$0f
    sta SID + 17
    rts

UpdateFilter:
    inc filterDivider
    lda filterDivider
    cmp #12
    bne UpdateFilter_Done
    lda #0
    sta filterDivider
    inc filterPhase
    lda filterPhase
    and #$1f
    sta filterPhase
    cmp #$10
    bcc UpdateFilter_Rising
    eor #$1f
UpdateFilter_Rising:
    asl
    asl
    asl
    clc
    adc #$60
    sta SID + 22
    lda #0
    sta SID + 21
UpdateFilter_Done:
    rts

SelectNote:
    sec
    sbc #36
    tax
    rts

; Original lead phrases. Zero means hold/rest; nonzero values are MIDI notes.
LeadNotes:
!byte 72,0,79,0,0,75,0,81,79,0,0,74,0,77,0,0
!byte 74,0,0,77,0,82,0,0,80,0,77,0,0,75,0,72
!byte 75,0,79,0,82,0,0,86,0,84,0,0,79,0,77,0
!byte 77,0,0,81,0,79,0,0,74,0,0,76,0,72,0,70
!byte 72,0,74,0,77,0,79,0,81,0,0,84,0,79,0,0
!byte 79,0,0,83,0,86,0,84,0,0,81,0,77,0,0,74
!byte 75,0,79,0,0,77,0,72,0,74,0,0,70,0,67,0
!byte 74,0,0,77,0,81,0,0,79,0,75,0,0,72,0,67

BassNotes:
!byte 48,0,0,55,0,0,51,0,48,0,0,55,0,0,46,0
!byte 46,0,0,53,0,0,50,0,46,0,0,53,0,0,43,0
!byte 51,0,0,58,0,0,55,0,51,0,0,58,0,0,50,0
!byte 53,0,0,48,0,0,55,0,53,0,0,60,0,0,52,0
!byte 48,0,0,55,0,0,51,0,48,0,0,58,0,0,55,0
!byte 55,0,0,50,0,0,53,0,55,0,0,62,0,0,53,0
!byte 51,0,0,46,0,0,50,0,51,0,0,55,0,0,46,0
!byte 50,0,0,57,0,0,53,0,50,0,0,45,0,0,43,0

DrumPattern:
!byte 0,0,0,1,2,0,0,1,0,0,0,1,2,0,3,1

LeadControls:
!byte $41,$41,$21,$51,$41,$61,$21,$51
BassControls:
!byte $11,$11,$11,$31,$11,$21,$11,$31
ArpRoots:
!byte 60,58,63,65,60,67,63,62
ArpThirds:
!byte 63,62,67,69,63,70,67,65
ArpFifths:
!byte 67,65,70,72,67,74,70,69

NoteFreqLo:
!byte $5a,$9c,$e2,$2d,$7b,$cf,$27,$85,$e8,$51,$c1,$37,$b4,$38,$c4,$59
!byte $f7,$9d,$4e,$0a,$d0,$a2,$81,$6d,$67,$70,$89,$b2,$ed,$3b,$9c,$13
!byte $a0,$45,$02,$da,$ce,$e0,$11,$64,$da,$76,$39,$26,$40,$89,$04,$b4
!byte $9c,$c0,$23,$c8,$b4,$eb,$72
NoteFreqHi:
!byte $04,$04,$04,$05,$05,$05,$06,$06,$06,$07,$07,$08,$08,$09,$09,$0a
!byte $0a,$0b,$0c,$0d,$0d,$0e,$0f,$10,$11,$12,$13,$14,$15,$17,$18,$1a
!byte $1b,$1d,$1f,$20,$22,$24,$27,$29,$2b,$2e,$31,$34,$37,$3a,$3e,$41
!byte $45,$49,$4e,$52,$57,$5c,$62

frameDivider:    !byte 0
sequenceStep:    !byte 0
modulationPhase: !byte 0
filterPhase:     !byte 0
filterDivider:   !byte 0
leadGateFrames:  !byte 0
bassGateFrames:  !byte 0
voice3GateFrames: !byte 0
leadControl:     !byte $41
bassControl:     !byte $11
barIndex:        !byte 0
arpPhase:        !byte 0
voice3Noise:     !byte 0
drumType:        !byte 0
